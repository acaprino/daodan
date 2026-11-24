#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""A Codebase Map run as `daodan/visual@1`: what the explorer draws, with nothing inferred here.

Reads only public APIs: the run snapshot (`snapshot_store`), the module graph (`modules`),
outlines and file imports (`source_reader`), card freshness (`semantic_store`), the stack
step's technologies (`technologies`: the list, and on each build unit its ids) and, when
the run has link rules, its flows (`flows`). States keep the producers' values:
`provenance`, `status` and card `freshness` are distinct fields, never promoted.

Every node carries `location` (`internal`, `external`) and, when known, `node_type`
from the closed list of the flow model: an external module is a service or API, a service
the stack recognises the type of its registry entry, a route handler a service or API, the
symbol that binds a user action a screen, a store the type its link rule names. A node of
unknown type has none. An external service and an item of `technologies` whose registry entry has a
logo carry the entry's id in `mark`; the others have none.

    python visual.py envelope RUN_DIR [--out FILE]
    python visual.py export RUN_DIR        # publishes .daodan/map/views/<run>/<digest>/visual.json
    python visual.py serve EXPORT_DIR      # http://127.0.0.1:<port>/, read-only

The MCP server serves the same page live (`codebase_map_ui`): `live_routes` answers with the
project's runs, a run's events and a run's envelope built at each request. Every server of the page
answers `/api/mark?id=ID` with the logo of a registry entry (`mark_files`).
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import shutil
import socket
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qsl, urlsplit, urlunsplit

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import card_store  # noqa: E402
import confinement  # noqa: E402
import edge_view  # noqa: E402
import modules  # noqa: E402
import snapshot  # noqa: E402
import semantic_store  # noqa: E402
import source_reader  # noqa: E402
from snapshot_store import logical_digest, open_snapshot, resolve_run_snapshot  # noqa: E402

SCHEMA = "daodan/visual@1"
LIMIT = 1000  # the readers' maximum per list: larger inputs are split, never cut in silence
_SECRET_WORDS = ("password=", "passwd=", "secret=", "token=", "apikey=", "api_key=")


def sanitize_address(text: str) -> str:
    """An address without credentials, query or fragment; text carrying a secret outside a URL is dropped."""
    parts = urlsplit(text) if isinstance(text, str) else None
    if parts and parts.scheme and parts.netloc:
        host = parts.hostname or ""
        netloc = f"{host}:{parts.port}" if parts.port else host
        return urlunsplit((parts.scheme, netloc, parts.path, "", ""))
    if isinstance(text, str) and any(word in text.casefold() for word in _SECRET_WORDS):
        return ""
    return text


def _chunks(items: list, size: int = LIMIT):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _module_ref(module: dict) -> str:
    kind = "external" if module.get("location") == "external" else (
        "virtual" if module.get("provenance") == "virtual" else (
            "build" if module.get("provenance") == "build" else module.get("kind", "component")
        )
    )
    return f"{kind}:{module['id']}"


def _collector(entities: dict, relations: dict):
    """`entity` and `relation`, which add to `entities` and `relations` by ref, a second time merging the fields."""
    def entity(ref: str, kind: str, name: str, **fields) -> dict:
        found = entities.setdefault(ref, {"ref": ref, "type": kind, "name": name, "technical": ref.split(":", 1)[1],
                                          "description": "", "evidence": [], "gaps": []})
        found.update({key: value for key, value in fields.items() if value is not None})
        return found

    def relation(kind: str, source: str, target: str, status: str = "confirmed", **fields) -> None:
        ref = f"{kind}:{source}->{target}"
        found = relations.setdefault(ref, {"ref": ref, "kind": kind, "source": source, "target": target,
                                           "status": status, "evidence": []})
        found.update(fields)

    return entity, relation


def _call(relations: dict, source: str, target: str, call: dict) -> None:
    """A resolved call from `source` to `target`, counted, with its site among the 20 a relation keeps."""
    status = call.get("confidence") or "confirmed"
    ref = f"calls:{source}->{target}" + (f" {status}" if status in edge_view.SEEN else "")
    conflict = bool(call.get("conflict"))
    if conflict:
        ref += " conflict"
    found = relations.setdefault(ref, {"ref": ref, "kind": "calls", "source": source, "target": target,
                                       "status": status, "evidence": [], **({"conflict": True} if conflict else {})})
    found["counts"] = {"calls": found.get("counts", {}).get("calls", 0) + 1}
    evidence = {"path": call["file"], "line": call["span"][0]}
    if conflict or status in edge_view.SEEN:
        evidence.update({key: call[key] for key in ("resolver", "conflict") if key in call})
    found["evidence"] = [*found["evidence"], evidence][:20]


def _symbols(store, paths: list[str], cards_path: Path, entity, relation, gaps: list) -> None:
    """The symbols of `paths` from their outlines, with the card freshness the semantic store records and the card's
    purpose."""
    freshness, purpose = {}, {}
    if store.format == "sqlite":
        for chunk in _chunks(paths):
            meta = semantic_store.query_meta_code(store, cards_path=cards_path, paths=chunk,
                                                  include_history=False, limit=LIMIT * 20)
            for row in meta.get("symbols", []):
                freshness[(row["file"], row["name"])] = row["freshness"]
                purpose[(row["file"], row["name"])] = (row.get("card") or {}).get("purpose")
    for path in paths:
        outline = source_reader.outline_manifest(store, path, None, LIMIT)
        if outline.get("truncated"):
            gaps.append({"refs": [f"file:{path}"], "reason": f"symbols truncated at {LIMIT}"})
        for item in outline.get("items", []):
            if not item.get("symbol"):
                continue
            ref = f"symbol:{path}::{item['symbol']}"
            entity(ref, "symbol", item["symbol"], path=path, location="internal",
                   lines=[item.get("start"), item.get("end")], freshness=freshness.get((path, item["symbol"])),
                   description=purpose.get((path, item["symbol"])))
            relation("defines", f"file:{path}", ref)


def build_envelope(run_dir: Path, *, symbols: bool = True) -> dict:
    """The run's envelope; without `symbols`, no file's outline or cards are read and its symbols are only the ends
    of its flows (the app's graph reads a file's symbols when the file is opened: `file_symbols`)."""
    run_dir = Path(run_dir)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    manifest = resolve_run_snapshot(run_dir, state)
    built = modules.ensure_graph(manifest)
    if built.get("state") == "failed":
        raise ValueError(f"module graph not available: {built.get('reason')}")
    graph = modules.load_graph(Path(built["graph"]))
    cards_path = card_store.default_cards_path(manifest)

    entities: dict[str, dict] = {}
    relations: dict[str, dict] = {}
    memberships: list[dict] = []
    gaps: list[dict] = []
    entity, relation = _collector(entities, relations)

    # Modules: components, features, external modules and build units, with their own states.
    by_id = {}
    for module in graph.get("modules", []):
        ref = _module_ref(module)
        by_id[module["id"]] = ref
        external = module.get("location") == "external"
        entity(ref, ref.split(":", 1)[0], module["name"], description=module.get("responsibility") or module.get("description") or "",
               provenance=module.get("provenance"), nature=module.get("nature"), status=module.get("status"),
               languages=module.get("languages"), toolchains=module.get("toolchains"),
               location="external" if external else "internal", node_type="servizio o API" if external else None,
               evidence=[{"path": item.get("path"), "line": item.get("line")} for item in module.get("evidence", [])],
               gaps=list(module.get("gaps", [])))
        if external and not any(item.get("resolved") for item in module.get("evidence", [])):
            gaps.append({"refs": [ref], "reason": "external module without resolved evidence"})
        for conflict in module.get("conflicts", []):
            if conflict.get("kind") == "shared_member":
                gaps.append({"refs": [ref] + [by_id.get(other, f"component:{other}") for other in conflict.get("others", [])],
                             "reason": f"shared_member: {conflict.get('member')}"})
    for gap in graph.get("gaps", []):
        gaps.append({"refs": [by_id[item] for item in gap.get("modules", []) if item in by_id],
                     "reason": gap.get("kind") or gap.get("reason") or json.dumps(gap, sort_keys=True)})
    for edge in graph.get("edges", []):
        if edge.get("source") in by_id and edge.get("target") in by_id:
            relation(edge["kind"], by_id[edge["source"]], by_id[edge["target"]], edge.get("status", "confirmed"),
                     counts={edge["kind"]: edge.get("evidence_total", len(edge.get("evidence", [])))},
                     evidence=[{"path": site.get("path"), "line": site.get("line")} for site in edge.get("evidence", [])[:20]])

    import technologies
    stack = technologies.ensure(manifest)
    for unit in stack.get("modules", stack["units"]):
        if unit["id"] in by_id:
            target_entity = entities[by_id[unit["id"]]]
            if unit["technologies"]:
                target_entity["technologies"] = unit["technologies"]
            for field in ("frameworks", "libraries", "services", "tools"):
                if unit.get(field) is not None:
                    target_entity[field] = unit[field]

    with open_snapshot(manifest) as store:
        root, target = store["root"], store["target"]
        snapshot_digest = logical_digest(store)
        headers = dict(store.iter_file_headers_only())  # one pass, without the symbols a file's entry carries
        paths = sorted(headers)
        # Directories and files: the physical hierarchy.
        for path in paths:
            file_ref = f"file:{path}"
            entity(file_ref, "file", PurePosixPath(path).name, path=path, location="internal",
                   lines=headers[path].get("lines"))
            parent, child = PurePosixPath(path).parent, file_ref
            while str(parent) not in ("", "."):
                directory = f"directory:{parent.as_posix()}"
                entity(directory, "directory", parent.name, path=parent.as_posix(), location="internal")
                relation("contains", directory, child)
                memberships.append({"member": child, "group": directory, "view": "physical"})
                child, parent = directory, parent.parent
        if symbols:
            _symbols(store, paths, cards_path, entity, relation, gaps)
        # Imports and resolved calls between files, read in blocks the reader accepts.
        shown_calls = set()
        for chunk in _chunks(paths):
            packet = source_reader.graph_packet(store, chunk, 1, LIMIT)
            if len(packet.get("imports", [])) >= LIMIT:
                gaps.append({"refs": [], "reason": f"file imports of a block reached the reader limit of {LIMIT}"})
            for link in packet.get("imports", []):
                if f"file:{link['source']}" in entities and f"file:{link['target']}" in entities:
                    relation("imports", f"file:{link['source']}", f"file:{link['target']}")
            if "calls" in packet.get("truncated", []):
                gaps.append({"refs": [], "reason": f"calls of a block reached the reader limit of {LIMIT}"})
            for call in packet.get("calls", []):  # a call resolved to a callable of another file
                source = f"file:{call['file']}"
                for end in edge_view.call_ends(call):
                    target = f"file:{end['target_id'].split('::')[0]}"
                    key = (call["id"], end["target_id"], end["confidence"], end["resolver"])
                    if source != target and source in entities and target in entities and key not in shown_calls:
                        _call(relations, source, target, {**call, **end})
                        shown_calls.add(key)

    # Services the stack recognises (one it only saw mentioned is no module's, nor a node): external modules the
    # registry proposes, with type, site and mark, used by each file that shows them; a mention is an uncertain use.
    import service_registry
    marked = {entry["id"] for entry in service_registry.load()["entries"] if entry.get("mark") or entry.get("mark_source")}
    for item in stack["technologies"]:
        if item["category"] != "service":
            continue
        ref = f"external:{item['id']}"
        proposed = {} if ref in entities else {  # a module the project declares keeps its own states and evidence
            "provenance": "registry", "status": "inferred",
            "evidence": [{"path": s["path"], "line": s["line"]} for s in item["signs"] if s["strength"] == "declared" and s["path"]][:20]}
        entity(ref, "external", item["name"], location="external", node_type=item["type"], site=item["site"],
               mark=item["id"] if item["id"] in marked else None, **proposed)
        for sign in item["signs"]:
            source, certain = f"file:{sign['path']}", sign["strength"] == "declared"
            if source in entities:
                key = f"uses:{source}->{ref}" + ("" if certain else " uncertain")
                used = relations.setdefault(key, {"ref": key, "kind": "uses", "source": source, "target": ref, "counts": {"uses": 0},
                                                  "status": "confirmed" if certain else "uncertain", "evidence": []})
                used["counts"]["uses"] += 1
                used["evidence"] = [*used["evidence"], {"path": sign["path"], "line": sign["line"]}][:20]

    # Memberships: a file belongs to every logical module that holds it; build and virtual units are physical groups.
    for module in graph.get("modules", []):
        ref = by_id[module["id"]]
        view = "physical" if module.get("provenance") in ("build", "virtual") else "logical"
        for path in module.get("files", []):
            if f"file:{path}" in entities:
                memberships.append({"member": f"file:{path}", "group": ref, "view": view})

    envelope_flows, linked = _flows(manifest, entities, by_id, graph, gaps, entity)
    relations.update((item["ref"], item) for item in linked if item["source"] in entities and item["target"] in entities)
    for found in entities.values():
        if "address" in found:
            found["address"] = sanitize_address(found["address"])
    return {
        "schema": SCHEMA,
        "meta": {"project_root": root, "run_id": run_dir.name, "target": target,
                 "git": (graph.get("binding") or {}).get("git"), "snapshot_digest": snapshot_digest,
                 "modules_digest": graph.get("inputs_digest"),
                 "cards_digest": _cards_digest(cards_path, root),
                 "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        "entities": sorted(entities.values(), key=lambda item: item["ref"]),
        "relations": sorted(relations.values(), key=lambda item: item["ref"]),
        "memberships": sorted(memberships, key=lambda item: (item["view"], item["group"], item["member"])),
        "gaps": gaps,
        "flows": envelope_flows,
        "technologies": [{"id": item["id"], "name": item["name"], "type": item["type"] or "altro",
                          "category": item["category"], **({"mark": item["id"]} if item["id"] in marked else {}),
                          "paths": sorted({sign["path"] for sign in item["signs"]
                                           if sign["strength"] == "declared" and sign["path"]}),
                          # the declared sites by which a module's stack holds it, as `technologies.ensure` matches them
                          "evidence": [{"path": sign["path"], "line": sign["line"]} for sign in item["signs"]
                                       if technologies.module_declaration(sign)]}
                         for item in stack["technologies"]],
    }


def file_symbols(run_dir: Path, path: str) -> dict:
    """The symbols of the file `path` of the run, as the envelope has them (outline, card freshness and purpose), and
    the resolved calls that start or end in the file, each with its site and the declaration it reaches, with the first
    line of every declaration the reader gave: the app's graph puts each end on a symbol by its lines
    (`app_view`). Only this file's symbols are read."""
    run_dir = Path(run_dir)
    manifest = resolve_run_snapshot(run_dir, json.loads((run_dir / "state.json").read_text(encoding="utf-8")))
    entities: dict[str, dict] = {}
    gaps: list[dict] = []
    entity, relation = _collector(entities, {})
    with open_snapshot(manifest) as store:
        _symbols(store, [path], card_store.default_cards_path(manifest), entity, relation, gaps)
        packet = source_reader.graph_packet(store, [path], 1, LIMIT)
    if "calls" in packet.get("truncated", []):
        gaps.append({"refs": [f"file:{path}"], "reason": f"calls of the file reached the reader limit of {LIMIT}"})
    return {"entities": list(entities.values()), "gaps": gaps,
            "calls": [{"id": call["id"], "file": call["file"], "line": call["span"][0], **end}
                      for call in packet.get("calls", []) for end in edge_view.call_ends(call)],
            "declarations": {item["id"]: item["span"][0] for item in packet.get("declarations", [])}}


@lru_cache(maxsize=32)
def _index_languages(manifest, snapshot_stamp):
    import flows
    return tuple(flows._links_languages(manifest))


def inputs_stamp(run_dir: Path) -> tuple:
    """The live graph depends on the same evidence and reader versions as its persisted links."""
    import flows
    from store_graph import source_stamp
    import technologies
    run_dir = Path(run_dir)
    manifest = run_dir / "snapshot" / "manifest.sqlite"
    inputs = flows._links_stamp(manifest)
    stable = all(s is None or s[-1] for s in inputs)
    languages = ()
    if inputs[0] and inputs[2]:
        languages = _index_languages(manifest, tuple(inputs[:3])) if stable else flows._links_languages(manifest)
    stamp = [flows._links_key([], inputs, languages)]
    read = [run_dir / "state.json", manifest.with_suffix(".json"), technologies.path(manifest),
            manifest.with_name("flow-rules.json"), card_store.default_cards_path(manifest)]
    for path in read:
        for item in (path, path.with_name(path.name + "-wal")):  # a SQLite store writes its log first
            try:
                identity = source_stamp(item)
            except FileNotFoundError:
                stamp.append((str(item), None))
            else:
                stamp.append((str(item), identity))
                stable = stable and bool(identity[-1])
    if not stable:
        stamp.append(object())  # no filesystem change clock: the next query must recheck its inputs
    return tuple(stamp)


def _cards_digest(cards_path: Path, root: str) -> str | None:
    """Digest of the card store's rows for this project, or None without a store."""
    if not Path(cards_path).is_file():
        return None
    rows = card_store.digests(cards_path, root)
    return hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _site(site: str) -> dict:
    path, _, line = site.rpartition(":")
    return {"path": path, "line": int(line)} if line.isdigit() else {"path": site, "line": None}


def _link_relations(links: dict) -> list[dict]:
    """The deduced links between two files, one relation per kind, files, key and certainty: a route call
    `calls` the file whose route it reaches (`uncertain` when several do), a reader `reads` the file that writes
    the store key it reads. Evidence: the asking sites, then the offering ones. A single side is no relation."""
    found: dict[tuple, dict] = {}

    def add(kind, link_type, key, status, asking, offering):
        source, target = _site(asking)["path"], _site(offering[0])["path"]
        if source == target:
            return
        ref = f"{kind}:file:{source}->file:{target} {link_type} {key}" + (" uncertain" if status == "uncertain" else "")
        item = found.setdefault(ref, {"ref": ref, "kind": kind, "source": f"file:{source}", "target": f"file:{target}",
                                      "status": status, "origin": "dedotto", "link_type": link_type, "key": key,
                                      "counts": {kind: 0}, "asking": [], "offering": []})
        item["counts"][kind] += 1
        item["asking"] += [asking] if asking not in item["asking"] else []
        item["offering"] += [site for site in offering if site not in item["offering"]]

    for edge in links["edges"]:
        if edge.get("route") and edge.get("offered"):
            status = "uncertain" if edge_view.uncertainty(edge) else "confirmed"
            add("calls", "rest", " ".join(edge["route"]), status, edge["site"], [edge["offered"]])
    for gap in links["gaps"]:
        by_file = defaultdict(list)
        for site in gap.get("offered", []):
            by_file[_site(site)["path"]].append(site)
        for sites in by_file.values():
            add("calls", "rest", " ".join(gap["key"]), "uncertain", gap["site"], sites)
    writers = defaultdict(list)
    for edge in links["edges"]:
        if edge["type"] == "scrive":
            writers[edge["to"]].append(edge)
    for edge in links["edges"]:
        if edge["type"] == "legge":
            by_file = defaultdict(list)
            for write in writers.get(edge["from"], []):
                status = "uncertain" if edge_view.uncertainty(edge) or edge_view.uncertainty(write) else "confirmed"
                by_file[_site(write["site"])["path"], status].append(write["site"])
            for (_, status), sites in by_file.items():
                add("reads", "store", edge["from"][len("store:"):], status, edge["site"], sites)
    out = []
    for item in found.values():  # both sides in the 20 sites a relation keeps
        sites = item.pop("asking")[:10] + item.pop("offering")[:10]
        out.append({**item, "evidence": [_site(site) for site in sites]})
    return out


def _flows(manifest: Path, entities: dict, by_id: dict, graph: dict, gaps: list, entity) -> tuple[list[dict], list[dict]]:
    """The run's flows, one per entry point, and its deduced links as relations, when link rules are recorded
    beside its snapshot."""
    rules_path = Path(manifest).with_name("flow-rules.json")
    if not rules_path.is_file():
        return [], []
    import flow_paths
    import flows
    links = flows.cached_links(Path(manifest), flows.load_rules(rules_path))
    names = {module["name"]: by_id[module["id"]] for module in graph.get("modules", []) if module["id"] in by_id}
    store_types = links.get("store_types", {})

    def ref(node: str) -> str:
        if node.startswith("store:"):
            name = node[len("store:"):]
            entity(node, "store", name, location="internal", node_type=store_types.get(name.split("/", 1)[0]))
            return node
        if node.startswith("module:"):
            return names.get(node[len("module:"):], node)
        found = f"symbol:{node}"
        if found not in entities:
            path, name = node.split("::", 1)
            entity(found, "symbol", name.split(".")[-1], path=path, location="internal")
        return found

    for name in links["stores"]:
        ref(f"store:{name}")  # a store is a node of the map even when no flow reaches it
    typed = {entry["symbol"]: "servizio o API" for entry in links["entries"] if entry["kind"] == "rotta"}
    typed.update({edge["from"]: "schermata" for edge in links["edges"] if edge["type"] == "attiva"})
    out = []
    for entry in links["entries"]:
        # A known handler can write on other paths even when the binding of this control is unproved.
        if reason := edge_view.uncertainty(entry):
            flow = {"nodes": [entry["symbol"]], "edges": [], "complete": False,
                    "gaps": [{"site": entry["site"], "reason": reason}]}
        else:
            flow = flows.trace(links, entry["symbol"], "from")
        steps = [{"source": ref(edge["from"]), "target": ref(edge["to"]), "type": edge["type"],
                  "origin": edge["origin"], "site": edge["site"],
                  **{key: edge[key] for key in ("route", "confidence", "resolver", "conflict") if key in edge}}
                 for edge in flow["edges"]]
        out.append({"ref": f"flow:{flow_paths.entry_id(entry)}", "entry": ref(entry["symbol"]), "entry_kind": entry["kind"],
                    **{k: entry[k] for k in ("site", "column", "label", "event", "shape") if k in entry},
                    "complete": flow["complete"], "nodes": sorted({ref(node) for node in flow["nodes"]}), "steps": steps,
                    "gaps": [{k: gap[k] for k in ("site", "reason")} for gap in flow["gaps"]]})
    for node, kind in typed.items():
        target = ref(node)
        if not entities[target].get("node_type"):
            entities[target]["node_type"] = kind
    for gap in links["gaps"]:
        gaps.append({"refs": [ref(gap["symbol"])] if gap.get("symbol") else [], "reason": f"flow: {gap['reason']} ({gap['site']})"})
    return out, _link_relations(links)


def validate_envelope(envelope: dict) -> None:
    """Every reference a relation, a membership or a flow makes names an entity, or ValueError."""
    known = {item["ref"] for item in envelope["entities"]}
    used = [(item["ref"], end) for item in envelope["relations"] for end in (item["source"], item["target"])]
    used += [(f"membership of {item['member']}", end) for item in envelope["memberships"] for end in (item["member"], item["group"])]
    for flow in envelope["flows"]:
        used += [(flow["ref"], end) for end in flow["nodes"]]
        used += [(flow["ref"], end) for step in flow["steps"] for end in (step["source"], step["target"])]
    for owner, end in used:
        if end not in known:
            raise ValueError(f"{owner} names an unknown entity: {end}")


def export(run_dir: Path, store_root: Path) -> Path:
    """Publish the run's envelope once per input digest; an existing export is never rewritten.

    The file is written in a directory beside the destination and moved in place only
    when valid; a snapshot written by another parser identity, or a card store that
    changes while the envelope is built, publishes nothing.
    """
    run_dir, store_root = Path(run_dir).resolve(), Path(store_root).resolve()
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    manifest = resolve_run_snapshot(run_dir, state)
    with open_snapshot(manifest) as store:
        root = store["root"]
        if store.get("parser_fingerprint") != snapshot.parser_fingerprint():
            raise ValueError(f"the snapshot of run {run_dir.name} was written by another parser identity; "
                             "refresh the run before exporting it")
    cards_path = card_store.default_cards_path(manifest)
    before = _cards_digest(cards_path, root)
    envelope = build_envelope(run_dir)
    validate_envelope(envelope)
    if _cards_digest(cards_path, root) != before:
        raise ValueError("the card store changed while the export was built; export again")
    stable = {**envelope, "meta": {key: value for key, value in envelope["meta"].items() if key != "created_at"}}
    digest = hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                            .encode("utf-8")).hexdigest()[:16]
    views = store_root / "views" / run_dir.name
    destination = views / digest
    if destination.is_dir():
        return destination
    views.mkdir(parents=True, exist_ok=True)
    confinement.reject_link_chain(views)
    partial = Path(tempfile.mkdtemp(prefix=f".{digest}.", dir=views))
    try:
        (partial / "visual.json").write_text(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")),
                                             encoding="utf-8")
        os.replace(partial, destination)
    except BaseException:
        shutil.rmtree(partial, ignore_errors=True)
        raise
    return destination


_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
          ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json",
          ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8"}
_POLICY = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; worker-src 'self' blob:"


class _Server(ThreadingHTTPServer):
    # On Windows SO_REUSEADDR lets a second server bind a port in use and take part of its connections.
    allow_reuse_address = sys.platform != "win32"
    linger = 5  # seconds a connection keeps reading after its answer, waiting for the client to close

    def shutdown_request(self, request):
        """Close in stages (RFC 9112, 9.6): a refused POST is answered before its body is read, and a close with
        bytes unread resets the connection, which can erase the answer before the client reads it. So the write
        side closes first, then what the client still sends is read and dropped until it closes, at most
        `linger` seconds."""
        deadline = time.monotonic() + self.linger
        try:
            request.shutdown(socket.SHUT_WR)
            while (left := deadline - time.monotonic()) > 0:
                request.settimeout(left)
                if not request.recv(65536):
                    break
        except OSError:  # the client reset, or still sends at the deadline: the connection closes all the same
            pass
        self.close_request(request)


def live_routes(service) -> dict:
    """The JSON routes of a live explorer over one MapService; a refused request raises ValueError."""
    def envelope(query: dict) -> dict:
        return build_envelope(service.root / "runs" / service.status(query["run"])["run_id"])

    return {"/api/runs": lambda query: service.runs(),
            "/api/events": lambda query: service.events(
                query["run"], after=int(query.get("after", 0)),
                limit=int(query.get("limit", 100)),
                pipeline_after=int(query.get("pipeline_after", 0)),
            ),
            "/api/modules": lambda query: service.modules(query["run"], query=query.get("query")),
            "/api/stack": lambda query: service.stack(query["run"], module=query.get("module")),
            "/api/pulse": lambda query: service.live_pulse(
                after=int(query.get("after", 0)), limit=int(query.get("limit", 100))
            ),
            "/api/requests": lambda query: service.ui_requests(),
            "/api/findings": lambda query: service.ui_findings(),
            "/data/visual.json": envelope}


def live_stream(service):
    """Generator of SSE frames `(event_name, payload_dict)` for `/api/stream`."""
    def frames(query: dict, should_stop):
        run_id = query.get("run")
        after = int(query.get("after", 0))
        pipeline_after = int(query.get("pipeline_after", 0))
        pulse_after = int(query.get("pulse_after", 0))
        once = query.get("once") == "1"
        max_seconds = min(float(query.get("max_seconds", 15)), 60.0)
        deadline = time.monotonic() + max_seconds

        def poll():
            nonlocal after, pipeline_after, pulse_after
            payload: dict = {}
            pulse = service.live_pulse(after=pulse_after, limit=100)
            if pulse["events"]:
                pulse_after = pulse["next_cursor"]
                payload["pulse"] = pulse
            if run_id:
                ev = service.events(run_id, after=after, limit=100, pipeline_after=pipeline_after)
                if ev["events"] or ev["pipeline"]["events"]:
                    after = ev["next_cursor"]
                    pipeline_after = ev["pipeline"]["next_cursor"]
                    payload["run_events"] = ev
            return payload

        initial = {"pulse": service.live_pulse(after=pulse_after, limit=100)}
        pulse_after = initial["pulse"]["next_cursor"]
        if run_id:
            ev = service.events(run_id, after=after, limit=100, pipeline_after=pipeline_after)
            after, pipeline_after = ev["next_cursor"], ev["pipeline"]["next_cursor"]
            initial["run_events"] = ev
        yield "snapshot", initial
        if once:
            return
        while not should_stop() and time.monotonic() < deadline:
            time.sleep(0.15)
            if should_stop():
                break
            delta = poll()
            if delta:
                yield "update", delta

    return {"/api/stream": frames}


def live_actions(service) -> dict:
    """What the page may ask: a request for the host session, and a run, which starts no model."""
    return {"/api/requests": lambda body: service.ui_request(body.get("kind"), body.get("scope"), body.get("text", "")),
            "/api/runs": lambda body: service.create_run(body["target"], body["run_id"])}


def mark_files(marks) -> dict:
    """The image the map's page asks of every server: the mark of the registry entry `id` (`service_registry.Marks`);
    any other id, or none, is 404."""
    return {"/api/mark": lambda query: marks.file(query.get("id"))}


def make_server(export_dir: Path | None, assets_dir: Path, port: int = 0, routes: dict | None = None,
                actions: dict | None = None, token: str | None = None,
                stream: dict | None = None, mounts: dict | None = None, files: dict | None = None) -> ThreadingHTTPServer:
    """A server on 127.0.0.1, read-only without `actions`: the viewer's files listed at start, and the export's envelope.

    `mounts` maps a name to a further folder of files, served under `/<name>/` by the same rules as the assets.

    `routes` maps an exact path to a function of the query that returns JSON, in place of
    an export: a ValueError, a missing parameter or an unreadable file answers 400; a project
    another helper holds (`confinement.ProjectBusy`) answers 503, busy now, as an action does.
    `files` maps an exact path to a function of the query that returns the file to serve, or None
    for none (404); the token may come in the query, as for the stream: an image sends no header.
    `actions` maps an exact path to a function of a POSTed JSON object of at most 16 KiB;
    a POST from another origin, or one that is not JSON, is refused before it is read.
    With `token`, every route and action also needs the `X-Daodan-Token` header: another
    local user who finds the port cannot read the project or queue requests.

    Paths are matched exactly against the list, so no request reaches a file outside it,
    a directory is never listed and a link in the assets is never served. A request whose
    Host is not this server is refused, and no response allows other origins.
    """
    assets_dir = Path(assets_dir).resolve()
    allowed: dict[str, Path] = {}
    folders = [("", assets_dir), *((f"/{name}", Path(folder).resolve()) for name, folder in (mounts or {}).items())]
    for prefix, folder in folders:
        for path in sorted(folder.rglob("*")) if folder.is_dir() else []:
            relative = path.relative_to(folder)
            if path.is_file() and not any((folder / Path(*relative.parts[:index])).is_symlink()
                                          for index in range(1, len(relative.parts) + 1)):
                allowed[f"{prefix}/{relative.as_posix()}"] = path
        if f"{prefix}/index.html" in allowed:
            allowed[f"{prefix}/"] = allowed[f"{prefix}/index.html"]
    if export_dir is not None:
        allowed["/data/visual.json"] = Path(export_dir).resolve() / "visual.json"
    routes, actions, stream, files = routes or {}, actions or {}, stream or {}, files or {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - the stdlib names the method
            port = self.server.server_address[1]
            if self.headers.get("Host") not in (f"127.0.0.1:{port}", f"localhost:{port}"):
                return self._send(421, b"misdirected request", "text/plain; charset=utf-8")
            address = urlsplit(self.path)
            query = dict(parse_qsl(address.query))
            if address.path in stream:
                if not self._authorized(query.get("token")):
                    return self._json(403, {"error": "refused"})
                return self._sse(stream[address.path], query)
            if address.path in routes:
                if not self._authorized():
                    return self._json(403, {"error": "refused"})
                try:
                    return self._json(200, routes[address.path](query))
                except confinement.ProjectBusy as error:
                    return self._json(503, {"error": str(error)})
                except (ValueError, KeyError, TypeError, OSError) as error:
                    return self._json(400, {"error": str(error)})
            if address.path in files:
                if not self._authorized(query.get("token")):
                    return self._json(403, {"error": "refused"})
                try:
                    found = files[address.path](query)
                    body = None if found is None else found.read_bytes()
                except (ValueError, KeyError, TypeError, OSError) as error:
                    return self._json(400, {"error": str(error)})
                if body is None:
                    return self._send(404, b"not found", "text/plain; charset=utf-8")
                return self._send(200, body, _TYPES.get(found.suffix.lower(), "application/octet-stream"))
            if address.path == "/data/visual.json" and not self._authorized():
                return self._json(403, {"error": "refused"})
            target = allowed.get(address.path)
            if target is None or not target.is_file():
                return self._send(404, b"not found", "text/plain; charset=utf-8")
            return self._send(200, target.read_bytes(), _TYPES.get(target.suffix.lower(), "application/octet-stream"))

        def do_POST(self):  # noqa: N802 - the stdlib names the method
            port = self.server.server_address[1]
            origins = (f"http://127.0.0.1:{port}", f"http://localhost:{port}")
            action = actions.get(urlsplit(self.path).path)
            if self.headers.get("Host") not in (origin[7:] for origin in origins):
                return self._send(421, b"misdirected request", "text/plain; charset=utf-8")
            length = self.headers.get("Content-Length") or ""
            length = int(length) if length.isdigit() else 0
            if (action is None or self.headers.get("Origin") not in origins or not 0 < length <= 16384
                    or self.headers.get("Content-Type") != "application/json" or not self._authorized()):
                return self._json(403, {"error": "refused"})
            try:
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("the body is not a JSON object")
                return self._json(200, action(body))
            except confinement.ProjectBusy as error:
                return self._json(503, {"error": str(error)})
            except (ValueError, KeyError, TypeError, OSError) as error:
                return self._json(400, {"error": str(error)})

        def _authorized(self, query_token: str | None = None) -> bool:
            given = self.headers.get("X-Daodan-Token") or query_token or ""
            return token is None or hmac.compare_digest(given, token)

        def _sse(self, producer, query: dict) -> None:
            try:
                iterator = iter(producer(query, lambda: bool(getattr(self.server, "_BaseServer__shutdown_request", False))))
                first_event, first_data = next(iterator)
            except StopIteration:
                first_event, first_data = None, None
            except (ValueError, KeyError, TypeError, OSError) as error:
                return self._json(400, {"error": str(error)})
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                if first_event is not None:
                    self.wfile.write(f"event: {first_event}\ndata: {json.dumps(first_data, ensure_ascii=False, separators=(',', ':'))}\n\n".encode("utf-8"))
                    self.wfile.flush()
                for event_name, payload in iterator:
                    self.wfile.write(f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n\n".encode("utf-8"))
                    self.wfile.flush()
            except OSError:
                pass
            self.close_connection = True

        def _json(self, code: int, value) -> None:
            self._send(code, json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), "application/json")

        def _send(self, code: int, body: bytes, kind: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Security-Policy", _POLICY)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # quiet: the terminal shows only the address
            return

    return _Server(("127.0.0.1", port), Handler)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    envelope_parser = sub.add_parser("envelope", help="print or write the envelope of a run")
    envelope_parser.add_argument("run_dir", type=Path)
    envelope_parser.add_argument("--out", type=Path)
    export_parser = sub.add_parser("export", help="publish the envelope under views/ of the analysis store")
    export_parser.add_argument("run_dir", type=Path)
    serve_parser = sub.add_parser("serve", help="serve an export and the viewer on 127.0.0.1")
    serve_parser.add_argument("export_dir", type=Path)
    serve_parser.add_argument("--assets", type=Path, default=SCRIPT_DIR.parent / "assets" / "viewer")
    serve_parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args(argv)
    if args.command == "envelope":
        text = json.dumps(build_envelope(args.run_dir.resolve()), ensure_ascii=False, separators=(",", ":"))
        if args.out:
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text)
        return 0
    if args.command == "export":
        run_dir = args.run_dir.resolve()
        print(export(run_dir, run_dir.parent.parent))
        return 0
    import service_registry
    marks = service_registry.Marks()
    server = make_server(args.export_dir, args.assets, args.port, files=mark_files(marks))
    print(f"http://127.0.0.1:{server.server_address[1]}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        marks.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
