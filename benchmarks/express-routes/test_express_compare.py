"""The pure counts of `summarize.py` on rows written by hand (no Modal, no project):
`modal run tests/modal_pytest.py --args "benchmarks/express-routes/test_express_compare.py -q"`."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "daodan/core")]

import cases  # noqa: E402
import flows  # noqa: E402
import summarize  # noqa: E402

EXPRESS = [
    {"method": "GET", "path": "/v1/users", "symbol": "routes/users.js::list"},
    {"method": "GET", "path": "/v1/users", "symbol": "routes/users.js::list"},  # the same route twice: once
    {"method": "POST", "path": "/v1/users/:id", "symbol": "routes/users.js::update"},
    {"method": "GET", "path": "/v1/health", "symbol": "app.js::health"},
    {"method": None, "path": "/v1/any", "symbol": "app.js::ANY /v1/any"},
    {"method": "GET", "path": None, "gap": "express route GET (computed): the path is no literal"},
    {"method": "GET", "path": "/x", "gap": "express route GET /x: the handler is no function of the snapshot: a call of a external"},
    {"method": "GET", "path": "/y", "gap": "express route GET /y: the handler is no function of the snapshot: a call of a external"},
    {"method": "GET", "path": "/z", "gap": "express route GET /z: mounted under a prefix that is no literal at app.js:9"},
]
NOIR = [
    {"method": "GET", "path": "/v1/users", "symbol": "routes/users.js::list"},  # the same route and function
    {"method": "POST", "path": "/users/{id}", "symbol": "routes/users.js::update"},  # the same function, the prefix lost
    {"method": "GET", "path": "/v1/health", "symbol": "app.js::other"},  # another function
    {"method": "DELETE", "path": "/gone", "symbol": "app.js::gone"},  # Noir's only
    {"method": "GET", "path": "/w", "gap": "noir reports this entry without a unique snapshot handler at its site"},
]


def test_a_bound_route_is_its_method_schema_and_symbol_once():
    assert summarize.bound(EXPRESS, flows.path_schema) == {
        ("GET", flows.path_schema("/v1/users"), "routes/users.js::list"), ("POST", flows.path_schema("/v1/users/:id"), "routes/users.js::update"),
        ("GET", flows.path_schema("/v1/health"), "app.js::health"), (None, flows.path_schema("/v1/any"), "app.js::ANY /v1/any")}


def test_the_cause_of_a_gap_leaves_out_the_route_and_the_sites():
    assert [summarize.cause(row["gap"]) for row in EXPRESS if row.get("gap")] == [
        "the path is no literal", "the handler is no function of the snapshot", "the handler is no function of the snapshot",
        "mounted under a prefix that is no literal"]


def test_compare_counts_routes_functions_and_discordances():
    out = summarize.compare(EXPRESS, NOIR, flows.path_schema)
    assert (out["express_rows"], out["express_bound"], out["noir_rows"], out["noir_bound"]) == (9, 4, 5, 4)
    assert (out["common_routes"], out["same_route_and_function"], out["same_function_other_path"]) == (2, 1, 1)
    assert out["express_gaps"] == {"the handler is no function of the snapshot": 2, "the path is no literal": 1,
                                   "mounted under a prefix that is no literal": 1}
    assert out["noir_gaps"] == 1
    assert out["only_express"] == sorted([["GET", flows.path_schema("/v1/health"), "app.js::health"],
                                          [None, flows.path_schema("/v1/any"), "app.js::ANY /v1/any"]], key=str)
    assert out["only_noir"] == sorted([["GET", flows.path_schema("/v1/health"), "app.js::other"],
                                       ["DELETE", flows.path_schema("/gone"), "app.js::gone"]], key=str)


def test_the_sample_is_fixed_by_its_seed_and_drawn_from_every_application():
    compared = {"a": {"only_express": [["GET", "/a/{}", f"a.js::f{i}"] for i in range(15)]},
                "b": {"only_express": [["POST", "/b", f"b.js::g{i}"] for i in range(15)]}}
    first = summarize.sample(compared)
    assert first == summarize.sample(compared) and len(first) == summarize.SAMPLE
    assert {item["application"] for item in first} == {"a", "b"}


def test_the_three_express_applications_are_those_of_noir_binding():
    spec = importlib.util.spec_from_file_location("binding_apps", HERE.parent / "noir-binding/apps.py")
    binding = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(binding)
    for name, (repository, commit, licence) in cases.CASES.items():
        if name != "tududi":
            assert binding.APPS[name][:4] == ("express", repository, commit, licence)
