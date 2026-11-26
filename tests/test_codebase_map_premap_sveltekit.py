"""The files SvelteKit's own `svelte-kit sync` lists for each route (`.svelte-kit/types/route_meta_data.json`), read from its
output and bound to the snapshot.

The container is a fake: the answers are the ones the real commands gave on Modal for the fixture of
`benchmarks/sveltekit-routes/` (`tests/fixtures/premap/sveltekit/answers.json`, recorded by that folder's
`modal_probe.py --mode source`): the answer of `svelte-kit sync` and the one of the print of the file, for each variant. The tool
gives each route the files its types come from (its `+page`, `+page.server` and `+server` modules and its layouts' too, so a
layout is listed by every route under it), with the path the project has them at, and nothing about the exports of a module:
those are the snapshot's own export records, bound to the functions they name (`QUERIES["sveltekit"]` says which exports a
file calls).
"""
from __future__ import annotations

import json
import os
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from test_codebase_map_premap_container_runner import bound, container, container_runner, manifest_of, premap, recorder

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/sveltekit-routes"
FIXTURE = BENCHMARK / "fixture"
ANSWERS = json.loads((Path(__file__).parent / "fixtures/premap/sveltekit/answers.json").read_text(encoding="utf-8"))
SOURCE = "sveltekit@daodan/premap/v2"
SYNC = ["timeout", "--kill-after=10", "900", "npx", "--no-install", "svelte-kit", "sync"]  # one folder has all the time there is
LAST = "nessun ingresso"
META = ".svelte-kit/types/route_meta_data.json"
ROUTES = "src/routes/"


def project(**changes) -> dict[str, str]:
    root = FIXTURE / "routes"
    files = {path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
             for path in root.rglob("*") if path.is_file() and path.name != "package-lock.json"}
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def moved(files: dict[str, str], old: str, new: str) -> dict[str, str]:
    return {(new + rel[len(old):] if rel.startswith(old) else rel): text for rel, text in files.items()}


def answers(name: str = "routes") -> list[dict]:
    return [{**answer, "root": "/work"} for answer in ANSWERS[name]]


def runner_for(pair):
    """A runner that answers each folder's two commands, `svelte-kit sync` and the print of the file, with the recorded pair."""
    asked = []

    def run(commands):
        asked.extend(commands)
        return [pair[1] if c["argv"][0] == "cat" else pair[0] for c in commands]
    return asked, run


def read(tmp_path, files, name="routes", pair=None):
    _, manifest = manifest_of(tmp_path, files)
    asked, run = runner_for(pair or answers(name))
    record = premap.write(manifest, sources=(premap.sveltekit,), runner=run)
    record["bound"] = bound(manifest, record)
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], asked


def at(files, file, needle):
    """`file:line` of the first line of the file that holds `needle`: the position is checked against the text itself."""
    return f"{file}:{next(n for n, line in enumerate(files[file].split(chr(10)), 1) if needle in line)}"


def found(record):
    """Each row: path, shape, kind, site, symbol, the export that starts it (None at the file), the gap."""
    return sorted((r["path"], r["shape"], r.get("kind"), r["site"], r["symbol"], r.get("handler"), r.get("gap"))
                  for r in record["bound"])


def starts(record, path):
    """The exports a route's files start: name -> the function the snapshot binds it to."""
    return {r["handler"]: r["symbol"].split("::")[1] for r in record["bound"] if r["path"] == path and r.get("handler")}


def listed():
    """The recorded JSON of the tool: route id -> the files it lists."""
    return json.loads(ANSWERS["routes"][1]["stdout"])


# ------------------------------------------------------------------- the routes of the project

def test_every_file_the_tool_lists_is_a_row_on_the_function_each_export_a_framework_call_names_with_its_route_and_its_line(tmp_path):
    files = project()
    record, gaps, asked = read(tmp_path, files)
    by = lambda file, name: f"{file}::{name}"  # noqa: E731
    shop = f"{ROUTES}(shop)/"
    expected = [
        ("/", "+page", "rotta", at(files, ROUTES + "+page.ts", "export const load"), by(ROUTES + "+page.ts", "load"), "load", None),
        ("/(shop)/checkout", "+page.server", "rotta", at(files, shop + "checkout/+page.server.ts", "export const load"),
         by(shop + "checkout/+page.server.ts", "load"), "load", None),
        ("/blog", "+page.server", "rotta", at(files, ROUTES + "blog/+page.server.ts", "export const load"),
         by(ROUTES + "blog/+page.server.ts", "load"), "load", None),
        ("/blog/[slug]", "+page.server", "rotta", at(files, ROUTES + "blog/[slug]/+page.server.ts", "export const load"),
         by(ROUTES + "blog/[slug]/+page.server.ts", "load"), "load", None),
        ("/login", "+page.server", "rotta", at(files, ROUTES + "login/+page.server.ts", "export async function load"),
         by(ROUTES + "login/+page.server.ts", "load"), "load", None),
        ("/docs/[...rest]", "+page", "rotta", at(files, ROUTES + "docs/[...rest]/+page.ts", "export const load"),
         by(ROUTES + "docs/[...rest]/+page.ts", "load"), "load", None),
        ("/legacy", "+page", "rotta", at(files, ROUTES + "legacy/+page.js", "export function load"),
         by(ROUTES + "legacy/+page.js", "load"), "load", None),
        ("/api/health", "+server", "rotta", at(files, ROUTES + "api/health/+server.ts", "export const GET"),
         by(ROUTES + "api/health/+server.ts", "GET"), "GET", None),
        ("/api/pay", "+server", "rotta", at(files, ROUTES + "api/pay/+server.ts", "export const POST"),
         by(ROUTES + "api/pay/+server.ts", "POST"), "POST", None),
        ("/api/pay", "+server", "rotta", at(files, ROUTES + "api/pay/+server.ts", "export async function GET"),
         by(ROUTES + "api/pay/+server.ts", "GET"), "GET", None),
        ("/hybrid", "+server", "rotta", at(files, ROUTES + "hybrid/+server.ts", "export const GET"),
         by(ROUTES + "hybrid/+server.ts", "GET"), "GET", None),
        ("/sitemap.xml", "+server", "rotta", at(files, ROUTES + "sitemap.xml/+server.ts", "export function GET"),
         by(ROUTES + "sitemap.xml/+server.ts", "GET"), "GET", None),
        *[("/api/items/[id]", "+server", "rotta", at(files, ROUTES + "api/items/[id]/+server.ts", f"export const {name}"),
           by(ROUTES + "api/items/[id]/+server.ts", name), name, None) for name in ("GET", "PUT", "DELETE", "fallback")],
    ]
    rows = found(record)
    assert [row for row in rows if not row[6] and row[2] == "rotta"] == sorted(expected)
    assert gaps == [] and all(r["reader"] == "sveltekit" and r["sources"] == [SOURCE] for r in record["bound"])
    assert [(c["argv"], c["cwd"], c["network"], c["env"]) for c in asked] == [
        (SYNC, ".", "none", {"npm_config_offline": "true"}),
        (["cat", META], ".", "none", {})]


def test_an_export_no_function_of_the_snapshot_is_bound_to_is_a_row_on_the_file_with_the_cause_the_snapshot_gives(tmp_path):
    """`actions` is an object: its members are anonymous functions of the snapshot, none of them named by the export; a `GET`
    that is the result of a call is no function either, and a re-export leads to another file."""
    record, _, _ = read(tmp_path, project())
    unbound = {r["path"]: (r["site"], r["symbol"], r["gap"]) for r in record["bound"] if r.get("gap")}
    assert sorted(unbound) == ["/(shop)/cart", "/(shop)/checkout", "/blog/[slug]", "/computed", "/login", "/reexport"]
    for path in ("/(shop)/cart", "/(shop)/checkout", "/blog/[slug]", "/login"):
        file = unbound[path][0]
        assert file.endswith("+page.server.ts") and unbound[path][1] == f"{file}::<module>"
        assert "actions: unsupported-target-kind" in unbound[path][2] and "load" not in unbound[path][2]  # `load` is bound
    assert "GET: unsupported-target-kind" in unbound["/computed"][2]
    assert "load: reexport-unsupported" in unbound["/reexport"][2]
    assert starts(record, "/(shop)/cart") == {} and starts(record, "/computed") == {}


def test_a_layout_is_one_row_on_its_file_that_no_flow_starts_from_however_many_routes_list_it(tmp_path):
    record, _, _ = read(tmp_path, project())
    layouts = [(r["site"], r["path"], r["shape"], r["kind"], r["symbol"]) for r in record["bound"] if r["shape"].startswith("+layout")]
    assert sorted(layouts) == sorted([
        (ROUTES + "+layout.ts", "/", "+layout", LAST, ROUTES + "+layout.ts::<module>"),
        (ROUTES + "+layout.server.ts", "/", "+layout.server", LAST, ROUTES + "+layout.server.ts::<module>"),
        (ROUTES + "(shop)/+layout.server.ts", "/(shop)", "+layout.server", LAST, ROUTES + "(shop)/+layout.server.ts::<module>")])
    assert all("handler" not in r and "gap" not in r for r in record["bound"] if r["shape"].startswith("+layout"))
    assert len(listed()) == 20 and sum(ROUTES + "+layout.server.ts" in files for files in listed().values()) == 15  # the root one: 15 routes list it


def test_each_file_is_owned_by_the_route_that_has_it_in_its_own_folder_and_the_tool_names_no_other_owner():
    """The tool does not say which of a route's files are its own: the owner is the route with the fewest segments that lists
    the file. It is the route whose id is the folder of the file (a route id is a path under the routes folder), checked here
    on the whole of what the tool printed."""
    import posixpath
    from premap import sveltekit
    owner = sveltekit._files(listed())
    assert len(owner) == 18 and set(owner) == {f for files in listed().values() for f in files}
    for file, route in owner.items():
        folder = posixpath.dirname(file)
        assert folder == "src/routes" if route == "/" else folder.endswith(route) and folder == "src/routes" + route
    assert owner[ROUTES + "(shop)/+layout.server.ts"] == "/(shop)"  # listed by three routes, owned by its own
    assert sum(ROUTES + "(shop)/+layout.server.ts" in files for files in listed().values()) == 3  # (not by `/(shop)/receipt`: its page resets the layout)


def test_the_route_is_the_tool_s_id_with_its_group_and_its_segments_as_written_and_a_page_with_no_module_has_no_row(tmp_path):
    record, _, _ = read(tmp_path, project())
    paths = {r["path"] for r in record["bound"]}
    assert {"/(shop)/checkout", "/(shop)/cart", "/blog/[slug]", "/docs/[...rest]", "/sitemap.xml"} <= paths
    # `+page.svelte` is no file the tool lists: a route whose files are a component and the layouts above it has no row
    for route in ("/about", "/lang/[[opt]]", "/items/[id=integer]", "/(shop)/receipt"):
        assert route in listed() and not [r for r in record["bound"] if r["path"] == route], route
        assert all(file.endswith(("+layout.ts", "+layout.server.ts")) for file in listed()[route]), route
    assert not [r for r in record["bound"] if r["site"].endswith(".svelte")]


def test_a_routes_folder_that_is_not_src_routes_needs_no_reading_the_tool_prints_the_files_where_the_project_has_them(tmp_path):
    files = moved(project(), "src/routes/", "src/pages/")
    record, gaps, _ = read(tmp_path, files, "routes-in-pages")
    assert gaps == [] and all(r["site"].startswith("src/pages/") for r in record["bound"])
    assert starts(record, "/api/pay") == {"POST": "POST", "GET": "GET"} and starts(record, "/blog/[slug]") == {"load": "load"}
    assert len(record["bound"]) == len(read(tmp_path / "again", project())[0]["bound"])


@pytest.mark.parametrize("name", ["old-kit-2.0.0", "old-kit-2.15.0", "old-kit-2.40.0"])
def test_the_older_sveltekit_the_benchmark_ran_print_the_same_json_so_the_same_rows(tmp_path, name):
    assert ANSWERS[name][1]["stdout"] == ANSWERS["routes"][1]["stdout"]
    record, gaps, _ = read(tmp_path, project(), name)
    assert gaps == [] and found(record) == found(read(tmp_path / "now", project())[0])


def test_a_route_that_was_deleted_is_no_row_the_tool_wrote_its_file_list_again(tmp_path):
    """`stale`: after a sync and two routes taken away, the second sync listed neither (the tool removes what it wrote)."""
    files = project(**{"src/routes/about/+page.svelte": None, "src/routes/api/health/+server.ts": None})
    record, gaps, _ = read(tmp_path, files, "stale")
    assert gaps == [] and "/about" not in {r["path"] for r in record["bound"]}
    assert not [r for r in record["bound"] if r["path"] == "/api/health"]


# ------------------------------------------------------------------------- what the tool does not say

def test_a_file_the_tool_lists_and_the_snapshot_does_not_hold_is_a_gap_and_no_row_and_the_other_files_are_read(tmp_path):
    record, [gap], _ = read(tmp_path, project(**{"src/routes/api/pay/+server.ts": None}))
    assert (gap["kind"], gap["path"]) == ("outside_snapshot", "src/routes/api/pay/+server.ts")
    assert "/api/pay" in gap["detail"] and "no file" in gap["detail"]
    assert not [r for r in record["bound"] if r["path"] == "/api/pay"]
    assert starts(record, "/api/health") == {"GET": "GET"}


def test_a_file_whose_name_the_table_does_not_know_is_a_row_with_no_kind_and_a_gap_and_a_shape_to_classify(tmp_path):
    import entries
    out = {**listed(), "/about": ["src/routes/about/+foo.ts"]}
    pair = [answers()[0], {**answers()[1], "stdout": json.dumps(out)}]
    record, _, _ = read(tmp_path, project(**{"src/routes/about/+foo.ts": "export const GET = () => 1;\n"}), pair=pair)
    [row] = [r for r in record["bound"] if r["shape"] == "+foo"]
    assert (row["path"], row["site"], row["symbol"]) == ("/about", "src/routes/about/+foo.ts", "src/routes/about/+foo.ts::<module>")
    assert "kind" not in row and "+foo" in row["gap"]
    assert ("sveltekit", "+foo") in {(q["reader"], q["shape"]) for q in entries.shape_questions(record["bound"])}


def test_an_out_dir_that_is_not_the_default_is_a_gap_that_says_so_with_the_tool_s_own_words_and_no_row(tmp_path):
    """`kit.outDir` is in `svelte.config.js`, which is code: the tool wrote the file elsewhere (`.kit-out`), and said so."""
    record, [gap], _ = read(tmp_path, project(), "out-dir")
    assert (gap["kind"], gap["path"]) == ("model_failed", ".")
    assert "wrote no .svelte-kit/types/route_meta_data.json" in gap["detail"] and "outDir" in gap["detail"] and ".kit-out" in gap["detail"]
    assert "framework_entries" not in record


@pytest.mark.parametrize("name, cause", [
    ("config-throws", "svelte.config.js needs a secret"), ("config-broken", "Unexpected end of input"),
    ("route-conflict", 'The "/(a)/x" and "/(b)/x" routes conflict with each other'),
    ("bad-matcher", "No matcher found for parameter 'nomatcher'")])
def test_a_sync_that_fails_is_the_folder_s_gap_with_the_cause_the_tool_wrote_first(tmp_path, name, cause):
    record, [gap], _ = read(tmp_path, project(), name)
    assert (gap["kind"], gap["path"]) == ("model_failed", ".")
    assert "exited with 1" in gap["detail"] and cause in gap["detail"] and "svelte-kit sync" in gap["detail"]
    assert "framework_entries" not in record


def test_a_failed_sync_is_not_read_even_when_an_earlier_one_left_the_file(tmp_path):
    """`failed-after-a-good-sync`: the config throws the second time, and the file the first sync wrote is still there, and
    printed with exit 0: the routes of the earlier run are no rows."""
    pair = answers("failed-after-a-good-sync")
    assert pair[0]["returncode"] == 1 and pair[1]["returncode"] == 0 and json.loads(pair[1]["stdout"])
    record, [gap], _ = read(tmp_path, project(), pair=pair)
    assert gap["kind"] == "model_failed" and "exited with 1" in gap["detail"] and "needs a secret" in gap["detail"]
    assert "framework_entries" not in record


def test_a_project_that_declares_the_command_and_has_not_installed_it_is_a_gap_that_says_it_could_not_be_found(tmp_path):
    record, [gap], asked = read(tmp_path, project(), "not-installed")
    assert gap["kind"] == "model_failed" and "ENOTCACHED" in gap["detail"] and "svelte-kit" in gap["detail"]
    assert asked[0]["env"] == {"npm_config_offline": "true"}  # npm asks no registry: it fails at once and says what it could not find
    assert "framework_entries" not in record


def test_a_project_whose_routes_are_only_components_lists_no_file_and_has_neither_a_row_nor_a_gap(tmp_path):
    record, gaps, _ = read(tmp_path, project(), "no-routes")
    assert json.loads(ANSWERS["no-routes"][1]["stdout"]) == {"/": []}
    assert gaps == [] and "framework_entries" not in record


def test_a_syntax_error_in_a_route_module_is_a_row_with_the_snapshot_s_cause_and_the_other_files_are_read(tmp_path):
    """`server-syntax-error`: sync exits 0 and lists the file; the snapshot cannot read it."""
    files = project(**{"src/routes/blog/+page.server.ts": "export const load = async () => ({ posts: [\n"})
    record, gaps, _ = read(tmp_path, files, "server-syntax-error")
    [blog] = [r for r in record["bound"] if r["path"] == "/blog"]
    assert blog["site"] == "src/routes/blog/+page.server.ts" and blog["gap"].startswith("no function found for the exports")
    assert gaps == [] and starts(record, "/blog/[slug]") == {"load": "load"}


def test_an_output_that_is_no_json_of_the_known_layout_is_a_gap_and_no_row(tmp_path):
    for n, stdout in enumerate(("not json", "[]", '{"/": "src/routes/+page.ts"}', '{"/": [3]}', "null")):
        record, [gap], _ = read(tmp_path / f"case{n}", project(), pair=[answers()[0], {**answers()[1], "stdout": stdout}])
        assert gap["kind"] == "model_failed" and "no JSON of the known layout" in gap["detail"], stdout
        assert "framework_entries" not in record


def test_a_failure_with_a_long_message_keeps_both_ends_of_it(tmp_path):
    long = {"root": "/work", "returncode": 1, "stdout": "", "stderr": "first words " + "x" * 2000 + " last words"}
    _, [gap], _ = read(tmp_path, project(), pair=[long, answers()[1]])
    assert "first words" in gap["detail"] and "last words" in gap["detail"] and len(gap["detail"]) < 1000


def test_a_sync_that_the_time_limit_ended_is_the_folder_s_gap_that_says_how_long_it_had(tmp_path):
    """`timed-out`: the same command with a limit of half a second, on Modal (the sync takes 1.0 s at the least): `timeout` ends it
    with 124 after 0.5 s, and the print finds no file, as none was written."""
    pair = answers("timed-out")
    assert pair[0]["returncode"] == 124 and pair[1]["returncode"] == 1
    record, [gap], _ = read(tmp_path, project(), pair=pair)
    assert (gap["kind"], gap["path"]) == ("model_failed", ".")
    assert "did not end in 900 seconds" in gap["detail"] and "svelte-kit sync" in gap["detail"]
    assert "framework_entries" not in record


def test_a_sync_that_timeout_had_to_kill_is_a_gap_that_names_the_time_and_the_memory_as_the_possible_causes(tmp_path):
    """Exit 137 is not recorded on Modal (the memory of the run was not exhausted on any fixture): the answer is the one `timeout
    --kill-after` and the kernel give, written here, as the tests of Angular's and Nuxt's scripts do."""
    pair = [{"root": "/work", "returncode": 137, "stdout": "", "stderr": ""}, answers()[1]]
    record, [gap], _ = read(tmp_path, project(), pair=pair)
    assert gap["kind"] == "model_failed" and "killed (exit 137)" in gap["detail"] and "900 seconds" in gap["detail"]
    assert f"{premap.sveltekit.MEMORY_GB} GB" in gap["detail"] and "framework_entries" not in record


def test_the_folders_share_the_time_and_none_has_less_than_ten_seconds_and_the_memory_is_the_runner_s(tmp_path):
    from snapshot_store import open_snapshot

    def seconds(count):
        files = {f"p{n}/package.json": '{"devDependencies": {"@sveltejs/kit": "2.70.4"}}\n' for n in range(count)}
        _, manifest = manifest_of(tmp_path / f"n{count}", files)
        with open_snapshot(manifest) as store:
            return {c["argv"][2] for c in premap.sveltekit.commands(premap.Context(manifest, store)) if c["argv"][0] == "timeout"}
    assert (seconds(1), seconds(3), seconds(200)) == ({"900"}, {"300"}, {"10"})
    assert premap.sveltekit.MEMORY_GB == container_runner.TOOLS["sveltekit"]["memory"]  # the same 3 GB the setup gives the container


# `shortcut:` in `sveltekit.py`: a form the framework documents that this reader leaves as a gap
def test_a_load_written_with_satisfies_is_a_row_with_the_snapshot_s_cause_and_not_a_function(tmp_path):
    """`export const load = (async () => ...) satisfies PageServerLoad` is a documented form (svelte.dev/docs/kit/load): the
    snapshot records `load` as a binding and the arrow as an anonymous function, so no function is bound to the export."""
    text = "import type { PageServerLoad } from './$types';\nexport const load = (async () => ({ posts: [] })) satisfies PageServerLoad;\n"
    record, gaps, _ = read(tmp_path, project(**{"src/routes/blog/+page.server.ts": text}))
    [blog] = [r for r in record["bound"] if r["path"] == "/blog"]
    assert blog["site"] == "src/routes/blog/+page.server.ts" and "handler" not in blog
    assert "load: unsupported-target-kind" in blog["gap"] and gaps == []


def test_an_overloaded_method_is_not_dropped_without_a_gap(tmp_path):
    """An export the file makes in several records (overload signatures and the implementation) is not an export the file does not
    make: before `semantic_store.exported_target` told the two apart (`export-ambiguous` and `export-missing`), `GET` went with no gap
    while `POST` was a row. Written as an `xfail(strict=True)` until that change was in; it was, and the mark went."""
    text = ("export function GET(a: string): void;\nexport function GET(a: number): void;\nexport function GET(a: any): void {}\n"
            "export const POST = async () => new Response('x');\n")
    record, _, _ = read(tmp_path, project(**{"src/routes/api/health/+server.ts": text}))
    rows = [r for r in record["bound"] if r["path"] == "/api/health"]
    assert {r["handler"] for r in rows if r.get("handler")} == {"POST"}  # what is bound stays bound
    assert [r["gap"] for r in rows if r.get("gap")] == [
        "no function found for the exports the framework starts /api/health from: GET: export-ambiguous"], "GET is neither a row nor a gap"


# ------------------------------------------------------------- what runs, and where

def test_only_a_package_json_that_declares_the_kit_starts_the_command_one_run_per_folder(tmp_path):
    from snapshot_store import open_snapshot
    files = {"apps/a/package.json": '{"devDependencies": {"@sveltejs/kit": "2.70.4"}}\n',
             "apps/b/package.json": '{"dependencies": {"@sveltejs/kit": "2.70.4"}}\n',
             "apps/c/package.json": '{"dependencies": {"svelte": "5.59.1", "@sveltejs/adapter-auto": "6.1.1"}}\n',
             "apps/d/package.json": "{\n", "apps/e/package.json": '["@sveltejs/kit"]\n'}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        asked = premap.sveltekit.commands(premap.Context(manifest, store))
    assert [(c["cwd"], c["argv"]) for c in asked] == [
        (folder, argv) for folder in ("apps/a", "apps/b")
        for argv in ([*SYNC[:2], "450", *SYNC[3:]], ["cat", META])]  # two folders share the time; `npm-files` reports a manifest that is not JSON
    assert all(c["tool"] == "sveltekit" and c["network"] == "none" for c in asked)
    assert [c["env"] for c in asked[:2]] == [{"npm_config_offline": "true"}, {}]
    _, manifest = manifest_of(tmp_path / "plain", {"package.json": '{"dependencies": {"svelte": "5.59.1"}}\n'})
    with open_snapshot(manifest) as store:
        assert premap.sveltekit.commands(premap.Context(manifest, store)) is None


def test_a_package_folder_is_read_against_its_own_files(tmp_path):
    files = {f"web/{rel}": text for rel, text in project().items()}
    files["web/package.json"] = '{"devDependencies": {"@sveltejs/kit": "2.70.4"}}\n'
    record, gaps, asked = read(tmp_path, files)
    assert gaps == [] and {c["cwd"] for c in asked} == {"web"}
    assert {r["site"].split(":")[0] for r in record["bound"]} >= {"web/src/routes/api/pay/+server.ts"}
    assert starts(record, "/api/pay") == {"POST": "POST", "GET": "GET"}


def test_the_setup_installs_no_package_the_project_s_own_command_is_in_the_packages_the_restore_installs(tmp_path):
    import preparation
    from snapshot_store import open_snapshot
    project_dir, manifest = manifest_of(tmp_path, {"package.json": '{"devDependencies": {"@sveltejs/kit": "2.70.4"}}\n'})
    with open_snapshot(manifest) as store:
        asked = premap.sveltekit.commands(premap.Context(manifest, store))
    spec = container_runner.TOOLS["sveltekit"]
    assert spec["setup"] == [container_runner.UNPACK["node"]]  # Node only
    assert (spec["restores"], spec["runs_on"]) == ("node", ("node",))
    calls, fake = recorder()
    with patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)(asked)
    first, *rest = calls[0]["commands"]
    plan = preparation.node_prepare(["package.json"], lambda rel: (project_dir / rel).read_text(encoding="utf-8"))
    assert f"( {plan['lines'][0]} )" in first["argv"][-1] and "install -g" not in first["argv"][-1]
    assert [c["network"] for c in rest] == ["none", "none"]  # the restore has the registries; the commands have no network


def marked_project(tmp_path, monkeypatch):
    """A project that declares the kit and holds all a `svelte-kit sync` would start, each file leaving its own mark in `marks/` if it
    runs on this machine: written as ES modules (the package is `"type": "module"`, as the fixture is), the command's bin with a Node
    shebang, the install scripts, the config files and the kit's own package; and, first on the PATH, a stand-in for each program
    that would start it (node, npx, npm, svelte-kit, vite, timeout) that writes a mark too."""
    marks, tools = tmp_path / "marks", tmp_path / "bin"
    marks.mkdir()
    tools.mkdir()

    def esm(name):
        return f"import {{ writeFileSync }} from 'node:fs';\nwriteFileSync({json.dumps((marks / name).as_posix())}, 'ran');\n"
    for name in ("node", "npx", "npm", "svelte-kit", "vite", "timeout"):
        (tools / name).write_text(f'#!/bin/sh\necho "$0 $*" >> "{marks}/tool-{name}"\n', encoding="utf-8", newline="\n")
        (tools / name).chmod(0o755)
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    manifest_text = json.dumps({"type": "module", "devDependencies": {"@sveltejs/kit": "2.70.4"},
                                "scripts": {"postinstall": "node mark.js", "prepare": "svelte-kit sync"}})
    files = project(**{"package.json": manifest_text, "mark.js": esm("mark.js"), "svelte.config.js": esm("svelte.config.js"),
                       "vite.config.ts": esm("vite.config.ts"), "src/params/integer.ts": esm("integer.ts"),
                       "node_modules/.bin/svelte-kit": "#!/usr/bin/env node\n" + esm("bin-svelte-kit"),
                       "node_modules/@sveltejs/kit/package.json": json.dumps({"name": "@sveltejs/kit", "type": "module", "exports": "./index.js"}),
                       "node_modules/@sveltejs/kit/index.js": esm("package-kit"),
                       ".svelte-kit/types/route_meta_data.json": '{"/": ["src/routes/+page.ts"]}\n'})
    return marks, manifest_of(tmp_path, files)[1]


def spied(monkeypatch):
    """Every process the code under test asks for: `subprocess.run`, `Popen` and `os.system`. Daodan's own `git` passes to the real
    one (it lists the files of the perimeter); anything else is recorded and not started, so that even a wrong source starts nothing
    of the project on this machine."""
    import subprocess
    started, run, popen = [], subprocess.run, subprocess.Popen

    def own(args):
        return isinstance(args, (list, tuple)) and bool(args) and Path(str(args[0])).stem == "git"

    def spy_run(args, *given, **options):
        started.append(args)
        return run(args, *given, **options) if own(args) else subprocess.CompletedProcess(args, 0, "", "")

    def spy_popen(args, *given, **options):
        started.append(args)
        if own(args):
            return popen(args, *given, **options)
        raise OSError("no process of the project starts on this machine")
    monkeypatch.setattr(subprocess, "run", spy_run)
    monkeypatch.setattr(subprocess, "Popen", spy_popen)
    monkeypatch.setattr(os, "system", lambda command: started.append(command) or 0)
    return started


def nothing_started(started, marks):
    assert [a for a in started if not (isinstance(a, (list, tuple)) and Path(str(a[0])).stem == "git")] == []  # Daodan's own git, only
    assert all("core.hooksPath=/dev/null" in a and "core.fsmonitor=false" in a for a in started)  # with the hooks and the monitor off
    assert sorted(path.name for path in marks.iterdir()) == []


def test_no_engine_carries_the_reason_and_nothing_of_the_project_runs_on_this_machine(tmp_path, monkeypatch):
    """Every file the tool would load is code of the project: each leaves a mark if it runs here. Without an engine the source
    states a gap with the cause, and no process of the project starts and no mark appears; with an engine's answer in hand, reading
    it starts nothing of the project either."""
    marks, manifest = marked_project(tmp_path, monkeypatch)
    started = spied(monkeypatch)
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        record = premap.write(manifest, sources=(premap.sveltekit,), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record
    nothing_started(started, marks)
    started.clear()
    record = premap.write(manifest, sources=(premap.sveltekit,), runner=runner_for(answers())[1])
    assert record["framework_entries"]
    nothing_started(started, marks)


@pytest.mark.parametrize("how", ["os.system", "subprocess.run", "subprocess.Popen"])
def test_the_check_of_the_sign_catches_a_source_that_starts_the_command_on_the_host(tmp_path, monkeypatch, how):
    """The mutation, in memory, three ways: a source that runs `svelte-kit sync` here. The check above must fail for each."""
    import subprocess
    marks, manifest = marked_project(tmp_path, monkeypatch)
    started = spied(monkeypatch)
    real = premap.sveltekit.commands
    command = ["npx", "--no-install", "svelte-kit", "sync"]

    def mutated(context):
        try:
            {"os.system": lambda: os.system(" ".join(command)), "subprocess.run": lambda: subprocess.run(command),
             "subprocess.Popen": lambda: subprocess.Popen(command)}[how]()
        except OSError:  # the spy refuses to start it, after recording it
            pass
        return real(context)
    monkeypatch.setattr(premap.sveltekit, "commands", mutated)
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        premap.write(manifest, sources=(premap.sveltekit,), runner=container_runner.runner(manifest))
    with pytest.raises(AssertionError):
        nothing_started(started, marks)


def test_a_snapshot_with_no_package_json_declaring_the_kit_runs_nothing(tmp_path):
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"svelte": "5.59.1"}}\n', "src/routes/+page.svelte": "<h1>x</h1>\n"})
    record = premap.write(manifest, sources=(premap.sveltekit,), runner=lambda commands: 1 / 0)
    assert record["sources"][0]["state"] == "not_needed" and "framework_entries" not in record


# --------------------------------------------------- the registry of the sources that give framework entries

def test_the_source_is_one_name_of_the_registry_with_its_table_in_the_data_and_its_setup_in_the_runner():
    import entries
    assert premap.sveltekit in premap.FRAMEWORK_SOURCES and premap.sveltekit in premap.SOURCES
    source = premap.sveltekit
    assert hasattr(source, "commands") and callable(source.from_record)
    assert source.NAME in entries.QUERIES and source.NAME in container_runner.TOOLS
    table = entries.QUERIES["sveltekit"]
    assert set(table) == {"+server", "+page.server", "+page", "+layout.server", "+layout"}
    assert table["+page.server"]["exports"] == ["load", "actions"] and "GET" in table["+server"]["exports"]
    assert table["+layout"] == {"kind": LAST} and table["+layout.server"] == {"kind": LAST}


def test_the_evidence_reads_the_rows_and_the_gaps_of_the_source_beside_the_others(tmp_path):
    from premap.flow_entries import evidence
    _, manifest = manifest_of(tmp_path, project())
    premap.write(manifest, sources=(premap.sveltekit,), runner=runner_for(answers())[1])
    rows, gaps = evidence(manifest)
    assert {r["reader"] for r in rows} == {"sveltekit"} and {r["path"] for r in rows} >= {"/api/pay", "/blog/[slug]"}
    assert [g for g in gaps if g.get("source") == SOURCE] == []  # the rows the snapshot cannot bind are rows with a gap, not gaps of the source


def test_a_premap_made_before_the_source_is_stale(tmp_path):
    _, manifest = manifest_of(tmp_path, project())
    before = tuple(source for source in premap.SOURCES if source is not premap.sveltekit)
    premap.write(manifest, sources=before)
    assert premap.state(manifest, sources=before)["state"] == "fresh"
    assert premap.state(manifest)["state"] == "stale"


def test_a_premap_where_the_source_was_not_needed_gives_the_evidence_no_row_and_no_gap(tmp_path):
    from premap.flow_entries import evidence
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"react": "19.3.1"}}\n'})
    premap.write(manifest, sources=(premap.sveltekit,), runner=lambda commands: 1 / 0)
    rows, gaps = evidence(manifest)
    assert [r for r in rows if r["reader"] == "sveltekit"] == [] and [g for g in gaps if g.get("source") == SOURCE] == []


# --------------------------------------------------------------------- what reaches the links

@pytest.fixture(scope="module")
def made(tmp_path_factory):
    _, manifest = manifest_of(tmp_path_factory.mktemp("sveltekit-links"), project())
    premap.write(manifest, sources=(premap.sveltekit,), runner=runner_for(answers())[1])
    return manifest


@pytest.fixture(scope="module")
def links(made):
    import flows
    return flows.cached_links(made, [])


def test_each_export_a_file_starts_is_an_entry_on_its_function_and_no_route_is_offered_by_it(links):
    entries_found = {(e["path"], e["symbol"].split("::")[1], e["kind"], e["handler_source"]) for e in links["entries"]
                     if e["reader"] == "sveltekit" and not e.get("gap")}
    assert {("/api/pay", "POST", "rotta", "sveltekit"), ("/api/pay", "GET", "rotta", "sveltekit"),
            ("/api/items/[id]", "fallback", "rotta", "sveltekit"), ("/blog/[slug]", "load", "rotta", "sveltekit"),
            ("/", "load", "rotta", "sveltekit"), ("/docs/[...rest]", "load", "rotta", "sveltekit"),
            ("/sitemap.xml", "GET", "rotta", "sveltekit")} <= entries_found
    assert len(entries_found) == 16  # one for each function bound: 9 in the endpoints and 7 `load`
    assert links["routes"]["offered"] == 0 and links["routes"]["linked"] == 0  # entries, not offered routes: the tool gives no method


def test_the_rows_the_snapshot_cannot_bind_are_gaps_of_the_links_with_what_was_looked_for(links):
    reasons = {g["site"]: g["reason"] for g in links["gaps"] if g["site"].endswith(("/cart/+page.server.ts", "/computed/+server.ts", "/reexport/+page.server.ts"))}
    assert "actions" in reasons[ROUTES + "(shop)/cart/+page.server.ts"] and "unsupported-target-kind" in reasons[ROUTES + "(shop)/cart/+page.server.ts"]
    assert "GET" in reasons[ROUTES + "computed/+server.ts"] and "reexport-unsupported" in reasons[ROUTES + "reexport/+page.server.ts"]


def test_a_layout_is_a_candidate_of_no_kind_that_starts_a_flow_and_so_no_entry(made, links):
    from premap.flow_entries import evidence
    layouts = [r for r in evidence(made)[0] if r["shape"].startswith("+layout")]
    assert len(layouts) == 3 and {r["kind"] for r in layouts} == {LAST}
    assert not [e for e in links["entries"] if e["site"].split(":")[0] in {r["site"] for r in layouts}]


def test_the_shapes_of_the_source_are_in_the_registry_so_no_question_is_asked_for_them(made):
    import entries
    from premap.flow_entries import evidence
    rows = [r for r in evidence(made)[0] if r["reader"] == "sveltekit"]
    assert {(r["shape"], r["entry"]) for r in entries.registry_rules(rows)} == {
        ("+server", "rotta"), ("+page.server", "rotta"), ("+page", "rotta"), ("+layout.server", LAST), ("+layout", LAST)}
    assert entries.shape_questions(rows) == []


def test_the_premap_the_whole_pipeline_wrote_on_modal_holds_the_rows_of_the_recorded_answer(tmp_path):
    """`results/pipeline-scan.json`: the `scan` step in Daodan's container, with the packages restored from the lockfile and the
    command run under `timeout` with no network, wrote the same 25 rows that the recorded answer gives here, and no gap of the
    source; the 16 entries are the rows on a function, and Noir's 25 endpoints in the same files stay gaps of their own."""
    scan = json.loads((BENCHMARK / "results/pipeline-scan.json").read_text(encoding="utf-8"))
    record, _, _ = read(tmp_path, project())
    assert scan["framework_entries"] == [{key: value for key, value in row.items() if key != "sources"} for row in record["bound"]]
    assert len(scan["framework_entries"]) == 25 and scan["source_gaps"] == []
    assert scan["sources"]["sveltekit"]["state"] == "ran" and scan["sources"]["next"]["state"] == "not_needed"
    assert scan["links"]["entries"] == {"sveltekit rotta": 16} and scan["links"]["routes"]["offered"] == 0
    assert scan["links"]["gaps"] == {"noir: no unique snapshot handler at its site": 25, "sveltekit: no function found for the exports": 6}


def test_a_source_that_a_fake_adds_to_the_tuple_is_read_with_no_other_line_than_the_name(tmp_path, monkeypatch):
    from premap.flow_entries import evidence
    row = {"reader": "svelte-like", "shape": "page", "site": "src/routes/+page.svelte", "symbol": "src/routes/+page.svelte::<module>",
           "path": "/", "sources": ["svelte-like@v1"]}
    fake = types.SimpleNamespace(NAME="svelte-like", from_record=lambda report: ([row], []))
    _, manifest = manifest_of(tmp_path, {"package.json": "{}\n"})
    premap.write(manifest, sources=())
    monkeypatch.setattr(premap, "FRAMEWORK_SOURCES", (*premap.FRAMEWORK_SOURCES, fake))
    assert row in evidence(manifest)[0]


def test_the_premap_rows_are_the_modules_with_their_exports_and_the_links_bind_them_to_the_functions(tmp_path):
    """No source binds a row (spec 8.13, point 2): the pre-map row is the module with its table's exports, and the links' binder
    puts each entry on the function the snapshot names."""
    import flows
    _, manifest = manifest_of(tmp_path, project())
    record = premap.write(manifest, sources=(premap.sveltekit,), runner=runner_for(answers())[1])
    [pay] = [r for r in record["framework_entries"] if r["path"] == "/api/pay"]
    assert pay["symbol"] == f"{pay['site']}::<module>" and pay["exports"] and "handler" not in pay and "handler_source" not in pay
    linked = {(e["path"], e["symbol"].split("::")[1], e["handler_source"]) for e in flows.cached_links(manifest, [])["entries"]
              if e["reader"] == "sveltekit"}
    assert {("/api/pay", "POST", "sveltekit"), ("/api/pay", "GET", "sveltekit")} <= linked
