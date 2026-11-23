"""The routes Noir and Next.js declare are offered routes: a call of the client meets them (`flows.link_facts`)."""
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import flows
import premap
from test_codebase_map_manifest_entries import noir_route
from test_codebase_map_premap_container_runner import manifest_of
from test_codebase_map_premap_nextjs import SHOP, VALIDATOR

RULES = [
    {"written": "apiGet", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "GET", "path": "arg0"}},
    {"written": "apiPost", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "POST", "path": "arg0"}},
    {"written": "router.get|post", "in": ["server"], "link": "offre", "handler": "last",
     "route": {"service": "api", "method": "part1", "path": "arg0"}},
]


def block(route, file, shape="RouteHandlerConfig"):
    """What `next typegen` writes for a file: the block of `.next/types/validator.ts` the reader reads."""
    stem = file.rsplit(".", 1)[0]
    return (f'\n// Validate ../../{file}\n{{\n  type __IsExpected<Specific extends {shape}<"{route}">> = Specific\n'
            f'  const handler = {{}} as typeof import("../../{stem}.js")\n  type __Check = __IsExpected<typeof handler>\n}}\n')


GET = "export async function GET() {\n  return Response.json({});\n}\n"
FILES = {
    **SHOP,  # `/checkout` and `/orders/[id]` are pages, `/api/pay` a route handler: its POST is line 1
    "app/api/orders/[id]/route.ts": GET,    # Next and Noir both declare it, spelled `[id]` and `:id`
    "app/api/items/[id]/route.ts": GET,     # only Next declares it
    "app/api/auth/[...nextauth]/route.ts": GET,  # a catch-all
    "server/accounts.py": ("def request_account_deletion():\n    pass\n\ndef twin_a():\n    pass\n\ndef twin_b():\n    pass\n\n"
                           "def search_x():\n    pass\n"),
    "server/routes.js": ("const router = require('express').Router();\n\nfunction legacy(req, res) {\n  res.json({});\n}\n\n"
                         "router.post('/legacy', legacy);\n"  # a rule offers it, and Noir declares it too
                         "\nfunction byId(req, res) {\n  res.json({});\n}\n\nrouter.get('/x/:id', byId);\n"),  # a rule: `/x/{}`
    "web/client.ts": "\n".join([
        "declare function apiGet(url: string): void;",
        "declare function apiPost(url: string): void;",
        "export function deleteAccount() { apiPost('/requestAccountDeletion'); }",
        "export function deleteAccountWithGet() { apiGet('/requestAccountDeletion'); }",
        "export function callGhost() { apiPost('/ghost'); }",
        "export function callTwin() { apiGet('/twin'); }",
        "export function viewCheckout() { apiGet('/checkout'); }",
        "export function viewOrder() { apiGet('/orders/7'); }",
        "export function payNow() { apiPost('/api/pay'); }",
        "export function loadOrder(id: string) { apiGet(`/api/orders/${id}`); }",
        "export function loadItem() { apiGet('/api/items/7'); }",
        "export function session() { apiGet('/api/auth/session'); }",
        "export function legacyCall() { apiPost('/legacy'); }",
        "export function searchX() { apiGet('/x/search'); }",  # the rule's `/x/{}` and Noir's `/x/search` both meet it
        "export function payLoose(y: string) { apiPost(`/api/pa${y}`); }", ""]),  # a hole that would have to equal `pay`
}
NOIR = {"endpoints": [
    noir_route("/requestAccountDeletion", "POST", "server/accounts.py", "request_account_deletion", 1),
    noir_route("/twin", "GET", "server/accounts.py", "twin_a", 4),
    noir_route("/twin", "GET", "server/accounts.py", "twin_b", 7),
    noir_route("/ghost", "POST", "server/accounts.py", "ghost", 1),  # no such function: no unique handler
    noir_route("/legacy", "POST", "server/routes.js", "legacy", 3),
    noir_route("/api/orders/:id", "GET", "app/api/orders/[id]/route.ts", "GET", 1),
    noir_route("/checkout", "GET", "app/checkout/page.tsx", "Checkout", 3),   # on the page: it is that page's own
    noir_route("/orders/:id", "GET", "app/orders/[id]/page.tsx", "Order", 1),  # on the page `/orders/[id]`, spelled `:id`
    noir_route("/x/search", "GET", "server/accounts.py", "search_x", 10)]}     # the rule's `/x/{}` is another function's
TYPEGEN = (VALIDATOR + block("/api/orders/[id]", "app/api/orders/[id]/route.ts")
           + block("/api/items/[id]", "app/api/items/[id]/route.ts")
           + block("/api/auth/[...nextauth]", "app/api/auth/[...nextauth]/route.ts"))


@pytest.fixture(scope="module")
def links(tmp_path_factory):
    from premap import nextjs, noir

    def run(commands):
        if commands[0]["tool"] == "noir":
            return [{"root": "/work", "returncode": 0, "stdout": json.dumps(NOIR), "stderr": ""}]
        return [{"root": "/work", "returncode": 0, "stderr": "", "stdout": "" if c["argv"][0] == "npx" else TYPEGEN}
                for c in commands]
    _, manifest = manifest_of(tmp_path_factory.mktemp("declared-routes"), FILES)
    premap.write(manifest, sources=(noir, nextjs), runner=run)
    return flows.link_facts(manifest, flows.validate_rules(RULES))


def arcs(links):
    return {(e["from"].split("::")[1], e["to"], tuple(e["route"])) for e in links["edges"] if e.get("route")}


def unlinked(links):
    return {g["symbol"].split("::")[1]: g["reason"] for g in links["gaps"] if "no handler" in g["reason"]}


def test_the_declared_routes_are_entries_on_the_functions_the_snapshot_resolves(links):
    """The ground of the tests below: the pre-map's rows reached the entries with their symbol, method and path."""
    found = {(e["reader"], e["symbol"], e.get("method"), e["path"]) for e in links["entries"] if e.get("reader") in ("noir", "next")}
    assert {("noir", "server/accounts.py::request_account_deletion", "POST", "/requestAccountDeletion"),
            ("noir", "server/accounts.py::search_x", "GET", "/x/search"),
            ("next", "app/api/orders/[id]/route.ts::GET", "GET", "/api/orders/[id]"),
            ("next", "app/api/items/[id]/route.ts::GET", "GET", "/api/items/[id]"),
            ("next", "app/api/pay/route.ts::POST", "POST", "/api/pay"),
            ("next", "app/checkout/page.tsx::Checkout", None, "/checkout")} <= found  # a page has no method of its own: Noir's is not copied
    assert not any(path == "/ghost" for *_, path in found)
    assert any(g["site"] == "server/accounts.py:1" and "without a unique snapshot handler" in g["reason"]
               for g in links["gaps"])


def test_noir_and_next_on_one_route_spelled_two_ways_are_one_entry(links):
    """`:id` and `[id]` are one path schema: Noir's route on the page, or on the function the route handler starts, is
    that entry (a page keeps no method: Noir's is not copied onto it)."""
    found = [(e["reader"], e["symbol"], e.get("method"), e["path"]) for e in links["entries"]
             if e["symbol"] in ("app/orders/[id]/page.tsx::Order", "app/api/orders/[id]/route.ts::GET")]
    assert sorted(found) == [("next", "app/api/orders/[id]/route.ts::GET", "GET", "/api/orders/[id]"),
                             ("next", "app/orders/[id]/page.tsx::Order", None, "/orders/[id]")]


def test_a_call_meets_the_noir_route_of_its_method_and_path(links):
    arc = next(e for e in links["edges"] if e["from"] == "web/client.ts::deleteAccount" and e.get("route"))
    assert (arc["type"], arc["to"], arc["route"], arc["offered"]) == (
        "chiama", "server/accounts.py::request_account_deletion", ["*", "POST", "/requestAccountDeletion"],
        "server/accounts.py:1")  # the service the rule names meets the `*` of a declared route


def test_a_call_of_another_method_meets_no_declared_route(links):
    assert ("deleteAccount", "server/accounts.py::request_account_deletion",
            ("*", "POST", "/requestAccountDeletion")) in arcs(links)  # the same route, its own method: linked
    assert "deleteAccountWithGet" not in {e[0] for e in arcs(links)}
    assert unlinked(links)["deleteAccountWithGet"] == "route api GET /requestAccountDeletion: no handler"


def test_two_declared_routes_that_meet_one_call_are_a_gap_with_the_candidates_and_no_link(links):
    [gap] = [g for g in links["gaps"] if g["symbol"] == "web/client.ts::callTwin"]
    assert gap["reason"] == "route api GET /twin: several handlers"
    assert (gap["candidates"], gap["offered"]) == (["server/accounts.py::twin_a", "server/accounts.py::twin_b"],
                                                  ["server/accounts.py:4", "server/accounts.py:7"])
    assert "callTwin" not in {e[0] for e in arcs(links)}


def test_a_noir_route_with_no_unique_handler_is_not_offered(links):
    assert "deleteAccount" in {e[0] for e in arcs(links)}  # the other Noir route of the file is
    assert unlinked(links)["callGhost"] == "route api POST /ghost: no handler"


def test_a_page_is_not_offered_even_when_it_took_the_method_of_a_noir_route(links):
    assert "payNow" in {e[0] for e in arcs(links)}  # a route handler of Next is
    assert {"viewCheckout", "viewOrder"} <= set(unlinked(links)) and not {"viewCheckout", "viewOrder"} & {e[0] for e in arcs(links)}


def test_a_rule_and_noir_on_the_same_function_method_and_path_are_one_route(links):
    assert [(e[1], e[2]) for e in arcs(links) if e[0] == "legacyCall"] == [("server/routes.js::legacy", ("api", "POST", "/legacy"))]
    assert not [g for g in links["gaps"] if g["symbol"] == "web/client.ts::legacyCall"]


def test_noir_and_next_on_the_same_handler_under_two_spellings_of_the_path_are_one_route(links):
    assert [(e[1], e[2]) for e in arcs(links) if e[0] == "loadOrder"] == [
        ("app/api/orders/[id]/route.ts::GET", ("*", "GET", "/api/orders/{}"))]
    assert not [g for g in links["gaps"] if g["symbol"] == "web/client.ts::loadOrder"]


def test_a_dynamic_segment_of_next_is_a_parameter_and_a_catch_all_is_a_gap_with_its_cause_and_place(links):
    assert [(e[1], e[2]) for e in arcs(links) if e[0] == "loadItem"] == [
        ("app/api/items/[id]/route.ts::GET", ("*", "GET", "/api/items/{}"))]
    [gap] = [g for g in links["gaps"] if "catch-all" in g["reason"]]
    assert (gap["site"], gap["symbol"]) == ("app/api/auth/[...nextauth]/route.ts:1", "app/api/auth/[...nextauth]/route.ts::GET")
    assert "/api/auth/[...nextauth]" in gap["reason"]
    assert "session" not in {e[0] for e in arcs(links)} and "session" in unlinked(links)  # no wrong link either


def test_a_route_of_a_rule_is_not_displaced_by_a_more_literal_declared_route(links):
    """The rule offers `/x/{}` on `byId`, Noir `/x/search` on `search_x`: a call of `/x/search` met the rule's route
    before the declared ones were offered, and still does (the service comes before the literal)."""
    assert [(e[1], e[2]) for e in arcs(links) if e[0] == "searchX"] == [("server/routes.js::byId", ("api", "GET", "/x/{}"))]
    assert not [g for g in links["gaps"] if g["symbol"] == "web/client.ts::searchX"]


def test_a_declared_route_is_met_only_by_a_path_no_hole_has_to_equal_a_literal_of(links):
    assert "payLoose" in unlinked(links) and "payLoose" not in {e[0] for e in arcs(links)}  # `/api/pa${y}` and `/api/pay`


def test_what_was_linked_before_is_linked_after_and_the_counts_rise(links):
    assert arcs(links) == {
        ("deleteAccount", "server/accounts.py::request_account_deletion", ("*", "POST", "/requestAccountDeletion")),
        ("payNow", "app/api/pay/route.ts::POST", ("*", "POST", "/api/pay")),
        ("loadOrder", "app/api/orders/[id]/route.ts::GET", ("*", "GET", "/api/orders/{}")),
        ("loadItem", "app/api/items/[id]/route.ts::GET", ("*", "GET", "/api/items/{}")),
        ("searchX", "server/routes.js::byId", ("api", "GET", "/x/{}")),
        ("legacyCall", "server/routes.js::legacy", ("api", "POST", "/legacy"))}  # the two a rule gave before
    assert links["routes"] == {"offered": 8, "called": 13, "linked": 6}


# ------------------------------------------------------------------ the pure parts

def row(reader, shape, method="GET", path="/x", symbol="a.py::f", kind="rotta", site="a.py:1", declares=True):
    """A row as its adapter writes it: the route's `schema` when the adapter declares a route (Noir's `http`, Next.js's
    route handler and page); the path spelled as the tool does becomes `REST`'s schema, None for a catch-all."""
    from premap import nextjs
    out = {"reader": reader, "shape": shape, "kind": kind, "symbol": symbol, "site": site, "method": method, "path": path}
    if declares:
        route = nextjs._next_path(path) if reader == "next" else path
        out["schema"] = flows.path_schema(route) if route is not None else None
    return out


def declared(rows, offered=()):
    points, gaps = flows._declared_routes(rows, list(offered))
    return [(p["symbol"], p["key"]) for p in points], gaps


def test_only_an_http_route_with_a_method_of_its_own_is_offered():
    rows = [row("noir", "http", path="/x"),
            row("next", "RouteHandlerConfig", "POST", "/api/y", "r.ts::POST", site="r.ts:1"),
            {**row("next", "AppPageConfig", None, "/page", "p.tsx::Page", site="p.tsx:1"), "page": True},  # a page has no method of its own
            row("noir", "ws", path="/live", symbol="b.py::live", declares=False),         # classified a route by a decision
            row("noir", "server-action", "POST", "/act", "c.ts::act", declares=False),
            row("noir", "cli", "CLI", "cli://deploy", "d.py::deploy", kind="comando", declares=False),
            row("manifesto", "project.scripts", "GET", "/z", "e.py::z", declares=False)]
    points, gaps = declared(rows)
    assert points == [("a.py::f", ("*", "GET", "/x")), ("r.ts::POST", ("*", "POST", "/api/y"))] and gaps == []


def test_a_next_path_gives_every_dynamic_segment_as_a_parameter_and_a_catch_all_as_a_gap():
    rows = [row("next", "RouteHandlerConfig", "GET", "/shop/[id]/items/[sku]", "a.ts::GET", site="a.ts:1"),
            row("next", "RouteHandlerConfig", "GET", "/docs/[...slug]", "b.ts::GET", site="b.ts:1"),
            row("next", "RouteHandlerConfig", "POST", "/docs/[[...slug]]", "b.ts::POST", site="b.ts:5"),
            row("noir", "http", "GET", "/files/:name", "c.py::f", site="c.py:3")]
    points, gaps = declared(rows)
    assert points == [("a.ts::GET", ("*", "GET", "/shop/{}/items/{}")), ("c.py::f", ("*", "GET", "/files/{}"))]
    assert [(g["site"], g["symbol"]) for g in gaps] == [("b.ts:1", "b.ts::GET"), ("b.ts:5", "b.ts::POST")]
    assert all("catch-all" in g["reason"] for g in gaps) and "/docs/[...slug]" in gaps[0]["reason"]


def test_a_declared_route_that_cannot_be_keyed_is_a_gap_with_its_cause():
    points, gaps = declared([row("noir", "http", "GET", "https://example.org", "a.py::f", site="a.py:2"),
                             row("noir", "http", "", "/x", "b.py::g", site="b.py:3")])
    assert points == [] and [(g["site"], g["symbol"]) for g in gaps] == [("a.py:2", "a.py::f"), ("b.py:3", "b.py::g")]
    assert "path" in gaps[0]["reason"] and "method" in gaps[1]["reason"]  # only a `page` has no method and is no gap
    assert flows._declared_routes([{**row("next", "AppPageConfig", None, "/p", site="p.tsx:1"), "page": True}], []) == ([], [])


def test_a_declared_route_of_a_function_method_and_path_schema_already_offered_is_dropped_whatever_its_service():
    offered = [{"symbol": "a.py::f", "key": ("api", "GET", "/x/{}"), "site": "a.py:1"}]
    points, _ = declared([row("noir", "http", "GET", "/x/:id"),                  # the rule's own route, spelled otherwise
                          row("noir", "http", "GET", "/x/:id", "b.py::g"),       # another function: its own route
                          row("noir", "http", "POST", "/x/:id"),                 # another method
                          row("next", "RouteHandlerConfig", "GET", "/y/[id]", "n.ts::GET"),
                          row("noir", "http", "GET", "/y/{id}", "n.ts::GET")],   # one handler, two spellings
                         offered)
    assert points == [("b.py::g", ("*", "GET", "/x/{}")), ("a.py::f", ("*", "POST", "/x/{}")),
                      ("n.ts::GET", ("*", "GET", "/y/{}"))]


def test_an_offered_star_meets_any_calling_service_and_the_calling_side_is_never_a_star():
    offered = [{"id": "rule", "key": ("api", "GET", "/x/{}")}, {"id": "declared", "key": ("*", "GET", "/x/{}")},
               {"id": "only", "key": ("*", "GET", "/y")}]

    def met(key):
        [(_, found)] = flows.join(flows.REST, [{"key": key}], offered)
        return [o["id"] for o in found]
    assert met(("api", "GET", "/x/{}")) == ["rule"]        # a route of the asked service comes before one of `*`
    assert met(("shop", "GET", "/x/{}")) == ["declared"]
    assert met(("api", "GET", "/y")) == ["only"]
    assert met(("api", "POST", "/y")) == []
    assert met(("*", "GET", "/y")) == ["only"] and met(("*", "GET", "/x/{}")) == ["declared"]
    assert flows.REST.meet(("*", "GET", "/y"), ("api", "GET", "/y")) is None
    assert flows.REST.key(None, "GET", "/y") is None  # a rule's service is a literal: none is a gap


def met(offered, key):
    [(_, found)] = flows.join(flows.REST, [{"key": key}], offered)
    return [o["id"] for o in found]


def test_a_route_of_the_calling_service_comes_before_a_more_literal_one_of_star():
    offered = [{"id": "rule", "key": ("api", "GET", "/x/{}")}, {"id": "declared", "key": ("*", "GET", "/x/search")}]
    assert met(offered, ("api", "GET", "/x/search")) == ["rule"]
    assert met(offered, ("shop", "GET", "/x/search")) == ["declared"]


def test_an_offered_star_is_met_only_by_a_path_no_hole_has_to_equal_a_literal_of():
    offered = [{"id": "search", "key": ("*", "GET", "/x/search")}, {"id": "dyn", "key": ("*", "GET", "/y/{}")}]
    assert met(offered, ("api", "GET", "/x/{}")) == []       # `/x/${q}`: a hole that would have to equal `search`
    assert met(offered, ("api", "GET", "/x/sea{}")) == []
    assert met(offered, ("api", "GET", "/x/search")) == ["search"]
    assert met(offered, ("api", "GET", "/y/7")) == met(offered, ("api", "GET", "/y/{}")) == ["dyn"]
    assert met([{"id": "r", "key": ("api", "GET", "/x/search")}], ("api", "GET", "/x/{}")) == ["r"]  # a service's own stay loose


@pytest.mark.parametrize("link", ["rotta", "offre"])
def test_a_rule_cannot_name_the_service_star(link):
    rule = {"written": "f", "link": link, "route": {"service": "*", "method": "GET", "path": "arg0"}}
    with pytest.raises(ValueError, match="service.*reserved"):
        flows.validate_rules([rule])
    flows.validate_rules([{**rule, "route": {**rule["route"], "service": "api"}}])


def test_a_change_of_the_link_code_changes_the_key_of_the_cached_links():
    seen = []
    with mock.patch.object(Path, "read_bytes", autospec=True, side_effect=lambda self: seen.append(self.name) or b""):
        flows._links_reader_digest.__wrapped__()
    assert "flows.py" in seen
