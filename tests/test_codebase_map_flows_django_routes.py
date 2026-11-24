"""The routes of a Django project are offered routes (`flows.link_facts`) as Noir's, Next.js's and Flask's are: a call of the client meets them.

The Django rows are the ones `premap/django_app.py` makes from the answer recorded on Modal (`tests/fixtures/premap/django/routes.json`) over the
fixture of `benchmarks/django-routes/`. Each carries the path schema `django_app` makes from Django's own parse of the route
(`/shop/products/<int:pk>/` is `/shop/products/{}`), or none where an argument may hold a `/`, the route is a `re_path`, is under
`i18n_patterns` or has a converter of the project's own: that route is a gap of the declared routes and meets no call. Django has no method per
route: a function view has none, and `flows._declared_routes` says so for each (a declared route that has no method), where a class-based view
has one row per method it answers and is offered like any other.

The wiring of the source (`entries.QUERIES["django"]`, `premap.FRAMEWORK_SOURCES`) is the one the report of task 14b gives; the module-scoped
fixture adds it for the run and takes it away.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import entries
import flows
import premap
from premap import django_app
from test_codebase_map_premap_container_runner import manifest_of
from test_codebase_map_premap_django import QUERY, WIRED, project, recorded

RULES = [
    {"written": "apiGet", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "GET", "path": "arg0"}},
    {"written": "apiPost", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "POST", "path": "arg0"}},
]
CLIENT = "\n".join([
    "declare function apiGet(url: string): void;",
    "declare function apiPost(url: string): void;",
    "export function viewProduct() { apiGet('/shop/products/7/'); }",  # `ProductDetail.get`, a class-based view: a method of its own
    "export function postProduct() { apiPost('/shop/products/7/'); }",  # the class has no `post`
    "export function listItems() { apiGet('/api/items/'); }",  # the same class under another prefix
    "export function createItem() { apiPost('/api/items/'); }",
    "export function viewBlog() { apiGet('/blog/2020/hello/'); }",  # a function view: no method, so no offered route
    "export function viewTenant() { apiGet('/acme/dash/'); }",  # a function view under an include prefix with an argument
    "export function viewAsset() { apiGet('/assets/a/b'); }",  # `/assets/<path:name>`: a name that holds a `/`
    "export function viewRegexClass() { apiGet('/regex-class/'); }",  # a class-based view under `re_path`
    "export function viewAdmin() { apiGet('/admin/login/'); }",  # the admin site's: not in the snapshot
    ""])


@pytest.fixture(scope="module")
def links(tmp_path_factory):
    def run(commands):
        return [recorded("routes") for _ in commands]
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(entries.QUERIES, "django", QUERY)
        if django_app not in premap.FRAMEWORK_SOURCES:  # once the wiring is in the tree it is there already
            patch.setattr(premap, "FRAMEWORK_SOURCES", (*premap.FRAMEWORK_SOURCES, django_app))
        _, manifest = manifest_of(tmp_path_factory.mktemp("django-routes"), {**project(), "web/client.ts": CLIENT})
        premap.write(manifest, sources=(premap.requirements, django_app), runner=run)
        return flows.link_facts(manifest, flows.validate_rules(RULES))


def arcs(links):
    return {(e["from"].split("::")[1], e["to"], tuple(e["route"])) for e in links["edges"] if e.get("route")}


def reasons(links):
    return [g["reason"] for g in links["gaps"]]


def test_django_is_a_framework_source_whose_rows_are_entries_of_the_links():
    """Waits for the lines of the report in `premap/__init__.py`."""
    if not WIRED["framework"]:
        pytest.skip("`django_app` is not in `premap.FRAMEWORK_SOURCES` yet: the wiring is in the report of task 14b")
    assert django_app in premap.SOURCES and premap.SOURCES.index(django_app) < premap.SOURCES.index(premap.angular)


def test_a_class_based_view_s_methods_are_entries_each_on_its_own_function(links):
    found = sorted((e["symbol"], e["method"], e["path"]) for e in links["entries"]
                   if e["reader"] == "django" and e["symbol"].startswith("shop/views/products.py::ProductList."))
    assert ("shop/views/products.py::ProductList.get", "GET", "/shop/products/") in found
    assert ("shop/views/products.py::ProductList.post", "POST", "/api/items/") in found
    assert {e["method"] for e in links["entries"] if e["reader"] == "django" and e["path"] == "/shop/products/"} == {"GET", "POST"}


def test_a_function_view_is_an_entry_with_no_method(links):
    [entry] = [e for e in links["entries"] if e["reader"] == "django" and e["path"] == "/blog/<int:year>/<slug:slug>/"]
    assert entry["symbol"] == "shop/views/pages.py::post" and entry.get("method") is None


def test_a_call_to_a_url_with_a_value_meets_the_route_of_its_method_and_the_value_is_the_parameter(links):
    found = arcs(links)
    assert ("viewProduct", "shop/views/products.py::ProductDetail.get", ("*", "GET", "/shop/products/{}")) in found
    assert ("listItems", "shop/views/products.py::ProductList.get", ("*", "GET", "/api/items")) in found
    assert ("createItem", "shop/views/products.py::ProductList.post", ("*", "POST", "/api/items")) in found
    arc = next(e for e in links["edges"] if e["from"] == "web/client.ts::viewProduct" and e.get("route"))
    assert arc["type"] == "chiama" and arc["offered"].startswith("shop/views/products.py:")
    assert not [g for g in links["gaps"] if g["symbol"] == "web/client.ts::viewProduct"]


def test_a_method_the_class_does_not_answer_meets_nothing(links):
    assert "postProduct" not in {name for name, *_ in arcs(links)}
    assert any(r.startswith("route api POST /shop/products/") and r.endswith(": no handler") for r in reasons(links))


def test_a_function_view_is_a_gap_of_the_declared_routes_because_it_has_no_method_and_meets_no_call(links):
    """Django gives no method for a function view (`require_http_methods` keeps its list in a closure): the route is not offered, and the
    links say so for each, in the words `flows._declared_routes` has for a row with a `schema` and no `method`."""
    mine = [g for g in links["gaps"] if g["reason"].startswith("declared route None /blog/<int:year>/<slug:slug>/")]
    assert [g["reason"] for g in mine] == ["declared route None /blog/<int:year>/<slug:slug>/: it has no method"]
    assert mine[0]["symbol"] == "shop/views/pages.py::post" and mine[0]["site"].startswith("shop/views/pages.py:")
    assert {"viewBlog", "viewTenant"}.isdisjoint({name for name, *_ in arcs(links)})
    assert any(r.startswith("route api GET /blog/2020/hello") and r.endswith(": no handler") for r in reasons(links))
    assert any(r.startswith("route api GET /acme/dash") and r.endswith(": no handler") for r in reasons(links))


def test_a_route_with_a_path_converter_or_under_re_path_or_i18n_patterns_is_a_gap_of_the_declared_routes_and_meets_no_call(links):
    wanted = ("/assets/<path:name>", "/regex-class/$", "/en/products-i18n/")
    mine = [g for g in links["gaps"] if g["reason"].startswith("declared route GET ") and g["reason"].split(" ")[3].rstrip(":") in wanted]
    assert sorted(g["reason"].split(": ")[0] for g in mine) == sorted(f"declared route GET {path}" for path in wanted)
    assert all("no single path schema" in g["reason"] and g["site"].startswith("shop/views/products.py:") for g in mine)
    assert {"viewAsset", "viewRegexClass"}.isdisjoint({name for name, *_ in arcs(links)})
    assert any(r.startswith("route api GET /assets/a/b") and r.endswith(": no handler") for r in reasons(links))


def test_a_view_of_the_framework_in_the_environment_is_no_offered_route(links):
    assert "viewAdmin" not in {name for name, *_ in arcs(links)}
    assert any(r.startswith("route api GET /admin/login") and r.endswith(": no handler") for r in reasons(links))
    assert not [e for e in links["entries"] if e["path"].startswith("/admin/") or e["path"] in ("/about/", "/go/")]
