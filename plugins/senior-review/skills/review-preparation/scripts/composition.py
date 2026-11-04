"""Bind the computed roster into dispatchable jobs, so the roles stay small and the review is composed.

``review_roster.py`` decides who reviews; this helper decides how those identities
become isolated jobs. Each roster identity becomes one job; a composition from
``plugin.toml`` expands to its leaf roles, so a tailored reviewer is a list of
focused role files plus the shared conventions, never a merged body. The output
names files and SHA-256 digests only: role prose is never copied into the plan.

Two commands:

- ``catalog``: the reviewer catalog derived from ``plugin.toml`` (``id``,
  ``kind``, ``members``), the entries ``review_roster.py`` reads from its
  ``--context``.
- ``bind``: ``ROSTER.json`` + ``BINDINGS.json`` -> ``PREPARED-REVIEW.json`` with
  ``jobs``, ``common`` and ``gaps``. An identity absent from the catalog or a
  missing role file leaves its job ``unbound`` and the exit status non-zero, so
  the dispatch step refuses an incomplete plan.

Usage:

    python composition.py catalog [--plugin-root DIR] --out CATALOG.json
    python composition.py bind --roster ROSTER.json --bindings BINDINGS.json [--plugin-root DIR] --out PREPARED-REVIEW.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

ROSTER_SCHEMA = "daodan/review-roster/v1"
SCHEMA = "daodan/prepared-review/v1"
PLUGIN = "senior-review"
COMMON = Path("skills/review-quality-gates/references/reviewer-common.md")
DEFAULT_ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_catalog(plugin_root: Path) -> dict:
    manifest = tomllib.loads((plugin_root / "plugin.toml").read_text(encoding="utf-8"))
    compositions = {f"{PLUGIN}:{name}": list(table["members"])
                    for name, table in manifest.get("reviewers", {}).get("compositions", {}).items()}
    entries = []
    for name in manifest["components"]["roles"]:
        identity = f"{PLUGIN}:{name}"
        if identity in compositions:
            entries.append({"id": identity, "kind": "composition", "members": compositions[identity]})
        else:
            # No `members` key: review_roster.py treats its presence as a composition.
            entries.append({"id": identity, "kind": "role", "file": (Path("roles") / f"{name}.md").as_posix()})
    return {"schema": "daodan/reviewer-catalog/v1", "plugin": PLUGIN, "entries": entries}


def leaf_roles(identity: str, entries: dict, trail: tuple = ()) -> list[str]:
    """Expand a composition to its leaf roles in first-seen order; a cycle is an error."""
    if identity in trail:
        raise ValueError("cyclic composition: " + " -> ".join((*trail, identity)))
    entry = entries.get(identity)
    if entry is None or entry["kind"] == "role":
        return [identity]
    leaves: list[str] = []
    for member in entry["members"]:
        for leaf in leaf_roles(member, entries, (*trail, identity)):
            if leaf not in leaves:
                leaves.append(leaf)
    return leaves


def bind(roster: dict, bindings: dict, plugin_root: Path) -> dict:
    if roster.get("schema") != ROSTER_SCHEMA:
        raise ValueError("roster schema is not " + ROSTER_SCHEMA)
    grounding = roster.get("grounding", {})
    candidate = bindings.get("candidate")
    if candidate is None or (grounding.get("candidate") and grounding["candidate"] != candidate):
        raise ValueError("bindings.candidate must equal the roster's grounding candidate")
    if "knowledge_selection" not in bindings:
        raise ValueError("bindings.knowledge_selection is required; use \"\" for an explicit empty selection")
    output_dir = bindings.get("output_dir", "jobs")
    default_mode = bindings.get("input_mode", "independent")
    scopes = bindings.get("scopes", {})
    default_scope = grounding.get("scope_id") or roster.get("id") or "candidate"

    catalog = load_catalog(plugin_root)
    entries = {row["id"]: row for row in catalog["entries"]}
    common_path = plugin_root / COMMON
    common = {"path": COMMON.as_posix(), "sha256": sha256(common_path)}
    gaps: list[str] = list(roster.get("gaps", []))
    jobs: list[dict] = []

    def scope_of(scope_id: str) -> dict:
        scope = scopes.get(scope_id, {})
        return {"input_mode": scope.get("input_mode", default_mode),
                "permissions": scope.get("permissions", "read-only"),
                "output_dir": scope.get("output_dir", output_dir)}

    def add_job(role: str, scope_id: str, members: list[str]) -> None:
        scope = scope_of(scope_id)
        source_bindings: dict[str, dict] = {}
        unbound: list[str] = []
        for member in members:
            entry = entries.get(member)
            path = plugin_root / entry["file"] if entry and entry.get("file") else None
            if path is None or not path.is_file():
                unbound.append(member)
                continue
            source_bindings[member] = {"path": entry["file"], "sha256": sha256(path)}
        for member in unbound:
            gaps.append(f"specialist absent from catalog or role file missing: {member} (job for {role}, scope {scope_id})")
        digest = hashlib.sha256()
        for member in sorted(source_bindings):
            digest.update(f"{member}\n{source_bindings[member]['sha256']}\n".encode())
        digest.update(f"common\n{common['sha256']}\n".encode())
        job_id = f"job-{len(jobs) + 1:02d}"
        jobs.append({
            "job_id": job_id, "role": role, "specialist_ids": members, "scope_id": scope_id,
            "input_mode": scope["input_mode"], "permissions": scope["permissions"],
            "candidate": candidate, "knowledge_selection": bindings["knowledge_selection"],
            "source_bindings": source_bindings, "body_sha256": digest.hexdigest(),
            "output_path": f"{scope['output_dir'].rstrip('/')}/{job_id}.md",
            "status": "unbound" if unbound else "bound", "unbound": unbound,
        })

    # Plan first: one job per roster identity, then one per uncovered required
    # specialist. Light folds the required specialists into its single job.
    plan: list[dict] = []
    for role in roster.get("roster", []):
        if role not in entries:
            gaps.append(f"roster identity absent from catalog: {role}")
        plan.append({"role": role, "scope_id": default_scope, "members": leaf_roles(role, entries)})

    def covered(identity: str, scope_id: str) -> bool:
        return any(job["scope_id"] == scope_id and identity in job["members"] for job in plan)

    for item in roster.get("required_specialists", []):
        identity, scope_id = item["specialist_id"], item.get("scope_id", default_scope)
        missing = [m for m in leaf_roles(identity, entries) if not covered(m, scope_id)]
        if not missing:
            continue
        if roster.get("shape") == "light" and plan and plan[0]["scope_id"] == scope_id:
            plan[0]["members"] += missing
        else:
            plan.append({"role": identity, "scope_id": scope_id, "members": missing})

    if roster.get("shape") == "light" and len(plan) != 1:
        raise ValueError(f"light requires exactly one discovery job, got {len(plan)}; use branch review")
    for job in plan:
        add_job(job["role"], job["scope_id"], job["members"])
    return {**roster, "schema": SCHEMA, "roster_schema": ROSTER_SCHEMA, "common": common,
            "catalog_sha256": sha256(plugin_root / "plugin.toml"), "jobs": jobs,
            "gaps": list(dict.fromkeys(gaps))}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_ROOT, help="directory holding plugin.toml")
    sub = parser.add_subparsers(dest="command", required=True)
    catalog_parser = sub.add_parser("catalog")
    catalog_parser.add_argument("--out", required=True)
    bind_parser = sub.add_parser("bind")
    bind_parser.add_argument("--roster", required=True)
    bind_parser.add_argument("--bindings", required=True)
    bind_parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    if args.command == "catalog":
        catalog = load_catalog(args.plugin_root)
        Path(args.out).write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"entries": len(catalog["entries"])}))
        return 0
    roster = json.loads(Path(args.roster).read_text(encoding="utf-8"))
    bindings = json.loads(Path(args.bindings).read_text(encoding="utf-8"))
    try:
        prepared = bind(roster, bindings, args.plugin_root)
    except ValueError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    Path(args.out).write_text(json.dumps(prepared, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unbound = [job["job_id"] for job in prepared["jobs"] if job["status"] == "unbound"]
    print(json.dumps({"jobs": len(prepared["jobs"]), "unbound": unbound, "gaps": prepared["gaps"]}))
    return 1 if unbound else 0


if __name__ == "__main__":
    sys.exit(main())
