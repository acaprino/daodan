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

import json
import sys
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402
import modules  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

SCHEMA = "daodan/system-map/v1"
NODE_TYPES = flows.NODE_TYPES + ("entità",)
POSITIONS = ("internal", "external", "unseen")
FLOW_TYPES = ("funzionale", "operativo", "tecnico", "dati", "hardware")
AREAS = ("accesso e identità", "funzioni principali", "pagamenti e abbonamenti", "dati dell'utente",
         "integrazioni esterne", "comunicazioni", "amministrazione", "esercizio")
ARROW_KINDS = ("chiama", "attiva", "scrive", "legge", "usa", "trasferisce", "stessa informazione")
_MAP_FIELDS = {"schema", "nodes", "flows", "areas", "scope", "remove"}
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


def _flow(record, nodes: set[str], present: set[str] | None, scope: set[str] | None) -> dict:
    record = _fields(record, _FLOW_FIELDS, "a flow")
    name = _text(record, "name", "a flow")
    where = f"flow {name}"
    out = {"name": name}
    if "id" in record:
        out["id"] = _text(record, "id", where)
    out["area"] = _text(record, "area", where)
    if scope is not None and key(out["area"]) not in scope:
        raise ValueError(f"{where}: area {out['area']} is outside the scope")
    if present is not None and key(out["area"]) not in present:
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


def validate(value: object, known: set[str] = frozenset()) -> dict:
    """The proposal in its normal form, or a ValueError that names the wrong field.

    `known` holds the keys of the nodes already in the map, which flows and `on` may name.
    """
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
        missing = [n for n in record["on"] if key(n) not in names and key(n) not in known]
        if missing:
            raise ValueError(f"node {record['name']}: on names {', '.join(missing)}, not in the map")
    present = {name for name, flag in seen.items() if flag} | {key(a) for a in scope or []}
    flow_list, flow_names = [], set()
    for record in value.get("flows", []):
        record = _flow(record, set(names) | set(known), present, None if scope is None else {key(a) for a in scope})
        if key(record["name"]) in flow_names:
            raise ValueError(f"flow name {record['name']} is repeated")
        flow_names.add(key(record["name"]))
        flow_list.append(record)
    remove = _texts(value, "remove", "the system map") if "remove" in value else []
    both = [name for name in remove if key(name) in flow_names]
    if both:
        raise ValueError(f"flow {', '.join(both)} is both proposed and removed")
    out = {"schema": SCHEMA, "nodes": nodes, "flows": flow_list, "areas": areas}
    if remove:
        out["remove"] = remove
    if scope is not None:
        out["scope"] = scope
    return out


# ---------------------------------------------------------------- verification
# Inside, nodes are keyed by an id and flows, arrows and `on` reference ids.

def _inside(path: str, directory: str) -> bool:
    return directory == "." or path == directory or path.startswith(directory + "/")


def _headers(manifest: Path) -> dict:
    with open_snapshot(manifest) as store:
        return dict(store.iter_file_headers_only())


def _module_files(manifest: Path) -> dict[str, list[str]]:
    """Files per module name; empty when the module graph does not build, so the member is refused."""
    try:
        graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    except (OSError, ValueError):
        return {}
    return {modules.slug(m["name"]): m.get("files", []) for m in graph["modules"]}


def _check_nodes(manifest: Path, links: dict, records: list[dict], headers: dict) -> dict[str, dict]:
    """Per node id: its report, its record and what it owns (whole files, symbols, other members)."""
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
                whole.update(f for f in headers if _inside(f, found["path"]))
            elif found["kind"] == "symbol":
                symbols.add((found["path"], found["symbol"]))
            else:
                whole.add(found["path"])
        problems += [f"evidence {e}: {evidence[e]['reason']}" for e in record["evidence"] if not evidence[e]["resolved"]]
        report = {"name": record["name"], "status": "refused" if problems else "accepted",
                  "files": sorted(whole | {path for path, _ in symbols})}
        if problems:
            report["reason"] = "; ".join(problems)
        out[record["id"]] = {"report": report, "record": record, "whole": whole, "symbols": symbols, "others": others}
    changed = True
    while changed:  # `on` names accepted nodes only
        changed = False
        for item in out.values():
            refused = [out[i]["report"]["name"] for i in item["record"]["on"] if out[i]["report"]["status"] != "accepted"]
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


def _check_arrow(arrow: dict, first: dict, second: dict, index: dict, headers: dict) -> dict:
    out = {"from": first["report"]["name"], "to": second["report"]["name"], "data": arrow["data"]}
    refused = [i["report"]["name"] for i in (first, second) if i["report"]["status"] != "accepted"]
    if refused:
        return {**out, "status": "refused", "reason": f"nodes refused: {', '.join(refused)}"}
    if first["record"]["position"] != "internal" or second["record"]["position"] != "internal" \
            or arrow.get("kind") == "stessa informazione":
        return {**out, **_declared(arrow, first, second, headers)}
    a, b = first["record"]["id"], second["record"]["id"]
    owners, readers = index["owners"], index["readers"]
    # A link between two members both nodes hold proves nothing between them.
    direct = [e for e in index["leaving"].get(a, []) if b in owners[e["to"]]
              and not {a, b} <= owners[e["from"]] & owners[e["to"]]]
    pairs = [(w, r) for w in index["leaving"].get(a, []) if w["type"] == "scrive"
             for r in readers.get(w["to"], []) if b in owners[r["to"]] and not {a, b} <= owners[w["from"]] & owners[r["to"]]]
    if not direct and not pairs:
        return {**out, "status": "refused",
                "reason": f"no link from a member of {out['from']} to a member of {out['to']}, "
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
    if not line.isdigit() or not 1 <= int(line) <= lines:
        return {"status": "refused", "reason": f"cite {arrow['cite']}: no such line in the snapshot"}
    files = set(first["report"]["files"]) | set(second["report"]["files"])
    if files and path not in files:
        return {"status": "refused", "reason": f"cite {arrow['cite']}: {path} is not a file of an end with code"}
    return {"status": "declared", "asserts": [arrow["kind"]], "via": [], "proof": [], "cite": arrow["cite"]}


def _verify(manifest: Path, links: dict, nodes: list[dict], flow_records: list[dict], headers: dict):
    """Reports of nodes and flows referenced by id, and the node items they were checked with."""
    items = _check_nodes(manifest, links, nodes, headers)
    endpoints = {end for edge in links["edges"] for end in (edge["from"], edge["to"])}
    index = {"owners": {end: {i for i, item in items.items() if _owns(item, end)} for end in endpoints},
             "leaving": {}, "readers": {}}
    for edge in links["edges"]:
        for owner in index["owners"][edge["from"]]:
            index["leaving"].setdefault(owner, []).append(edge)
        if edge["type"] == "legge":
            index["readers"].setdefault(edge["from"], []).append(edge)
    out = []
    for record in flow_records:
        arrows = [_check_arrow(a, items[a["from"]], items[a["to"]], index, headers) for a in record["arrows"]]
        refused = [items[i]["report"]["name"] for i in record["nodes"] if items[i]["report"]["status"] != "accepted"]
        report = {"name": record["name"], "status": "accepted", "arrows": arrows}
        if refused:
            report.update(status="refused", reason=f"nodes refused: {', '.join(refused)}")
        elif all(a["status"] == "refused" for a in arrows):
            report.update(status="refused", reason="no arrow stands")
        out.append(report)
    return {"nodes": [items[n["id"]]["report"] for n in nodes], "flows": out}, items


def _by_key(value: dict) -> tuple[list[dict], list[dict]]:
    """A validated proposal with each name as its own id."""
    nodes = [{**n, "id": key(n["name"]), "on": [key(o) for o in n["on"]]} for n in value["nodes"]]
    flow_records = [{**f, "nodes": [key(n) for n in f["nodes"]],
                     "arrows": [{**a, "from": key(a["from"]), "to": key(a["to"])} for a in f["arrows"]]}
                    for f in value["flows"]]
    return nodes, flow_records


def verify(manifest: Path, links: dict, value: dict) -> dict:
    """Accept or refuse each node, arrow and flow of a validated proposal, with the reason."""
    manifest = Path(manifest)
    return _verify(manifest, links, *_by_key(value), _headers(manifest))[0]


# ---------------------------------------------------------------- record

FILE = "system-map.json"
DECLARED_FILE = "codebase-system-map.json"
DECLARED_SCHEMA = "daodan/declared-system-map/v1"
_STORED = ("id", "name", "type", "position", "members", "evidence", "on", "where")


def _read_declared(manifest: Path, headers: dict, known: set[str]) -> tuple[dict, list[dict]]:
    """The project's confirmed records, read from the snapshot; a file that does not read is a gap."""
    empty = {"nodes": [], "flows": []}
    if DECLARED_FILE not in headers:
        return empty, []
    with open_snapshot(manifest) as store:
        lines = flows.Source(store).lines(DECLARED_FILE)
    try:
        if lines is None:
            raise ValueError("changed since the snapshot; refresh it")
        value = _fields(json.loads("\n".join(lines)), {"schema", "nodes", "flows"}, DECLARED_FILE)
        if value.get("schema") != DECLARED_SCHEMA:
            raise ValueError(f"schema must be {DECLARED_SCHEMA}")
        nodes = [_node(n) for n in value.get("nodes", [])]
        if any("id" not in n for n in nodes):
            raise ValueError("every declared node has its id")
        ids = known | {n["id"] for n in nodes}
        if unknown := sorted({o for n in nodes for o in n["on"]} - ids):
            raise ValueError(f"on names unknown ids {', '.join(unknown)}")
        flow_records = [_flow(f, ids, None, None) for f in value.get("flows", [])]
        if any("id" not in f for f in flow_records):
            raise ValueError("every declared flow has its id")
        return {"nodes": nodes, "flows": flow_records}, []
    except ValueError as error:
        return empty, [{"path": DECLARED_FILE, "reason": str(error)}]


def _state(manifest: Path, headers: dict) -> dict:
    """The recorded map with the project's declared records over it."""
    path = manifest.with_name(FILE)
    stored = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"nodes": [], "flows": [], "areas": []}
    if stored.get("schema", SCHEMA) != SCHEMA:
        raise ValueError(f"{FILE} is not a system map of this schema")
    nodes = {n["id"]: n for n in stored["nodes"]}
    flow_records = {f["id"]: f for f in stored["flows"]}
    declared, gaps = _read_declared(manifest, headers, set(nodes))
    for record in declared["nodes"]:
        nodes[record["id"]] = {**record, "digests": nodes.get(record["id"], {}).get("digests", {})}
    for record in declared["flows"]:
        before = {(a["from"], a["to"]): a for a in flow_records.get(record["id"], {}).get("arrows", [])}
        flow_records[record["id"]] = {**record, "arrows": [
            {**a, "digests": before.get((a["from"], a["to"]), {}).get("digests", {})} for a in record["arrows"]]}
    return {"nodes": nodes, "flows": flow_records, "areas": {key(a["name"]): a for a in stored.get("areas", [])},
            "declared": {r["id"] for r in declared["nodes"] + declared["flows"]}, "gaps": gaps, "exists": path.is_file()}


def _changed(digests: dict, headers: dict, paths=None) -> list[str]:
    return sorted(f for f, digest in digests.items()
                  if (paths is None or f in paths) and (headers.get(f) or {}).get("raw_hash") != digest)


def _site_file(site: str) -> str:
    path, _, line = site.rpartition(":")
    return path if line.isdigit() else site


LEFT_LISTED = 40  # past this many, a report lists what coverage leaves out by directory; the map keeps the names


def _reported(coverage: dict) -> dict:
    """Coverage as a report gives it back: a long remainder is counted by directory, never dropped."""
    out = {}
    for kind, part in coverage.items():
        if len(part["left"]) <= LEFT_LISTED:
            out[kind] = part
            continue
        by = {}
        for value in part["left"]:
            where = value.split("::", 1)[0].rsplit("/", 1)[0] if "::" in value or kind != "stores" else value.split("/", 1)[0]
            by[where] = by.get(where, 0) + 1
        out[kind] = {"in": part["in"], "of": part["of"], "left_by_directory": dict(sorted(by.items()))}
    return out


def _coverage(links: dict, items: dict, holders: list[str]) -> dict:
    owners = [items[i] for i in dict.fromkeys(holders)]

    def part(values, strip=0):
        inside = {v for v in values if any(_owns(o, v) for o in owners)}
        return {"in": len(inside), "of": len(values), "left": sorted(v[strip:] for v in set(values) - inside)}

    entries = sorted({e["symbol"] for e in links["entries"]})
    return {"entries": part(entries), "stores": part(sorted("store:" + k for k in links["stores"]), 6),
            "routes": part(sorted({e["symbol"] for e in links["entries"] if e["kind"] == "rotta"}))}


def _evaluate(manifest: Path, links: dict, state: dict, headers: dict) -> dict:
    """The map as `load` gives it: verified again, with freshness, correspondences and coverage."""
    nodes, flow_records, declared = state["nodes"], state["flows"], state["declared"]
    report, items = _verify(manifest, links, list(nodes.values()), list(flow_records.values()), headers)
    name = {i: n["name"] for i, n in nodes.items()}
    ok = {"accepted", "confirmed"}

    def status(ident, verified):
        return {"accepted": "confirmed", "refused": "incomplete"}[verified] if ident in declared else verified

    out_nodes = []
    for record, checked in zip(nodes.values(), report["nodes"]):
        state_of = status(record["id"], checked["status"])
        changed = _changed(record.get("digests", {}), headers)
        fresh = state_of in ok and (record["position"] == "internal" or not changed)
        out_nodes.append({**{k: record[k] for k in _STORED if k in record}, "on": [name[o] for o in record["on"]],
                          "status": state_of, **({"reason": checked["reason"]} if "reason" in checked else {}),
                          "files": checked["files"], "fresh": fresh, "changed_files": [] if fresh else changed})
    out_flows, holders = [], []
    for record, checked in zip(flow_records.values(), report["flows"]):
        arrows = []
        for arrow, result in zip(record["arrows"], checked["arrows"]):
            changed = _changed(arrow.get("digests", {}), headers)
            fresh = result["status"] == "proved" or (result["status"] == "declared" and not changed)
            arrows.append({**result, **({"kind": arrow["kind"]} if "kind" in arrow else {}),
                           "fresh": fresh, "changed_files": [] if fresh else changed})
        state_of = status(record["id"], checked["status"])
        if state_of in ok:
            holders += record["nodes"]
        changed = sorted({f for a in arrows for f in a["changed_files"]})
        out_flows.append({"id": record["id"], "name": record["name"], "area": record["area"], "types": record["types"],
                          "nodes": [name[i] for i in record["nodes"]], "arrows": arrows, "paths": record.get("paths", []),
                          "status": state_of, **({"reason": checked["reason"]} if "reason" in checked else {}),
                          "fresh": state_of in ok and all(a["fresh"] for a in arrows), "changed_files": changed})
    correspondences = []
    for record in nodes.values():
        for target in record["on"]:
            cited = {e.split("#")[0] for e in record["evidence"] + nodes[target]["evidence"]}
            changed = sorted(set(_changed(record.get("digests", {}), headers, cited))
                             | set(_changed(nodes[target].get("digests", {}), headers, cited)))
            standing = items[record["id"]]["report"]["status"] == items[target]["report"]["status"] == "accepted"
            correspondences.append({"from": record["name"], "to": nodes[target]["name"],
                                    "status": "declared" if standing else "refused",
                                    "fresh": standing and not changed, "changed_files": changed})
    return {"schema": SCHEMA, "nodes": out_nodes, "flows": out_flows, "areas": list(state["areas"].values()),
            "correspondences": correspondences, "coverage": _coverage(links, items, holders), "gaps": state["gaps"]}


def _digests(paths, headers: dict) -> dict:
    return {f: headers[f]["raw_hash"] for f in sorted(paths) if f in headers}


def _assign(name: str, taken: set[str]) -> str:
    base = modules.slug(name) or "node"
    ident, number = base, 2
    while ident in taken:
        ident, number = f"{base}-{number}", number + 1
    taken.add(ident)
    return ident


def _nested(first: list[str], second: list[str]) -> bool:
    a, b = set(first), set(second)
    return bool(a and b) and (a <= b or b <= a)


def record(manifest: Path, rules: list[dict], value: object) -> dict:
    """Validate and verify a proposal, merge it into the recorded map and write it beside the manifest."""
    manifest = Path(manifest).resolve()
    links = flows.cached_links(manifest, rules)
    headers = _headers(manifest)
    state = _state(manifest, headers)
    nodes, flow_records, declared = state["nodes"], state["flows"], state["declared"]
    before = {**nodes, **flow_records}
    node_names = {key(n["name"]): i for i, n in nodes.items()}
    flow_names = {key(f["name"]): i for i, f in flow_records.items()}
    proposal = validate(value, known=set(node_names) | set(nodes))
    taken = set(nodes) | set(flow_records)
    ident, node_reports, changes = {}, {}, {}

    # Nodes: an id or a current name recalls a node; a new one must not repeat an existing one.
    fresh_nodes = []
    for p in proposal["nodes"]:
        target = p.get("id") or node_names.get(key(p["name"]))
        if "id" in p and p["id"] not in nodes:
            node_reports[key(p["name"])] = {"name": p["name"], "status": "refused", "reason": f"no node has id {p['id']}"}
            ident[key(p["name"])] = None
        elif target in declared:
            node_reports[key(p["name"])] = {"id": target, "name": p["name"], "status": "confirmed",
                                            "reason": f"confirmed by the project; rename it in {DECLARED_FILE}"}
            ident[key(p["name"])] = target
        elif target and node_names.get(key(p["name"]), target) != target:
            node_reports[key(p["name"])] = {"name": p["name"], "status": "refused",
                                            "reason": f"node {node_names[key(p['name'])]} already has this name"}
            ident[key(p["name"])] = None
        elif target:
            ident[key(p["name"])] = target
            changes[target] = p
        else:
            fresh_nodes.append(p)
    current = {i: {**n, **changes.get(i, {})} for i, n in nodes.items()}
    for p in fresh_nodes:
        basis = "members" if p["position"] == "internal" else "evidence"
        twin = next((i for i, n in current.items() if n["type"] == p["type"] and _nested(n[basis], p[basis])), None)
        if twin:
            node_reports[key(p["name"])] = {"name": p["name"], "status": "refused",
                                            "reason": f"repeats node {twin}: the same {basis}, or nested ones"}
            ident[key(p["name"])] = None
        else:
            ident[key(p["name"])] = _assign(p["name"], taken)
            changes[ident[key(p["name"])]] = current[ident[key(p["name"])]] = p

    def resolve(reference: str) -> str | None:
        k = key(reference)
        return ident[k] if k in ident else node_names.get(k) or (reference if reference in nodes else None)

    candidate = dict(nodes)
    for i, p in changes.items():
        on = [resolve(o) for o in p["on"]]
        candidate[i] = {**{k: v for k, v in p.items() if k in _STORED}, "id": i, "on": [o for o in on if o]}

    # Flows: the proposal adds or changes the ones it names; a flow leaves only when `remove` names it.
    flow_reports, flow_changes, held = {}, {}, set()
    dropped, not_removed = set(), []
    for name in proposal.get("remove", []):
        target = name if name in flow_records else flow_names.get(key(name))
        if target is None:
            reason = "a node leaves the map when no flow uses it" if resolve(name) else "no flow has this id or name"
        elif target in declared:
            reason = f"confirmed by the project; remove it from {DECLARED_FILE}"
        elif any(f.get("id") == target or flow_names.get(key(f["name"])) == target for f in proposal["flows"]):
            reason = "the proposal also changes it"
        else:
            dropped.add(target)
            continue
        not_removed.append({"name": name, "reason": reason})

    def refuse(f, target, reason):
        flow_reports[key(f["name"])] = {"name": f["name"], "status": "refused", "reason": reason}
        if target in flow_records:
            held.add(target)

    for f in proposal["flows"]:
        target = f.get("id") or flow_names.get(key(f["name"]))
        refs = [resolve(n) for n in f["nodes"]]
        twin = next((i for i, g in flow_records.items() if i != target and set(g["nodes"]) == set(refs)), None)
        if "id" in f and f["id"] not in flow_records:
            refuse(f, None, f"no flow has id {f['id']}")
        elif target in declared:
            flow_reports[key(f["name"])] = {"id": target, "name": f["name"], "status": "confirmed",
                                            "reason": f"confirmed by the project; change it in {DECLARED_FILE}"}
        elif None in refs:
            refuse(f, target, f"nodes refused: {', '.join(n for n, r in zip(f['nodes'], refs) if r is None)}")
        elif twin:
            refuse(f, target, f"repeats flow {twin}: the same nodes")
        else:
            i = target or _assign(f["name"], taken)
            flow_changes[i] = {**{k: f[k] for k in ("name", "area", "types", "paths")}, "id": i, "nodes": refs,
                               "arrows": [{**a, "from": resolve(a["from"]), "to": resolve(a["to"])} for a in f["arrows"]]}
    kept_flows = {i: f for i, f in flow_records.items() if i not in dropped}
    trial, _ = _verify(manifest, links, list(candidate.values()),
                       list({**kept_flows, **flow_changes}.values()), headers)
    checked = dict(zip(candidate, trial["nodes"]))
    for (i, f), result in zip({**kept_flows, **flow_changes}.items(), trial["flows"]):
        if i not in flow_changes:
            continue
        flow_reports[key(f["name"])] = {"id": i, **result}
        if result["status"] == "refused":
            del flow_changes[i]
            if i in flow_records:
                held.add(i)
        else:
            flow_changes[i]["arrows"] = [a for a, r in zip(flow_changes[i]["arrows"], result["arrows"])
                                         if r["status"] != "refused"]
    # A refused change leaves the node as it was; a new refused node is not recorded.
    final_nodes = {i: (n if checked[i]["status"] == "accepted" or i not in nodes else nodes[i])
                   for i, n in candidate.items() if checked[i]["status"] == "accepted" or i in nodes}
    final_flows = {**kept_flows, **{i: flow_records[i] for i in held}, **flow_changes}
    used = {i for f in final_flows.values() for i in f["nodes"]} | (declared & set(final_nodes))
    stack = list(used)
    while stack:
        for target in final_nodes.get(stack.pop(), {}).get("on", []):
            if target not in used:
                used.add(target)
                stack.append(target)
    final_nodes = {i: n for i, n in sorted(final_nodes.items()) if i in used}
    areas = {**state["areas"], **{key(a["name"]): a for a in proposal["areas"]}}
    final = {"nodes": final_nodes, "flows": dict(sorted(final_flows.items())), "areas": areas, "declared": declared,
             "gaps": state["gaps"]}
    system = _evaluate(manifest, links, final, headers)

    # Freshness: what each record depends on, as the snapshot has it now.
    for record_, checked_ in zip(final_nodes.values(), system["nodes"]):
        record_["digests"] = _digests(set(checked_["files"]) | {e.split("#")[0] for e in record_["evidence"]}, headers)
    for record_, checked_ in zip(final_flows.values(), system["flows"]):
        for arrow, result in zip(record_["arrows"], checked_["arrows"]):
            files = {_site_file(p["site"]) for p in result.get("proof", [])} | (
                {_site_file(result["cite"])} if "cite" in result else set())
            arrow["digests"] = _digests(files, headers)
    snapshot._write_json_atomic(manifest.with_name(FILE), {
        "schema": SCHEMA, "nodes": list(final_nodes.values()), "flows": list(final["flows"].values()),
        "areas": sorted(areas.values(), key=lambda a: key(a["name"]))})

    def plain(r):
        return {k: v for k, v in r.items() if k != "digests"} | (
            {"arrows": [{k: v for k, v in a.items() if k != "digests"} for a in r["arrows"]]} if "arrows" in r else {})

    after = {**final_nodes, **final["flows"]}
    for p in proposal["nodes"]:
        if key(p["name"]) not in node_reports:
            node_reports[key(p["name"])] = {"id": ident[key(p["name"])], **checked[ident[key(p["name"])]]}
        report = node_reports[key(p["name"])]
        if report["status"] == "accepted" and report["id"] not in final_nodes:
            report.update(status="refused", reason="no flow uses it and no node names it in on")
    proposed = {flow_reports[key(f["name"])].get("id") for f in proposal["flows"]}
    return {"nodes": [node_reports[key(p["name"])] for p in proposal["nodes"]],
            "flows": [flow_reports[key(f["name"])] for f in proposal["flows"]],
            "failing": [f["id"] for f in system["flows"] if f["id"] not in proposed and f["status"] not in
                        ("accepted", "confirmed")],
            "coverage": _reported(system["coverage"]), "not_removed": not_removed,
            "created": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
            "updated": sorted(i for i in set(after) & set(before) if plain(after[i]) != plain(before[i])),
            "kept": sorted(i for i in set(after) & set(before) if plain(after[i]) == plain(before[i]))}


def load(manifest: Path, rules: list[dict]) -> dict | None:
    """The recorded map with the declared one over it, verified again on the current snapshot."""
    manifest = Path(manifest).resolve()
    headers = _headers(manifest)
    state = _state(manifest, headers)
    if not state["exists"] and not state["declared"]:
        return None
    return _evaluate(manifest, flows.cached_links(manifest, rules), state, headers)


def find(records: list[dict], name: str) -> dict | None:
    """The record with this id or this current name."""
    return next((r for r in records if r["id"] == name or key(r["name"]) == key(name)), None)


def about(system: dict, name: str) -> dict:
    """An area, a flow or a node, by id or current name: its flows, nodes, member files and nodes without code."""
    k = key(name)
    flow, node = find(system["flows"], name), find(system["nodes"], name)
    by_name = {n["name"]: n for n in system["nodes"]}
    if flow:
        kind, label, chosen = "flow", flow["name"], [flow]
    elif node:
        kind, label, chosen = "node", node["name"], [f for f in system["flows"] if node["name"] in f["nodes"]]
    elif any(key(f["area"]) == k for f in system["flows"]) or any(key(a["name"]) == k for a in system["areas"]):
        kind, chosen = "area", [f for f in system["flows"] if key(f["area"]) == k]
        label = next((a["name"] for a in system["areas"] if key(a["name"]) == k), name)
    else:
        raise ValueError(f"no area, flow or node is called {name}")
    involved = [node] if kind == "node" else [by_name[n] for n in dict.fromkeys(n for f in chosen for n in f["nodes"])]

    def files(group):
        return sorted({path for n in group for path in n["files"]})

    return {"kind": kind, "name": label,
            "flows": [{"id": f["id"], "name": f["name"], "area": f["area"], "status": f["status"],
                       "files": files(by_name[n] for n in f["nodes"])} for f in chosen],
            "nodes": [{k_: n[k_] for k_ in ("id", "name", "type", "position", "status")} for n in involved],
            "files": files(involved),
            "externals": sorted((n["name"] for n in involved if n["position"] == "external"), key=key),
            "unseen": [{"name": n["name"], "where": n["where"]} for n in involved if n["position"] == "unseen"]}
