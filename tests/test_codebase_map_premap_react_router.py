"""The routes a React Router or Remix project's own command prints, `react-router routes --json` and `remix routes --json`,
read from its output and bound to the snapshot.

The container is a fake: the answers are the ones the real commands printed on Modal for the fixtures of
`benchmarks/react-router-routes/` (`tests/fixtures/premap/react-router/answers.json`, recorded by that folder's
`modal_probe.py --mode source`). The tool gives each route its `path`, its `index` and its `file` (relative to the app
directory, which it does not name), and nothing about the route module's exports: those are the snapshot's own export
records, bound to the functions they name (`QUERIES["react-router"]` says which exports a route starts).
"""
from __future__ import annotations

import json
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from test_codebase_map_container_runner import bound, container, container_runner, manifest_of, entry_points, premap, recorder

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/react-router-routes/fixture"
ANSWERS = json.loads((Path(__file__).parent / "fixtures/premap/react-router/answers.json").read_text(encoding="utf-8"))
SOURCE = "react-router@daodan/premap/v5"  # v5: the route's `schema`; v4: the module row with its `exports`, bound by the links; v3: the root's and a pathless layout's data functions are rows; v2: an absolute child, the root under `app/`: an older pre-map is stale
LAST = "nessun ingresso"
EXPORTS = ("default", "loader", "action", "clientLoader", "clientAction")
LIMIT = ["timeout", "--kill-after=10", "300"]  # what ends a command that does not end: 10 seconds after the signal, the kill


def project(name: str, **changes) -> dict[str, str]:
    files = {path.relative_to(BENCHMARK / name).as_posix(): path.read_text(encoding="utf-8")
             for path in (BENCHMARK / name).rglob("*") if path.is_file() and path.name != "package-lock.json"}
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def answer(name: str) -> dict:
    return {**ANSWERS[name], "root": "/work"}


def runner_for(answers):
    """A runner that answers each command from `answers`, folder -> the recorded answer."""
    asked = []

    def run(commands):
        asked.extend(commands)
        return [answers[c["cwd"]] if isinstance(answers, dict) else answers for c in commands]
    return asked, run


def read(tmp_path, files, name="framework", answers=None):
    _, manifest = manifest_of(tmp_path, files)
    asked, run = runner_for(answers or {".": answer(name)})
    record = entry_points.write(manifest, sources=(entry_points.react_router,), runner=run)
    record["bound"] = bound(manifest, record)
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], asked


def at(files, file, needle):
    """`file:line` of the first line of the file that holds `needle`: the position is checked against the text itself."""
    return f"{file}:{next(n for n, line in enumerate(files[file].split(chr(10)), 1) if needle in line)}"


def found(record):
    """Each row: path, shape, kind, site, symbol, the export that starts it (None at the file), the gap."""
    return sorted((r["path"], r["shape"], r["kind"], r["site"], r["symbol"], r.get("handler"), r.get("gap"))
                  for r in record["bound"])


def starts(record, path, shape=None):
    """The exports a route starts: name -> the function the snapshot binds it to."""
    return {r["handler"]: r["symbol"].split("::")[1] for r in record["bound"]
            if r["path"] == path and r.get("handler") and (shape is None or r["shape"] == shape)}


# ------------------------------------------------------------------- the routes of the project

def test_every_route_of_the_tree_the_tool_prints_is_a_candidate_with_its_file_and_the_function_each_of_its_exports_names(tmp_path):
    files = project("framework")
    record, gaps, asked = read(tmp_path, files)
    by = lambda file, name: f"{file}::{name}"  # noqa: E731
    routes = "app/routes/"
    expected = [
        ("/", "layout", LAST, "app/root.tsx", by("app/root.tsx", "<module>"), None, None),
        ("/", "index", "rotta", at(files, routes + "home.tsx", "export default function Home"),
         by(routes + "home.tsx", "Home"), "default", None),
        ("/", "layout", LAST, routes + "shop/layout.tsx", by(routes + "shop/layout.tsx", "<module>"), None, None),
        ("/about", "route", "rotta", at(files, routes + "about.tsx", "const About"), by(routes + "about.tsx", "About"), "default", None),
        ("/checkout", "route", "rotta", at(files, routes + "shop/checkout.tsx", "function loader"),
         by(routes + "shop/checkout.tsx", "loader"), "loader", None),
        ("/checkout", "route", "rotta", at(files, routes + "shop/checkout.tsx", "function action"),
         by(routes + "shop/checkout.tsx", "action"), "action", None),
        ("/checkout", "route", "rotta", at(files, routes + "shop/checkout.tsx", "function Checkout"),
         by(routes + "shop/checkout.tsx", "Checkout"), "default", None),
        ("/orders/:id", "route", "rotta", at(files, routes + "shop/order.tsx", "const loader"),
         by(routes + "shop/order.tsx", "loader"), "loader", None),
        ("/orders/:id", "route", "rotta", at(files, routes + "shop/order.tsx", "function Order"),
         by(routes + "shop/order.tsx", "Order"), "default", None),
        ("/api/pay", "route", "rotta", at(files, routes + "api/pay.ts", "function loader"), by(routes + "api/pay.ts", "loader"), "loader", None),
        ("/api/pay", "route", "rotta", at(files, routes + "api/pay.ts", "function action"), by(routes + "api/pay.ts", "action"), "action", None),
        ("/api/health", "route", "rotta", at(files, routes + "api/health.ts", "function loader"),
         by(routes + "api/health.ts", "loader"), "loader", None),
        ("/:lang?/blog", "route", "rotta", at(files, routes + "blog.tsx", "function Blog"), by(routes + "blog.tsx", "Blog"), "default", None),
        ("/users/:id", "route", "rotta", at(files, routes + "users/user.tsx", "function User"), by(routes + "users/user.tsx", "User"), "default", None),
        ("/users/:id/edit", "route", "rotta", at(files, routes + "users/edit.tsx", "function action"),
         by(routes + "users/edit.tsx", "action"), "action", None),
        ("/users/:id/edit", "route", "rotta", at(files, routes + "users/edit.tsx", "function EditUser"),
         by(routes + "users/edit.tsx", "EditUser"), "default", None),
        ("/nested", "route", "rotta", at(files, routes + "nested/layout.tsx", "function NestedLayout"),
         by(routes + "nested/layout.tsx", "NestedLayout"), "default", None),
        ("/nested", "index", "rotta", at(files, routes + "nested/index.tsx", "function NestedIndex"),
         by(routes + "nested/index.tsx", "NestedIndex"), "default", None),
        ("/nested/child", "route", "rotta", at(files, routes + "nested/child.tsx", "function NestedChild"),
         by(routes + "nested/child.tsx", "NestedChild"), "default", None),
        ("/en/hello", "route", "rotta", at(files, routes + "hello.tsx", "function Hello"), by(routes + "hello.tsx", "Hello"), "default", None),
        ("/it/hello", "route", "rotta", at(files, routes + "hello.tsx", "function Hello"), by(routes + "hello.tsx", "Hello"), "default", None),
    ]
    rows = found(record)
    gap_rows = [row for row in rows if row[6]]
    assert [row for row in rows if not row[6]] == sorted(expected)
    # `docs.tsx` default-exports an anonymous function and `legacy.jsx` re-exports: the snapshot binds neither, so each is a gap row
    assert [(row[0], row[3], row[4], row[5]) for row in gap_rows] == [
        ("/docs/*", routes + "docs.tsx", by(routes + "docs.tsx", "<module>"), None),
        ("/legacy", routes + "legacy.jsx", by(routes + "legacy.jsx", "<module>"), None)]
    assert "default" in gap_rows[0][6] and "default: reexport-unsupported" in gap_rows[1][6]
    assert gaps == []
    assert all(r["reader"] == "react-router" and r["sources"] == [SOURCE] for r in record["bound"])
    assert [(c["argv"], c["cwd"], c["network"]) for c in asked] == [
        ([*LIMIT, "npx", "--no-install", "react-router", "routes", "--json"], ".", "none")]


def test_a_route_module_with_no_default_export_is_a_resource_route_and_starts_only_its_data_functions(tmp_path):
    record, _, _ = read(tmp_path, project("framework"))
    assert starts(record, "/api/pay") == {"loader": "loader", "action": "action"}
    assert starts(record, "/api/health") == {"loader": "loader"}
    assert starts(record, "/checkout") == {"loader": "loader", "action": "action", "default": "Checkout"}


def test_a_layout_with_no_path_is_one_row_on_its_file_that_no_flow_starts_from(tmp_path):
    record, _, _ = read(tmp_path, project("framework"))
    layout = [r for r in record["bound"] if r["site"] == "app/routes/shop/layout.tsx"]
    assert [(r["shape"], r["kind"], r["path"], r["symbol"]) for r in layout] == [
        ("layout", LAST, "/", "app/routes/shop/layout.tsx::<module>")]
    assert "handler" not in layout[0] and "gap" not in layout[0]  # the tool gives no export to start: not a gap, a layout


DATA = "export async function loader() { return null; }\nexport async function action() { return null; }\n"
ROOT = 'import { Outlet } from "react-router";\n' + DATA + "export default function App() { return <Outlet />; }\n"
LAYOUT = 'import { Outlet } from "react-router";\n' + DATA + "export default function ShopLayout() { return <Outlet />; }\n"


def test_the_loader_and_action_of_the_root_are_entries_on_their_functions_and_the_module_row_stays(tmp_path):
    """`getTargetMatch` of react-router 7.18.6 (read, not run): the target of a submission is the last match that contributes a
    path, and the first match always does, so the root's `action` is the target of a post to `/`; its `loader` runs for each
    request of a page under it."""
    files = project("framework", **{"app/root.tsx": ROOT})
    record, gaps, _ = read(tmp_path, files)
    assert starts(record, "/", "root-data") == {"loader": "loader", "action": "action"}
    rows = [r for r in record["bound"] if r["site"].startswith("app/root.tsx")]
    assert {(r["shape"], r["kind"]) for r in rows} == {("layout", LAST), ("root-data", "rotta")}
    assert [r["site"] for r in rows if r["shape"] == "root-data"] == [at(files, "app/root.tsx", "function loader"),
                                                                       at(files, "app/root.tsx", "function action")]
    assert gaps == []


def test_the_loader_of_a_layout_with_no_path_is_an_entry_and_its_action_is_not_because_no_post_has_it_as_target(tmp_path):
    """A layout with no path does not contribute a path, so `getTargetMatch` never returns it: its `action` is never called by
    the framework (dead code, not an entry and not a gap); its `loader` runs for each request of a page under it."""
    file = "app/routes/shop/layout.tsx"
    files = project("framework", **{file: LAYOUT})
    record, gaps, _ = read(tmp_path, files)
    assert starts(record, "/", "layout-data") == {"loader": "loader"}
    rows = [r for r in record["bound"] if r["site"].startswith(file)]
    assert {(r["shape"], r["kind"]) for r in rows} == {("layout", LAST), ("layout-data", "rotta")}
    assert not [r for r in rows if r.get("gap")] and gaps == []


def test_a_layout_or_root_with_no_data_function_is_the_module_row_only_and_no_gap(tmp_path):
    record, _, _ = read(tmp_path, project("framework"))
    assert not [r for r in record["bound"] if r["shape"] in ("root-data", "layout-data")]


def test_a_data_function_of_the_root_or_a_layout_that_the_snapshot_cannot_bind_is_a_gap_row_of_the_data_shape(tmp_path):
    """The gap row has the shape of the data function, not `layout`: a row of a shape that no flow starts from is dropped
    before its gap is looked at (`flows._classify_entries`)."""
    files = project("framework", **{"app/root.tsx": "export const loader = make();\nexport default function App() { return null; }\n"})
    record, _, _ = read(tmp_path, files)
    [row] = [r for r in record["bound"] if r["shape"] == "root-data"]
    assert row["gap"] and "loader" in row["gap"] and row["symbol"] == "app/root.tsx::<module>" and row["kind"] == "rotta"


def test_the_gap_of_a_root_data_function_reaches_the_links_and_its_function_is_an_entry(tmp_path):
    import flows
    files = project("framework", **{"app/root.tsx": ROOT, "app/routes/shop/layout.tsx": LAYOUT})
    _, manifest = manifest_of(tmp_path, files)
    entry_points.write(manifest, sources=(entry_points.react_router,), runner=runner_for({".": answer("framework")})[1])
    found = flows.cached_links(manifest, [])
    assert {(e["shape"], e["symbol"].split("::")[1], e["handler_source"]) for e in found["entries"]
            if e["reader"] == "react-router" and e["shape"].endswith("-data")} == {
        ("root-data", "loader", "react-router"), ("root-data", "action", "react-router"), ("layout-data", "loader", "react-router")}
    files = project("framework", **{"app/root.tsx": "export const loader = make();\nexport default function App() { return null; }\n"})
    _, manifest = manifest_of(tmp_path / "unbound", files)
    entry_points.write(manifest, sources=(entry_points.react_router,), runner=runner_for({".": answer("framework")})[1])
    assert [g for g in flows.cached_links(manifest, [])["gaps"] if g["site"].startswith("app/root.tsx")]


def test_the_path_of_a_route_is_the_path_of_its_ancestors_and_its_own(tmp_path):
    record, _, _ = read(tmp_path, project("framework"))
    paths = {r["site"].split(":")[0]: r["path"] for r in record["bound"]}
    assert paths["app/routes/shop/checkout.tsx"] == "/checkout"  # under a layout with no path
    assert paths["app/routes/nested/child.tsx"] == "/nested/child"  # under a layout with one
    assert paths["app/routes/api/pay.ts"] == "/api/pay"  # one path of two segments
    assert paths["app/routes/blog.tsx"] == "/:lang?/blog" and paths["app/routes/docs.tsx"] == "/docs/*"  # as the tool writes them


def test_the_schema_of_a_route_is_its_path_with_each_parameter_as_one_and_none_for_a_splat_or_an_optional_segment(tmp_path):
    record, _, _ = read(tmp_path, project("framework"))
    schemas = {r["path"]: r["schema"] for r in record["bound"]}
    assert schemas["/orders/:id"] == "/orders/{}" and schemas["/users/:id/edit"] == "/users/{}/edit" and schemas["/about"] == "/about"
    assert schemas["/"] == "/" and schemas["/:lang?/blog"] is None and schemas["/docs/*"] is None  # several schemas: a gap of the links
    assert entry_points.react_router._schema("/files/about?") is None


def test_a_path_that_begins_with_a_slash_is_the_whole_path_of_the_route_and_of_what_is_under_it(tmp_path):
    """Measured on Modal (`results/absolute-child.json`, `routes.ts` nests `/users/:id` under `users`): the tool prints the path as
    written, and React Router's own rule is that an absolute child path is the whole path (`users` > `/users/:id` is `/users/:id`,
    not `/users/users/:id`); a child of that route is under the whole path (`details` > `/users/:id/details`)."""
    files = project("framework", **{"app/routes.ts": "// users > /users/:id > details, users > /users/new, /about: see the recorded answer\n"})
    record, gaps, _ = read(tmp_path, files, "absolute-child")
    paths = {r["site"].split(":")[0]: r["path"] for r in record["bound"]}
    assert gaps == []
    assert paths["app/routes/users/user.tsx"] == "/users" and paths["app/routes/users/edit.tsx"] == "/users/:id"
    assert paths["app/routes/nested/child.tsx"] == "/users/:id/details"  # a relative child under an absolute one
    assert paths["app/routes/hello.tsx"] == "/users/new" and paths["app/routes/about.tsx"] == "/about"  # one nested, one at the top


def test_an_absolute_child_that_does_not_start_with_its_parent_s_path_is_given_as_the_tool_prints_it(tmp_path):
    """React Router's rule is that it must (`/elsewhere` under `other` is invalid), and the tool does not enforce it (Modal,
    `results/absolute-child-elsewhere.json`: exit 0 and the path as written): this reader does not repeat the framework's check."""
    record, gaps, _ = read(tmp_path, project("framework"), "absolute-child-elsewhere")
    paths = {r["site"].split(":")[0]: r["path"] for r in record["bound"]}
    assert gaps == [] and paths["app/routes/docs.tsx"] == "/other" and paths["app/routes/legacy.jsx"] == "/elsewhere"


def test_two_routes_of_one_module_are_two_rows_with_their_own_paths(tmp_path):
    record, _, _ = read(tmp_path, project("framework"))
    hello = [(r["path"], r["site"]) for r in record["bound"] if r["site"].startswith("app/routes/hello.tsx")]
    assert sorted(hello) == [("/en/hello", "app/routes/hello.tsx:1"), ("/it/hello", "app/routes/hello.tsx:1")]


def test_the_file_convention_of_flat_routes_is_the_routes_the_tool_prints(tmp_path):
    files = project("flat")
    record, gaps, _ = read(tmp_path, files, "flat")
    routes = "app/routes/"
    assert gaps == []
    assert sorted({(r["path"], r["shape"], r["site"].split(":")[0]) for r in record["bound"]}) == sorted([
        ("/", "layout", "app/root.tsx"), ("/:lang?/docs", "route", routes + "($lang).docs.tsx"),
        ("/api/pay", "route", routes + "api.pay.ts"), ("/files/*", "route", routes + "files.$.tsx"),
        ("/", "index", routes + "_index.tsx"), ("/", "layout", routes + "_auth.tsx"),
        ("/login", "route", routes + "_auth.login.tsx"), ("/about", "route", routes + "about.tsx"),
        ("/blog", "route", routes + "blog.tsx"), ("/blog", "index", routes + "blog._index.tsx"),
        ("/blog/:slug", "route", routes + "blog.$slug.tsx"), ("/shop", "route", routes + "shop/route.tsx")])
    assert starts(record, "/api/pay") == {"action": "action"}  # a resource route here too
    assert starts(record, "/blog/:slug") == {"loader": "loader", "default": "Post"}


@pytest.mark.parametrize("name, tool", [("remix", "remix"), ("remix-vite", "remix")])
def test_remix_prints_the_same_tree_with_its_own_command_classic_or_vite(tmp_path, name, tool):
    files = project(name)
    record, gaps, asked = read(tmp_path, files, name)
    assert gaps == [] and [c["argv"] for c in asked] == [[*LIMIT, "npx", "--no-install", tool, "routes", "--json"]]
    assert starts(record, "/custom/:id") == {"default": "Custom"}  # the route remix.config.js or vite.config.ts adds
    assert [(r["site"]) for r in record["bound"] if r["path"] == "/custom/:id"] == [at(files, "app/custom.tsx", "function Custom")]
    assert starts(record, "/api/pay") == {"action": "action"} and starts(record, "/blog/:slug") == {"loader": "loader", "default": "Post"}
    assert {r["path"] for r in record["bound"]} == {"/", "/login", "/blog/:slug", "/api/pay", "/about", "/custom/:id"}


# ------------------------------------------------------------------------- what the tool does not say

def test_a_file_the_tool_names_and_the_snapshot_does_not_hold_is_a_gap_and_no_candidate_and_the_other_routes_are_read(tmp_path):
    files = project("framework", **{"app/routes/about.tsx": None})
    record, [gap], _ = read(tmp_path, files, "file-missing")
    assert (gap["kind"], gap["path"]) == ("outside_snapshot", "app/routes/about.tsx")
    assert "/about" in gap["detail"] and "no file" in gap["detail"]
    assert not [r for r in record["bound"] if r["path"] == "/about"]
    assert starts(record, "/checkout") == {"loader": "loader", "action": "action", "default": "Checkout"}


def src_project(**changes) -> dict[str, str]:
    """The `framework` fixture with its app directory at `src` (`appDirectory: "src"`), as `app-directory-src` ran it."""
    files = {rel.replace("app/", "src/", 1) if rel.startswith("app/") else rel: text for rel, text in project("framework").items()}
    return {**files, **changes}


def test_a_project_whose_app_directory_is_not_app_is_one_gap_naming_the_cause_and_no_candidate(tmp_path):
    """The tool prints each file relative to the app directory and does not name it (Modal, `app-directory-src`: the same
    paths for `appDirectory: "src"`): this reader takes the default one, and names why it reads nothing when the root route's
    file, the one the tool always prints first, is not under it."""
    record, [gap], _ = read(tmp_path, src_project(), "app-directory-src")
    assert (gap["kind"], gap["path"]) == ("model_partial", ".")
    assert "app directory" in gap["detail"] and "app/root.tsx" in gap["detail"] and "appDirectory" in gap["detail"]
    assert "framework_entries" not in record


def test_a_file_that_happens_to_be_under_app_does_not_make_a_project_with_another_app_directory_readable(tmp_path):
    """With `appDirectory: "src"` the files the tool names are `routes/about.tsx` and the like: one that is also under `app/`
    (a leftover, a second app) must not be read as the route's own. The root route's file is the proof of the directory."""
    stray = {"app/routes/about.tsx": "export default function Stray() { return null; }\n"}
    record, [gap], _ = read(tmp_path, src_project(**stray), "app-directory-src")
    assert (gap["kind"], gap["path"]) == ("model_partial", ".") and "app/root.tsx" in gap["detail"]
    assert "framework_entries" not in record


@pytest.mark.parametrize("name, cause", [
    ("routes-ts-throws", "routes.ts needs a database"), ("routes-ts-broken", "Expected \")\" but found end of file"),
    ("routes-ts-absent", "Route config file not found")])
def test_a_command_that_fails_is_the_folder_s_gap_with_the_cause_the_tool_wrote_first(tmp_path, name, cause):
    record, [gap], _ = read(tmp_path, project("framework"), name)
    assert (gap["kind"], gap["path"]) == ("model_failed", ".")
    assert "exited with 1" in gap["detail"] and cause in gap["detail"] and "react-router routes --json" in gap["detail"]
    assert "framework_entries" not in record


def test_a_command_the_time_limit_ended_is_the_folder_s_gap_saying_how_long_it_ran_and_no_candidate(tmp_path):
    """Modal (`hang` of `answers.json`): a `routes.ts` that waits for something that never comes, run under `timeout --kill-after`, is
    ended with exit 124 and leaves no process of the command; 137 is `timeout`'s own code for the command it had to kill."""
    assert ANSWERS["hang"]["returncode"] == 124
    for name, answered in (("recorded", ANSWERS["hang"]), ("killed", {**ANSWERS["hang"], "returncode": 137})):
        record, [gap], _ = read(tmp_path / name, project("framework"), answers={".": {**answered, "root": "/work"}})
        assert (gap["kind"], gap["path"]) == ("model_failed", ".")
        assert "did not end in 300 seconds" in gap["detail"] and "react-router routes --json" in gap["detail"], name
        assert "exited with" not in gap["detail"] and "framework_entries" not in record


def test_a_project_that_declares_the_command_and_has_not_installed_it_is_a_gap_that_says_it_could_not_be_found(tmp_path):
    record, [gap], asked = read(tmp_path, project("framework"), "not-installed")
    assert gap["kind"] == "model_failed" and "ENOTCACHED" in gap["detail"] and "react-router" in gap["detail"]
    assert asked[0]["env"] == {"npm_config_offline": "true"}  # npm asks no registry: it fails at once and says what it could not find


def test_an_output_that_is_no_json_of_the_known_layout_is_a_gap_and_no_candidate(tmp_path):
    for n, stdout in enumerate(("not json", '{"routes": []}', '[{"id": "root"}]', '[{"file": 3}]')):
        record, [gap], _ = read(tmp_path / f"case{n}", project("framework"), answers={
            ".": {"root": "/work", "returncode": 0, "stdout": stdout, "stderr": ""}})
        assert gap["kind"] == "model_failed" and "no JSON of the known layout" in gap["detail"], stdout
        assert "framework_entries" not in record


def test_a_failure_with_a_long_message_keeps_both_ends_of_it(tmp_path):
    long = {"root": "/work", "returncode": 1, "stdout": "", "stderr": "first words " + "x" * 2000 + " last words"}
    _, [gap], _ = read(tmp_path, project("framework"), answers={".": long})
    assert "first words" in gap["detail"] and "last words" in gap["detail"] and len(gap["detail"]) < 1000


def test_a_route_module_that_exports_none_of_what_a_route_starts_is_a_row_with_a_gap_naming_what_was_looked_for(tmp_path):
    record, _, _ = read(tmp_path, project("framework", **{"app/routes/blog.tsx": "export const handle = {};\n"}))
    [row] = [r for r in record["bound"] if r["path"] == "/:lang?/blog"]
    assert row["symbol"] == "app/routes/blog.tsx::<module>" and row["site"] == "app/routes/blog.tsx"
    assert all(name in row["gap"] for name in EXPORTS)


OVERLOADED = ("export function loader(a: string): string;\nexport function loader(a: number): number;\n"
              "export function loader(a: any) { return a; }\n")  # three records of one export name in the snapshot
BOTH = "export const action = () => 1;\nexport type action = { x: number };\nexport const loader = () => 2;\n"  # a value and a type of one name


def test_the_snapshot_tells_an_export_that_is_missing_from_one_that_is_made_twice(tmp_path):
    """`exported_target` gave one reason for both (`export-missing-or-ambiguous`), so a route module that makes an export twice
    (a TypeScript overload, a `const` and a `type` of one name) lost it without a word."""
    import semantic_store
    from snapshot_store import open_snapshot
    _, manifest = manifest_of(tmp_path, {"package.json": "{}\n", "r/overload.ts": OVERLOADED + "export const POST = () => 1;\n", "r/both.ts": BOTH})
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        resolver = semantic_store._Resolver(db)
        assert resolver.exported_target("r/overload.ts", "loader") == (None, "export-ambiguous")
        assert resolver.exported_target("r/both.ts", "action") == (None, "export-ambiguous")
        assert resolver.exported_target("r/overload.ts", "action") == (None, "export-missing")
        assert resolver.exported_target("r/both.ts", "default") == (None, "export-missing")
        identity, reason = resolver.exported_target("r/overload.ts", "POST")
        assert identity and reason is None


def test_an_export_a_route_module_makes_twice_is_a_gap_naming_the_cause_and_one_it_does_not_make_is_not(tmp_path):
    record, _, _ = read(tmp_path, project("framework", **{"app/routes/api/health.ts": OVERLOADED, "app/routes/api/pay.ts": BOTH}))
    [health] = [r for r in record["bound"] if r["path"] == "/api/health"]
    assert health["symbol"] == "app/routes/api/health.ts::<module>" and "loader: export-ambiguous" in health["gap"]
    assert "default" not in health["gap"]  # the exports it does not make are not what it says: they are what a route does not need
    pay = [r for r in record["bound"] if r["path"] == "/api/pay"]
    assert {r["handler"] for r in pay if r.get("handler")} == {"loader"}  # the one it makes once is read, beside the gap
    [gap] = [r for r in pay if r.get("gap")]
    assert "action: export-ambiguous" in gap["gap"] and "loader" not in gap["gap"]


# ------------------------------------------------------------- what runs, and where

def test_only_the_packages_that_install_the_command_start_it_and_one_that_is_only_the_library_starts_nothing(tmp_path):
    from snapshot_store import open_snapshot
    count = []

    def asked(manifest_text):
        _, manifest = manifest_of(tmp_path / f"case{len(count)}", {"package.json": manifest_text})
        count.append(1)
        with open_snapshot(manifest) as store:
            return entry_points.react_router.commands(premap.Context(manifest, store))
    assert asked('{"dependencies": {"react-router": "7.0.0", "react-router-dom": "7.0.0"}}') is None  # library mode: no command lists its routes
    assert asked('{"dependencies": {"react-router": "7.0.0"}, "devDependencies": {"@react-router/node": "7.0.0"}}') is None
    assert asked('{"devDependencies": {"@react-router/dev": "7.0.0"}}')[0]["argv"] == [*LIMIT, "npx", "--no-install", "react-router", "routes", "--json"]
    assert asked('{"dependencies": {"@remix-run/dev": "2.17.5"}}')[0]["argv"] == [*LIMIT, "npx", "--no-install", "remix", "routes", "--json"]
    assert asked("{") is None and asked('["@react-router/dev"]') is None  # `npm-files` reports a manifest that is not JSON


def test_each_package_json_declaring_the_command_is_one_run_in_its_folder(tmp_path):
    from snapshot_store import open_snapshot
    files = {"apps/a/package.json": '{"devDependencies": {"@react-router/dev": "7.18.6"}}\n',
             "apps/b/package.json": '{"dependencies": {"@remix-run/dev": "2.17.5"}}\n',
             "apps/c/package.json": '{"dependencies": {"react-router": "7.18.6"}}\n'}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        asked = entry_points.react_router.commands(premap.Context(manifest, store))
    assert [(c["cwd"], c["argv"][-3]) for c in asked] == [("apps/a", "react-router"), ("apps/b", "remix")]
    assert all(c["tool"] == "react-router" and c["network"] == "none" and c["env"] == {"npm_config_offline": "true"} for c in asked)


def test_the_folders_share_the_time_so_that_folders_that_all_hang_do_not_take_the_whole_run(tmp_path):
    """One run lasts 1800 seconds and holds the restore of the packages: a limit of 300 seconds for each of six folders that hang
    would be the whole run again. Up to three folders have 300 each, more share 900, none has less than 10."""
    from snapshot_store import open_snapshot
    assert [entry_points.react_router.seconds(n) for n in (1, 3, 6, 90, 100)] == [300, 300, 150, 10, 10]
    files = {f"apps/{name}/package.json": '{"devDependencies": {"@react-router/dev": "7.18.6"}}\n' for name in "abcdef"}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        asked = entry_points.react_router.commands(premap.Context(manifest, store))
    assert [c["argv"][:3] for c in asked] == [["timeout", "--kill-after=10", "150"]] * 6
    record, [gap], _ = read(tmp_path / "hang", project("framework"), answers={".": {**ANSWERS["hang"], "root": "/work"}})
    assert "did not end in 300 seconds" in gap["detail"]  # the seconds the command was given, told from its own argument


def test_the_setup_installs_no_package_the_project_s_own_command_is_in_the_packages_the_restore_installs(tmp_path):
    import preparation
    from snapshot_store import open_snapshot
    project_dir, manifest = manifest_of(tmp_path, {"package.json": '{"devDependencies": {"@react-router/dev": "7.18.6"}}\n'})
    with open_snapshot(manifest) as store:
        asked = entry_points.react_router.commands(premap.Context(manifest, store))
    spec = container_runner.TOOLS["react-router"]
    assert spec["setup"] == [container_runner.UNPACK["node"]]  # Node only
    assert (spec["restores"], spec["runs_on"]) == ("node", ("node",))
    calls, fake = recorder()
    with patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)(asked)
    first, *rest = calls[0]["commands"]
    plan = preparation.node_prepare(["package.json"], lambda rel: (project_dir / rel).read_text(encoding="utf-8"))
    assert f"( {plan['lines'][0]} )" in first["argv"][-1] and "install -g" not in first["argv"][-1]
    assert [c["network"] for c in rest] == ["none"]  # the restore has the registries; the command has no network


def program(args) -> str:
    """The program a command starts: the first word of a command line, the first item (a path may hold spaces) of an argument list."""
    return Path(str(args[0] if isinstance(args, (list, tuple)) else args.split()[0])).stem


class Host:
    """This machine as a project's own code would find it: a folder of the project where every file starts something if it is run,
    fake `node`, `npx`, `npm`, `react-router`, `remix` and `daodan-react-router` first on the PATH (`name` and `name.cmd`, each writes a
    mark), and every way to start a process recorded in `started` and, but for Daodan's own `git`, refused: the real tool never
    starts here, whatever a change of the source asks for. The signs are ES modules, as the fixture's `package.json` says
    (`"type": "module"`), and the shebang names `node`, so they would write their mark if they ran."""

    def __init__(self, tmp_path, monkeypatch):
        import os
        import subprocess
        self.marks, self.tools, self.started = tmp_path / "marks", tmp_path / "bin", []
        self.marks.mkdir()
        self.tools.mkdir()
        for name in ("node", "npx", "npm", "react-router", "remix", "daodan-react-router"):
            (self.tools / name).write_text(f'#!/bin/sh\necho "$0 $*" >> "{self.marks.as_posix()}/{name}"\n', encoding="utf-8", newline="\n")
            (self.tools / name).chmod(0o755)
            (self.tools / f"{name}.cmd").write_text(f'@echo %0 %* >> "{self.marks}\\{name}"\r\n', encoding="utf-8", newline="")
        monkeypatch.setenv("PATH", f"{self.tools}{os.pathsep}{os.environ['PATH']}")
        sign = f'import {{ writeFileSync }} from "node:fs";\nwriteFileSync("{self.marks.as_posix()}/loaded", "ran");\n'
        assert json.loads(project("framework")["package.json"])["type"] == "module"
        self.project, self.manifest = manifest_of(tmp_path, project("framework", **{
            "app/routes.ts": sign, "react-router.config.ts": sign, "vite.config.ts": sign}))
        bin_file = self.project / "node_modules/.bin/react-router"
        bin_file.parent.mkdir(parents=True)
        bin_file.write_text("#!/usr/bin/env node\n" + sign, encoding="utf-8", newline="\n")
        bin_file.chmod(0o755)
        real = subprocess.Popen

        def popen(args, *given, **options):
            self.started.append(args)
            if program(args) != "git":
                raise FileNotFoundError(f"refused by the test: {args}")
            return real(args, *given, **options)

        def system(command, *given):
            self.started.append(command)
            return 1  # the shell's own failure: nothing ran

        def popen_pipe(command, *given, **options):
            self.started.append(command)
            raise OSError("refused by the test")
        monkeypatch.setattr(subprocess, "Popen", popen)  # `run`, `call` and `check_output` start theirs through it
        monkeypatch.setattr(os, "system", system)
        monkeypatch.setattr(os, "popen", popen_pipe)

    def write(self, runner):
        return entry_points.write(self.manifest, sources=(entry_points.react_router,), runner=runner)

    def check(self):
        """What must hold of this machine after the source ran: Daodan's own `git` (hooks and fsmonitor off) is the only process
        that started, and nothing the project holds or the PATH offers left a mark."""
        assert {program(a) for a in self.started} <= {"git"}, f"started on this machine: {self.started}"
        assert all("core.hooksPath=/dev/null" in a and "core.fsmonitor=false" in a for a in self.started)
        assert sorted(path.name for path in self.marks.iterdir()) == []


def test_no_engine_carries_the_reason_and_nothing_of_the_project_runs_on_this_machine(tmp_path, monkeypatch):
    host = Host(tmp_path, monkeypatch)
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        record = host.write(container_runner.runner(host.manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record
    host.check()
    host.started.clear()  # and with an engine's answer in hand, reading it starts nothing of the project either
    record = host.write(runner_for({".": answer("framework")})[1])
    assert record["framework_entries"]
    host.check()


@pytest.mark.parametrize("how", ["os.system", "subprocess.run", "subprocess.Popen with a shell", "os.popen"])
def test_the_check_of_that_test_fails_when_the_source_starts_a_command_of_the_project_on_this_machine(tmp_path, monkeypatch, how):
    """The mutation of the source that the test must catch: `commands` starts the project's own command here. The check fails on
    what the spies recorded (the fakes on the PATH are a second proof where the system runs them)."""
    import os
    import subprocess
    host = Host(tmp_path, monkeypatch)
    argv = ["npx", "--no-install", "react-router", "routes", "--json"]
    start = {"os.system": lambda: os.system(" ".join(argv)), "subprocess.run": lambda: subprocess.run(argv, cwd=host.project),
             "subprocess.Popen with a shell": lambda: subprocess.Popen(" ".join(argv), shell=True, cwd=host.project),
             "os.popen": lambda: os.popen(" ".join(argv))}[how]
    commands = entry_points.react_router.commands

    def mutated(context):
        try:
            start()
        except OSError:
            pass  # the refusal of the spy: the call is recorded
        return commands(context)
    monkeypatch.setattr(entry_points.react_router, "commands", mutated)
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        host.write(container_runner.runner(host.manifest))
    with pytest.raises(AssertionError, match="started on this machine"):
        host.check()


def test_a_snapshot_with_no_package_json_declaring_the_command_runs_nothing(tmp_path):
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"react-router": "7.18.6"}}\n', "app/root.tsx": "export default null;\n"})
    record = entry_points.write(manifest, sources=(entry_points.react_router,), runner=lambda commands: 1 / 0)
    assert record["sources"][0]["state"] == "not_needed" and "framework_entries" not in record


# --------------------------------------------------- the registry of the sources that give framework entries

def test_the_sources_that_give_entries_of_their_own_are_one_tuple_and_each_is_a_registered_model_source():
    import entries
    assert {entry_points.nextjs, entry_points.react_router} <= set(entry_points.FRAMEWORK_SOURCES)  # one tuple; each framework's source adds its name
    for source in entry_points.FRAMEWORK_SOURCES:
        assert source in entry_points.SOURCES and hasattr(source, "commands") and callable(source.from_record)
        assert source.NAME in entries.QUERIES and source.NAME in container_runner.TOOLS  # the table is keyed by the source's name


def test_the_evidence_reads_the_rows_and_the_gaps_of_every_source_of_the_tuple(tmp_path):
    from entry_points.flow_entries import evidence
    from test_codebase_map_premap_nextjs import SHOP, VALIDATOR
    files = {**SHOP, **{f"web/{rel}": text for rel, text in project("framework").items()}}
    _, manifest = manifest_of(tmp_path, files)

    def run(commands):
        if commands[0]["tool"] == "next":
            return [{"root": "/work", "returncode": 0, "stderr": "", "stdout": "" if c["argv"][0] == "npx" else VALIDATOR} for c in commands]
        return [{**answer("framework")} for _ in commands]
    entry_points.write(manifest, sources=(entry_points.nextjs, entry_points.react_router), runner=run)
    rows, gaps = evidence(manifest)
    assert {r["reader"] for r in rows} >= {"next", "react-router"}
    assert {r["path"] for r in rows if r["reader"] == "react-router"} >= {"/checkout", "/api/pay"}
    assert [g for g in gaps if g.get("source") == SOURCE] == []  # the two routes the snapshot cannot bind are rows with a gap, not gaps of the source


def test_a_source_added_to_the_tuple_reaches_the_evidence_and_the_key_of_the_cached_links_with_no_other_line(tmp_path, monkeypatch):
    import flows
    from pathlib import Path as Reader
    from entry_points.flow_entries import evidence
    fake_file = tmp_path / "svelte_like.py"
    fake_file.write_text("# a source of another framework\n", encoding="utf-8")
    row = {"reader": "svelte-like", "shape": "page", "site": "src/routes/+page.svelte", "symbol": "src/routes/+page.svelte::<module>",
           "path": "/", "sources": ["svelte-like@v1"]}
    fake = types.SimpleNamespace(NAME="svelte-like", __file__=str(fake_file), from_record=lambda report: (
        [row], [{"kind": "model_partial", "path": "x", "detail": "gap of the fake", "source": "svelte-like@v1"}]))
    _, manifest = manifest_of(tmp_path / "proj", {"package.json": "{}\n"})
    premap.write(manifest, sources=())
    entry_points.write(manifest, sources=())
    monkeypatch.setattr(entry_points, "FRAMEWORK_SOURCES", (*entry_points.FRAMEWORK_SOURCES, fake))
    rows, gaps = evidence(manifest)
    assert row in rows and any(g["detail"] == "gap of the fake" for g in gaps)
    seen = []
    with patch.object(Reader, "read_bytes", autospec=True, side_effect=lambda self: seen.append(self.name) or b""):
        flows._links_reader_digest.__wrapped__()
    assert {"nextjs.py", "react_router.py", "svelte_like.py", "angular.py", "angular_templates.mjs", "binder.py"} <= set(seen)


# --------------------------------------------------------------------- what reaches the links

@pytest.fixture(scope="module")
def made(tmp_path_factory):
    _, manifest = manifest_of(tmp_path_factory.mktemp("react-router-links"), project("framework"))
    entry_points.write(manifest, sources=(entry_points.react_router,), runner=runner_for({".": answer("framework")})[1])
    return manifest


@pytest.fixture(scope="module")
def links(made):
    import flows
    return flows.cached_links(made, [])


def test_each_export_a_route_starts_is_an_entry_on_its_function_and_no_route_is_offered_by_it(links):
    found = {(e["path"], e["symbol"].split("::")[1], e["kind"], e["handler_source"]) for e in links["entries"]
             if e["reader"] == "react-router" and not e.get("gap")}
    assert {("/checkout", "loader", "rotta", "react-router"), ("/checkout", "action", "rotta", "react-router"),
            ("/checkout", "Checkout", "rotta", "react-router"), ("/api/pay", "action", "rotta", "react-router"),
            ("/orders/:id", "loader", "rotta", "react-router"), ("/about", "About", "rotta", "react-router")} <= found
    assert links["routes"]["offered"] == 0 and links["routes"]["linked"] == 0  # entries, not offered routes: the tool gives no method
    assert "declared route None /about: it has no method" in {g["reason"] for g in links["gaps"]}  # as Django's, with the cause


def test_the_routes_the_snapshot_cannot_bind_are_gaps_of_the_links_with_what_was_looked_for(links):
    reasons = {g["site"]: g["reason"] for g in links["gaps"] if g["site"].startswith(("app/routes/docs.tsx", "app/routes/legacy.jsx"))}
    assert "default" in reasons["app/routes/docs.tsx"] and "reexport-unsupported" in reasons["app/routes/legacy.jsx"]


def test_a_layout_is_a_candidate_of_no_kind_that_starts_a_flow_and_so_no_entry(made, links):
    from entry_points.flow_entries import evidence
    [layout] = [r for r in evidence(made)[0] if r["site"] == "app/routes/shop/layout.tsx" and r["shape"] == "layout"]
    assert (layout["reader"], layout["kind"]) == ("react-router", LAST)
    assert not [e for e in links["entries"] if e["site"] == "app/routes/shop/layout.tsx"]


def test_the_shapes_of_the_source_are_in_the_registry_so_no_question_is_asked_for_them(made):
    import entries
    from entry_points.flow_entries import evidence
    rules = entries.registry_rules([r for r in evidence(made)[0] if r["reader"] == "react-router"])
    # the module rows of the root's and of a layout's data functions are rows of the pre-map now (`exports_optional`)
    assert {(r["shape"], r["entry"]) for r in rules} == {("route", "rotta"), ("index", "rotta"), ("layout", LAST),
                                                         ("root-data", "rotta"), ("layout-data", "rotta")}
    rules = entries.registry_rules([{"reader": "react-router", "shape": shape, "kind": "rotta"} for shape in ("root-data", "layout-data")])
    assert {(r["shape"], r["entry"]) for r in rules} == {("root-data", "rotta"), ("layout-data", "rotta")}


def test_the_premap_the_whole_pipeline_wrote_on_modal_holds_the_rows_of_the_recorded_answer(tmp_path):
    """`results/pipeline-scan.json`: the `scan` step in Daodan's container, with the packages restored from the lockfile and the
    command run with no network, wrote the same 23 rows that the recorded answer gives here, and no gap of the source; the 19
    entries are the rows on a function, and Noir's 25 endpoints in the same files stay gaps of their own. The run was recorded
    before the `schema` and the note on an anonymous default, readings of the same answer that the recording does not hold."""
    scan = json.loads((BENCHMARK.parent / "results/pipeline-scan.json").read_text(encoding="utf-8"))
    record, _, _ = read(tmp_path, project("framework"))
    from languages.semantic import ANONYMOUS_DEFAULT

    def same(row: dict) -> dict:  # the recording predates the schema and the binder's note on an anonymous default (T1.C.6),
        row = {key: value for key, value in row.items() if key not in ("sources", "schema")}  # which names the export it
        if "gap" in row:  # could not read instead of every export the framework looks for
            row["gap"] = row["gap"].partition(" from: ")[0]
        return row
    assert [same(row) for row in scan["framework_entries"]] == [same(row) for row in record["bound"]]
    assert any(ANONYMOUS_DEFAULT in row.get("gap", "") for row in record["bound"])
    assert len(scan["framework_entries"]) == 23 and scan["source_gaps"] == []
    assert scan["sources"]["react-router"]["state"] == "ran" and scan["sources"]["next"]["state"] == "not_needed"
    assert scan["links"]["entries"] == {"react-router rotta": 19} and scan["links"]["routes"]["offered"] == 0
    assert scan["links"]["gaps"] == {"noir: no unique snapshot handler at its site": 25, "react-router: no function found for the exports": 2}


# ---------------------------------------------------- the library: routes written in code, no command lists them

def library_gaps(tmp_path, packages_by_file):
    """The gaps the source tells for a project whose `package.json` files declare these dependencies, from the pre-map's
    own `packages` (what `modules.py` read of each manifest) and through the evidence the flows read."""
    from entry_points.flow_entries import evidence
    files = {rel: json.dumps({"dependencies": {name: "1.0.0" for name in names}}) for rel, names in packages_by_file.items()}
    _, manifest = manifest_of(tmp_path, files)
    record = premap.write(manifest, sources=(premap.module_graph,))
    entry_points.write(manifest, sources=(entry_points.react_router,), runner=lambda commands: [
        {"root": "/work", "returncode": 1, "stdout": "", "stderr": "no tool here"} for _ in commands])
    library = lambda found: [g for g in found if g.get("source") == SOURCE and "routes written in code" in g["detail"]]  # noqa: E731
    return library(evidence(manifest)[1]), library(entry_points.react_router.stated_gaps(record))


@pytest.mark.parametrize("names", [("react-router-dom", "react"), ("react-router",), ("react-router", "react-router-dom")])
def test_a_project_that_declares_only_the_library_has_a_gap_naming_the_file_and_the_cause_and_runs_nothing(tmp_path, names):
    gaps, recorded = library_gaps(tmp_path, {"web/package.json": names})
    [gap] = gaps  # one for the file, not one for each package it declares
    assert (gap["kind"], gap["path"]) == ("model_partial", "web/package.json") and recorded == gaps
    assert "routes written in code" in gap["detail"] and "no official tool lists them" in gap["detail"]
    assert "@react-router/dev" in gap["detail"] and "exploration" in gap["detail"] and "react-router" in gap["detail"]


def test_a_manifest_that_declares_the_command_has_no_library_gap_and_a_manifest_that_declares_neither_has_none(tmp_path):
    gaps, _ = library_gaps(tmp_path, {"a/package.json": ("react-router", "@react-router/dev"), "b/package.json": ("react-router-dom", "@remix-run/dev"),
                                      "c/package.json": ("react", "vite")})
    assert gaps == []
    gaps, _ = library_gaps(tmp_path / "two", {"web/package.json": ("react-router-dom",), "admin/package.json": ("react-router",),
                                              "api/package.json": ("@react-router/dev",)})
    assert sorted(g["path"] for g in gaps) == ["admin/package.json", "web/package.json"]


def test_the_library_gap_needs_no_container_and_no_command(tmp_path):
    from snapshot_store import open_snapshot
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"react-router-dom": "6.30.4"}}\n'})
    with open_snapshot(manifest) as store:
        assert entry_points.react_router.commands(premap.Context(manifest, store)) is None
    stated = premap.write(manifest, sources=(premap.module_graph,))
    record = entry_points.write(manifest, sources=(entry_points.react_router,), runner=lambda commands: 1 / 0)
    assert [s["state"] for s in record["sources"] if s["source"].startswith("react-router@")] == ["not_needed"]
    assert len(entry_points.react_router.stated_gaps(stated)) == 1


def test_a_premap_made_before_the_source_is_stale(tmp_path):
    _, manifest = manifest_of(tmp_path, project("framework"))
    premap.write(manifest, sources=())
    before = tuple(source for source in entry_points.SOURCES if source is not entry_points.react_router)
    entry_points.write(manifest, sources=before)
    assert entry_points.state(manifest, sources=before)["state"] == "fresh"
    assert entry_points.state(manifest)["state"] == "stale"


def test_a_premap_where_the_source_was_not_needed_gives_the_evidence_no_react_router_row_and_no_gap(tmp_path):
    from entry_points.flow_entries import evidence
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"react": "19.3.1"}}\n'})
    entry_points.write(manifest, sources=(entry_points.react_router,), runner=lambda commands: 1 / 0)
    rows, gaps = evidence(manifest)
    assert [r for r in rows if r["reader"] == "react-router"] == [] and [g for g in gaps if g.get("source") == SOURCE] == []


def test_the_premap_rows_are_the_modules_with_their_exports_and_the_links_bind_them_to_the_functions(tmp_path):
    """No source binds a row (spec 8.13, point 2): the pre-map row is the module with the exports its table says start a
    function, and the links' binder puts each entry on the function the snapshot names."""
    import flows
    files = project("framework", **{"app/root.tsx": ROOT})
    _, manifest = manifest_of(tmp_path, files)
    record = entry_points.write(manifest, sources=(entry_points.react_router,), runner=runner_for({".": answer("framework")})[1])
    [checkout] = [r for r in record["framework_entries"] if r["path"] == "/checkout"]
    assert (checkout["site"], checkout["symbol"], checkout["exports"]) == (
        "app/routes/shop/checkout.tsx", "app/routes/shop/checkout.tsx::<module>", list(EXPORTS))
    assert not [r for r in record["framework_entries"] if "handler" in r or "handler_source" in r]
    [data] = [r for r in record["framework_entries"] if r["shape"] == "root-data"]
    assert data["exports_optional"] is True and data["symbol"] == "app/root.tsx::<module>"
    linked = {(e["path"], e["symbol"].split("::")[1], e["handler_source"]) for e in flows.cached_links(manifest, [])["entries"]
              if e["reader"] == "react-router"}
    assert {("/checkout", "loader", "react-router"), ("/checkout", "Checkout", "react-router"), ("/", "action", "react-router")} <= linked


def test_the_public_candidates_hold_the_entries_on_their_functions_and_the_gap_rows(made):
    """`entries._declared_rows` and `cached_syntax` (the MCP candidates, the brief) give the rows the links' binder binds, not the
    pre-map's module rows."""
    import entries
    rows = entries._declared_rows(made)
    assert {(r["path"], r["symbol"].split("::")[1], r["handler_source"]) for r in rows if r.get("handler_source")
            and r["reader"] == "react-router"} >= {("/checkout", "loader", "react-router"), ("/checkout", "Checkout", "react-router")}
    assert {r["site"] for r in rows if r.get("gap") and r["reader"] == "react-router"} == {"app/routes/docs.tsx", "app/routes/legacy.jsx"}
    assert not [r for r in rows if "exports" in r or "methods" in r]
    syntax = entries.cached_syntax(made)
    assert [c for c in syntax if c["reader"] == "react-router" and c.get("handler") == "loader" and c["path"] == "/checkout"]
