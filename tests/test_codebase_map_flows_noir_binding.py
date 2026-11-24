"""A Noir endpoint is bound to the function that starts where Noir cites its handler when the name Noir gives agrees with it: two data, the place
and the name, each an equality with the snapshot's (measured on 25 applications: `benchmarks/noir-binding`). The answers are short forms of real ones:
a closure (`closure`, anything-llm), the function that builds the handler (`recycles.blockRecycleItems()`, juice-shop), a Go method named by its
variable (`api.GetPage` for `SysApi.GetPage`, go-admin), a class view named by its class (`ListFindingGroups`, DefectDojo), a function written at the
top of a module (`authController.register`, node-express-boilerplate) and an endpoint with no handler (`"handler": null`). Everything runs on the
snapshot's own facts (`flows.Facts`), as the links and the candidates do."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import edge_view
import entries
import flows
import premap
import semantic_store
from premap import noir
from snapshot_store import open_snapshot
from test_codebase_map_premap_container_runner import manifest_of

RULES = [{"written": "app.get|post|delete", "in": ["routes"], "link": "offre", "handler": "last",
          "route": {"service": "api", "method": "part1", "path": "arg0"}}]


def source(*lines):
    return "\n".join(lines) + "\n"


def endpoint(url, method, file, name, line, protocol="http"):
    return {"protocol": protocol, "url": url, "method": method, "kind": "", "handler": {"path": f"/work/{file}", "line": line, "name": name}}


def without_handler(url, method, file, line):
    """What Noir answers where it finds the route and not its handler: the line of the registration, in `code_paths`."""
    return {"protocol": "http", "url": url, "method": method, "kind": "", "handler": None, "details": {"code_paths": [{"path": f"/work/{file}", "line": line}]}}


def snapshot_of(tmp_path, answer, files):
    _, manifest = manifest_of(tmp_path, files)
    premap.write(manifest, sources=(noir,), runner=lambda commands: [
        {"root": "/work", "returncode": 0, "stdout": json.dumps({"endpoints": answer}), "stderr": ""}])
    return manifest


def bound(tmp_path, answer, files, rules=()):
    """The rows Noir gives, as the links and the candidates bind them (`flows.bind_declared`), by method and path."""
    manifest = snapshot_of(tmp_path, answer, files)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        rows = flows.bind_declared(noir.recorded(manifest), flows.Facts(store, db, view), view, list(rules))
    return {(row["method"], row["path"]): row for row in rows}


def links_of(tmp_path, answer, files, rules=()):
    return flows.link_facts(snapshot_of(tmp_path, answer, files), list(rules))


def symbols(rows):
    return {key: row.get("symbol") for key, row in rows.items() if not row.get("gap")}


def causes(rows):
    return {key: row["gap"].partition(": ")[2] for key, row in rows.items() if row.get("gap")}


def entry_of(links, method, path):
    [found] = [e for e in links["entries"] if e.get("reader") == "noir" and (e["method"], e["path"]) == (method, path)]
    return found


def calls_from(links, symbol):
    return sorted(e["to"] for e in links["edges"] if e["type"] == "chiama" and e["from"] == symbol)


# ----------------------------------------------------------------------------------------- the name agrees with the function at the line

def test_a_name_that_agrees_with_the_function_that_starts_at_the_line_binds_it_whatever_the_receiver_or_the_class(tmp_path):
    files = {"app/apis/sys_api.go": source("package apis", "", "type SysApi struct{}", "", "func parse() {}", "", "func (e SysApi) GetPage() {", "\tparse()", "}"),  # 7
             "routes/tfa.js": source("function status() { return 1; }", "function verify(req, res) {", "  res.json(status());", "}", "module.exports = { verify };"),  # 2
             "dojo/views.py": source("class ListFindingGroups(View):", "    def get(self, request):", "        return helper()", "", "", "def helper():", "    return 1"),  # 2
             "dojo/other.py": source("def submit():", "    pass")}  # 1
    answer = [endpoint("/api/v1/sys-api", "GET", "app/apis/sys_api.go", "api.GetPage", 7), endpoint("/2fa/verify", "POST", "routes/tfa.js", "twoFactorAuth.verify", 2),
              endpoint("/findings/groups", "GET", "dojo/views.py", "ListFindingGroups", 2), endpoint("/submit", "POST", "dojo/other.py", "submit", 1)]
    links = links_of(tmp_path, answer, files)
    assert entry_of(links, "GET", "/api/v1/sys-api")["symbol"] == "app/apis/sys_api.go::SysApi.GetPage"
    assert calls_from(links, "app/apis/sys_api.go::SysApi.GetPage") == ["app/apis/sys_api.go::parse"]
    assert entry_of(links, "POST", "/2fa/verify")["symbol"] == "routes/tfa.js::verify"
    assert entry_of(links, "GET", "/findings/groups")["symbol"] == "dojo/views.py::ListFindingGroups.get"
    assert calls_from(links, "dojo/views.py::ListFindingGroups.get") == ["dojo/views.py::helper"]
    assert entry_of(links, "POST", "/submit")["symbol"] == "dojo/other.py::submit"  # the name binds first, as it always did


def test_a_name_that_is_none_of_the_function_at_the_line_is_a_gap_that_says_both(tmp_path):
    """The place alone cannot tell a handler from the function that registers it: Noir names `ghost` where `request_account_deletion` starts."""
    files = {"server/accounts.py": source("def request_account_deletion():", "    return delete_everything()", "", "", "def delete_everything():", "    return 1")}
    rows = bound(tmp_path, [endpoint("/requestAccountDeletion", "POST", "server/accounts.py", "request_account_deletion", 1),
                            endpoint("/ghost", "POST", "server/accounts.py", "ghost", 1), endpoint("/inside", "POST", "server/accounts.py", "ghost", 2)], files)
    assert symbols(rows) == {("POST", "/requestAccountDeletion"): "server/accounts.py::request_account_deletion"}
    assert causes(rows) == {("POST", "/ghost"): "Noir names ghost, the function at the line is request_account_deletion",
                            ("POST", "/inside"): "no function starts at the line Noir cites for the handler"}


def test_a_class_view_named_by_another_class_or_a_method_named_as_another_is_no_handler(tmp_path):
    files = {"dojo/views.py": source("class ListFindingGroups(View):", "    def get(self, request):", "        return 1", "", "",
                                     "class Other(View):", "    def post(self, request):", "        return 2")}
    rows = bound(tmp_path, [endpoint("/a", "GET", "dojo/views.py", "OtherView", 2), endpoint("/b", "POST", "dojo/views.py", "ListFindingGroups", 7)], files)
    assert symbols(rows) == {}
    assert causes(rows) == {("GET", "/a"): "Noir names OtherView, the function at the line is ListFindingGroups.get",
                            ("POST", "/b"): "Noir names ListFindingGroups, the function at the line is Other.post"}


def test_a_row_with_no_handler_name_never_binds_by_position_where_a_function_or_a_closure_starts(tmp_path):
    """Noir cites the registration (phazly: 76 script entries; measured: 8 rows would have bound wrongly) or a place with no name: the closure
    that starts on that line is not named by the route and stays folded."""
    files = {"server/router.js": source("function registerRoutes(app) {", "  app.get('/health', (req, res) => res.send(ok()));", "}", "function ok() { return 'ok'; }"),
             "server/script.py": source("def run():", "    return 1")}
    nameless = endpoint("/nameless", "GET", "server/router.js", None, 2)  # a handler with a place and no name
    answer = [without_handler("/health", "GET", "server/router.js", 2), nameless, without_handler("/run", "GET", "server/script.py", 1)]
    rows = bound(tmp_path, answer, files)
    assert symbols(rows) == {}
    assert {row["gap"] for row in rows.values()} == {"noir reports this entry without a unique snapshot handler at its site"}
    links = links_of(tmp_path / "links", answer, files)
    assert calls_from(links, "server/router.js::registerRoutes") == ["server/router.js::ok"]  # the closure's call is still the registering function's


def test_a_name_that_is_the_snapshot_s_own_for_a_function_with_no_node_is_a_gap_and_does_not_fail_the_links(tmp_path):
    """The name binds first, as it always did: the function it names has no node, and a row with no symbol failed the sort of the entries
    (`TypeError: '<' not supported between 'str' and 'NoneType'`) as soon as one other entry was there."""
    files = {"src/auth.js": source("const wrap = (fn) => fn;", "exports.register = wrap(async (req, res) => {", "  res.json(1);", "});"),
             "src/other.js": source("function other() {", "  return 1;", "}")}
    answer = [endpoint("/x", "POST", "src/auth.js", "(anonymous)", 3), endpoint("/y", "GET", "src/other.js", "other", 1)]
    links = links_of(tmp_path, answer, files)
    assert [e["symbol"] for e in links["entries"] if e.get("reader") == "noir"] == ["src/other.js::other"]
    [gap] = [g for g in links["gaps"] if g["site"] == "src/auth.js:3"]
    assert gap["reason"].endswith("the function there has no node: an anonymous function no named function holds")
    assert all(isinstance(e["symbol"], str) for e in links["entries"])


# ----------------------------------------------------------------------------------------------------- the function that builds the handler

def test_a_factory_is_bound_when_its_node_holds_the_calls_of_the_function_it_returns(tmp_path):
    # shortcut: Noir cites the function that builds a handler (`f()`), not the handler: its node holds the calls of the function it returns, which has no node of its own
    files = {"routes/recycles.js": source("function check() {", "  return 1;", "}", "", "function blockRecycleItems() {", "  return (req, res) => {", "    res.json(check());", "  };", "}"),  # 5
             "routes/factory.js": source("function check() { return 1; }", "const blockItems = () => (req, res) => {", "  res.json(check());", "};")}  # 2: both start on the line
    answer = [endpoint("/api/Recycles", "GET", "routes/recycles.js", "recycles.blockRecycleItems()", 5), endpoint("/api/Items", "GET", "routes/factory.js", "items.blockItems()", 2)]
    links = links_of(tmp_path, answer, files)
    assert entry_of(links, "GET", "/api/Recycles")["symbol"] == "routes/recycles.js::blockRecycleItems"
    assert calls_from(links, "routes/recycles.js::blockRecycleItems") == ["routes/recycles.js::check"]
    assert entry_of(links, "GET", "/api/Items")["symbol"] == "routes/factory.js::blockItems"
    assert calls_from(links, "routes/factory.js::blockItems") == ["routes/factory.js::check"]


def test_a_factory_whose_returned_function_is_a_node_of_its_own_is_a_gap_that_names_the_factory(tmp_path):
    """The node of the factory would not hold what the handler calls: a Go func literal, a Python lambda and a named JavaScript function are each a node."""
    files = {"api/h.go": source("package api", "", "func check() {}", "", "func Make() HandlerFunc {", "\treturn func(c *Context) {", "\t\tcheck()", "\t}", "}"),  # 5
             "app/v.py": source("def check():", "    return 1", "", "", "def make():", "    return lambda request: check()"),  # 5
             "routes/f.js": source("function check() { return 1; }", "function makeHandler() {", "  return function handle(req, res) {", "    res.json(check());", "  };", "}")}  # 2
    answer = [endpoint("/go", "GET", "api/h.go", "api.Make()", 5), endpoint("/py", "GET", "app/v.py", "views.make()", 5), endpoint("/js", "GET", "routes/f.js", "f.makeHandler()", 2)]
    rows = bound(tmp_path, answer, files)
    assert symbols(rows) == {}
    assert causes(rows) == {
        ("GET", "/go"): "Noir names api.Make(), a function that builds the handler: the one it returns is not folded into Make",
        ("GET", "/py"): "Noir names views.make(), a function that builds the handler: the one it returns is not folded into make",
        ("GET", "/js"): "Noir names f.makeHandler(), a function that builds the handler: the one it returns is not folded into makeHandler"}


# ------------------------------------------------------------------------------------------------ the function written in place, named by its route

ROUTER = source(
    "function listUsers() {",                            # 1
    "  return [];",                                      # 2
    "}",                                                 # 3
    "function addUser() {",                              # 4
    "  return 1;",                                       # 5
    "}",                                                 # 6
    "function removeUser() {",                           # 7
    "  return 2;",                                       # 8
    "}",                                                 # 9
    "",                                                  # 10
    "function userEndpoints(app) {",                     # 11
    "  app.get('/users', (req, res) => {",               # 12
    "    res.json(listUsers().map((u) => u));",          # 13
    "  });",                                             # 14
    "  app.post('/users', (req, res) => {",              # 15
    "    res.json(addUser());",                          # 16
    "  });",                                             # 17
    "  app.delete('/users/:id', (req, res) => {",        # 18
    "    res.json(removeUser());",                       # 19
    "  });",                                             # 20
    "}",                                                 # 21
    "",                                                  # 22
    "module.exports = { userEndpoints };")               # 23
USERS = [endpoint("/users", "GET", "routes/users.js", "closure", 12), endpoint("/users", "POST", "routes/users.js", "closure", 15),
         endpoint("/users/:id", "DELETE", "routes/users.js", "closure", 18)]


def test_each_closure_written_as_a_route_handler_is_its_own_node_named_by_the_route_with_the_calls_inside_its_own_lines(tmp_path):
    links = links_of(tmp_path, USERS, {"routes/users.js": ROUTER})
    assert {(e["method"], e["path"]): e["symbol"] for e in links["entries"] if e.get("reader") == "noir"} == {
        ("GET", "/users"): "routes/users.js::GET /users", ("POST", "/users"): "routes/users.js::POST /users",
        ("DELETE", "/users/:id"): "routes/users.js::DELETE /users/:id"}
    assert calls_from(links, "routes/users.js::GET /users") == ["routes/users.js::listUsers"]  # the callback inside it is part of it
    assert calls_from(links, "routes/users.js::POST /users") == ["routes/users.js::addUser"]
    assert calls_from(links, "routes/users.js::DELETE /users/:id") == ["routes/users.js::removeUser"]
    assert calls_from(links, "routes/users.js::userEndpoints") == []  # the function that registers them calls none of what the closures call
    assert not [g for g in links["gaps"] if g["site"].startswith("routes/users.js")]


def test_a_function_at_the_top_of_a_module_that_no_named_function_holds_is_the_route_s_node_and_the_links_are_built(tmp_path):
    files = {"src/auth.js": source("const wrap = (fn) => fn;", "exports.register = wrap(async (req, res) => {", "  res.json(check());", "});", "function check() { return 1; }"),
             "src/other.js": source("function other() {", "  return 1;", "}")}
    links = links_of(tmp_path, [endpoint("/v1/auth/register", "POST", "src/auth.js", "authController.register", 2), endpoint("/y", "GET", "src/other.js", "other", 1)], files)
    assert entry_of(links, "POST", "/v1/auth/register")["symbol"] == "src/auth.js::POST /v1/auth/register"
    assert calls_from(links, "src/auth.js::POST /v1/auth/register") == ["src/auth.js::check"]
    assert all(isinstance(e["symbol"], str) for e in links["entries"])


def test_the_closure_and_not_the_callback_or_the_registrar_is_the_one_function_at_a_line_that_holds_the_others(tmp_path):
    """Several functions start on one line: the one no other of them holds (their spans) is the handler of a route written on that line, or the
    function that registers it, which a name that is not Noir's `closure` for it refuses."""
    files = {"routes/u.js": source("function list() { return []; }", "function users(app) {", "  app.get('/users', (req, res) => res.json(list().map((u) => u.id)));", "}"),  # 3
             "routes/r.js": source("function a() { return 1; }", "function b() { return 2; }",
                                   "function register(app) { app.get('/a', (req, res) => { res.json(a()); });", "  app.post('/b', (req, res) => {", "    res.json(b());", "  });", "}"),  # 3, 4
             "src/health.js": source("const ok = () => 'ok';", "export const healthRoutes = (app) => app.get('/health', (req, res) => res.send(ok()));"),  # 2
             "lib/m.js": source("function a(){return 1}function b(){return 2}function register(app){app.get('/a',(q,s)=>s.json(a()));app.get('/b',(q,s)=>s.json(b()))}")}  # 1
    answer = [endpoint("/users", "GET", "routes/u.js", "closure", 3), endpoint("/a", "GET", "routes/r.js", "closure", 3), endpoint("/b", "POST", "routes/r.js", "closure", 4),
              endpoint("/health", "GET", "src/health.js", "closure", 2), endpoint("/m/a", "GET", "lib/m.js", "closure", 1)]
    rows = bound(tmp_path, answer, files)
    assert symbols(rows) == {("GET", "/users"): "routes/u.js::GET /users", ("POST", "/b"): "routes/r.js::POST /b"}
    assert causes(rows) == {("GET", "/a"): "Noir names closure, the function at the line is register",
                            ("GET", "/health"): "Noir names closure, the function at the line is healthRoutes",
                            ("GET", "/m/a"): "several functions start at the line and none holds the others"}
    links = links_of(tmp_path / "links", answer, files)
    assert calls_from(links, "routes/u.js::GET /users") == ["routes/u.js::list"]
    assert calls_from(links, "routes/r.js::register") == ["routes/r.js::a"]  # the closure of `/a` is still the registering function's


def test_a_closure_that_is_the_value_of_a_property_keeps_the_node_of_its_property(tmp_path):
    ctl = source("function find() { return []; }", "module.exports = {", "  list: async (req, res) => {", "    res.json(find());", "  },",  # 3
                 "  create: async (req, res) => {", "    res.json(find());", "  },", "};")
    routes = source("const ctl = require('./ctl');", "function r(app) {", "  app.get('/items', ctl.list);", "  app.post('/items', ctl.create);", "}")
    links = links_of(tmp_path, [endpoint("/items", "GET", "src/ctl.js", "ctl.list", 3)], {"src/ctl.js": ctl, "src/routes.js": routes})
    assert entry_of(links, "GET", "/items")["symbol"] == "src/ctl.js::list"
    assert calls_from(links, "src/ctl.js::list") == ["src/ctl.js::find"] and calls_from(links, "src/ctl.js::create") == ["src/ctl.js::find"]
    assert not [e for e in links["edges"] if "GET /items" in e["from"] or "GET /items" in e["to"]]


def test_two_closures_that_are_the_value_of_the_same_property_share_a_node_and_neither_is_bound(tmp_path):
    files = {"src/two.js": source("const a = {", "  list: (req, res) => 1,", "};", "const b = {", "  list: (req, res) => 2,", "};")}
    rows = bound(tmp_path, [endpoint("/a", "GET", "src/two.js", "closure", 2), endpoint("/b", "GET", "src/two.js", "closure", 5)], files)
    assert symbols(rows) == {}
    assert set(causes(rows).values()) == {"the function there shares its node src/two.js::list with other functions of the same name"}


def test_a_lambda_is_named_by_its_route_whether_it_is_alone_in_its_method_or_not(tmp_path):
    """The name must not depend on the siblings: a lone lambda was `CatalogApi.MapCatalogApi.(lambda)` and became `GET /a` when a sibling was added."""
    alone = source("public static class CatalogApi", "{", "    public static void MapCatalogApi(this Router app)", "    {", '        app.MapGet("/a", () => One());', "    }", "",
                   "    static int One() => 1;", "    static int Two(System.Func<int,int> f) => 2;", "}")
    sibling = alone.replace("    }\n\n", "        Two(x => x);\n    }\n\n")
    for tag, text in (("alone", alone), ("sibling", sibling)):
        links = links_of(tmp_path / tag, [endpoint("/a", "GET", "api/Cat.cs", "closure", 5)], {"api/Cat.cs": text})
        assert entry_of(links, "GET", "/a")["symbol"] == "api/Cat.cs::GET /a", tag
        assert calls_from(links, "api/Cat.cs::GET /a") == ["api/Cat.cs::CatalogApi.One"], tag


def test_the_lambdas_of_a_minimal_api_and_the_func_literals_of_a_go_router_are_each_a_node_named_by_their_route(tmp_path):
    """The `(lambda)` of one C# method and the `(func)` of one Go function are one qualified name: without the route's name they share one node."""
    csharp = source("public static class CatalogApi", "{", "    public static void MapCatalogApi(this Router app)", "    {", '        app.MapGet("/a", () => One());',
                    '        app.MapGet("/b", () =>', "        {", "            return Two();", "        });", '        app.MapGet("/c", () => Three());', "    }", "",
                    "    static int One() => 1;", "    static int Two() => 2;", "    static int Three() => 3;", "}")
    go = source("package router", "", "func a() {}", "func b() {}", "", "func Register(r Router) {", '\tr.GET("/health", func(c Ctx) {', "\t\ta()", "\t})",
                '\tr.GET("/ready", func(c Ctx) {', "\t\tb()", "\t})", "}")
    answer = [endpoint("/a", "GET", "api/Cat.cs", "closure", 5), endpoint("/b", "GET", "api/Cat.cs", "closure", 6), endpoint("/c", "GET", "api/Cat.cs", "closure", 10),
              endpoint("/health", "GET", "router/router.go", "closure", 7), endpoint("/ready", "GET", "router/router.go", "closure", 10)]
    links = links_of(tmp_path, answer, {"api/Cat.cs": csharp, "router/router.go": go})
    assert {e["path"]: e["symbol"] for e in links["entries"] if e.get("reader") == "noir"} == {
        "/a": "api/Cat.cs::GET /a", "/b": "api/Cat.cs::GET /b", "/c": "api/Cat.cs::GET /c",
        "/health": "router/router.go::GET /health", "/ready": "router/router.go::GET /ready"}
    assert [calls_from(links, f"api/Cat.cs::GET /{x}") for x in "abc"] == [["api/Cat.cs::CatalogApi.One"], ["api/Cat.cs::CatalogApi.Two"], ["api/Cat.cs::CatalogApi.Three"]]
    assert calls_from(links, "router/router.go::GET /health") == ["router/router.go::a"]
    assert calls_from(links, "router/router.go::GET /ready") == ["router/router.go::b"]


def test_a_go_func_literal_inside_a_route_closure_is_still_the_shared_node_of_the_functions_that_hold_it(tmp_path):
    """Pinned, not fixed: the readers fold only `(anonymous)` into the function that holds it, so the `(func)` a route's closure starts (`go func() { a() }()`) is
    one node for every closure of the function that registers the routes. The same goes for a lambda inside a C# lambda."""
    go = source("package router", "", "func a() {}", "func b() {}", "", "func Register(r Router) {", '\tr.GET("/health", func(c Ctx) {', "\t\tgo func() { a() }()", "\t})",
                '\tr.GET("/ready", func(c Ctx) {', "\t\tgo func() { b() }()", "\t})", "}")
    links = links_of(tmp_path, [endpoint("/health", "GET", "router/r.go", "closure", 7), endpoint("/ready", "GET", "router/r.go", "closure", 10)], {"router/r.go": go})
    assert {e["path"]: e["symbol"] for e in links["entries"] if e.get("reader") == "noir"} == {"/health": "router/r.go::GET /health", "/ready": "router/r.go::GET /ready"}
    assert calls_from(links, "router/r.go::Register.(func).(func)") == ["router/r.go::a", "router/r.go::b"]  # both routes' calls are on one node
    assert calls_from(links, "router/r.go::GET /health") == [] and calls_from(links, "router/r.go::GET /ready") == []


# ------------------------------------------------------------------------------------------------------------ more routes, or none, on a function

def test_two_routes_on_one_closure_share_its_node_whatever_the_order_noir_lists_them(tmp_path):
    files = {"routes/ping.js": source("function ok() { return 1; }", "", "function ping(app) {", "  app.get('/ping', (req, res) => {", "    res.json(ok());", "  });", "}")}
    get, head = endpoint("/ping", "GET", "routes/ping.js", "closure", 4), endpoint("/ping", "HEAD", "routes/ping.js", "closure", 4)
    for answer in ([get, head], [head, get]):
        links = links_of(tmp_path / answer[0]["method"], answer, files)
        assert {(e["method"], e["symbol"]) for e in links["entries"] if e.get("reader") == "noir"} == {
            ("GET", "routes/ping.js::GET /ping"), ("HEAD", "routes/ping.js::GET /ping")}
        assert calls_from(links, "routes/ping.js::GET /ping") == ["routes/ping.js::ok"]


def test_two_functions_that_one_route_would_name_are_named_none_of_them(tmp_path):
    files = {"routes/dup.js": source("function x() {}", "function y() {}", "", "function dup(app) {", "  app.get('/dup', (req, res) => {", "    x();", "  });",
                                     "  app.get('/dup', (req, res) => {", "    y();", "  });", "}"),
             "api/Dup.cs": source("public static class Dup", "{", "    public static void Map(this Router app)", "    {", '        app.MapGet("/dup", () => X());',
                                  '        app.MapGet("/dup", () => Y());', "    }", "    static int X() => 1;", "    static int Y() => 2;", "}"),
             "src/dup.js": source("const wrap = (fn) => fn;", "exports.a = wrap(async (req, res) => 1);", "exports.b = wrap(async (req, res) => 2);")}
    answer = [endpoint("/dup", "GET", "routes/dup.js", "closure", 5), endpoint("/dup", "GET", "routes/dup.js", "closure", 8),
              endpoint("/dup", "GET", "api/Dup.cs", "closure", 5), endpoint("/dup", "GET", "api/Dup.cs", "closure", 6),
              endpoint("/dup", "GET", "src/dup.js", "closure", 2), endpoint("/dup", "GET", "src/dup.js", "closure", 3)]
    manifest = snapshot_of(tmp_path, answer, files)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        rows = flows.bind_declared(noir.recorded(manifest), flows.Facts(store, db, view), view, [])
    assert [(r["site"], r["gap"].partition(": ")[2]) for r in rows] == [
        ("routes/dup.js:5", "the function there is folded into routes/dup.js::dup"), ("routes/dup.js:8", "the function there is folded into routes/dup.js::dup"),
        ("api/Dup.cs:5", "the function there is anonymous and its route is the route of another function of the file"),
        ("api/Dup.cs:6", "the function there is anonymous and its route is the route of another function of the file"),
        ("src/dup.js:2", "the function there has no node: an anonymous function no named function holds"),
        ("src/dup.js:3", "the function there has no node: an anonymous function no named function holds")]
    assert calls_from(flows.link_facts(manifest, []), "routes/dup.js::dup") == ["routes/dup.js::x", "routes/dup.js::y"]


def test_an_endpoint_that_is_no_route_names_no_function(tmp_path):
    """A command Noir finds (`cli`) cites a handler too, but a closure it starts is no route's node."""
    files = {"routes/cmd.js": source("function run(program) {", "  program.command('go', (args) => {", "    return 1;", "  });", "}")}
    rows = bound(tmp_path, [endpoint("go", "GET", "routes/cmd.js", "closure", 2, protocol="cli")], files)
    assert set(causes(rows).values()) == {"the function there is folded into routes/cmd.js::run"}


# ----------------------------------------------------------------------------------------------- the rules, the candidates and the links agree

def test_a_rule_that_names_a_closure_by_its_route_keeps_its_name_and_the_noir_row_is_on_the_same_node(tmp_path):
    links = links_of(tmp_path, [endpoint("/api/users", "GET", "routes/users.js", "closure", 12)], {"routes/users.js": ROUTER}, RULES)
    [row] = [e for e in links["entries"] if e.get("reader") == "noir"]
    assert row["symbol"] == "routes/users.js::GET /users"  # the rule's route, not Noir's `/api/users`
    assert {e["symbol"] for e in links["entries"] if e["site"] == "routes/users.js:12"} == {"routes/users.js::GET /users"}  # the rule's own entry is on it too
    assert calls_from(links, "routes/users.js::GET /users") == ["routes/users.js::listUsers"]


def test_the_candidates_are_on_the_nodes_of_the_links_with_the_rules_the_links_are_made_with(tmp_path):
    answer = [endpoint("/api/users", "GET", "routes/users.js", "closure", 12), endpoint("/users", "POST", "routes/users.js", "closure", 15)]
    manifest = snapshot_of(tmp_path, answer, {"routes/users.js": ROUTER})
    from snapshot import _write_json_atomic
    _write_json_atomic(manifest.with_name("flow-rules.json"), {"schema": flows.RULES_SCHEMA, "rules": RULES, "project_rules": True})
    links = flows.link_facts(manifest, flows.load_rules(manifest.with_name("flow-rules.json")))
    nodes = {e["from"] for e in links["edges"]} | {e["to"] for e in links["edges"]} | {e["symbol"] for e in links["entries"]}
    found = {(row["method"], row["path"]): row["symbol"] for row in entries.cached_syntax(manifest) if row["reader"] == "noir"}
    assert found == {("GET", "/api/users"): "routes/users.js::GET /users", ("POST", "/users"): "routes/users.js::POST /users"}
    assert set(found.values()) <= nodes
    assert found == {(e["method"], e["path"]): e["symbol"] for e in links["entries"] if e.get("reader") == "noir"}


# ----------------------------------------------------------------------------------------------------------- nothing else changes

WORLD = {
    "api/users.js": ROUTER,  # Noir's closures: no rule reads this folder
    "routes/ruled.js": source("function helper() { return 1; }", "function ruled(app) {", "  app.get('/ruled', (req, res) => res.json(helper()));", "}"),  # a rule's closure, and Noir's
    "routes/other.js": source("function helper() { return 1; }", "const handlers = {", "  list: async (req, res) => res.json(helper()),", "};",
                              "function build() {", "  return (req, res) => res.json(helper());", "}",
                              "function more(app) {", "  app.get('/more', (req, res) => res.json([1].map((n) => helper())));", "  setTimeout(() => helper(), 10);", "}",  # 9, 10
                              "module.exports = { handlers, build, more };"),
    "src/auth.js": source("const wrap = (fn) => fn;", "exports.register = wrap(async (req, res) => {", "  res.json(check());", "});", "function check() { return 1; }"),  # 2
    "server/router.js": source("function registerRoutes(app) {", "  app.get('/health', (req, res) => res.send(ok()));", "}", "function ok() { return 'ok'; }"),  # 2
    "api/Cat.cs": source("public static class CatalogApi", "{", "    public static void MapCatalogApi(this Router app)", "    {", '        app.MapGet("/a", () => One());',
                         '        app.MapGet("/b", () => Two());', "        Three(x => x);", "    }", "    static int One() => 1;", "    static int Two() => 2;",
                         "    static int Three(System.Func<int,int> f) => 3;", "}")}
WORLD_ANSWER = [endpoint("/users", "GET", "api/users.js", "closure", 12), endpoint("/users", "POST", "api/users.js", "closure", 15),
                endpoint("/users/:id", "DELETE", "api/users.js", "closure", 18), endpoint("/api/ruled", "GET", "routes/ruled.js", "closure", 3),
                endpoint("/v1/auth/register", "POST", "src/auth.js", "authController.register", 2), without_handler("/health", "GET", "server/router.js", 2),
                endpoint("/ca", "GET", "api/Cat.cs", "closure", 5), endpoint("/cb", "GET", "api/Cat.cs", "closure", 6)]
CITED = {"api/users.js": range(12, 21), "src/auth.js": range(2, 5), "api/Cat.cs": range(5, 7)}  # the lines of the closures Noir cites as handlers, whole


def test_no_node_and_no_edge_changes_but_those_of_the_closures_noir_cites_as_routes_and_of_what_is_written_inside_them(tmp_path):
    """The same project with the rules, with Noir's answer and with none: the entries, the edges and the gaps of everything else are the same."""
    quiet = flows.link_facts(snapshot_of(tmp_path / "quiet", [], WORLD), RULES)
    said = flows.link_facts(snapshot_of(tmp_path / "said", WORLD_ANSWER, WORLD), RULES)

    def edges(links):
        return {(e["from"], e["to"], e["type"], e["site"]) for e in links["edges"]}

    def cited(edge):
        file, _, line = edge[3].rpartition(":")
        return int(line) in CITED.get(file, ())
    gone, new = edges(quiet) - edges(said), edges(said) - edges(quiet)
    assert gone and new and all(cited(e) for e in gone | new)  # an edge changes only inside the lines of a closure Noir cites
    assert {e[0] for e in new} == {"api/users.js::GET /users", "api/users.js::POST /users", "api/users.js::DELETE /users/:id", "src/auth.js::POST /v1/auth/register",
                                   "api/Cat.cs::GET /ca", "api/Cat.cs::GET /cb"}
    assert {e[0] for e in gone} == {"api/users.js::userEndpoints", "src/auth.js::<module>", "api/Cat.cs::CatalogApi.MapCatalogApi.(lambda)"}
    assert edges(quiet) & edges(said) >= {e for e in edges(quiet) if e[3].startswith(("routes/", "server/"))}  # the rule's closures, the others: the same edges

    def rest(links):
        return {(e["symbol"], e["kind"], e["site"]) for e in links["entries"] if e.get("reader") != "noir"}
    assert rest(quiet) == rest(said)  # the entries the rule gave are the same
    assert [g for g in quiet["gaps"] if g["site"].startswith("routes/other")] == [g for g in said["gaps"] if g["site"].startswith("routes/other")]
    [ruled] = [e for e in said["entries"] if e.get("reader") == "noir" and e["path"] == "/api/ruled"]
    assert ruled["symbol"] == "routes/ruled.js::GET /ruled"  # the rule's name for the closure Noir cites too


def test_no_declaration_has_another_node_but_the_closures_noir_cites_as_routes_and_what_is_written_inside_them(tmp_path):
    manifest = snapshot_of(tmp_path, WORLD_ANSWER, WORLD)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        facts = flows.Facts(store, db, view)
        flows._name_written_handlers(facts, view, RULES)  # the rules first, as the links do
        before = {ident: facts.node(ident) for ident in facts.declarations}
        flows.bind_declared(noir.recorded(manifest), facts, view, RULES)
        after = {ident: facts.node(ident) for ident in facts.declarations}
        changed = {(d["file"], d["line"]) for d in facts.declarations.values() if before[d["id"]] != after[d["id"]]}
    # the closures of `api/users.js` and the callback inside the first, the function at the top of `src/auth.js` and the two lambdas of `api/Cat.cs`: not the closure of
    # `/health` (Noir names no handler), not the lambda `Three(x => x)`, not the closure a rule had named, not what is in `routes/other.js`
    assert changed == {("api/users.js", 12), ("api/users.js", 13), ("api/users.js", 15), ("api/users.js", 18), ("src/auth.js", 2), ("api/Cat.cs", 5), ("api/Cat.cs", 6)}
