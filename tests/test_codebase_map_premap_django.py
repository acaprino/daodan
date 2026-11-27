"""The routes a Django project declares, `premap/django_app.py`: the commands it gives, and the rows and the gaps `read` makes from what
Daodan's script (`premap/django_routes.py`, run in the container by the project's own Python) prints.

The answers are real ones: `benchmarks/django-routes/modal_probe.py` runs the script on Modal, in the runner's image with the network
blocked, over the fixture (`benchmarks/django-routes/fixture/`, Django 6.1.3), over copies of it that do not load and over projects of other
layouts (`benchmarks/django-routes/layouts/`), and records what the container runner would return
(`tests/fixtures/premap/django/<variant>.json`, with the print of the script and the `VERSION` of the source in `script.json`). A few
tests build an answer in line where the shape under test is Daodan's own check of the layout or a case no project of the fixture makes;
each says so.

The wiring a source needs in files this change does not own is injected here, the same dicts the report of task 14b gives for them:
`container_runner.TOOLS["django"]`, `entries.QUERIES["django"]`, `premap.FRAMEWORK_SOURCES`. Each test that waits for the wiring to be
in the tree uses `wired`.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from test_codebase_map_container_runner import bound, container, container_runner, manifest_of, premap, recorder
from test_codebase_map_premap_sveltekit import nothing_started, spied

import entries  # noqa: E402
from premap import django_app  # noqa: E402

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/django-routes"
FIXTURE = BENCHMARK / "fixture"
LAYOUTS = BENCHMARK / "layouts"
RECORDED = Path(__file__).parent / "fixtures/premap/django"
SOURCE = f"django@{django_app.VERSION}"
SOURCES = (premap.module_graph, premap.requirements, django_app)  # the facts `django_app.commands` reads are those two sources'

# the entry the wiring adds to `container_runner.TOOLS` (the same dict as in the report of task 14b)
TOOL = {"files": [(None, None, "django_routes.py")], "setup": [f"cp {container_runner.IN}/django_routes.py {container_runner.T}/django_routes.py"],
        "registries": True, "restores": "python", "memory": 3}
QUERY = {"route": {"kind": "rotta"}}  # the table the wiring adds to `entry-queries.json`


@pytest.fixture(autouse=True)
def wired(monkeypatch):
    """What the wiring of the source adds in the files of the pre-map that are not this change's: the runner's entry, the table of the entry
    queries and the registry of the sources whose rows are entries."""
    import entries
    monkeypatch.setitem(container_runner.TOOLS, "django", TOOL)
    monkeypatch.setitem(entries.QUERIES, "django", QUERY)
    if django_app not in premap.FRAMEWORK_SOURCES:  # once the wiring is in the tree it is there already
        monkeypatch.setattr(premap, "FRAMEWORK_SOURCES", (*premap.FRAMEWORK_SOURCES, django_app))


def project(folder: Path = FIXTURE, **changes) -> dict[str, str]:
    files = {path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
             for path in folder.rglob("*") if path.is_file() and "__pycache__" not in path.parts}
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def printed(routes, **fields):
    """An answer built in line: what the script prints, and nothing else, on the standard output."""
    return {"returncode": 0, "stdout": json.dumps({"called": True, "routes": routes, "unread": [], "locale": None, **fields}), "stderr": "", "root": "/work"}


def commands_of(tmp_path, files, sources=SOURCES):
    _, manifest = manifest_of(tmp_path, files)
    asked = []
    premap.write(manifest, sources=sources, runner=lambda commands: asked.extend(commands) or [printed([]) for _ in commands])
    return asked


# ----------------------------------------- the Python the command runs, and the folder it runs in: `manage.py`, from the snapshot

def test_a_project_with_manage_py_beside_its_manifest_runs_the_script_in_the_environment_of_that_folder(tmp_path):
    import preparation
    [command] = commands_of(tmp_path, project())
    assert command["cwd"] == "." and command["venv"] == "." and command["tool"] == "django" and command["network"] == "none"
    assert command["argv"][:2] == ["sh", "-c"] and command["argv"][3:] == ["django", "900", f"{preparation.T}/django_routes.py"]
    assert f'exec timeout --kill-after=10 "$1" {preparation.VENVS}/./bin/python -I "$2"' == command["argv"][2]


def test_the_folder_of_manage_py_is_where_the_command_runs_and_the_manifest_may_be_above_it(tmp_path):
    [command] = commands_of(tmp_path, project(LAYOUTS / "subfolder"))  # `requirements.txt` at the root, `src/manage.py`
    assert command["cwd"] == "src" and command["venv"] == "."


def test_two_projects_with_their_own_manifests_are_two_commands_each_in_its_own_environment_and_sharing_the_time(tmp_path):
    import preparation
    found = commands_of(tmp_path, project(LAYOUTS / "two-projects"))
    assert [(c["cwd"], c["venv"]) for c in found] == [("a", "a"), ("b", "b")]
    assert all(c["argv"][3:] == ["django", "450", f"{preparation.T}/django_routes.py"] for c in found)
    assert f"{preparation.VENVS}/a/bin/python" in found[0]["argv"][2] and f"{preparation.VENVS}/b/bin/python" in found[1]["argv"][2]


def test_a_manifest_without_manage_py_runs_nothing_and_a_manage_py_nobody_declares_django_for_neither(tmp_path):
    for files in (project(LAYOUTS / "no-manage"), {"manage.py": "x = 1\n", "requirements.txt": "flask==3.1.3\n"}):
        _, manifest = manifest_of(tmp_path / str(len(files)), files)
        record = premap.write(manifest, sources=SOURCES, runner=lambda commands: 1 / 0)
        assert [s["state"] for s in record["sources"] if s["source"].startswith("django")] == ["not_needed"]


def test_django_declared_only_in_a_pyproject_runs_there_and_a_requirements_file_that_is_not_a_manifest_names_no_folder(tmp_path):
    files = {"api/pyproject.toml": "[project]\nname='a'\nversion='1'\ndependencies=['Django>=5']\n", "api/manage.py": "x = 1\n",
             "docs/requirements/base.txt": "django\n", "docs/manage.py": "x = 1\n"}
    assert [c["cwd"] for c in commands_of(tmp_path, files)] == ["api"]
    assert commands_of(tmp_path / "no-module-graph", files, sources=(premap.requirements, django_app)) == []  # `requirements` alone does not read it


def test_a_poetry_project_asks_poetry_for_its_environment(tmp_path):
    files = {"pyproject.toml": "[project]\nname='r'\nversion='1'\ndependencies=['django>=5']\n", "poetry.lock": "", "manage.py": "x = 1\n"}
    [command] = commands_of(tmp_path, files)
    assert '"$(cd /work/. && poetry env info -e)"' in command["argv"][2] and "venvs" not in command["argv"][2]


def test_the_folders_share_the_time_and_none_has_less_than_ten_seconds():
    assert [django_app.run_seconds(n) for n in (1, 3, 90, 200)] == [900, 300, 10, 10]


# ----------------------------------------------------------------------- helpers over the answers

def recorded(name: str) -> dict:
    """The answer the probe recorded for a variant, as the container runner returns it."""
    return {**json.loads((RECORDED / f"{name}.json").read_text(encoding="utf-8")), "root": "/work"}


def view(file, qualname, line=None, **more):
    """A handler as the script prints it, for an answer built in line."""
    return {"kind": "function", "type": "builtins.function", "module": file.removesuffix(".py").replace("/", "."), "qualname": qualname,
            "file": file, "line": line, "environment": False, "distribution": None, "owners": [], **more}


def route(path, handler, method=None, **more):
    """A route as the script prints it, for an answer built in line."""
    return {"path": path, "parts": [[False, path]], "arguments": {}, "view": None, "handlers": [{"method": method, "handler": handler}], **more}


def routes_of(answer) -> dict:
    return {r["path"]: r for r in django_app._printed(answer)["routes"]}


def read(tmp_path, files, answers, sources=(premap.requirements, django_app)):
    _, manifest = manifest_of(tmp_path, files)
    asked = []

    def run(commands):
        asked.extend(commands)
        return answers
    record = premap.write(manifest, sources=sources, runner=run)
    # the rows as the links bind them (`binder.bind`): the source gives a name at a position, the binder ties it to the function
    record = {**record, "framework_entries": bound(manifest, record)} if "framework_entries" in record else record
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], asked


def line_of(files, file, needle, after=None):
    """The line of `file` that holds `needle`, the first one below the line that holds `after` when it is given."""
    lines = files[file].split("\n")
    start = next(n for n, line in enumerate(lines) if after in line) if after else 0
    return next(n for n, line in enumerate(lines[start:], start + 1) if needle in line)


def rows(record):
    return [r for r in record.get("framework_entries", []) if r["reader"] == "django"]


def fixture_rows(tmp_path):
    files = project()
    record, gaps, asked = read(tmp_path, files, [recorded("routes")])
    return files, record, gaps, asked


def by_key(record):
    return {(r["path"], r.get("method")): r for r in rows(record)}


# ----------------------------------------------------------------------- the recorded answer of the fixture

FIXTURE_ROUTES = {
    "/shop/", "/shop/products/", "/shop/products/<int:pk>/", "/shop/generic/", "/shop/decorated/", "/shop/mixed/", "/shop/own-head/", "/shop/cart/", "/shop/lambda/",
    "/api/items/", "/api/items/<int:pk>/", "/about/", "/go/", "/blog/<int:year>/<slug:slug>/", "/files/<path:rest>", "/assets/<path:name>",
    "/regex-class/$", "/year/<yyyy:year>/", "/pair/<pair:p>/", "/token/<uuid:token>/", "/<str:tenant>/dash/", "/<str:tenant>/dash/report/<int:n>/",
    "/legacy/(?P<year>[0-9]{4})/$", "/optional/(?:(?P<n>[0-9]+)/)?$", "/(alpha|beta)/$", "/partial/", "/plain-wrapper/", "/lambda/", "/async/",
    "/private/", "/en/localized/", "/en/products-i18n/", "/noprefix/"}


def test_the_script_s_answer_is_one_json_document_on_the_standard_output_and_every_route_of_the_loaded_urlconf_is_in_it():
    answer = recorded("routes")
    assert answer["returncode"] == 0 and answer["stderr"] == ""
    document = json.loads(answer["stdout"])  # the whole output, not its last line
    assert document["called"] is True and document["unread"] == []
    paths = set(routes_of(answer))
    assert FIXTURE_ROUTES <= paths and {p for p in paths if p.startswith("/admin/")}  # the admin site's own routes are there too
    assert paths - FIXTURE_ROUTES == {p for p in paths if p.startswith("/admin/")}


def test_each_route_and_method_is_a_row_on_the_function_that_answers_it_at_the_line_of_its_def_with_the_route_as_django_writes_it(tmp_path):
    files, record, gaps, asked = fixture_rows(tmp_path)
    found = by_key(record)
    products, pages, mixins = "shop/views/products.py", "shop/views/pages.py", "shop/mixins.py"
    where = {  # (path, method) -> (file, qualified name, the line `def` is on, the line to look below)
        ("/shop/", None): (pages, "home", "def home(", None),
        ("/shop/products/", "GET"): (products, "ProductList.get", "def get(", "class ProductList"),
        ("/shop/products/", "POST"): (products, "ProductList.post", "def post(", "class ProductList"),
        ("/shop/products/<int:pk>/", "GET"): (products, "ProductDetail.get", "def get(", "class ProductDetail"),
        ("/shop/mixed/", "GET"): (mixins, "AuditMixin.get", "def get(", "class AuditMixin"),  # the mixin's file, not the view's
        ("/shop/mixed/", "POST"): (products, "Mixed.post", "def post(", "class Mixed"),
        ("/shop/own-head/", "GET"): (products, "OwnHead.get", "def get(", "class OwnHead"),
        ("/shop/own-head/", "HEAD"): (products, "OwnHead.head", "def head(", "class OwnHead"),
        ("/shop/own-head/", "OPTIONS"): (products, "OwnHead.options", "def options(", "class OwnHead"),
        ("/shop/cart/", None): (pages, "cart", "def cart(", None),  # `require_http_methods` above it: the function, not the decorator
        ("/api/items/", "GET"): (products, "ProductList.get", "def get(", "class ProductList"),
        ("/api/items/", "POST"): (products, "ProductList.post", "def post(", "class ProductList"),
        ("/api/items/<int:pk>/", "GET"): (products, "ProductDetail.get", "def get(", "class ProductDetail"),
        ("/assets/<path:name>", "GET"): (products, "Assets.get", "def get(", "class Assets"),
        ("/regex-class/$", "GET"): (products, "ProductList.get", "def get(", "class ProductList"),
        ("/blog/<int:year>/<slug:slug>/", None): (pages, "post", "def post(", None),
        ("/files/<path:rest>", None): (pages, "serve_file", "def serve_file(", None),
        ("/<str:tenant>/dash/", None): (pages, "home", "def home(", None),
        ("/<str:tenant>/dash/report/<int:n>/", None): (pages, "report", "def report(", None),
        ("/legacy/(?P<year>[0-9]{4})/$", None): (pages, "archive", "def archive(", None),
        ("/partial/", None): (pages, "generic", "def generic(", None),  # a `functools.partial`: Django's own `lookup_str` takes its `func`
        ("/async/", None): (pages, "fast", "def fast(", None),  # `async def`, under `require_GET`
        ("/private/", None): (pages, "private", "def private(", None),  # `csrf_exempt` over `login_required`: two wrappers
        ("/en/products-i18n/", "POST"): (products, "ProductList.post", "def post(", "class ProductList"),
        ("/noprefix/", None): (pages, "home", "def home(", None),
        # a wrapper made without `functools.wraps` is the function Django runs: the row is on the wrapper
        ("/plain-wrapper/", None): ("config/urls.py", "without_wraps.wrapper", "def wrapper(", None)}
    assert set(where) <= set(found)
    for key, (file, qualified, needle, below) in where.items():
        row = found[key]
        assert row["shape"] == "route" and row["kind"] == "rotta" and row["sources"] == [SOURCE] and row["reader"] == "django" and not row.get("gap"), key
        assert row["symbol"] == f"{file}::{qualified}" and row["handler"] == qualified.rsplit(".", 1)[-1] and row["handler_source"] == "django", key
        assert row["site"] == f"{file}:{line_of(files, file, needle, below)}" and (("method" in row) == (key[1] is not None)), key
    assert [(c["cwd"], c["network"], c["env"]) for c in asked] == [(".", "none", {})]


def test_a_function_view_declares_no_method_and_its_row_has_none_and_a_class_based_view_has_a_row_for_each_method_its_class_answers(tmp_path):
    """Django has no method per route. `require_http_methods` keeps its list in a closure (read from Django 6.1.3's `decorators/http.py`: no
    attribute), so a function view is one handler with no method; a class-based view is read as `View.dispatch` reads it, each name of
    `http_method_names` the class has: `options` is dropped where it is Django's own (every `View` has one) and `head` where it is `get`'s."""
    by_path = routes_of(recorded("routes"))
    assert [a["method"] for a in by_path["/shop/cart/"]["handlers"]] == [None]
    assert [a["method"] for a in by_path["/shop/products/"]["handlers"]] == ["GET", "POST"]
    assert [a["method"] for a in by_path["/shop/products/<int:pk>/"]["handlers"]] == ["GET"]  # no `OPTIONS` of `View`, no `HEAD` of `setup`
    assert [a["method"] for a in by_path["/shop/own-head/"]["handlers"]] == ["GET", "HEAD", "OPTIONS"]  # declared by the class: they stay
    assert by_path["/shop/products/"]["view"]["qualname"] == "ProductList" and by_path["/shop/cart/"]["view"] is None


def test_a_method_answered_by_the_framework_is_a_row_on_the_projects_class_with_the_gap_that_says_so(tmp_path):
    files, record, gaps, _ = fixture_rows(tmp_path)
    [generic] = [r for r in rows(record) if r["path"] == "/shop/generic/"]
    products = "shop/views/products.py"
    assert generic["method"] == "GET" and generic["symbol"] == f"{products}::<module>" and "handler" not in generic
    assert generic["site"] == f"{products}:{line_of(files, products, 'class ProductGeneric')}"
    assert "ProductGeneric is a class-based view and GET is answered by BaseListView.get of Django, not by a function of the project" in generic["gap"]


def test_a_decorated_class_is_at_the_line_of_its_class_statement_and_not_of_its_first_decorator(tmp_path):
    """`inspect.getsourcelines` of a decorated class starts at its first decorator; the script takes the line of the `class` from the
    interpreter's own parse of the module (`ast`), as it does for a `def`: Noir cites the `class` line, and the two are compared by position."""
    files, record, _, _ = fixture_rows(tmp_path)
    products = "shop/views/products.py"
    [row] = [r for r in rows(record) if r["path"] == "/shop/decorated/"]
    wanted = line_of(files, products, "class DecoratedGeneric")
    assert wanted > line_of(files, products, "@method_decorator") and row["site"] == f"{products}:{wanted}"
    assert "DecoratedGeneric is a class-based view and GET is answered by BaseListView.get of Django" in row["gap"]
    assert routes_of(recorded("routes"))["/shop/decorated/"]["view"]["line"] == wanted


def test_a_view_that_is_a_frameworks_own_class_used_as_it_is_or_a_framework_function_is_counted_in_one_gap_of_the_folder_by_distribution(tmp_path):
    """`TemplateView.as_view(template_name=...)`, `RedirectView`, `admin.site.urls`: Django registers no route of its own (no rule like
    Flask's `static`), so each is a route the project mounts whose answer is not in the snapshot: one `model_partial` gap, by distribution."""
    by_path = routes_of(recorded("routes"))
    admin = [path for path in by_path if path.startswith("/admin/")]
    assert by_path["/about/"]["handlers"][0]["handler"]["environment"] is True and by_path["/about/"]["handlers"][0]["handler"]["owners"] == ["Django"]
    _, record, gaps, _ = fixture_rows(tmp_path)
    [partial] = [g for g in gaps if g["kind"] == "model_partial" and "packages of the restored environment" in g["detail"]]
    assert partial["path"] == "." and f"{len(admin) + 2} routes of the URLconf are views of packages of the restored environment" in partial["detail"]
    assert f"Django ({len(admin) + 2}: /admin/, /admin/login/, /admin/logout/ and {len(admin) + 2 - django_app.LISTED} more)" in partial["detail"]
    assert not [r for r in rows(record) if r["path"] in ("/about/", "/go/") or r["path"].startswith("/admin/")]


# ------------------------------------------------------------------- the path schema, from django's own parts of the route

def test_the_script_prints_the_parts_of_a_path_route_from_djangos_own_normalize_and_the_converter_of_every_level():
    """`normalize` (`django.utils.regex_helper`, the function `reverse()` uses) turns the compiled regular expression of the levels composed as
    `URLResolver._populate` composes them into a form with a hole for each argument; the converters are `RoutePattern.converters` of every level,
    the prefix's too (`<str:tenant>/dash/`)."""
    by_path = routes_of(recorded("routes"))
    assert by_path["/shop/products/<int:pk>/"]["parts"] == [[False, "/shop/products/"], [True, "pk"], [False, "/"]]
    assert by_path["/<str:tenant>/dash/report/<int:n>/"]["parts"] == [[False, "/"], [True, "tenant"], [False, "/dash/report/"], [True, "n"], [False, "/"]]
    assert by_path["/<str:tenant>/dash/report/<int:n>/"]["arguments"] == {"tenant": True, "n": True}  # `tenant` is the include's, `n` the pattern's
    assert by_path["/shop/"]["parts"] == [[False, "/shop/"]] and by_path["/shop/"]["arguments"] == {}
    assert by_path["/blog/<int:year>/<slug:slug>/"]["arguments"] == {"year": True, "slug": True}


def test_only_djangos_own_converters_that_cannot_hold_a_slash_are_one_segment_and_a_converter_of_the_project_proves_nothing():
    """Django has no `part_isolating`: the question is put to Django itself, a `RoutePattern` of one argument of the converter and its `match`
    of a path of two segments (the method the resolver matches a route with). `path` accepts it and so does `Pair` (a `/` in its own pattern):
    False; `int`, `str`, `slug` and `uuid` are Django's own and do not: True; `FourDigits` (`[0-9]{4}`) may be one segment and nothing says so:
    None."""
    by_path = routes_of(recorded("routes"))
    assert by_path["/files/<path:rest>"]["arguments"] == {"rest": False} and by_path["/assets/<path:name>"]["arguments"] == {"name": False}
    assert by_path["/pair/<pair:p>/"]["arguments"] == {"p": False}
    assert by_path["/year/<yyyy:year>/"]["arguments"] == {"year": None}
    assert by_path["/shop/products/<int:pk>/"]["arguments"] == {"pk": True} and by_path["/<str:tenant>/dash/"]["arguments"] == {"tenant": True}
    assert by_path["/blog/<int:year>/<slug:slug>/"]["arguments"] == {"year": True, "slug": True}
    assert by_path["/token/<uuid:token>/"]["arguments"] == {"token": True}


SCHEMAS = {  # the path as `flows.path_schema` reads it: what Noir's `/admin/users/:user_id` is, `/admin/users/{}`
    "/shop/": "/shop", "/shop/products/": "/shop/products", "/shop/products/<int:pk>/": "/shop/products/{}", "/api/items/<int:pk>/": "/api/items/{}",
    "/blog/<int:year>/<slug:slug>/": "/blog/{}/{}", "/<str:tenant>/dash/": "/{}/dash", "/<str:tenant>/dash/report/<int:n>/": "/{}/dash/report/{}",
    "/plain-wrapper/": "/plain-wrapper", "/token/<uuid:token>/": "/token/{}", "/noprefix/": None,  # under `i18n_patterns` the prefix depends on the language: no single schema
    "/files/<path:rest>": None, "/assets/<path:name>": None, "/pair/<pair:p>/": None, "/year/<yyyy:year>/": None,  # an argument that may hold a `/`, or is the project's
    "/legacy/(?P<year>[0-9]{4})/$": None, "/optional/(?:(?P<n>[0-9]+)/)?$": None, "/(alpha|beta)/$": None, "/regex-class/$": None,  # `re_path`
    "/en/localized/": None, "/en/products-i18n/": None}


def test_a_route_row_has_the_path_schema_of_its_arguments_and_none_where_django_gives_no_single_one(tmp_path):
    import flows
    _, record, _, _ = fixture_rows(tmp_path)
    mine = [r for r in rows(record) if r["path"] in SCHEMAS]
    assert {r["path"] for r in mine} == set(SCHEMAS)
    assert {r["path"]: r["schema"] for r in mine} == SCHEMAS and all("schema" in r for r in mine)
    assert next(r for r in mine if r["path"] == "/shop/products/<int:pk>/")["schema"] == flows.path_schema("/shop/products/:pk/")  # Noir's spelling


def test_the_schema_comes_from_djangos_parts_not_from_the_text_of_the_route(tmp_path):
    """A route whose `parts` or `arguments` Django did not give has no schema (None: a gap of the declared routes), never one made from
    `path`; an argument whose converter is not proved one segment is not taken for one."""
    answer = recorded("routes")
    document = json.loads(answer["stdout"])
    for found in document["routes"]:
        if found["path"] == "/shop/products/<int:pk>/":
            found["parts"] = None
        if found["path"] == "/blog/<int:year>/<slug:slug>/":
            found["arguments"]["year"] = None
        if found["path"] == "/<str:tenant>/dash/report/<int:n>/":
            found["arguments"] = {}  # a converter the script did not give: not taken for one segment
    record, _, _ = read(tmp_path, project(), [{**answer, "stdout": json.dumps(document)}])
    wanted = ("/shop/products/<int:pk>/", "/blog/<int:year>/<slug:slug>/", "/<str:tenant>/dash/report/<int:n>/", "/<str:tenant>/dash/")
    assert {r["path"]: r["schema"] for r in rows(record) if r["path"] in wanted} == {
        "/shop/products/<int:pk>/": None, "/blog/<int:year>/<slug:slug>/": None, "/<str:tenant>/dash/report/<int:n>/": None, "/<str:tenant>/dash/": "/{}/dash"}


def test_a_route_under_i18n_patterns_is_listed_in_the_language_the_project_loaded_in_and_one_gap_says_the_others_are_not(tmp_path):
    document = json.loads(recorded("routes")["stdout"])
    assert document["locale"] == {"active": "en", "others": 1}  # LANGUAGES of the fixture: `en` and `it`
    by_path = routes_of(recorded("routes"))
    assert by_path["/en/localized/"]["parts"] is None and by_path["/noprefix/"]["parts"] is None  # `prefix_default_language=False`: `it` has its own
    _, _, gaps, _ = fixture_rows(tmp_path)
    [gap] = [g for g in gaps if "i18n_patterns" in g["detail"]]
    assert gap["kind"] == "model_partial" and "`en`" in gap["detail"] and "the 1 other languages of LANGUAGES" in gap["detail"]


# ------------------------------------------------------------------- what is not the project's, or not read

def test_a_view_that_is_a_function_of_the_project_outside_the_snapshot_or_no_function_is_a_gap_with_the_route_and_no_row(tmp_path):
    answer = printed([route("/x/", view("../elsewhere/views.py", "index", line=3)), route("/y/", {**view("x.py", None), "file": None, "type": "foo.Counter"})])
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["outside_snapshot", "outside_snapshot"]
    assert gaps[0]["detail"] == "/x/: index has no source file of the project the snapshot holds (../elsewhere/views.py)" and gaps[0]["path"] == "."
    assert gaps[1]["detail"] == "/y/: foo.Counter has no source file of the project the snapshot holds (none)"


def test_a_view_installed_from_a_local_directory_is_a_gap_that_says_it_is_a_copy_of_the_project_and_where_from(tmp_path):
    """PEP 610: `direct_url.json` of the distribution (read with `importlib.metadata`) says it was installed from a directory: the project's
    own code, copied into `site-packages`, which is not the snapshot's file."""
    answer = recorded("routes-installed-copy")
    assert answer["returncode"] == 0, answer["stderr"]
    shared = routes_of(answer)["/shared/view/"]["handlers"][0]["handler"]
    assert shared["environment"] is True and shared["distribution"]["name"] == "sharedlib" and shared["distribution"]["url"].startswith("file:///work/libs/shared")
    record, gaps, _ = read(tmp_path, project(LAYOUTS / "installed-copy"), [answer])
    [gap] = [g for g in gaps if g["detail"].startswith("/shared/view/: ")]
    assert gap["kind"] == "outside_snapshot" and "installed copy of the project, not the snapshot's file" in gap["detail"]
    assert "sharedlib" in gap["detail"] and "file:///work/libs/shared" in gap["detail"]
    assert [r["path"] for r in rows(record) if not r.get("gap")] == ["/own/"]  # the project's own view is a row
    assert not [g for g in gaps if g["kind"] == "model_partial"]


def test_a_handler_the_script_gave_no_line_is_a_row_on_its_file_and_the_binder_says_the_gap(tmp_path):
    record, _, _ = read(tmp_path, project(), [printed([route("/x/", view("shop/views/pages.py", "home", line=None))])])
    [row] = rows(record)
    assert row["site"] == "shop/views/pages.py" and row["symbol"] == "shop/views/pages.py::<module>" and "without a unique snapshot handler" in row["gap"]


def test_a_lambda_is_a_row_on_its_file_with_the_binders_gap_because_the_snapshot_calls_it_by_another_name(tmp_path):
    files, record, _, _ = fixture_rows(tmp_path)
    [lam] = [r for r in rows(record) if r["path"] == "/shop/lambda/"]
    assert lam["site"] == f"shop/urls.py:{line_of(files, 'shop/urls.py', 'lambda request')}" and lam["symbol"] == "shop/urls.py::<module>"
    assert lam["handler"] == "<lambda>" and "without a unique snapshot handler" in lam["gap"]


def test_a_class_based_view_with_no_handler_for_any_method_is_a_row_on_the_class_with_the_gap_and_one_that_is_not_in_the_snapshot_is_a_gap(tmp_path):
    cls = view("shop/views/products.py", "Empty", line=3, kind="class")
    record, gaps, _ = read(tmp_path, project(), [printed([{**route("/e/", None), "view": cls}])])
    [row] = rows(record)
    assert row["site"] == "shop/views/products.py:3" and "Empty is a class-based view with no HTTP method of its own" in row["gap"] and "method" not in row
    other = {**cls, "file": "../elsewhere.py"}
    record, gaps, _ = read(tmp_path / "other", project(), [printed([{**route("/e/", None), "view": other}])])
    assert rows(record) == [] and gaps[0]["kind"] == "outside_snapshot" and gaps[0]["detail"] == "/e/: no function answers it"


# ------------------------------------------------------------------- the includes and the views of the other packages

def test_an_include_whose_urlconf_has_no_patterns_is_a_gap_and_the_routes_beside_it_stay(tmp_path):
    """`include("module")` imports the module where `urls.py` is read, so one that does not import fails the whole URLconf (`broken-include`,
    below); the include that fails later is the one `URLResolver.url_patterns` refuses: a module with no `urlpatterns` (an empty list is accepted: no route, no error)."""
    answer = recorded("no-patterns-include")
    assert answer["returncode"] == 0, answer["stderr"]
    document = json.loads(answer["stdout"])
    assert [u["route"] for u in document["unread"]] == ["/<str:tenant>/dash/"]
    assert document["unread"][0]["error"].startswith("ImproperlyConfigured: The included URLconf") and "does not appear to have any patterns" in document["unread"][0]["error"]
    record, gaps, _ = read(tmp_path, project(), [answer])
    [gap] = [g for g in gaps if "did not load" in g["detail"]]
    assert gap["kind"] == "model_partial" and gap["detail"].startswith("the URLconf included at /<str:tenant>/dash/ did not load, its routes are not read: ImproperlyConfigured: ")
    assert [r for r in rows(record) if r["path"] == "/shop/products/"] and not [r for r in rows(record) if "dash" in r["path"]]


def test_a_project_without_the_admin_has_no_admin_route_and_the_environment_gap_counts_what_is_left(tmp_path):
    paths = set(routes_of(recorded("no-admin")))
    assert not [p for p in paths if p.startswith("/admin/")] and {"/about/", "/go/"} <= paths
    _, gaps, _ = read(tmp_path, project(), [recorded("no-admin")])
    [partial] = [g for g in gaps if "packages of the restored environment" in g["detail"]]
    assert partial["detail"].startswith("2 routes of the URLconf are views of packages of the restored environment, not of the project: Django (2: ")


def test_djangos_static_helper_adds_a_route_of_the_framework_only_when_debug_is_on(tmp_path):
    off, on = routes_of(recorded("routes")), routes_of(recorded("debug-static"))
    assert not [p for p in off if p.startswith("/media/")] and [p for p in on if p.startswith("/media/")] == ["/media/(?P<path>.*)$"]
    assert on["/media/(?P<path>.*)$"]["handlers"][0]["handler"]["environment"] is True and on["/media/(?P<path>.*)$"]["parts"] is None


def test_an_application_with_no_route_is_a_gap_and_no_row(tmp_path):
    record, gaps, _ = read(tmp_path, project(), [printed([], unread=[], locale=None)])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_partial"] and gaps[0]["detail"] == "the URLconf has no route"


# ------------------------------------------------------------------- what the script reports of a project that does not load

@pytest.mark.parametrize("variant, returncode, cause", [
    ("settings-error", 3, "ModuleNotFoundError: No module named 'not_installed'"),  # `manage.py`'s own settings module raises on import
    ("settings-needs-env", 3, "KeyError: 'SECRET_KEY'"),  # a settings module that reads the environment: the container has none of the project's
    ("urls-error", 3, "ModuleNotFoundError: No module named 'not_installed'"),
    ("broken-include", 3, "ModuleNotFoundError: No module named 'not_installed'"),  # `include("shop.dash_urls")` imports it where `urls.py` is read
    ("urls-queries", 3, "OperationalError: no such table: shop_product"),  # a URLconf that queries a database at import
    ("ready-queries", 3, "OperationalError: no such table: shop_product"),  # an app whose `ready()` does
    ("db-postgres-no-driver", 3, "ImproperlyConfigured: Error loading psycopg2 or psycopg module"),  # `django.setup()` loads the backend module
    ("manage-no-call", 4, "ran and did not run the shell command"),
    ("hangs", 124, "did not end in 900 seconds"),
])
def test_a_project_that_does_not_load_or_a_script_that_is_stopped_is_the_folder_s_gap_with_the_cause_and_no_row(tmp_path, variant, returncode, cause):
    answer = recorded(variant)
    assert answer["returncode"] == returncode
    record, gaps, _ = read(tmp_path, project(), [answer])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and cause in gaps[0]["detail"] and gaps[0]["path"] == "."
    assert "restored for '.'" in gaps[0]["detail"]


def test_a_killed_script_or_a_line_that_is_not_the_known_layout_is_the_folder_s_gap(tmp_path):
    for answer, cause in (({"returncode": 137, "stdout": "", "stderr": ""}, "exit 137"), ({"returncode": 0, "stdout": "not json\n", "stderr": ""}, "printed no JSON"),
                          ({"returncode": 0, "stdout": json.dumps([]), "stderr": ""}, "printed no JSON"),
                          ({"returncode": 0, "stdout": json.dumps({"called": True, "routes": []}), "stderr": ""}, "printed no JSON")):
        record, gaps, _ = read(tmp_path / cause.replace(" ", "-") / str(answer["returncode"]), project(), [{**answer, "root": "/work"}])
        assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and cause in gaps[0]["detail"] and gaps[0]["path"] == "."


# ---------------------------------------- what follows the JSON, what the project prints, and the databases the settings name

@pytest.mark.parametrize("variant", ["thread", "atexit-print", "replaced-stdout", "prints", "db-none", "db-postgres-driver", "routes-django42", "routes-django52"])
def test_nothing_the_project_does_around_the_json_changes_the_answer(tmp_path, variant):
    """A thread that never ends, a print at exit, a replaced `sys.stdout`, a print while the settings load, no database or one whose driver is
    installed and whose server is not there (`django.setup()` opens no connection), and another Django (5.2.19, 4.2.30): the same routes."""
    answer = recorded(variant)
    assert answer["returncode"] == 0, (variant, answer["stderr"])
    assert json.loads(answer["stdout"])["called"] is True
    def seen(document):  # the line of a function of the packages is the version's own: the project's functions are compared by line too
        return {p: [(a["method"], a["handler"]["qualname"], None if a["handler"]["environment"] else a["handler"]["line"]) for a in r["handlers"]]
                for p, r in routes_of(document).items() if p in FIXTURE_ROUTES}
    assert seen(answer) == seen(recorded("routes"))


def test_what_the_project_prints_while_it_loads_never_reaches_the_standard_output_which_is_the_json_alone():
    """Descriptor 1 is the standard error while the project's code runs: the print of the settings and the one at exit never reach the output."""
    for variant in ("prints", "atexit-print"):
        answer = recorded(variant)
        assert answer["returncode"] == 0 and "settings loaded" not in answer["stdout"] and "goodbye" not in answer["stdout"]
        assert json.loads(answer["stdout"])["called"] is True


# ------------------------------------------------------------------- the layouts, measured on Modal

def test_a_manage_py_in_a_subfolder_gives_the_rows_of_that_folder_on_the_paths_from_the_root(tmp_path):
    answer = recorded("routes-subfolder")
    assert answer["returncode"] == 0, answer["stderr"]
    files = project(LAYOUTS / "subfolder")
    record, gaps, asked = read(tmp_path, files, [answer], sources=SOURCES)
    [row] = rows(record)
    assert row["path"] == "/hello/" and row["site"] == f"src/mysite/urls.py:{line_of(files, 'src/mysite/urls.py', 'def hello(')}"
    assert row["symbol"] == "src/mysite/urls.py::hello" and [c["cwd"] for c in asked] == ["src"] and not [g for g in gaps if g["kind"] == "model_failed"]


def test_two_projects_each_with_its_own_manage_py_are_read_one_by_one(tmp_path):
    files = project(LAYOUTS / "two-projects")
    record, gaps, asked = read(tmp_path, files, [recorded("routes-two-projects-a"), recorded("routes-two-projects-b")], sources=SOURCES)
    assert [c["cwd"] for c in asked] == ["a", "b"]
    assert sorted((r["path"], r["symbol"]) for r in rows(record)) == [("/view_a/", "a/proj/urls.py::view_a"), ("/view_b/", "b/proj/urls.py::view_b")]
    assert not gaps


def test_a_manage_py_that_runs_management_utility_itself_gives_the_same_document_as_one_that_calls_execute_from_command_line(tmp_path):
    """The way `django_routes.py` reaches the settings is `manage.py shell -c`, not a replacement of `execute_from_command_line` (measured: that
    one never gets the call from a launcher like django-configurations', exit 4)."""
    answer = recorded("routes-custom-launcher")
    assert answer["returncode"] == 0, answer["stderr"]
    record, _, _ = read(tmp_path, project(LAYOUTS / "custom-launcher"), [answer], sources=SOURCES)
    assert [(r["path"], r["site"]) for r in rows(record)] == [("/hello/", f"proj/urls.py:{line_of(project(LAYOUTS / 'custom-launcher'), 'proj/urls.py', 'def hello(')}")]


def test_a_django_rest_framework_viewset_is_read_as_its_own_as_view_maps_it_each_method_to_the_function_of_the_class_that_answers(tmp_path):
    """`ViewSetMixin.as_view` sets `cls` and `actions` (HTTP method to the name of a method of the class) on the view: the handler of each is
    `getattr(cls, name)`. The project's `list` is a row; `create`, `retrieve` and the others are DRF's own (`CreateModelMixin.create`): rows on the
    class with the gap. A router's patterns are `re_path`s (`^items/(?P<pk>[^/.]+)/$`): no schema."""
    answer = recorded("routes-drf")
    assert answer["returncode"] == 0, answer["stderr"]
    files = project(LAYOUTS / "drf")
    record, gaps, _ = read(tmp_path, files, [answer], sources=SOURCES)
    found = {(r["path"], r.get("method")): r for r in rows(record)}
    listed = found[("/v1/items/$", "GET")]
    assert listed["symbol"] == "api/views.py::ItemViewSet.list" and listed["site"] == f"api/views.py:{line_of(files, 'api/views.py', 'def list(')}" and listed["schema"] is None
    assert found[("/v1/items/(?P<pk>[^/.]+)/publish/$", "POST")]["symbol"] == "api/views.py::ItemViewSet.publish"
    assert found[("/ping/", "GET")]["symbol"] == "api/views.py::Ping.get" and found[("/ping/", "POST")]["symbol"] == "api/views.py::Ping.post"
    created = found[("/v1/items/$", "POST")]
    assert "ItemViewSet is a class-based view and POST is answered by CreateModelMixin.create of djangorestframework" in created["gap"]
    assert created["site"] == f"api/views.py:{line_of(files, 'api/views.py', 'class ItemViewSet')}"


# ------------------------------------------------------- what the script prints is checked as `read` uses it

MALFORMED = [
    ("a path that is not text", lambda r: r.update(path=1)),
    ("a part that is not a pair", lambda r: r.update(parts=[[False]])),
    ("a part whose flag is not a boolean", lambda r: r.update(parts=[["x", "/"]])),
    ("arguments that are not a mapping", lambda r: r.update(arguments=["a"])),
    ("an argument whose isolation is not a boolean", lambda r: r.update(arguments={"a": "yes"})),
    ("handlers that are not a list", lambda r: r.update(handlers="GET")),
    ("no handler at all", lambda r: r.update(handlers=[])),
    ("a method that is not text", lambda r: r["handlers"][0].update(method=1)),
    ("a file that is not text", lambda r: r["handlers"][0]["handler"].update(file=5)),
    ("a qualified name that is not text", lambda r: r["handlers"][0]["handler"].update(qualname=5)),
    ("a line that is not a number", lambda r: r["handlers"][0]["handler"].update(line="7")),
    ("an environment flag that is not a boolean", lambda r: r["handlers"][0]["handler"].update(environment="yes")),
    ("owners that are not a list", lambda r: r["handlers"][0]["handler"].update(owners="Django")),
    ("a distribution that is not a mapping", lambda r: r["handlers"][0]["handler"].update(distribution="x")),
    ("a kind that is neither a function nor a class", lambda r: r["handlers"][0]["handler"].update(kind="method")),
    ("a view that is a function", lambda r: r.update(view=view("shop/views/pages.py", "home", line=1)))]


@pytest.mark.parametrize("what, spoil", MALFORMED, ids=[what for what, _ in MALFORMED])
def test_a_value_of_the_answer_that_read_would_use_and_is_malformed_is_that_folder_s_gap_and_the_other_folders_keep_their_rows(tmp_path, what, spoil):
    """Inline answers: two folders, the first spoiled in one value. The check of the layout is whole, so `read` never raises in the middle of a
    folder and loses the rows of the ones before and after it."""
    files = {"api/requirements.txt": "django==6.1.3\n", "api/manage.py": "x = 1\n", "api/views.py": "def x():\n    return 'x'\n",
             "worker/requirements.txt": "django==6.1.3\n", "worker/manage.py": "x = 1\n", "worker/views.py": "def y():\n    return 'y'\n"}
    api = route("/x/", view("views.py", "x", line=1))
    spoil(api)
    answers = [printed([api], unread=[], locale=None), printed([route("/y/", view("views.py", "y", line=1))], unread=[], locale=None)]
    record, gaps, _ = read(tmp_path, files, answers)
    assert [g["kind"] for g in gaps] == ["model_failed"] and gaps[0]["path"] == "api" and "known layout" in gaps[0]["detail"], what
    assert [(r["path"], r["site"]) for r in rows(record)] == [("/y/", "worker/views.py:1")]


@pytest.mark.parametrize("spoil", [lambda d: d.update(unread="x"), lambda d: d.update(unread=[{"route": 1, "error": "e"}]),
                                   lambda d: d.update(locale="en"), lambda d: d.update(locale={"active": "en", "others": "1"}), lambda d: d.pop("locale")])
def test_the_unread_includes_and_the_locale_are_checked_too(tmp_path, spoil):
    document = {"called": True, "routes": [], "unread": [], "locale": None}
    spoil(document)
    record, gaps, _ = read(tmp_path, project(), [{"returncode": 0, "stdout": json.dumps(document), "stderr": "", "root": "/work"}])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and "known layout" in gaps[0]["detail"]


def test_several_folders_each_with_rows_are_read_one_by_one_and_a_folder_that_fails_does_not_take_the_others(tmp_path):
    files = {f"{name}/{rel}": text for name in ("api", "tools", "worker")
             for rel, text in (("requirements.txt", "django==6.1.3\n"), ("manage.py", "x = 1\n"), ("views.py", "def v():\n    return 1\n"))}
    answers = [printed([route("/x/", view("views.py", "v", line=1))], unread=[], locale=None),  # api
               {"returncode": 3, "stdout": "", "stderr": "ModuleNotFoundError: No module named 'x'\n", "root": "/work"},  # tools
               printed([route("/z/", view("views.py", "v", line=1), method="GET")], unread=[], locale=None)]  # worker
    record, gaps, asked = read(tmp_path, files, answers)
    assert [c["cwd"] for c in asked] == ["api", "tools", "worker"]
    assert sorted((r["path"], r.get("method"), r["site"]) for r in rows(record)) == [("/x/", None, "api/views.py:1"), ("/z/", "GET", "worker/views.py:1")]
    assert [(g["kind"], g["path"]) for g in gaps] == [("model_failed", "tools")]


def test_the_rows_and_the_gaps_a_source_persisted_are_the_ones_from_record_gives_back(tmp_path):
    _, record, gaps, _ = fixture_rows(tmp_path)
    back_rows, back_gaps = django_app.from_record(record)
    assert back_rows == rows(record) and back_gaps == gaps and back_rows


# ---------------------------------------------------------------- what is persisted, and where the script runs

def test_the_recorded_answers_carry_the_print_of_the_script_that_made_them_and_the_version_of_the_source_they_were_made_for():
    """A pre-map is fresh while its source's `NAME@VERSION` is the one it was made by (`premap.state`): a script that changes with no new
    `VERSION` leaves stale rows in a project's pre-map. The recording holds both: changing the script fails here until it is recorded again,
    and the record is made with the `VERSION` the source has then: raise it with the script."""
    script = container_runner.SCRIPTS / "django_routes.py"
    printed_digest = hashlib.sha256(script.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert json.loads((RECORDED / "script.json").read_text(encoding="utf-8")) == {"django_routes.py": printed_digest, "version": django_app.VERSION}, (
        "the script or the version changed: record the answers again (`benchmarks/django-routes/modal_probe.py --mode record`)")


def test_the_runner_restores_the_python_environment_of_each_folder_and_the_script_is_unpacked_beside_the_tools(tmp_path):
    import preparation
    spec = container_runner.TOOLS["django"]
    assert spec["restores"] == "python" and spec["registries"] and spec["memory"] == container_runner.TOOLS["next"]["memory"]
    assert "django_routes.py" in {name for _, _, name in spec["files"]} and f"{preparation.T}/django_routes.py" in spec["setup"][0]
    (tmp_path / "p").mkdir()
    (tmp_path / "p/requirements.txt").write_text("django==6.1.3\n", encoding="utf-8")
    restored = container_runner._python(tmp_path / "p")
    assert len(restored["lines"]) == 2 and any("for f in '.'" in line and "uv venv" in line for line in restored["lines"])
    first, files, _, _ = container_runner.plan("django", [], [], restored["lines"], restored["needs"])
    assert first["network"] == "registries" and [name for _, _, name in files][0] == "django_routes.py"


WIRED = {"tool": container_runner.TOOLS.get("django"), "queries": entries.QUERIES.get("django"),
         "framework": django_app in premap.FRAMEWORK_SOURCES, "sources": django_app in premap.SOURCES}  # what the tree has before `wired` adds it


def test_the_wiring_in_the_tree_is_what_the_report_of_task_14b_gives():
    """Waits for the lines of the report in `container_runner.py`, `entry-queries.json` and `premap/__init__.py`: skipped until they are there."""
    if not any(WIRED.values()):
        pytest.skip("the wiring of the source is not in the tree yet: `container_runner.TOOLS['django']`, `entry-queries.json`, `premap.SOURCES` and `FRAMEWORK_SOURCES`")
    assert WIRED["tool"] == TOOL and WIRED["queries"] == QUERY and WIRED["framework"] and WIRED["sources"]
    assert premap.SOURCES.index(django_app) < premap.SOURCES.index(premap.angular)  # after the other frameworks' sources


def test_the_source_opens_no_store_and_borrows_nothing_from_another_framework_s_source():
    import ast
    tree = ast.parse(Path(django_app.__file__).read_text(encoding="utf-8"))
    named = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "semantic_store" not in named and not {"starts", "exported_target"} & attributes
    others = {"nextjs", "react_router", "nuxt", "sveltekit", "flask_app", "angular", "astro", "fastapi_app"}
    assert not others & named and not {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
                                       and isinstance(node.value, ast.Name) and node.value.id in others}
    assert not {node.name for node in tree.body if isinstance(node, ast.FunctionDef)} & {"_folders", "_folder", "_excerpt"}


def test_no_engine_carries_the_reason_as_the_source_s_gap_and_nothing_of_the_project_runs_here(tmp_path):
    _, manifest = manifest_of(tmp_path, project())
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        record = premap.write(manifest, sources=(premap.module_graph, premap.requirements, django_app), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record


# ------------------------------------------- the project's code never runs on the host (AGENTS.md, «Regola invalicabile»)

def marked_project(tmp_path, monkeypatch):
    """A project that declares Django and holds all a load of it would start, each file leaving its own mark in `marks/` if it runs on this
    machine: `manage.py`, the settings, the URLconf, an app's `ready()`, `sitecustomize.py` and a `conftest.py`; and, first on the PATH, a
    stand-in for each program that would start it (python, python3, uv, poetry, timeout, django-admin) that writes a mark too."""
    marks, tools = tmp_path / "marks", tmp_path / "bin"
    marks.mkdir()
    tools.mkdir()

    def mark(name):
        return f"import pathlib\npathlib.Path({json.dumps((marks / name).as_posix())}).write_text('ran')\n"
    for name in ("python", "python3", "uv", "poetry", "timeout", "django-admin"):
        (tools / name).write_text(f'#!/bin/sh\necho "$0 $*" >> "{marks}/tool-{name}"\n', encoding="utf-8", newline="\n")
        (tools / name).chmod(0o755)
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    files = project(**{"manage.py": mark("manage.py") + "import os\nos.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')\n",
                       "config/settings.py": mark("settings"), "config/urls.py": mark("urls"), "shop/apps.py": mark("apps"),
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
    real = django_app.commands
    command = ["python", "-I", "django_routes.py"]

    def mutated(context):
        try:
            {"os.system": lambda: os.system(" ".join(command)), "subprocess.run": lambda: subprocess.run(command),
             "subprocess.Popen": lambda: subprocess.Popen(command)}[how]()
        except OSError:  # the spy refuses to start it, after recording it
            pass
        return real(context)
    monkeypatch.setattr(django_app, "commands", mutated)
    monkeypatch.setattr(container, "run_in_container", lambda *args, **kwargs: {"state": "gap", "cause": "no engine", "remedy": "start one"})
    premap.write(manifest, sources=SOURCES, runner=container_runner.runner(manifest))
    with pytest.raises(AssertionError):
        nothing_started(started, marks)
