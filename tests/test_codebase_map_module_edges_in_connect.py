"""The module graph's `imports` and `calls` edges are no longer `scan`'s (spec of the pipeline, 8.11 step 5, piece A).

They join files `parse` reads to the modules `scan` establishes (8.2), so `scan` writes the modules and the edges that need no
symbol (`declares`, `contains`, `uses`), reading none, and the first reader of the whole graph (`modules.ensure_graph`, which
every reader and the `union` step call) adds `imports` and `calls` in a second write of the same `modules.json`. The graph
every reader gets is the one of before.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules  # noqa: E402
import pipeline  # noqa: E402
import snapshot  # noqa: E402
# Imported before any patch: they take `semantic_reader` by name when first imported, and would keep the patch's raiser.
import store_consumers  # noqa: E402,F401
import store_graph  # noqa: E402,F401
from test_codebase_map_premap_container_runner import manifest_of  # noqa: E402

FILES = {
    "libs/a/package.json": '{"name":"@acme/a","dependencies":{"@acme/b":"1"}}', "libs/a/project.json": '{"name":"a"}',
    "libs/a/index.ts": 'import { b } from "../b/index";\n\nexport function a() {\n  return b();\n}\n',
    "libs/b/package.json": '{"name":"@acme/b"}', "libs/b/index.ts": "export function b() {\n  return 1;\n}\n",
}
# The graph of before (measured on commit b2835a9, scan and the edges in one pass): `@acme/a` declares and imports `@acme/b`.
BEFORE = {"imports": [["@acme/a", "@acme/b"]], "declares": [["@acme/a", "@acme/b"]], "calls": [], "contains": [], "uses": []}


def _kinds(graph: dict) -> set[str]:
    return {edge["kind"] for edge in graph["edges"]}


def _relations(graph: dict) -> dict:
    names = {module["id"]: module["name"] for module in graph["modules"]}
    return {kind: sorted([names.get(e["source"], e["source"]), names.get(e["target"], e["target"])]
                         for e in graph["edges"] if e["kind"] == kind) for kind in BEFORE}


def test_scan_writes_the_modules_reading_no_symbol_and_the_graph_readers_get_is_the_whole_one(tmp_path):
    import semantic_store
    _, manifest = manifest_of(tmp_path / "split", FILES)
    no_symbols = AssertionError("scan read the snapshot's symbols")
    with mock.patch.object(snapshot, "resolved_imports", side_effect=no_symbols), \
            mock.patch.object(semantic_store, "semantic_reader", side_effect=no_symbols):
        result = pipeline.run(manifest, start="scan", stop="scan", fast_scan=True)
    assert "failed" not in result["scan"]
    scanned = json.loads(modules.graph_name(manifest).read_text(encoding="utf-8"))
    assert not {"imports", "calls"} & _kinds(scanned) and "declares" in _kinds(scanned)

    whole = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    assert _relations(whole) == BEFORE
    assert whole["coverage"]["edges"] == {kind: len(pairs) for kind, pairs in BEFORE.items()}


def test_the_union_step_leaves_the_whole_graph(tmp_path):
    _, manifest = manifest_of(tmp_path, FILES)
    pipeline.run(manifest, start="scan", stop="scan", fast_scan=True)
    with mock.patch.object(pipeline.Analyze, "run", return_value={}), \
            mock.patch.object(pipeline.Dynamic, "run", return_value={}):
        pipeline.run(manifest, start="union")
    graph = json.loads(modules.graph_name(manifest).read_text(encoding="utf-8"))
    assert "imports" in _kinds(graph)
