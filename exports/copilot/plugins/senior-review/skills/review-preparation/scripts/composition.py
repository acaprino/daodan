"""Pure assembly of canonical review obligations. No discovery or dispatch."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import PurePosixPath


def _digest(value):
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _required(roster, entries):
    required = set()

    def expand(identity, scope, trail=()):
        if identity not in entries or identity in trail:
            raise ValueError(f"unknown or cyclic specialist: {identity}")
        members = entries[identity].get("members")
        if members is not None:
            if not members or len(members) != len(set(members)):
                raise ValueError(f"invalid members: {identity}")
            for member in members:
                expand(member, scope, (*trail, identity))
        if members is None or entries[identity].get("kind") == "method-binding":
            required.add((identity, scope))

    rows = roster.get("required_specialists")
    if not isinstance(rows, list) or not rows:
        raise ValueError("composition requires explicit specialist obligations")
    for row in rows:
        if (not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k]
                for k in ("specialist_id", "scope_id")) or not isinstance(row.get("evidence"), list) or not row["evidence"]):
            raise ValueError("invalid specialist obligation")
        expand(row["specialist_id"], row["scope_id"])
    return sorted(required)


def _entries(catalog):
    rows = catalog.get("entries", [])
    entries = {row["id"]: row for row in rows}
    if len(entries) != len(rows):
        raise ValueError("duplicate catalog identity")
    return entries


def compose_jobs(roster: dict, catalog: dict, bindings: dict) -> list[dict]:
    """Bind every required member once; reject stale inputs or an unfit budget.

    Bindings come from preparation's verified installed inventory, never role
    discovery. `text` is the actual host file; roots, references and knowledge
    are revalidated by the coordinator before dispatch against this fingerprint.
    """
    entries = _entries(catalog)
    candidate = roster.get("grounding", {}).get("candidate")
    if not candidate or bindings.get("candidate") != candidate or bindings.get("host") != catalog.get("host"):
        raise ValueError("candidate or host binding mismatch")
    if not bindings.get("knowledge_selection"):
        raise ValueError("prepared knowledge selection fingerprint required")
    limit = bindings.get("max_body_chars")
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("max_body_chars must be positive")
    common = bindings.get("common", [])
    if not isinstance(common, list) or not common or any(not isinstance(item, dict) or not isinstance(item.get("body"), str) or not item["body"] for item in common):
        raise ValueError("prepared common review conventions required once")
    groups = {}
    for identity, scope_id in _required(roster, entries):
        entry = entries[identity]
        bound = bindings.get("roles", {}).get(identity, {})
        scope = bindings.get("scopes", {}).get(scope_id, {})
        if entry.get("kind") not in {"role", "method-binding"}:
            raise ValueError(f"unknown reviewer kind: {identity}")
        if entry["kind"] == "method-binding" and bound.get("skills") != entry.get("skills"):
            raise ValueError(f"unverified method skill binding: {identity}")
        expected = entry.get("host_binding", {})
        if any("/override:" in source for source in entry.get("source_hashes", {})):
            raise ValueError(f"host-specific override needs an explicit composition binding: {identity}")
        if (not isinstance(bound.get("text"), str) or not bound.get("root")
                or expected.get("host") != catalog["host"]
                or bound.get("file") != expected.get("file")
                or _digest(bound["text"]) != expected.get("sha256")
                or any(bound.get(k) != entry.get(k) for k in ("provider", "provider_version", "source_hashes"))):
            raise ValueError(f"unverified provider/body binding: {identity}")
        mode = bound.get("input_mode", scope.get("input_mode"))
        permissions = bound.get("permissions", scope.get("permissions"))
        if not mode or not permissions or not scope.get("output_dir"):
            raise ValueError(f"missing scope/input/permission/output binding: {identity}/{scope_id}")
        if permissions != scope.get("permissions"):
            raise ValueError(f"member permissions differ from the scoped grant: {identity}/{scope_id}")
        directory = scope["output_dir"]
        if not isinstance(directory, str) or ":" in directory or PurePosixPath(directory.replace("\\", "/")).is_absolute() or ".." in PurePosixPath(directory.replace("\\", "/")).parts:
            raise ValueError("output directory must stay relative to the owned run")
        if identity.endswith(":premise-auditor") and mode not in {"blind", "full-context", "claim-check"}:
            raise ValueError("premise auditor needs its explicit independent input mode")
        # Only discovery members share a job; lenses and process roles stay alone.
        key = (scope_id, mode, _canonical(permissions), identity if mode != "discovery" else "")
        text = bound["text"]
        if text.startswith("---\n"):
            _, separator, text = text[4:].partition("\n---\n")
            if not separator:
                raise ValueError(f"invalid host role frontmatter: {identity}")
        part = {"id": identity, "owner": entry["provider"], "body": text,
                "operation_scope": entry.get("operation_scope", ""),
                "root_marker": expected.get("root_reference", "${CLAUDE_PLUGIN_ROOT}"),
                "root_reference": bound["root"]}
        groups.setdefault(key, []).append(part)

    jobs = []
    for (scope_id, mode, permissions, _), parts in sorted(groups.items()):
        batches = [[]]
        for part in parts:
            if limit and len(assemble_body([part], common)) > limit:
                raise ValueError(f"budget cannot fit required specialist: {part['id']}")
            if limit and batches[-1] and len(assemble_body([*batches[-1], part], common)) > limit:
                batches.append([])
            batches[-1].append(part)
        for batch in batches:
            body = assemble_body(batch, common)
            members = [part["id"] for part in batch]
            fingerprint = {"candidate": candidate, "scope_id": scope_id, "input_mode": mode,
                           "permissions": json.loads(permissions), "specialist_ids": members,
                           "body_sha256": _digest(body), "knowledge_selection": bindings["knowledge_selection"],
                           "source_bindings": {m: {k: v for k, v in bindings["roles"][m].items() if k != "text"}
                                               for m in members}}
            job_id = "review-" + _digest(_canonical(fingerprint))[7:23]
            jobs.append({"id": job_id, "role": "project-protocol:isolated-worker", **fingerprint,
                         "output_path": bindings["scopes"][scope_id]["output_dir"].rstrip("/\\") + f"/{job_id}.md",
                         "body": body})
    problems = validate_composition(roster, jobs, catalog)
    if problems:
        raise ValueError("; ".join(problems))
    return jobs


def validate_composition(roster: dict, jobs: list[dict], catalog: dict) -> list[str]:
    """Validate the complete plan, separately from incremental dispatch checks."""
    try:
        entries = _entries(catalog)
        required = set(_required(roster, entries))
    except (ValueError, KeyError, TypeError) as error:
        return [str(error)]
    errors, covered, identities = [], [], set()
    if not isinstance(jobs, list) or not roster.get("grounding", {}).get("candidate"):
        return ["composition needs a job array and a bound candidate"]
    for job in jobs:
        fields = ("id", "role", "specialist_ids", "scope_id", "input_mode", "body_sha256", "output_path")
        if not isinstance(job, dict) or not all(job.get(field) for field in fields):
            errors.append("job missing required binding")
            continue
        if any(not isinstance(job[field], str) for field in fields if field != "specialist_ids"):
            errors.append("job identity, scope, mode, digest and output bindings must be strings")
            continue
        if job["id"] in identities:
            errors.append("duplicate job identity: " + job["id"])
        identities.add(job["id"])
        if (not isinstance(job["specialist_ids"], list) or
                any(not isinstance(member, str) or not member for member in job["specialist_ids"])):
            errors.append("job members must be an array of specialist identities")
            continue
        if job["role"] != "project-protocol:isolated-worker" and (job["role"] not in entries or
                sorted(entries[job["role"]].get("members", [job["role"]])) != sorted(job["specialist_ids"])):
            errors.append("job role does not bind its members")
        if job["input_mode"] != "discovery" and len(job["specialist_ids"]) != 1:
            errors.append("independent input mode cannot merge members")
        if "body" in job and (not isinstance(job["body"], str) or _digest(job["body"]) != job["body_sha256"]):
            errors.append("job body digest mismatch")
        if job.get("candidate") != roster.get("grounding", {}).get("candidate"):
            errors.append("job candidate mismatch")
        covered.extend((member, job["scope_id"]) for member in job["specialist_ids"])
    counts = Counter(covered)
    if set(covered) != required:
        errors.append("job members/scopes differ from required obligations")
    if any(count != 1 for count in counts.values()):
        errors.append("required obligation scheduled more than once")
    if roster.get("shape") == "light" and len(jobs) != 1:
        errors.append("light review requires exactly one discovery; incomplete, use branch review")
    return errors


def assemble_body(parts: list[dict], common: list[dict]) -> str:
    """Keep domain prose intact; supply shared conventions once per assignment."""
    output = []
    for item in common:
        if item["body"] not in output:
            output.append(item["body"])
    shared = ("Apply the common review conventions and working discipline supplied in the "
              "assignment once. Missing required brief inputs fail the assignment.")
    if not common:
        output.append(shared)
    for part in parts:
        body = part["body"].replace(shared, "")
        for match in re.findall(r'<daodan_host_binding\b[^>]*>.*?</daodan_host_binding>', body, re.DOTALL):
            if not any(match in item for item in output):
                output.append(match)
            body = body.replace(match, "")
        marker = part.get("root_marker", "${CLAUDE_PLUGIN_ROOT}")
        body = re.sub(
            r'Read `' + re.escape(marker) + r'/skills/review-quality-gates/references/reviewer-common\.md`\s*'
            r'once per assignment and apply its conventions; reuse them if already supplied\.', "", body)
        # This retained leaf couples the common hook to a taxonomy reference.
        body = body.replace(
            f'Read `{marker}/skills/review-quality-gates/references/reviewer-common.md`\n'
            'once per assignment, reusing supplied conventions, and relevant L1-L8 categories of',
            'Read relevant L1-L8 categories of')
        root = part.get("root_reference", f"<{part['owner']}-plugin-root>")
        operation_scope = part.get("operation_scope", "").strip()
        if operation_scope and operation_scope not in body:
            body = operation_scope + "\n\n" + body
        output.append(
            f"## Specialist `{part['id']}`\n\n"
            f"Provider `{part['owner']}` owns these instructions and unqualified skills. "
            f"Resolve `{root}` from that installed provider's verified location.\n\n"
            + body.replace(marker, root).strip())
    output.append("## Composed delivery\n\nKeep the assigned job, scope, candidate and body digest in the native result. "
                  "Return one member_results entry per specialist: specialist_id, status (delivered or failed), "
                  "coverage (complete or incomplete), findings (canonical finding IDs) and gaps. "
                  "Write each finding once and reference it from every relevant member. "
                  "A clean member still declares its checks and coverage. Missing input or unfinished checks "
                  "leave that member incomplete; a delivered report does not imply successful coverage.")
    return "\n\n".join(output) + "\n"


def main(argv=None) -> int:
    """Read verified installed bodies without copying their text into bindings."""
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("roster", "catalog", "bindings", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        roster, catalog, bindings = [json.loads(path.read_text(encoding="utf-8"))
                                     for path in (args.roster, args.catalog, args.bindings)]
        for bound in bindings.get("roles", {}).values():
            root = Path(bound["root"]).resolve(strict=True)
            source = (root / bound["file"]).resolve(strict=True)
            if not source.is_relative_to(root):
                raise ValueError("role file escapes its verified provider root")
            bound["text"] = source.read_bytes().decode("utf-8")
        for common in bindings.get("common", []):
            if "file" in common:
                common["body"] = Path(common["file"]).read_bytes().decode("utf-8")
                if _digest(common["body"]) != common.get("sha256"):
                    raise ValueError("common conventions or working discipline changed")
        roster["jobs"] = compose_jobs(roster, catalog, bindings)
        args.out.write_text(json.dumps(roster, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"composition failed: {error}\n")
    print(json.dumps({"jobs": len(roster["jobs"]), "members": sum(len(j["specialist_ids"]) for j in roster["jobs"]),
                      "output": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
