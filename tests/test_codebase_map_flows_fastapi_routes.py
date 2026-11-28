"""The routes of a FastAPI application are offered routes (`flows.link_facts`), like Noir's, Next.js's and Flask's: a call of the client meets them.

The FastAPI rows are the ones `entry_points/fastapi_app.py` makes from the answer recorded on Modal (`tests/fixtures/premap/fastapi/routes.json`) over the
fixture of `benchmarks/fastapi-routes/`; the Noir rows are built in line (what Noir prints is not run here). Each row carries the path schema
`fastapi_app` makes from Starlette's own compiled path and convertors (`/api/users/{user_id}` is `/api/users/{}`, as Noir's `/api/users/:user_id`), or none
where a parameter may hold a `/` or its convertor does not say it holds one segment: that route is a gap of the declared routes and meets no call. A websocket
is an entry and offers no route: no schema, so no gap either.

The source is not registered in the shared files, by decision (`benchmarks/fastapi-routes/README.md`, «Applicazioni vere»): the fixture registers it for the module
(`monkeypatch`), and the test that checks the real registry is `xfail(strict)` (`WAITS`, in `test_codebase_map_premap_fastapi.py`) until `wiring/wiring.diff` is applied.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import entries
import flows
import entry_points
import premap
from entry_points import fastapi_app, noir
from test_codebase_map_manifest_entries import noir_route
from test_codebase_map_container_runner import manifest_of, write_both
from test_codebase_map_premap_fastapi import QUERIES, WAITS, WIRED, project, recorded

RULES = [
    {"written": "apiGet", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "GET", "path": "arg0"}},
    {"written": "apiDelete", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "DELETE", "path": "arg0"}},
]
CLIENT = "\n".join([
    "declare function apiGet(url: string): void;",
    "declare function apiDelete(url: string): void;",
    "export function viewUser() { apiGet('/api/users/7'); }",
    "export function removeUser() { apiDelete('/api/users/7'); }",
    "export function viewUserDeep() { apiGet('/api/users/7/delete'); }",  # one segment more
    "export function viewTyped() { apiGet('/typed/7'); }",  # `/typed/{n:int}`
    "export function viewSub() { apiGet('/sub/items/3'); }",  # a mounted application
    "export function viewTenant() { apiGet('/t/acme/info'); }",  # a mount with a parameter of its own
    "export function viewFile() { apiGet('/files/a/b'); }",  # `/files/{file_path:path}`: a name that holds a `/`
    "export function viewSlug() { apiGet('/slug/a-b'); }",  # `/slug/{s:slug}`: a convertor of the project's, which does not say
    "export function viewGlued() { apiGet('/glued/x-y'); }",  # `/glued/{a}-{b}`
    "export function viewStrict() { apiGet('/strict'); }",  # `/strict/`
    "export function viewStrictSlash() { apiGet('/strict/'); }",
    "export function viewLoose() { apiGet('/loose'); }",
    "export function viewDocs() { apiGet('/docs'); }",  # FastAPI's own view, in the environment: no route of the project
    ""])
NOIR = {"endpoints": [  # the same function FastAPI's row is on: Noir's spelling of the route is the text of the decorator
    noir_route("/api/users/{user_id}", "GET", "app/routers/users.py", "read_user", 11),
    noir_route("/api/users/{user_id}", "DELETE", "app/routers/users.py", "delete_user", 16),
    noir_route("/loose", "GET", "app/main.py", "loose", 1)]}  # the line is not the one of the def: the function is the key


@pytest.fixture(scope="module")
def links(tmp_path_factory):
    def run(commands):
        if commands[0]["tool"] == "noir":
            return [{"root": "/work", "returncode": 0, "stdout": json.dumps(NOIR), "stderr": ""}]
        return [recorded("routes") for _ in commands]
    _, manifest = manifest_of(tmp_path_factory.mktemp("fastapi-routes"), {**project(), "web/client.ts": CLIENT})
    with pytest.MonkeyPatch.context() as patch:  # the wiring of shared files, for this fixture only: see the module's docstring
        if not WIRED["queries"]:
            patch.setitem(entries.QUERIES, "fastapi", QUERIES)
        if not WIRED["registry"]:
            patch.setattr(entry_points, "FRAMEWORK_SOURCES", (*entry_points.FRAMEWORK_SOURCES, fastapi_app))
        write_both(manifest, sources=(premap.module_graph, premap.requirements, noir, fastapi_app), runner=run)
        return flows.link_facts(manifest, flows.validate_rules(RULES))


def arcs(links):
    return {(e["from"].split("::")[1], e["to"], tuple(e["route"])) for e in links["edges"] if e.get("route")}


def reasons(links):
    return [g["reason"] for g in links["gaps"]]


@WAITS
def test_fastapi_is_a_framework_source_whose_rows_are_entries_of_the_links():
    assert fastapi_app in entry_points.FRAMEWORK_SOURCES and fastapi_app in entry_points.SOURCES
    assert entry_points.SOURCES.index(fastapi_app) < entry_points.SOURCES.index(entry_points.angular)  # after the other frameworks' sources


def test_a_fastapi_route_and_the_noir_row_for_the_same_function_are_one_entry(links):
    found = [(e["reader"], e["symbol"], e["method"], e["path"]) for e in links["entries"] if e["symbol"] == "app/routers/users.py::read_user"]
    assert found == [("fastapi", "app/routers/users.py::read_user", "GET", "/api/users/{user_id}")]  # Noir's row of the same path and function: not a second one
    assert sorted((e["reader"], e["method"]) for e in links["entries"] if e["symbol"] == "app/routers/users.py::delete_user") == [("fastapi", "DELETE")]
    assert [e["reader"] for e in links["entries"] if e["symbol"] == "app/main.py::loose"] == ["fastapi"]  # a parameterless route too


def test_a_call_to_a_url_with_a_value_meets_the_route_of_its_method_and_the_value_is_the_parameter(links):
    found = arcs(links)
    assert ("viewUser", "app/routers/users.py::read_user", ("*", "GET", "/api/users/{}")) in found
    assert ("removeUser", "app/routers/users.py::delete_user", ("*", "DELETE", "/api/users/{}")) in found
    assert ("viewTyped", "app/main.py::read_typed", ("*", "GET", "/typed/{}")) in found
    assert ("viewSub", "app/sub.py::sub_item", ("*", "GET", "/sub/items/{}")) in found  # the mount's prefix is in the route
    assert ("viewTenant", "app/sub.py::tenant_info", ("*", "GET", "/t/{}/info")) in found  # and its parameter is a hole
    arc = next(e for e in links["edges"] if e["from"] == "web/client.ts::viewUser" and e.get("route"))
    assert arc["type"] == "chiama" and arc["offered"].startswith("app/routers/users.py:")  # the service the rule names meets the `*` of a declared route
    assert not [g for g in links["gaps"] if g["symbol"] == "web/client.ts::viewUser"]


def test_a_call_with_one_segment_more_or_a_trailing_slash_difference_is_judged_by_the_schema(links):
    found = {name for name, *_ in arcs(links)}
    assert "viewUserDeep" not in found  # `/api/users/{}` is two segments after `api`, the call is three
    assert {"viewStrict", "viewStrictSlash", "viewLoose"} <= found  # `/strict/` and `/strict` are one schema


@pytest.mark.parametrize("path, function, call", [("/files/{file_path:path}", "read_file", "viewFile"), ("/slug/{s:slug}", "read_slug", "viewSlug")])
def test_a_route_whose_convertor_may_hold_a_slash_or_does_not_say_it_is_a_gap_of_the_declared_routes_and_meets_no_call(links, path, function, call):
    [mine] = [g for g in links["gaps"] if g["reason"].startswith("declared route ") and path in g["reason"]]
    assert mine["reason"].startswith(f"declared route GET {path}: ") and "no single path schema" in mine["reason"]
    assert mine["site"].startswith("app/main.py:") and mine["symbol"] == f"app/main.py::{function}"
    assert call not in {name for name, *_ in arcs(links)}


def test_two_parameters_in_one_segment_make_a_schema_that_no_call_meets(links):
    """`path_schema` writes `/glued/{}-{}`, and `flows._rest_meet` grades a hole glued to a literal only on the asking side: the route is offered, not met."""
    assert "viewGlued" not in {name for name, *_ in arcs(links)}
    assert "route api GET /glued/x-y: no handler" in reasons(links)


def test_a_view_of_the_framework_in_the_environment_is_no_offered_route(links):
    assert "viewDocs" not in {name for name, *_ in arcs(links)}
    assert "route api GET /docs: no handler" in reasons(links)
    assert not [e for e in links["entries"] if e["path"].endswith(("/docs", "/openapi.json", "/redoc"))]


def test_a_websocket_is_an_entry_and_no_offered_route_and_no_gap_of_the_declared_routes(links):
    [socket] = [e for e in links["entries"] if e["path"] == "/ws"]
    assert (socket["reader"], socket["symbol"]) == ("fastapi", "app/main.py::socket") and not socket.get("method")
    assert not [r for r in reasons(links) if "/ws" in r and r.startswith("declared route")]


def test_a_class_based_endpoint_is_a_gap_of_the_links_and_no_entry_and_a_lambda_is_no_entry(links):
    assert not [e for e in links["entries"] if e["path"] in ("/endpoint", "/lambda")]  # rows with a gap of the binder are no entry
    assert [r for r in reasons(links) if r == "Endpoint is a class-based endpoint: which of its methods answers a request is not read"]
