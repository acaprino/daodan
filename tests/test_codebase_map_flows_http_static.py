"""HTTP calls linked to the declared routes with no rule (`flows.link_facts` with `[]`).

A call the engine resolves into the client table (`daodan/data/http-clients.json`) asks for a route read where the table
says, as a rule reads it (`flows._value`); a call of a wrapper `http_wrappers.py` proves asks by the rule it proposes. The
routes offered are the ones `find_entry_points` declares (`entry-points.json`, service `*`). The snapshot is the one of
`fixtures/http-wrapper` with the index scip-typescript wrote for it (`src/static.ts` holds the direct calls); Noir's
report, which the container gives, is written here.
"""
import json
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "daodan/core"))
sys.path.insert(0, str(TESTS))
import code_graph  # noqa: E402
import entry_points  # noqa: E402
import flows  # noqa: E402
import resolve_edges  # noqa: E402
from indexers import typescript  # noqa: E402
from test_codebase_map_flows import read_project  # noqa: E402
from test_codebase_map_flows_http_wrapper import FIXTURE, sources  # noqa: E402
from test_codebase_map_manifest_entries import noir_route  # noqa: E402

NOIR = {"endpoints": [  # the functions of `src/server.ts`, by line
    noir_route("/api/orders", "POST", "src/server.ts", "createOrder", 12),
    noir_route("/api/twin", "GET", "src/server.ts", "listPing", 11),
    noir_route("/api/twin", "GET", "src/server.ts", "showWindow", 16)]}


@pytest.fixture(scope="module")
def links(tmp_path_factory):
    from entry_points import noir
    manifest = read_project(tmp_path_factory.mktemp("http-static"), sources())
    with code_graph.Snapshot(manifest) as snap:
        index = code_graph.Index(snap.root)
        index.load(FIXTURE / "index.scip")
        hops, traversal, _ = code_graph.adapter_traversal(typescript, index, snap)
        built = {language: code_graph.build(index, snap, language, hops,
                                            {"name": "scip-typescript", "version": typescript.VERSION}, None, traversal)
                 for language in ("javascript", "typescript")}
        code_graph.write_store(snap, resolve_edges.default_edge_store(manifest), built, f"scip-typescript@{typescript.VERSION}")
    entry_points.write(manifest, sources=(noir,), runner=lambda commands: [
        {"root": "/work", "returncode": 0, "stdout": json.dumps(NOIR), "stderr": ""}])
    return flows.link_facts(manifest, [])


def arcs(links, caller):
    return [(edge["to"], edge["route"]) for edge in links["edges"] if edge.get("route") and edge["from"] == caller]


def gaps(links, symbol):
    return [gap for gap in links["gaps"] if gap["symbol"] == symbol]


def test_a_call_of_the_client_meets_the_declared_route_of_its_method_and_path(links):
    assert arcs(links, "src/static.ts::createDirect") == [("src/server.ts::createOrder", ["*", "POST", "/api/orders"])]
    assert gaps(links, "src/static.ts::createDirect") == []


def test_a_computed_url_is_a_gap(links):
    assert arcs(links, "src/static.ts::computedDirect") == []
    assert [(gap["site"], gap["reason"]) for gap in gaps(links, "src/static.ts::computedDirect")] == [
        ("src/static.ts:10", "rotta: route not a literal")]


def test_two_declared_routes_are_an_uncertain_link(links):
    assert arcs(links, "src/static.ts::twinDirect") == []
    [gap] = gaps(links, "src/static.ts::twinDirect")
    assert gap["reason"] == "route GET /api/twin: several handlers"  # the method is the table's default
    assert gap["candidates"] == ["src/server.ts::listPing", "src/server.ts::showWindow"]


def test_a_call_through_a_proved_wrapper_meets_the_declared_route(links):
    assert ("src/server.ts::createOrder", ["*", "POST", "/api/orders"]) in arcs(links, "src/callers.ts::useAll")
    # the wrapper's own call of the client reads its parameter: the calls of the wrapper ask, it does not
    assert gaps(links, "src/client.ts::plain") == []
