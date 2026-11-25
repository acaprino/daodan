"""The routes of a Flask application are offered routes (`flows.link_facts`), like Noir's and Next.js's: a call of the client meets them.

The Flask rows are the ones `premap/flask_app.py` makes from the answer recorded on Modal (`tests/fixtures/premap/flask/routes.json`) over
the fixture of `benchmarks/flask-routes/`; the Noir rows are built in line (what Noir prints is not run here). Each row carries the
path schema `flask_app` makes from werkzeug's own parse of the rule (`/admin/users/<int:user_id>` is `/admin/users/{}`, as Noir's
`/admin/users/:user_id`), or none where a parameter may hold a `/`: that route is a gap of the declared routes and meets no call.

The source is not wired (`benchmarks/flask-routes/README.md`, «Applicazioni vere»): it is not in `premap.SOURCES` and `FRAMEWORK_SOURCES`, and
`entry-queries.json` has no table for it. The fixture below puts it among the framework sources, with its table, for the time the rows are made and
linked, as the tests of the Django and FastAPI sources do, so what was measured stays tested.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import entries
import flows
import premap
from premap import flask_app, noir
from test_codebase_map_manifest_entries import noir_route
from test_codebase_map_premap_container_runner import manifest_of
from test_codebase_map_premap_flask import QUERY, project, recorded

RULES = [
    {"written": "apiGet", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "GET", "path": "arg0"}},
    {"written": "apiPost", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "POST", "path": "arg0"}},
]
CLIENT = "\n".join([
    "declare function apiGet(url: string): void;",
    "declare function apiPost(url: string): void;",
    "export function viewUser() { apiGet('/admin/users/7'); }",
    "export function saveUser() { apiPost('/admin/users/7'); }",
    "export function deleteUser() { apiPost('/admin/users/7/delete'); }",  # one segment more
    "export function viewInt() { apiGet('/int/7'); }",
    "export function viewFile() { apiGet('/files/a/b'); }",  # `/files/<path:name>`: a name that holds a `/`
    "export function viewGlued() { apiGet('/glued/x-y'); }",  # `/glued/<a>-<b>`
    "export function viewStrict() { apiGet('/strict'); }",  # `/strict/`
    "export function viewStrictSlash() { apiGet('/strict/'); }",
    "export function viewLoose() { apiGet('/loose'); }",
    "export function viewStatic() { apiGet('/static/app.css'); }",  # Flask's own view, in the environment: no route of the project
    ""])
NOIR = {"endpoints": [  # the same function Flask's row is on: Noir's spelling of the rule is the text of the decorator
    noir_route("/admin/users/<int:user_id>", "GET", "admin/blueprint.py", "user", 7),
    noir_route("/admin/users/<int:user_id>", "POST", "admin/blueprint.py", "user", 7),
    noir_route("/loose", "GET", "wsgi.py", "loose_without_slash", 1)]}  # the line is not the one of the def: the function is the key


@pytest.fixture(scope="module")
def links(tmp_path_factory):
    def run(commands):
        if commands[0]["tool"] == "noir":
            return [{"root": "/work", "returncode": 0, "stdout": json.dumps(NOIR), "stderr": ""}]
        return [recorded("routes") for _ in commands]
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(entries.QUERIES, "flask", QUERY)
        patch.setattr(premap, "FRAMEWORK_SOURCES", (*premap.FRAMEWORK_SOURCES, flask_app))
        _, manifest = manifest_of(tmp_path_factory.mktemp("flask-routes"), {**project(), "web/client.ts": CLIENT})
        premap.write(manifest, sources=(premap.requirements, noir, flask_app), runner=run)
        return flows.link_facts(manifest, flows.validate_rules(RULES))


def arcs(links):
    return {(e["from"].split("::")[1], e["to"], tuple(e["route"])) for e in links["edges"] if e.get("route")}


def reasons(links):
    return [g["reason"] for g in links["gaps"]]


def test_the_rows_of_the_source_are_entries_of_the_links_where_it_is_among_the_framework_sources(links):
    assert {e["reader"] for e in links["entries"]} >= {"flask"}


def test_a_flask_route_and_the_noir_row_for_the_same_function_are_one_entry(links):
    found = [(e["reader"], e["symbol"], e["method"], e["path"]) for e in links["entries"]
             if e["symbol"] == "admin/blueprint.py::user"]
    assert sorted(found) == [("flask", "admin/blueprint.py::user", "GET", "/admin/users/<int:user_id>"),
                             ("flask", "admin/blueprint.py::user", "POST", "/admin/users/<int:user_id>")]
    assert [e["reader"] for e in links["entries"] if e["symbol"] == "wsgi.py::loose_without_slash"] == ["flask"]  # a parameterless route too


def test_a_call_to_a_url_with_a_value_meets_the_route_of_its_method_and_the_value_is_the_parameter(links):
    found = arcs(links)
    assert ("viewUser", "admin/blueprint.py::user", ("*", "GET", "/admin/users/{}")) in found
    assert ("saveUser", "admin/blueprint.py::user", ("*", "POST", "/admin/users/{}")) in found
    assert ("viewInt", "wsgi.py::by_int", ("*", "GET", "/int/{}")) in found
    arc = next(e for e in links["edges"] if e["from"] == "web/client.ts::viewUser" and e.get("route"))
    assert arc["type"] == "chiama" and arc["offered"].startswith("admin/blueprint.py:")  # the service the rule names meets the `*` of a declared route
    # Flask's and Noir's rows for the function are one offered route: two would be "several handlers" for the call
    assert not [g for g in links["gaps"] if g["symbol"] == "web/client.ts::viewUser"]


def test_a_call_with_one_segment_more_or_a_trailing_slash_difference_is_judged_by_the_schema(links):
    found = {name for name, *_ in arcs(links)}
    assert "deleteUser" not in found  # `/admin/users/{}` is two segments after `admin`, the call is three
    assert {"viewStrict", "viewStrictSlash", "viewLoose"} <= found  # `/strict/` and `/strict` are one schema


def test_a_route_with_a_path_converter_is_a_gap_of_the_declared_routes_and_meets_no_call(links):
    mine = [g for g in links["gaps"] if g["reason"].startswith("declared route ") and "<path:name>" in g["reason"]]
    assert sorted(g["reason"].split(": ")[0] for g in mine) == ["declared route GET /files/<path:name>", "declared route PUT /files/<path:name>"]
    assert all("no single path schema" in g["reason"] and g["site"].startswith("wsgi.py:") and g["symbol"] == "wsgi.py::by_path" for g in mine)
    assert "viewFile" not in {name for name, *_ in arcs(links)}
    assert "route api GET /files/a/b: no handler" in reasons(links)


def test_two_parameters_in_one_segment_make_a_schema_that_no_call_meets(links):
    """Measured: `path_schema` writes `/glued/{}-{}`, and `flows._rest_meet` grades a hole glued to a literal only on the asking side:
    a call `/glued/x-y` has no handler. The route is offered, and it is not met."""
    assert "viewGlued" not in {name for name, *_ in arcs(links)}
    assert "route api GET /glued/x-y: no handler" in reasons(links)


def test_a_view_of_the_framework_in_the_environment_is_no_offered_route(links):
    assert "viewStatic" not in {name for name, *_ in arcs(links)}
    assert "route api GET /static/app.css: no handler" in reasons(links)
    assert not [e for e in links["entries"] if "static" in e["path"]]
