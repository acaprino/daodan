#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""System map of a snapshot: named nodes, flows and areas, verified on the flow links.

A node is a named thing of the system at the level a person names it; its members
are files, symbols, store keys and modules. A node without code (an actor, a device,
an external service or project, a part outside the snapshot) has no members and
cites its evidence. A flow is a named process: its nodes and the arrows between
them, each with the data that passes. References between nodes are by name.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402

SCHEMA = "daodan/system-map/v1"
NODE_TYPES = flows.NODE_TYPES + ("entità",)
POSITIONS = ("internal", "external", "unseen")
FLOW_TYPES = ("funzionale", "operativo", "tecnico", "dati", "hardware")
AREAS = ("accesso e identità", "funzioni principali", "pagamenti e abbonamenti", "dati dell'utente",
         "integrazioni esterne", "comunicazioni", "amministrazione", "esercizio")
ARROW_KINDS = ("chiama", "attiva", "scrive", "legge", "usa", "trasferisce", "stessa informazione")
_MAP_FIELDS = {"schema", "nodes", "flows", "areas", "scope"}
_NODE_FIELDS = {"id", "name", "type", "position", "members", "evidence", "on", "where"}
_FLOW_FIELDS = {"id", "name", "area", "types", "nodes", "arrows", "paths"}
_ARROW_FIELDS = {"from", "to", "data", "kind", "cite"}
_AREA_FIELDS = {"name", "present"}


def key(name: str) -> str:
    """A name as compared: case and accents do not count."""
    plain = unicodedata.normalize("NFKD", str(name).strip())
    return "".join(c for c in plain if not unicodedata.combining(c)).casefold()


def _fields(record, allowed: set, where: str) -> dict:
    if not isinstance(record, dict):
        raise ValueError(f"{where} must be an object")
    unknown = sorted(set(record) - allowed)
    if unknown:
        raise ValueError(f"{where}: unknown field {', '.join(unknown)}")
    return record


def _text(record: dict, field: str, where: str, required: bool = True) -> str | None:
    value = record.get(field)
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise ValueError(f"{where}: {field} must be a short text")
    return value.strip()


def _texts(record: dict, field: str, where: str) -> list[str]:
    value = record.get(field, [])
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f"{where}: {field} must be a list of texts")
    return list(dict.fromkeys(v.strip() for v in value))


def _node(record) -> dict:
    record = _fields(record, _NODE_FIELDS, "a node")
    name = _text(record, "name", "a node")
    where = f"node {name}"
    out = {"name": name}
    if "id" in record:
        out["id"] = _text(record, "id", where)
    out["type"] = record.get("type")
    if out["type"] not in NODE_TYPES:
        raise ValueError(f"{where}: type must be one of {', '.join(NODE_TYPES)}")
    out["position"] = record.get("position", "internal")
    if out["position"] not in POSITIONS:
        raise ValueError(f"{where}: position must be one of {', '.join(POSITIONS)}")
    for field in ("members", "evidence", "on"):
        out[field] = _texts(record, field, where)
    if out["position"] == "internal" and not out["members"]:
        raise ValueError(f"{where}: an internal node has members")
    if out["position"] != "internal" and out["members"]:
        raise ValueError(f"{where}: a node without code has no members; cite the files that bind to it as evidence")
    if out["position"] == "external" and not out["evidence"]:
        raise ValueError(f"{where}: an external node cites its evidence")
    if out["position"] == "unseen":
        out["where"] = _text(record, "where", where)
    elif "where" in record:
        raise ValueError(f"{where}: where belongs to an unseen node")
    return out


def _arrow(record, where: str, names: set[str]) -> dict:
    record = _fields(record, _ARROW_FIELDS, f"{where}: an arrow")
    out = {}
    for end in ("from", "to"):
        out[end] = _text(record, end, f"{where}: an arrow")
        if key(out[end]) not in names:
            raise ValueError(f"{where}: arrow {end} {out[end]} is not a node of the flow")
    out["data"] = _text(record, "data", f"{where}: arrow {out['from']} -> {out['to']}")
    if "kind" in record:
        if record["kind"] not in ARROW_KINDS:
            raise ValueError(f"{where}: arrow kind must be one of {', '.join(ARROW_KINDS)}")
        out["kind"] = record["kind"]
    if "cite" in record:
        out["cite"] = _text(record, "cite", where)
    return out


def _flow(record, nodes: set[str], present: set[str], scope: set[str] | None) -> dict:
    record = _fields(record, _FLOW_FIELDS, "a flow")
    name = _text(record, "name", "a flow")
    where = f"flow {name}"
    out = {"name": name}
    if "id" in record:
        out["id"] = _text(record, "id", where)
    out["area"] = _text(record, "area", where)
    if scope is not None and key(out["area"]) not in scope:
        raise ValueError(f"{where}: area {out['area']} is outside the scope")
    if key(out["area"]) not in present:
        raise ValueError(f"{where}: area {out['area']} is not declared present")
    out["types"] = _texts(record, "types", where)
    if not out["types"] or any(t not in FLOW_TYPES for t in out["types"]):
        raise ValueError(f"{where}: types are one or more of {', '.join(FLOW_TYPES)}")
    out["nodes"] = _texts(record, "nodes", where)
    missing = [n for n in out["nodes"] if key(n) not in nodes]
    if missing:
        raise ValueError(f"{where}: nodes {', '.join(missing)} are not in the map")
    arrows = record.get("arrows", [])
    if not isinstance(arrows, list):
        raise ValueError(f"{where}: arrows must be a list")
    inside = {key(n) for n in out["nodes"]}
    out["arrows"] = [_arrow(arrow, where, inside) for arrow in arrows]
    out["paths"] = _texts(record, "paths", where)
    return out


def validate(value: object) -> dict:
    """The proposal in its normal form, or a ValueError that names the wrong field."""
    value = _fields(value, _MAP_FIELDS, "the system map")
    if value.get("schema", SCHEMA) != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")
    for field in ("nodes", "flows", "areas"):
        if not isinstance(value.get(field, []), list):
            raise ValueError(f"{field} must be a list")
    scope = None
    if "scope" in value:
        scope = _texts(value, "scope", "the system map")
        if not scope:
            raise ValueError("scope names at least one area")
    areas, seen = [], {}
    for record in value.get("areas", []):
        record = _fields(record, _AREA_FIELDS, "an area")
        name = _text(record, "name", "an area")
        if not isinstance(record.get("present"), bool):
            raise ValueError(f"area {name}: present must be true or false")
        if key(name) in seen:
            raise ValueError(f"areas: {name} is declared twice")
        seen[key(name)] = record["present"]
        areas.append({"name": name, "present": record["present"]})
    if scope is None:
        missing = [area for area in AREAS if key(area) not in seen]
        if missing:
            raise ValueError(f"areas: declare {', '.join(missing)} present or absent")
    nodes, names = [], {}
    for record in value.get("nodes", []):
        record = _node(record)
        if key(record["name"]) in names:
            raise ValueError(f"node name {record['name']} repeats {names[key(record['name'])]}")
        names[key(record["name"])] = record["name"]
        nodes.append(record)
    for record in nodes:
        missing = [n for n in record["on"] if key(n) not in names]
        if missing:
            raise ValueError(f"node {record['name']}: on names {', '.join(missing)}, not in the map")
    present = {name for name, flag in seen.items() if flag}
    flow_list, flow_names = [], set()
    for record in value.get("flows", []):
        record = _flow(record, set(names), present, None if scope is None else {key(a) for a in scope})
        if key(record["name"]) in flow_names:
            raise ValueError(f"flow name {record['name']} is repeated")
        flow_names.add(key(record["name"]))
        flow_list.append(record)
    out = {"schema": SCHEMA, "nodes": nodes, "flows": flow_list, "areas": areas}
    if scope is not None:
        out["scope"] = scope
    return out
