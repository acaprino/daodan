"""Express's routes from a module of Daodan's (`entry_points/express.py`, `T1.C.8`): the method of GitNexus in our words
(`benchmarks/express-routes/README.md`), the forms of the calls as data (`entry-queries.json`, `express`), the trees and the names
of the snapshot, and the binder's third form, the span of the handler.

The fixtures (`tests/fixtures/entry-points/express/`): `v4`, Express 4 in CommonJS (an app and its routers in several files, `use`
with a nested prefix, `route().get().post()`, an array of handlers, a handler imported by name, handlers written in place, a router
passed to a function, a computed path and a computed prefix, `app.get('env')`); `v5`, Express 5 in TypeScript with ES modules (named
`Router`, a router exported and imported, a namespace import, `all`, the path syntax of Express 5). Nothing of them runs.
"""
from __future__ import annotations

import shutil
import sys
import types
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "daodan/core"))
import binder  # noqa: E402
import entries  # noqa: E402
import entry_points  # noqa: E402
import flows  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from entry_points import express  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

FIXTURES = TESTS / "fixtures/entry-points/express"


def _read(tmp_path, case: str) -> tuple[list[dict], list[dict]]:
    """The rows the module reads on a fixture, and the same rows as the binder ties them."""
    shutil.copytree(FIXTURES / case, tmp_path / "proj")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(tmp_path / "proj", manifest)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        facts = flows.Facts(store, db)
        found = express.rows(facts)
        return found, binder.bind(found, facts, facts.resolver)


def _routes(rows: list[dict]) -> set[tuple]:
    return {(row["method"], row["path"], row.get("symbol")) for row in rows if not row.get("gap")}


def _gaps(rows: list[dict]) -> set[tuple]:
    return {(row["site"], row["gap"]) for row in rows if row.get("gap")}


def test_the_query_of_each_grammar_compiles():
    for grammar in ("javascript", "typescript", "tsx"):
        assert entries._query(grammar, express.NAME) is not None, grammar


def test_express_4_prefixes_of_use_are_composed_across_files_and_each_handler_is_bound_by_its_span(tmp_path):
    found, bound = _read(tmp_path, "v4")
    spans = {(row["method"], row["path"]): (row["site"], row["span"]) for row in found if not row.get("gap")}
    # the site and the span are the handler's, not the registration's: `list` is declared at line 5 of the router's file
    assert spans["GET", "/api/v1/users"] == ("routes/users.js:5", [5, 0, 7, 1])
    assert all(row["schema"] == flows.path_schema(row["path"]) for row in found if not row.get("gap"))
    assert _routes(bound) == {
        ("GET", "/api/v1/users", "routes/users.js::list"),  # router mounted under `/users` on a router under `/api/v1`
        ("GET", "/api/v1/users/:id", "routes/users.js::show"),  # `route('/:id').get(show).post(update)`
        ("POST", "/api/v1/users/:id", "routes/users.js::update"),
        ("GET", "/api/v1/status", "status.js::GET /api/v1/status"),  # a router passed to a function; its handler written in place
        ("GET", "/health", "handlers.js::health"),  # imported by name: `const { health } = require(...)`, `module.exports = { health }`
        ("POST", "/login", "app.js::POST /login"),  # written in place: named by its route
        ("GET", "/multi", "app.js::multi"),  # an array of handlers: the last
        ("PUT", "/checked", "app.js::PUT /checked"),  # a chain of handlers: the last
    }
    assert {row["shape"] for row in found if row["path"] == "/api/v1/users/:id"} == {"route"}
    assert all(row["handler_source"] == "express" for row in bound if not row.get("gap"))


def test_a_computed_path_and_a_computed_prefix_are_gaps_with_the_cause_and_a_setting_is_no_route(tmp_path):
    found, _ = _read(tmp_path, "v4")
    unknown = "mounted under a prefix that is no literal at app.js:26"
    assert _gaps(found) == {
        ("app.js:25", "express route GET (computed): the path is no literal"),
        ("routes/users.js:17", f"express route GET /: {unknown}"),
        ("routes/users.js:18", f"express route GET /:id: {unknown}"),
        ("routes/users.js:18", f"express route POST /:id: {unknown}"),
    }
    assert all(row["symbol"].endswith("::<module>") for row in found if row.get("gap"))
    assert not [row for row in found if row["site"] == "app.js:27"]  # `app.get('env')`: Express's getter of a setting
    assert not (tmp_path / "proj/ran.txt").exists()  # the app writes this file when it runs: it is read, never run (AGENTS.md)


def test_express_5_with_es_modules_a_named_router_an_exported_router_and_all(tmp_path):
    found, bound = _read(tmp_path, "v5")
    assert _routes(bound) == {
        ("DELETE", "/admin/cache", "src/app.ts::DELETE /admin/cache"),
        ("GET", "/admin/orders/:id", "src/orders.ts::getOrder"),  # `export const orders = Router()`, imported and mounted
        (None, "/admin/orders/:id/audit", "src/orders.ts::getOrder"),  # `all`: any method
        ("GET", "/files/{*path}", "src/files.ts::download"),  # a namespace import's member; the path syntax of Express 5
    }
    assert not _gaps(found)
    assert {row["schema"] for row in found if row["path"] == "/admin/orders/:id"} == {"/admin/orders/{}"}


def test_the_binder_ties_a_span_to_the_one_function_with_it_and_says_why_it_cannot():
    """The third form: an equality of two data, the span the reader gives and the snapshot's own; none, or two, is a gap."""
    declared = [{"id": "a.js::function@1:0", "name": "one", "line": 1, "end": 3, "span": [1, 0, 3, 1]},
                {"id": "a.js::function@5:0", "name": "two", "line": 5, "end": 7, "span": [5, 0, 7, 1]},
                {"id": "a.js::function@9:0", "name": "three", "line": 9, "end": 9, "span": [9, 0, 9, 9]},
                {"id": "a.js::function@9:0b", "name": "four", "line": 9, "end": 9, "span": [9, 0, 9, 9]}]
    facts = types.SimpleNamespace(functions={"a.js": declared}, route_named={}, own_node=lambda ident: ident, node=lambda ident: ident,
                                  property_label=lambda declaration: None, name_routes=lambda names: None)
    base = {"reader": "express", "shape": "method", "kind": "rotta", "method": "GET", "path": "/x", "symbol": "a.js::<module>"}
    one, none, two = binder.bind([{**base, "site": "a.js:5", "span": [5, 0, 7, 1]}, {**base, "site": "a.js:2", "span": [2, 0, 2, 4]},
                                  {**base, "site": "a.js:9", "span": [9, 0, 9, 9]}], facts, resolver=None)
    assert (one["symbol"], one["handler_source"], one.get("gap")) == ("a.js::function@5:0", "express", None)
    assert none["gap"].endswith("no function of the snapshot has the span of the handler")
    assert two["gap"].endswith("several functions of the snapshot have the span of the handler")


def test_express_is_a_primary_source_of_the_union_with_noir_and_is_not_run_by_the_step_yet():
    """A Noir route on the schema of an Express row in the same file is that row (`one_entry`); `T1.C.9` wires the module."""
    mine = {"reader": "express", "shape": "method", "kind": "rotta", "method": "GET", "path": "/users/:id", "schema": "/users/{}",
            "site": "routes/users.js:9", "symbol": "routes/users.js::show"}
    noir = {"reader": "noir", "shape": "http", "kind": "rotta", "method": "GET", "path": "/users/:id", "schema": "/users/{}",
            "site": "routes/users.js:18", "symbol": "routes/users.js::show"}
    other = {**noir, "path": "/users", "schema": "/users"}
    assert entry_points.one_entry([mine, noir, other]) == [mine, other]
    assert express not in entry_points.SOURCES and express in entry_points.TREE_SOURCES
    flows.validate_rules([{"link": "ingresso", "reader": "express", "shape": "method", "entry": "rotta", "source": "modello"}])
