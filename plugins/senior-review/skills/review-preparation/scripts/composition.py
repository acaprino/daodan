"""Bind the computed roster into dispatchable jobs, so the roles stay small and the review is composed.

``review_roster.py`` computes the rigor and an automatic roster; team-review's Phase 1
replaces that roster with the reviewers it chose (``selection`` in the bindings). This
helper decides how those identities become isolated jobs. Each roster identity becomes one job; a composition from
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
  the dispatch step refuses an incomplete plan. A branch bind must state its
  ``selection``, so skipping the choice is an error and not 26 silent members.
  With ``coverage`` (branch review on content basis only), every file of the
  resolved perimeter (``grounding.conclusion_paths``) gets one cell per planned
  reviewer of the default scope, and each such job becomes one job per group of
  its open files under a byte budget, with ``paths`` and a single JSON result at
  ``output_path``. Stack reviewers (TypeScript, React, Tauri) skip only files
  that clearly lack their stack; a requested file absent from the inventory stays
  open without a job.
- ``account``: after the delivery barrier, each group job's result at
  ``output_path`` closes its cells. A cell is ``covered`` only when the result is
  bound to its job, delivered, complete for every member, and lists the file in
  ``read`` and not in ``partial``; every other assigned cell stays ``open`` with
  the reason. Exit 0 means the account succeeded, not that the review is complete.

Usage:

    python composition.py catalog [--plugin-root DIR] --out CATALOG.json
    python composition.py bind --roster ROSTER.json --bindings BINDINGS.json [--plugin-root DIR] --out PREPARED-REVIEW.json
    python composition.py account --prepared PREPARED-REVIEW.json --out COVERAGE.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

import review_roster

ROSTER_SCHEMA = "daodan/review-roster/v1"
SCHEMA = "daodan/prepared-review/v1"
COVERAGE_SCHEMA = "daodan/review-coverage/v1"
FILES_SCHEMA = "codebase-map/files/v1"
PLUGIN = "senior-review"
COMMON = Path("skills/review-quality-gates/references/reviewer-common.md")
DEFAULT_ROOT = Path(__file__).resolve().parents[3]
AUTOMATIC_SOURCES = {"computed-roster", "code-review-floor"}
# Source bytes per group job, calibrated by benchmarks/whole-source-coverage. It
# sizes the groups; it neither bounds token cost nor sets the host's parallelism.
GROUP_BYTES = 120_000
SCRIPT_LANGUAGES = {"javascript", "typescript", "vue", "svelte"}
CONFIG_SUFFIXES = {".json", ".toml", ".yaml", ".yml", ".ini", ".cfg"}
MISSING = "missing from map inventory"


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


def apply_selection(roster: dict, selection) -> dict:
    """Make Phase 1's choice the roster; only obligations with a source of their own survive it."""
    branch = roster.get("shape") == "branch"
    if selection is None and branch:
        raise ValueError('bindings.selection is required for branch: the reviewers Phase 1 chose, '
                         'or "automatic" for a variant or document kind without that choice')
    if selection is None or selection == "automatic":
        return roster
    if not branch:
        raise ValueError("only a branch review takes a selection")
    if not isinstance(selection, list) or not selection or not all(isinstance(r, str) and r for r in selection):
        raise ValueError('bindings.selection must be a non-empty list of catalog identities or "automatic"')
    kept = [item for item in roster.get("required_specialists", [])
            if not all(isinstance(e, dict) and e.get("source") in AUTOMATIC_SOURCES for e in item.get("evidence", []))]
    return {**roster, "roster": list(selection), "required_specialists": kept,
            "selection": {"reviewers": list(selection),
                          "superseded": [r for r in roster.get("roster", []) if r not in selection]}}


def pack(rows: list[dict], budget: int) -> list[list[dict]]:
    """Files in path order; a new group when the next file would pass the budget. A larger file stands alone."""
    groups: list[list[dict]] = []
    size = 0
    for row in sorted(rows, key=lambda item: item["path"]):
        if groups and size + row["size"] <= budget:
            groups[-1].append(row)
            size += row["size"]
        else:
            groups.append([row])
            size = row["size"]
    return groups


def coverage_scope(roster: dict, coverage: dict, entries: dict) -> dict:
    """Validated coverage bindings and the facts the cells need, read once."""
    if not isinstance(coverage, dict):
        raise ValueError("coverage must be an object with files, root and budget")
    if roster.get("shape") != "branch" or roster.get("review_basis") != "content":
        raise ValueError("coverage applies only to a branch review on content basis")
    budget = coverage.get("budget", GROUP_BYTES)
    if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
        raise ValueError("coverage.budget must be a positive number of bytes")
    requested = roster.get("grounding", {}).get("conclusion_paths")
    if not isinstance(requested, list) or not all(isinstance(path, str) for path in requested):
        raise ValueError("coverage needs grounding.conclusion_paths: the resolved perimeter, never implied")
    try:
        files = Path(coverage["files"])
        payload = json.loads(files.read_text(encoding="utf-8"))
    except (KeyError, TypeError, OSError, ValueError) as error:
        raise ValueError(f"coverage.files must name the FILES.json of snapshot.py files: {error}") from None
    if not isinstance(payload, dict) or payload.get("schema") != FILES_SCHEMA:
        raise ValueError("coverage.files schema is not " + FILES_SCHEMA)
    inventory = {row["path"]: row for row in payload.get("files", [])}
    ordered = sorted(inventory)
    paths: set[str] = set()
    for entry in requested:
        # A directory entry selects its inventoried files; an entry selecting none stays as a missing path.
        under = [entry] if entry in inventory else [path for path in ordered if review_roster.in_scope(path, [entry])]
        paths.update(under or [entry])
    root = Path(coverage.get("root", ".")).resolve()
    for path in sorted(paths & inventory.keys()):
        if not (root / path).is_file():
            raise ValueError(f"inventory file missing on disk: {path}; refresh the map")
    # Paths named by an obligation's evidence keep a stack reviewer's check; configuration sources keep everyone's.
    configured: list[str] = []
    obliged: dict[str, list[str]] = {}
    for item in roster.get("required_specialists", []):
        for evidence in item.get("evidence", []):
            if isinstance(evidence, dict) and isinstance(evidence.get("path"), str):
                obliged.setdefault(item.get("specialist_id"), []).append(evidence["path"])
                if evidence.get("source") == "configurations":
                    configured.append(evidence["path"])
    stacks = {**review_roster.LANGUAGE_ROLE, "tauri": review_roster.SIGNAL_ROLE["tauri"]}
    units = coverage.get("units", [])
    if not isinstance(units, list) or not all(isinstance(unit, list) and all(isinstance(path, str) for path in unit)
                                              for unit in units):
        raise ValueError("coverage.units must be a list of path lists")
    return {"files": files.resolve().as_posix(), "root": root, "budget": budget, "inventory": inventory, "units": units,
            "paths": sorted(paths), "configured": configured, "obliged": obliged, "texts": {},
            "stack_of": {leaf: stack for stack, role in stacks.items() for leaf in leaf_roles(role, entries)}}


def stack_skip(cover: dict, path: str, row: dict, stacks: set[str], keep: list[str]) -> str | None:
    """Why a stack-only reviewer skips the file, or None when the file keeps the check."""
    if (row.get("language") is None or Path(path).suffix.lower() in CONFIG_SUFFIXES
            or review_roster.MANIFEST_NAME.search(path) or review_roster.in_scope(path, keep)):
        return None
    if stacks & {"typescript", "react"} and row["language"] in SCRIPT_LANGUAGES:
        return None
    if "tauri" in stacks:
        if review_roster.SIGNAL_PATHS["tauri"].search(path):
            return None
        texts = cover["texts"]
        if path not in texts:
            texts[path] = (cover["root"] / path).read_text(encoding="utf-8", errors="replace")
        if review_roster.SIGNAL_PATTERNS["tauri"].search(texts[path]):
            return None
    return f"no {', '.join(sorted(stacks))} sign in file"


def reviewer_cells(cover: dict, role: str, members: list[str]) -> list[dict]:
    """One cell per perimeter path for this reviewer: open, or not-applicable with its reason."""
    stack_of = cover["stack_of"]
    stacks = {stack_of[member] for member in members} if all(member in stack_of for member in members) else set()
    keep = cover["configured"] + [path for identity in (role, *members) for path in cover["obliged"].get(identity, [])]
    cells = []
    for path in cover["paths"]:
        row = cover["inventory"].get(path)
        cell = {"path": path, "reviewer": role, "sha256": row["sha256"] if row else None,
                "status": "open", "job_id": None, "note": "" if row else MISSING}
        reason = stack_skip(cover, path, row, stacks, keep) if row and stacks else None
        if reason:
            cell.update(status="not-applicable", note=reason)
        cells.append(cell)
    return cells


def bind(roster: dict, bindings: dict, plugin_root: Path) -> dict:
    if roster.get("schema") != ROSTER_SCHEMA:
        raise ValueError("roster schema is not " + ROSTER_SCHEMA)
    roster = apply_selection(roster, bindings.get("selection"))
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
    cover = coverage_scope(roster, bindings["coverage"], entries) if bindings.get("coverage") is not None else None
    common_path = plugin_root / COMMON
    common = {"path": COMMON.as_posix(), "sha256": sha256(common_path)}
    gaps: list[str] = list(roster.get("gaps", []))
    jobs: list[dict] = []

    def scope_of(scope_id: str) -> dict:
        scope = scopes.get(scope_id, {})
        return {"input_mode": scope.get("input_mode", default_mode),
                "permissions": scope.get("permissions", "read-only"),
                "output_dir": scope.get("output_dir", output_dir)}

    def sources(members: list[str]) -> tuple[dict, list[str], str]:
        source_bindings: dict[str, dict] = {}
        unbound: list[str] = []
        for member in members:
            entry = entries.get(member)
            path = plugin_root / entry["file"] if entry and entry.get("file") else None
            if path is None or not path.is_file():
                unbound.append(member)
                continue
            source_bindings[member] = {"path": entry["file"], "sha256": sha256(path)}
        digest = hashlib.sha256()
        for member in sorted(source_bindings):
            digest.update(f"{member}\n{source_bindings[member]['sha256']}\n".encode())
        digest.update(f"common\n{common['sha256']}\n".encode())
        return source_bindings, unbound, digest.hexdigest()

    def add_job(role: str, scope_id: str, members: list[str], group: list[dict] | None = None) -> str:
        scope = scope_of(scope_id)
        source_bindings, unbound, body = sources(members)
        for member in unbound:
            gaps.append(f"specialist absent from catalog or role file missing: {member} (job for {role}, scope {scope_id})")
        job_id = f"job-{len(jobs) + 1:02d}"
        output = f"{scope['output_dir'].rstrip('/')}/{job_id}"
        job = {
            "job_id": job_id, "role": role, "specialist_ids": members, "scope_id": scope_id,
            "input_mode": scope["input_mode"], "permissions": scope["permissions"],
            "candidate": candidate, "knowledge_selection": bindings["knowledge_selection"],
            "source_bindings": source_bindings, "body_sha256": body, "output_path": f"{output}.md",
            "status": "unbound" if unbound else "bound", "unbound": unbound,
        }
        if group is not None:
            # A group job concludes on its paths and delivers one JSON reviewer-result.
            job.update(paths=[row["path"] for row in group], bytes=sum(row["size"] for row in group),
                       output_path=f"{output}.json")
        jobs.append(job)
        return job_id

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
    cells: list[dict] = []
    reviewers: dict[str, str] = {}
    for job in plan:
        if cover is None or job["scope_id"] != default_scope:
            add_job(job["role"], job["scope_id"], job["members"])
            continue
        # The job becomes one job per group of its open, inventoried files; with none it has no job.
        own = reviewer_cells(cover, job["role"], job["members"])
        cells += own
        reviewers[job["role"]] = sources(job["members"])[2]
        pending = {cell["path"]: cell for cell in own if cell["status"] == "open" and cell["sha256"] is not None}
        groups = []
        for unit in cover["units"]:
            # A given unit keeps its files together; a file already in a group stays in the first one.
            group = [cover["inventory"][path] for path in unit
                     if path in pending and all(path not in [row["path"] for row in g] for g in groups)]
            if group:
                groups.append(group)
        grouped = {row["path"] for group in groups for row in group}
        groups += pack([cover["inventory"][path] for path in pending if path not in grouped], cover["budget"])
        for group in groups:
            job_id = add_job(job["role"], job["scope_id"], job["members"], group)
            for row in group:
                pending[row["path"]]["job_id"] = job_id
    result = {**roster, "schema": SCHEMA, "roster_schema": ROSTER_SCHEMA, "common": common,
              "catalog_sha256": sha256(plugin_root / "plugin.toml"), "jobs": jobs,
              "gaps": list(dict.fromkeys(gaps))}
    if cover is not None:
        result["coverage"] = {"schema": COVERAGE_SCHEMA, "files": cover["files"], "root": cover["root"].as_posix(),
                              "budget": cover["budget"], "reviewers": reviewers, "cells": cells}
    return result


def relative(path: str, root: str) -> str:
    """A reported path as a root-relative POSIX path; one outside the root stays absolute and matches nothing."""
    text = path.replace("\\", "/")
    base = root.replace("\\", "/").rstrip("/") + "/"
    if os.path.normcase(text).startswith(os.path.normcase(base)):
        text = text[len(base):]
    while text.startswith("./"):
        text = text[2:]
    return text


def delivery_problem(job: dict, result) -> str | None:
    """Why a group job's result cannot close its cells, or None when it can."""
    if result is None:
        return "no result file"
    if not isinstance(result, dict):
        return "invalid result: not a JSON object"
    ids = result.get("specialist_ids")
    bound = {"job_id": job["job_id"], "reviewer": job["role"], "scope_id": job["scope_id"],
             "candidate": job["candidate"], "body_sha256": job["body_sha256"]}
    if (any(result.get(key) != value for key, value in bound.items()) or not isinstance(ids, list)
            or sorted(ids, key=str) != sorted(job["specialist_ids"])):
        return "invalid result: bound to another job, reviewer, members, scope, candidate or body"
    read, partial = result.get("read"), result.get("partial")
    if (not isinstance(read, list) or not all(isinstance(path, str) for path in read)
            or not isinstance(partial, dict)
            or not all(isinstance(path, str) and isinstance(reason, str) for path, reason in partial.items())):
        return "invalid result: read must list paths and partial map paths to reasons"
    if result.get("status") != "delivered":
        return "failed result"
    rows = [row for row in result.get("member_results") or [] if isinstance(row, dict)]
    for member in job["specialist_ids"]:
        own = [row for row in rows if row.get("specialist_id") == member]
        if len(own) != 1 or own[0].get("status") != "delivered" or own[0].get("coverage") != "complete":
            return f"incomplete checks: {member}"
    return None


def account(prepared: dict, deliveries: dict, root: Path) -> dict:
    """Covered and open cells from each group job's result; unassigned and not-applicable cells keep their state."""
    coverage = prepared.get("coverage")
    if not isinstance(coverage, dict) or not isinstance(coverage.get("cells"), list):
        raise ValueError("the prepared review has no coverage; bind it with coverage")
    base = Path(root).as_posix()
    verdicts = {}
    for job in prepared.get("jobs", []):
        if "paths" not in job:
            continue
        result = deliveries.get(job["job_id"])
        problem = delivery_problem(job, result)
        read = set() if problem else {relative(path, base) for path in result["read"]}
        partial = {} if problem else {relative(path, base): reason for path, reason in result["partial"].items()}
        verdicts[job["job_id"]] = problem, read, partial
    summary = {reviewer: {"covered": 0, "open": 0, "not-applicable": 0} for reviewer in coverage.get("reviewers", {})}
    cells = []
    for cell in coverage["cells"]:
        cell = dict(cell)
        if cell["status"] == "open" and cell.get("job_id") in verdicts:
            problem, read, partial = verdicts[cell["job_id"]]
            if problem:
                cell["note"] = problem
            elif cell["path"] in partial:
                cell["note"] = "partial: " + partial[cell["path"]]
            elif cell["path"] in read:
                cell.update(status="covered", note="")
            else:
                cell["note"] = "not read"
        cells.append(cell)
        summary.setdefault(cell["reviewer"], {"covered": 0, "open": 0, "not-applicable": 0})[cell["status"]] += 1
    return {"schema": COVERAGE_SCHEMA, "cells": cells, "summary": summary}


def load_result(path: Path):
    """A job's result as parsed JSON; None when the file is absent; the error text when it is not JSON."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        return f"unreadable: {error}"


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
    account_parser = sub.add_parser("account")
    account_parser.add_argument("--prepared", required=True)
    account_parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    if args.command == "catalog":
        catalog = load_catalog(args.plugin_root)
        Path(args.out).write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"entries": len(catalog["entries"])}))
        return 0
    if args.command == "account":
        try:
            prepared = json.loads(Path(args.prepared).read_text(encoding="utf-8"))
            root = Path(prepared["coverage"]["root"])
            # Result paths resolve against the prepared root, so the cwd never changes the count.
            deliveries = {job["job_id"]: load_result(root / job["output_path"])
                          for job in prepared.get("jobs", []) if "paths" in job}
            report = account(prepared, deliveries, root)
        except (OSError, KeyError, TypeError, ValueError) as error:
            print(json.dumps({"error": f"cannot account coverage: {error}"}), file=sys.stderr)
            return 2
        Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        unfinished = [cell for cell in report["cells"] if cell["status"] == "open"]
        print(json.dumps({"summary": report["summary"], "open_total": len(unfinished), "open": unfinished[:20]}))
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
