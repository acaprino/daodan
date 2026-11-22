"""The same dynamic destinations and evidence in the store, flows, graph packet and UI."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))

import app_view
import code_graph
import edge_store
import edge_view
import engine_pass
import flows
import modules
import snapshot
import source_reader
import system_brief
import visual


def test_polymorphic_call_keeps_observed_and_sampled_ends_in_both_directions(tmp_path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "dispatch.py").write_text("def dispatch(fn): return fn()\n", encoding="utf-8")
    (root / "handlers.py").write_text("def first(): pass\ndef second(): pass\n", encoding="utf-8")
    manifest = tmp_path / "run" / "manifest.sqlite"
    snapshot.write_snapshot(root, manifest)
    resolver = "test-recorder@1"
    with code_graph.Snapshot(manifest) as snap:
        (ident, file, caller, line, col), = snap.connection.execute(
            "SELECT id,file,caller,l0,c0 FROM sem_references WHERE kind='call'").fetchall()
        place = dict(reference_id=ident, file=file, language="python", kind="call", l0=line, c0=col)
        hole = {**place, "class": "no-occurrence", "resolver": "scip-python", "reason": "missing occurrence"}
        sites = code_graph._sites(snap, "python")
        base = edge_store.language_coverage(sites, [], [hole])
        out = edge_store.default_edge_store(manifest)
        binding = edge_store.store_binding(snap.store, manifest, snap.store.metadata["parser_fingerprint"],
                                           {"python": {"engine": "scip-python", "state": "fresh", "coverage": base}}, {})
        edge_store.write_edge_store(out, [], binding, [hole])
        targets = dict(snap.connection.execute("SELECT name,id FROM sem_declarations WHERE file='handlers.py'"))
        counts = [("first", "observed"), ("second", "observed"), ("second", "sampled")]
        rows = [{**place, "caller": caller, "verdict": "project-callable", "symbol": targets[name],
                 "target_id": targets[name], "resolver": resolver, "confidence": confidence, "payload": {}}
                for name, confidence in counts]
        code_graph.write_observed(snap, out, "python", rows, {"resolver": resolver})
        expected = {(targets[name], confidence) for name, confidence in counts}
        for seed in ("dispatch.py", "handlers.py"):
            call, = source_reader.graph_packet(snap.store, [seed], 1, 30)["calls"]
            assert {(end["target_id"], end["confidence"]) for end in edge_view.call_ends(call)} == expected
            assert call["target_id"] is None  # The call has no single exclusive destination.
    links = flows.link_facts(manifest, [])
    assert system_brief.brief(manifest, [])["steps"]["dinamico"]
    physical = flows.trace(links, "dispatch.py::dispatch", "from")
    assert {(edge["to"], edge["origin"], edge["confidence"], edge["resolver"]) for edge in physical["edges"]} == {
        (f"handlers.py::{name}", "osservato", confidence, resolver) for name, confidence in counts}
    logical = flows.at_level(physical, "logico", {"dispatch.py": "sender", "handlers.py": "handlers"})
    assert {(edge["confidence"], edge["links"]) for edge in logical["edges"]} == {("observed", 2), ("sampled", 1)}
    relations = {}
    for end in edge_view.call_ends(call):
        visual._call(relations, "file:dispatch.py", "file:handlers.py", {**call, **end})
    app_edges = app_view._edges(list(relations.values()), {"file:dispatch.py", "file:handlers.py"}, {})
    assert {(edge["status"], edge["counts"]["calls"]) for edge in app_edges} == {("observed", 2), ("sampled", 1)}
    assert all(site["resolver"] == resolver for edge in app_edges for site in edge["evidence"])


def test_unread_intervals_and_missing_language_lower_coverage(tmp_path):
    files = {"snapshot": 1, "indexed": 1, "missing": [], "unread": [{"path": "ui.ts", "lines": [[1, 4]]}]}
    assert edge_store.language_coverage([], [], [], files)["state"] == "lower-bound"
    root = tmp_path / "project"
    root.mkdir()
    (root / "ui.ts").write_text("export const answer = 42;\n", encoding="utf-8")
    (root / "logic.py").write_text("answer = 42\n", encoding="utf-8")
    manifest = tmp_path / "run" / "manifest.sqlite"
    snapshot.write_snapshot(root, manifest)
    with code_graph.Snapshot(manifest) as snap:
        binding = edge_store.store_binding(snap.store, manifest, snap.store.metadata["parser_fingerprint"],
            {"python": {"engine": "scip-python", "state": "fresh", "coverage": {"state": "complete"}}}, {})
        edge_store.write_edge_store(edge_store.default_edge_store(manifest), [], binding, [])
        view = edge_view.load_edge_view(snap.store)
        assert view["coverage"]["status"] == "lower-bound"
        assert "no engine coverage for typescript" in view["gaps"]


def test_links_reject_old_cache_and_follow_the_engine_wal_and_module_inputs(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.py").write_text("answer = 42\n", encoding="utf-8")
    manifest = tmp_path / "run" / "manifest.sqlite"
    snapshot.write_snapshot(root, manifest)
    with code_graph.Snapshot(manifest) as snap:
        binding = edge_store.store_binding(snap.store, manifest, snap.store.metadata["parser_fingerprint"], {}, {})
        edges = edge_store.default_edge_store(manifest)
        edge_store.write_edge_store(edges, [], binding, [])
    path = manifest.with_name("flow-links.json")
    old = ["daodan/flow-links/v2", "[]", str(manifest.stat().st_mtime_ns), str(edges.stat().st_mtime_ns)]
    old_key = hashlib.sha256("\0".join(old).encode()).hexdigest()
    path.write_text(json.dumps({"key": old_key, "links": {"generation": 0}}), encoding="utf-8")
    generations = []
    def count(*args, **kwargs):
        generations.append(len(generations) + 1)
        return {"generation": generations[-1]}
    monkeypatch.setattr(flows, "link_facts", count)
    assert flows.cached_links(manifest, []) == {"generation": 1}
    assert flows.cached_links(manifest, []) == {"generation": 1}
    monkeypatch.setattr(engine_pass, "adapter_fingerprint", lambda name: f"new-{name}")
    assert flows.cached_links(manifest, []) == {"generation": 2}
    edges.with_name(edges.name + "-wal").write_bytes(b"synthetic WAL stamp")
    assert flows.cached_links(manifest, []) == {"generation": 3}
    modules.write_ledger(manifest, [], replace=True)
    assert flows.cached_links(manifest, []) == {"generation": 4}
    assert flows.cached_links(manifest, []) == {"generation": 4}
    monkeypatch.setattr(flows, "_links_reader_digest", lambda: "next-reader")
    assert flows.cached_links(manifest, []) == {"generation": 5}
