"""Evidence-bound functional requirements documents with versions and review states.

Standard library only. Records are JSON files under docs/frd/. Version 1 is
FRD-NNNN-<slug>.json; later versions are FRD-NNNN-vN-<slug>.json. Requirements,
entities and relationships carry stable ids, a review state and exact source
spans. Unicode offsets are Python string offsets into the UTF-8 decoded source.

Commands:
  propose  --project ROOT --title T --slug S --task TASK --sha SHA --data FILE
  propose  --project ROOT --revise FRD-NNNN --task TASK --sha SHA --data FILE
           --expect-digest D [--title T]
  validate --project ROOT [--frd FRD-NNNN]
  merge    --project ROOT --frd FRD-NNNN --data FILE --expect-digest D
  resolve  --project ROOT --frd FRD-NNNN --item ID --status STATE
           --expect-digest D [--data FILE] [--conflict CONFLICT-NNNN]
  promote  --project ROOT --frd FRD-NNNN --sha SHA --expect-digest D
  verify   --project ROOT --frd FRD-NNNN --sha SHA --expect-digest D
  index    --project ROOT

Every command prints JSON. Refusals exit 1 and write nothing. Writes hold
.frd-lock, validate the future state, render the index before the first write,
and replace each file atomically. Every mutation of an existing record requires
its current whole-file SHA-256 through --expect-digest. Calling promote is the
explicit approval act; agents must obtain user approval before calling it.
"""

from __future__ import annotations

import argparse
import contextlib
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
import uuid

ID_PATTERN = re.compile(r"^FRD-(\d{4})$")
FILE_PATTERN = re.compile(r"^(FRD-\d{4})(?:-v([1-9]\d*))?-([a-z0-9]+(?:-[a-z0-9]+)*)\.json$")
SLUG_PATTERN = re.compile(r"^(?!v\d+-)[a-z0-9]+(?:-[a-z0-9]+)*$")
ITEM_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-\d{3,}$")
CONFLICT_PATTERN = re.compile(r"^CONFLICT-\d{4,}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{7,64}$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATUSES = ("Proposed", "Accepted", "Superseded")
ITEM_STATUSES = ("extracted", "verified", "corrected", "rejected")
ENTITY_TYPES = ("PERSON", "ORGANIZATION", "LOCATION")
COLLECTIONS = ("requirements", "entities", "relationships")
DATA_KEYS = set(COLLECTIONS)
RECORD_KEYS = {
    "schema_version", "frd_id", "version", "title", "status", "author", "created_from_task",
    "proposed_on", "proposed_at_sha", "accepted_on", "accepted_at_sha", "last_verified_sha",
    "superseded_by", "requirements", "entities", "relationships", "conflicts",
}
EVIDENCE_KEYS = {"path", "document_sha256", "start", "end", "excerpt"}
DEFAULT_DIR = "docs/frd"
LOCK_NAME = ".frd-lock"
INDEX_START = "<!-- frd-index:start -->"
INDEX_END = "<!-- frd-index:end -->"


class FrdError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise FrdError(message)


def nonempty(value, where):
    require(isinstance(value, str) and bool(value.strip()), f"{where} must be a non-empty string")


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise FrdError(f"{path}: invalid JSON: {error.msg} at line {error.lineno}") from None
    require(isinstance(value, dict), f"{path}: JSON root must be an object")
    return value


def render_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def frd_dir(project, directory):
    project = Path(project).resolve()
    require(project.is_dir(), "Project root must be a directory")
    relative = Path(directory or DEFAULT_DIR)
    require(not relative.is_absolute() and ".." not in relative.parts,
            "FRD directory must be a project-relative path without traversal")
    return project, project / relative


@contextlib.contextmanager
def write_lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / LOCK_NAME
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            holder = lock.read_text(encoding="utf-8").strip()
        except OSError:
            holder = ""
        raise FrdError(f"{LOCK_NAME} is held by {holder or 'another write'}; retry when it ends, "
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


def source_document(project, relative):
    nonempty(relative, "evidence.path")
    require("\\" not in relative, f"evidence.path {relative!r} must use POSIX separators")
    pure = PurePosixPath(relative)
    require(not pure.is_absolute() and not PureWindowsPath(relative).drive
            and ".." not in pure.parts and "." not in pure.parts and relative == pure.as_posix(),
            f"evidence.path {relative!r} must be a normalized project-relative path without traversal")
    candidate = project.joinpath(*pure.parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(project)
    except (OSError, ValueError):
        raise FrdError(f"evidence.path {relative!r} is missing or escapes the project") from None
    require(resolved.is_file(), f"evidence.path {relative!r} is not a file")
    return resolved


def check_evidence(project, evidence, where, fresh=True):
    require(isinstance(evidence, dict), f"{where} must be an object")
    require(set(evidence) == EVIDENCE_KEYS,
            f"{where} keys must be {', '.join(sorted(EVIDENCE_KEYS))}")
    require(isinstance(evidence["document_sha256"], str) and DIGEST_PATTERN.fullmatch(evidence["document_sha256"]),
            f"{where}.document_sha256 must be a lowercase SHA-256")
    start, end = evidence["start"], evidence["end"]
    require(type(start) is int and type(end) is int and 0 <= start < end,
            f"{where} offsets must be integers with 0 <= start < end")
    require(isinstance(evidence["excerpt"], str) and evidence["excerpt"], f"{where}.excerpt must be nonempty")
    if not fresh:
        return
    path = source_document(project, evidence["path"])
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(evidence["document_sha256"] == digest,
            f"{where} has stale document_sha256 for {evidence['path']}: expected {evidence['document_sha256']}, found {digest}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise FrdError(f"{where} source {evidence['path']} is not UTF-8") from None
    require(end <= len(text), f"{where} end exceeds the Unicode length of {evidence['path']}")
    require(text[start:end] == evidence["excerpt"],
            f"{where} excerpt does not match Unicode [{start},{end}) in {evidence['path']}")


def content_of(item):
    if "text" in item:
        return {"text": item["text"]}
    if "name" in item:
        return {"entity_type": item["entity_type"], "name": item["name"]}
    return {"source": item["source"], "target": item["target"], "type": item["type"]}


def check_item(item, collection, where, extraction=False):
    require(isinstance(item, dict), f"{where} must be an object")
    required = {"id", "status", "evidence"}
    if collection == "requirements":
        required.add("text")
    elif collection == "entities":
        required.update(("entity_type", "name"))
    else:
        required.update(("source", "target", "type"))
    require(set(item) == required, f"{where} keys must be {', '.join(sorted(required))}")
    require(isinstance(item["id"], str) and ITEM_PATTERN.fullmatch(item["id"]), f"{where}.id has an invalid format")
    require(item["status"] in ITEM_STATUSES, f"{where}.status must be one of {', '.join(ITEM_STATUSES)}")
    if extraction:
        require(item["status"] == "extracted", f"{where}.status must be extracted in a new extraction")
    if collection == "entities":
        require(item["entity_type"] in ENTITY_TYPES,
                f"{where}.entity_type must be PERSON, ORGANIZATION or LOCATION")
        nonempty(item["name"], f"{where}.name")
    elif collection == "requirements":
        nonempty(item["text"], f"{where}.text")
    else:
        for key in ("source", "target", "type"):
            nonempty(item[key], f"{where}.{key}")
        require(ITEM_PATTERN.fullmatch(item["source"]) and ITEM_PATTERN.fullmatch(item["target"]),
                f"{where} source and target must be entity ids")
    require(isinstance(item["evidence"], list) and item["evidence"], f"{where}.evidence must be a non-empty list")


def check_data(project, data, where="data", extraction=False, fresh=True):
    require(isinstance(data, dict) and set(data) == DATA_KEYS,
            f"{where} must contain exactly requirements, entities and relationships")
    items = {}
    for collection in COLLECTIONS:
        values = data[collection]
        require(isinstance(values, list), f"{where}.{collection} must be a list")
        for index, item in enumerate(values):
            location = f"{where}.{collection}[{index}]"
            check_item(item, collection, location, extraction)
            require(item["id"] not in items, f"{location}.id {item['id']} is duplicated")
            items[item["id"]] = (collection, item)
            for evidence_index, evidence in enumerate(item["evidence"]):
                check_evidence(project, evidence, f"{location}.evidence[{evidence_index}]", fresh=fresh)
    for collection, item in items.values():
        if collection == "relationships":
            for key in ("source", "target"):
                target = items.get(item[key])
                require(target is not None and target[0] == "entities",
                        f"{item['id']}.{key} {item[key]} must name an entity in this FRD")
    require(data["requirements"], f"{where}.requirements must not be empty")
    return items


def normalize_extraction(project, data, where="data"):
    require(isinstance(data, dict) and set(data) == DATA_KEYS,
            f"{where} must contain exactly requirements, entities and relationships")
    normalized = {}
    for collection in COLLECTIONS:
        require(isinstance(data[collection], list), f"{where}.{collection} must be a list")
        normalized[collection] = []
        for source in data[collection]:
            require(isinstance(source, dict), f"{where}.{collection} item must be an object")
            item = dict(source)
            item.setdefault("status", "extracted")
            normalized[collection].append(item)
    check_data(project, normalized, where, extraction=True)
    return normalized


def read_record(path):
    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrdError(f"{path.name}: invalid UTF-8 JSON: {error}") from None
    require(isinstance(data, dict), f"{path.name}: JSON root must be an object")
    return {"path": path, "data": data, "digest": hashlib.sha256(raw).hexdigest()}


def load_records(directory):
    records = {}
    if not directory.is_dir():
        return records
    for path in sorted(directory.glob("FRD-*.json")):
        match = FILE_PATTERN.fullmatch(path.name)
        require(match is not None, f"{path.name}: invalid FRD file name")
        record = read_record(path)
        data = record["data"]
        require(data.get("frd_id") == match.group(1), f"{path.name}: frd_id does not match the file name")
        key = pinned(data)
        require(key not in records, f"{key} appears twice")
        records[key] = record
    return records


def pinned(data):
    return f"{data.get('frd_id')} v{data.get('version')}"


def label(data):
    return data["frd_id"] if data["version"] == 1 else pinned(data)


def versions_of(records, identity):
    return [record for record in records.values() if record["data"].get("frd_id") == identity]


def current(versions, status):
    return next((record for record in versions if record["data"].get("status") == status), None)


def check_record(project, record, fresh=True):
    data, where = record["data"], record["path"].name
    require(set(data) == RECORD_KEYS, f"{where}: record keys do not match schema_version 1")
    require(data["schema_version"] == 1, f"{where}: schema_version must be 1")
    require(isinstance(data["frd_id"], str) and ID_PATTERN.fullmatch(data["frd_id"]), f"{where}: invalid frd_id")
    require(type(data["version"]) is int and data["version"] >= 1, f"{where}: version must be a whole number from 1")
    match = FILE_PATTERN.fullmatch(where)
    require(match.group(2) == (None if data["version"] == 1 else str(data["version"])),
            f"{where}: file name does not match version")
    for key in ("title", "author", "created_from_task"):
        nonempty(data[key], f"{where}.{key}")
    require(data["status"] in STATUSES, f"{where}: status must be Proposed, Accepted or Superseded")
    for key in ("proposed_at_sha",):
        require(isinstance(data[key], str) and SHA_PATTERN.fullmatch(data[key]), f"{where}: {key} must be a commit sha")
    for key in ("accepted_at_sha", "last_verified_sha"):
        require(data[key] is None or (isinstance(data[key], str) and SHA_PATTERN.fullmatch(data[key])),
                f"{where}: {key} must be a commit sha or null")
    for key in ("proposed_on", "accepted_on"):
        value = data[key]
        if value is None:
            require(key == "accepted_on", f"{where}: {key} has an invalid ISO date")
            continue
        require(isinstance(value, str) and DATE_PATTERN.fullmatch(value),
                f"{where}: {key} has an invalid ISO date")
    if data["status"] == "Proposed":
        require(data["accepted_on"] is None and data["accepted_at_sha"] is None
                and data["last_verified_sha"] is None and data["superseded_by"] is None,
                f"{where}: Proposed cannot carry acceptance, verification or supersession fields")
    elif data["status"] == "Accepted":
        require(data["accepted_on"] is not None and data["accepted_at_sha"] is not None and data["superseded_by"] is None,
                f"{where}: Accepted requires acceptance fields and no superseded_by")
    else:
        require(data["accepted_on"] is not None and data["accepted_at_sha"] is not None,
                f"{where}: Superseded retains its acceptance fields")
        successor = data["superseded_by"]
        require(isinstance(successor, str) and re.fullmatch(r"FRD-\d{4} v[1-9]\d*", successor),
                f"{where}: Superseded requires a pinned superseded_by")
    check_data(project, {key: data[key] for key in COLLECTIONS}, where, fresh=fresh)
    require(isinstance(data["conflicts"], list), f"{where}.conflicts must be a list")
    conflict_ids = set()
    item_ids = {item["id"] for key in COLLECTIONS for item in data[key]}
    for index, conflict in enumerate(data["conflicts"]):
        location = f"{where}.conflicts[{index}]"
        require(isinstance(conflict, dict), f"{location} must be an object")
        require(set(conflict) == {"id", "item_id", "existing", "incoming", "status", "resolution"},
                f"{location} keys do not match the conflict schema")
        require(isinstance(conflict["id"], str) and CONFLICT_PATTERN.fullmatch(conflict["id"]),
                f"{location}.id has an invalid format")
        require(conflict["id"] not in conflict_ids, f"{location}.id is duplicated")
        conflict_ids.add(conflict["id"])
        require(isinstance(conflict["item_id"], str) and conflict["item_id"] in item_ids,
                f"{location}.item_id does not name an item")
        require(conflict["status"] in ("open", "resolved"), f"{location}.status must be open or resolved")
        require(conflict["resolution"] is None or isinstance(conflict["resolution"], str),
                f"{location}.resolution must be a string or null")
        require((conflict["status"] == "open") == (conflict["resolution"] is None),
                f"{location}: open conflicts have no resolution; resolved conflicts have one")
        collection = next(key for key in COLLECTIONS for item in data[key] if item["id"] == conflict["item_id"])
        for side in ("existing", "incoming"):
            require(isinstance(conflict[side], dict) and conflict[side].get("id") == conflict["item_id"],
                    f"{location}.{side} must be an item with the conflict item_id")
            check_item(conflict[side], collection, f"{location}.{side}")
            for evidence_index, evidence in enumerate(conflict[side]["evidence"]):
                check_evidence(project, evidence, f"{location}.{side}.evidence[{evidence_index}]", fresh=fresh)


def validate_all(project, records, stale_ok=frozenset()):
    for key, record in records.items():
        check_record(project, record, fresh=key not in stale_ok and record["data"]["status"] != "Superseded")
    for identity in sorted({record["data"]["frd_id"] for record in records.values()}):
        versions = versions_of(records, identity)
        require(sorted(record["data"]["version"] for record in versions) == list(range(1, len(versions) + 1)),
                f"{identity}: versions must run from 1 without gaps")
        for status in ("Accepted", "Proposed"):
            require(sum(record["data"]["status"] == status for record in versions) <= 1,
                    f"{identity}: at most one {status} version is allowed")
        for record in versions:
            data = record["data"]
            if data["status"] == "Superseded":
                successor = records.get(data["superseded_by"])
                require(successor is not None and successor["data"]["status"] == "Accepted",
                        f"{pinned(data)}: superseded_by must name an existing Accepted version")
                require(successor["data"]["version"] > data["version"],
                        f"{pinned(data)}: superseded_by must name a later version")


def record_data(record):
    return {key: record["data"][key] for key in COLLECTIONS}


def all_items(data):
    return {item["id"]: item for collection in COLLECTIONS for item in data[collection]}


def evidence_key(evidence):
    return json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def merge_evidence(existing, incoming):
    result = list(existing)
    seen = {evidence_key(item) for item in result}
    for item in incoming:
        key = evidence_key(item)
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result


def next_identity(records):
    numbers = [int(record["data"]["frd_id"][4:]) for record in records.values()]
    return f"FRD-{(max(numbers) + 1 if numbers else 1):04d}"


def git_author(project):
    import subprocess
    try:
        result = subprocess.run(["git", "-C", str(project), "config", "user.name"], capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
    except OSError:
        return "unknown"
    return result.stdout.strip() or "unknown"


def select(records, identity, status, refusal):
    versions = versions_of(records, identity)
    require(versions, f"{identity} does not exist")
    record = current(versions, status)
    if record is None:
        latest = max(versions, key=lambda item: item["data"]["version"])["data"]
        raise FrdError(f"{pinned(latest)} is {latest['status']}; {refusal}")
    return record


def check_digest(record, expected):
    require(record["digest"] == expected,
            f"{pinned(record['data'])} changed since it was read: expected {expected}, found {record['digest']}")


def render_index(records):
    lines = [INDEX_START, "", "Generated by frd_tool.py. Edit records through the CLI, not this block.", "",
             "| FRD | Version | Title | Status | Requirements | Open conflicts | Verified at |",
             "|---|---:|---|---|---:|---:|---|"]
    ordered = sorted(records.values(), key=lambda record: (record["data"]["frd_id"], record["data"]["version"]))
    if not ordered:
        lines.append("| none | | | | | | |")
    for record in ordered:
        data = record["data"]
        opened = sum(conflict["status"] == "open" for conflict in data["conflicts"])
        link = f"[{data['frd_id']}](<{record['path'].name}>)"
        lines.append(f"| {link} | {data['version']} | {data['title']} | {data['status']} | "
                     f"{len(data['requirements'])} | {opened} | `{data['last_verified_sha'] or ''}` |")
    lines.extend(["", INDEX_END])
    return "\n".join(lines) + "\n"


def index_text(directory, records):
    path = directory / "README.md"
    block = render_index(records)
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        start, end = text.find(INDEX_START), text.find(INDEX_END)
        require(start >= 0 and end >= start, "README.md lacks the frd-index markers")
        return path, text[:start] + block.rstrip("\n") + text[end + len(INDEX_END):]
    return path, ("# Functional requirements documents\n\n"
                  "FRD records bind requirements and domain references to exact current source spans. "
                  "Only explicit promotion accepts a proposed version.\n\n" + block)


def index_matches(directory, records):
    path = directory / "README.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    start, end = text.find(INDEX_START), text.find(INDEX_END)
    return start >= 0 and end >= start and text[start:end + len(INDEX_END)] == render_index(records).rstrip("\n")


def commit(project, directory, records, changed, stale_ok=frozenset()):
    validate_all(project, records, stale_ok=stale_ok)
    path, index = index_text(directory, records)
    rendered = [(record, render_json(record["data"])) for record in changed]
    for record, text in rendered:
        atomic_write(record["path"], text)
        record["digest"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    atomic_write(path, index)


def command_propose(args):
    project, directory = frd_dir(args.project, args.dir)
    if args.sha is not None:
        require(SHA_PATTERN.fullmatch(args.sha), "sha must be a commit sha")
    extraction = normalize_extraction(project, read_json(args.data))
    with write_lock(directory):
        records = load_records(directory)
        validate_all(project, records, stale_ok=frozenset(records))
        if args.revise:
            accepted = select(records, args.revise, "Accepted", "only an Accepted FRD can be revised")
            check_digest(accepted, args.expect_digest)
            require(current(versions_of(records, args.revise), "Proposed") is None,
                    f"{args.revise} already has a Proposed version")
            base = accepted["data"]
            identity = args.revise
            version = max(record["data"]["version"] for record in versions_of(records, identity)) + 1
            slug = FILE_PATTERN.fullmatch(next(record for record in versions_of(records, identity)
                                               if record["data"]["version"] == 1)["path"].name).group(3)
            title = (args.title or base["title"]).strip()
        else:
            require(SLUG_PATTERN.fullmatch(args.slug), "slug must be lowercase words joined by single hyphens")
            identity, version, slug = next_identity(records), 1, args.slug
            title = args.title.strip()
        nonempty(title, "title")
        path = directory / (f"{identity}-{slug}.json" if version == 1 else f"{identity}-v{version}-{slug}.json")
        require(not path.exists(), f"{path.name} already exists")
        data = {
            "schema_version": 1, "frd_id": identity, "version": version, "title": title, "status": "Proposed",
            "author": git_author(project), "created_from_task": args.task,
            "proposed_on": date.today().isoformat(), "proposed_at_sha": args.sha,
            "accepted_on": None, "accepted_at_sha": None, "last_verified_sha": None, "superseded_by": None,
            **extraction, "conflicts": [],
        }
        candidate = {"path": path, "data": data, "digest": None}
        future = {**records, pinned(data): candidate}
        commit(project, directory, future, [candidate], stale_ok=frozenset(records))
    return {"frd_id": identity, "version": version, "status": "Proposed",
            "path": str(path.relative_to(project).as_posix()), "digest": candidate["digest"]}


def mutate(args, status, refusal, change):
    project, directory = frd_dir(args.project, args.dir)
    if getattr(args, "sha", None) is not None:
        require(SHA_PATTERN.fullmatch(args.sha), "sha must be a commit sha")
    with write_lock(directory):
        records = load_records(directory)
        record = select(records, args.frd, status, refusal)
        stale_ok = frozenset(records) - {pinned(record["data"])}
        validate_all(project, records, stale_ok=stale_ok)
        check_digest(record, args.expect_digest)
        changed, output = change(project, record, records)
        commit(project, directory, records, changed, stale_ok=stale_ok)
    return {"frd_id": args.frd, "version": record["data"]["version"], "status": record["data"]["status"],
            "digest": record["digest"], **output}


def command_merge(args):
    extraction = normalize_extraction(project=Path(args.project).resolve(), data=read_json(args.data))

    def change(project, record, records):
        data = record["data"]
        existing_items = all_items(data)
        incoming_items = all_items(extraction)
        open_items = {conflict["item_id"] for conflict in data["conflicts"] if conflict["status"] == "open"}
        added, updated, conflicts = 0, 0, 0
        next_conflict = 1 + max([int(conflict["id"].split("-")[1]) for conflict in data["conflicts"]] or [0])
        for item_id, incoming in incoming_items.items():
            existing = existing_items.get(item_id)
            if existing is None:
                collection = next(key for key in COLLECTIONS if incoming in extraction[key])
                data[collection].append(incoming)
                existing_items[item_id] = incoming
                added += 1
                continue
            if item_id in open_items:
                continue
            if content_of(existing) == content_of(incoming):
                before = len(existing["evidence"])
                existing["evidence"] = merge_evidence(existing["evidence"], incoming["evidence"])
                updated += len(existing["evidence"]) != before
                continue
            conflict = {
                "id": f"CONFLICT-{next_conflict:04d}", "item_id": item_id,
                "existing": json.loads(json.dumps(existing)), "incoming": incoming,
                "status": "open", "resolution": None,
            }
            next_conflict += 1
            data["conflicts"].append(conflict)
            open_items.add(item_id)
            conflicts += 1
        return [record], {"added": added, "evidence_merged": updated, "conflicts_opened": conflicts,
                          "open_conflicts": len(open_items)}

    return mutate(args, "Proposed", "only a Proposed FRD accepts an extraction merge", change)


def command_resolve(args):
    replacement = read_json(args.data) if args.data else None

    def change(project, record, records):
        data = record["data"]
        items = all_items(data)
        require(args.item in items, f"{args.item} does not exist in {args.frd}")
        item = items[args.item]
        conflict = None
        if args.conflict:
            conflict = next((entry for entry in data["conflicts"]
                             if entry["id"] == args.conflict and entry["status"] == "open"), None)
            require(conflict is not None, f"{args.conflict} is not an open conflict")
            require(conflict["item_id"] == args.item, f"{args.conflict} does not concern {args.item}")
        elif any(entry["item_id"] == args.item and entry["status"] == "open" for entry in data["conflicts"]):
            raise FrdError(f"{args.item} has an open conflict; pass --conflict")
        if args.status == "corrected":
            candidate = replacement if replacement is not None else conflict and conflict["incoming"]
            require(candidate is not None, "corrected requires --data, or --conflict to accept its incoming item")
            collection = next(key for key in COLLECTIONS if item in data[key])
            candidate = dict(candidate)
            candidate["status"] = "corrected"
            check_item(candidate, collection, args.item)
            require(candidate["id"] == args.item, f"corrected item id must remain {args.item}")
            if collection == "relationships":
                for key in ("source", "target"):
                    require(candidate[key] in items and items[candidate[key]] in data["entities"],
                            f"{args.item}.{key} must name an entity in this FRD")
            for index, evidence in enumerate(candidate["evidence"]):
                check_evidence(project, evidence, f"{args.item}.evidence[{index}]")
            if conflict and replacement is None:
                candidate["evidence"] = merge_evidence(item["evidence"], candidate["evidence"])
            item.clear()
            item.update(candidate)
            resolution = "corrected"
        else:
            require(replacement is None, "--data is allowed only with --status corrected")
            item["status"] = args.status
            resolution = args.status
        if conflict:
            conflict["status"] = "resolved"
            conflict["resolution"] = resolution
        return [record], {"item": args.item, "item_status": args.status,
                          "conflict": args.conflict, "open_conflicts": sum(
                              entry["status"] == "open" for entry in data["conflicts"])}

    return mutate(args, "Proposed", "only a Proposed FRD is resolved", change)


def command_promote(args):
    def change(project, record, records):
        data = record["data"]
        opened = [conflict["id"] for conflict in data["conflicts"] if conflict["status"] == "open"]
        require(not opened, "unresolved conflicts block promote: " + ", ".join(opened))
        previous = current(versions_of(records, args.frd), "Accepted")
        if data["version"] > 1:
            require(previous is not None, f"{pinned(data)} revises {args.frd}, which has no Accepted version")
        data.update(status="Accepted", accepted_at_sha=args.sha, accepted_on=date.today().isoformat(),
                    last_verified_sha=None)
        changed = [record]
        if previous:
            previous["data"].update(status="Superseded", superseded_by=pinned(data))
            changed.append(previous)
        return changed, {"accepted_at_sha": args.sha,
                         "superseded": [pinned(previous["data"])] if previous else []}

    return mutate(args, "Proposed", "only a Proposed FRD is promoted after explicit user approval", change)


def command_verify(args):
    def change(project, record, records):
        record["data"]["last_verified_sha"] = args.sha
        return [record], {"last_verified_sha": args.sha}

    return mutate(args, "Accepted", "only an Accepted FRD is verified", change)


def command_validate(args):
    project, directory = frd_dir(args.project, args.dir)
    records = load_records(directory)
    if args.frd:
        versions = versions_of(records, args.frd)
        require(versions, f"{args.frd} does not exist")
        validate_all(project, records, stale_ok=frozenset(records))
        output = {"valid": True, "frd_id": args.frd, "evidence_freshness": "not-checked"}
        for status in ("Accepted", "Proposed"):
            record = current(versions, status)
            output[status.lower()] = record and {"version": record["data"]["version"], "digest": record["digest"],
                                                 "file": record["path"].name}
        return output
    validate_all(project, records)
    require(not records and not (directory / "README.md").exists() or index_matches(directory, records),
            "README.md index is stale; run index")
    return {"valid": True, "records": len(records),
            "accepted": sum(record["data"]["status"] == "Accepted" for record in records.values()),
            "open_conflicts": sum(conflict["status"] == "open" for record in records.values()
                                  for conflict in record["data"]["conflicts"])}


def command_index(args):
    project, directory = frd_dir(args.project, args.dir)
    with write_lock(directory):
        records = load_records(directory)
        validate_all(project, records)
        path, text = index_text(directory, records)
        atomic_write(path, text)
    return {"index": str(path.relative_to(project).as_posix()), "records": len(records)}


COMMANDS = {
    "propose": command_propose, "validate": command_validate, "merge": command_merge,
    "resolve": command_resolve, "promote": command_promote, "verify": command_verify, "index": command_index,
}
REQUIRED = {
    "merge": ("frd", "data", "expect_digest"),
    "resolve": ("frd", "item", "status", "expect_digest"),
    "promote": ("frd", "sha", "expect_digest"),
    "verify": ("frd", "sha", "expect_digest"),
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=tuple(COMMANDS))
    parser.add_argument("--project", type=Path)
    parser.add_argument("--dir", default=DEFAULT_DIR)
    for name in ("--frd", "--revise", "--title", "--slug", "--task", "--sha", "--expect-digest",
                 "--item", "--status", "--conflict"):
        parser.add_argument(name)
    for name in ("--data",):
        parser.add_argument(name, type=Path)
    args = parser.parse_args(argv)
    try:
        require(args.project is not None, "--project is required")
        required = REQUIRED.get(args.command, ())
        if args.command == "propose":
            required = ("task", "sha", "data") + (("revise", "expect_digest") if args.revise else ("title", "slug"))
        missing = [f"--{name.replace('_', '-')}" for name in required if getattr(args, name) is None]
        require(not missing, f"{args.command} requires " + ", ".join(missing))
        if args.command == "resolve":
            require(args.status in ("verified", "corrected", "rejected"),
                    "resolve --status must be verified, corrected or rejected")
        output = COMMANDS[args.command](args)
        output["checked_at"] = datetime.now(timezone.utc).isoformat()
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (FrdError, OSError, UnicodeError) as error:
        print(f"FRD error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
