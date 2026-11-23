"""One binder ties the rows of every entries' source to the snapshot's functions (spec of the pipeline, 8.13, point 2).

No source binds a row: it gives a row on the module with the exports that start a function (`exports`; `methods` when
each export is a method of the route), or a name at a position (`handler` with `site` `file:line`). The binder, in the
links (`connect`), binds both forms the same way for every source: an export to the function the snapshot's export
records name, a name to the one function of that name whose lines hold the position. A source added to the tuple
reaches it with no line changed outside its file and its table. What does not reduce to these forms stays in its
source with the reason beside it (Angular and Astro, the template sources).
"""
from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "daodan/core"))
sys.path.insert(0, str(TESTS))
import premap  # noqa: E402
from test_codebase_map_premap_container_runner import manifest_of  # noqa: E402

SOURCES = {
    "package.json": "{}\n",
    "api/orders.ts": ("export function GET() {\n  return 1;\n}\n\nexport const LIMIT = 5;\n\n"
                      "export function POST() {\n  return 2;\n}\n"),
    "api/legacy.ts": "function handle() {\n  return 2;\n}\n\nexport { handle };\n",
    "web/client.ts": ("function get(path: string) {\n  return path;\n}\n\nfunction post(path: string) {\n  return path;\n}\n\n"
                      "export function loadOrder() {\n  return get(\"/orders/1\");\n}\n\n"
                      "export function saveOrder() {\n  return post(\"/orders/1\");\n}\n\n"
                      "export function openLegacy() {\n  return get(\"/legacy\");\n}\n"),
}
ROWS = [
    # a route handler's module: each method it exports is an entry on its function, with that method
    {"reader": "fake", "shape": "endpoint", "kind": "rotta", "site": "api/orders.ts", "symbol": "api/orders.ts::<module>",
     "path": "/orders/:id", "methods": ["GET", "POST", "DELETE"], "sources": ["fake@v1"]},
    # a module whose export the tool says starts it: `LIMIT` is no function, so the row stays with the gap
    {"reader": "fake", "shape": "page", "kind": "rotta", "site": "api/orders.ts", "symbol": "api/orders.ts::<module>",
     "path": "/limits", "exports": ["LIMIT"], "sources": ["fake@v1"]},
    # a name at a position, as Noir gives a handler
    {"reader": "fake", "shape": "named", "kind": "rotta", "site": "api/legacy.ts:2", "symbol": "api/legacy.ts::<module>",
     "path": "/legacy", "handler": "handle", "sources": ["fake@v1"]},
    # a position the tool names no function at: a gap, never a silent row
    {"reader": "fake", "shape": "named", "kind": "rotta", "site": "api/legacy.ts:5", "symbol": "api/legacy.ts::<module>",
     "path": "/unnamed", "handler": None, "sources": ["fake@v1"]},
]


def _links(tmp_path, monkeypatch, rows=ROWS, rules=()):
    import flows
    _, manifest = manifest_of(tmp_path, SOURCES)
    premap.write(manifest, sources=())
    fake_file = tmp_path / "fake.py"
    fake_file.write_text("# a source of another framework\n", encoding="utf-8")
    fake = types.SimpleNamespace(NAME="fake", __file__=str(fake_file), from_record=lambda report: (rows, []))
    monkeypatch.setattr(premap, "FRAMEWORK_SOURCES", (*premap.FRAMEWORK_SOURCES, fake))
    return flows.link_facts(manifest, list(rules))


def test_the_exports_of_a_module_row_are_entries_on_their_functions_whatever_the_source(tmp_path, monkeypatch):
    links = _links(tmp_path, monkeypatch)
    found = {(e["path"], e["symbol"], e["site"], e.get("method"), e["handler_source"]) for e in links["entries"]
             if e["reader"] == "fake" and not e.get("gap")}
    assert {("/orders/:id", "api/orders.ts::GET", "api/orders.ts:1", "GET", "fake"),
            ("/orders/:id", "api/orders.ts::POST", "api/orders.ts:7", "POST", "fake")} <= found
    # `DELETE` is an export the file does not make: no gap, a route module has the exports it needs
    assert not [e for e in links["entries"] if e.get("method") == "DELETE"]


def test_an_export_that_names_no_function_keeps_the_module_row_with_the_gap_naming_it(tmp_path, monkeypatch):
    links = _links(tmp_path, monkeypatch)
    assert not [e for e in links["entries"] if e["reader"] == "fake" and e["path"] == "/limits"]
    [gap] = [g for g in links["gaps"] if "/limits" in g["reason"]]  # a row with a gap is a gap of the links
    assert gap["symbol"] == "api/orders.ts::<module>" and "LIMIT" in gap["reason"]


def test_a_name_at_a_position_is_the_one_function_of_that_name_whose_lines_hold_it(tmp_path, monkeypatch):
    links = _links(tmp_path, monkeypatch)
    [row] = [e for e in links["entries"] if e["reader"] == "fake" and e["path"] == "/legacy"]
    assert (row["symbol"], row["handler_source"], row.get("gap")) == ("api/legacy.ts::handle", "fake", None)
    [gap] = [g for g in links["gaps"] if g["site"] == "api/legacy.ts:5"]
    assert "without a unique snapshot handler" in gap["reason"]


def test_a_noir_endpoint_with_no_handler_name_is_a_row_at_its_position_that_the_binder_says_is_a_gap():
    """Noir's row always carries `handler`, the name or None, so the binder says what it could not bind."""
    import binder
    from premap import noir
    report = {"endpoints": [{"method": "GET", "url": "/x", "protocol": "http",
                             "details": {"code_paths": [{"path": "/src/app.py", "line": 3}]}}]}
    [row] = noir.rows(report, "/src")
    assert (row["site"], row["handler"]) == ("app.py:3", None)
    facts = types.SimpleNamespace(functions={"app.py": [{"id": "app.py::f", "name": "f", "line": 1, "end": 9}]})
    [bound] = binder.bind([row], facts, resolver=None)
    assert "without a unique snapshot handler" in bound["gap"] and bound["symbol"] == "app.py::<module>"


def test_no_source_of_the_entries_tuple_binds_a_row_itself():
    """The sources of `FRAMEWORK_SOURCES` read their tool's output; binding is the binder's, so none opens the snapshot's
    semantic store or looks an export up."""
    for source in premap.FRAMEWORK_SOURCES:
        tree = ast.parse(Path(source.__file__).read_text(encoding="utf-8"))
        named = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
            alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert "semantic_store" not in named and not {"starts", "exported_target"} & attributes, source.NAME


# --------------------------------------------------------------------- the row's fields, read by field (8.13, point 1)

ROUTE_ROWS = [
    # a route handler: each method it exports is an entry and a route it offers, on the path schema its tool gives
    {"reader": "fake", "shape": "endpoint", "kind": "rotta", "site": "api/orders.ts", "symbol": "api/orders.ts::<module>",
     "path": "/orders/:id", "schema": "/orders/{}", "methods": ["GET", "POST"], "sources": ["fake@v1"]},
    # Noir on the same route, method and file is that entry, not a second
    {"reader": "noir", "shape": "http", "kind": "rotta", "site": "api/orders.ts:1", "symbol": "api/orders.ts::<module>",
     "path": "/orders/:id", "schema": "/orders/{}", "method": "GET", "handler": "GET", "sources": ["noir@1.5.0"]},
    # a page answers any method: it offers no route, and the method Noir gives its path is not copied onto it
    {"reader": "fake", "shape": "view", "kind": "rotta", "site": "api/legacy.ts", "symbol": "api/legacy.ts::<module>",
     "path": "/legacy", "schema": "/legacy", "page": True, "exports": ["handle"], "sources": ["fake@v1"]},
    {"reader": "noir", "shape": "http", "kind": "rotta", "site": "api/legacy.ts:2", "symbol": "api/legacy.ts::<module>",
     "path": "/legacy", "schema": "/legacy", "method": "GET", "handler": "handle", "sources": ["noir@1.5.0"]},
]
CALLS = [{"written": verb, "in": ["web"], "link": "rotta", "route": {"service": "api", "method": verb.upper(), "path": "arg0"}}
         for verb in ("get", "post")]


def test_a_source_added_to_the_tuple_is_bound_joined_with_noir_and_offers_its_routes_with_no_other_line(tmp_path, monkeypatch):
    links = _links(tmp_path, monkeypatch, ROUTE_ROWS, CALLS)
    routed = {(e["from"], e["to"], e["route"][1]) for e in links["edges"] if e.get("route")}
    assert routed == {("web/client.ts::loadOrder", "api/orders.ts::GET", "GET"),
                      ("web/client.ts::saveOrder", "api/orders.ts::POST", "POST")}
    orders = [e for e in links["entries"] if e.get("path") == "/orders/:id"]
    assert sorted((e["method"], e["handler_source"]) for e in orders) == [("GET", "fake"), ("POST", "fake")]
    [page] = [e for e in links["entries"] if e.get("path") == "/legacy"]
    assert (page["symbol"], page["handler_source"], page.get("method")) == ("api/legacy.ts::handle", "fake", None)


def test_the_pages_the_exploration_opens_are_the_rows_marked_page_whose_schema_has_no_parameter():
    """Any source's page (`page`), not one framework's shape; a pattern (`/items/{}`) or a route with no single schema
    is no page to open, and a route handler is no page."""
    from dynamic import app
    record = {"framework_entries": [
        {"reader": "fake", "shape": "view", "page": True, "path": "/about", "schema": "/about", "site": "web/about.ts"},
        {"reader": "fake", "shape": "view", "page": True, "path": "/items/:id", "schema": "/items/{}", "site": "web/items.ts"},
        {"reader": "fake", "shape": "view", "page": True, "path": "/docs/[...all]", "schema": None, "site": "web/docs.ts"},
        {"reader": "fake", "shape": "endpoint", "path": "/api/x", "schema": "/api/x", "site": "web/api.ts"},
        {"reader": "fake", "shape": "view", "page": True, "path": "/other", "schema": "/other", "site": "admin/other.ts"}]}
    assert app._pages(record, "web") == ["/about"]
    assert app._pages(record, ".") == ["/about", "/other"]
