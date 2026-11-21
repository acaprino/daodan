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

import functools
import json
import re
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
NODE_TYPES = flows.NODE_TYPES + ("entità", "applicazione", "lavoro a orario")
POSITIONS = ("internal", "external", "unseen")
FLOW_TYPES = ("funzionale", "operativo", "tecnico", "dati", "hardware", "devops")
AREAS = ("accesso e identità", "funzioni principali", "pagamenti e abbonamenti", "dati dell'utente",
         "integrazioni esterne", "comunicazioni", "amministrazione", "esercizio")
ARROW_KINDS = ("chiama", "attiva", "scrive", "legge", "usa", "trasferisce", "stessa informazione")
# Given by the owner on 19 November 2026: a provider makes the program work, an integration platform is a system of
# others the program exchanges data with.
FAMILIES = ("provider", "piattaforma di integrazione")
NOT_SERVICES = ("attore", "dispositivo", "filesystem")  # external nodes that are not a system of others
_SERVICE_FIELDS = ("family", "role", "mode")
_MAP_FIELDS = {"schema", "nodes", "flows", "areas", "scope", "remove"}
_NODE_FIELDS = {"id", "name", "type", "position", "members", "evidence", "on", "inside", "where", "registry",
                *_SERVICE_FIELDS}
_FLOW_FIELDS = {"id", "name", "area", "types", "nodes", "entries", "effects", "arrows", "paths"}
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
    if "inside" in record:
        out["inside"] = _text(record, "inside", where)
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
    return {**out, **_service(record, out, where)}


@functools.cache
def _registry_names() -> dict[str, str]:
    import service_registry
    return {entry["id"]: entry["name"] for entry in service_registry.load()["entries"]}


# The checks a machine makes on names without error; the other rules are in references/system-map.md, «Names».
EMPTY_WORDS = ("gestione", "elaborazione", "processo", "management", "handling", "processing")


def flow_name_problem(name: str) -> str | None:
    """Why a flow's name does not stand: its first word is an empty one, compared without case and accents."""
    first = re.match(r"\w*", name.strip()).group()
    if key(first) in EMPTY_WORDS:
        return f"the name must not begin with {first}, a word that says nothing: name the action and its object"
    return None


def registry_name_problem(name: str, registry: str | None) -> str | None:
    """Why an external node's name does not stand: it does not begin with the name of its registry entry."""
    proper = _registry_names().get(registry)
    if proper and not re.match(re.escape(key(proper)) + r"(\W|$)", key(name)):
        return f"the name must begin with {proper}, the name of registry entry {registry}"
    return None


def _service(record: dict, node: dict, where: str) -> dict:
    """An external node's registry id; a service of others also says its family, what it is for and how the program
    connects to it."""
    out, external = {}, node["position"] == "external"
    if "registry" in record:
        if not external:
            raise ValueError(f"{where}: only an external node has a registry id")
        out["registry"] = _text(record, "registry", where)
        if out["registry"] not in _registry_names():
            raise ValueError(f"{where}: registry {out['registry']} is not an id of the service registry")
    given = [field for field in _SERVICE_FIELDS if field in record]
    if given and (not external or node["type"] in NOT_SERVICES):
        raise ValueError(f"{where}: only an external service has {', '.join(given)}")
    for field in given:
        out[field] = _text(record, field, where)
    if out.get("family", FAMILIES[0]) not in FAMILIES:
        raise ValueError(f"{where}: family must be one of {', '.join(FAMILIES)}")
    return out


def _named(record: dict) -> list[str]:
    """The nodes a node names: those it runs on and the one it is inside."""
    return record["on"] + ([record["inside"]] if record.get("inside") else [])


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
    if ("entries" in record) != ("effects" in record):
        raise ValueError(f"{where}: declare entries and effects together")
    for field in ("entries", "effects"):
        if field in record:
            endpoints = _texts(record, field, where)
            if not endpoints or any(key(n) not in inside for n in endpoints):
                raise ValueError(f"{where}: {field} must name one or more nodes of the flow")
            out[field] = endpoints
    out["arrows"] = [_arrow(arrow, where, inside) for arrow in arrows]
    out["paths"] = _texts(record, "paths", where)
    return out


def validate(value: object, known: set[str] = frozenset()) -> dict:
    """The proposal in its normal form, or a ValueError that names the wrong field.

    `known` holds the keys of the nodes already in the map, which flows, `on` and `inside` may name.
    """
    value = _fields(value, _MAP_FIELDS, "the system map")
    if value.get("schema", SCHEMA) != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")
    for field in ("nodes", "flows", "areas"):
        if not isinstance(value.get(field, []), list):
            raise ValueError(f"{field} must be a list")
    scope = None
    if value.get("scope") is not None:  # absent, null or an empty list: the whole system
        scope = _texts(value, "scope", "the system map") or None
    scope_keys = {key(a) for a in scope} if scope is not None else None
    areas, seen = [], {}
    for record in value.get("areas", []):
        record = _fields(record, _AREA_FIELDS, "an area")
        name = _text(record, "name", "an area")
        if scope_keys is not None and key(name) not in scope_keys:
            raise ValueError(f"area {name} is outside the scope")
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
        for field, values in (("on", record["on"]), ("inside", [record["inside"]] if "inside" in record else [])):
            missing = [n for n in values if key(n) not in names and key(n) not in known]
            if missing:
                raise ValueError(f"node {record['name']}: {field} names {', '.join(missing)}, not in the map")
    present = {name for name, flag in seen.items() if flag} | ((scope_keys or set()) - seen.keys())
    flow_list, flow_names = [], set()
    for record in value.get("flows", []):
        record = _flow(record, set(names) | set(known), present, scope_keys)
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
    for ident, item in out.items():  # `inside` climbs towards the whole system, never back to the node
        at, seen = item["record"].get("inside"), set()
        while at in out and at != ident and at not in seen:
            seen.add(at)
            at = out[at]["record"].get("inside")
        if at == ident:
            report = item["report"]
            report.update(status="refused", reason="; ".join(filter(None, (report.get("reason"),
                                                                           "inside goes round in a circle"))))
    changed = True
    while changed:  # `on` and `inside` name accepted nodes only
        changed = False
        for item in out.values():
            refused = [out[i]["report"]["name"] for i in _named(item["record"])
                       if out[i]["report"]["status"] != "accepted"]
            if refused and item["report"]["status"] == "accepted":
                item["report"].update(status="refused",
                                      reason=f"on or inside names refused nodes: {', '.join(refused)}")
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


def _beside(items: dict, endpoint: str) -> set[str]:
    """Nodes that hold another function of the endpoint's file, when no node holds the endpoint as a function."""
    path, found, symbol = endpoint.partition("::")
    if not found or endpoint.startswith(("store:", "module:")):
        return set()
    holders = {i for i, item in items.items() if any(p == path for p, _ in item["symbols"])}
    claimed = any(p == path and (symbol == s or symbol.startswith(s + "."))
                  for i in holders for p, s in items[i]["symbols"])
    return set() if claimed else holders


def _between(a: str, b: str, owners: dict, leaving: dict, readers: dict) -> tuple[list, list]:
    """Links from the first node to the second, and pairs of a write and a read of the same store key."""
    # A link between two members both nodes hold proves nothing between them.
    direct = [e for e in leaving.get(a, []) if b in owners[e["to"]]
              and not {a, b} <= owners[e["from"]] & owners[e["to"]]]
    pairs = [(w, r) for w in leaving.get(a, []) if w["type"] == "scrive"
             for r in readers.get(w["to"], []) if b in owners[r["to"]] and not {a, b} <= owners[w["from"]] & owners[r["to"]]]
    return direct, pairs


def _proof(edge: dict) -> dict:
    return {name: edge[name] for name in ("from", "to", "type", "site", "origin", "confidence", "resolver", "conflict")
            if name in edge}


def _check_arrow(arrow: dict, first: dict, second: dict, index: dict, headers: dict) -> dict:
    out = {"from": first["report"]["name"], "to": second["report"]["name"], "data": arrow["data"]}
    refused = [i["report"]["name"] for i in (first, second) if i["report"]["status"] != "accepted"]
    if refused:
        return {**out, "status": "refused", "reason": f"nodes refused: {', '.join(refused)}"}
    if first["record"]["position"] != "internal" or second["record"]["position"] != "internal" \
            or arrow.get("kind") == "stessa informazione":
        return {**out, **{k: arrow[k] for k in ("kind", "cite") if k in arrow},
                **_declared(arrow, first, second, headers)}
    a, b = first["record"]["id"], second["record"]["id"]
    direct, pairs = _between(a, b, index["owners"], index["leaving"], index["readers"])
    precise = bool(direct or pairs)
    if not precise:  # the most specific level that holds: the member, else the file of a function member
        direct, pairs = _between(a, b, index["near"], index["leaving_near"], index["readers"])
    if not direct and not pairs:
        return {**out, **{k: arrow[k] for k in ("kind", "cite") if k in arrow}, "status": "refused",
                "reason": f"no link from a member of {out['from']} to a member of {out['to']}, "
                          "nor a write and a read of the same store key"}
    types = {e["type"] for e in direct} | ({"trasferisce"} if pairs else set())
    via = {e["to"] for e in direct if e["type"] == "scrive"} | {e["from"] for e in direct if e["type"] == "legge"}
    via |= {w["to"] for w, _ in pairs}
    proof = [_proof(e) for e in direct] + [_proof(e) for pair in pairs for e in pair]
    return {**out, "status": "proved", "asserts": [k for k in ARROW_KINDS if k in types],
            "via": sorted(v[6:] for v in via), "proof": list({tuple(p.items()): p for p in proof}.values()),
            **({} if precise else {"precise": False})}


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


def _reachable(starts, adjacent: dict) -> set:
    reached = set(starts)
    stack = list(reached)
    while stack:
        following = adjacent[stack.pop()] - reached
        reached.update(following)
        stack.extend(following)
    return reached


def _flow_verdict(record: dict, arrows: list[dict], items: dict) -> dict:
    def named(ids):
        return sorted(items[i]["report"]["name"] for i in ids)

    endpoints = {k: named(record[k]) for k in ("entries", "effects") if k in record}
    out = {"name": record["name"], "arrows": arrows, **endpoints,
           "reachability": "unproved" if endpoints else "not_declared"}
    refused = [i for i in record["nodes"] if items[i]["report"]["status"] != "accepted"]
    if refused:
        return {**out, "status": "refused", "reason": f"nodes refused: {', '.join(named(refused))}"}
    if all(a["status"] == "refused" for a in arrows):
        return {**out, "status": "refused", "reason": "no arrow stands"}
    forward = {i: set() for i in record["nodes"]}
    backward = {i: set() for i in record["nodes"]}
    for arrow, result in zip(record["arrows"], arrows):
        if result["status"] != "refused":
            first, second = arrow["from"], arrow["to"]
            forward[first].add(second)
            backward[second].add(first)
    if endpoints:
        from_entries = _reachable(record["entries"], forward)
        to_effects = _reachable(record["effects"], backward)
        missing = forward.keys() - (from_entries & to_effects)
        if missing:
            return {**out, "status": "incomplete",
                    "reason": f"outside a directed path from an entry to an effect: {', '.join(named(missing))}"}
        out["reachability"] = "verified"
    joined = {i: outs | backward[i] for i, outs in forward.items()}
    disconnected = joined.keys() - _reachable(record["nodes"][:1], joined)
    if disconnected:
        return {**out, "status": "incomplete",
                "reason": f"standing arrows leave disconnected nodes: {', '.join(named(disconnected))}"}
    if any(a["status"] == "refused" for a in arrows):
        return {**out, "status": "incomplete", "reason": "one or more arrows are refused"}
    return {**out, "status": "accepted"}


def _verify(manifest: Path, links: dict, nodes: list[dict], flow_records: list[dict], headers: dict):
    """Reports of nodes and flows referenced by id, and the node items they were checked with."""
    items = _check_nodes(manifest, links, nodes, headers)
    endpoints = {end for edge in links["edges"] for end in (edge["from"], edge["to"])}
    owners = {end: {i for i, item in items.items() if _owns(item, end)} for end in endpoints}
    index = {"owners": owners, "near": {end: owners[end] | _beside(items, end) for end in endpoints},
             "leaving": {}, "leaving_near": {}, "readers": {}}
    for edge in links["edges"]:
        for owner in owners[edge["from"]]:
            index["leaving"].setdefault(owner, []).append(edge)
        for owner in index["near"][edge["from"]]:
            index["leaving_near"].setdefault(owner, []).append(edge)
        if edge["type"] == "legge":
            index["readers"].setdefault(edge["from"], []).append(edge)
    out = []
    for record in flow_records:
        arrows = [_check_arrow(a, items[a["from"]], items[a["to"]], index, headers) for a in record["arrows"]]
        out.append(_flow_verdict(record, arrows, items))
    return {"nodes": [items[n["id"]]["report"] for n in nodes], "flows": out}, items


def _by_key(value: dict) -> tuple[list[dict], list[dict]]:
    """A validated proposal with each name as its own id."""
    nodes = [{**n, "id": key(n["name"]), "on": [key(o) for o in n["on"]],
              **({"inside": key(n["inside"])} if "inside" in n else {})} for n in value["nodes"]]
    flow_records = [{**f, **{k: [key(n) for n in f[k]] for k in ("nodes", "entries", "effects") if k in f},
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
_STORED = ("id", "name", "type", "position", "members", "evidence", "on", "inside", "where", "registry",
           *_SERVICE_FIELDS)


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
        if unknown := sorted({o for n in nodes for o in _named(n)} - ids):
            raise ValueError(f"on or inside names unknown ids {', '.join(unknown)}")
        flow_records = [_flow(f, {key(i) for i in ids}, None, None) for f in value.get("flows", [])]
        if any("id" not in f for f in flow_records):
            raise ValueError("every declared flow has its id")
        for flow in flow_records:
            participants = set(flow["nodes"])
            references = {i for a in flow["arrows"] for i in (a["from"], a["to"])}
            references.update(flow.get("entries", []) + flow.get("effects", []))
            if participants - ids or references - participants:
                raise ValueError(f"flow {flow['name']}: participants and endpoints must use exact node ids")
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
            "refused_proposals": stored.get("refused_proposals", []),
            "declared": {r["id"] for r in declared["nodes"] + declared["flows"]}, "gaps": gaps, "exists": path.is_file()}


def _changed(digests: dict, headers: dict, paths=None) -> list[str]:
    return sorted(f for f, digest in digests.items()
                  if (paths is None or f in paths) and (headers.get(f) or {}).get("raw_hash") != digest)


def _site_file(site: str) -> str:
    path, _, line = site.rpartition(":")
    return path if line.isdigit() else site


LEFT_LISTED = 40  # past this many, a report lists what coverage leaves out by directory; the map keeps the names


def listed(files: list[str]) -> dict:
    """A list of files as a report gives it back: a long one is counted by directory, cut higher until the
    directories are few. A node that is a whole part resolves to every file of it, and an answer naming them one by
    one is too long to be read."""
    if len(files) <= LEFT_LISTED:
        return {"files": files}
    folders = [path.rsplit("/", 1)[0] if "/" in path else "." for path in files]
    depth = max(folder.count("/") + 1 for folder in folders)
    while True:
        by = {}
        for folder in folders:
            where = "/".join(folder.split("/")[:depth])
            by[where] = by.get(where, 0) + 1
        if len(by) <= LEFT_LISTED or depth == 1:
            return {"files_by_directory": dict(sorted(by.items()))}
        depth -= 1


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
        if ident in declared:
            return "confirmed" if verified == "accepted" else "incomplete"
        return verified

    out_nodes = []
    for record, checked in zip(nodes.values(), report["nodes"]):
        state_of = status(record["id"], checked["status"])
        changed = _changed(record.get("digests", {}), headers)
        fresh = state_of in ok and (record["position"] == "internal" or not changed)
        out_nodes.append({**{k: record[k] for k in _STORED if k in record}, "on": [name[o] for o in record["on"]],
                          **({"inside": name[record["inside"]]} if record.get("inside") else {}),
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
                          **{k: checked[k] for k in ("reachability", "entries", "effects") if k in checked},
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
            "refused_proposals": state["refused_proposals"],
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


def _dependencies(nodes: dict, roots) -> set[str]:
    """The nodes used directly, plus the nodes named by their on/inside references."""
    used = set(roots)
    stack = list(used)
    while stack:
        for target in _named(nodes[stack.pop()]):
            if target not in used:
                used.add(target)
                stack.append(target)
    return used


def record(manifest: Path, rules: list[dict], value: object) -> dict:
    """Validate and verify a proposal, merge it into the recorded map and write it beside the manifest."""
    manifest = Path(manifest).resolve()
    links = flows.cached_links(manifest, rules)
    headers = _headers(manifest)
    state = _state(manifest, headers)
    node_names = {key(n["name"]): i for i, n in state["nodes"].items()}
    proposal = validate(value, known=set(node_names) | set(state["nodes"]))
    flow_names = {key(f["name"]): i for i, f in state["flows"].items()}
    targets = set()
    for part, names in (("nodes", node_names), ("flows", flow_names)):
        for entry in proposal[part]:
            target = entry.get("id") or names.get(key(entry["name"]))
            if target is not None:
                if target in targets:
                    raise ValueError(f"the proposal names id {target} twice")
                targets.add(target)
    scope = {key(a) for a in proposal.get("scope", [])}
    outside = {i for i, f in state["flows"].items() if scope and key(f["area"]) not in scope}
    protected = _dependencies(state["nodes"], (n for i in outside for n in state["flows"][i]["nodes"]))
    if protected:
        # A part with no flow of its own belongs to the area that owns its nearest ancestor.
        inside = _dependencies(state["nodes"], (n for i, f in state["flows"].items() if i not in outside for n in f["nodes"]))
        parents = {i: n["inside"] for i, n in state["nodes"].items() if n.get("inside")}
        owners = inside | protected
        for i in state["nodes"].keys() - owners:
            at, visited = i, set()
            while at in parents and at not in owners and at not in visited:
                visited.add(at)
                at = parents[at]
            if at in protected:
                protected.add(i)
        protected = _dependencies(state["nodes"], protected)
    taken = set(state["nodes"]) | set(state["flows"])
    ident, node_reports, candidate, resolve = _record_nodes(state, proposal, node_names, taken, protected)
    settled = _record_flows(manifest, links, headers, state, proposal, candidate, resolve, taken, flow_names, outside)
    return _write(manifest, links, headers, state, proposal, (ident, node_reports, candidate), settled)


def _record_nodes(state: dict, proposal: dict, node_names: dict, taken: set[str], protected: set[str]):
    """Per proposed node the id it recalls or takes, the reports of those refused, the candidate map, the resolver.

    An id or a current name recalls a node; a new one must not repeat an existing one.
    """
    nodes, declared = state["nodes"], state["declared"]
    ident, node_reports, changes = {}, {}, {}
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
        elif problem := registry_name_problem(p["name"], p.get("registry")):
            node_reports[key(p["name"])] = {"name": p["name"], "status": "refused", "reason": problem}
            ident[key(p["name"])] = None
        elif target and node_names.get(key(p["name"]), target) != target:
            node_reports[key(p["name"])] = {"name": p["name"], "status": "refused",
                                            "reason": f"node {node_names[key(p['name'])]} already has this name"}
            ident[key(p["name"])] = None
        elif target in protected:
            # A scoped proposal may repeat a shared node verbatim, or just use its name.
            # Leave its stored evidence and its confirmation time alone in either case.
            comparable = {**p, "id": target, "on": [node_names.get(key(n), n) for n in p["on"]]}
            if "inside" in p:
                comparable["inside"] = node_names.get(key(p["inside"]), p["inside"])
            if comparable == {k: v for k, v in nodes[target].items() if k in _STORED}:
                ident[key(p["name"])] = target
            else:
                node_reports[key(p["name"])] = {"name": p["name"], "status": "refused",
                                                "reason": f"node {target} is used by a flow outside the scope"}
                ident[key(p["name"])] = None
        elif target:
            ident[key(p["name"])] = target
            changes[target] = p
        else:
            fresh_nodes.append(p)
    current = {i: {**n, **changes.get(i, {})} for i, n in nodes.items()}
    up = _parents(nodes, changes, fresh_nodes)
    for p in fresh_nodes:
        basis = "members" if p["position"] == "internal" else "evidence"
        # A part inside a node, or the node a part is inside, does not repeat it.
        twin = next((i for i, n in current.items() if n["type"] == p["type"] and _nested(n[basis], p[basis])
                     and key(n["name"]) not in _above(up, key(p["name"]))
                     and key(p["name"]) not in _above(up, key(n["name"]))), None)
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
        inside = resolve(p["inside"]) if "inside" in p else None  # like `on`, a refused parent is dropped
        candidate[i].pop("inside", None)
        candidate[i].update({"inside": inside} if inside else {})
    return ident, node_reports, candidate, resolve


def _parents(nodes: dict, changes: dict, fresh: list[dict]) -> dict[str, str]:
    """Per node, by name key, the key of the node it is inside, over the map as the proposal would leave it."""
    stored = {i: n for i, n in nodes.items() if i not in changes}
    names = {i: key(n["name"]) for i, n in {**stored, **changes}.items()}
    known = set(names.values()) | {key(p["name"]) for p in fresh}
    up = {names[i]: names.get(n["inside"]) for i, n in stored.items() if n.get("inside")}
    for p in [*changes.values(), *fresh]:
        if p.get("inside"):
            up[key(p["name"])] = key(p["inside"]) if key(p["inside"]) in known else names.get(p["inside"])
    return up


def _above(up: dict[str, str], name: str) -> set[str]:
    """The keys of the nodes a node is inside, up to the top."""
    seen = set()
    while (name := up.get(name)) is not None and name not in seen:
        seen.add(name)
    return seen


def _record_flows(manifest: Path, links: dict, headers: dict, state: dict, proposal: dict, candidate: dict,
                  resolve, taken: set[str], flow_names: dict, outside: set[str]):
    """The proposal adds or changes the flows it names; a flow leaves only when `remove` names it.

    Gives the flow reports, the flows the map keeps, the nodes as the trial verified them and what `remove` left.
    """
    flow_records, declared = state["flows"], state["declared"]
    flow_reports, flow_changes, held = {}, {}, set()
    dropped, not_removed = set(), []
    for name in proposal.get("remove", []):
        target = name if name in flow_records else flow_names.get(key(name))
        if target is None:
            reason = "a node leaves the map when no flow uses it" if resolve(name) else "no flow has this id or name"
        elif target in declared:
            reason = f"confirmed by the project; remove it from {DECLARED_FILE}"
        elif target in outside:
            reason = f"flow {target} belongs to an area outside the scope"
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
        # Older clients can revise an anchored flow without erasing its declared contract.
        endpoints = ({k: [resolve(n) for n in f[k]] for k in ("entries", "effects")} if "entries" in f else
                     {k: flow_records[target][k] for k in ("entries", "effects") if k in flow_records.get(target, {})})
        twin = next((i for i, g in flow_records.items() if i != target and set(g["nodes"]) == set(refs)), None)
        if "id" in f and f["id"] not in flow_records:
            refuse(f, None, f"no flow has id {f['id']}")
        elif target in declared:
            flow_reports[key(f["name"])] = {"id": target, "name": f["name"], "status": "confirmed",
                                            "reason": f"confirmed by the project; change it in {DECLARED_FILE}"}
        elif target in outside:
            refuse(f, target, f"flow {target} belongs to an area outside the scope")
        elif target and flow_names.get(key(f["name"]), target) != target:
            refuse(f, target, f"flow {flow_names[key(f['name'])]} already has this name")
        elif problem := flow_name_problem(f["name"]):
            refuse(f, target, problem)
        elif None in refs:
            refuse(f, target, f"nodes refused: {', '.join(n for n, r in zip(f['nodes'], refs) if r is None)}")
        elif any(i not in refs for bound in endpoints.values() for i in bound):
            refuse(f, target, "redeclare entries and effects when removing a previously declared endpoint")
        elif twin:
            refuse(f, target, f"repeats flow {twin}: the same nodes")
        else:
            i = target or _assign(f["name"], taken)
            flow_changes[i] = {**{k: f[k] for k in ("name", "area", "types", "paths")}, **endpoints, "id": i, "nodes": refs,
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
    final_flows = {**kept_flows, **{i: flow_records[i] for i in held}, **flow_changes}
    return flow_reports, final_flows, checked, not_removed


def _refused_proposals(state, proposal, reports, final_flows, not_removed):
    """Keep the latest all-arrow refusal separately from the admitted version of a flow."""
    scope = {key(a) for a in proposal.get("scope", [])}
    pending = {}
    dropped = state["flows"].keys() - final_flows.keys()
    remove = {key(n) for n in proposal.get("remove", [])}
    proposing = {key(f["name"]) for f in proposal["flows"]}
    for row in state["refused_proposals"]:
        area, name = key(row["area"]), key(row["name"])
        if row.get("id") in dropped:
            continue
        if "id" not in row and name in remove - proposing and (not scope or area in scope):
            not_removed[:] = [r for r in not_removed if key(r["name"]) != name]
            continue
        pending[area, name] = row
    for flow in proposal["flows"]:
        name = key(flow["name"])
        result = reports[name]
        all_refused = bool(result.get("arrows")) and result["status"] == "refused" and result.get("reason") == "no arrow stands"
        if result["status"] not in ("accepted", "incomplete") and not all_refused:
            continue
        ident = result.get("id")
        if ident in state["flows"]:
            pending = {k: row for k, row in pending.items() if row.get("id") != ident}
        item = key(flow["area"]), name
        pending.pop(item, None)
        if all_refused:
            pending[item] = {**{k: v for k, v in result.items() if k != "id"}, "area": flow["area"],
                             **({"id": ident} if ident in state["flows"] else {})}
    return [pending[k] for k in sorted(pending)]


def _write(manifest: Path, links: dict, headers: dict, state: dict, proposal: dict, node_part: tuple,
           flow_part: tuple) -> dict:
    """Keep the nodes the map still holds, write the map with its freshness and report what changed."""
    ident, node_reports, candidate = node_part
    flow_reports, final_flows, checked, not_removed = flow_part
    nodes, declared = state["nodes"], state["declared"]
    before = {**nodes, **state["flows"]}
    # A refused change leaves the node as it was; a new refused node is not recorded.
    final_nodes = {i: (n if checked[i]["status"] == "accepted" or i not in nodes else nodes[i])
                   for i, n in candidate.items() if checked[i]["status"] == "accepted" or i in nodes}
    # A node stays while a flow uses it, the project confirms it, it is inside a node or `on` or `inside` names it.
    used = {i for f in final_flows.values() for i in f["nodes"]} | (declared & set(final_nodes)) | {
        i for i, n in final_nodes.items() if n.get("inside")}
    used = _dependencies(final_nodes, used)
    final_nodes = {i: n for i, n in sorted(final_nodes.items()) if i in used}
    areas = {**state["areas"], **{key(a["name"]): a for a in proposal["areas"]}}
    final = {"nodes": final_nodes, "flows": dict(sorted(final_flows.items())), "areas": areas, "declared": declared,
             "gaps": state["gaps"], "refused_proposals": _refused_proposals(
                 state, proposal, flow_reports, final_flows, not_removed)}
    system = _evaluate(manifest, links, final, headers)

    # Only a proposed and accepted record (or a first declaration) gains a new
    # baseline. An unrelated write must not attest to evidence that has changed.
    for record_, checked_ in zip(final_nodes.values(), system["nodes"]):
        if record_ is nodes.get(record_["id"]) and record_.get("digests"):
            continue
        record_["digests"] = _digests(set(checked_["files"]) | {e.split("#")[0] for e in record_["evidence"]}, headers)
    for checked_ in system["flows"]:
        record_ = final_flows[checked_["id"]]
        for arrow, result in zip(record_["arrows"], checked_["arrows"]):
            if record_ is state["flows"].get(record_["id"]) and arrow.get("digests"):
                continue
            files = {_site_file(p["site"]) for p in result.get("proof", [])} | (
                {_site_file(result["cite"])} if "cite" in result else set())
            arrow["digests"] = _digests(files, headers)

    def plain(r):
        return {k: v for k, v in r.items() if k != "digests"} | (
            {"arrows": [{k: v for k, v in a.items() if k != "digests"} for a in r["arrows"]]} if "arrows" in r else {})

    after = {**final_nodes, **final["flows"]}
    for p in proposal["nodes"]:
        if key(p["name"]) not in node_reports:
            node_reports[key(p["name"])] = {"id": ident[key(p["name"])], **checked[ident[key(p["name"])]]}
        report = node_reports[key(p["name"])]
        if report["status"] == "accepted" and report["id"] not in final_nodes:
            report.update(status="refused",
                          reason="no flow uses it, it is inside no node and no node names it in on or inside")
    proposed = {flow_reports[key(f["name"])].get("id") for f in proposal["flows"]}
    # Project-confirmed identities cannot be changed by a proposal. Surface a
    # failed verification of those stored records in this answer just as on load.
    for group, reports in (("nodes", node_reports), ("flows", flow_reports)):
        incomplete = {item["id"]: item for item in system[group] if item["status"] == "incomplete"}
        for reported in reports.values():
            if reported["status"] == "confirmed" and (current := incomplete.get(reported["id"])):
                reported.update(status="incomplete", reason=current["reason"])

    def short(report):
        return {**{k: v for k, v in report.items() if k != "files"}, **listed(report["files"])} if "files" in report else report

    answer = {"nodes": [short(node_reports[key(p["name"])]) for p in proposal["nodes"]],
              "flows": [flow_reports[key(f["name"])] for f in proposal["flows"]],
              "failing": [f["id"] for f in system["flows"] if f["id"] not in proposed and f["status"] not in
                          ("accepted", "confirmed")],
              "coverage": _reported(system["coverage"]), "not_removed": not_removed,
              "created": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
              "updated": sorted(i for i in set(after) & set(before) if plain(after[i]) != plain(before[i])),
              "kept": sorted(i for i in set(after) & set(before) if plain(after[i]) == plain(before[i]))}
    snapshot._write_json_atomic(manifest.with_name(FILE), {
        "schema": SCHEMA, "nodes": list(final_nodes.values()), "flows": list(final["flows"].values()),
        "refused_proposals": final["refused_proposals"],
        "areas": sorted(areas.values(), key=lambda a: key(a["name"]))})
    return answer


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
    refused = system.get("refused_proposals", [])
    matching = [r for r in refused if key(r["name"]) == k or r.get("id") == name or
                (flow and r.get("id") == flow["id"])]
    if flow:
        kind, label, chosen = "flow", flow["name"], [flow]
    elif node:
        kind, label, chosen = "node", node["name"], [f for f in system["flows"] if node["name"] in f["nodes"]]
    elif any(key(f["area"]) == k for f in system["flows"]) or any(key(a["name"]) == k for a in system["areas"]):
        kind, chosen = "area", [f for f in system["flows"] if key(f["area"]) == k]
        label = next((a["name"] for a in system["areas"] if key(a["name"]) == k), name)
        matching = [r for r in refused if key(r["area"]) == k]
    elif matching:
        kind, label, chosen = "refused_flow", matching[0]["name"], []
    else:
        raise ValueError(f"no area, flow or node is called {name}")
    involved = [node] if kind == "node" else [by_name[n] for n in dict.fromkeys(n for f in chosen for n in f["nodes"])]

    def files(group):
        return sorted({path for n in group for path in n["files"]})

    return {"kind": kind, "name": label,
            **({"refused_proposals": matching} if matching else {}),
            "flows": [{"id": f["id"], "name": f["name"], "area": f["area"], "status": f["status"],
                       "fresh": f["fresh"],
                       **{k: f[k] for k in ("reachability", "entries", "effects") if k in f},
                       **({"reason": f["reason"]} if "reason" in f else {}),
                       **({"refused_arrows": arrows} if (arrows := [a for a in f["arrows"] if a["status"] == "refused"]) else {}),
                       **listed(files(by_name[n] for n in f["nodes"]))} for f in chosen],
            "nodes": [{k_: n[k_] for k_ in ("id", "name", "type", "position", "status", "fresh")} for n in involved],
            **listed(files(involved)),
            "externals": sorted((n["name"] for n in involved if n["position"] == "external"), key=key),
            "unseen": [{"name": n["name"], "where": n["where"]} for n in involved if n["position"] == "unseen"]}
