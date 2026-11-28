"""The server routes a Nuxt project's own `nuxt prepare` makes Nitro write, `.nuxt/types/nitro-routes.d.ts`, and the pages its
own `@nuxt/kit` resolves (`entry_points/nuxt_pages.mjs`), read from their output and bound to the snapshot.

The container is a fake: the answers are the ones the real commands gave on Modal for the fixtures of
`benchmarks/nuxt-routes/` (`tests/fixtures/premap/nuxt/answers.json`, recorded by that folder's `modal_probe.py --mode source`):
for each variant, the answer of `nuxt prepare`, of the `cat` of the file and of Daodan's script. The file ties each server route
to its HTTP method (the key of a handler with no method in its file name is `default`) and to the import of its handler's file; no
file `nuxt prepare` writes by default names the pages (`benchmarks/nuxt-routes/README.md`), and the script gives them with the
file each one is made from: Nuxt's own `loadNuxt` and its hook `pages:resolved`.
"""
from __future__ import annotations

import json
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from test_codebase_map_container_runner import bound, container, container_runner, manifest_of, entry_points, premap, recorder

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/nuxt-routes/fixture"
ANSWERS = json.loads((Path(__file__).parent / "fixtures/premap/nuxt/answers.json").read_text(encoding="utf-8"))
SOURCE = "nuxt@daodan/premap/v3"  # v3: the route's `schema`, a page is `page`
GAP = "no function found for the exports the framework starts {} from: default: anonymous default export is unresolved"
HANDLERS = (  # what the file names for the fixture: (route, method, file); None is a handler with no method in its file name
    ("/api/files/**:path", "GET", "server/api/files/[...path].get.ts"),
    ("/api/health", None, "server/api/health.ts"),
    ("/api/hello", "GET", "server/api/hello.get.ts"),
    ("/api/plain", "GET", "server/api/plain.get.ts"),
    ("/api/users/:id", "DELETE", "server/api/users/[id].delete.ts"),
    ("/api/users/:id", "GET", "server/api/users/[id].get.ts"),
    ("/api/users", "GET", "server/api/users/index.get.ts"),
    ("/api/users", "POST", "server/api/users/index.post.ts"),
    ("/feed", "GET", "server/routes/feed.get.ts"),
    ("/sitemap.xml", None, "server/routes/sitemap.xml.ts"),
    ("/api/from-config", "POST", "server/custom/config-handler.ts"),  # `nitro.handlers` of nuxt.config.ts: code of the project
)
INTERNAL = (  # the two routes Nuxt itself registers: their handlers are a package's and a virtual module, not the project's
    ("/__nuxt_error", "node_modules/@nuxt/nitro-server/dist/runtime/handlers/renderer"),
    ("/__nuxt_island/**", "server/#internal/nuxt/island-renderer"),
)


def project(name: str, **changes) -> dict[str, str]:
    files = {path.relative_to(BENCHMARK / name).as_posix(): path.read_text(encoding="utf-8")
             for path in (BENCHMARK / name).rglob("*") if path.is_file() and path.name != "package-lock.json"}
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def answer(name: str) -> tuple[dict, dict, dict]:
    """What the container answered for a variant: `nuxt prepare`, the `cat` of the file it writes, Daodan's script."""
    return tuple({"root": "/work", **one} for one in ANSWERS[name])


def pages_answer(pages, called=True, before="") -> dict:
    """What the script prints for a tree of pages: one JSON line, after what a module of the project may have printed."""
    return {"root": "/work", "returncode": 0, "stderr": "",
            "stdout": before + json.dumps({"called": called, "pages": pages}, separators=(",", ":")) + "\n"}


def page(name, path, file, *children):
    return {"name": name, "path": path, "file": file, "children": list(children)}


def runner_for(answers):
    """A runner that answers each command from `answers`, folder -> (prepare answer, cat answer, script answer)."""
    asked = []
    index = {"npx": 0, "cat": 1, "timeout": 2}

    def run(commands):
        asked.extend(commands)
        return [answers[c["cwd"]][index[c["argv"][0]]] for c in commands]
    return asked, run


def read(tmp_path, files, name="nuxt3", answers=None):
    _, manifest = manifest_of(tmp_path, files)
    asked, run = runner_for(answers or {".": answer(name)})
    record = entry_points.write(manifest, sources=(entry_points.nuxt,), runner=run)
    record["bound"] = bound(manifest, record)
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], asked


def at(files, file, needle):
    """`file:line` of the first line of the file that holds `needle`: the position is checked against the text itself."""
    return f"{file}:{next(n for n, line in enumerate(files[file].split(chr(10)), 1) if needle in line)}"


def _order(row):
    return tuple("" if value is None else value for value in row)


def rows(record, shape="server-route"):
    """Each row of a shape: route, method, site, symbol, the export that starts it (None at the file), the gap."""
    return sorted(((r["path"], r.get("method"), r["site"], r["symbol"], r.get("handler"), r.get("gap"))
                   for r in record["bound"] if r["shape"] == shape), key=_order)


NUXT3_PAGES = (  # the routes of `fixture/nuxt3`, each with the file Nuxt made it from (`from-hook` is made from `about.vue` too)
    ("/about", "pages/about.vue"), ("/", "pages/index.vue"), ("/quokka-path", "pages/legacy.vue"), ("/parent", "pages/parent.vue"),
    ("/parent/child", "pages/parent/child.vue"), ("/foo/bar", "pages/foo/bar.vue"), ("/:slug(.*)*", "pages/[...slug].vue"),
    ("/foo", "pages/foo/index.vue"), ("/users/:id()", "pages/users/[id].vue"), ("/blog/:page?", "pages/blog/[[page]].vue"),
    ("/from-hook", "pages/about.vue"))
NUXT4_PAGES = tuple((path, "app/" + file) for path, file in NUXT3_PAGES) + (("/checkout", "app/pages/(shop)/checkout.vue"),)


def pages_expected(pages):
    """The rows of the pages: on the file, no line (the tool gives none), no method and no function, no gap."""
    return sorted(((path, None, file, f"{file}::<module>", None, None) for path, file in pages), key=_order)


def expected(files, handlers=HANDLERS):
    """The rows of the file the tool wrote: `plain.get.ts` default-exports a function the snapshot binds; the others
    default-export a call (`defineEventHandler(...)`), which no function declaration is: a row on the file with its gap."""
    out = []
    for route, method, file in handlers:
        if file == "server/api/plain.get.ts":
            out.append((route, method, at(files, file, "export default function plain"), f"{file}::plain", "default", None))
        else:
            out.append((route, method, file, f"{file}::<module>", None, GAP.format(route)))
    return sorted(out, key=_order)


# ------------------------------------------------------------------- the routes of the file the tool wrote

@pytest.mark.parametrize("name, fixture", [("nuxt3", "nuxt3"), ("nuxt4", "nuxt4"), ("nuxt4-root-layout", "nuxt4")])
def test_every_server_route_the_types_name_is_a_candidate_with_its_method_and_file_and_the_function_its_default_export_names(
        tmp_path, name, fixture):
    files = project(fixture)
    if name == "nuxt4-root-layout":  # the app's own folder moved to the root: the server's files are where they were
        files = {rel.removeprefix("app/"): text for rel, text in files.items()}
    record, gaps, asked = read(tmp_path, files, name)
    assert rows(record) == expected(files)
    assert {(r["reader"], r["shape"], r["kind"]) for r in record["bound"]} == {("nuxt", "server-route", "rotta"), ("nuxt", "page", "rotta")}
    # the two routes Nuxt registers itself name no file of the project: a gap each, with the path the tool imports
    assert sorted((g["kind"], g["path"]) for g in gaps) == sorted(("outside_snapshot", path) for _, path in INTERNAL)
    by_path = {g["path"]: g for g in gaps}
    for route, path in INTERNAL:
        assert route in by_path[path]["detail"] and "no file with that path" in by_path[path]["detail"]


def test_the_method_is_the_key_the_tool_wrote_in_capitals_and_none_where_the_file_name_gave_none(tmp_path):
    record, _, _ = read(tmp_path, project("nuxt3"))
    methods = {(r["path"], r.get("method")) for r in record["bound"]}
    assert ("/api/users", "GET") in methods and ("/api/users", "POST") in methods and ("/api/users/:id", "DELETE") in methods
    assert ("/api/health", None) in methods and ("/sitemap.xml", None) in methods
    assert not [r for r in record["bound"] if r.get("method") == "DEFAULT"]  # `default` is the tool's word for any method


def test_the_route_is_written_as_the_tool_wrote_it_and_no_path_is_derived_from_a_file_name(tmp_path):
    record, _, _ = read(tmp_path, project("nuxt3"))
    server = [r for r in record["bound"] if r["shape"] == "server-route"]
    assert {r["path"] for r in server} == {route for route, _, _ in HANDLERS}
    # `[id]` and `[...path]` of the file names are the tool's `:id` and `**:path`: only its text says so
    assert all("[" not in r["path"] for r in server)


def test_the_schema_of_a_route_has_each_parameter_as_one_and_none_where_the_route_or_page_stands_for_several(tmp_path):
    record, _, _ = read(tmp_path, project("nuxt3"))
    server = {r["path"]: r["schema"] for r in record["bound"] if r["shape"] == "server-route"}
    assert server["/api/users/:id"] == "/api/users/{}" and server["/api/files/**:path"] is None and server["/sitemap.xml"] == "/sitemap.xml"
    pages = {r["path"]: (r["schema"], r.get("page")) for r in record["bound"] if r["shape"] == "page"}
    assert pages["/users/:id()"] == ("/users/{}", True) and pages["/about"] == ("/about", True)
    assert pages["/:slug(.*)*"] == (None, True) and pages["/blog/:page?"] == (None, True)  # a catch-all and an optional page
    assert entry_points.nuxt._route_schema("/api/*/x") == "/api/{}/x" and entry_points.nuxt._route_schema("/api/**") is None


def test_a_route_that_nuxt_config_declares_in_code_is_a_row_like_the_others(tmp_path):
    record, _, _ = read(tmp_path, project("nuxt3"))
    [row] = [r for r in record["bound"] if r["path"] == "/api/from-config"]
    assert (row["method"], row["site"]) == ("POST", "server/custom/config-handler.ts")


def test_the_layouts_and_the_middleware_are_no_rows_whatever_the_page_pass_says(tmp_path):
    record, _, _ = read(tmp_path, project("nuxt3"))
    assert not [r for r in record["bound"] if r["site"].startswith(("layouts/", "middleware/", "app.vue", "server/middleware/"))]


def test_a_project_without_pages_gives_its_server_routes_all_the_same_and_the_pages_a_gap_saying_the_hook_was_not_called(tmp_path):
    bare = "export default defineNuxtConfig({ compatibilityDate: '2025-07-15', telemetry: false, devtools: { enabled: false } })\n"
    files = {rel: text for rel, text in project("nuxt3", **{"nuxt.config.ts": bare}).items() if not rel.startswith("pages/")}
    record, gaps, _ = read(tmp_path, files, "no-pages")
    handlers = tuple(h for h in HANDLERS if h[0] != "/api/from-config")  # the config that declared it is gone
    assert rows(record) == expected(files, handlers) and rows(record, "page") == []
    assert sorted(g["path"] for g in gaps if g["kind"] == "outside_snapshot") == sorted(path for _, path in INTERNAL)
    [none] = [g for g in gaps if g["kind"] == "model_partial"]
    assert none["path"] == "." and "pages:resolved" in none["detail"] and "no pages folder" in none["detail"]


# ------------------------------------------------------------------------------- the pages `loadNuxt` resolves

@pytest.mark.parametrize("name, fixture, pages", [("nuxt3", "nuxt3", NUXT3_PAGES), ("nuxt4", "nuxt4", NUXT4_PAGES)])
def test_every_page_the_script_prints_is_a_row_on_its_file_with_its_whole_path_and_the_module_as_the_symbol(tmp_path, name, fixture, pages):
    files = project(fixture)
    record, gaps, _ = read(tmp_path, files, name)
    assert rows(record, "page") == pages_expected(pages)
    assert {(r["reader"], r["kind"]) for r in record["bound"] if r["shape"] == "page"} == {("nuxt", "rotta")}
    assert not [g for g in gaps if g["kind"] != "outside_snapshot"]  # the two routes of Nuxt's own are the only gaps


def test_the_app_folder_moved_to_the_root_gives_the_same_pages_under_the_root(tmp_path):
    files = {rel.removeprefix("app/"): text for rel, text in project("nuxt4").items()}
    record, _, _ = read(tmp_path, files, "nuxt4-root-layout")
    assert rows(record, "page") == pages_expected([(path, file.removeprefix("app/")) for path, file in NUXT4_PAGES])


def test_a_route_made_from_the_same_file_as_another_is_a_row_of_its_own(tmp_path):
    record, _, _ = read(tmp_path, project("nuxt3"))
    assert {r["path"] for r in record["bound"] if r["shape"] == "page" and r["site"] == "pages/about.vue"} == {"/about", "/from-hook"}


def test_a_page_of_a_layer_is_a_row_on_its_file_when_the_snapshot_holds_it_and_a_gap_when_it_does_not(tmp_path):
    layer = {"layers/base/pages/from-layer.vue": "<template><div>layer</div></template>\n", "layers/base/nuxt.config.ts": "export default defineNuxtConfig({})\n"}
    held, gaps, _ = read(tmp_path / "held", project("nuxt3", **layer), "layer")
    assert ("/from-layer", None, "layers/base/pages/from-layer.vue", "layers/base/pages/from-layer.vue::<module>", None, None) in rows(held, "page")
    absent, gaps, _ = read(tmp_path / "absent", project("nuxt3"), "layer")
    assert "/from-layer" not in {r["path"] for r in absent["framework_entries"] if r["shape"] == "page"}
    [gap] = [g for g in gaps if g["path"] == "layers/base/pages/from-layer.vue"]
    assert gap["kind"] == "outside_snapshot" and "/from-layer" in gap["detail"] and "no file with that path" in gap["detail"]


def test_a_page_of_a_layer_of_nuxt_4_is_under_the_layers_own_app_folder(tmp_path):
    layer = {"layers/base/app/pages/from-layer.vue": "<template><div>layer</div></template>\n"}
    record, _, _ = read(tmp_path, project("nuxt4", **layer), "layer-nuxt4")
    assert ("/from-layer", None, "layers/base/app/pages/from-layer.vue", "layers/base/app/pages/from-layer.vue::<module>", None, None) \
        in rows(record, "page")
    assert len(rows(record, "page")) == len(NUXT4_PAGES) + 1


def test_a_route_with_no_file_is_a_gap_naming_it_and_the_others_are_read(tmp_path):
    record, gaps, _ = read(tmp_path, project("nuxt3"), "redirect")  # `pages.push({ name: 'old', path: '/old', redirect: '/about' })`
    assert rows(record, "page") == pages_expected(NUXT3_PAGES)
    [gap] = [g for g in gaps if g["kind"] == "model_partial"]
    assert gap["path"] == "." and "/old" in gap["detail"] and "no file" in gap["detail"]


def test_a_child_route_has_the_path_of_its_ancestors_unless_it_starts_with_a_slash_as_vue_router_reads_it(tmp_path):
    tree = [page("parent", "/parent", "pages/parent.vue",
                 page("child", "child", "pages/parent/child.vue", page("deep", "deep", "pages/parent/deep.vue")),
                 page("home", "", "pages/parent/index.vue"), page("away", "/away", "pages/parent/away.vue")),
            page("top", "top/", "pages/top.vue")]
    files = {name: "<template><div/></template>\n" for name in ("pages/parent.vue", "pages/parent/child.vue", "pages/parent/deep.vue",
                                                                  "pages/parent/index.vue", "pages/parent/away.vue", "pages/top.vue")}
    record, _, _ = read(tmp_path, {**project("nuxt3"), **files},
                        answers={".": (*answer("nuxt3")[:2], pages_answer(tree))})
    assert {(r["path"], r["site"]) for r in record["bound"] if r["shape"] == "page"} == {
        ("/parent", "pages/parent.vue"), ("/parent/child", "pages/parent/child.vue"), ("/parent/child/deep", "pages/parent/deep.vue"),
        ("/parent", "pages/parent/index.vue"), ("/away", "pages/parent/away.vue"), ("/top", "pages/top.vue")}


def test_what_a_module_prints_before_the_json_is_no_part_of_it(tmp_path):
    tree = [page("about", "/about", "pages/about.vue")]
    record, gaps, _ = read(tmp_path, project("nuxt3"), answers={
        ".": (*answer("nuxt3")[:2], pages_answer(tree, before="[nuxt-module] hello\n{\"not\": \"the answer\"}\n"))})
    assert rows(record, "page") == pages_expected([("/about", "pages/about.vue")])
    assert not [g for g in gaps if g["kind"] == "model_failed"]


def test_the_script_failing_is_a_gap_with_the_cause_it_wrote_and_the_server_routes_are_still_read(tmp_path):
    for name, cause in (("config-throws", "loadNuxt failed: nuxt.config needs a database"),
                        ("hook-file-missing", "buildNuxt failed: ENOENT"), ("not-installed", "@nuxt/kit is not installed")):
        pages = answer(name)[2]
        record, gaps, _ = read(tmp_path / name, project("nuxt3"), answers={".": (*answer("nuxt3")[:2], pages)})
        [gap] = [g for g in gaps if g["kind"] == "model_failed"]
        assert gap["path"] == "." and f"daodan-nuxt exited with {pages['returncode']}" in gap["detail"] and cause in gap["detail"], name
        assert rows(record, "page") == [] and rows(record) == expected(project("nuxt3")), name


def test_the_time_the_script_was_given_and_the_memory_of_the_run_are_in_the_gap_when_it_was_stopped(tmp_path):
    [first] = [g for g in read(tmp_path / "timeout", project("nuxt3"), "timeout")[1] if g["kind"] == "model_failed"]
    assert "did not end in 900 seconds" in first["detail"] and first["path"] == "."
    killed = {"root": "/work", "returncode": 137, "stdout": "", "stderr": ""}
    [second] = [g for g in read(tmp_path / "killed", project("nuxt3"), answers={".": (*answer("nuxt3")[:2], killed)})[1]
                if g["kind"] == "model_failed"]
    assert "exit 137" in second["detail"] and "900 seconds" in second["detail"] and f"{entry_points.nuxt.MEMORY_GB} GB" in second["detail"]
    assert entry_points.nuxt.MEMORY_GB == container_runner.TOOLS["nuxt"]["memory"]


def test_an_output_that_is_no_json_of_the_known_layout_is_a_gap_and_no_row(tmp_path):
    for text in ("", "not json\n", "[]\n", "{\"called\": true}\n", "{\"called\": true, \"pages\": [{\"path\": \"/a\"}]}\n"):
        record, gaps, _ = read(tmp_path / str(abs(hash(text))), project("nuxt3"), answers={
            ".": (*answer("nuxt3")[:2], {"root": "/work", "returncode": 0, "stdout": text, "stderr": ""})})
        [gap] = [g for g in gaps if g["kind"] == "model_failed"]
        assert "daodan-nuxt printed no JSON of the known layout" in gap["detail"], text
        assert rows(record, "page") == [], text


def test_the_script_failing_in_one_folder_is_that_folder_s_gap_and_the_other_is_still_read(tmp_path):
    files = {f"apps/{name}/{rel}": text for name in "ab" for rel, text in project("nuxt3").items()}
    record, gaps, _ = read(tmp_path, files, answers={"apps/a": (*answer("nuxt3")[:2], answer("config-throws")[2]), "apps/b": answer("nuxt3")})
    assert [(g["kind"], g["path"]) for g in gaps if g["kind"] == "model_failed"] == [("model_failed", "apps/a")]
    assert {r["site"].split("/pages/")[0] for r in record["bound"] if r["shape"] == "page"} == {"apps/b"}


# ----------------------------------------------------------------------------- what binds a route to the snapshot

def test_a_function_the_default_export_names_is_the_site_and_the_symbol_of_the_row_and_the_call_default_is_a_gap_row(tmp_path):
    files = project("nuxt3")
    record, _, _ = read(tmp_path, files)
    [bound] = [r for r in record["bound"] if r["path"] == "/api/plain"]
    assert (bound["site"], bound["symbol"], bound["handler"], bound["handler_source"]) == (
        at(files, "server/api/plain.get.ts", "export default function plain"), "server/api/plain.get.ts::plain", "default", "nuxt")
    assert "gap" not in bound
    [call] = [r for r in record["bound"] if r["path"] == "/api/hello"]
    assert call["site"] == "server/api/hello.get.ts" and call["symbol"].endswith("::<module>") and "default" in call["gap"]


def test_an_import_that_matches_no_snapshot_file_is_a_gap_and_no_row(tmp_path):
    files = project("nuxt3", **{"server/api/hello.get.ts": None})
    record, gaps, _ = read(tmp_path, files)
    assert "/api/hello" not in {r["path"] for r in record["bound"]}
    [gap] = [g for g in gaps if g["path"] == "server/api/hello.get"]
    assert gap["kind"] == "outside_snapshot" and "/api/hello" in gap["detail"] and "no file with that path" in gap["detail"]


def test_an_import_that_matches_two_snapshot_files_is_a_gap_naming_both_and_no_row(tmp_path):
    files = project("nuxt3", **{"server/api/hello.get.js": "export default () => 1\n"})
    record, gaps, _ = read(tmp_path, files)
    assert "/api/hello" not in {r["path"] for r in record["bound"]}
    [gap] = [g for g in gaps if g["path"] == "server/api/hello.get"]
    assert gap["kind"] == "model_partial" and "server/api/hello.get.ts" in gap["detail"] and "server/api/hello.get.js" in gap["detail"]


def test_a_handler_file_of_the_snapshot_that_is_no_script_is_no_match(tmp_path):
    files = project("nuxt3", **{"server/api/hello.get.ts": None, "server/api/hello.get.md": "# not a handler\n"})
    record, gaps, _ = read(tmp_path, files)
    assert "/api/hello" not in {r["path"] for r in record["bound"]}
    assert [g["kind"] for g in gaps if g["path"] == "server/api/hello.get"] == ["outside_snapshot"]


# ------------------------------------------------------------------------------------------- what goes wrong

def prepare_gap(gaps):
    """The one gap `nuxt prepare` itself caused (the script's own are told apart by their words)."""
    [gap] = [g for g in gaps if g["kind"] != "outside_snapshot" and "daodan-nuxt" not in g["detail"]]
    return gap


def test_a_prepare_that_fails_is_the_gap_with_the_cause_the_tool_wrote_first_and_no_server_row(tmp_path):
    record, gaps, _ = read(tmp_path, project("nuxt3"), "config-throws")  # its `cat` still finds the file an earlier run wrote
    gap = prepare_gap(gaps)
    assert gap["kind"] == "model_failed" and gap["path"] == "."
    assert "exited with 1" in gap["detail"] and "nuxt.config needs a database" in gap["detail"]
    assert rows(record) == []


def test_a_nuxt_that_is_not_installed_fails_at_once_and_the_gap_names_the_package_npm_looked_for(tmp_path):
    record, gaps, _ = read(tmp_path, project("nuxt3"), "not-installed")
    gap = prepare_gap(gaps)
    assert gap["kind"] == "model_failed" and "ENOTCACHED" in gap["detail"] and "/nuxt" in gap["detail"]
    assert "framework_entries" not in record  # the script found no `@nuxt/kit` either


def test_a_file_that_prepare_did_not_write_is_a_gap_naming_the_likely_cause_and_the_pages_are_read_all_the_same(tmp_path):
    record, gaps, _ = read(tmp_path, project("nuxt3"), "build-dir")  # `buildDir` names another folder
    gap = prepare_gap(gaps)
    assert gap["kind"] == "model_failed" and gap["path"] == "."
    assert "buildDir" in gap["detail"] and ".nuxt/types/nitro-routes.d.ts" in gap["detail"]
    assert rows(record) == [] and rows(record, "page") == pages_expected(NUXT3_PAGES)  # the script does not read `.nuxt`


def test_prepare_failing_in_one_folder_is_that_folder_s_gap_and_the_other_is_still_read(tmp_path):
    files = {f"apps/{name}/{rel}": text for name in "ab" for rel, text in project("nuxt3").items()}
    answers = {"apps/a": answer("not-installed"), "apps/b": answer("nuxt3")}
    record, gaps, _ = read(tmp_path, files, answers=answers)
    assert {g["path"] for g in gaps if g["kind"] == "model_failed"} == {"apps/a"}
    assert {r["site"].split(":")[0] for r in record["bound"]} >= {"apps/b/server/api/hello.get.ts"}
    assert not [r for r in record["bound"] if r["site"].startswith("apps/a/")]


def test_the_file_cut_in_the_middle_of_a_route_is_a_gap_and_no_server_row(tmp_path):
    prepare, printed, pages = answer("nuxt3")
    cut = {**printed, "stdout": printed["stdout"][:printed["stdout"].index("'/feed'") + 30]}
    record, gaps, _ = read(tmp_path, project("nuxt3"), answers={".": (prepare, cut, pages)})
    gap = prepare_gap(gaps)
    assert gap["kind"] == "model_partial" and gap["path"] == "." and "did not parse whole" in gap["detail"] and "line" in gap["detail"]
    assert rows(record) == []


def test_a_file_that_parses_clean_and_names_no_route_is_a_gap_saying_none_was_found(tmp_path):
    prepare, printed, pages = answer("nuxt3")
    header = {**printed, "stdout": printed["stdout"][:printed["stdout"].index("  interface InternalApi")] + "}\nexport {}\n"}
    record, gaps, _ = read(tmp_path, project("nuxt3"), answers={".": (prepare, header, pages)})
    gap = prepare_gap(gaps)
    assert gap["kind"] == "model_partial" and "no route" in gap["detail"] and ".nuxt/types/nitro-routes.d.ts" in gap["detail"]
    assert rows(record) == []


def test_a_route_with_no_handler_file_the_reader_reads_is_a_gap_naming_the_route_and_the_others_are_read(tmp_path):
    prepare, printed, pages = answer("nuxt3")
    odd = printed["stdout"].replace("  interface InternalApi {\n", "  interface InternalApi {\n    '/api/odd': {\n      'get': unknown\n    }\n")
    record, gaps, _ = read(tmp_path, project("nuxt3"), answers={".": (prepare, {**printed, "stdout": odd}, pages)})
    assert [g for g in gaps if "/api/odd" in g["detail"]][0]["kind"] == "model_partial"
    assert "/api/odd" not in {r["path"] for r in record["bound"]} and "/api/hello" in {r["path"] for r in record["bound"]}


# ------------------------------------------------------------------------------------ the syntax tree of the file

def test_the_routes_are_read_from_the_tree_whatever_the_wrappers_around_the_import_and_the_order_of_the_methods():
    import entries
    older = ("declare module 'nitropack' {\n  interface InternalApi {\n"
             "    '/a': {\n      'get': Awaited<ReturnType<typeof import('../../server/api/a.get').default>>\n"
             "      'post': Awaited<ReturnType<typeof import('../../server/api/a.post').default>>\n    }\n"
             "    '/b/:id': {\n      'default': Simplify<Serialize<Awaited<ReturnType<typeof import('../../server/routes/b/[id]').default>>>>\n    }\n"
             "  }\n}\n")
    found, error, unread = entry_points.nuxt.nitro_routes(older)
    assert (error, unread) == (None, [])
    assert found == [{"path": "/a", "method": "get", "import": "../../server/api/a.get"},
                     {"path": "/a", "method": "post", "import": "../../server/api/a.post"},
                     {"path": "/b/:id", "method": "default", "import": "../../server/routes/b/[id]"}]


def test_a_text_that_does_not_parse_whole_gives_the_line_of_the_error_and_no_route():
    import entries
    whole = "interface InternalApi {\n  '/a': {\n    'get': Awaited<ReturnType<typeof import('x').default>>\n  }\n}\n"
    assert entry_points.nuxt.nitro_routes(whole)[0] == [{"path": "/a", "method": "get", "import": "x"}]
    found, error, unread = entry_points.nuxt.nitro_routes(whole + "const = = ;\n")  # a route that was whole is no row when the file is not
    assert found == [] and error == 6 and unread == []


# ------------------------------------------------------------------------------------------- what the source asks

def test_a_snapshot_with_no_package_json_declaring_nuxt_runs_nothing(tmp_path):
    from snapshot_store import open_snapshot
    files = {"web/package.json": '{"dependencies": {"vue": "3.5.46"}}\n', "docs/package.json": "{",
             "tools/package.json": '["nuxt"]\n', "pages/index.vue": "<template><div/></template>\n"}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        assert entry_points.nuxt.commands(premap.Context(manifest, store)) is None
    record = entry_points.write(manifest, sources=(entry_points.nuxt,), runner=lambda commands: 1 / 0)
    assert record["sources"][0]["state"] == "not_needed" and "framework_entries" not in record


def test_each_package_json_declaring_nuxt_among_its_dependencies_or_dev_dependencies_is_one_run(tmp_path):
    from snapshot_store import open_snapshot
    files = {"apps/a/package.json": '{"dependencies": {"nuxt": "4.6.4"}}\n',
             "apps/b/package.json": '{"devDependencies": {"nuxt": "3.21.11"}}\n',
             "apps/c/package.json": '{"dependencies": {"vue": "3.5.46"}}\n'}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        asked = entry_points.nuxt.commands(premap.Context(manifest, store))
    assert [(c["cwd"], c["argv"][0]) for c in asked] == [("apps/a", "npx"), ("apps/a", "cat"), ("apps/b", "npx"), ("apps/b", "cat"),
                                                          ("apps/a", "timeout"), ("apps/b", "timeout")]  # the script after all the others
    assert {c["argv"][2] for c in asked if c["argv"][0] == "timeout"} == {"450"}  # two folders share the 900 seconds


def test_the_folders_share_the_time_of_the_script_and_none_has_less_than_ten_seconds():
    assert [entry_points.nuxt.pages_seconds(n) for n in (1, 2, 3, 90, 91, 500)] == [900, 450, 300, 10, 10, 10]


def test_the_commands_use_the_projects_own_nuxt_without_network_and_the_setup_installs_no_package(tmp_path):
    import preparation
    from snapshot_store import open_snapshot
    project_dir, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"nuxt": "4.6.4"}}\n'})
    with open_snapshot(manifest) as store:
        asked = entry_points.nuxt.commands(premap.Context(manifest, store))
    # `npm_config_offline`: without `nuxt` installed `npx --no-install` still asks the registry and fails after 70 seconds with a network
    # error (measured: 70.6 s, `benchmarks/nuxt-routes/`); offline it fails at once, saying what is missing (0.45 s)
    assert asked == [
        {"tool": "nuxt", "argv": ["npx", "--no-install", "nuxt", "prepare"], "cwd": ".", "env": {"npm_config_offline": "true"},
         "network": "none"},
        {"tool": "nuxt", "argv": ["cat", ".nuxt/types/nitro-routes.d.ts"], "cwd": ".", "env": {}, "network": "none"},
        {"tool": "nuxt", "argv": ["timeout", "--kill-after=10", "900", "daodan-nuxt"], "cwd": ".", "env": {}, "network": "none"}]
    spec = container_runner.TOOLS["nuxt"]
    assert spec["setup"][0] == container_runner.UNPACK["node"] and len(spec["setup"]) == 2  # Node, and Daodan's script: no package
    assert not any("npm install" in line for line in spec["setup"])  # `nuxt` and `@nuxt/kit` are the project's own
    assert (spec["restores"], spec["runs_on"]) == ("node", ("node",))
    calls, fake = recorder()
    with patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)(asked)
    first, *rest = calls[0]["commands"]
    plan = preparation.node_prepare(["package.json"], lambda rel: (project_dir / rel).read_text(encoding="utf-8"))
    assert f"( {plan['lines'][0]} )" in first["argv"][-1] and "install -g" not in first["argv"][-1]
    assert [c["network"] for c in rest] == ["none", "none", "none"]  # the restore has the registries; the commands have no network


def test_the_setup_installs_daodans_script_as_a_command_and_the_script_is_beside_the_source():
    from pathlib import Path as Beside
    spec = container_runner.TOOLS["nuxt"]
    assert (None, None, "nuxt_pages.mjs") in spec["files"] and "daodan-nuxt" in spec["setup"][1] and "nuxt_pages.mjs" in spec["setup"][1]
    assert container_runner.fetched(None, None, "nuxt_pages.mjs") == Beside(entry_points.nuxt.__file__).with_name("nuxt_pages.mjs")
    assert container_runner.fetched(None, None, "nuxt_pages.mjs").is_file()
    assert entry_points.nuxt.SCRIPT == "daodan-nuxt"


def test_in_an_analysis_the_source_has_a_preparation_that_takes_the_shared_restore_before_its_commands(tmp_path):
    import node_preparation
    from snapshot_store import open_snapshot
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"nuxt": "4.6.4"}}\n'})
    with open_snapshot(manifest) as store:
        asked = entry_points.nuxt.commands(premap.Context(manifest, store))
    calls, fake = recorder()
    with node_preparation.analysis(), patch.object(container, "run_commands", fake):  # as the pipeline runs it
        container_runner.runner(manifest)(asked)
    [call] = calls
    assert call["commands"][0]["network"] == "registries" and call["node_restore"]["script"]
    assert [c["network"] for c in call["commands"][1:]] == ["none", "none", "none"]


def test_no_engine_carries_the_reason_and_nothing_of_the_project_runs_on_this_machine(tmp_path):
    """Every file the tool would load is code of the project: each leaves a mark if it runs here. Without an engine the source
    states a gap with the cause, and neither a process starts nor a mark appears."""
    mark = tmp_path / "ran-on-the-host"
    code = f"require('fs').writeFileSync({json.dumps(str(mark).replace(chr(92), '/'))}, 'x');\n"
    files = project("nuxt3", **{"nuxt.config.ts": code, "server/api/hello.get.ts": code, "modules/mark.ts": code,
                                "node_modules/.bin/nuxt": "#!/bin/sh\n" + code,
                                "package.json": json.dumps({"dependencies": {"nuxt": "3.21.11"}, "scripts": {"postinstall": f"node -e \"{code}\""}})})
    _, manifest = manifest_of(tmp_path, files)
    _, run = recorder(state="gap")
    import subprocess
    started, real = [], subprocess.Popen

    def spy(args, *given, **options):
        started.append(args)
        return real(args, *given, **options)
    with patch.object(container, "run_commands", run), patch.object(subprocess, "Popen", spy):
        record = entry_points.write(manifest, sources=(entry_points.nuxt,), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record and not mark.exists()
    assert {Path(str(a[0] if isinstance(a, (list, tuple)) else a)).stem for a in started} <= {"git"}  # Daodan's own read of the ignore rules
    started.clear()  # and with an engine's answer in hand, reading it starts nothing of the project either
    _, answered = runner_for({".": answer("nuxt3")})
    with patch.object(subprocess, "Popen", spy):
        record = entry_points.write(manifest, sources=(entry_points.nuxt,), runner=answered)
    assert record["framework_entries"] and not mark.exists()
    assert {Path(str(a[0] if isinstance(a, (list, tuple)) else a)).stem for a in started} <= {"git"}


# --------------------------------------------------- the registry of the sources that give framework entries

def test_the_source_is_registered_as_one_of_the_sources_that_give_entries_of_their_own():
    import entries
    assert entry_points.nuxt in entry_points.FRAMEWORK_SOURCES and entry_points.nuxt in entry_points.SOURCES
    assert hasattr(entry_points.nuxt, "commands") and callable(entry_points.nuxt.from_record)
    assert entry_points.nuxt.NAME in entries.QUERIES and entry_points.nuxt.NAME in container_runner.TOOLS  # the table is keyed by the source's name
    assert entries.QUERIES["nuxt"] == {"server-route": {"kind": "rotta", "exports": ["default"]}, "page": {"kind": "rotta", "page": True}}


def test_a_premap_made_before_the_source_is_stale(tmp_path):
    _, manifest = manifest_of(tmp_path, project("nuxt3"))
    premap.write(manifest, sources=())
    before = tuple(source for source in entry_points.SOURCES if source is not entry_points.nuxt)
    entry_points.write(manifest, sources=before)
    assert entry_points.state(manifest, sources=before)["state"] == "fresh"
    assert entry_points.state(manifest)["state"] == "stale"


def test_the_rows_and_the_gaps_of_the_source_reach_the_flow_evidence(tmp_path):
    from entry_points.flow_entries import evidence
    files = project("nuxt3")
    _, manifest = manifest_of(tmp_path, files)
    entry_points.write(manifest, sources=(entry_points.nuxt,), runner=runner_for({".": answer("nuxt3")})[1])
    rows_, gaps = evidence(manifest)
    mine = [r for r in rows_ if r["reader"] == "nuxt"]
    assert {(r["path"], r.get("method")) for r in mine if r["shape"] == "server-route"} == {(route, method) for route, method, _ in HANDLERS}
    assert {(r["path"], r["site"]) for r in mine if r["shape"] == "page"} == set(NUXT3_PAGES)
    assert sorted(g["path"] for g in gaps if g.get("source") == SOURCE) == sorted(path for _, path in INTERNAL)


def test_a_premap_where_the_source_was_not_needed_gives_the_evidence_no_nuxt_row_and_no_gap(tmp_path):
    from entry_points.flow_entries import evidence
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"vue": "3.5.46"}}\n'})
    entry_points.write(manifest, sources=(entry_points.nuxt,), runner=lambda commands: 1 / 0)
    rows_, gaps = evidence(manifest)
    assert [r for r in rows_ if r["reader"] == "nuxt"] == [] and [g for g in gaps if g.get("source") == SOURCE] == []


def test_the_source_file_of_the_nuxt_reader_is_part_of_the_key_of_the_cached_links():
    import flows
    from pathlib import Path as Reader
    seen = []
    with patch.object(Reader, "read_bytes", autospec=True, side_effect=lambda self: seen.append(self.name) or b""):
        flows._links_reader_digest.__wrapped__()
    assert "nuxt.py" in seen  # from the one tuple, `entry_points.FRAMEWORK_SOURCES`: no other line names the file


# --------------------------------------------------------------------- what reaches the links

@pytest.fixture(scope="module")
def made(tmp_path_factory):
    _, manifest = manifest_of(tmp_path_factory.mktemp("nuxt-links"), project("nuxt3"))
    entry_points.write(manifest, sources=(entry_points.nuxt,), runner=runner_for({".": answer("nuxt3")})[1])
    return manifest


@pytest.fixture(scope="module")
def links(made):
    import flows
    return flows.cached_links(made, [])


def test_the_route_handler_the_snapshot_binds_is_an_entry_with_its_method_and_an_offered_route(links):
    found = [(e["path"], e.get("method"), e["symbol"], e["kind"], e["handler_source"]) for e in links["entries"]
             if e["reader"] == "nuxt" and e["shape"] == "server-route"]
    assert found == [("/api/plain", "GET", "server/api/plain.get.ts::plain", "rotta", "nuxt")]
    assert links["routes"]["offered"] == 1 and links["routes"]["linked"] == 0  # it has a method and a schema: a call would meet it


def test_each_page_is_an_entry_of_its_file_as_a_next_page_is_one_with_the_path_and_no_method(links):
    found = {(e["path"], e["site"], e["symbol"], e["kind"]) for e in links["entries"] if e["reader"] == "nuxt" and e["shape"] == "page"}
    assert found == {(path, file, f"{file}::<module>", "rotta") for path, file in NUXT3_PAGES}
    assert not [e for e in links["entries"] if e["reader"] == "nuxt" and e["shape"] == "page" and e.get("method")]
    assert not [g for g in links["gaps"] if g["site"].startswith("pages/")]  # a page answers any method: no declared route, no gap


def test_the_handlers_the_snapshot_cannot_bind_are_gaps_of_the_links_with_what_was_looked_for(links):
    reasons = {g["site"]: g["reason"] for g in links["gaps"] if g["site"].startswith("server/") and "framework starts" in g["reason"]}
    assert set(reasons) == {file for _, _, file in HANDLERS if file != "server/api/plain.get.ts"}
    assert all("default" in reason for reason in reasons.values())


def test_the_shape_of_the_source_is_in_the_registry_so_no_question_is_asked_for_it(made):
    import entries
    from entry_points.flow_entries import evidence
    rules = entries.registry_rules([r for r in evidence(made)[0] if r["reader"] == "nuxt"])
    assert {(r["shape"], r["entry"]) for r in rules} == {("server-route", "rotta"), ("page", "rotta")}


def test_the_premap_rows_are_the_modules_with_their_exports_and_the_links_report_the_call_default_as_a_gap(tmp_path):
    """No source binds a row (spec 8.13, point 2): a server route's row is the handler file with the `default` export, and the
    links' binder reads the snapshot's export record: a `defineEventHandler(...)` call is no function, so the links' gap says so."""
    import flows
    _, manifest = manifest_of(tmp_path, project("nuxt3"))
    record = entry_points.write(manifest, sources=(entry_points.nuxt,), runner=runner_for({".": answer("nuxt3")})[1])
    servers = [r for r in record["framework_entries"] if r["shape"] == "server-route"]
    assert servers and all(r["exports"] == ["default"] and r["symbol"] == f"{r['site']}::<module>" and "handler" not in r for r in servers)
    links = flows.cached_links(manifest, [])
    [hello] = [g for g in links["gaps"] if g["site"] == "server/api/hello.get.ts"]
    assert "default" in hello["reason"] and not [e for e in links["entries"] if e["site"].startswith("server/api/hello.get.ts")]
    [plain] = [e for e in links["entries"] if e["site"].startswith("server/api/plain.get.ts")]
    assert plain["symbol"] == "server/api/plain.get.ts::plain"
