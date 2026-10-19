"""Canonical architecture decision records: lifecycle, index and scope resolution.

Standard library only. A record is a Markdown file under the ADR directory
(default docs/adr/) named ADR-NNNN-<slug>.md with a front matter block in a
small, documented YAML subset: scalar values, lists of scalars written as
"- item" lines, and the one nested mapping "scope" whose children are lists.

Commands:
  template                         print a skeleton body to fill after the interview
  init-index  --project ROOT       create the index when it is missing
  propose     --project ROOT --title T --slug S --task TASK --sha SHA
              --body FILE [--paths P ...] [--modules M ...] [--domains D ...]
              [--symbols S ...] [--supersedes ADR-NNNN ...]
                                   allocate the next id and write a Proposed record
  validate    --project ROOT [--adr ADR-NNNN]
                                   check one record or the whole directory and index
  resolve     --project ROOT [--paths P ...] [--modules M ...] [--domains D ...]
              [--symbols S ...]    list the Accepted, unsuperseded records governing a scope
  promote     --project ROOT --adr ADR-NNNN --sha SHA
                                   Proposed -> Accepted, supersede its targets, rewrite the index
  index       --project ROOT       rewrite the index from the records

Every command prints JSON. A refusal exits 1 with the reason on stderr and
writes nothing: promote validates every file it will touch before the first
write, and each write is atomic.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import json
import os
from pathlib import Path
import re
import sys
import uuid

ID_PATTERN = re.compile(r"^ADR-(\d{4})$")
FILE_PATTERN = re.compile(r"^(ADR-\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{7,64}$")
STATUSES = ("Proposed", "Accepted", "Superseded")
SCOPE_KEYS = ("paths", "modules", "domains")
FRONT_REQUIRED = ("adr_id", "title", "status", "scope", "governs_symbols", "created_from_task",
                  "proposed_at_sha", "accepted_at_sha", "last_verified_sha", "supersedes", "superseded_by")
FRONT_ORDER = FRONT_REQUIRED
SECTIONS = {
    "Verified Interview Examples": re.compile(r"\*\*(EX-\d{3})"),
    "Rejected Alternatives": re.compile(r"\*\*(RA-\d{3})"),
    "Enforceable Invariants": re.compile(r"\*\*(INV-\d{3})"),
}
INDEX_START = "<!-- adr-index:start -->"
INDEX_END = "<!-- adr-index:end -->"
DEFAULT_DIR = "docs/adr"

TEMPLATE = """# {adr_id}: {title}

## Context and Problem Statement

State the situation in the code as it is, with file:line locators, and the
question this record answers.

## Decision Drivers

- The constraints and goals that shaped the choice.

## Decision

The choice, stated so that a reader can tell whether code conforms to it.

## Verified Interview Examples

- **EX-001** (nominal case): Input: `...` -> Expected: `...`
- **EX-002** (boundary case): Input: `...` -> Expected: `...`
- **EX-003** (rejection or error case): Input: `...` -> Expected: `...`

## Rejected Alternatives

- **RA-001**: the alternative, and the reason it must not come back.

## Enforceable Invariants

- **INV-001**: a property the code and its tests must keep.

## Consequences

- What changes in code, tests, documentation and operations.

## Confirmation

- Tests or checks that enforce the examples and invariants.
"""


class AdrError(ValueError):
    pass


# --- front matter -----------------------------------------------------------


def parse_scalar(raw):
    value = raw.strip()
    if value in ("null", "~", ""):
        return None
    if value in ("true", "false"):
        return value == "true"
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_front_matter(text, where):
    if not text.startswith("---\n"):
        raise AdrError(f"{where}: front matter must open with --- on the first line")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise AdrError(f"{where}: front matter is not closed")
    block, body = text[4:end], text[end + 5:]
    data = {}
    current = None      # key receiving "- item" lines
    nested = None       # name of the nested mapping being filled
    for number, line in enumerate(block.split("\n"), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if stripped.startswith("- "):
            if current is None:
                raise AdrError(f"{where}:{number}: list item without a key")
            target = data[nested][current] if nested else data[current]
            target.append(parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            raise AdrError(f"{where}:{number}: expected key: value")
        key, _, raw = stripped.partition(":")
        key = key.strip()
        if indent == 0:
            nested = None
            if raw.strip() == "":
                data[key] = {} if key == "scope" else []
                current = None if key == "scope" else key
                if key == "scope":
                    nested = key
            else:
                data[key] = parse_scalar(raw)
                current = None
        elif nested:
            if raw.strip() == "":
                data[nested][key] = []
                current = key
            else:
                data[nested][key] = parse_scalar(raw)
                current = None
        else:
            raise AdrError(f"{where}:{number}: unexpected indentation")
    return data, body


def format_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if text == "" or any(ch in text for ch in ":#\"'") or text != text.strip() or text in ("null", "true", "false"):
        return json.dumps(text)
    return text


def format_front_matter(data):
    lines = ["---"]
    for key in FRONT_ORDER:
        value = data[key]
        if key == "scope":
            lines.append("scope:")
            for child in SCOPE_KEYS:
                items = value.get(child, [])
                lines.append(f"  {child}:")
                lines.extend(f"    - {format_scalar(item)}" for item in items)
        elif isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {format_scalar(item)}" for item in value)
        else:
            lines.append(f"{key}: {format_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# --- records ----------------------------------------------------------------


def adr_dir(project, directory):
    project = Path(project).resolve()
    if not project.is_dir():
        raise AdrError("Project root must be a directory")
    relative = Path(directory or DEFAULT_DIR)
    if relative.is_absolute() or ".." in relative.parts:
        raise AdrError("ADR directory must be a project-relative path without traversal")
    return project, project / relative


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_record(path):
    text = path.read_text(encoding="utf-8")
    front, body = parse_front_matter(text, path.name)
    return {"path": path, "front": front, "body": body}


def load_records(directory):
    records = {}
    if not directory.is_dir():
        return records
    for path in sorted(directory.glob("ADR-*.md")):
        match = FILE_PATTERN.fullmatch(path.name)
        if not match:
            raise AdrError(f"{path.name}: file name must be ADR-NNNN-<slug>.md")
        record = read_record(path)
        identity = record["front"].get("adr_id")
        if identity != match.group(1):
            raise AdrError(f"{path.name}: adr_id {identity!r} does not match the file name")
        if identity in records:
            raise AdrError(f"{identity} appears twice")
        records[identity] = record
    return records


def check_record(record, records):
    front, body, where = record["front"], record["body"], record["path"].name
    missing = [key for key in FRONT_REQUIRED if key not in front]
    if missing:
        raise AdrError(f"{where}: front matter is missing " + ", ".join(missing))
    identity = front["adr_id"]
    if not isinstance(identity, str) or not ID_PATTERN.fullmatch(identity):
        raise AdrError(f"{where}: adr_id must look like ADR-0001")
    if not isinstance(front["title"], str) or not front["title"].strip():
        raise AdrError(f"{where}: title is required")
    if front["status"] not in STATUSES:
        raise AdrError(f"{where}: status must be one of {', '.join(STATUSES)}")
    scope = front["scope"]
    if not isinstance(scope, dict) or set(scope) - set(SCOPE_KEYS):
        raise AdrError(f"{where}: scope holds only paths, modules and domains")
    for key in SCOPE_KEYS:
        items = scope.get(key, [])
        if not isinstance(items, list) or any(not isinstance(item, str) or not item for item in items):
            raise AdrError(f"{where}: scope.{key} must be a list of strings")
    if not any(scope.get(key) for key in SCOPE_KEYS):
        raise AdrError(f"{where}: scope names at least one path, module or domain")
    for key in ("governs_symbols", "supersedes"):
        items = front[key]
        if not isinstance(items, list) or any(not isinstance(item, str) or not item for item in items):
            raise AdrError(f"{where}: {key} must be a list of strings")
    for key in ("proposed_at_sha",):
        if not isinstance(front[key], str) or not SHA_PATTERN.fullmatch(front[key]):
            raise AdrError(f"{where}: {key} must be a commit sha")
    for key in ("accepted_at_sha", "last_verified_sha"):
        value = front[key]
        if value is not None and (not isinstance(value, str) or not SHA_PATTERN.fullmatch(value)):
            raise AdrError(f"{where}: {key} must be a commit sha or null")
    if not isinstance(front["created_from_task"], str) or not front["created_from_task"].strip():
        raise AdrError(f"{where}: created_from_task names the run or task that produced this record")
    status = front["status"]
    if status == "Proposed" and (front["accepted_at_sha"] is not None or front["superseded_by"] is not None):
        raise AdrError(f"{where}: a Proposed record has no accepted_at_sha and no superseded_by")
    if status == "Accepted" and (front["accepted_at_sha"] is None or front["superseded_by"] is not None):
        raise AdrError(f"{where}: an Accepted record carries accepted_at_sha and no superseded_by")
    if status == "Superseded":
        successor = front["superseded_by"]
        if not isinstance(successor, str) or not ID_PATTERN.fullmatch(successor):
            raise AdrError(f"{where}: a Superseded record names superseded_by")
        if successor not in records:
            raise AdrError(f"{where}: superseded_by {successor} does not exist")
        if identity not in records[successor]["front"].get("supersedes", []):
            raise AdrError(f"{where}: {successor} does not list {identity} in supersedes")
    for target in front["supersedes"]:
        if not ID_PATTERN.fullmatch(target):
            raise AdrError(f"{where}: supersedes entries look like ADR-0001")
        if target == identity:
            raise AdrError(f"{where}: a record cannot supersede itself")
        if target not in records:
            raise AdrError(f"{where}: supersedes {target}, which does not exist")
        if status == "Accepted":
            other = records[target]["front"]
            if other["status"] != "Superseded" or other["superseded_by"] != identity:
                raise AdrError(f"{where}: {target} must be Superseded by {identity} once this record is Accepted")
    check_sections(body, where)
    return front


def check_sections(body, where):
    found = {}
    for heading, pattern in SECTIONS.items():
        marker = f"\n## {heading}\n"
        start = body.find(marker)
        if start < 0 and not body.startswith(marker[1:]):
            raise AdrError(f"{where}: section '## {heading}' is required")
        start = start + len(marker) if start >= 0 else len(marker) - 1
        rest = body[start:]
        stop = rest.find("\n## ")
        section = rest if stop < 0 else rest[:stop]
        ids = pattern.findall(section)
        if not ids:
            raise AdrError(f"{where}: section '## {heading}' needs at least one numbered item")
        if len(set(ids)) != len(ids):
            raise AdrError(f"{where}: section '## {heading}' repeats an identifier")
        if "`...`" in section:
            raise AdrError(f"{where}: section '## {heading}' still holds template placeholders")
        found[heading] = ids
    return found


def check_chains(records):
    """No cycle through supersedes, and no record superseded by a non-Accepted record."""
    for identity, record in records.items():
        seen = {identity}
        current = record["front"].get("superseded_by")
        while current is not None:
            if current in seen:
                raise AdrError(f"{identity}: supersession chain loops through {current}")
            seen.add(current)
            successor = records.get(current)
            if successor is None:
                raise AdrError(f"{identity}: supersession chain reaches missing {current}")
            if successor["front"]["status"] == "Proposed":
                raise AdrError(f"{identity}: superseded by {current}, which is still Proposed")
            current = successor["front"].get("superseded_by")


def validate_all(records):
    for record in records.values():
        check_record(record, records)
    check_chains(records)


# --- index ------------------------------------------------------------------


def render_index(records):
    def row(record):
        front = record["front"]
        scope = front["scope"]
        where = ", ".join(f"`{item}`" for key in SCOPE_KEYS for item in scope.get(key, [])) or "none"
        return front, where

    active = [r for r in records.values() if r["front"]["status"] == "Accepted"]
    proposed = [r for r in records.values() if r["front"]["status"] == "Proposed"]
    superseded = [r for r in records.values() if r["front"]["status"] == "Superseded"]
    lines = [INDEX_START, "",
             "Generated by adr_tool.py from the records in this directory. Edit a record and",
             "run `index`; do not edit this block by hand.", "",
             "## Active decisions", "",
             "| ADR | Title | Governs | Symbols | Accepted at |", "|---|---|---|---:|---|"]
    for record in sorted(active, key=lambda r: r["front"]["adr_id"]):
        front, where = row(record)
        lines.append(f"| [{front['adr_id']}](<{record['path'].name}>) | {front['title']} | {where} | {len(front['governs_symbols'])} | `{front['accepted_at_sha']}` |")
    if not active:
        lines.append("| none | | | | |")
    lines += ["", "## Proposed", "", "| ADR | Title | Governs | From task |", "|---|---|---|---|"]
    for record in sorted(proposed, key=lambda r: r["front"]["adr_id"]):
        front, where = row(record)
        lines.append(f"| [{front['adr_id']}](<{record['path'].name}>) | {front['title']} | {where} | `{front['created_from_task']}` |")
    if not proposed:
        lines.append("| none | | | |")
    lines += ["", "## Superseded", "", "| ADR | Title | Superseded by |", "|---|---|---|"]
    for record in sorted(superseded, key=lambda r: r["front"]["adr_id"]):
        front = record["front"]
        lines.append(f"| [{front['adr_id']}](<{record['path'].name}>) | {front['title']} | {front['superseded_by']} |")
    if not superseded:
        lines.append("| none | | |")
    lines += ["", INDEX_END]
    return "\n".join(lines) + "\n"


def write_index(directory, records, create=False):
    path = directory / "README.md"
    block = render_index(records)
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        start, end = text.find(INDEX_START), text.find(INDEX_END)
        if start < 0 or end < 0 or end < start:
            raise AdrError("README.md lacks the adr-index markers; add them or move the prose elsewhere")
        text = text[:start] + block.rstrip("\n") + text[end + len(INDEX_END):]
    elif create:
        text = ("# Architecture decision records\n\n"
                "One record per decision, named ADR-NNNN-<slug>.md. A record is Proposed when the\n"
                "interview produces it, Accepted when the change that implements it is merged, and\n"
                "Superseded when a later Accepted record names it. Read the active table before\n"
                "touching the paths, modules or domains it governs.\n\n" + block)
    else:
        raise AdrError("README.md does not exist; run init-index first")
    atomic_write(path, text)
    return path


def index_matches(directory, records):
    path = directory / "README.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    start, end = text.find(INDEX_START), text.find(INDEX_END)
    if start < 0 or end < 0:
        return False
    return text[start:end + len(INDEX_END)] == render_index(records).rstrip("\n")


# --- scope resolution -------------------------------------------------------


def path_matches(pattern, candidate):
    candidate = candidate.replace("\\", "/").lstrip("./")
    pattern = pattern.replace("\\", "/").lstrip("./")
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return candidate == prefix or candidate.startswith(prefix + "/")
    if pattern.endswith("/"):
        return candidate.startswith(pattern)
    return fnmatch.fnmatchcase(candidate, pattern) or candidate == pattern


def resolve(records, paths=(), modules=(), domains=(), symbols=()):
    matches = []
    for record in records.values():
        front = record["front"]
        if front["status"] != "Accepted" or front["superseded_by"] is not None:
            continue
        scope = front["scope"]
        reasons = []
        for candidate in paths:
            for pattern in scope.get("paths", []):
                if path_matches(pattern, candidate):
                    reasons.append(f"path {candidate} matches {pattern}")
        for candidate in modules:
            if candidate in scope.get("modules", []):
                reasons.append(f"module {candidate}")
        for candidate in domains:
            if candidate in scope.get("domains", []):
                reasons.append(f"domain {candidate}")
        for candidate in symbols:
            if candidate in front["governs_symbols"]:
                reasons.append(f"symbol {candidate}")
        if reasons:
            matches.append({"adr_id": front["adr_id"], "title": front["title"], "file": record["path"].name,
                            "accepted_at_sha": front["accepted_at_sha"], "reasons": reasons})
    matches.sort(key=lambda item: (-len(item["reasons"]), item["adr_id"]))
    return matches


# --- commands ---------------------------------------------------------------


def next_identity(records):
    numbers = [int(ID_PATTERN.fullmatch(identity).group(1)) for identity in records]
    return f"ADR-{(max(numbers) + 1 if numbers else 1):04d}"


def command_propose(args):
    project, directory = adr_dir(args.project, args.dir)
    if not SLUG_PATTERN.fullmatch(args.slug):
        raise AdrError("slug must be lowercase words joined by single hyphens")
    if not SHA_PATTERN.fullmatch(args.sha):
        raise AdrError("sha must be a commit sha")
    records = load_records(directory)
    validate_all(records)
    identity = next_identity(records)
    body = Path(args.body).read_text(encoding="utf-8")
    if body.startswith("---"):
        raise AdrError("The body file holds the sections only; the tool writes the front matter")
    front = {
        "adr_id": identity, "title": args.title.strip(), "status": "Proposed",
        "scope": {"paths": list(args.paths), "modules": list(args.modules), "domains": list(args.domains)},
        "governs_symbols": list(args.symbols), "created_from_task": args.task, "proposed_at_sha": args.sha,
        "accepted_at_sha": None, "last_verified_sha": None, "supersedes": list(args.supersedes), "superseded_by": None,
    }
    path = directory / f"{identity}-{args.slug}.md"
    if path.exists():
        raise AdrError(f"{path.name} already exists")
    candidate = {"path": path, "front": front, "body": body}
    check_record(candidate, {**records, identity: candidate})
    for target in front["supersedes"]:
        if records[target]["front"]["status"] != "Accepted":
            raise AdrError(f"{target} is not Accepted, so it cannot be superseded")
    heading = f"# {identity}: {front['title']}\n"
    body = body.lstrip("\n")
    if body.startswith("# ADR-NNNN"):
        body = heading + body.split("\n", 1)[1]
    elif not body.startswith("# "):
        body = heading + "\n" + body
    atomic_write(path, format_front_matter(front) + "\n" + body)
    records[identity] = read_record(path)
    write_index(directory, records, create=True)
    return {"adr_id": identity, "path": str(path.relative_to(project).as_posix()), "status": "Proposed"}


def command_promote(args):
    project, directory = adr_dir(args.project, args.dir)
    if not SHA_PATTERN.fullmatch(args.sha):
        raise AdrError("sha must be the merged commit sha")
    records = load_records(directory)
    validate_all(records)
    record = records.get(args.adr)
    if record is None:
        raise AdrError(f"{args.adr} does not exist")
    front = record["front"]
    if front["status"] != "Proposed":
        raise AdrError(f"{args.adr} is {front['status']}, only a Proposed record is promoted")
    targets = []
    for target in front["supersedes"]:
        other = records[target]["front"]
        if other["status"] != "Accepted":
            raise AdrError(f"{target} is {other['status']} and cannot be superseded by {args.adr}")
        targets.append(records[target])
    # Build the whole future state, validate it, then write every file.
    front["status"], front["accepted_at_sha"], front["last_verified_sha"] = "Accepted", args.sha, args.sha
    for target in targets:
        target["front"]["status"], target["front"]["superseded_by"] = "Superseded", args.adr
    validate_all(records)
    for changed in (record, *targets):
        atomic_write(changed["path"], format_front_matter(changed["front"]) + "\n" + changed["body"].lstrip("\n"))
    write_index(directory, records, create=True)
    return {"adr_id": args.adr, "status": "Accepted", "accepted_at_sha": args.sha,
            "superseded": [target["front"]["adr_id"] for target in targets]}


def command_validate(args):
    _, directory = adr_dir(args.project, args.dir)
    records = load_records(directory)
    if args.adr:
        if args.adr not in records:
            raise AdrError(f"{args.adr} does not exist")
        check_record(records[args.adr], records)
        return {"valid": True, "adr_id": args.adr}
    validate_all(records)
    stale = not index_matches(directory, records) if records or (directory / "README.md").is_file() else False
    if stale:
        raise AdrError("README.md index is stale; run index")
    return {"valid": True, "records": len(records),
            "accepted": sum(1 for r in records.values() if r["front"]["status"] == "Accepted")}


def command_resolve(args):
    _, directory = adr_dir(args.project, args.dir)
    records = load_records(directory)
    validate_all(records)
    return {"active": resolve(records, args.paths, args.modules, args.domains, args.symbols)}


def command_index(args):
    project, directory = adr_dir(args.project, args.dir)
    records = load_records(directory)
    validate_all(records)
    path = write_index(directory, records, create=args.command == "init-index")
    return {"index": str(path.relative_to(project).as_posix()), "records": len(records)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("template", "init-index", "propose", "validate", "resolve", "promote", "index"))
    parser.add_argument("--project", type=Path)
    parser.add_argument("--dir", default=DEFAULT_DIR, help="ADR directory relative to the project (default docs/adr)")
    parser.add_argument("--adr")
    parser.add_argument("--title")
    parser.add_argument("--slug")
    parser.add_argument("--task")
    parser.add_argument("--sha")
    parser.add_argument("--body", type=Path)
    parser.add_argument("--paths", nargs="*", default=())
    parser.add_argument("--modules", nargs="*", default=())
    parser.add_argument("--domains", nargs="*", default=())
    parser.add_argument("--symbols", nargs="*", default=())
    parser.add_argument("--supersedes", nargs="*", default=())
    args = parser.parse_args(argv)
    try:
        if args.command == "template":
            print(TEMPLATE.format(adr_id="ADR-NNNN", title="<title>"), end="")
            return 0
        if args.project is None:
            raise AdrError("--project is required")
        if args.command == "propose":
            for name in ("title", "slug", "task", "sha", "body"):
                if getattr(args, name) is None:
                    raise AdrError(f"propose requires --{name}")
            output = command_propose(args)
        elif args.command == "promote":
            if not args.adr or not args.sha:
                raise AdrError("promote requires --adr and --sha")
            output = command_promote(args)
        elif args.command == "validate":
            output = command_validate(args)
        elif args.command == "resolve":
            output = command_resolve(args)
        else:
            output = command_index(args)
        output["checked_at"] = datetime.now(timezone.utc).isoformat()
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (AdrError, OSError, UnicodeError) as error:
        print(f"ADR error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
