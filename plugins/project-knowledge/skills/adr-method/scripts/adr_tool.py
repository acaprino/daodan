"""Canonical architecture decision records: lifecycle, versions, index, scope and drift.

Standard library only. A record is a Markdown file under the ADR directory
(default docs/adr/). Version 1 of a decision is ADR-NNNN-<slug>.md; a later
version N is ADR-NNNN-vN-<slug>.md with the slug of version 1. The front matter
uses a small, documented YAML subset: scalar values, lists of scalars written
as "- item" lines, and the one nested mapping "scope" whose children are lists.

Commands:
  template                         print a skeleton body to fill after the interview
  init-index  --project ROOT       create the index when it is missing
  propose     --project ROOT --title T --slug S --task TASK --sha SHA --body FILE
              [--paths P ...] [--modules M ...] [--domains D ...] [--symbols S ...]
              [--supersedes ADR-NNNN ...] [--depends-on ADR-NNNN ...]
                                   allocate the next id and write version 1 as Proposed
  propose     --project ROOT --revise ADR-NNNN --task TASK --sha SHA --body FILE
              [--title T] [--paths ...] [--modules ...] [--domains ...] [--symbols ...]
              [--supersedes ...] [--depends-on ...]
                                   write the next version of an Accepted decision as Proposed;
                                   scope, symbols and dependencies default to the Accepted version
  validate    --project ROOT [--adr ADR-NNNN] [--sha SHA]
                                   check one decision or the whole directory and index;
                                   --adr prints the digests of its Accepted and Proposed
                                   versions, --sha lists the drifted Accepted records
  resolve     --project ROOT [--paths P ...] [--modules M ...] [--domains D ...]
              [--symbols S ...]    list the Accepted, unsuperseded records governing a scope
  promote     --project ROOT --adr ADR-NNNN --sha SHA --expect-digest D
                                   approved Proposed version -> Accepted, supersede what it replaces
  verify      --project ROOT --adr ADR-NNNN --sha SHA --expect-digest D
                                   record that the code at SHA conforms to the Accepted version
  retire      --project ROOT --adr ADR-NNNN --reason TEXT --expect-digest D
                                   Proposed version -> Abandoned
  index       --project ROOT       rewrite the index from the records

Every command prints JSON. A refusal exits 1 with the reason on stderr and
writes nothing. Every write holds the exclusive lock .adr-lock in the ADR
directory, validates the whole future state and renders the index before the
first write, and writes each file atomically. promote, verify and retire refuse
when the record's digest, the SHA-256 of its file, differs from --expect-digest.
"""

from __future__ import annotations

import argparse
import contextlib
from datetime import date, datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ID_PATTERN = re.compile(r"^ADR-(\d{4})$")
REF_PATTERN = re.compile(r"^(ADR-\d{4})(?: v([1-9]\d*))?$")
FILE_PATTERN = re.compile(r"^(ADR-\d{4})(?:-v([1-9]\d*))?-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
SLUG_PATTERN = re.compile(r"^(?!v\d+-)[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{7,64}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ITEM_PATTERN = re.compile(r"^(?:EX|RA|INV)-\d{3}$")
STATUSES = ("Proposed", "Accepted", "Superseded", "Abandoned")
SCOPE_KEYS = ("paths", "modules", "domains")
FRONT_ORDER = ("adr_id", "version", "title", "status", "author", "scope", "governs_symbols", "depends_on",
               "created_from_task", "proposed_on", "proposed_at_sha", "accepted_on", "accepted_at_sha",
               "last_verified_sha", "retired_on", "retired_reason", "supersedes", "superseded_by", "changes")
SECTIONS = {
    "Verified Interview Examples": re.compile(r"\*\*(EX-\d{3})"),
    "Rejected Alternatives": re.compile(r"\*\*(RA-\d{3})"),
    "Enforceable Invariants": re.compile(r"\*\*(INV-\d{3})"),
}
INDEX_START = "<!-- adr-index:start -->"
INDEX_END = "<!-- adr-index:end -->"
HEADER_START = "<!-- adr-header:start -->"
HEADER_END = "<!-- adr-header:end -->"
HEADER_BLOCK = re.compile(r"\A(# [^\n]*\n)\n<!-- adr-header:start -->\n.*?\n<!-- adr-header:end -->\n", re.S)
DEFAULT_DIR = "docs/adr"
LOCK_NAME = ".adr-lock"

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


def render_header(front):
    """One line from the front matter: version, state, date and author."""
    parts = [f"Version {front['version']}"]
    status = front["status"]
    if status == "Accepted":
        parts.append(f"Accepted {front['accepted_on']} at {front['accepted_at_sha'][:7]}")
    elif status == "Superseded":
        parts.append(f"Superseded by {front['superseded_by']}")
    elif status == "Abandoned":
        parts.append(f"Abandoned {front['retired_on']}: {front['retired_reason']}")
    parts.append(f"{'Proposed' if status == 'Proposed' else 'proposed'} {front['proposed_on']} by {front['author']}")
    return " · ".join(parts)


def compose(front, body):
    """The record file: front matter, the title line, the generated header, then the body."""
    title, _, rest = HEADER_BLOCK.sub(r"\1", body.lstrip("\n"), count=1).partition("\n")
    return f"{format_front_matter(front)}\n{title}\n\n{HEADER_START}\n{render_header(front)}\n{HEADER_END}\n{rest}"


# --- records ----------------------------------------------------------------


def adr_dir(project, directory):
    project = Path(project).resolve()
    if not project.is_dir():
        raise AdrError("Project root must be a directory")
    relative = Path(directory or DEFAULT_DIR)
    if relative.is_absolute() or ".." in relative.parts:
        raise AdrError("ADR directory must be a project-relative path without traversal")
    return project, project / relative


@contextlib.contextmanager
def write_lock(directory, create=False):
    """Hold the exclusive lock of the ADR directory for one write; refuse, naming the holder, when it is taken."""
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    elif not directory.is_dir():
        raise AdrError("The ADR directory does not exist; run init-index first")
    lock = directory / LOCK_NAME
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            holder = lock.read_text(encoding="utf-8").strip()
        except OSError:
            holder = ""
        raise AdrError(f"{LOCK_NAME} is held by {holder or 'another write'}; retry when it ends, "
                       "or delete the file if that process no longer runs") from None
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(f"pid {os.getpid()} since {datetime.now(timezone.utc).isoformat()}\n")
        yield
    finally:
        lock.unlink(missing_ok=True)


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


def pinned(front):
    """The identity of one version, as a run cites it: ADR-0006 v2."""
    return f"{front.get('adr_id')} v{front.get('version')}"


def label(front):
    return front["adr_id"] if front["version"] == 1 else pinned(front)


def read_record(path):
    raw = path.read_bytes()
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    front, body = parse_front_matter(text, path.name)
    version = front.get("version")
    if isinstance(version, str) and version.isascii() and version.isdigit():
        front["version"] = int(version)
    return {"path": path, "front": front, "body": body, "digest": hashlib.sha256(raw).hexdigest()}


def write_record(record):
    text = compose(record["front"], record["body"])
    atomic_write(record["path"], text)
    record["digest"] = hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_records(directory):
    """Every version of every decision, keyed by its pinned identity."""
    records = {}
    if not directory.is_dir():
        return records
    for path in sorted(directory.glob("ADR-*.md")):
        match = FILE_PATTERN.fullmatch(path.name)
        if not match:
            raise AdrError(f"{path.name}: file name must be ADR-NNNN-<slug>.md or ADR-NNNN-vN-<slug>.md")
        record = read_record(path)
        identity = record["front"].get("adr_id")
        if identity != match.group(1):
            raise AdrError(f"{path.name}: adr_id {identity!r} does not match the file name")
        key = pinned(record["front"])
        if key in records:
            raise AdrError(f"{key} appears twice")
        records[key] = record
    return records


def versions_of(records, identity):
    return [record for record in records.values() if record["front"].get("adr_id") == identity]


def current(versions, status):
    return next((record for record in versions if record["front"]["status"] == status), None)


def successor_of(record, records):
    """The record that replaced this one: a later version, or the version of another decision listing it."""
    successor = record["front"].get("superseded_by")
    if successor is None or successor in records:
        return records.get(successor)
    identity = record["front"].get("adr_id")
    return next((other for other in versions_of(records, successor)
                 if identity in other["front"].get("supersedes", [])), None)


def check_fields(record):
    """Check one record on its own: front matter fields, status rules and the machine-checked sections."""
    front, body, where = record["front"], record["body"], record["path"].name
    missing = [key for key in FRONT_ORDER if key not in front]
    if missing:
        raise AdrError(f"{where}: front matter is missing " + ", ".join(missing))
    identity, version = front["adr_id"], front["version"]
    if not isinstance(identity, str) or not ID_PATTERN.fullmatch(identity):
        raise AdrError(f"{where}: adr_id must look like ADR-0001")
    if type(version) is not int or version < 1:
        raise AdrError(f"{where}: version must be a whole number from 1")
    if FILE_PATTERN.fullmatch(where).group(2) != (None if version == 1 else str(version)):
        expected = f"{identity}-<slug>.md" if version == 1 else f"{identity}-v{version}-<slug>.md"
        raise AdrError(f"{where}: version {version} is named {expected}")
    for key, rule in (("title", "title is required"), ("author", "author names who proposed the record"),
                      ("created_from_task", "created_from_task names the run or task that produced this record")):
        if not isinstance(front[key], str) or not front[key].strip():
            raise AdrError(f"{where}: {rule}")
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
    for key in ("governs_symbols", "depends_on", "supersedes", "changes"):
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
    for key in ("proposed_on", "accepted_on", "retired_on"):
        value = front[key]
        if (value is not None or key == "proposed_on") and (not isinstance(value, str) or not DATE_PATTERN.fullmatch(value)):
            raise AdrError(f"{where}: {key} must be an ISO date" + ("" if key == "proposed_on" else " or null"))
    status = front["status"]
    if status == "Proposed" and (front["accepted_at_sha"] is not None or front["accepted_on"] is not None
                                 or front["superseded_by"] is not None):
        raise AdrError(f"{where}: a Proposed record has no accepted_at_sha, accepted_on or superseded_by")
    if status == "Accepted" and (front["accepted_at_sha"] is None or front["accepted_on"] is None
                                 or front["superseded_by"] is not None):
        raise AdrError(f"{where}: an Accepted record carries accepted_at_sha and accepted_on and no superseded_by")
    if status == "Abandoned":
        reason = front["retired_reason"]
        if front["retired_on"] is None or not isinstance(reason, str) or not reason.strip():
            raise AdrError(f"{where}: an Abandoned record carries retired_on and retired_reason")
        if front["accepted_at_sha"] is not None or front["superseded_by"] is not None:
            raise AdrError(f"{where}: an Abandoned record was never accepted and is never superseded")
    elif front["retired_on"] is not None or front["retired_reason"] is not None:
        raise AdrError(f"{where}: only an Abandoned record carries retired_on and retired_reason")
    if status == "Superseded":
        successor = front["superseded_by"]
        match = REF_PATTERN.fullmatch(successor) if isinstance(successor, str) else None
        if match is None:
            raise AdrError(f"{where}: a Superseded record names superseded_by")
        if match.group(2) and (match.group(1) != identity or int(match.group(2)) <= version):
            raise AdrError(f"{where}: superseded_by {successor} is not a later version of {identity}")
    for key in ("supersedes", "depends_on"):
        for target in front[key]:
            if not ID_PATTERN.fullmatch(target):
                raise AdrError(f"{where}: {key} entries look like ADR-0001")
            if target == identity:
                raise AdrError(f"{where}: " + ("a version never supersedes its own decision" if key == "supersedes"
                                               else "a record never depends on its own decision"))
    if any(not ITEM_PATTERN.fullmatch(item) for item in front["changes"]):
        raise AdrError(f"{where}: changes lists EX, RA and INV identifiers")
    if version == 1 and front["changes"]:
        raise AdrError(f"{where}: the first version of a decision records no changes")
    check_sections(body, where)


def check_links(record, records):
    """Check what one record says about others, once every record passed check_fields."""
    front, where = record["front"], record["path"].name
    identity, successor = front["adr_id"], front["superseded_by"]
    if front["status"] == "Superseded":
        if successor not in records and not versions_of(records, successor):
            raise AdrError(f"{where}: superseded_by {successor} does not exist")
        if successor_of(record, records) is None:
            raise AdrError(f"{where}: {successor} does not list {identity} in supersedes")
    for key in ("supersedes", "depends_on"):
        for target in front[key]:
            if not versions_of(records, target):
                raise AdrError(f"{where}: {key} {target}, which does not exist")
    if front["status"] == "Accepted":
        for target in front["supersedes"]:
            others = versions_of(records, target)
            if current(others, "Accepted") or not any(other["front"]["superseded_by"] == identity for other in others):
                raise AdrError(f"{where}: {target} must be Superseded by {identity} once this record is Accepted")


def check_sections(body, where):
    """Check the three machine-checked sections and return the text of each item by identifier."""
    items = {}
    for heading, pattern in SECTIONS.items():
        marker = f"\n## {heading}\n"
        start = body.find(marker)
        if start < 0 and not body.startswith(marker[1:]):
            raise AdrError(f"{where}: section '## {heading}' is required")
        start = start + len(marker) if start >= 0 else len(marker) - 1
        rest = body[start:]
        stop = rest.find("\n## ")
        section = rest if stop < 0 else rest[:stop]
        matches = list(pattern.finditer(section))
        ids = [match.group(1) for match in matches]
        if not ids:
            raise AdrError(f"{where}: section '## {heading}' needs at least one numbered item")
        if len(set(ids)) != len(ids):
            raise AdrError(f"{where}: section '## {heading}' repeats an identifier")
        if "`...`" in section:
            raise AdrError(f"{where}: section '## {heading}' still holds template placeholders")
        starts = [section.rfind("\n", 0, match.start()) + 1 for match in matches] + [len(section)]
        for identity, begin, end in zip(ids, starts, starts[1:]):
            items[identity] = " ".join(section[begin:end].split())
    return items


def check_decisions(records):
    """Versions of a decision run from 1 without gaps, with at most one Accepted and one Proposed."""
    for identity in sorted({record["front"]["adr_id"] for record in records.values()}):
        versions = versions_of(records, identity)
        if sorted(record["front"]["version"] for record in versions) != list(range(1, len(versions) + 1)):
            raise AdrError(f"{identity}: versions must run from 1 without gaps")
        for status in ("Accepted", "Proposed"):
            if sum(record["front"]["status"] == status for record in versions) > 1:
                raise AdrError(f"{identity}: a decision has at most one {status} version")


def check_chains(records):
    """No cycle through superseded_by, and no record replaced by a Proposed or Abandoned one."""
    for key, record in records.items():
        seen = {key}
        successor = successor_of(record, records)
        while successor is not None:
            name = pinned(successor["front"])
            if name in seen:
                raise AdrError(f"{key}: supersession chain loops through {name}")
            seen.add(name)
            if successor["front"]["status"] in ("Proposed", "Abandoned"):
                raise AdrError(f"{key}: superseded by {name}, which is {successor['front']['status']}")
            successor = successor_of(successor, records)


def validate_all(records):
    for record in records.values():
        check_fields(record)
    for record in records.values():
        check_links(record, records)
    check_decisions(records)
    check_chains(records)


# --- index ------------------------------------------------------------------


def render_index(records):
    def row(record):
        front = record["front"]
        scope = front["scope"]
        where = ", ".join(f"`{item}`" for key in SCOPE_KEYS for item in scope.get(key, [])) or "none"
        return front, f"[{label(front)}](<{record['path'].name}>)", where

    def having(status):
        found = [record for record in records.values() if record["front"]["status"] == status]
        return sorted(found, key=lambda record: (record["front"]["adr_id"], record["front"]["version"]))

    lines = [INDEX_START, "",
             "Generated by adr_tool.py from the records in this directory. Edit a record and",
             "run `index`; do not edit this block by hand.", "",
             "## Active decisions", "",
             "| ADR | Title | Governs | Symbols | Accepted at |", "|---|---|---|---:|---|"]
    for record in having("Accepted"):
        front, link, where = row(record)
        lines.append(f"| {link} | {front['title']} | {where} | {len(front['governs_symbols'])} | `{front['accepted_at_sha']}` |")
    if not having("Accepted"):
        lines.append("| none | | | | |")
    lines += ["", "## Proposed", "", "| ADR | Title | Governs | From task |", "|---|---|---|---|"]
    for record in having("Proposed"):
        front, link, where = row(record)
        lines.append(f"| {link} | {front['title']} | {where} | `{front['created_from_task']}` |")
    if not having("Proposed"):
        lines.append("| none | | | |")
    lines += ["", "## Superseded", "", "| ADR | Title | Superseded by |", "|---|---|---|"]
    for record in having("Superseded"):
        front, link, _ = row(record)
        lines.append(f"| {link} | {front['title']} | {front['superseded_by']} |")
    if not having("Superseded"):
        lines.append("| none | | |")
    lines += ["", "## Abandoned", "", "| ADR | Title | Retired on | Reason |", "|---|---|---|---|"]
    for record in having("Abandoned"):
        front, link, _ = row(record)
        lines.append(f"| {link} | {front['title']} | {front['retired_on']} | {front['retired_reason']} |")
    if not having("Abandoned"):
        lines.append("| none | | | |")
    lines += ["", INDEX_END]
    return "\n".join(lines) + "\n"


def index_text(directory, records, create=False):
    """The index file regenerated from the records, rendered before any write so a refusal writes nothing."""
    path = directory / "README.md"
    block = render_index(records)
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        start, end = text.find(INDEX_START), text.find(INDEX_END)
        if start < 0 or end < 0 or end < start:
            raise AdrError("README.md lacks the adr-index markers; add them or move the prose elsewhere")
        return path, text[:start] + block.rstrip("\n") + text[end + len(INDEX_END):]
    if create:
        return path, ("# Architecture decision records\n\n"
                      "One record per version of a decision: ADR-NNNN-<slug>.md, then ADR-NNNN-vN-<slug>.md.\n"
                      "A record is Proposed when the interview produces it, Accepted when the user\n"
                      "approves its text, Superseded when a later version or another Accepted record\n"
                      "replaces it, and Abandoned when it is retired unapproved. Read the active table\n"
                      "before touching the paths, modules or domains it governs.\n\n" + block)
    raise AdrError("README.md does not exist; run init-index first")


def index_matches(directory, records):
    path = directory / "README.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    start, end = text.find(INDEX_START), text.find(INDEX_END)
    if start < 0 or end < 0:
        return False
    return text[start:end + len(INDEX_END)] == render_index(records).rstrip("\n")


def commit(directory, records, changed):
    """Validate the future state, render the index, then write each changed record and the index."""
    validate_all(records)
    path, index = index_text(directory, records, create=True)
    for record in changed:
        write_record(record)
    atomic_write(path, index)


# --- scope resolution and drift ---------------------------------------------


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
            matches.append({"adr_id": front["adr_id"], "version": front["version"], "title": front["title"],
                            "file": record["path"].name, "accepted_at_sha": front["accepted_at_sha"],
                            "digest": record["digest"], "reasons": reasons})
    matches.sort(key=lambda item: (-len(item["reasons"]), item["adr_id"]))
    return matches


def changed_files(project, base, head):
    result = subprocess.run(["git", "-C", str(project), "diff", "--name-only", "--relative", "-z", base, head],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise AdrError(f"git diff --name-only {base} {head} failed: {result.stderr.strip()}")
    return [path for path in result.stdout.split("\0") if path]


def drifted(project, records, sha):
    """Accepted records whose governed files changed since their last verification; never verified is files null."""
    entries, changes = [], {}
    for record in sorted(records, key=lambda record: record["front"]["adr_id"]):
        front = record["front"]
        if front["status"] != "Accepted":
            continue
        entry = {"adr_id": front["adr_id"], "version": front["version"], "files": None}
        base = front["last_verified_sha"]
        if base is not None:
            if base not in changes:
                changes[base] = changed_files(project, base, sha)
            patterns = front["scope"].get("paths", []) + [symbol.split("#", 1)[0].split(":", 1)[-1]
                                                          for symbol in front["governs_symbols"]]
            entry["files"] = [path for path in changes[base] if any(path_matches(item, path) for item in patterns)]
            if not entry["files"]:
                continue
        entries.append(entry)
    return entries


# --- commands ---------------------------------------------------------------


def next_identity(records):
    numbers = [int(record["front"]["adr_id"][4:]) for record in records.values()]
    return f"ADR-{(max(numbers) + 1 if numbers else 1):04d}"


def git_author(project):
    try:
        result = subprocess.run(["git", "-C", str(project), "config", "user.name"], capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
    except OSError:
        return "unknown"
    return result.stdout.strip() or "unknown"


def chosen(given, inherited):
    return list(inherited if given is None else given)


def command_propose(args):
    project, directory = adr_dir(args.project, args.dir)
    if args.revise and args.slug:
        raise AdrError("propose --revise keeps the slug of version 1; drop --slug")
    if not args.revise and not SLUG_PATTERN.fullmatch(args.slug):
        raise AdrError("slug must be lowercase words joined by single hyphens")
    if not SHA_PATTERN.fullmatch(args.sha):
        raise AdrError("sha must be a commit sha")
    body = Path(args.body).read_text(encoding="utf-8")
    if body.startswith("---"):
        raise AdrError("The body file holds the sections only; the tool writes the front matter")
    with write_lock(directory, create=True):
        records = load_records(directory)
        validate_all(records)
        if args.revise:
            versions = versions_of(records, args.revise)
            accepted = current(versions, "Accepted")
            if accepted is None:
                raise AdrError(f"{args.revise} has no Accepted version to revise")
            if current(versions, "Proposed") is not None:
                raise AdrError(f"{pinned(current(versions, 'Proposed')['front'])} is still Proposed: "
                               "a decision has one open version at a time")
            base, identity = accepted["front"], args.revise
            version = max(record["front"]["version"] for record in versions) + 1
            slug = FILE_PATTERN.fullmatch(next(r for r in versions if r["front"]["version"] == 1)["path"].name).group(3)
        else:
            base = {"title": "", "scope": {}, "governs_symbols": [], "depends_on": []}
            identity, version, slug = next_identity(records), 1, args.slug
        title = (args.title or base["title"]).strip()
        path = directory / (f"{identity}-{slug}.md" if version == 1 else f"{identity}-v{version}-{slug}.md")
        if path.exists():
            raise AdrError(f"{path.name} already exists")
        heading = f"# {identity}: {title}\n"
        body = body.lstrip("\n")
        if body.startswith("# ADR-"):
            body = heading + body.partition("\n")[2]
        elif not body.startswith("# "):
            body = heading + "\n" + body
        changes = []
        if args.revise:
            before, after = check_sections(accepted["body"], accepted["path"].name), check_sections(body, path.name)
            changes = sorted(item for item in before.keys() | after.keys() if before.get(item) != after.get(item))
        front = {
            "adr_id": identity, "version": version, "title": title, "status": "Proposed",
            "author": git_author(project),
            "scope": {key: chosen(getattr(args, key), base["scope"].get(key, [])) for key in SCOPE_KEYS},
            "governs_symbols": chosen(args.symbols, base["governs_symbols"]),
            "depends_on": chosen(args.depends_on, base["depends_on"]),
            "created_from_task": args.task, "proposed_on": date.today().isoformat(), "proposed_at_sha": args.sha,
            "accepted_on": None, "accepted_at_sha": None, "last_verified_sha": None,
            "retired_on": None, "retired_reason": None,
            "supersedes": chosen(args.supersedes, ()), "superseded_by": None, "changes": changes,
        }
        candidate = {"path": path, "front": front, "body": body}
        future = {**records, pinned(front): candidate}
        validate_all(future)
        for key in ("supersedes", "depends_on"):
            for target in front[key]:
                if current(versions_of(records, target), "Accepted") is None:
                    raise AdrError(f"{target} is not Accepted, so it cannot be "
                                   + ("superseded" if key == "supersedes" else "a dependency"))
        commit(directory, future, [candidate])
    return {"adr_id": identity, "version": version, "path": str(path.relative_to(project).as_posix()),
            "status": "Proposed", "digest": candidate["digest"], "changes": changes}


def select(versions, adr, status, refusal):
    """The version of a decision in the given status, or a refusal naming the latest version's status."""
    if not versions:
        raise AdrError(f"{adr} does not exist")
    record = current(versions, status)
    if record is None:
        latest = max(versions, key=lambda item: item["front"]["version"])["front"]
        raise AdrError(f"{pinned(latest)} is {latest['status']}, {refusal}")
    return record


def rewrite(args, status, refusal, change):
    """Under the lock: pick the version in that status, check its digest, apply change, validate, write."""
    _, directory = adr_dir(args.project, args.dir)
    if args.sha is not None and not SHA_PATTERN.fullmatch(args.sha):
        raise AdrError("sha must be a commit sha")
    with write_lock(directory):
        records = load_records(directory)
        validate_all(records)
        versions = versions_of(records, args.adr)
        record = select(versions, args.adr, status, refusal)
        if record["digest"] != args.expect_digest:
            raise AdrError(f"{pinned(record['front'])} changed since it was read: "
                           f"expected {args.expect_digest}, found {record['digest']}")
        changed, output = change(record, versions, records)
        commit(directory, records, changed)
    return {"adr_id": args.adr, "version": record["front"]["version"], "status": record["front"]["status"],
            "digest": record["digest"], **output}


def command_promote(args):
    def change(record, versions, records):
        front = record["front"]
        previous = current(versions, "Accepted")
        if front["version"] > 1 and previous is None:
            raise AdrError(f"{pinned(front)} revises {args.adr}, which has no Accepted version left")
        targets = []
        for target in front["supersedes"]:
            others = versions_of(records, target)
            if current(others, "Accepted") is None:
                latest = max(others, key=lambda item: item["front"]["version"])["front"]
                raise AdrError(f"{target} is {latest['status']} and cannot be superseded by {args.adr}")
            targets.append(current(others, "Accepted"))
        front.update(status="Accepted", accepted_at_sha=args.sha, accepted_on=date.today().isoformat())
        replaced = [previous] if previous else []
        for old in replaced:
            old["front"].update(status="Superseded", superseded_by=pinned(front))
        for other in targets:
            other["front"].update(status="Superseded", superseded_by=args.adr)
        gone = {old["front"]["adr_id"] for old in replaced + targets}
        dependents = sorted({item["front"]["adr_id"] for item in records.values()
                             if item["front"]["status"] == "Accepted" and item["front"]["adr_id"] != args.adr
                             and gone & set(item["front"]["depends_on"])})
        output = {"accepted_at_sha": args.sha, "dependents_to_review": dependents,
                  "superseded": [pinned(old["front"]) for old in replaced] + [other["front"]["adr_id"] for other in targets]}
        return [record, *replaced, *targets], output

    return rewrite(args, "Proposed", "only a Proposed record is promoted", change)


def command_verify(args):
    def change(record, versions, records):
        record["front"]["last_verified_sha"] = args.sha
        return [record], {"last_verified_sha": args.sha}

    return rewrite(args, "Accepted", "only an Accepted record is verified", change)


def command_retire(args):
    reason = args.reason.strip()
    if not reason:
        raise AdrError("retire requires a reason")

    def change(record, versions, records):
        record["front"].update(status="Abandoned", retired_on=date.today().isoformat(), retired_reason=reason)
        return [record], {"retired_on": record["front"]["retired_on"], "retired_reason": reason}

    return rewrite(args, "Proposed", "only a Proposed record is retired", change)


def command_validate(args):
    project, directory = adr_dir(args.project, args.dir)
    if args.sha is not None and not SHA_PATTERN.fullmatch(args.sha):
        raise AdrError("sha must be a commit sha")
    records = load_records(directory)
    validate_all(records)
    if args.adr:
        selected = versions_of(records, args.adr)
        if not selected:
            raise AdrError(f"{args.adr} does not exist")
        output = {"valid": True, "adr_id": args.adr}
        for status in ("Accepted", "Proposed"):
            record = current(selected, status)
            output[status.lower()] = record and {"version": record["front"]["version"], "digest": record["digest"],
                                                 "file": record["path"].name}
    else:
        selected = list(records.values())
        stale = not index_matches(directory, records) if records or (directory / "README.md").is_file() else False
        if stale:
            raise AdrError("README.md index is stale; run index")
        output = {"valid": True, "records": len(records),
                  "accepted": sum(1 for r in records.values() if r["front"]["status"] == "Accepted")}
    if args.sha:
        output["drifted"] = drifted(project, selected, args.sha)
    return output


def command_resolve(args):
    _, directory = adr_dir(args.project, args.dir)
    records = load_records(directory)
    validate_all(records)
    return {"active": resolve(records, args.paths or (), args.modules or (), args.domains or (), args.symbols or ())}


def command_index(args):
    project, directory = adr_dir(args.project, args.dir)
    with write_lock(directory, create=args.command == "init-index"):
        records = load_records(directory)
        validate_all(records)
        path, text = index_text(directory, records, create=args.command == "init-index")
        atomic_write(path, text)
    return {"index": str(path.relative_to(project).as_posix()), "records": len(records)}


COMMANDS = {"init-index": command_index, "propose": command_propose, "validate": command_validate,
            "resolve": command_resolve, "promote": command_promote, "verify": command_verify,
            "retire": command_retire, "index": command_index}
REQUIRED = {"promote": ("adr", "sha", "expect_digest"), "verify": ("adr", "sha", "expect_digest"),
            "retire": ("adr", "reason", "expect_digest")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("template", *COMMANDS))
    parser.add_argument("--project", type=Path)
    parser.add_argument("--dir", default=DEFAULT_DIR, help="ADR directory relative to the project (default docs/adr)")
    for name in ("--adr", "--revise", "--title", "--slug", "--task", "--sha", "--reason", "--expect-digest"):
        parser.add_argument(name)
    parser.add_argument("--body", type=Path)
    for name in ("--paths", "--modules", "--domains", "--symbols", "--supersedes", "--depends-on"):
        parser.add_argument(name, nargs="*")
    args = parser.parse_args(argv)
    try:
        if args.command == "template":
            print(TEMPLATE.format(adr_id="ADR-NNNN", title="<title>"), end="")
            return 0
        if args.project is None:
            raise AdrError("--project is required")
        required = REQUIRED.get(args.command, ())
        if args.command == "propose":
            required = ("task", "sha", "body") + (() if args.revise else ("title", "slug"))
        missing = [f"--{name.replace('_', '-')}" for name in required if getattr(args, name) is None]
        if missing:
            raise AdrError(f"{args.command} requires " + ", ".join(missing))
        output = COMMANDS[args.command](args)
        output["checked_at"] = datetime.now(timezone.utc).isoformat()
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (AdrError, OSError, UnicodeError) as error:
        print(f"ADR error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
