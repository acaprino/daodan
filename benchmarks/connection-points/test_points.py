"""The language-free part: route keys, the join by key, islands and reach."""
import points


def _exposed(key, site, handler="h"):
    return {"site": site, "role": "exposes", "kind": "http", "keys": [key], "holder": handler}


def _calls(keys, site, hole=None):
    return {"site": site, "role": "calls", "kind": "http", "keys": keys, "holder": "c", "hole": hole}


def test_route_keys_turn_parameters_into_placeholders():
    assert points.route_key("PATCH", "/api/task/:uid") == "PATCH /api/task/{}"
    assert points.route_key("GET", "/api/") == "GET /api"
    assert points.route_key("GET", "*") == "GET /{*}"


ROUTES = [_exposed("GET /api/tasks", "r:1"), _exposed("GET /api/tasks/metrics", "r:2"),
          _exposed("GET /api/task/{}", "r:3"), _exposed("PATCH /api/task/{}", "r:4"),
          _exposed("GET /api/project/{}", "r:5"), _exposed("GET /api/project/{}/complete", "r:6"),
          _exposed("GET /{*}", "spa:1"), _exposed("ALL /api/x", "r:7")]


def _one(keys, site="c:1"):
    return points.join(ROUTES + [_calls(keys, site)])


def test_exact_keys_join_and_the_literal_route_beats_a_parameter():
    out = _one(["GET /api/tasks/metrics"])
    assert [(l["call"], l["route"], l["match"]) for l in out["links"]] == [("c:1", "r:2", "exact")]


def test_a_literal_value_fills_a_parameter():
    assert [l["route"] for l in _one(["GET /api/task/abc"])["links"]] == ["r:3"]


def test_a_partial_hole_joins_loosely_and_says_so():
    out = _one(["GET /api/tasks{}"])
    assert [(l["route"], l["match"]) for l in out["links"]] == [("r:1", "loose")]


def test_an_unknown_method_with_two_routes_is_uncertain_with_candidates():
    out = _one(["* /api/task/{}"])
    assert out["links"] == [] and sorted(out["uncertain"][0]["candidates"]) == ["r:3", "r:4"]


def test_all_matches_every_method():
    assert [l["route"] for l in _one(["DELETE /api/x"])["links"]] == ["r:7"]


def test_a_call_only_the_catch_all_takes_is_a_missing_route():
    out = _one(["GET /api/nothing"])
    assert out["links"] == [] and out["calls_only"][0]["reason"] == "only the catch-all route"


def test_one_sided_keys_are_reported_not_dropped():
    out = points.join(ROUTES + [_calls(["GET /api/tasks"], "c:1"), _calls([], "c:2", hole="path built at run time")])
    assert "r:5" in {r["site"] for r in out["exposed_only"]}
    assert [h["site"] for h in out["holes"]] == ["c:2"]


def test_a_site_with_several_keys_links_each_and_drops_none():
    out = _one(["GET /api/tasks", "GET /api/tasks{}&x=1"])
    assert [l["route"] for l in out["links"]] == ["r:1"]
    assert out["unmatched_candidates"][0]["key"] == "GET /api/tasks{}&x=1"
    assert out["calls_only"] == []


def test_islands_count_components_singletons_and_share():
    out = points.islands({"a", "b", "c", "d", "e"}, [("a", "b"), ("b", "c")])
    assert out == {"nodes": 5, "components": 3, "largest": [3, 1, 1], "singletons": 2, "largest_share": 0.6}


def test_holder_of_a_span_is_the_innermost_definition_that_holds_it():
    edges = [("m", "x", "f.js:5"), ("inner", "y", "f.js:6"), ("fn", "z", "f.js:12")]
    lines = {"m": 1, "inner": 6, "fn": 10}
    assert points.holder("f.js", 4, 8, edges, lines, "m") == "m"  # an inline handler at the top level
    assert points.holder("f.js", 10, 14, edges, lines, "m") == "fn"  # a named handler
    assert points.holder("f.js", 20, 22, edges, lines, "m") == "m"  # no edge inside: its module


def test_reach_follows_edges_forward():
    assert points.reach({"a"}, [("a", "b"), ("b", "c"), ("d", "a")], {"c"}) == {"a"}
