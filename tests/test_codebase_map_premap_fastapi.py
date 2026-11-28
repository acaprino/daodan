"""The routes of a FastAPI application, `entry_points/fastapi_app.py`: the commands it gives, and the rows and the gaps `read` makes from what
Daodan's script (`entry_points/fastapi_routes.py`, run in the container by the project's own Python) prints.

The answers are real ones: `benchmarks/fastapi-routes/modal_probe.py` runs the script on Modal, in the runner's image with the network
blocked, over the fixture (`benchmarks/fastapi-routes/fixture/`), over copies of it that do not load or that find their application
another way, and in the images of other FastAPI versions, and records what the container runner would return
(`tests/fixtures/premap/fastapi/<variant>.json`, with the print of the two script files and the `VERSION` of the source in
`script.json`). A few tests build an answer in line where the shape under test is Daodan's own check of the layout or a case no
project of the fixture makes; each says so.

Three things of the wiring are in shared files this source does not own (`premap/__init__.py`, `container_runner.TOOLS`,
`entry-queries.json`): `wired` puts them in place for each test, and the tests that check the real files are marked `xfail(strict)`. The wiring is
not done, by decision: on the real applications the pinned Noir gives what this source gives (`benchmarks/fastapi-routes/README.md`, «Applicazioni vere»).
Applying `benchmarks/fastapi-routes/wiring/wiring.diff` turns each of those tests into an XPASS(strict) failure that says to remove its mark.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from test_codebase_map_container_runner import bound, container, container_runner, manifest_of, entry_points, premap, recorder, write_both
from test_codebase_map_premap_sveltekit import nothing_started, spied

import entries
import preparation
from entry_points import fastapi_app

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/fastapi-routes"
FIXTURE = BENCHMARK / "fixture"
RECORDED = Path(__file__).parent / "fixtures/premap/fastapi"
SOURCE = f"fastapi@{fastapi_app.VERSION}"
SOURCES = (premap.module_graph, premap.requirements, fastapi_app)  # the facts `fastapi_app.commands` reads are those two sources'
SCRIPTS = ("fastapi_routes.py", "python_script.py")
QUERIES = {"route": {"kind": "rotta"}, "websocket": {"kind": "rotta"}}  # the table `entry-queries.json` has to hold under `fastapi`
WIRED = {"tool": "fastapi" in container_runner.TOOLS, "queries": "fastapi" in entries.QUERIES,
         "registry": fastapi_app in entry_points.SOURCES and fastapi_app in entry_points.FRAMEWORK_SOURCES}  # the shared files, as they are


def probe_plan():
    """The probe's `plan.py`: the entry of `container_runner.TOOLS` it ran with, in one place."""
    spec = importlib.util.spec_from_file_location("fastapi_probe_plan", BENCHMARK / "plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def wired(monkeypatch):
    """The three entries of shared files, as the report gives them, where the files do not have them yet."""
    if not WIRED["tool"]:
        monkeypatch.setitem(container_runner.TOOLS, "fastapi", probe_plan().TOOL)
    if not WIRED["queries"]:
        monkeypatch.setitem(entries.QUERIES, "fastapi", QUERIES)


def project(folder: Path = FIXTURE, **changes) -> dict[str, str]:
    files = {path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
             for path in folder.rglob("*") if path.is_file() and "__pycache__" not in path.parts}
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def printed(routes, **fields):
    """An answer built in line: what the script prints, and nothing else, on the standard output."""
    document = {"called": True, "application": "app.main:app", "found": "entrypoint-pyproject", "root_path": "",
                "competing": {"others": [], "shadowed": []}, "routes": routes, "unread": []}
    return {"returncode": 0, "stdout": json.dumps({**document, **fields}), "stderr": "", "root": "/work"}


def commands_of(tmp_path, files, sources=SOURCES):
    _, manifest = manifest_of(tmp_path, files)
    asked = []
    write_both(manifest, sources=sources, runner=lambda commands: asked.extend(commands) or [printed([]) for _ in commands])
    return asked


# ----------------------------------------- the Python the command runs, from the folders the restore makes (`preparation`)

def test_the_fixture_declares_fastapi_in_its_pyproject_only_which_the_module_graph_reads_and_requirements_does_not():
    files = project()
    assert "requirements.txt" not in files and "fastapi[standard]" in files["pyproject.toml"]


def test_fastapi_declared_in_a_pyproject_only_runs_there_by_the_python_of_the_root(tmp_path):
    [command] = commands_of(tmp_path, project())
    assert command["cwd"] == "." and command["venv"] == "." and command["tool"] == "fastapi" and command["network"] == "none"
    assert command["argv"][:2] == ["sh", "-c"] and command["argv"][3:] == ["fastapi", "900", f"{preparation.T}/fastapi_routes.py"]
    assert f'exec timeout --kill-after=10 "$1" {preparation.VENVS}/./bin/python -I "$2"' == command["argv"][2]
    assert command["env"] == {}


def test_fastapi_declared_in_a_requirements_file_runs_where_the_file_is(tmp_path):
    files = {"api/requirements.txt": "fastapi==0.165.0\nuvicorn\n", "api/main.py": "x = 1\n", "worker/requirements.txt": "celery==5.4.0\n"}
    assert [(c["cwd"], c["venv"]) for c in commands_of(tmp_path, files)] == [("api", "api")]


def test_a_uv_workspace_member_runs_in_the_environment_of_the_workspace_root_and_keeps_its_own_folder_as_cwd(tmp_path):
    files = {"pyproject.toml": "[project]\nname='r'\nversion='1'\n[tool.uv.workspace]\nmembers=['api']\n", "uv.lock": "",
             "api/pyproject.toml": "[project]\nname='a'\nversion='1'\ndependencies=['fastapi[standard]==0.165.0']\n", "api/main.py": "x = 1\n"}
    [command] = commands_of(tmp_path, files)
    assert command["cwd"] == "api" and command["venv"] == "." and f"{preparation.VENVS}/./bin/python" in command["argv"][2]
    assert "poetry" not in command["argv"][2]


def test_a_poetry_project_asks_poetry_for_its_environment_where_it_lives_in_poetrys_own_cache(tmp_path):
    files = {"pyproject.toml": "[tool.poetry]\nname='p'\nversion='1'\n[tool.poetry.dependencies]\npython='^3.12'\nfastapi='0.165.0'\n",
             "poetry.lock": "", "main.py": "x = 1\n"}
    [command] = commands_of(tmp_path, files)
    assert command["cwd"] == "." and command["venv"] == "." and '"$(cd /work/. && poetry env info -e)"' in command["argv"][2]
    assert "venvs" not in command["argv"][2]


def test_a_folder_with_its_own_lockfile_below_the_root_is_its_own_environment(tmp_path):
    files = {"pyproject.toml": "[project]\nname='r'\nversion='1'\n", "api/pyproject.toml": "[project]\nname='a'\nversion='1'\n"
             "dependencies=['fastapi==0.165.0']\n", "api/uv.lock": "", "api/main.py": "x = 1\n"}
    [command] = commands_of(tmp_path, files)
    assert command["cwd"] == "api" and command["venv"] == "api" and f"{preparation.VENVS}/api/bin/python" in command["argv"][2]


def test_only_a_package_named_fastapi_makes_a_folder_and_a_requirements_file_that_is_not_a_manifest_names_no_folder(tmp_path):
    files = {"a/requirements.txt": "fastapi-utils==0.8.0\nfastapi-cli\n", "b/requirements.txt": "starlette==1.10.0\n",
             "docs/requirements/base.txt": "fastapi\n", "c/pyproject.toml": "[project]\nname='c'\nversion='1'\ndependencies=['fastapi']\n"}
    assert [c["cwd"] for c in commands_of(tmp_path, files)] == ["c"]
    assert commands_of(tmp_path / "no-module-graph", files, sources=(premap.requirements, fastapi_app)) == []  # `requirements` alone does not read it


def test_the_folders_share_the_time_and_none_has_less_than_ten_seconds():
    assert [fastapi_app.run_seconds(n) for n in (1, 3, 90, 200)] == [900, 300, 10, 10]


def test_only_a_folder_whose_manifest_declares_fastapi_runs_the_script(tmp_path):
    _, manifest = manifest_of(tmp_path / "plain", {"requirements.txt": "django==6.1.3\n"})
    record = write_both(manifest, sources=(premap.requirements, fastapi_app), runner=lambda commands: 1 / 0)
    assert [s["state"] for s in record["sources"] if s["source"].startswith("fastapi")] == ["not_needed"]


# ----------------------------------------------------------------------------------------- the answers, and what is built in line

DOCS_OFF = "from fastapi import FastAPI\n\napp = FastAPI(docs_url=None, redoc_url=None)\n\n\n@app.get('/docs')\ndef my_docs():\n    return 'mine'\n"
HOST = "\n\nhost_app = FastAPI()\n\n\n@host_app.get('/hosted')\ndef hosted():\n    return 'hosted'\n\n\napp.router.host('api.example.com', host_app)\n"
# the two edits of the fixture that `modal_probe.py` made for the variants `docs-off` and `host`


def recorded(name: str) -> dict:
    """The answer the probe recorded for a variant, as the container runner returns it."""
    return {**json.loads((RECORDED / f"{name}.json").read_text(encoding="utf-8")), "root": "/work"}


def view(file, qualname, line=None, **more):
    """A handler as the script prints it, for an answer built in line."""
    return {"kind": "function", "type": "builtins.function", "module": file.removesuffix(".py").replace("/", "."), "qualname": qualname,
            "file": file, "line": line, "environment": False, "distribution": None, **more}


def route(path, methods, handler, **more):
    """A route as the script prints it, for an answer built in line."""
    return {"kind": "http", "path": path, "methods": methods, "docs": False, "parts": [[False, path]], "arguments": {}, "handler": handler, **more}


def routes_of(answer) -> dict:
    """The routes of an answer by `(path, methods)`: a path may be there for several methods, and the documentation of two applications may share one."""
    return {(r["path"], tuple(r["methods"])): r for r in fastapi_app._printed(answer)["routes"]}


def read(tmp_path, files, answers, sources=SOURCES):
    _, manifest = manifest_of(tmp_path, files)
    asked = []

    def run(commands):
        asked.extend(commands)
        return answers
    record = write_both(manifest, sources=sources, runner=run)
    # the rows as the links bind them (`binder.bind`): the source gives a name at a position, the binder ties it to the function
    record = {**record, "framework_entries": bound(manifest, record)} if "framework_entries" in record else record
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], asked


def line_of(files, file, needle, nth=1):
    """The line of `file` that holds `needle`, the `nth` time."""
    return [n for n, line in enumerate(files[file].split("\n"), 1) if needle in line][nth - 1]


def rows(record):
    return [r for r in record.get("framework_entries", []) if r["reader"] == "fastapi"]


def fixture_rows(tmp_path):
    files = project()
    record, gaps, asked = read(tmp_path, files, [recorded("routes")])
    return files, record, gaps, asked


def gaps_with(gaps, kind, word):
    return [g for g in gaps if g["kind"] == kind and word in g["detail"]]


# ------------------------------------------------------------------------------------- the recorded answer of the fixture

DOCS = ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc")  # the four routes FastAPI registers for itself
PATHS = {*DOCS, *(f"/sub{path}" for path in DOCS), "/api/users/orders/", "/api/users/orders/{order_id}/ship", "/api/embedded/leaf",
         "/api/users/{user_id}", "/sub/hello", "/sub/items/{item_id}", "/t/{tenant_id}/info", "/items/{item_id}", "/items", "/logged",
         "/unwrapped", "/multi", "/both", "/hidden", "/added", "/lambda", "/page", "/callable", "/partial", "/stdlib", "/third-party",
         "/files/{file_path:path}", "/typed/{n:int}", "/uuid/{u:uuid}", "/slug/{s:slug}", "/pair/{p:pair}", "/two/{a}/{b}",
         "/glued/{a}-{b}", "/strict/", "/loose", "/ws", "/plain", "/endpoint"}


def test_the_script_s_answer_is_one_json_document_on_the_standard_output_and_every_route_of_the_application_is_in_it():
    answer = recorded("routes")
    assert answer["returncode"] == 0 and answer["stderr"] == ""
    document = json.loads(answer["stdout"])  # the whole output, not its last line
    assert document["called"] is True and document["application"] == "app.main:app" and document["found"] == "entrypoint-pyproject"
    assert {path for path, _ in routes_of(answer)} == PATHS
    assert [(u["path"], u["type"]) for u in document["unread"]] == [("/static", "starlette.staticfiles.StaticFiles"), ("/raw", "builtins.function")]


WHERE = {  # (path, method) -> (file, the function as the snapshot names it, a text of its `def`, which one of them)
    ("/api/users/orders/", "GET"): ("app/orders.py", "list_orders", "def list_orders(", 1),
    ("/api/users/orders/{order_id}/ship", "POST"): ("app/orders.py", "ship_order", "def ship_order(", 1),
    ("/api/users/{user_id}", "GET"): ("app/routers/users.py", "read_user", "def read_user(", 1),
    ("/api/users/{user_id}", "DELETE"): ("app/routers/users.py", "delete_user", "def delete_user(", 1),
    ("/api/embedded/leaf", "GET"): ("app/sub.py", "embedded_leaf", "def embedded_leaf(", 1),  # a mount of an included router
    ("/sub/hello", "GET"): ("app/sub.py", "hello", "def hello(", 1),  # a mounted FastAPI application
    ("/sub/items/{item_id}", "GET"): ("app/sub.py", "sub_item", "def sub_item(", 1),
    ("/t/{tenant_id}/info", "GET"): ("app/sub.py", "tenant_info", "def tenant_info(", 1),  # a mount with a parameter of its own
    ("/items/{item_id}", "GET"): ("app/main.py", "read_item", "def read_item(", 1),
    ("/items", "POST"): ("app/main.py", "create_item", "def create_item(", 1),
    ("/logged", "GET"): ("app/main.py", "read_logged", "def read_logged(", 1),  # `functools.wraps` under `@app.get`: the function, not the wrapper
    # a wrapper made without `functools.wraps` is the function FastAPI runs: the row is on the wrapper (`plain`'s, the second of the file)
    ("/unwrapped", "GET"): ("app/main.py", "plain.wrapper", "def wrapper(*args", 2),
    ("/multi", "GET"): ("app/main.py", "multi", "def multi(", 1), ("/multi", "POST"): ("app/main.py", "multi", "def multi(", 1),
    ("/both", "GET"): ("app/main.py", "both", "def both(", 1), ("/both", "HEAD"): ("app/main.py", "both", "def both(", 1),
    ("/hidden", "GET"): ("app/main.py", "hidden", "def hidden(", 1),
    ("/added", "PUT"): ("app/main.py", "added", "def added(", 1), ("/added", "PATCH"): ("app/main.py", "added", "def added(", 1),
    ("/page", "GET"): ("app/main.py", "Pages.show", "def show(", 1),  # a bound method: its function, named `Class.method`
    ("/files/{file_path:path}", "GET"): ("app/main.py", "read_file", "def read_file(", 1),
    ("/typed/{n:int}", "GET"): ("app/main.py", "read_typed", "def read_typed(", 1),
    ("/uuid/{u:uuid}", "GET"): ("app/main.py", "read_uuid", "def read_uuid(", 1),
    ("/slug/{s:slug}", "GET"): ("app/main.py", "read_slug", "def read_slug(", 1),
    ("/pair/{p:pair}", "GET"): ("app/main.py", "read_pair", "def read_pair(", 1),
    ("/two/{a}/{b}", "GET"): ("app/main.py", "read_two", "def read_two(", 1),
    ("/glued/{a}-{b}", "GET"): ("app/main.py", "read_glued", "def read_glued(", 1),
    ("/strict/", "GET"): ("app/main.py", "strict", "def strict(", 1), ("/loose", "GET"): ("app/main.py", "loose", "def loose(", 1),
    ("/plain", "GET"): ("app/main.py", "plain_text", "def plain_text(", 1), ("/plain", "POST"): ("app/main.py", "plain_text", "def plain_text(", 1),
}


def test_each_route_and_method_is_a_row_on_the_function_the_endpoint_is_at_the_line_of_its_def_with_the_path_as_fastapi_writes_it(tmp_path):
    files, record, _, asked = fixture_rows(tmp_path)
    bound_rows = {(r["path"], r.get("method")): r for r in rows(record) if not r.get("gap") and r["shape"] == "route"}
    assert sorted(bound_rows) == sorted(WHERE)
    for key, (file, qualified, needle, nth) in WHERE.items():
        row = bound_rows[key]
        assert row["shape"] == "route" and row["kind"] == "rotta" and row["sources"] == [SOURCE] and row["reader"] == "fastapi"
        assert row["symbol"] == f"{file}::{qualified}" and row["handler"] == qualified.rsplit(".", 1)[-1] and row["handler_source"] == "fastapi", key
        assert row["site"].rpartition(":")[0] == file and "host" not in row, key
        # the record of a decorated function sits on its `def`, not on the decorators above it
        assert int(row["site"].rpartition(":")[2]) == line_of(files, file, needle, nth), key
    assert [(c["cwd"], c["network"], c["env"]) for c in asked] == [(".", "none", {})]


def test_a_method_the_framework_adds_is_not_one_the_route_declares_and_one_it_declares_stays():
    """Starlette's `Route` adds `HEAD` beside `GET` (`/plain`, added with `add_route`); FastAPI's `APIRoute` adds none, so the `HEAD` of
    `/both` was declared and stays: the script drops it for the first kind only."""
    by_route = routes_of(recorded("routes"))
    assert ("/plain", ("GET", "POST")) in by_route and ("/both", ("GET", "HEAD")) in by_route and ("/multi", ("GET", "POST")) in by_route
    assert ("/", ("GET",)) not in by_route and ("/items", ("POST",)) in by_route and ("/added", ("PATCH", "PUT")) in by_route
    assert by_route[("/endpoint", ())]["handler"]["kind"] == "class" and ("/ws", ()) in by_route  # no method: a class-based endpoint, a websocket


def test_the_routers_the_application_includes_are_read_with_the_prefix_of_each_inclusion_and_a_mount_inside_one_is_where_fastapi_serves_it(tmp_path):
    """FastAPI 0.165.0 keeps an included router (`_IncludedRouter`), no longer copies its routes: `iter_route_contexts` gives each route its
    effective path. `/api/users/orders/` is a router in a router in the application; the mount of an included router is served at the
    inclusion's prefix without the router's own `/users` (`matches.json`: `/api/embedded/leaf` is 200, `/api/users/embedded/leaf` 404)."""
    paths = {path for path, _ in routes_of(recorded("routes"))}
    assert {"/api/users/orders/", "/api/users/{user_id}", "/api/embedded/leaf"} <= paths and "/api/users/embedded/leaf" not in paths
    served = dict(line.split(" -> ") for line in recorded("matches")["stdout"].splitlines())
    assert served["/api/embedded/leaf"].startswith("200") and served["/api/users/embedded/leaf"].startswith("404")


def test_the_routes_of_a_mounted_application_have_the_mount_s_prefix_and_its_parameter_and_its_own_documentation_is_told_by_its_own_attributes(tmp_path):
    by_route = routes_of(recorded("routes"))
    assert by_route[("/t/{tenant_id}/info", ("GET",))]["arguments"] == {"tenant_id": True}  # the mount's `{tenant_id}`, not the synthetic `path` of a mount
    assert by_route[("/t/{tenant_id}/info", ("GET",))]["parts"] == [[False, "/t/"], [True, "tenant_id"], [False, "/info"]]
    assert all(by_route[(f"/sub{path}", ("GET",))]["docs"] for path in DOCS) and all(by_route[(path, ("GET",))]["docs"] for path in DOCS)
    assert not any(r["docs"] for r in by_route.values() if r["path"] not in (*DOCS, *(f"/sub{path}" for path in DOCS)))
    assert not [r for path, r in by_route if path.startswith("/t/") and path != "/t/{tenant_id}/info"]  # `tenant` has no documentation routes at all


def test_a_rule_that_is_only_a_documentation_route_of_the_framework_is_neither_a_row_nor_a_gap(tmp_path):
    """FastAPI registers four routes for itself (`FastAPI.setup`): `openapi_url`, `docs_url`, `redoc_url` and `swagger_ui_oauth2_redirect_url`.
    The script says `docs` of a route whose path is one of the owning application's own attributes (the sub-application's, for a mounted one) and
    that is not an `APIRoute`; the source is silent only when its view is in the packages of the restored environment."""
    answer = recorded("routes")
    by_route = routes_of(answer)
    for path in DOCS:
        assert by_route[(path, ("GET",))]["docs"] is True and by_route[(path, ("GET",))]["handler"]["environment"] is True
        assert by_route[(path, ("GET",))]["handler"]["file"].endswith("site-packages/fastapi/applications.py")
    _, record, gaps, _ = fixture_rows(tmp_path)
    assert not [r for r in rows(record) if r["path"] in DOCS or r["path"].startswith("/sub/doc") or r["path"].startswith("/sub/redoc")]
    assert not [g for g in gaps if any(g["detail"].startswith(f"{path}") for path in DOCS)]


def test_a_project_route_at_the_path_of_a_documentation_route_the_application_turned_off_is_a_row_and_the_others_stay_silent(tmp_path):
    """`FastAPI(docs_url=None, redoc_url=None)` and a `@app.get("/docs")` of the project: the path is a documentation route's only by the
    owning application's attributes, and its attribute is None: the route is the project's."""
    answer = recorded("docs-off")
    by_route = routes_of(answer)
    assert by_route[("/docs", ("GET",))]["docs"] is False and by_route[("/openapi.json", ("GET",))]["docs"] is True
    files = project(**{"app/main.py": DOCS_OFF})  # the text of the variant, which `modal_probe.py` wrote in the copy
    record, gaps, _ = read(tmp_path, files, [answer])
    assert [(r["path"], r["method"], r["symbol"]) for r in rows(record)] == [("/docs", "GET", "app/main.py::my_docs")]
    assert not [g for g in gaps if g["kind"] == "model_partial" and "docs" in g["detail"]]


def test_a_documentation_route_whose_view_is_a_function_of_the_project_is_a_row_whatever_the_script_says_of_its_path(tmp_path):
    """The source is silent only for a view in the packages of the restored environment: a function of the project at the path of a documentation
    route (the application kept its `docs_url` and the project registered its own view of it) is the project's."""
    answer = printed([route("/docs", ["GET"], view("app/main.py", "read_item", line=45), docs=True)])  # an inline answer
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert [(r["path"], r["method"], r["symbol"]) for r in rows(record)] == [("/docs", "GET", "app/main.py::read_item")] and not gaps


def test_a_rule_that_is_neither_documentation_nor_a_function_of_the_snapshot_is_a_gap_with_the_cause(tmp_path):
    _, record, gaps, _ = fixture_rows(tmp_path)
    stdlib = routes_of(recorded("routes"))[("/stdlib", ("GET",))]["handler"]
    assert stdlib["environment"] is False and stdlib["file"].endswith("python3.12/json/__init__.py")
    [gap] = [g for g in gaps if g["detail"].startswith("/stdlib: ")]
    assert gap["kind"] == "outside_snapshot" and "dumps has no source file of the project the snapshot holds" in gap["detail"]
    assert gap["detail"].endswith(f"({stdlib['file']})") and gap["path"] == "."
    assert not [r for r in rows(record) if r["path"] == "/stdlib"]


@pytest.mark.parametrize("path, what", [("/partial", "functools.partial"), ("/callable", "app.main.Counter")])
def test_an_endpoint_that_is_not_a_function_has_a_gap_that_names_what_it_is_and_no_row(tmp_path, path, what):
    _, record, gaps, _ = fixture_rows(tmp_path)  # a `functools.partial`, an object with `__call__`: no source file, no `__qualname__`
    [gap] = [g for g in gaps if g["detail"].startswith(f"{path}: ")]
    assert gap["kind"] == "outside_snapshot" and gap["detail"] == f"{path}: {what} has no source file of the project the snapshot holds (none)"
    assert not [r for r in rows(record) if r["path"] == path]


def test_the_other_views_of_the_environment_are_counted_in_one_gap_of_the_folder_with_their_modules(tmp_path):
    """A view of a library (`fastapi.utils.is_body_allowed_for_status_code` here) is not the project's file: one `model_partial` gap per
    folder with the count and the modules, the documentation routes not in it."""
    handler = routes_of(recorded("routes"))[("/third-party", ("GET",))]["handler"]
    assert handler["environment"] is True and handler["module"] == "fastapi.utils"
    _, record, gaps, _ = fixture_rows(tmp_path)
    [partial] = gaps_with(gaps, "model_partial", "packages of the restored environment")
    assert partial["path"] == "." and "1 route" in partial["detail"] and "/third-party (fastapi)" in partial["detail"]
    assert "not of the project" in partial["detail"] and "/docs" not in partial["detail"]
    assert not [r for r in rows(record) if r["path"] == "/third-party"] and not [g for g in gaps if g["detail"].startswith("/third-party")]


def test_a_mount_whose_application_has_no_routes_is_one_gap_of_the_folder_with_its_path_and_type_and_never_silent(tmp_path):
    """`StaticFiles` and an ASGI function mounted on the application have no routes to read: they are named, with their types."""
    _, record, gaps, _ = fixture_rows(tmp_path)
    [unread] = gaps_with(gaps, "model_partial", "does not read")
    assert unread["path"] == "." and "2 routes" in unread["detail"]
    assert "/static (starlette.staticfiles.StaticFiles)" in unread["detail"] and "/raw (builtins.function)" in unread["detail"]


def test_a_folder_whose_routes_are_all_the_frameworks_says_so_and_does_not_yield_nothing(tmp_path):
    only_docs = printed([route(path, ["GET"], view("../venv/fastapi/applications.py", "docs", environment=True), docs=True) for path in DOCS])
    record, gaps, _ = read(tmp_path, project(), [only_docs])  # an inline answer: an application with nothing but its documentation
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_partial"] and "no route of the project" in gaps[0]["detail"]
    record, gaps, _ = read(tmp_path / "empty", project(), [recorded("empty")])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_partial"] and "has no route" in gaps[0]["detail"]
    assert json.loads(recorded("empty")["stdout"])["routes"] == []  # `openapi_url=None`, `docs_url=None`, `redoc_url=None`: nothing registered


def test_a_route_with_no_endpoint_is_a_gap_that_says_so_and_no_row(tmp_path):
    record, gaps, _ = read(tmp_path, project(), [printed([route("/x", ["GET"], None)])])  # an inline answer
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["outside_snapshot"]
    assert gaps[0]["detail"] == "/x: no function: the route has no endpoint" and gaps[0]["path"] == "."


def test_a_view_installed_from_a_local_directory_is_a_gap_that_says_it_is_a_copy_of_the_project_and_where_from(tmp_path):
    """PEP 610: `direct_url.json` of the distribution says it was installed from a directory: the project's own code, copied into
    `site-packages`, which is not the snapshot's file. An inline answer: the case of the Flask probe's `installed-copy` layout."""
    copy = view("../venv/lib/python3.12/site-packages/sharedlib/views.py", "shared", environment=True,
                distribution={"name": "sharedlib", "url": "file:///work/libs/shared"})
    record, gaps, _ = read(tmp_path, project(), [printed([route("/shared", ["GET"], copy), route("/own", ["GET"], view("app/main.py", "read_item", line=45))])])
    [gap] = [g for g in gaps if g["detail"].startswith("/shared: ")]
    assert gap["kind"] == "outside_snapshot" and "installed copy of the project, not the snapshot's file" in gap["detail"]
    assert "sharedlib" in gap["detail"] and "file:///work/libs/shared" in gap["detail"]
    assert [r["path"] for r in rows(record)] == ["/own"] and not [g for g in gaps if g["kind"] == "model_partial"]


def test_a_class_based_endpoint_is_a_row_on_its_file_with_the_gap_for_the_method_it_does_not_read(tmp_path):
    _, record, _, _ = fixture_rows(tmp_path)
    [mine] = [r for r in rows(record) if r["path"] == "/endpoint"]
    assert "method" not in mine and mine["symbol"] == "app/main.py::<module>" and "class-based endpoint" in mine["gap"] and "Endpoint" in mine["gap"]


def test_a_handler_the_snapshot_has_no_record_of_is_a_row_on_its_file_with_the_cause_and_not_a_guess_by_name(tmp_path):
    _, record, _, _ = fixture_rows(tmp_path)
    [lam] = [r for r in rows(record) if r["path"] == "/lambda"]
    assert lam["site"].startswith("app/main.py:") and lam["symbol"] == "app/main.py::<module>" and lam["handler"] == "<lambda>"
    assert "without a unique snapshot handler" in lam["gap"]  # the binder's words: the snapshot names a lambda `(lambda)`


def test_a_handler_the_script_gave_no_line_is_a_row_on_its_file_and_the_binder_says_the_gap(tmp_path):
    answer = printed([route("/x", ["GET"], view("app/main.py", "read_item", line=None))])  # an inline answer: a function whose source the interpreter lacks
    record, _, _ = read(tmp_path, project(), [answer])
    [row] = rows(record)
    assert row["site"] == "app/main.py" and row["symbol"] == "app/main.py::<module>" and "without a unique snapshot handler" in row["gap"]


def test_the_script_prints_the_line_of_the_def_of_a_decorated_function_and_not_of_its_first_decorator():
    """`co_firstlineno` of a decorated function is the line of its first decorator: the script takes the `def`'s from the parse of the whole module."""
    files = project()
    handlers = {path: r["handler"] for (path, _), r in routes_of(recorded("routes")).items()}
    assert handlers["/items/{item_id}"]["line"] == line_of(files, "app/main.py", "def read_item(")  # `@app.get` above it
    assert handlers["/logged"]["line"] == line_of(files, "app/main.py", "def read_logged(")  # `@app.get` and `@logged` above it
    assert handlers["/page"]["line"] == line_of(files, "app/main.py", "def show(")  # a method
    assert handlers["/api/users/{user_id}"]["line"] in (line_of(files, "app/routers/users.py", "def read_user("),
                                                        line_of(files, "app/routers/users.py", "def delete_user("))
    assert handlers["/lambda"]["line"] == line_of(files, "app/main.py", "lambda: {")  # not a `def`: the line its code starts on
    assert handlers["/callable"]["line"] is None and handlers["/partial"]["line"] is None and handlers["/endpoint"]["line"] is None  # no source line


# --------------------------------------------------------------- a websocket is an entry of its own and offers no route to the links

def test_a_websocket_is_a_row_with_a_shape_of_its_own_and_neither_a_method_nor_a_schema(tmp_path):
    _, record, _, _ = fixture_rows(tmp_path)
    [socket] = [r for r in rows(record) if r["path"] == "/ws"]
    assert socket["shape"] == "websocket" and socket["kind"] == "rotta" and socket["symbol"] == "app/main.py::socket" and not socket.get("gap")
    assert "method" not in socket and "schema" not in socket  # a row with a schema and no method is a gap of the links
    assert entries.QUERIES["fastapi"]["websocket"]["kind"] in entries.ENTRY_KINDS


# ------------------------------------------------------------------- the path schema, from Starlette's compiled path and its convertors

SCHEMAS = {  # the path as `flows.path_schema` reads it: what Noir's `/admin/users/:user_id` is, `/admin/users/{}`
    "/api/users/orders/": "/api/users/orders", "/api/users/orders/{order_id}/ship": "/api/users/orders/{}/ship",
    "/api/users/{user_id}": "/api/users/{}", "/api/embedded/leaf": "/api/embedded/leaf", "/sub/hello": "/sub/hello",
    "/sub/items/{item_id}": "/sub/items/{}", "/t/{tenant_id}/info": "/t/{}/info", "/items/{item_id}": "/items/{}", "/items": "/items",
    "/typed/{n:int}": "/typed/{}", "/uuid/{u:uuid}": "/uuid/{}", "/two/{a}/{b}": "/two/{}/{}", "/glued/{a}-{b}": "/glued/{}-{}",
    "/strict/": "/strict", "/loose": "/loose", "/plain": "/plain",  # the trailing slash is not in the schema
    "/files/{file_path:path}": None,  # `path`: a parameter that holds several segments, no single schema
    "/slug/{s:slug}": None, "/pair/{p:pair}": None}  # a convertor of the project's: Starlette does not say whether it holds a `/`


def test_a_route_row_has_the_path_schema_of_its_parameters_and_none_where_a_convertor_does_not_say_it_holds_one_segment(tmp_path):
    import flows
    _, record, _, _ = fixture_rows(tmp_path)
    mine = [r for r in rows(record) if r["path"] in SCHEMAS]
    assert {r["path"] for r in mine} == set(SCHEMAS)
    assert {r["path"]: r["schema"] for r in mine} == SCHEMAS and all("schema" in r for r in mine)
    assert next(r for r in mine if r["path"] == "/api/users/{user_id}")["schema"] == flows.path_schema("/api/users/:user_id")  # Noir's


def test_the_script_prints_each_argument_with_what_the_class_of_its_convertor_says_of_the_segments_it_holds():
    """`str`, `int`, `float` and `uuid` of Starlette (the exact classes) hold one segment; `path` holds several; a convertor of the project's
    says nothing (None), also when it holds one (`SlugConvertor`: Starlette has no `part_isolating`, and `matches.json` shows `/slug/a/b` is 404)."""
    by_path = {path: r["arguments"] for (path, _), r in routes_of(recorded("routes")).items()}
    assert by_path["/typed/{n:int}"] == {"n": True} and by_path["/uuid/{u:uuid}"] == {"u": True} and by_path["/two/{a}/{b}"] == {"a": True, "b": True}
    assert by_path["/files/{file_path:path}"] == {"file_path": False} and by_path["/slug/{s:slug}"] == {"s": None}
    assert by_path["/pair/{p:pair}"] == {"p": None} and by_path["/items/{item_id}"] == {"item_id": True} and by_path["/items"] == {}
    served = dict(line.split(" -> ") for line in recorded("matches")["stdout"].splitlines())
    assert served["/files/a/b"].startswith("200") and served["/typed/a"].startswith("404") and served["/slug/a/b"].startswith("404")
    assert served["/pair/a/b"].startswith("200") and served["/two/1/2"].startswith("200") and served["/t/acme/b/info"].startswith("404")


def test_the_schema_comes_from_the_parts_and_the_convertors_not_from_the_text_of_the_path(tmp_path):
    """A route whose `parts` or `arguments` the script does not give has no schema (None: a gap of the declared routes), never one made
    from `path`; a convertor that does not say is not taken for one that does."""
    answer = recorded("routes")
    document = json.loads(answer["stdout"])
    for found in document["routes"]:
        if found["path"] == "/api/users/{user_id}":
            found["parts"] = None
        if found["path"] == "/typed/{n:int}":
            found["arguments"]["n"] = None
        if found["path"] == "/two/{a}/{b}":
            found["arguments"] = None
    record, _, _ = read(tmp_path, project(), [{**answer, "stdout": json.dumps(document)}])
    wanted = ("/api/users/{user_id}", "/typed/{n:int}", "/two/{a}/{b}", "/uuid/{u:uuid}")
    assert {r["path"]: r["schema"] for r in rows(record) if r["path"] in wanted} == {
        "/api/users/{user_id}": None, "/typed/{n:int}": None, "/two/{a}/{b}": None, "/uuid/{u:uuid}": "/uuid/{}"}


def test_a_route_under_a_host_is_a_row_on_its_path_and_the_host_is_not_in_it(tmp_path):
    """`app.router.host("api.example.com", app)`: Starlette's `Host` holds the routes of an application served only for that host name. The row has
    the path alone, as Flask's has no host: nothing in the links reads one."""
    files = project()
    record, _, _ = read(tmp_path, project(**{"app/main.py": files["app/main.py"] + HOST}), [recorded("host")])
    [hosted] = [r for r in rows(record) if r["path"] == "/hosted"]
    assert hosted["schema"] == "/hosted" and hosted["method"] == "GET" and "host" not in hosted and hosted["symbol"] == "app/main.py::hosted"


# --------------------------------------------------- where the application is found: FastAPI's own loader, as `fastapi-cli` has it

@pytest.mark.parametrize("variant, application, found", [
    ("routes", "app.main:app", "entrypoint-pyproject"),  # `[tool.fastapi] entrypoint = "app.main:app"`
    ("no-entrypoint", "app.main:app", "auto-discovery"),  # no `[tool.fastapi]`: `app/main.py` is the first of its default paths that exists
    ("main-py", "main:app", "auto-discovery"),  # `main.py` is before `app/main.py`
    ("api-name", "main:api", "auto-discovery"),  # the object is called `api`
    ("other-name", "main:server", "auto-discovery"),  # the one FastAPI object of the module, with no preferred name
    ("entrypoint-other", "other:service", "entrypoint-pyproject")])
def test_the_application_is_found_by_the_way_the_cli_finds_it_and_its_routes_are_read(tmp_path, variant, application, found):
    answer = recorded(variant)
    assert answer["returncode"] == 0, answer["stderr"]
    document = json.loads(answer["stdout"])
    assert (document["application"], document["found"]) == (application, found) and document["competing"] == {"others": [], "shadowed": []}
    assert routes_of(answer)


@pytest.mark.parametrize("variant, competing, word", [
    ("two-apps", {"others": ["second"], "shadowed": []}, "second"),  # the loader took the first object `dir()` gives: `first`
    ("wrapped", {"others": [], "shadowed": ["app"]}, "wrapper")])  # `app = CORSMiddleware(inner)`: the loader took `inner`
def test_where_the_loader_took_the_first_fastapi_object_it_found_and_the_module_has_another_candidate_the_folder_is_a_gap_and_no_row(
        tmp_path, variant, competing, word):
    """Measured: the loader answers without an error in both (`results/`), so the script says what else the module holds and the source
    reads no route: rows of an application the project may not serve, or without the prefix a wrapper adds, would be wrong rows."""
    answer = recorded(variant)
    assert json.loads(answer["stdout"])["competing"] == competing and routes_of(answer)
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_partial"] and gaps[0]["path"] == "."
    assert word in gaps[0]["detail"] and json.loads(answer["stdout"])["application"] in gaps[0]["detail"]


@pytest.mark.parametrize("variant, returncode, cause", [
    ("no-app", 3, "Could not find FastAPI app in module"),  # `main.py` with no FastAPI object
    ("no-main", 3, "Could not find a default file"),  # no `[tool.fastapi]` and none of the default paths
    ("entrypoint-missing", 3, 'Could not import module "nothing"'),
    ("entrypoint-not-app", 3, "other:plain is a builtins.str, which has no routes"),  # the entrypoint names something that is no application
    ("module-raises", 3, "boom"),
    ("missing-package", 3, "not_installed"),
    ("plain-routes", 3, "No module named 'fastapi_cli'"),  # `fastapi` without `fastapi[standard]`: the loader is not there
    ("module-hangs", 124, "did not end in 900 seconds")])
def test_an_application_that_does_not_load_or_a_script_that_is_stopped_is_the_folder_s_gap_with_the_cause_and_no_row(tmp_path, variant, returncode, cause):
    answer = recorded(variant)
    assert answer["returncode"] == returncode
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and cause in gaps[0]["detail"] and gaps[0]["path"] == "."
    assert "restored for '.'" in gaps[0]["detail"]  # the environment the script ran in, for the Python is the nearest folder's above


def test_the_application_is_what_the_fixture_loads_in_the_other_versions_of_fastapi_and_what_each_one_keeps_of_included_routers(tmp_path):
    """Measured on FastAPI 0.115.14 (Starlette 0.46.2, `include_router` copies each route, `app.routes` is flat and drops a mount of an
    included router) and 0.137.1 (`include_router` keeps the router, there is no `iter_route_contexts` yet: the router is `unread`, named by
    its type) and 0.165.0 (above)."""
    now, old, mid = (set(routes_of(recorded(name))) for name in ("routes", "old-routes", "mid-routes"))
    assert old == {key for key in now if key[0] != "/api/embedded/leaf"}
    [included] = [u for u in json.loads(recorded("mid-routes")["stdout"])["unread"] if u["path"] is None]
    assert included["type"] == "fastapi.routing._IncludedRouter" and not [path for path, _ in mid if path.startswith("/api/")]
    record, gaps, _ = read(tmp_path, project(), [recorded("mid-routes")])
    [unread] = gaps_with(gaps, "model_partial", "does not read")
    assert "fastapi.routing._IncludedRouter" in unread["detail"] and "/static" in unread["detail"]
    assert rows(record)


def test_the_routes_app_frontend_registers_are_in_a_private_list_that_neither_app_routes_nor_iter_route_contexts_gives_and_are_not_read(tmp_path):
    """`app.frontend("/ui", directory="static")` (FastAPI 0.165.0's own static front end) adds a `_FrontendRoute`, which the application keeps
    in `_low_priority_routes` (inferred: the source of `APIRouter.include_router` reads that list, the one of `APIRouter.frontend` was not read): the answer is the
    same as without it. A route with no
    function of the project, and not named: the source has no public way to know it is there (the same for `not_found`, whose handler is one)."""
    answer = recorded("frontend")
    assert answer["returncode"] == 0, answer["stderr"]
    assert set(routes_of(answer)) == set(routes_of(recorded("routes"))) and json.loads(answer["stdout"])["unread"] == json.loads(recorded("routes")["stdout"])["unread"]


def test_an_application_with_a_root_path_keeps_its_rows_and_has_a_gap_that_says_a_proxy_adds_a_prefix(tmp_path):
    answer = recorded("root-path")
    assert json.loads(answer["stdout"])["root_path"] == "/proxy"  # `FastAPI(root_path="/proxy")`: FastAPI deprecates it, `--root-path` of the CLI is its way
    record, gaps, _ = read(tmp_path, project(**{"app/main.py": "def x():\n    return 'x'\n"}), [answer])
    assert [r["path"] for r in rows(record)] == ["/x"]
    [gap] = gaps_with(gaps, "model_partial", "root_path")
    assert "/proxy" in gap["detail"] and "prefix" in gap["detail"]
    assert json.loads(recorded("routes")["stdout"])["root_path"] == ""


def test_the_lifespan_of_an_application_does_not_run_while_the_script_loads_it_and_its_routes_are_read(tmp_path):
    """The lifespan of the variant writes a file when it starts (`benchmarks/fastapi-routes/results/lifespan.json`: `left_in_the_project` has no
    `lifespan-ran`): loading the application is not starting it; a route a lifespan or a startup handler adds is not read."""
    answer = recorded("lifespan")
    assert answer["returncode"] == 0 and "/x" in {path for path, _ in routes_of(answer)}


def test_the_rows_and_the_gaps_a_source_persisted_are_the_ones_from_record_gives_back(tmp_path):
    _, record, gaps, _ = fixture_rows(tmp_path)
    back_rows, back_gaps = fastapi_app.from_record(record)
    assert back_rows == rows(record) and back_gaps == gaps and back_rows


# ---------------------------------------------- what follows the JSON, and what the script does not take for the application

def test_what_the_project_prints_while_it_loads_never_reaches_the_standard_output_which_is_the_json_alone():
    """Descriptor 1 is the standard error while the project's code runs: a `print` that is not flushed dies with its buffer when the
    script leaves (`os._exit`), one that is flushed is on the standard error. Either way the standard output is the answer alone."""
    answer = recorded("module-prints")
    assert answer["returncode"] == 0 and "main loaded" not in answer["stdout"]
    assert json.loads(answer["stdout"])["called"] is True and routes_of(answer)


@pytest.mark.parametrize("variant, said", [("thread", "a thread that never ends"), ("atexit-print", "a print at exit"),
                                           ("replaced-stdout", "a project that replaces sys.stdout")])
def test_nothing_the_project_does_after_the_json_changes_the_answer(tmp_path, variant, said):
    """The script writes the JSON to the descriptor it saved before the project's code ran, and leaves with `os._exit`: a non-daemon
    thread does not keep it alive, an `atexit` print is not the last line, a replaced `sys.stdout` hides nothing."""
    answer = recorded(variant)
    assert answer["returncode"] == 0, (said, answer["stderr"])
    assert json.loads(answer["stdout"])["called"] is True and {path for path, _ in routes_of(answer)} == {*DOCS, "/x"}
    record, gaps, _ = read(tmp_path, project(**{"app/main.py": "def x():\n    return 'x'\n"}), [answer])
    assert [r["path"] for r in rows(record)] == ["/x"] and not [g for g in gaps if g["kind"] == "model_failed"]


# ------------------------------------------------------- what the script prints is checked as `read` uses it

MALFORMED = [
    ("a method that is not text", lambda r: r.update(methods=[1])),
    ("methods that are not a list", lambda r: r.update(methods="GET")),
    ("a part that is not a pair", lambda r: r.update(parts=[[False]])),
    ("a part whose flag is not a boolean", lambda r: r.update(parts=[["x", "/"]])),
    ("arguments that are not a mapping", lambda r: r.update(arguments=["a"])),
    ("an argument whose isolation is not a boolean", lambda r: r.update(arguments={"a": "yes"})),
    ("a documentation flag that is not a boolean", lambda r: r.update(docs="no")),
    ("a kind that is neither http nor websocket", lambda r: r.update(kind="grpc")),
    ("a path that is not text", lambda r: r.update(path=3)),
    ("a file that is not text", lambda r: r["handler"].update(file=5)),
    ("a qualified name that is not text", lambda r: r["handler"].update(qualname=5)),
    ("a line that is not a number", lambda r: r["handler"].update(line="7")),
    ("an environment flag that is not a boolean", lambda r: r["handler"].update(environment="yes")),
    ("a distribution that is not a mapping", lambda r: r["handler"].update(distribution="x")),
    ("a kind of handler that is neither a function nor a class", lambda r: r["handler"].update(kind="method"))]


@pytest.mark.parametrize("what, spoil", MALFORMED, ids=[what for what, _ in MALFORMED])
def test_a_value_of_the_answer_that_read_would_use_and_is_malformed_is_that_folder_s_gap_and_the_other_folders_keep_their_rows(tmp_path, what, spoil):
    """Inline answers: two folders, the first spoiled in one value. The check of the layout is whole, so `read` never raises in the
    middle of a folder and loses the rows of the ones before and after it."""
    files = {"api/requirements.txt": "fastapi==0.165.0\n", "api/main.py": "def x():\n    return 'x'\n",
             "worker/requirements.txt": "fastapi==0.165.0\n", "worker/main.py": "def y():\n    return 'y'\n"}
    api = route("/x", ["GET"], view("main.py", "x", line=1))
    spoil(api)
    answers = [printed([api]), printed([route("/y", ["GET"], view("main.py", "y", line=1))])]
    record, gaps, _ = read(tmp_path, files, answers)
    assert [g["kind"] for g in gaps] == ["model_failed"] and gaps[0]["path"] == "api" and "known layout" in gaps[0]["detail"], what
    assert [(r["path"], r["site"]) for r in rows(record)] == [("/y", "worker/main.py:1")]


@pytest.mark.parametrize("spoil", [lambda d: d.update(application=1), lambda d: d.update(found=None), lambda d: d.update(root_path=None),
                                   lambda d: d.update(competing=[]), lambda d: d["competing"].update(others="second"),
                                   lambda d: d["competing"].update(shadowed=[1]), lambda d: d.update(unread=[{"path": "/x"}]),
                                   lambda d: d.update(unread=[{"path": 1, "type": "x"}]), lambda d: d.pop("called"), lambda d: d.pop("routes")])
def test_a_document_of_an_unknown_layout_is_the_folder_s_gap(tmp_path, spoil):
    document = json.loads(printed([route("/x", ["GET"], view("main.py", "x", line=1))])["stdout"])
    spoil(document)
    record, gaps, _ = read(tmp_path, project(), [{"returncode": 0, "stdout": json.dumps(document), "stderr": "", "root": "/work"}])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and "known layout" in gaps[0]["detail"]


@pytest.mark.parametrize("answer, cause", [  # Daodan's own check of what the script printed: the layout, not FastAPI's output
    ({"returncode": 0, "stdout": "not json\n", "stderr": ""}, "printed no JSON"),
    ({"returncode": 0, "stdout": "log of the project\n" + printed([])["stdout"], "stderr": ""}, "printed no JSON"),
    ({"returncode": 0, "stdout": json.dumps([]), "stderr": ""}, "no `called`"),
    ({"returncode": 137, "stdout": "", "stderr": ""}, "exit 137"),
])
def test_a_line_that_is_not_the_known_layout_or_a_killed_script_is_the_folder_s_gap_with_the_cause(tmp_path, answer, cause):
    record, gaps, _ = read(tmp_path, project(), [{**answer, "root": "/work"}])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and cause in gaps[0]["detail"] and gaps[0]["path"] == "."


def test_several_folders_each_with_rows_are_read_one_by_one_and_a_folder_that_fails_does_not_take_the_others(tmp_path):
    files = {"api/requirements.txt": "fastapi==0.165.0\n", "api/main.py": "def x():\n    return 'x'\n",
             "tools/requirements.txt": "fastapi==0.165.0\n", "tools/main.py": "def t():\n    return 't'\n",
             "worker/requirements.txt": "fastapi==0.165.0\n", "worker/main.py": "def z():\n    return 'z'\n"}
    answers = [printed([route("/x", ["GET"], view("main.py", "x", line=1))]),  # api
               {"returncode": 3, "stdout": "", "stderr": "FastAPICLIException: Could not find FastAPI app in module\n", "root": "/work"},  # tools
               printed([route("/z", ["GET", "POST"], view("main.py", "z", line=1))])]  # worker
    record, gaps, asked = read(tmp_path, files, answers)
    assert [c["cwd"] for c in asked] == ["api", "tools", "worker"]
    assert sorted((r["path"], r["method"], r["site"], r["symbol"]) for r in rows(record)) == [
        ("/x", "GET", "api/main.py:1", "api/main.py::x"), ("/z", "GET", "worker/main.py:1", "worker/main.py::z"),
        ("/z", "POST", "worker/main.py:1", "worker/main.py::z")]
    assert [(g["kind"], g["path"]) for g in gaps] == [("model_failed", "tools")]


# -------------------------------------------------------------------- the helpers of the script, which are plain Python and run here

def script_module(name):
    """A script of `entry_points/` loaded by its path, as the container loads `python_script.py`: importing runs no project code."""
    path = Path(fastapi_app.__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_parts_of_a_path_are_the_names_the_framework_gave_and_the_text_between_them():
    routes = script_module("fastapi_routes.py")
    assert routes.tokens("/t/{tenant_id}/info", ["tenant_id"]) == [[False, "/t/"], [True, "tenant_id"], [False, "/info"]]
    assert routes.tokens("/glued/{a}-{b}", ["a", "b"]) == [[False, "/glued/"], [True, "a"], [False, "-"], [True, "b"]]
    assert routes.tokens("/{id}/{1}", ["id"]) == [[False, "/"], [True, "id"], [False, "/{1}"]]  # a brace that is no parameter of the framework's is text
    assert routes.tokens("", []) == [] and routes.tokens("/a/{ab}", ["a"]) == [[False, "/a/{ab}"]]


def test_the_arguments_of_a_prefix_and_of_the_path_under_it_count_as_one_segment_only_where_both_say_so():
    routes = script_module("fastapi_routes.py")
    assert routes.merged({"a": True}, {"b": False}) == {"a": True, "b": False}
    assert routes.merged({"a": True}, {"a": True}) == {"a": True} and routes.merged({"a": True}, {"a": None}) == {"a": None}
    assert routes.merged({"a": True}, {"a": False}) == {"a": None} and routes.merged({}, {}) == {}


def test_the_line_of_a_def_is_the_interpreters_own_parse_of_the_module_for_a_decorated_function_a_method_and_a_line_at_column_0(tmp_path):
    shared = script_module("python_script.py")
    file = tmp_path / "views.py"
    file.write_text('import functools\n\n\n@functools.cache\n@functools.cache\ndef decorated():\n    return 1\n\n\nclass C:\n'
                    '    def text(self):\n        return """\nat column 0\n"""\n\n    def method(self):\n        return 2\n', encoding="utf-8")
    assert shared.definitions(str(file)) == {4: 6, 11: 11, 16: 16}  # first decorator line -> line of the def
    assert shared.definition_line(shared.definition_line, str(file)) == shared.definition_line.__code__.co_firstlineno  # no entry: the object's own first line
    assert shared.definitions(str(tmp_path / "missing.py")) == {} and shared.definition_line(None, str(file)) is None


def test_a_view_is_described_by_its_function_after_functools_wraps_a_bound_method_by_its_function_and_a_partial_by_its_type(tmp_path):
    import functools
    shared = script_module("python_script.py")

    def plain():
        return 1

    @functools.wraps(plain)
    def wrapper():
        return plain()

    class Pages:
        def show(self):
            return 1
    assert shared.function_of(wrapper) is plain and shared.function_of(Pages().show) is Pages.show
    described = shared.describe(shared.function_of(wrapper), "function", str(Path(__file__).parent))
    assert described["qualname"].endswith("plain") and described["file"].endswith(Path(__file__).name) and described["environment"] is False
    assert described["line"] == plain.__code__.co_firstlineno
    kind = shared.describe(functools.partial(plain), "function", str(tmp_path))
    assert kind["file"] is None and kind["qualname"] is None and kind["type"] == "functools.partial" and kind["line"] is None


# ----------------------------------------------------------------- what is persisted, and where the script runs

def test_the_recorded_answers_carry_the_print_of_the_two_scripts_that_made_them_and_the_version_of_the_source_they_were_made_for():
    """A pre-map is fresh while its source's `NAME@VERSION` is the one it was made by (`premap.state`): a script that changes with no
    new `VERSION` leaves stale rows in a project's pre-map. The recording holds the print of both files and the version: changing a script
    fails here until it is recorded again, and the record is made with the `VERSION` the source has then: raise it with the script."""
    folder = container_runner.SCRIPTS
    prints = {name: hashlib.sha256((folder / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in SCRIPTS}
    assert json.loads((RECORDED / "script.json").read_text(encoding="utf-8")) == {**prints, "version": fastapi_app.VERSION}, (
        "a script or the version changed: record the answers again (`benchmarks/fastapi-routes/modal_probe.py`)")


def test_the_runner_restores_the_python_environment_of_each_folder_and_both_scripts_are_unpacked_beside_the_tools(tmp_path):
    spec = container_runner.TOOLS["fastapi"]  # the entry the report gives (`wired`), or the runner's own
    assert spec["restores"] == "python" and spec["registries"] and spec["memory"] == container_runner.TOOLS["next"]["memory"]
    assert {name for _, _, name in spec["files"]} == set(SCRIPTS)
    assert all(f"{preparation.T}/{name}" in spec["setup"][0] for name in SCRIPTS)
    project_dir = tmp_path / "p"
    (project_dir / "api").mkdir(parents=True)
    (project_dir / "api/requirements.txt").write_text("fastapi==0.165.0\n", encoding="utf-8")
    assert any("'api'" in line and "uv venv" in line for line in container_runner._python(project_dir)["lines"])
    first, files, *_ = container_runner.plan("fastapi", [], [], container_runner._python(project_dir)["lines"], ["uv"])
    assert [name for _, _, name in files if name.endswith(".py")] == list(SCRIPTS) and first["network"] == "registries"


def test_no_engine_carries_the_reason_as_the_source_s_gap_and_nothing_of_the_project_runs_here(tmp_path):
    _, manifest = manifest_of(tmp_path, project())
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        record = write_both(manifest, sources=SOURCES, runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record


# ------------------------------------------- the project's code never runs on the host (AGENTS.md, «Regola invalicabile»)

def marked_project(tmp_path, monkeypatch):
    """A project that declares FastAPI and holds all a load of its application would start, each file leaving its own mark in `marks/`
    if it runs on this machine: the module `app/main.py`, the package `app/`, `sitecustomize.py` and a `conftest.py`; and, first on the
    PATH, a stand-in for each program that would start it (python, python3, uv, poetry, timeout, fastapi, uvicorn) that writes a mark too."""
    marks, tools = tmp_path / "marks", tmp_path / "bin"
    marks.mkdir()
    tools.mkdir()

    def mark(name):
        return f"import pathlib\npathlib.Path({json.dumps((marks / name).as_posix())}).write_text('ran')\n"
    for name in ("python", "python3", "uv", "poetry", "timeout", "fastapi", "uvicorn"):
        (tools / name).write_text(f'#!/bin/sh\necho "$0 $*" >> "{marks}/tool-{name}"\n', encoding="utf-8", newline="\n")
        (tools / name).chmod(0o755)
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    files = project(**{"app/main.py": mark("main.py") + "from fastapi import FastAPI\napp = FastAPI()\n", "app/__init__.py": mark("package"),
                       "sitecustomize.py": mark("sitecustomize.py"), "conftest.py": mark("conftest.py")})
    return marks, manifest_of(tmp_path, files)[1]


def test_nothing_of_the_project_starts_on_the_host_without_an_engine_nor_when_the_answer_is_read(tmp_path, monkeypatch):
    marks, manifest = marked_project(tmp_path, monkeypatch)
    started = spied(monkeypatch)
    monkeypatch.setattr(container, "run_in_container", lambda *args, **kwargs: {"state": "gap", "cause": "no engine", "remedy": "start one"})
    record = write_both(manifest, sources=SOURCES, runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record
    nothing_started(started, marks)  # Daodan's own git only, with the hooks and the monitor off; no tool, no file of the project
    started.clear()
    record = write_both(manifest, sources=SOURCES, runner=lambda commands: [recorded("routes") for _ in commands])  # an answer in hand: reading it starts nothing
    assert record["framework_entries"]
    nothing_started(started, marks)


@pytest.mark.parametrize("how", ["os.system", "subprocess.run", "subprocess.Popen"])
def test_the_check_catches_a_source_that_starts_the_command_on_the_host(tmp_path, monkeypatch, how):
    """The mutation, in memory, three ways: a source that runs the script here. The check above must fail for each."""
    import subprocess
    marks, manifest = marked_project(tmp_path, monkeypatch)
    started = spied(monkeypatch)
    real = fastapi_app.commands
    command = ["python", "-I", "fastapi_routes.py"]

    def mutated(context):
        try:
            {"os.system": lambda: os.system(" ".join(command)), "subprocess.run": lambda: subprocess.run(command),
             "subprocess.Popen": lambda: subprocess.Popen(command)}[how]()
        except OSError:  # the spy refuses to start it, after recording it
            pass
        return real(context)
    monkeypatch.setattr(fastapi_app, "commands", mutated)
    monkeypatch.setattr(container, "run_in_container", lambda *args, **kwargs: {"state": "gap", "cause": "no engine", "remedy": "start one"})
    write_both(manifest, sources=SOURCES, runner=container_runner.runner(manifest))
    with pytest.raises(AssertionError):
        nothing_started(started, marks)


# ----------------------------------------------- the rules of the entries' sources, checked on this one (they list only what is registered)

def test_the_source_keeps_no_copy_of_a_shared_helper_and_borrows_no_other_sources():
    tree = ast.parse(Path(fastapi_app.__file__).read_text(encoding="utf-8"))
    assert not {node.name for node in tree.body if isinstance(node, ast.FunctionDef)} & {"_folders", "_folder", "_excerpt"}
    others = {source.__name__.rsplit(".", 1)[-1] for source in (*entry_points.FRAMEWORK_SOURCES, *entry_points.TEMPLATE_SOURCES)} - {"fastapi_app"}
    borrowed = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in others]
    borrowed += [alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                 and ((node.module or "").rsplit(".", 1)[-1] in others or node.module in ("premap", "entry_points") and any(alias.name in others for alias in node.names))
                 for alias in node.names]
    assert not borrowed  # what two sources share is in `frameworks`, whatever its name


def test_the_source_binds_no_row_itself_and_opens_no_store_of_the_snapshot():
    tree = ast.parse(Path(fastapi_app.__file__).read_text(encoding="utf-8"))
    named = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert "semantic_store" not in named and not {"starts", "exported_target"} & {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}


# ------------------------------------------------------ the wiring in files this source does not own: each waits for it

WAITS = pytest.mark.xfail(strict=True, reason="not wired, by decision (benchmarks/fastapi-routes/README.md): remove this mark when `wiring/wiring.diff` is applied")


@WAITS
def test_the_source_is_registered_with_the_pre_map_and_is_a_framework_source_after_the_other_frameworks_and_before_angular():
    assert fastapi_app in entry_points.SOURCES and fastapi_app in entry_points.FRAMEWORK_SOURCES
    assert entry_points.SOURCES.index(fastapi_app) < entry_points.SOURCES.index(entry_points.angular)


@WAITS
def test_the_runner_has_the_setup_the_probe_ran_with():
    assert WIRED["tool"] and container_runner.TOOLS["fastapi"] == probe_plan().TOOL


@WAITS
def test_entry_queries_has_the_table_of_the_source():
    assert WIRED["queries"] and entries.QUERIES["fastapi"] == QUERIES
