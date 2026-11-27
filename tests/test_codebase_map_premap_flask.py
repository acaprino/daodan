"""The routes of a Flask application, `premap/flask_app.py`: the commands it gives, and the rows and the gaps `read` makes from what
Daodan's script (`premap/flask_routes.py`, run in the container by the project's own Python) prints.

The answers are real ones: `benchmarks/flask-routes/modal_probe.py` runs the script on Modal, in the runner's image with the network
blocked, over the fixture (`benchmarks/flask-routes/fixture/`), over copies of it that do not load and over folders of other layouts
(`benchmarks/flask-routes/layouts/`: a uv workspace, a Poetry project, a root `pyproject.toml` with an `api/requirements.txt`, a project
that installs a local package), and records what the container runner would return (`tests/fixtures/premap/flask/<variant>.json`, with
the print of the script and the `VERSION` of the source in `script.json`). A few tests build an answer in line where the shape under
test is Daodan's own check of the layout or a case no project of the fixture makes; each says so.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from test_codebase_map_container_runner import bound, container, container_runner, manifest_of, premap, recorder, snapshot
from test_codebase_map_premap_sveltekit import nothing_started, spied
from unittest.mock import patch

from premap import flask_app

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/flask-routes"
FIXTURE = BENCHMARK / "fixture"
LAYOUTS = BENCHMARK / "layouts"
RECORDED = Path(__file__).parent / "fixtures/premap/flask"
SOURCE = f"flask@{flask_app.VERSION}"
SOURCES = (premap.module_graph, premap.requirements, flask_app)  # the facts `flask_app.commands` reads are those two sources'
QUERY = {"route": {"kind": "rotta"}}  # the table of the entry queries the source reads (`read`); it is not in `entry-queries.json`: the source is not wired


@pytest.fixture(autouse=True)
def wired(monkeypatch):
    """What the source needs of the files of the pre-map that do not name it: it is not in `premap.SOURCES` and `FRAMEWORK_SOURCES`, nor has
    `entry-queries.json` a table for it (measured on Modal, and left unwired by decision: `benchmarks/flask-routes/README.md`, «Applicazioni
    vere»). Each test runs with the table and the source among the framework sources, as the Django and FastAPI sources' tests do."""
    import entries
    monkeypatch.setitem(entries.QUERIES, "flask", QUERY)
    monkeypatch.setattr(premap, "FRAMEWORK_SOURCES", (*premap.FRAMEWORK_SOURCES, flask_app))


def project(folder: Path = FIXTURE, **changes) -> dict[str, str]:
    files = {path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
             for path in folder.rglob("*") if path.is_file() and "__pycache__" not in path.parts}
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def recorded(name: str) -> dict:
    """The answer the probe recorded for a variant, as the container runner returns it."""
    return {**json.loads((RECORDED / f"{name}.json").read_text(encoding="utf-8")), "root": "/work"}


def view(file, qualname, line=None, **more):
    """A handler as the script prints it, for an answer built in line."""
    return {"kind": "function", "type": "builtins.function", "module": file.removesuffix(".py").replace("/", "."), "qualname": qualname,
            "file": file, "line": line, "environment": False, "distribution": None, **more}


def rule(path, methods, handler, **more):
    """A rule as the script prints it, for an answer built in line."""
    return {"rule": path, "methods": methods, "build_only": False, "redirect_to": False, "static": False,
            "parts": [[False, "/"], *([[False, path.strip("/")]] if path != "/" else [])], "arguments": {}, "handler": handler, **more}


def printed(routes, dispatch=None, **fields):
    """An answer built in line: what the script prints, and nothing else, on the standard output."""
    return {"returncode": 0, "stdout": json.dumps({"called": True, "dispatch": dispatch, "routes": routes}), "stderr": "", "root": "/work", **fields}


def routes_of(answer) -> dict:
    return {r["rule"]: r for r in flask_app._printed(answer)["routes"]}


def read(tmp_path, files, answers, sources=(premap.requirements, flask_app)):
    _, manifest = manifest_of(tmp_path, files)
    asked = []

    def run(commands):
        asked.extend(commands)
        return answers
    record = premap.write(manifest, sources=sources, runner=run)
    # the rows as the links bind them (`binder.bind`): the source gives a name at a position, the binder ties it to the function
    record = {**record, "framework_entries": bound(manifest, record)} if "framework_entries" in record else record
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], asked


def line_of(files, file, needle):
    """The line of `file` that holds `needle`."""
    return next(n for n, line in enumerate(files[file].split("\n"), 1) if needle in line)


def rows(record):
    return [r for r in record.get("framework_entries", []) if r["reader"] == "flask"]


def fixture_rows(tmp_path):
    files = project()
    record, gaps, asked = read(tmp_path, files, [recorded("routes")])
    return files, record, gaps, asked


# ----------------------------------------------------------------------- the recorded answer of the fixture

def test_the_script_s_answer_is_one_json_document_on_the_standard_output_and_every_rule_of_the_url_map_is_in_it():
    answer = recorded("routes")
    assert answer["returncode"] == 0 and answer["stderr"] == ""
    assert json.loads(answer["stdout"])["called"] is True  # the whole output, not its last line
    assert set(routes_of(answer)) == {
        "/", "/items", "/wrapped", "/unwrapped", "/page", "/lambda", "/partial", "/callable", "/orders", "/hello", "/options",
        "/admin/users/<int:user_id>", "/admin/stats", "/nested/inner", "/static/<path:filename>",
        "/int/<int:id>", "/string/<string:name>", "/uuid/<uuid:u>", "/files/<path:name>", "/slug/<slug:s>", "/tail/<tail:rest>",
        "/tailre/<tailre:rest>", "/pair/<pair:p>", "/glued/<a>-<b>", "/two/<int:x>/<int:y>", "/strict/", "/loose", "/relaxed/",
        "/sub", "/stdlib", "/head-only", "/get-options", "/built", "/old", "/third-party", "/docs", "/nested-doc",
        "/assets/files/<path:filename>"}


def test_each_rule_and_method_is_a_row_on_the_function_the_view_is_at_the_line_of_its_def_with_the_rule_as_flask_writes_it(tmp_path):
    files, record, gaps, asked = fixture_rows(tmp_path)
    bound_rows = {(r["path"], r.get("method")): r for r in rows(record) if not r.get("gap")}
    assert sorted(bound_rows) == sorted([
        ("/", "GET"), ("/admin/stats", "GET"), ("/admin/users/<int:user_id>", "GET"), ("/admin/users/<int:user_id>", "POST"),
        ("/items", "POST"), ("/nested/inner", "GET"), ("/options", "OPTIONS"), ("/page", "GET"), ("/unwrapped", "GET"), ("/wrapped", "GET"),
        ("/int/<int:id>", "GET"), ("/string/<string:name>", "GET"), ("/uuid/<uuid:u>", "GET"), ("/files/<path:name>", "GET"),
        ("/files/<path:name>", "PUT"), ("/slug/<slug:s>", "GET"), ("/tail/<tail:rest>", "GET"), ("/tailre/<tailre:rest>", "GET"),
        ("/pair/<pair:p>", "GET"), ("/glued/<a>-<b>", "GET"), ("/two/<int:x>/<int:y>", "GET"), ("/strict/", "GET"), ("/loose", "GET"),
        ("/relaxed/", "GET"), ("/sub", "GET"), ("/head-only", "HEAD"), ("/get-options", "GET"), ("/get-options", "OPTIONS"),
        ("/docs", "GET"), ("/nested-doc", "GET")])
    where = {("/", "GET"): ("wsgi.py", "index", "def index("), ("/items", "POST"): ("wsgi.py", "create_item", "def create_item("),
             ("/wrapped", "GET"): ("wsgi.py", "wrapped", "def wrapped("),  # `functools.wraps` under `app.get`: the function, not the wrapper
             ("/page", "GET"): ("wsgi.py", "Pages.show", "def show("),  # a bound method: its function, named `Class.method`
             ("/admin/users/<int:user_id>", "GET"): ("admin/blueprint.py", "user", "def user("),
             ("/admin/users/<int:user_id>", "POST"): ("admin/blueprint.py", "user", "def user("),
             ("/admin/stats", "GET"): ("admin/blueprint.py", "stats", "def stats("),
             # a function nested in a factory: Python writes `make_blueprint.<locals>.inner`, the snapshot `make_blueprint.inner`
             ("/nested/inner", "GET"): ("admin/blueprint.py", "make_blueprint.inner", "def inner("),
             # a wrapper made without `functools.wraps` is the function Flask runs: the row is on the wrapper
             ("/unwrapped", "GET"): ("wsgi.py", "plain.wrapper", "def wrapper(*args"),
             ("/docs", "GET"): ("wsgi.py", "Docs.page", "def page("), ("/nested-doc", "GET"): ("wsgi.py", "make_view.nested_doc", "def nested_doc(")}
    for key, (file, qualified, needle) in where.items():
        row = bound_rows[key]
        assert row["shape"] == "route" and row["kind"] == "rotta" and row["sources"] == [SOURCE] and row["reader"] == "flask"
        assert row["symbol"] == f"{file}::{qualified}" and row["handler"] == qualified.rsplit(".", 1)[-1] and row["handler_source"] == "flask", key
        assert row["site"].rpartition(":")[0] == file and "host" not in row, key
        if key != ("/unwrapped", "GET"):  # the one `def wrapper(*args` of the fixture that is `plain`'s comes second
            # the record of a decorated function sits on its `def`, not on the decorators above it
            assert int(row["site"].rpartition(":")[2]) == line_of(files, file, needle), key
    assert [(c["cwd"], c["network"], c["env"]) for c in asked] == [(".", "none", {})]


def test_a_method_the_framework_adds_is_not_one_the_rule_declares_and_one_it_declares_stays(tmp_path):
    """Werkzeug adds `HEAD` beside `GET` (`routing/rules.py`), Flask adds `OPTIONS` and says so on the rule
    (`provide_automatic_options`, `sansio/app.py`): the script drops those, and a declared `OPTIONS` or `HEAD` is a method."""
    by_rule = routes_of(recorded("routes"))
    assert by_rule["/"]["methods"] == ["GET"] and by_rule["/orders"]["methods"] == ["GET", "POST"]
    assert by_rule["/options"]["methods"] == ["OPTIONS"] and by_rule["/head-only"]["methods"] == ["HEAD"]
    assert by_rule["/get-options"]["methods"] == ["GET", "OPTIONS"]


def test_a_rule_that_is_only_for_building_urls_or_only_redirects_is_no_row_and_no_gap(tmp_path):
    by_rule = routes_of(recorded("routes"))
    assert by_rule["/built"]["build_only"] is True and by_rule["/old"]["redirect_to"] is True
    assert by_rule["/built"]["handler"] is None and by_rule["/old"]["handler"] is None and by_rule["/"]["build_only"] is False
    _, record, gaps, _ = fixture_rows(tmp_path)
    assert not [r for r in rows(record) if r["path"] in ("/built", "/old")]
    assert not [g for g in gaps if g["detail"].startswith(("/built", "/old"))]


def test_the_script_prints_the_line_of_the_def_of_a_decorated_function_and_not_of_its_first_decorator():
    """`co_firstlineno` of a decorated function is the line of its first decorator, which no record of the function holds: the script
    takes the line of the `def` from the interpreter's own parse of the whole module (`ast`), for a method, a nested function and a
    lambda too, and for a function with a line at column 0 in a string (a parse of the function alone fails there)."""
    files = project()
    handlers = {rule_: found["handler"] for rule_, found in routes_of(recorded("routes")).items()}
    assert handlers["/"]["line"] == line_of(files, "wsgi.py", "def index(")
    assert handlers["/wrapped"]["line"] == line_of(files, "wsgi.py", "def wrapped(")  # `@app.get` and `@guarded` above it
    assert handlers["/page"]["line"] == line_of(files, "wsgi.py", "def show(")  # a method
    assert handlers["/admin/stats"]["line"] == line_of(files, "admin/blueprint.py", "def stats(")
    assert handlers["/nested/inner"]["line"] == line_of(files, "admin/blueprint.py", "def inner(")  # nested, in another file
    assert handlers["/docs"]["line"] == line_of(files, "wsgi.py", "def page(")  # a method with a line at column 0
    assert handlers["/nested-doc"]["line"] == line_of(files, "wsgi.py", "def nested_doc(")  # decorated, nested, a line at column 0
    assert handlers["/lambda"]["line"] == line_of(files, "wsgi.py", "view_func=lambda")  # not a `def`: the line its code starts on
    assert handlers["/orders"]["line"] is None and handlers["/partial"]["line"] is None  # a class-based view, no source file


def test_a_handler_the_snapshot_has_no_record_of_is_a_row_on_its_file_with_the_cause_and_not_a_guess_by_name(tmp_path):
    _, record, _, _ = fixture_rows(tmp_path)
    [lam] = [r for r in rows(record) if r["path"] == "/lambda"]
    assert lam["site"].startswith("wsgi.py:") and lam["symbol"] == "wsgi.py::<module>" and lam["handler"] == "<lambda>"
    assert "without a unique snapshot handler" in lam["gap"]  # the binder's words: the snapshot names a lambda `(lambda)`


def test_a_handler_the_script_gave_no_line_is_a_row_on_its_file_and_the_binder_says_the_gap(tmp_path):
    answer = printed([rule("/x", ["GET"], view("wsgi.py", "index", line=None))])  # an inline answer: a function whose source the interpreter lacks
    record, _, _ = read(tmp_path, project(), [answer])
    [row] = rows(record)
    assert row["site"] == "wsgi.py" and row["symbol"] == "wsgi.py::<module>" and "without a unique snapshot handler" in row["gap"]


def test_a_rule_with_no_view_at_all_is_a_gap_that_says_so_and_no_row(tmp_path):
    answer = printed([rule("/x", ["GET"], None)])  # an inline answer: a rule whose endpoint has no view function, which is not `build_only`
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["outside_snapshot"]
    assert gaps[0]["detail"] == "/x: no function: Flask's view for this endpoint is missing" and gaps[0]["path"] == "."


# -------------------------------------------------------------------- the views of the restored environment

def test_flasks_own_static_rule_is_named_by_the_official_datum_and_is_neither_a_row_nor_a_gap(tmp_path):
    """The rule Flask registers for `static_folder` has the endpoint `static` (the Quickstart documents it; `Flask.__init__` adds it
    when `has_static_folder` is true): the script says `static` of it, from `app.has_static_folder` and the endpoint. A blueprint's own
    (`Blueprint.register`: its `send_static_file`, when its `has_static_folder`) is named by the official data too: `app.blueprints`, and
    the view being the blueprint's bound `send_static_file`."""
    by_rule = routes_of(recorded("routes"))
    statics = {"/static/<path:filename>", "/assets/files/<path:filename>"}  # the application's, and a blueprint's with a `static_folder`
    assert all(by_rule[rule_]["static"] is True for rule_ in statics)
    assert not any(found["static"] for rule_, found in by_rule.items() if rule_ not in statics)
    static = by_rule["/static/<path:filename>"]["handler"]
    assert static["environment"] is True and static["file"].endswith("site-packages/flask/app.py")
    _, record, gaps, _ = fixture_rows(tmp_path)
    assert not [g for g in gaps if g["detail"].startswith(("/static/", "/assets/"))]
    assert not [r for r in rows(record) if r["path"].startswith(("/static", "/assets"))]


def test_the_other_views_of_the_environment_are_counted_in_one_gap_of_the_folder_with_their_modules(tmp_path):
    """A third-party view (`werkzeug.utils.redirect` here: what an extension's route or a decorator that does not use
    `functools.wraps` leaves) is not the project's file: one `model_partial` gap per folder with the count and the modules."""
    by_rule = routes_of(recorded("routes"))
    assert by_rule["/third-party"]["handler"]["environment"] is True and by_rule["/third-party"]["handler"]["module"] == "werkzeug.utils"
    _, record, gaps, _ = fixture_rows(tmp_path)
    [partial] = [g for g in gaps if g["kind"] == "model_partial"]
    assert partial["path"] == "." and "1 rule" in partial["detail"] and "/third-party" in partial["detail"] and "werkzeug" in partial["detail"]
    assert "not of the project" in partial["detail"] and "flask" not in partial["detail"].replace("Flask", "")  # `static` is not in the count
    assert not [r for r in rows(record) if r["path"] == "/third-party"] and not [g for g in gaps if g["detail"].startswith("/third-party")]


def test_a_folder_whose_rules_are_all_the_frameworks_says_so_and_does_not_yield_nothing(tmp_path):
    only_static = printed([rule("/static/<path:filename>", ["GET"], view("../venv/flask/app.py", "Flask.__init__.<locals>.<lambda>", environment=True),
                                static=True)])  # an inline answer: a Flask application with nothing but its static rule
    record, gaps, _ = read(tmp_path, project(), [only_static])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_partial"] and "no rule of the project" in gaps[0]["detail"]


def test_a_view_installed_from_a_local_directory_is_a_gap_that_says_it_is_a_copy_of_the_project_and_where_from(tmp_path):
    """PEP 610: `direct_url.json` of the distribution (read with `importlib.metadata`) says it was installed from a directory: the
    project's own code, copied into `site-packages`, which is not the snapshot's file."""
    answer = recorded("installed-copy")
    assert answer["returncode"] == 0, answer["stderr"]
    shared = routes_of(answer)["/shared"]["handler"]
    assert shared["environment"] is True and shared["distribution"]["name"] == "sharedlib"
    assert shared["distribution"]["url"].startswith("file:///work/libs/shared")
    record, gaps, _ = read(tmp_path, project(LAYOUTS / "installed-copy"), [answer])
    [gap] = [g for g in gaps if g["detail"].startswith("/shared: ")]
    assert gap["kind"] == "outside_snapshot" and "installed copy of the project, not the snapshot's file" in gap["detail"]
    assert "sharedlib" in gap["detail"] and "file:///work/libs/shared" in gap["detail"]
    assert [r["path"] for r in rows(record) if not r.get("gap")] == ["/own"]  # the project's own view is a row; Flask's static is silent
    assert not [g for g in gaps if g["kind"] == "model_partial"]


def test_a_view_outside_the_snapshot_and_outside_the_environment_is_a_gap_with_the_rule_and_the_file_and_no_row(tmp_path):
    stdlib = routes_of(recorded("routes"))["/stdlib"]["handler"]  # `json.dumps`: the interpreter's own library
    assert stdlib["environment"] is False and stdlib["file"].endswith("python3.12/json/__init__.py")
    _, record, gaps, _ = fixture_rows(tmp_path)
    [gap] = [g for g in gaps if g["detail"].startswith("/stdlib: ")]
    assert gap["kind"] == "outside_snapshot" and "dumps has no source file of the project the snapshot holds" in gap["detail"]
    assert gap["detail"].endswith(f"({stdlib['file']})") and gap["path"] == "."
    assert not [r for r in rows(record) if r["path"] == "/stdlib"]


@pytest.mark.parametrize("rule_, what", [("/partial", "functools.partial"), ("/callable", "wsgi.Counter")])
def test_a_view_that_is_not_a_function_has_a_gap_that_names_what_it_is_and_no_row(tmp_path, rule_, what):
    _, record, gaps, _ = fixture_rows(tmp_path)  # a `functools.partial`, an object with `__call__`: no source file, no `__qualname__`
    [gap] = [g for g in gaps if g["detail"].startswith(f"{rule_}: ")]
    assert gap["kind"] == "outside_snapshot" and gap["detail"] == f"{rule_}: {what} has no source file of the project the snapshot holds (none)"
    assert not [r for r in rows(record) if r["path"] == rule_]


def test_a_class_based_view_is_a_row_on_its_file_with_the_gap_for_the_method_it_does_not_read(tmp_path):
    _, record, _, _ = fixture_rows(tmp_path)
    mine = sorted((r["path"], r["method"], "class-based view" in r["gap"], r["symbol"]) for r in rows(record)
                  if r["path"] in ("/orders", "/hello"))
    assert mine == [("/hello", "GET", True, "wsgi.py::<module>"), ("/orders", "GET", True, "wsgi.py::<module>"),
                    ("/orders", "POST", True, "wsgi.py::<module>")]


# ------------------------------------------------------------------- the path schema, from werkzeug's own parse of the rule

def test_the_script_prints_each_argument_with_the_part_isolating_werkzeug_gives_its_converter():
    """`part_isolating` is werkzeug's documented attribute of a converter (`BaseConverter`): False where the argument may hold a `/`.
    Read from werkzeug 3.1.9 (`benchmarks/flask-routes/results/werkzeug-source.json`): `PathConverter` sets it False; a converter that
    defines its own `regex` and not `part_isolating` gets `"/" not in regex`, so `PairConverter` (a `/` in its regex) is False and
    `TailRegexConverter` (a `PathConverter` with `regex = ".+"`) is True, which is how the matcher then treats it (`url-matching.json`)."""
    by_rule = routes_of(recorded("routes"))
    assert by_rule["/admin/users/<int:user_id>"]["arguments"] == {"user_id": True}
    assert by_rule["/string/<string:name>"]["arguments"] == {"name": True} and by_rule["/uuid/<uuid:u>"]["arguments"] == {"u": True}
    assert by_rule["/files/<path:name>"]["arguments"] == {"name": False}
    assert by_rule["/slug/<slug:s>"]["arguments"] == {"s": True}
    assert by_rule["/tail/<tail:rest>"]["arguments"] == {"rest": False}  # a PathConverter that only inherits
    assert by_rule["/tailre/<tailre:rest>"]["arguments"] == {"rest": True}
    assert by_rule["/pair/<pair:p>"]["arguments"] == {"p": False}
    assert by_rule["/glued/<a>-<b>"]["arguments"] == {"a": True, "b": True}
    assert by_rule["/"]["arguments"] == {} and by_rule["/"]["parts"] == [[False, "/"]]
    assert by_rule["/glued/<a>-<b>"]["parts"] == [[False, "/"], [False, "glued"], [False, "/"], [True, "a"], [False, "-"], [True, "b"]]


SCHEMAS = {  # the path as `flows.path_schema` reads it: what Noir's `/admin/users/:user_id` is, `/admin/users/{}`
    "/": "/", "/items": "/items", "/admin/stats": "/admin/stats", "/nested/inner": "/nested/inner",
    "/admin/users/<int:user_id>": "/admin/users/{}", "/int/<int:id>": "/int/{}", "/string/<string:name>": "/string/{}",
    "/uuid/<uuid:u>": "/uuid/{}", "/slug/<slug:s>": "/slug/{}", "/two/<int:x>/<int:y>": "/two/{}/{}",
    "/tailre/<tailre:rest>": "/tailre/{}",  # werkzeug's own matcher takes it as one segment
    "/glued/<a>-<b>": "/glued/{}-{}",  # two parameters in one segment: `path_schema` writes both, and no call meets it (see the links test)
    "/strict/": "/strict", "/loose": "/loose", "/relaxed/": "/relaxed",  # `strict_slashes` and the trailing slash: the same schema
    "/files/<path:name>": None, "/tail/<tail:rest>": None, "/pair/<pair:p>": None}  # a parameter that may hold a `/`: no single schema


def test_a_rule_row_has_the_path_schema_of_its_parameters_and_none_where_a_parameter_may_hold_a_slash(tmp_path):
    import flows
    _, record, _, _ = fixture_rows(tmp_path)
    mine = [r for r in rows(record) if r["path"] in SCHEMAS]
    assert {r["path"] for r in mine} == set(SCHEMAS)
    assert {r["path"]: r["schema"] for r in mine} == SCHEMAS and all("schema" in r for r in mine)
    assert next(r for r in mine if r["path"] == "/admin/users/<int:user_id>")["schema"] == flows.path_schema("/admin/users/:user_id")  # Noir's


def test_the_schema_comes_from_werkzeugs_parts_not_from_the_text_of_the_rule(tmp_path):
    """A rule whose `parts` or `arguments` the installed werkzeug does not give has no schema (None: a gap of the declared routes),
    never one made from `rule`; a converter that does not say `part_isolating` is not taken for one that does."""
    answer = recorded("routes")
    document = json.loads(answer["stdout"])
    for found in document["routes"]:
        if found["rule"] == "/admin/users/<int:user_id>":
            found["parts"] = None
        if found["rule"] == "/int/<int:id>":
            found["arguments"]["id"] = None
        if found["rule"] == "/two/<int:x>/<int:y>":
            found["arguments"] = None
    record, _, _ = read(tmp_path, project(), [{**answer, "stdout": json.dumps(document)}])
    wanted = ("/admin/users/<int:user_id>", "/int/<int:id>", "/two/<int:x>/<int:y>", "/string/<string:name>")
    assert {r["path"]: r["schema"] for r in rows(record) if r["path"] in wanted} == {
        "/admin/users/<int:user_id>": None, "/int/<int:id>": None, "/two/<int:x>/<int:y>": None, "/string/<string:name>": "/string/{}"}


def test_the_host_part_of_a_rule_is_not_in_its_path_and_its_arguments_do_not_make_holes(tmp_path):
    hosts = routes_of(recorded("host-matching"))
    assert hosts["/<tenant>/x"]["parts"] == [[False, "/"], [True, "tenant"], [False, "/"], [False, "x"]]
    assert hosts["/<tenant>/x"]["arguments"] == {"sub": True, "tenant": True}  # `sub` is in the host: no hole of the path
    record, _, _ = read(tmp_path, project(), [recorded("host-matching")])
    assert {r["path"]: r["schema"] for r in rows(record)} == {"/h": "/h", "/<tenant>/x": "/{}/x"}
    assert all("host" not in r for r in rows(record))  # nothing in the links reads a host: the row has none


# ------------------------------------------------------------------- what the script reports of a project that does not load

@pytest.mark.parametrize("variant, returncode, cause", [
    ("no-wsgi", 3, "Could not locate a Flask application"),  # no `wsgi.py` or `app.py`, no `FLASK_APP`
    ("module-raises", 3, "boom"),
    ("missing-package", 3, "not_installed"),
    ("two-apps", 3, "multiple Flask applications"),
    ("module-hangs", 124, "did not end in 900 seconds"),
])
def test_an_application_that_does_not_load_or_a_script_that_is_stopped_is_the_folder_s_gap_with_the_cause_and_no_row(tmp_path, variant, returncode, cause):
    answer = recorded(variant)
    assert answer["returncode"] == returncode
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and cause in gaps[0]["detail"] and gaps[0]["path"] == "."


@pytest.mark.parametrize("variant, route", [("app-py", "/"), ("flask-app-variable", "/"), ("factory", "/made")])
def test_where_flask_finds_the_application_by_its_own_rules_the_routes_are_read_as_for_wsgi_py(tmp_path, variant, route):
    answer = recorded(variant)
    assert answer["returncode"] == 0, answer["stderr"]
    assert route in routes_of(answer)


def test_a_flaskenv_file_names_the_application_only_where_python_dotenv_is_installed_and_the_restore_does_not_install_it(tmp_path):
    with_dotenv, without = recorded("flaskenv-with-dotenv"), recorded("flaskenv-without-dotenv")
    assert with_dotenv["returncode"] == 0 and "/admin/stats" in routes_of(with_dotenv)
    assert without["returncode"] == 3 and "python-dotenv" in without["stderr"]  # Flask's own tip, and then it finds no application
    _, gaps, _ = read(tmp_path, project(), [without])
    assert "python-dotenv" in gaps[0]["detail"] and "Could not locate a Flask application" in gaps[0]["detail"]


def test_the_rows_and_the_gaps_a_source_persisted_are_the_ones_from_record_gives_back(tmp_path):
    _, record, gaps, _ = fixture_rows(tmp_path)
    back_rows, back_gaps = flask_app.from_record(record)
    assert back_rows == rows(record) and back_gaps == gaps and back_rows


def test_an_application_with_no_rule_is_a_gap_and_no_row(tmp_path):
    record, gaps, _ = read(tmp_path, project(), [recorded("no-rules")])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_partial"]


# ---------------------------------------------------------------- what follows the JSON, and what the script does not take for the application

def test_what_the_project_prints_while_it_loads_never_reaches_the_standard_output_which_is_the_json_alone():
    """Descriptor 1 is the standard error while the project's code runs: a `print` that is not flushed dies with its buffer when the
    script leaves (`os._exit`), one that is flushed is on the standard error. Either way the standard output is the answer alone."""
    answer = recorded("module-prints")
    assert answer["returncode"] == 0 and "wsgi loaded" not in answer["stdout"]
    assert json.loads(answer["stdout"])["called"] is True and routes_of(answer)


@pytest.mark.parametrize("variant, said", [("thread", "a thread that never ends"), ("atexit-print", "a print at exit"),
                                           ("replaced-stdout", "a project that replaces sys.stdout")])
def test_nothing_the_project_does_after_the_json_changes_the_answer(tmp_path, variant, said):
    """The script writes the JSON to the descriptor it saved before the project's code ran, and leaves with `os._exit`: a non-daemon
    thread does not keep it alive (the old answer was exit 124 and no output), an `atexit` print is not the last line, a replaced
    `sys.stdout` hides nothing (`results/before-review/`)."""
    answer = recorded(variant)
    assert answer["returncode"] == 0, (said, answer["stderr"])
    assert json.loads(answer["stdout"])["called"] is True and set(routes_of(answer)) == {"/static/<path:filename>", "/x"}
    record, gaps, _ = read(tmp_path, {"requirements.txt": "flask==3.1.3\n", "wsgi.py": "def x():\n    return 'x'\n"}, [answer])
    assert [r["path"] for r in rows(record)] == ["/x"] and not [g for g in gaps if g["kind"] == "model_failed"]


def test_a_dispatcher_that_mounts_the_loaded_application_is_a_gap_with_the_prefix_and_never_rows_with_the_wrong_paths(tmp_path):
    """`application = DispatcherMiddleware(Flask("main"), {"/sub": sub})`, or the same under another name (`server`): the one Flask instance
    of the module, which Flask's loader picks, is `sub`, and its rules lack the mount prefix (`results/before-review/dispatcher.json`:
    `/hello`, which the dispatcher answers at `/sub/hello` and not at `/hello`, `results/dispatcher-serves.json`). The script finds the
    dispatcher by its class (`werkzeug.middleware.dispatcher.DispatcherMiddleware`, with its documented `app` and `mounts`) among the
    globals of the module that holds the loaded application and on `app.wsgi_app`, never by the name it has."""
    for variant in ("dispatcher", "dispatcher-server"):
        answer = recorded(variant)
        assert answer["returncode"] == 0, answer["stderr"]
        dispatch = json.loads(answer["stdout"])["dispatch"]
        assert dispatch["loaded"] == "mounted" and dispatch["prefixes"] == ["/sub"], variant
        record, gaps, _ = read(tmp_path / variant, project(), [answer])
        assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_partial"] and gaps[0]["path"] == ".", variant
        assert "DispatcherMiddleware" in gaps[0]["detail"] and "/sub" in gaps[0]["detail"] and "none is read" in gaps[0]["detail"], variant


@pytest.mark.parametrize("variant", ["dispatcher-main", "dispatcher-wsgi-app"])
def test_a_dispatcher_whose_main_application_is_the_loaded_one_keeps_its_rows_and_names_the_applications_it_mounts(tmp_path, variant):
    """`application = DispatcherMiddleware(app, {"/sub": sub})`, or Flask's documented `app.wsgi_app = DispatcherMiddleware(app.wsgi_app, ...)`:
    the rules of the loaded application are served as they are; the mounted application's (`/sub/hello`) are named in a gap, not rows."""
    answer = recorded(variant)
    assert answer["returncode"] == 0, answer["stderr"]
    dispatch = json.loads(answer["stdout"])["dispatch"]
    assert dispatch["loaded"] == "main" and dispatch["prefixes"] == []
    [mount] = dispatch["mounts"]
    assert mount["prefix"] == "/sub" and "/sub/hello" in mount["rules"] and mount["count"] == len(mount["rules"])
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert [r["path"] for r in rows(record)] == ["/"] and [g["kind"] for g in gaps] == ["model_partial"]
    assert "/sub/hello" in gaps[0]["detail"] and "not rows" in gaps[0]["detail"]


@pytest.mark.parametrize("variant, route", [("dash-style", "/dash"), ("imported-app-module", "/viaapp")])
def test_a_server_that_is_not_called_app_is_no_gap_where_no_dispatcher_is_there(tmp_path, variant, route):
    """`app = Dash(...)` with `server = app.server` (an `app` that is not Flask), and `import app` with `server = app.app` (an `app` that is a
    module): the loader picks the one Flask instance and nothing wraps it. The names `app` and `application` decide nothing."""
    answer = recorded(variant)
    assert answer["returncode"] == 0, answer["stderr"]
    assert json.loads(answer["stdout"])["dispatch"] is None and route in routes_of(answer)
    record, gaps, _ = read(tmp_path, project(**{"app.py": "def view():\n    return 'x'\n"}), [answer])  # `app.py` is in the snapshot: rows, not a gap
    assert [r["path"] for r in rows(record)] == [route] and not [g for g in gaps if g["kind"] == "model_partial"]


def test_what_the_project_does_to_the_descriptor_the_answer_goes_to_is_a_gap_with_its_own_cause(tmp_path):
    """The script saves descriptor 1 at a high number, and checks before it writes that it is still the descriptor it saved (a project that
    closes or replaces it on purpose, or a pipe that broke): any failure to write leaves with exit 4, not through the interpreter's exit."""
    answer = recorded("closes-answer")
    assert answer["returncode"] == 4 and answer["stdout"] == "" and "could not write" in answer["stderr"]
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"]
    assert "could not write its answer" in gaps[0]["detail"] and "exit 4" in gaps[0]["detail"] and "restored for '.'" in gaps[0]["detail"]


# ------------------------------------------------------- what the script prints is checked as `read` uses it

MALFORMED = [
    ("a rule with no handler key", lambda r: r.pop("handler")),
    ("a method that is not text", lambda r: r.update(methods=[1])),
    ("methods that are not a list", lambda r: r.update(methods="GET")),
    ("a part that is not a pair", lambda r: r.update(parts=[[False]])),
    ("a part whose flag is not a boolean", lambda r: r.update(parts=[["x", "/"]])),
    ("arguments that are not a mapping", lambda r: r.update(arguments=["a"])),
    ("an argument whose isolation is not a boolean", lambda r: r.update(arguments={"a": "yes"})),
    ("a flag that is not a boolean", lambda r: r.update(build_only="no")),
    ("a file that is not text", lambda r: r["handler"].update(file=5)),
    ("a qualified name that is not text", lambda r: r["handler"].update(qualname=5)),
    ("a line that is not a number", lambda r: r["handler"].update(line="7")),
    ("an environment flag that is not a boolean", lambda r: r["handler"].update(environment="yes")),
    ("a distribution that is not a mapping", lambda r: r["handler"].update(distribution="x")),
    ("a kind that is neither a function nor a class", lambda r: r["handler"].update(kind="method"))]


@pytest.mark.parametrize("what, spoil", MALFORMED, ids=[what for what, _ in MALFORMED])
def test_a_value_of_the_answer_that_read_would_use_and_is_malformed_is_that_folder_s_gap_and_the_other_folders_keep_their_rows(tmp_path, what, spoil):
    """Inline answers: two folders, the first spoiled in one value. The check of the layout is whole, so `read` never raises in the
    middle of a folder and loses the rows of the ones before and after it."""
    files = {"api/requirements.txt": "flask==3.1.3\n", "api/wsgi.py": "def x():\n    return 'x'\n",
             "worker/requirements.txt": "flask==3.1.3\n", "worker/wsgi.py": "def y():\n    return 'y'\n"}
    api = rule("/x", ["GET"], view("wsgi.py", "x", line=1))
    spoil(api)
    answers = [printed([api]), printed([rule("/y", ["GET"], view("wsgi.py", "y", line=1))])]
    record, gaps, _ = read(tmp_path, files, answers)
    assert [g["kind"] for g in gaps] == ["model_failed"] and gaps[0]["path"] == "api" and "known layout" in gaps[0]["detail"], what
    assert [(r["path"], r["site"]) for r in rows(record)] == [("/y", "worker/wsgi.py:1")]


@pytest.mark.parametrize("answer, cause", [  # Daodan's own check of what the script printed: the layout, not Flask's output
    ({"returncode": 0, "stdout": "not json\n", "stderr": ""}, "printed no JSON"),
    ({"returncode": 0, "stdout": "log of the project\n" + json.dumps({"called": True, "routes": []}), "stderr": ""}, "printed no JSON"),
    ({"returncode": 0, "stdout": json.dumps({"called": True, "routes": [{"rule": 1}]}), "stderr": ""}, "printed no JSON"),
    ({"returncode": 0, "stdout": json.dumps([]), "stderr": ""}, "printed no JSON"),
    ({"returncode": 137, "stdout": "", "stderr": ""}, "exit 137"),
])
def test_a_line_that_is_not_the_known_layout_or_a_killed_script_is_the_folder_s_gap_with_the_cause(tmp_path, answer, cause):
    record, gaps, _ = read(tmp_path, project(), [{**answer, "root": "/work"}])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and cause in gaps[0]["detail"] and gaps[0]["path"] == "."


@pytest.mark.parametrize("spoil", [
    "x", {"loaded": "who", "prefixes": [], "mounts": []}, {"loaded": "mounted", "prefixes": "/sub", "mounts": []},
    {"loaded": "mounted", "prefixes": ["/sub"], "mounts": [{"prefix": "/sub", "rules": [1], "count": 1}]},
    {"loaded": "mounted", "prefixes": ["/sub"], "mounts": [{"prefix": "/sub", "rules": [], "count": "1"}]}])
def test_a_dispatch_of_an_unknown_layout_is_that_folder_s_gap(tmp_path, spoil):
    answer = printed([rule("/x", ["GET"], view("wsgi.py", "x", line=1))], dispatch=spoil)  # an inline answer: a dispatch the script does not print
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and "known layout" in gaps[0]["detail"]


def test_an_answer_too_deep_for_the_parser_is_that_folder_s_gap_and_the_other_folders_keep_their_rows(tmp_path):
    """`json.loads` of a document nested 200000 deep raises `RecursionError`, which is not a `ValueError`: the boundary of the folder catches it."""
    files = {"api/requirements.txt": "flask==3.1.3\n", "api/wsgi.py": "def x():\n    return 'x'\n",
             "worker/requirements.txt": "flask==3.1.3\n", "worker/wsgi.py": "def y():\n    return 'y'\n"}
    deep = {"returncode": 0, "stdout": "[" * 200000 + "]" * 200000, "stderr": "", "root": "/work"}
    record, gaps, _ = read(tmp_path, files, [deep, printed([rule("/y", ["GET"], view("wsgi.py", "y", line=1))])])
    assert [(g["kind"], g["path"]) for g in gaps] == [("model_failed", "api")]
    assert [(r["path"], r["site"]) for r in rows(record)] == [("/y", "worker/wsgi.py:1")]


def test_a_value_the_check_let_through_and_read_cannot_use_is_the_folder_s_gap_and_not_an_exception_that_loses_the_others(tmp_path, monkeypatch):
    """If the check of the layout misses a value, `read` raises (`KeyError` here, for a rule with no `handler`) in the middle of a folder: the
    boundary of the folder catches `ValueError`, `KeyError`, `TypeError` and `RecursionError`, so the rows of the other folders stay."""
    monkeypatch.setattr(flask_app, "_printed", lambda result: json.loads(result["stdout"]))  # a check that lets everything through
    files = {"api/requirements.txt": "flask==3.1.3\n", "api/wsgi.py": "def x():\n    return 'x'\n",
             "worker/requirements.txt": "flask==3.1.3\n", "worker/wsgi.py": "def y():\n    return 'y'\n"}
    broken = rule("/x", ["GET"], None)
    del broken["handler"]
    record, gaps, _ = read(tmp_path, files, [printed([broken]), printed([rule("/y", ["GET"], view("wsgi.py", "y", line=1))])])
    assert [(g["kind"], g["path"]) for g in gaps] == [("model_failed", "api")] and "KeyError" in gaps[0]["detail"]
    assert [r["path"] for r in rows(record)] == ["/y"]


def ignored_lockfiles(tmp_path, ignore):
    """A project in a git work tree whose lockfiles are untracked, ignored or not (`ignore`): the files of the project, its snapshot."""
    import shutil
    import subprocess
    git = shutil.which("git")
    if git is None:
        pytest.skip("no git: the perimeter cannot ask it what is ignored")
    project_dir = tmp_path / "proj"
    files = {"pyproject.toml": "[project]\nname='r'\nversion='1'\ndependencies=['flask==3.1.3']\n", "poetry.lock": "# lock\n",
             "api/pyproject.toml": "[project]\nname='a'\nversion='1'\ndependencies=['flask==3.1.3']\n", "api/uv.lock": "version = 1\n",
             ".gitignore": "poetry.lock\nuv.lock\n" if ignore else "\n"}
    for rel, text in files.items():
        (project_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (project_dir / rel).write_text(text, encoding="utf-8", newline="\n")
    run = ["-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", str(project_dir)]
    subprocess.run([git, *run, "init", "-q"], check=True)
    subprocess.run([git, *run, "add", "pyproject.toml", "api/pyproject.toml", ".gitignore"], check=True)
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project_dir, manifest)
    return project_dir, manifest


def test_the_lockfiles_the_command_counts_are_the_ones_the_restore_sees_and_a_git_ignored_one_is_none_of_them(tmp_path):
    """The container is given the perimeter of the project (git-ignored untracked files left out) and restores from it. The command picks the
    Python from the same file set (`preparation.perimeter_files`), so an ignored lockfile changes neither: the manager is `pip` in both."""
    import preparation
    managers = {}
    for ignore in (True, False):
        project_dir, manifest = ignored_lockfiles(tmp_path / str(ignore), ignore)
        asked = []
        premap.write(manifest, sources=SOURCES, runner=lambda commands: asked.extend(commands) or [printed([]) for _ in commands])
        restored = container_runner._python(project_dir)
        managers[ignore] = ({c["cwd"]: c["venv"] for c in asked}, [line.split("for f in ")[1].split(";")[0] for line in restored["lines"][1:]],
                            " ".join(c["argv"][2] for c in asked), " ".join(restored["lines"]))
    commands, restore, words, lines = managers[True]
    assert commands == {".": ".", "api": "."} and restore == ["'.'"] and "poetry" not in words and "poetry" not in lines and "uv sync" not in lines
    commands, restore, words, lines = managers[False]  # not ignored: both read the lockfiles, and both say the same
    assert commands == {".": ".", "api": "api"} and restore == ["'.'", "'api'"] and "poetry env info -e" in words and f"{preparation.VENVS}/api/bin/python" in words
    assert "poetry install" in lines and "uv sync" in lines


def test_several_folders_each_with_rows_are_read_one_by_one_and_a_folder_that_fails_does_not_take_the_others(tmp_path):
    files = {"api/requirements.txt": "flask==3.1.3\n", "api/wsgi.py": "def x():\n    return 'x'\n",
             "tools/requirements.txt": "flask==3.1.3\n", "tools/wsgi.py": "def t():\n    return 't'\n",
             "worker/requirements.txt": "flask==3.1.3\n", "worker/wsgi.py": "def z():\n    return 'z'\n"}
    answers = [printed([rule("/x", ["GET"], view("wsgi.py", "x", line=1))]),  # api
               {"returncode": 3, "stdout": "", "stderr": "NoAppException: Could not locate a Flask application\n", "root": "/work"},  # tools
               printed([rule("/z", ["GET", "POST"], view("wsgi.py", "z", line=1))])]  # worker
    record, gaps, asked = read(tmp_path, files, answers)
    assert [c["cwd"] for c in asked] == ["api", "tools", "worker"]
    assert sorted((r["path"], r["method"], r["site"], r["symbol"]) for r in rows(record)) == [
        ("/x", "GET", "api/wsgi.py:1", "api/wsgi.py::x"), ("/z", "GET", "worker/wsgi.py:1", "worker/wsgi.py::z"),
        ("/z", "POST", "worker/wsgi.py:1", "worker/wsgi.py::z")]
    assert [(g["kind"], g["path"]) for g in gaps] == [("model_failed", "tools")]


# ----------------------------------------- the Python the command runs, from the folders the restore makes (`preparation`)

def commands_of(tmp_path, files, sources=SOURCES):
    _, manifest = manifest_of(tmp_path, files)
    asked = []
    premap.write(manifest, sources=sources, runner=lambda commands: asked.extend(commands) or [printed([]) for _ in commands])
    return asked


def test_a_plain_root_project_runs_the_script_in_the_environment_of_the_root(tmp_path):
    import preparation
    [command] = commands_of(tmp_path, project())
    assert command["cwd"] == "." and command["venv"] == "." and command["tool"] == "flask" and command["network"] == "none"
    assert command["argv"][:2] == ["sh", "-c"] and command["argv"][3:] == ["flask", "900", f"{preparation.T}/flask_routes.py"]
    assert f'exec timeout --kill-after=10 "$1" {preparation.VENVS}/./bin/python -I "$2"' == command["argv"][2]


def test_a_uv_workspace_member_runs_in_the_environment_of_the_workspace_root_and_keeps_its_own_folder_as_cwd(tmp_path):
    import preparation
    [command] = commands_of(tmp_path, project(LAYOUTS / "uv-workspace"))  # `api` declares flask; the root has the `uv.lock` and the workspace
    assert command["cwd"] == "api" and command["venv"] == "." and f"{preparation.VENVS}/./bin/python" in command["argv"][2]
    assert "poetry" not in command["argv"][2]


def test_a_root_pyproject_with_a_requirements_file_in_a_subfolder_uses_the_root_environment(tmp_path):
    import preparation
    [command] = commands_of(tmp_path, project(LAYOUTS / "root-and-sub"))
    assert command["cwd"] == "api" and command["venv"] == "." and f"{preparation.VENVS}/./bin/python" in command["argv"][2]


def test_a_poetry_project_asks_poetry_for_its_environment_where_it_lives_in_poetrys_own_cache(tmp_path):
    [command] = commands_of(tmp_path, project(LAYOUTS / "poetry"))  # flask is declared in `pyproject.toml` only: the module graph says so
    assert command["cwd"] == "." and command["venv"] == "." and '"$(cd /work/. && poetry env info -e)"' in command["argv"][2]
    assert "venvs" not in command["argv"][2]
    assert container_runner._python(LAYOUTS / "poetry")["needs"] == ["poetry"]  # the restore installs poetry, which brings the uv it uses


def test_a_folder_with_its_own_lockfile_below_the_root_is_its_own_environment(tmp_path):
    import preparation
    files = {"pyproject.toml": "[project]\nname='r'\nversion='1'\n", "api/pyproject.toml": "[project]\nname='a'\nversion='1'\ndependencies=['flask==3.1.3']\n",
             "api/uv.lock": "", "api/wsgi.py": "x = 1\n"}
    [command] = commands_of(tmp_path, files)
    assert command["cwd"] == "api" and command["venv"] == "api" and f"{preparation.VENVS}/api/bin/python" in command["argv"][2]


def test_flask_declared_only_in_a_pyproject_runs_there_and_a_requirements_file_that_is_not_a_manifest_names_no_folder(tmp_path):
    files = {"api/pyproject.toml": "[project]\nname='a'\nversion='1'\ndependencies=['flask==3.1.3']\n", "api/wsgi.py": "x = 1\n",
             "docs/requirements/base.txt": "flask\n", "worker/requirements.txt": "celery==5.4.0\n"}
    assert [c["cwd"] for c in commands_of(tmp_path, files)] == ["api"]
    assert commands_of(tmp_path / "no-module-graph", files, sources=(premap.requirements, flask_app)) == []  # `requirements` alone does not read it


def test_the_folders_share_the_time_and_none_has_less_than_ten_seconds():
    assert [flask_app.run_seconds(n) for n in (1, 3, 90, 200)] == [900, 300, 10, 10]


def test_only_a_folder_whose_manifest_declares_flask_runs_the_script(tmp_path):
    _, manifest = manifest_of(tmp_path / "plain", {"requirements.txt": "django==6.1.3\n"})
    record = premap.write(manifest, sources=(premap.requirements, flask_app), runner=lambda commands: 1 / 0)
    assert [s["state"] for s in record["sources"] if s["source"].startswith("flask")] == ["not_needed"]


# ----------------------------------------------------------------- the layouts, measured on Modal

def test_the_script_run_by_the_python_of_a_uv_workspace_gives_the_rows_of_the_member_on_its_own_folder(tmp_path):
    answer = recorded("uv-workspace")
    assert answer["returncode"] == 0, answer["stderr"]
    files = project(LAYOUTS / "uv-workspace")
    record, gaps, asked = read(tmp_path, files, [answer], sources=SOURCES)
    [row] = [r for r in rows(record) if r["path"] == "/hello"]
    assert row["site"] == f"api/wsgi.py:{line_of(files, 'api/wsgi.py', 'def hello(')}" and row["symbol"] == "api/wsgi.py::hello"
    assert [c["cwd"] for c in asked] == ["api"] and not [g for g in gaps if g["kind"] == "model_failed"]


def test_the_script_run_by_the_python_poetry_names_gives_the_rows_of_a_project_that_declares_flask_in_pyproject_only(tmp_path):
    answer = recorded("poetry")
    assert answer["returncode"] == 0, answer["stderr"]
    files = project(LAYOUTS / "poetry")
    record, _, asked = read(tmp_path, files, [answer], sources=SOURCES)
    [row] = [r for r in rows(record) if r["path"] == "/hello"]
    assert row["site"] == f"wsgi.py:{line_of(files, 'wsgi.py', 'def hello(')}" and [c["cwd"] for c in asked] == ["."]


def test_a_project_whose_requirements_are_in_a_subfolder_of_a_root_that_does_not_declare_flask_is_a_gap_that_names_the_missing_package(tmp_path):
    answer = recorded("root-and-sub")
    assert answer["returncode"] == 3 and "No module named 'flask'" in answer["stderr"]
    record, gaps, _ = read(tmp_path, project(LAYOUTS / "root-and-sub"), [answer], sources=SOURCES)
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and gaps[0]["path"] == "api"
    assert "No module named 'flask'" in gaps[0]["detail"] and "restored for '.'" in gaps[0]["detail"]


# ---------------------------------------------------------- what is persisted, and where the script runs

def test_the_recorded_answers_carry_the_print_of_the_script_that_made_them_and_the_version_of_the_source_they_were_made_for():
    """A pre-map is fresh while its source's `NAME@VERSION` is the one it was made by (`premap.state`): a script that changes with no
    new `VERSION` leaves stale rows in a project's pre-map. The recording holds both: changing the script fails here until it is
    recorded again, and the record is made with the `VERSION` the source has then: raise it with the script."""
    script = container_runner.SCRIPTS / "flask_routes.py"
    printed_digest = hashlib.sha256(script.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert json.loads((RECORDED / "script.json").read_text(encoding="utf-8")) == {"flask_routes.py": printed_digest, "version": flask_app.VERSION}, (
        "the script or the version changed: record the answers again (`benchmarks/flask-routes/modal_probe.py`)")


def test_the_runner_restores_the_python_environment_of_each_folder_and_the_script_is_unpacked_beside_the_tools(tmp_path):
    import preparation
    spec = container_runner.TOOLS["flask"]
    assert spec["restores"] == "python" and spec["registries"] and spec["memory"] == container_runner.TOOLS["next"]["memory"]
    assert "flask_routes.py" in {name for _, _, name in spec["files"]} and f"{preparation.T}/flask_routes.py" in spec["setup"][0]
    project_dir = tmp_path / "p"
    (project_dir / "api").mkdir(parents=True)
    (project_dir / "api/requirements.txt").write_text("flask==3.1.3\n", encoding="utf-8")
    (project_dir / "docs").mkdir()
    (project_dir / "docs/uv.lock").write_text("", encoding="utf-8")
    (project_dir / "docs/pyproject.toml").write_text("[project]\nname='d'\nversion='1'\n", encoding="utf-8")
    restored = container_runner._python(project_dir)
    assert len(restored["lines"]) == 3 and any("'api'" in line and "uv venv" in line for line in restored["lines"])
    assert any("'docs'" in line and "uv sync" in line for line in restored["lines"])
    assert set(restored["needs"]) == {"uv"}


def test_the_folder_of_the_root_is_restored_into_a_directory_that_exists_before_uv_makes_the_environment_there(tmp_path):
    """Measured on Modal (`benchmarks/flask-routes/results/venv-dir.json`): `uv venv <venvs>/.`, which is the root folder's environment,
    fails with `failed to create directory` when `<venvs>` is not there (the runner's setup makes `tools/bin` and `home`, no `venvs`),
    where `uv venv <venvs>/api` makes its parents. The root folder's restore failed, and the script's command ended with exit 127."""
    import preparation
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("flask==3.1.3\n", encoding="utf-8")
    restored = container_runner._python(project_dir)
    assert restored["lines"][0] == f"mkdir -p {preparation.VENVS}"
    assert any("for f in '.'" in line and "uv venv" in line for line in restored["lines"][1:])
    first, _, _, _ = container_runner.plan("flask", [], [], restored["lines"], restored["needs"])
    setup = first["argv"][2]
    assert setup.index(f"mkdir -p {preparation.VENVS}") < setup.index("uv venv")  # the order the container runs them in
    (tmp_path / "empty").mkdir()
    assert container_runner._python(tmp_path / "empty")["lines"] == []  # no Python folder, no `venvs` made


def test_no_engine_carries_the_reason_as_the_source_s_gap_and_nothing_of_the_project_runs_here(tmp_path):
    _, manifest = manifest_of(tmp_path, project())
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        record = premap.write(manifest, sources=(premap.requirements, flask_app), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record


# ------------------------------------------- the project's code never runs on the host (AGENTS.md, «Regola invalicabile»)

def marked_project(tmp_path, monkeypatch):
    """A project that declares Flask and holds all a load of its application would start, each file leaving its own mark in `marks/`
    if it runs on this machine: the module `wsgi.py`, the package `admin/`, `sitecustomize.py` and a `conftest.py`; and, first on the
    PATH, a stand-in for each program that would start it (python, python3, uv, poetry, timeout, flask) that writes a mark too."""
    marks, tools = tmp_path / "marks", tmp_path / "bin"
    marks.mkdir()
    tools.mkdir()

    def mark(name):
        return f"import pathlib\npathlib.Path({json.dumps((marks / name).as_posix())}).write_text('ran')\n"
    for name in ("python", "python3", "uv", "poetry", "timeout", "flask"):
        (tools / name).write_text(f'#!/bin/sh\necho "$0 $*" >> "{marks}/tool-{name}"\n', encoding="utf-8", newline="\n")
        (tools / name).chmod(0o755)
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    files = project(**{"wsgi.py": mark("wsgi.py") + "from flask import Flask\napp = Flask(__name__)\n", "admin/__init__.py": mark("admin"),
                       "sitecustomize.py": mark("sitecustomize.py"), "conftest.py": mark("conftest.py")})
    return marks, manifest_of(tmp_path, files)[1]


def test_nothing_of_the_project_starts_on_the_host_without_an_engine_nor_when_the_answer_is_read(tmp_path, monkeypatch):
    marks, manifest = marked_project(tmp_path, monkeypatch)
    started = spied(monkeypatch)
    monkeypatch.setattr(container, "run_in_container", lambda *args, **kwargs: {"state": "gap", "cause": "no engine", "remedy": "start one"})
    record = premap.write(manifest, sources=SOURCES, runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record
    nothing_started(started, marks)  # Daodan's own git only, with the hooks and the monitor off; no tool, no file of the project
    started.clear()
    premap.write(manifest, sources=SOURCES, runner=lambda commands: [recorded("routes") for _ in commands])  # an answer in hand: reading it starts nothing
    nothing_started(started, marks)


@pytest.mark.parametrize("how", ["os.system", "subprocess.run", "subprocess.Popen"])
def test_the_check_catches_a_source_that_starts_the_command_on_the_host(tmp_path, monkeypatch, how):
    """The mutation, in memory, three ways: a source that runs the script here. The check above must fail for each."""
    import subprocess
    marks, manifest = marked_project(tmp_path, monkeypatch)
    started = spied(monkeypatch)
    real = flask_app.commands
    command = ["python", "-I", "flask_routes.py"]

    def mutated(context):
        try:
            {"os.system": lambda: os.system(" ".join(command)), "subprocess.run": lambda: subprocess.run(command),
             "subprocess.Popen": lambda: subprocess.Popen(command)}[how]()
        except OSError:  # the spy refuses to start it, after recording it
            pass
        return real(context)
    monkeypatch.setattr(flask_app, "commands", mutated)
    monkeypatch.setattr(container, "run_in_container", lambda *args, **kwargs: {"state": "gap", "cause": "no engine", "remedy": "start one"})
    premap.write(manifest, sources=SOURCES, runner=container_runner.runner(manifest))
    with pytest.raises(AssertionError):
        nothing_started(started, marks)
