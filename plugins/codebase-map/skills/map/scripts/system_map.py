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

An arrow between two nodes with code is proved by a link from a member of the first
to a member of the second, or by a write and a read of the same store key; it asserts
only what those links say. An arrow with an end without code, or one that says
`stessa informazione`, is declared: it names its kind and cites a `path:line`.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402
import modules  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

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


# ---------------------------------------------------------------- verification

def _module_files(manifest: Path) -> dict[str, list[str]]:
    state = modules.ensure_graph(manifest)
    graph = modules.load_graph(Path(state["graph"]))
    return {modules.slug(m["name"]): m.get("files", []) for m in graph["modules"]}


def _check_nodes(manifest: Path, links: dict, records: list[dict], headers: dict) -> dict[str, dict]:
    """Per node key: status, reason, files, and what it owns (whole files, symbols, other members)."""
    texts = sorted({m for r in records for m in r["members"] if not m.startswith(("store:", "module:"))})
    members = dict(zip(texts, modules.resolve_members(manifest, texts))) if texts else {}
    cited = sorted({e for r in records for e in r["evidence"]})
    evidence = dict(zip(cited, modules.resolve_evidence(manifest, cited))) if cited else {}
    module_files = None
    out = {}
    for record in records:
        problems, whole, symbols, others = [], set(), set(), set()
        for member in record["members"]:
            if member.startswith("store:"):
                others.add(member)
                if member[6:] not in links["stores"]:
                    problems.append(f"member {member}: the links have no store key {member[6:]}")
            elif member.startswith("module:"):
                module_files = _module_files(manifest) if module_files is None else module_files
                found = module_files.get(modules.slug(member[7:]))
                others.add("module:" + modules.slug(member[7:]))
                if found is None:
                    problems.append(f"member {member}: the module graph has no module of that name")
                else:
                    whole.update(found)
            elif not (found := members[member])["resolved"]:
                problems.append(f"member {member}: {found['reason']}")
            elif found["kind"] == "directory":
                whole.update(f for f in headers if modules._inside(f, found["path"]))
            elif found["kind"] == "symbol":
                symbols.add((found["path"], found["symbol"]))
            else:
                whole.add(found["path"])
        problems += [f"evidence {e}: {evidence[e]['reason']}" for e in record["evidence"] if not evidence[e]["resolved"]]
        report = {"name": record["name"], "status": "refused" if problems else "accepted",
                  "files": sorted(whole | {path for path, _ in symbols})}
        if problems:
            report["reason"] = "; ".join(problems)
        out[key(record["name"])] = {"report": report, "record": record, "whole": whole, "symbols": symbols,
                                    "others": others}
    changed = True
    while changed:  # `on` names accepted nodes only
        changed = False
        for item in out.values():
            refused = [n for n in item["record"]["on"] if out[key(n)]["report"]["status"] != "accepted"]
            if refused and item["report"]["status"] == "accepted":
                item["report"].update(status="refused", reason=f"on names refused nodes: {', '.join(refused)}")
                changed = True
    return out


def _owns(item: dict, endpoint: str) -> bool:
    if endpoint.startswith("store:"):
        return endpoint in item["others"]
    if endpoint.startswith("module:"):
        return "module:" + modules.slug(endpoint[7:]) in item["others"]
    path, _, symbol = endpoint.partition("::")
    return path in item["whole"] or any(p == path and (symbol == s or symbol.startswith(s + "."))
                                        for p, s in item["symbols"])


def _proof(edge: dict) -> dict:
    return {name: edge[name] for name in ("from", "to", "type", "site")}


def _check_arrow(arrow: dict, first: dict, second: dict, links: dict, headers: dict) -> dict:
    out = {"from": arrow["from"], "to": arrow["to"], "data": arrow["data"]}
    refused = [i["report"]["name"] for i in (first, second) if i["report"]["status"] != "accepted"]
    if refused:
        return {**out, "status": "refused", "reason": f"nodes refused: {', '.join(refused)}"}
    without_code = [i["report"]["name"] for i in (first, second) if i["record"]["position"] != "internal"]
    if without_code or arrow.get("kind") == "stessa informazione":
        return {**out, **_declared(arrow, first, second, headers)}
    direct = [e for e in links["edges"] if _owns(first, e["from"]) and _owns(second, e["to"])]
    pairs = [(w, r) for w in links["edges"] if w["type"] == "scrive" and _owns(first, w["from"])
             for r in links["edges"] if r["type"] == "legge" and r["from"] == w["to"] and _owns(second, r["to"])]
    if not direct and not pairs:
        return {**out, "status": "refused",
                "reason": f"no link from a member of {arrow['from']} to a member of {arrow['to']}, "
                          "nor a write and a read of the same store key"}
    types = {e["type"] for e in direct} | ({"trasferisce"} if pairs else set())
    via = {e["to"] for e in direct if e["type"] == "scrive"} | {e["from"] for e in direct if e["type"] == "legge"}
    via |= {w["to"] for w, _ in pairs}
    proof = [_proof(e) for e in direct] + [_proof(e) for pair in pairs for e in pair]
    return {**out, "status": "proved", "asserts": [k for k in ARROW_KINDS if k in types],
            "via": sorted(v[6:] for v in via), "proof": list({tuple(p.values()): p for p in proof}.values())}


def _declared(arrow: dict, first: dict, second: dict, headers: dict) -> dict:
    """A declared arrow: its kind and a cited `path:line` that exists, in a file of an end with code."""
    if "kind" not in arrow:
        return {"status": "refused", "reason": "a declared arrow says its kind"}
    if "cite" not in arrow:
        return {"status": "refused", "reason": "a declared arrow cites path:line"}
    path, _, line = arrow["cite"].rpartition(":")
    lines = (headers.get(path) or {}).get("lines") or 0
    if path not in headers or not line.isdigit() or not 1 <= int(line) <= lines:
        return {"status": "refused", "reason": f"cite {arrow['cite']}: no such line in the snapshot"}
    files = set(first["report"]["files"]) | set(second["report"]["files"])
    if files and path not in files:
        return {"status": "refused", "reason": f"cite {arrow['cite']}: {path} is not a file of an end with code"}
    return {"status": "declared", "asserts": [arrow["kind"]], "via": [], "proof": [], "cite": arrow["cite"]}


def verify(manifest: Path, links: dict, value: dict) -> dict:
    """Accept or refuse each node, arrow and flow of a validated proposal, with the reason."""
    manifest = Path(manifest)
    with open_snapshot(manifest) as store:
        headers = dict(store.iter_file_headers_only())
    nodes = _check_nodes(manifest, links, value["nodes"], headers)
    out = []
    for record in value["flows"]:
        arrows = [_check_arrow(a, nodes[key(a["from"])], nodes[key(a["to"])], links, headers) for a in record["arrows"]]
        refused = [n for n in record["nodes"] if nodes[key(n)]["report"]["status"] != "accepted"]
        report = {"name": record["name"], "status": "accepted", "arrows": arrows}
        if refused:
            report.update(status="refused", reason=f"nodes refused: {', '.join(refused)}")
        elif all(a["status"] == "refused" for a in arrows):
            report.update(status="refused", reason="no arrow stands")
        out.append(report)
    return {"nodes": [item["report"] for item in nodes.values()], "flows": out}
