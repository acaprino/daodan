"""Canonical architecture decision records: lifecycle, versions, index, scope and drift.

Standard library only. A record is a Markdown file under the ADR directory
(default docs/adr/). Version 1 of a decision is ADR-NNNN-<slug>.md; a later
version N is ADR-NNNN-vN-<slug>.md with the slug of version 1. The front matter
uses a small, documented YAML subset: scalar values, lists of scalars written
as "- item" lines, and the one nested mapping "scope" whose children are lists.

Commands:
  template                         print a skeleton body to fill after the interview
  state       --project PATH       whether the project keeps decision records: active, declined
                                   or undecided, with the foreign record directories and the
                                   project root (the top of the Git work tree owning PATH); writes nothing
  decline     --project PATH       store the user's no: the local Git config, or .daodan/adr-declined
                                   outside Git
  init-index  --project ROOT       clear a stored decline, then create the index, or append its
                                   marked block to a README.md that has none
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
              [--symbols S ...]    list the Accepted, unsuperseded records governing a scope and
                                   the foreign record directories to read as constraints
  promote     --project ROOT --adr ADR-NNNN --sha SHA --expect-digest D
                                   approved Proposed version -> Accepted, supersede what it replaces
  verify      --project ROOT --adr ADR-NNNN --sha SHA --expect-digest D
                                   record that the code at SHA conforms to the Accepted version
  retire      --project ROOT --adr ADR-NNNN --reason TEXT --expect-digest D
                                   Proposed version -> Abandoned
  index       --project ROOT       rewrite the index from the records

propose and promote take --sha unless the project has no commit yet; then the
record carries a null sha.

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
import posixpath
import re
import stat
import subprocess
import sys
import time
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
FRD_INDEX = "docs/frd/README.md"
DECLINE_KEY = "daodan.decisionRecords"
DECLINE_MARKER = ".daodan/adr-declined"
TURN_ON = "Run /daodan:record-decision to turn decision records back on."
FOREIGN_DIRS = ("adr", "adrs", "decisions", "architecture-decisions")
FOREIGN_FILE = re.compile(r"^(?:ADR-)?(\d{4})-.+\.md$")
WALK_DEPTH = 6
WALK_SKIP = ("node_modules", "vendor", "dist", "build", "target", "__pycache__")

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
        sha = front["accepted_at_sha"]
        parts.append(f"Accepted {front['accepted_on']}" + (f" at {sha[:7]}" if sha else " before the first commit"))
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


def daodan_front(text):
    """Whether a text opens with Daodan front matter: a --- block holding the adr_id key."""
    lines = text.replace("\r\n", "\n").split("\n")
    if lines[0] != "---":
        return False
    for line in lines[1:]:
        if line == "---":
            return False
        if line.startswith("adr_id:"):
            return True
    return False


def daodan_record(path):
    """Whether a numbered file is Daodan's; any other is another tool's, read and never written."""
    try:
        with path.open("rb") as handle:
            head = handle.read(65536)
    except OSError:
        return False
    return daodan_front(head.decode("utf-8", errors="replace"))


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
        if FOREIGN_FILE.fullmatch(path.name) and not daodan_record(path):
            continue
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
    # A sha is null only when the project had no commit when the record was proposed or accepted.
    for key in ("proposed_at_sha", "accepted_at_sha", "last_verified_sha"):
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
    if status == "Accepted" and (front["accepted_on"] is None or front["superseded_by"] is not None):
        raise AdrError(f"{where}: an Accepted record carries accepted_on and no superseded_by")
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
        sha = front["accepted_at_sha"]
        lines.append(f"| {link} | {front['title']} | {where} | {len(front['governs_symbols'])} | "
                     + (f"`{sha}` |" if sha else "no commit |"))
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


def has_index(text):
    start, end = text.find(INDEX_START), text.find(INDEX_END)
    return 0 <= start < end


def index_text(directory, records, create=False, adopt=False):
    """The index file regenerated from the records, rendered before any write so a refusal writes nothing.

    Every byte outside the markers is kept. adopt (init-index) appends the marked block to a README.md
    that has none, after its last byte."""
    path = directory / "README.md"
    block = render_index(records)
    if path.is_file():
        text = path.read_bytes().decode("utf-8")
        if has_index(text):
            start, end = text.find(INDEX_START), text.find(INDEX_END)
            return path, text[:start] + block.rstrip("\n") + text[end + len(INDEX_END):]
        if not adopt:
            raise AdrError("README.md lacks the adr-index markers; run init-index to append them")
        return path, text + ("" if not text or text.endswith("\n") else "\n") + "\n" + block
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


def next_identity(records, directory):
    """The number after every Daodan record and every numbered file another tool keeps beside them."""
    numbers = [int(record["front"]["adr_id"][4:]) for record in records.values()]
    if directory.is_dir():
        numbers += [int(match.group(1)) for path in directory.iterdir() if (match := FOREIGN_FILE.fullmatch(path.name))]
    return f"ADR-{(max(numbers) + 1 if numbers else 1):04d}"


def git_author(project):
    try:
        result = subprocess.run(["git", "-C", str(project), "config", "user.name"], capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
    except OSError:
        return "unknown"
    return result.stdout.strip() or "unknown"


# --- project state: active, declined or undecided ---------------------------


def run_git(project, *arguments, deadline=None):
    """One Git command in the project: (exit code, stdout), exit code None when Git cannot run."""
    timeout = None if deadline is None else max(0.1, deadline - time.monotonic())
    try:
        result = subprocess.run(["git", "-C", str(project), *arguments], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=timeout)
    except OSError:
        return None, ""
    except subprocess.TimeoutExpired:
        raise AdrError(f"git {arguments[0]} exceeded the time budget") from None
    return result.returncode, result.stdout


def in_git(project, deadline=None):
    """Whether a Git work tree owns the project. One its enclosing repository ignores is its own root."""
    code, out = run_git(project, "rev-parse", "--is-inside-work-tree", deadline=deadline)
    if code != 0 or out.strip() != "true":
        return False
    code, _ = run_git(project, "check-ignore", "-q", ".", deadline=deadline)
    return code != 0


def has_commit(project):
    return in_git(project) and run_git(project, "rev-parse", "--verify", "--quiet", "HEAD")[0] == 0


def given_sha(project, sha, command):
    """The --sha value. Only a project without a commit may omit it, and its record carries null."""
    if sha is None:
        if has_commit(project):
            raise AdrError(f"{command} requires --sha")
        return None
    if not SHA_PATTERN.fullmatch(sha):
        raise AdrError("sha must be a commit sha")
    return sha


def no_links(path, boundary):
    """Refuse a symbolic link or reparse point between the boundary and the path."""
    for item in (path, *path.parents):
        if item == boundary:
            break
        try:
            metadata = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise AdrError(f"{item.relative_to(boundary).as_posix()} is a link; refusing to write through it")


def candidate_files(project, own, git_owned, deadline=None):
    """Project-relative paths that can reveal decision records: tracked candidates with Git, a bounded walk without."""
    if git_owned:
        pathspecs = [".adr-dir", ":(glob)**/.adr-dir", f":(glob){own}/*",
                     *(f":(glob,icase)**/{name}/*" for name in FOREIGN_DIRS)]
        code, out = run_git(project, "ls-files", "-z", "--", *pathspecs, deadline=deadline)
        if code != 0:
            raise AdrError("git ls-files failed")
        return [path for path in out.split("\0") if path]
    found = []
    for folder, directories, files in os.walk(project):
        if deadline is not None and time.monotonic() > deadline:
            raise AdrError("the project walk exceeded the time budget")
        relative = Path(folder).relative_to(project)
        depth = len(relative.parts)
        directories[:] = [] if depth >= WALK_DEPTH else [
            name for name in directories if not name.startswith(".") and name not in WALK_SKIP]
        found.extend((relative / name).as_posix() for name in files)
    return found


def foreign_dirs(project, files, own):
    """Directories holding another tool's decision records: named by .adr-dir, or by convention.

    The ADR directory own is Daodan's index only when its README.md carries the adr-index markers; it
    is foreign too when it holds a numbered record without Daodan front matter or a README.md without
    the markers. New Daodan records still go there, beside the foreign files."""
    found = set()
    for name in files:
        parent, _, leaf = name.rpartition("/")
        if leaf == ".adr-dir":
            try:
                named = (project / name).read_text(encoding="utf-8").strip().splitlines()
            except (OSError, UnicodeError):
                continue
            target = named[0].strip().replace("\\", "/") if named else ""
            resolved = posixpath.normpath(posixpath.join(parent, target)) if target else ""
            if (resolved and resolved != own and not posixpath.isabs(target) and ":" not in target
                    and resolved != ".." and not resolved.startswith("../") and (project / resolved).is_dir()):
                found.add(resolved)
        elif parent == own:
            if FOREIGN_FILE.fullmatch(leaf) and not daodan_record(project / name):
                found.add(own)
        elif parent.rpartition("/")[2].lower() in FOREIGN_DIRS and FOREIGN_FILE.fullmatch(leaf):
            found.add(parent)
    readme = project / own / "README.md"
    if readme.is_file():
        try:
            if not has_index(readme.read_bytes().decode("utf-8", errors="replace")):
                found.add(own)
        except OSError:
            found.add(own)
    return sorted(found)


def detect_foreign(project, own, git_owned, deadline=None):
    return foreign_dirs(project, candidate_files(project, own, git_owned, deadline), own)


def declined(project, git_owned, deadline=None):
    """A stored no: the local Git config value, or the .daodan/adr-declined marker, read in Git too."""
    if git_owned:
        code, out = run_git(project, "config", "--local", "--get", DECLINE_KEY, deadline=deadline)
        if code == 0 and out.strip() == "declined":
            return True
    return (project / DECLINE_MARKER).is_file()


def project_root(project, deadline=None):
    """(root, git_owned): the top of the Git work tree that owns the path and does not ignore it, else the path."""
    if not in_git(project, deadline):
        return project, False
    code, out = run_git(project, "rev-parse", "--show-toplevel", deadline=deadline)
    if code != 0 or not out.strip():
        raise AdrError("git rev-parse --show-toplevel failed")
    return Path(out.strip()).resolve(), True


def project_state(project, directory=DEFAULT_DIR, deadline=None):
    """Active when records exist (the index, an FRD or foreign records), else declined or undecided."""
    project, _ = adr_dir(project, directory)
    project, git_owned = project_root(project, deadline)
    project, own = adr_dir(project, directory)
    relative = own.relative_to(project).as_posix()
    foreign = detect_foreign(project, relative, git_owned, deadline)
    frd = (project / FRD_INDEX).is_file()
    if (own / "README.md").is_file() or frd or foreign:
        state = "active"
    elif declined(project, git_owned, deadline):
        state = "declined"
    else:
        state = "undecided"
    return {"state": state, "adr_dir": relative, "foreign": foreign, "frd": frd, "project": str(project)}


def clear_decline(project):
    """Forget a stored no, the Git config value and the marker both. True when one was stored."""
    cleared = False
    if in_git(project) and run_git(project, "config", "--local", "--get", DECLINE_KEY)[0] == 0:
        if run_git(project, "config", "--local", "--unset", DECLINE_KEY)[0] != 0:
            raise AdrError(f"git config --local --unset {DECLINE_KEY} failed")
        cleared = True
    marker = project / DECLINE_MARKER
    if marker.is_file():
        no_links(marker, project)
        marker.unlink()
        cleared = True
    return cleared


def command_state(args):
    return project_state(args.project, args.dir)


def command_decline(args):
    project, _ = adr_dir(args.project, args.dir)
    project, git_owned = project_root(project)
    if git_owned:
        if run_git(project, "config", "--local", DECLINE_KEY, "declined")[0] != 0:
            raise AdrError(f"git config --local {DECLINE_KEY} failed")
        stored = f"git config --local {DECLINE_KEY}"
    else:
        root, marker = project / ".daodan", project / DECLINE_MARKER
        no_links(marker, project)
        no_links(root / ".daodan-root", project)
        if root.is_dir() and not (root / ".daodan-root").is_file() and any(root.iterdir()):
            raise AdrError(".daodan must be dedicated and carry .daodan-root")
        root.mkdir(exist_ok=True)
        (root / ".daodan-root").touch(exist_ok=True)
        atomic_write(marker, f"Decision records declined on {date.today().isoformat()}. {TURN_ON}\n")
        stored = DECLINE_MARKER
    return {"state": "declined", "stored": stored, "message": TURN_ON, "project": str(project)}


def chosen(given, inherited):
    return list(inherited if given is None else given)


def command_propose(args):
    project, directory = adr_dir(args.project, args.dir)
    if args.revise and args.slug:
        raise AdrError("propose --revise keeps the slug of version 1; drop --slug")
    if not args.revise and not SLUG_PATTERN.fullmatch(args.slug):
        raise AdrError("slug must be lowercase words joined by single hyphens")
    sha = given_sha(project, args.sha, "propose")
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
            identity, version, slug = next_identity(records, directory), 1, args.slug
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
            "created_from_task": args.task, "proposed_on": date.today().isoformat(), "proposed_at_sha": sha,
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
    project, _ = adr_dir(args.project, args.dir)
    args.sha = given_sha(project, args.sha, "promote")

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
    project, directory = adr_dir(args.project, args.dir)
    records = load_records(directory)
    validate_all(records)
    foreign = detect_foreign(project, directory.relative_to(project).as_posix(), in_git(project))
    return {"active": resolve(records, args.paths or (), args.modules or (), args.domains or (), args.symbols or ()),
            "foreign_records_to_read_as_constraints": foreign}


def command_index(args):
    project, directory = adr_dir(args.project, args.dir)
    initial = args.command == "init-index"
    if initial:
        # Refuse before any change, then clear the stored no before the first write: a failed clear writes nothing.
        records = load_records(directory)
        validate_all(records)
        index_text(directory, records, create=True, adopt=True)
        cleared = clear_decline(project)
    with write_lock(directory, create=initial):
        records = load_records(directory)
        validate_all(records)
        path, text = index_text(directory, records, create=initial, adopt=initial)
        atomic_write(path, text)
    output = {"index": str(path.relative_to(project).as_posix()), "records": len(records)}
    if initial:
        output["decline_cleared"] = cleared
    return output


COMMANDS = {"state": command_state, "decline": command_decline, "init-index": command_index,
            "propose": command_propose, "validate": command_validate, "resolve": command_resolve,
            "promote": command_promote, "verify": command_verify, "retire": command_retire, "index": command_index}
REQUIRED = {"promote": ("adr", "expect_digest"), "verify": ("adr", "sha", "expect_digest"),
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
            required = ("task", "body") + (() if args.revise else ("title", "slug"))
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
