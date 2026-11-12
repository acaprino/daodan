#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""A Codebase Map run as `daodan/visual@1`: what the explorer draws, with nothing inferred here.

Reads only public APIs: the run snapshot (`snapshot_store`), the module graph (`modules`),
outlines and file imports (`source_reader`), card freshness (`semantic_store`) and, when
the run has link rules, its flows (`flows`). States keep the producers' values:
`provenance`, `status` and card `freshness` are distinct fields, never promoted.

Every node carries `location` (`internal`, `external`) and, when known, `node_type`
from the closed list of the flow model: an external module is a service or API, a
route handler a service or API, the symbol that binds a user action a screen, a store
the type its link rule names. A node of unknown type has none.

    python visual.py envelope RUN_DIR [--out FILE]
    python visual.py export RUN_DIR        # publishes .daodan/map/views/<run>/<digest>/visual.json
    python visual.py serve EXPORT_DIR      # http://127.0.0.1:<port>/, read-only

The MCP server serves the same page live (`codebase_map_ui`): `live_routes` answers with the
project's runs, a run's events and a run's envelope built at each request.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qsl, urlsplit, urlunsplit

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import card_store  # noqa: E402
import confinement  # noqa: E402
import modules  # noqa: E402
import snapshot  # noqa: E402
import semantic_store  # noqa: E402
import source_reader  # noqa: E402
from snapshot_store import file_headers, logical_digest, open_snapshot, resolve_run_snapshot  # noqa: E402

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
        "build" if module.get("provenance") == "build" else module.get("kind", "component"))
    return f"{kind}:{module['id']}"


def build_envelope(run_dir: Path) -> dict:
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

    # Modules: components, features, external modules and build units, with their own states.
    by_id = {}
    for module in graph.get("modules", []):
        ref = _module_ref(module)
        by_id[module["id"]] = ref
        external = module.get("location") == "external"
        entity(ref, ref.split(":", 1)[0], module["name"], description=module.get("responsibility") or module.get("description") or "",
               provenance=module.get("provenance"), status=module.get("status"),
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

    with open_snapshot(manifest) as store:
        root, target = store["root"], store["target"]
        snapshot_digest = logical_digest(store)
        paths = sorted(file_headers(store))
        headers = file_headers(store)
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
        # Symbols, with the card freshness the semantic store records and the card's purpose.
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
        # Imports between files, read in blocks the reader accepts.
        for chunk in _chunks(paths):
            packet = source_reader.graph_packet(store, chunk, 1, LIMIT)
            if len(packet.get("imports", [])) >= LIMIT:
                gaps.append({"refs": [], "reason": f"file imports of a block reached the reader limit of {LIMIT}"})
            for link in packet.get("imports", []):
                if f"file:{link['source']}" in entities and f"file:{link['target']}" in entities:
                    relation("imports", f"file:{link['source']}", f"file:{link['target']}")

    # Memberships: a file belongs to every logical module that holds it; build units are physical groups.
    for module in graph.get("modules", []):
        ref = by_id[module["id"]]
        view = "physical" if module.get("provenance") == "build" else "logical"
        for path in module.get("files", []):
            if f"file:{path}" in entities:
                memberships.append({"member": f"file:{path}", "group": ref, "view": view})

    envelope_flows = _flows(manifest, entities, by_id, graph, gaps, entity)
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
    }


def _cards_digest(cards_path: Path, root: str) -> str | None:
    """Digest of the card store's rows for this project, or None without a store."""
    if not Path(cards_path).is_file():
        return None
    rows = card_store.digests(cards_path, root)
    return hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _flows(manifest: Path, entities: dict, by_id: dict, graph: dict, gaps: list, entity) -> list[dict]:
    """The run's flows, one per entry point, when link rules are recorded beside its snapshot."""
    rules_path = Path(manifest).with_name("flow-rules.json")
    if not rules_path.is_file():
        return []
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
        flow = flows.trace(links, entry["symbol"], "from")
        steps = [{"source": ref(edge["from"]), "target": ref(edge["to"]), "type": edge["type"],
                  "origin": edge["origin"], "site": edge["site"], **({"route": edge["route"]} if edge.get("route") else {})}
                 for edge in flow["edges"]]
        out.append({"ref": f"flow:{ref(entry['symbol'])}", "entry": ref(entry["symbol"]), "entry_kind": entry["kind"],
                    "complete": flow["complete"], "nodes": sorted({ref(node) for node in flow["nodes"]}), "steps": steps})
    for node, kind in typed.items():
        target = ref(node)
        if not entities[target].get("node_type"):
            entities[target]["node_type"] = kind
    for gap in links["gaps"]:
        gaps.append({"refs": [ref(gap["symbol"])] if gap.get("symbol") else [], "reason": f"flow: {gap['reason']} ({gap['site']})"})
    return out


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
          ".svg": "image/svg+xml", ".png": "image/png", ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8"}
_POLICY = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; worker-src 'self' blob:"


def live_routes(service) -> dict:
    """The JSON routes of a live explorer over one MapService; a refused request raises ValueError."""
    def envelope(query: dict) -> dict:
        return build_envelope(service.root / "runs" / service.status(query["run"])["run_id"])

    return {"/api/runs": lambda query: service.runs(),
            "/api/events": lambda query: service.events(query["run"], after=int(query.get("after", 0))),
            "/data/visual.json": envelope}


def make_server(export_dir: Path | None, assets_dir: Path, port: int = 0, routes: dict | None = None) -> ThreadingHTTPServer:
    """A read-only server on 127.0.0.1: the viewer's files listed at start, and the export's envelope.

    `routes` maps an exact path to a function of the query that returns JSON, in place of
    an export: a ValueError, a missing parameter or an unreadable file answers 400.

    Paths are matched exactly against the list, so no request reaches a file outside it,
    a directory is never listed and a link in the assets is never served. A request whose
    Host is not this server is refused, and no response allows other origins.
    """
    assets_dir = Path(assets_dir).resolve()
    allowed: dict[str, Path] = {}
    for path in sorted(assets_dir.rglob("*")) if assets_dir.is_dir() else []:
        relative = path.relative_to(assets_dir)
        if path.is_file() and not any((assets_dir / Path(*relative.parts[:index])).is_symlink()
                                      for index in range(1, len(relative.parts) + 1)):
            allowed["/" + relative.as_posix()] = path
    if "/index.html" in allowed:
        allowed["/"] = allowed["/index.html"]
    if export_dir is not None:
        allowed["/data/visual.json"] = Path(export_dir).resolve() / "visual.json"
    routes = routes or {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - the stdlib names the method
            port = self.server.server_address[1]
            if self.headers.get("Host") not in (f"127.0.0.1:{port}", f"localhost:{port}"):
                return self._send(421, b"misdirected request", "text/plain; charset=utf-8")
            address = urlsplit(self.path)
            if address.path in routes:
                try:
                    return self._json(200, routes[address.path](dict(parse_qsl(address.query))))
                except (ValueError, KeyError, OSError) as error:
                    return self._json(400, {"error": str(error)})
            target = allowed.get(address.path)
            if target is None or not target.is_file():
                return self._send(404, b"not found", "text/plain; charset=utf-8")
            return self._send(200, target.read_bytes(), _TYPES.get(target.suffix.lower(), "application/octet-stream"))

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

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


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
    serve_parser.add_argument("--assets", type=Path, default=SCRIPT_DIR.parents[2] / "assets" / "viewer")
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
    server = make_server(args.export_dir, args.assets, args.port)
    print(f"http://127.0.0.1:{server.server_address[1]}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
