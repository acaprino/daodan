"""The pure counts of `summarize.py` on rows written by hand (no Modal, no project): `modal run tests/modal_pytest.py --args "benchmarks/hono-routes/test_hono_routes.py -q"`."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "daodan/core")]

import flows  # noqa: E402
import summarize  # noqa: E402

INSPECTED = [  # as `inspectRoutes` prints the fixture
    {"path": "/*", "method": "ALL", "name": "timing", "isMiddleware": True},
    {"path": "/health", "method": "GET", "name": "health", "isMiddleware": False},
    {"path": "/inline", "method": "GET", "name": "[handler]", "isMiddleware": False},
    {"path": "/api/v1/users", "method": "GET", "name": "listUsers", "isMiddleware": False},
    {"path": "/api/v1/users", "method": "GET", "name": "listUsers", "isMiddleware": False},
    {"path": "/api/v1/users/:id", "method": "POST", "name": "[handler]", "isMiddleware": False},
    {"path": "/old", "method": "GET", "name": "render", "isMiddleware": False},
]
FUNCTIONS = [
    {"name": "health", "qualified_name": "health"},
    {"name": "listUsers", "qualified_name": "listUsers"},
    {"name": "render", "qualified_name": "A.render"},
    {"name": "render", "qualified_name": "B.render"},
    {"name": "(anonymous)", "qualified_name": None},
]


def test_routes_drop_middleware_and_repeats():
    found = summarize.routes(INSPECTED)
    assert [(r["method"], r["path"]) for r in found] == [
        ("GET", "/health"), ("GET", "/inline"), ("GET", "/api/v1/users"), ("POST", "/api/v1/users/:id"), ("GET", "/old")]


def test_a_handler_is_bindable_only_by_a_name_of_one_function():
    counted = summarize.names(FUNCTIONS)
    assert [summarize.handler(n, counted) for n in ("health", "[handler]", "render", "missing", "[middleware]")] == [
        "unique", "nameless", "ambiguous", "absent", "nameless"]


def test_compare_counts_common_routes_by_method_and_schema():
    counted = summarize.names(FUNCTIONS)
    noir = [{"method": "GET", "path": "/health", "symbol": "src/index.js::health"},
            {"method": "GET", "path": "/api/v1/users", "symbol": "src/api.js::other"},
            {"method": "post", "path": "/api/v1/users/{id}"},
            {"method": "DELETE", "path": "/gone"}]
    out = summarize.compare(summarize.routes(INSPECTED), noir, counted,
                            {"health": "src/index.js::health", "listUsers": "src/api.js::listUsers"}, flows.path_schema)
    assert (out["inspect_routes"], out["noir_routes"], out["common"]) == (5, 4, 3)
    assert out["only_noir"] == [["DELETE", flows.path_schema("/gone")]]
    assert sorted(m for m, _ in out["only_inspect"]) == ["GET", "GET"]
    assert out["inspect_handlers"] == {"ambiguous": 1, "nameless": 2, "unique": 2}
    assert (out["noir_bound"], out["common_bound_by_both"], out["common_same_function"]) == (2, 2, 1)
