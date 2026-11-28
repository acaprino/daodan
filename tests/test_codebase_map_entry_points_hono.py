"""Hono's routes from the module of Express (`entry_points/express.py`, `T1.C.10`): the same code on the data of the `hono` section of
`entry-queries.json` (`new Hono()`, `route` that mounts, `basePath`, verbs that return their app), bound by the span of the handler.

The fixture (`tests/fixtures/entry-points/hono/`, TypeScript, ES modules): an app and two sub-apps in other files, a `basePath` app that
mounts one of them, a named handler imported, handlers written in place, a chain of verbs, `all`, a middleware, a prefix that is no
literal. Nothing of it runs.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "daodan/core"))
import binder  # noqa: E402
import entry_points  # noqa: E402
import flows  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from entry_points import express  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

FIXTURE = TESTS / "fixtures/entry-points/hono"


def _read(tmp_path, sections=express.SECTIONS) -> tuple[list[dict], list[dict]]:
    shutil.copytree(FIXTURE, tmp_path / "proj")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(tmp_path / "proj", manifest)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        facts = flows.Facts(store, db)
        found = express.rows(facts, sections)
        return found, binder.bind(found, facts, facts.resolver)


def test_hono_routes_compose_route_and_base_path_across_files_and_bind_each_handler_by_its_span(tmp_path):
    found, bound = _read(tmp_path)
    assert {(row["method"], row["path"], row.get("symbol")) for row in bound if not row.get("gap")} == {
        ("GET", "/health", "src/handlers.ts::health"),  # imported by name
        ("POST", "/login", "src/index.ts::POST /login"),  # written in place: named by its route
        ("GET", "/me", "src/index.ts::GET /me"),  # a verb on the app the verb before returns
        ("GET", "/api/users", "src/users.ts::list"),  # `route('/users', users)` on a `basePath('/api')` app, mounted at `/`
        (None, "/api/users/:id", "src/users.ts::ANY /api/users/:id"),  # `all`: any method
        ("DELETE", "/api/cache", "src/index.ts::DELETE /api/cache"),  # a route of the `basePath` app itself
    }
    assert {row["reader"] for row in found} == {"hono"}
    assert all(row["handler_source"] == "hono" for row in bound if not row.get("gap"))
    assert all(row["schema"] == flows.path_schema(row["path"]) for row in found if not row.get("gap"))
    assert not (tmp_path / "proj/ran.txt").exists()  # read, never run (AGENTS.md)


def test_a_prefix_that_is_no_literal_is_a_gap_and_a_middleware_is_no_route(tmp_path):
    found, _ = _read(tmp_path)
    assert {(row["site"], row["gap"]) for row in found if row.get("gap")} == {
        ("src/other.ts:5", "hono route GET /o: mounted under a prefix that is no literal at src/index.ts:21")}
    assert not [row for row in found if row.get("registered", row["site"]).startswith("src/index.ts:14")]  # `use`: a middleware


def test_each_library_is_read_only_for_its_section(tmp_path):
    found, _ = _read(tmp_path, ("express",))
    assert found == []


def test_hono_rows_are_rows_of_a_tree_source():
    assert entry_points.tree_readers() == ("express", "hono")
    flows.validate_rules([{"link": "ingresso", "reader": "hono", "shape": "method", "entry": "rotta", "source": "modello"}])
