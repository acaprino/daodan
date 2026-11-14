"""The client adapter on a small fixture: every way tududi builds a request, and the cases it must not guess."""
from pathlib import Path

import client_http

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures" / "client"
FETCH = "ext lib.dom.d.ts/fetch()."
GET_API = "p paths.ts/getApiPath()."
SEND = "p service.ts/send()."
CSRF = "p csrf.ts/fetchWithCsrf."
RULES = {"sink": {"name": "fetch", "symbol": "/fetch()."},
         "prefix": [{"function": "getApiPath", "symbol": "paths.ts/getApiPath().", "prefix": "/api/"}]}


def _index():
    """Edges per site as (holder, symbol), the shape the graph gives."""
    holders = {7: "listTasks", 11: "deleteTask", 15: "timeline", 21: "projects", 25: "iterations",
               26: "iterations", 31: "plan", 34: "send", 37: "checkIn", 39: "createUser", 41: "unknown",
               43: "avatar"}
    edges = {}
    for line in (7, 11, 15, 21, 26, 31, 34, 41):
        edges[f"service.ts:{line}"] = [(f"p service.ts/{holders[line]}.", FETCH)]
    for line in (7, 11, 21, 25, 31, 34, 39, 43):
        edges.setdefault(f"service.ts:{line}", []).append((f"p service.ts/{holders[line]}.", GET_API))
    edges["service.ts:34"] = [(SEND, FETCH), (SEND, GET_API)]
    edges["service.ts:37"] = [("p service.ts/checkIn.", SEND)]
    edges["service.ts:39"].append(("p service.ts/createUser.", CSRF))
    edges["csrf.ts:2"] = [(CSRF, FETCH)]
    return {"edges": edges}


def _run():
    sources = {path.name: path.read_text(encoding="utf-8") for path in FIX.glob("*.ts")}
    return client_http.extract(sources, RULES, _index())


def _keys(out):
    return {site["site"]: site["keys"] for site in out["sites"]}


def test_direct_calls_get_method_and_normalised_path():
    keys = _keys(_run())
    assert keys["service.ts:11"] == ["DELETE /api/task/{}"]
    assert keys["service.ts:15"] == ["GET /api/task/{}/timeline"]  # module constant prefix


def test_a_variable_glued_to_a_segment_stays_a_partial_hole():
    assert _keys(_run())["service.ts:7"] == ["GET /api/tasks{}"]


def test_local_variables_helpers_and_branches_give_every_candidate():
    keys = _keys(_run())
    assert keys["service.ts:21"] == ["GET /api/projects"]  # let url, url += ?query
    assert keys["service.ts:26"] == ["GET /api/task/{}/next"]  # two branches, one key
    assert keys["service.ts:31"] == ["GET /api/daily-plan"]  # withQuery returns path or path?query


def test_wrappers_move_the_call_to_their_confirmed_callers():
    out = _run()
    keys = _keys(out)
    assert keys["service.ts:37"] == ["POST /api/habits/{}/check-in"]  # send(path, method)
    assert keys["service.ts:39"] == ["POST /api/admin/users"]  # fetchWithCsrf(getApiPath(...), options)
    assert {w["name"] for w in out["wrappers"]} == {"send", "fetchWithCsrf", "unknown"}
    assert "service.ts:34" not in keys and "csrf.ts:2" not in keys


def test_a_url_nobody_passes_is_a_declared_hole():
    site = next(s for s in _run()["sites"] if s["site"] == "service.ts:41")
    assert site["keys"] == [] and "fileUrl" in site["hole"]


def test_api_paths_outside_requests_are_counted_not_lost():
    assert [use["site"] for use in _run()["outside"]] == ["service.ts:43"]


def test_a_call_the_index_does_not_confirm_is_reported_not_joined():
    index = _index()
    index["edges"]["service.ts:37"] = []
    out = client_http.extract({p.name: p.read_text(encoding="utf-8") for p in FIX.glob("*.ts")}, RULES, index)
    assert "service.ts:37" not in _keys(out)
    assert any(u["site"] == "service.ts:37" for u in out["unconfirmed"])


def test_a_call_confirmed_for_one_of_two_same_named_wrappers_is_not_unconfirmed():
    sources = {"a.ts": "async function send(path: string) {\n    return fetch(path);\n}\nsend('/x');\n",
               "b.ts": "async function send(path: string) {\n    return fetch(path);\n}\n"}
    edges = {"a.ts:2": [("a send", FETCH)], "b.ts:2": [("b send", FETCH)], "a.ts:4": [("a.ts", "a send")]}
    out = client_http.extract(sources, RULES, {"edges": edges})
    assert _keys(out)["a.ts:4"] == ["GET /x"] and out["unconfirmed"] == []
