"""Declared and proposed module records: their validation, the proposals ledger
beside the manifest, and the resolution of members and evidence against the
snapshot."""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from module_inventory import _Inventory, _json, _plain, _posix, slug
from snapshot_store import open_snapshot

DECLARED_SCHEMA = "daodan/declared-modules/v1"
LEDGER_SCHEMA = "daodan/module-proposals/v1"
LEDGER_FILE = "proposals.json"
DECLARED_FILE = "codebase-modules.json"
MODULE_KINDS = ("component", "feature")
LOCATIONS = ("internal", "external")
MAX_MEMBERS = 500
MAX_MODULES = 500


def validate_module(record: object) -> dict:
    if not isinstance(record, dict):
        raise ValueError("a module must be an object")
    unknown = set(record) - {"name", "kind", "location", "responsibility", "members", "evidence"}
    if unknown:
        raise ValueError("unknown module fields: " + ", ".join(sorted(unknown)))
    name = record.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError("module name must be a short text")
    kind = record.get("kind")
    if kind not in MODULE_KINDS:
        raise ValueError(f"module {name}: kind is required, one of " + ", ".join(MODULE_KINDS))
    location = record.get("location", LOCATIONS[0])
    if location not in LOCATIONS:
        raise ValueError(f"module {name}: location must be one of " + ", ".join(LOCATIONS))
    if kind == "feature" and location == "external":
        raise ValueError(f"module {name}: a feature is a highlight over internal members, it has no external location")
    responsibility = record.get("responsibility", "")
    if not isinstance(responsibility, str) or len(responsibility) > 1000:
        raise ValueError(f"module {name}: responsibility must be text of at most 1000 characters")
    members = record.get("members") or []
    if location == "external":
        if members:
            raise ValueError(f"module {name}: an external module has no members; cite the files that bind to it as evidence")
    elif (not isinstance(members, list) or not members or len(members) > MAX_MEMBERS
            or any(not isinstance(m, str) or not m.strip() or len(m) > 1000 for m in members)):
        raise ValueError(f"module {name}: members must be 1 to {MAX_MEMBERS} entity ids or paths")
    evidence = record.get("evidence", [])
    if not isinstance(evidence, list) or any(not isinstance(e, str) or not e.strip() or len(e) > 1000 for e in evidence):
        raise ValueError(f"module {name}: evidence must be a list of path or path#heading references")
    return {"name": name.strip(), "kind": kind, "location": location, "responsibility": responsibility.strip(),
            "members": list(dict.fromkeys(m.strip() for m in members)),
            "evidence": list(dict.fromkeys(e.strip() for e in evidence))}


def validate_modules(value: object, *, source: str) -> list[dict]:
    if isinstance(value, dict) and "modules" in value:
        if value.get("schema") not in (None, DECLARED_SCHEMA, LEDGER_SCHEMA):
            raise ValueError(f"{source}: unsupported schema")
        value = value["modules"]
    if not isinstance(value, list) or len(value) > MAX_MODULES:
        raise ValueError(f"{source}: modules must be a list of at most {MAX_MODULES} records")
    records = [validate_module(item) for item in value]
    if len({slug(r["name"]) for r in records}) != len(records):
        raise ValueError(f"{source}: module names must be distinct")
    return records


def ledger_name(manifest: Path) -> Path:
    return Path(manifest).with_name(LEDGER_FILE)


def load_ledger(manifest: Path) -> list[dict]:
    path = ledger_name(manifest)
    _plain(path)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"not a readable proposals ledger: {error}") from error
    if not isinstance(value, dict) or value.get("schema") != LEDGER_SCHEMA:
        raise ValueError("not a proposals ledger of this schema")
    return validate_modules(value, source=LEDGER_FILE)


def write_ledger(manifest: Path, records: list[dict], *, replace: bool = False) -> list[dict]:
    """Record proposals beside the manifest; a same-named proposal replaces the earlier one."""
    manifest = Path(manifest).resolve()
    kept = [] if replace else [r for r in load_ledger(manifest) if slug(r["name"]) not in {slug(x["name"]) for x in records}]
    proposals = sorted([*kept, *records], key=lambda r: slug(r["name"]))
    path = ledger_name(manifest)
    descriptor, name = tempfile.mkstemp(prefix=".proposals-", dir=path.parent)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(_json({"schema": LEDGER_SCHEMA, "modules": proposals}).encode("utf-8"))
    os.replace(name, path)
    return proposals


def _member(inventory: _Inventory, store, text: str) -> dict:
    """One member as the snapshot knows it: a symbol, a file, a directory, or unresolved with the reason."""
    if "::" in text:
        path, symbol = text.split("::", 1)
        path = _posix(path)
        record = {"id": f"{path}::{symbol}", "kind": "symbol", "path": path, "symbol": symbol, "resolved": False}
        if path not in inventory.headers:
            record["reason"] = inventory.absence(path)
            return record
        spec = ((store.get_file(path, semantic=False) or {}).get("symbols") or {}).get(symbol)
        if spec is None:
            record["reason"] = "symbol is not in the snapshot of this file"
            return record
        record.update(resolved=True, start_line=spec.get("start"), end_line=spec.get("end"), hash=spec.get("hash"))
        return record
    path = _posix(text)
    if path in inventory.headers:
        return {"id": path, "kind": "file", "path": path, "resolved": True}
    if path in inventory.directories:
        return {"id": path, "kind": "directory", "path": path, "resolved": True}
    return {"id": path, "kind": "file", "path": path, "resolved": False, "reason": inventory.absence(path)}


def _evidence(inventory: _Inventory, text: str) -> dict:
    path, _, anchor = text.partition("#")
    path = _posix(path)
    if path not in inventory.headers:
        return {"path": path, "line": None, "resolved": False, "reason": inventory.absence(path)}
    record = {"path": path, "line": None, "resolved": True}
    if anchor:
        for number, line in enumerate(inventory.text(path).split("\n"), 1):
            match = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
            if match and slug(re.sub(r"[`*]", "", match.group(1))) == slug(anchor):
                record["line"] = number
                break
        else:
            record.update(resolved=False, reason=f"heading #{anchor} not found in {path}")
    return record


def resolve_members(manifest: Path, texts: list[str]) -> list[dict]:
    """Members as the snapshot knows them, each resolved or with the reason it is not."""
    with open_snapshot(manifest) as store:
        inventory = _Inventory(store)
        return [_member(inventory, store, text) for text in texts]


def resolve_evidence(manifest: Path, texts: list[str]) -> list[dict]:
    """`path` or `path#heading` references, each resolved or with the reason it is not."""
    with open_snapshot(manifest) as store:
        inventory = _Inventory(store)
        return [_evidence(inventory, text) for text in texts]
