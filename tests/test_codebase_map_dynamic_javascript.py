"""The dynamic step's JavaScript observer: the test command a package declares, the container run that observes it,
the recorder, and the join of what it saw with the snapshot's references.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_dynamic_javascript.py

The container is a fake `container.run_in_container`: it keeps the scripts it is given and plays the files a run
brings back, so each test checks what the observer sends, keeps and says. The recorder's own tests run the small
project under a real Node with the recorder preloaded, as the container does; they skip without Node, or without
a @babel/core to give it (DAODAN_TEST_BABEL names its folder; else one this repository resolves). The join runs
on the observation recorded from that project, kept here (`RECORDED`), which the recorder's test compares with a
fresh one.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import code_graph  # noqa: E402
import container  # noqa: E402
import dynamic  # noqa: E402
import premap  # noqa: E402
import preparation  # noqa: E402
import snapshot  # noqa: E402
from dynamic import javascript as observer  # noqa: E402
from premap import npm_tests  # noqa: E402

READERS = tuple(source for source in premap.SOURCES if not hasattr(source, "commands"))
INDEX = '''const path = require("path");
class Box { size() { return 1; } static make() { return new Box(); } }
function first(xs) { return xs[0]; }
const table = { run: first };
module.exports = { first, apply: (fn, v) => fn(v), Box, table, base: p => path.basename(p) };
'''
MORE = '''export const twice = fn => v => fn(fn(v));
export function inc(v) { return v + 1; }
'''
TEST = '''const test = require("node:test");
const assert = require("node:assert");
const lib = require("../src");

test("first", async () => {
  assert.strictEqual(lib.first([1, 2]), 1);
  assert.strictEqual(lib.apply(lib.first, [3]), 3);
  assert.strictEqual(lib.table.run([4]), 4);
  assert.strictEqual(lib.Box.make().size(), 1);
  assert.strictEqual(lib.base("a/b.js"), "b.js");
  const more = await import("../src/more.mjs");
  assert.strictEqual(more.twice(more.inc)(1), 3);
});
'''
PROJECT = {"package.json": '{"name": "small", "scripts": {"test": "node --test"}}\n', "src/index.js": INDEX,
           "src/more.mjs": MORE, "test/index.test.js": TEST}


def write(folder: Path, files: dict) -> Path:
    for rel, text in files.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(text, encoding="utf-8", newline="\n")
    return folder


# --- the pre-map: the test script a package declares -----------------------------------------------------------

def premapped(tmp_path, files: dict) -> dict:
    project = write(tmp_path / "proj", files)
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    record = premap.write(manifest, sources=READERS)
    assert not [gap for gap in record["gaps"] if gap["kind"] == "source_failed"]
    return record


def declared(tmp_path, files: dict) -> list[dict]:
    return [{key: value for key, value in entry.items() if key != "sources"}
            for entry in premapped(tmp_path, files).get("tests", [])]


def package(script: str | None = None, **scripts: str) -> str:
    return json.dumps({"name": "p", "scripts": {**({"test": script} if script is not None else {}), **scripts}})


def test_the_reader_is_a_source_of_the_pre_map():
    assert npm_tests in premap.SOURCES and npm_tests.RANK == "reader"


def test_the_test_script_of_a_package_names_its_runner(tmp_path):
    found = declared(tmp_path, {
        "package.json": package("cross-env NODE_ENV=test jest --coverage"),
        "cra/package.json": package("react-scripts test"),
        "vite/package.json": package("vitest run"),
        "mocha/package.json": package("c8 mocha --recursive"),
        "node/package.json": package("node --experimental-vm-modules --test test/"),
        "tap/package.json": package("tap test/*.js"),
        "bun/package.json": package("bun test --coverage"),
        "turbo/package.json": package("turbo run --filter=web test"),
        "built/package.json": package("turbo run build && jest"),  # turbo builds, Jest runs the tests
        "through/package.json": package("npm run lint && yarn test:unit", **{"test:unit": "mocha", "lint": "eslint ."}),
    })
    assert found == [
        {"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test", "args": []},
        {"root": "built", "runner": "jest", "declared_in": "built/package.json#scripts.test", "args": []},
        {"root": "bun", "runner": "bun", "declared_in": "bun/package.json#scripts.test", "args": []},
        {"root": "cra", "runner": "jest", "declared_in": "cra/package.json#scripts.test", "args": []},
        {"root": "mocha", "runner": "mocha", "declared_in": "mocha/package.json#scripts.test", "args": []},
        {"root": "node", "runner": "node:test", "declared_in": "node/package.json#scripts.test", "args": []},
        # a script that names none of them is npm's to run: the runner is whatever it starts
        {"root": "tap", "runner": "npm", "declared_in": "tap/package.json#scripts.test", "args": []},
        {"root": "through", "runner": "mocha", "declared_in": "through/package.json#scripts.test", "args": []},
        {"root": "turbo", "runner": "turbo", "declared_in": "turbo/package.json#scripts.test", "args": []},
        {"root": "vite", "runner": "vitest", "declared_in": "vite/package.json#scripts.test", "args": []}]


def test_a_playwright_script_names_playwright_as_its_runner(tmp_path):
    """eShop: the root package.json declares only `test:e2e`, `playwright test`; the full-stack FastAPI template's
    frontend `test` is `bunx playwright test`. Playwright is their runner, not npm's whatever, and the run that
    never ends (`--ui`, the Inspector's `--debug`) does not declare it."""
    found = declared(tmp_path, {
        "package.json": package(None, **{"test:e2e": "playwright test", "test:e2e:ui": "playwright test --ui"}),
        "frontend/package.json": package("bunx playwright test", **{"test:ui": "bunx playwright test --ui"}),
        "debug/package.json": package(None, **{"e2e:debug": "npx playwright test --debug"})})
    assert found == [
        {"root": ".", "runner": "playwright", "declared_in": "package.json#scripts.test:e2e", "args": []},
        {"root": "frontend", "runner": "playwright", "declared_in": "frontend/package.json#scripts.test", "args": []}]
    record = premapped(tmp_path / "debug", {"package.json": package(None, **{"e2e": "npx playwright test --debug"})})
    [gap] = [gap for gap in record["gaps"] if gap["kind"] == "tests_not_declared"]
    assert (gap["runner"], gap["scripts"]) == ("playwright", ["e2e"])


def test_a_package_without_a_test_script_states_nothing(tmp_path):
    assert declared(tmp_path, {
        "package.json": package(None, build="tsc"),
        "init/package.json": package('echo "Error: no test specified" && exit 1'),
        "broken/package.json": "{not json"}) == []


def test_a_runner_the_test_script_does_not_reach_runs_through_its_plainest_script(tmp_path):
    """tududi's scripts: `npm test` runs Jest in backend/ (`cd backend`); the frontend's Jest at the root runs once,
    through the script with the fewest arguments after `jest` that does not watch. Where every one watches (or waits
    for a debugger), they are a gap that names them."""
    record = premapped(tmp_path, {
        "package.json": package("npm run backend:test", **{
            "backend:test": "cd backend && cross-env NODE_ENV=test jest --maxWorkers=4",
            "backend:test:unit": "cd backend && cross-env NODE_ENV=test jest tests/unit",
            "backend:test:coverage": "cd backend && cross-env NODE_ENV=test jest --coverage",
            "frontend:test": "jest", "frontend:test:watch": "jest --watch", "frontend:test:coverage": "jest --coverage",
            "test:watch": "npm run frontend:test:watch",
            "test:coverage": "npm run frontend:test:coverage && npm run backend:test:coverage",
            "test:ui": "bash e2e/bin/run-e2e.sh && echo \"Success!\"", "lint": "eslint ."}),
        # Vitest without `run` watches; `-w` is Jest's --maxWorkers, --watchAll=false turns its watch off
        "web/package.json": package(None, **{"test:unit": "vitest run --coverage", "check": "vitest run",
                                             "test:dev": "vitest", "spec": "jest -w 2 --watchAll=false"}),
        "watch/package.json": package("mocha", **{
            "spec:watch": "jest --watchAll", "spec:dev": "npm run spec:once -- --watch", "spec:once": "jest --ci",
            "spec:debug": "node --inspect-brk node_modules/.bin/jest --runInBand"})})
    assert [{k: v for k, v in item.items() if k != "sources"} for item in record["tests"]] == [
        entry(".", "jest"), {**entry(".", "jest"), "declared_in": "package.json#scripts.frontend:test"},
        {**entry("watch", "mocha")}, {**entry("watch", "jest"), "declared_in": "watch/package.json#scripts.spec:once"},
        {**entry("web", "jest"), "declared_in": "web/package.json#scripts.spec"},
        {**entry("web", "vitest"), "declared_in": "web/package.json#scripts.check"}]
    assert not [gap for gap in record["gaps"] if gap["kind"] == "tests_not_declared"]
    record = premapped(tmp_path / "only", {"package.json": package("mocha", **{
        "spec:watch": "jest --watchAll", "spec:dev": "npm run spec:watch -- --coverage",
        "spec:debug": "node --inspect-brk node_modules/.bin/jest --runInBand"})})
    assert [item["declared_in"] for item in record["tests"]] == ["package.json#scripts.test"]
    [gap] = [gap for gap in record["gaps"] if gap["kind"] == "tests_not_declared"]
    assert (gap["path"], gap["runner"], gap["scripts"]) == ("package.json", "jest",
                                                            ["spec:debug", "spec:dev", "spec:watch"])
    assert "jest in ." in gap["detail"] and "it starts mocha in ." in gap["detail"] and "watch" in gap["detail"]


# --- the plan: from the pre-map alone --------------------------------------------------------------------------

def record(tests: list[dict], units: list[str] = (".",), **more) -> dict:
    return {"units": [{"name": f"p{n}", "kind": "npm-package", "root": root} for n, root in enumerate(units)],
            "tests": tests, **more}


def entry(root: str, runner: str) -> dict:
    manifest = "package.json" if root == "." else f"{root}/package.json"
    return {"root": root, "runner": runner, "declared_in": f"{manifest}#scripts.test", "args": []}


def test_the_plan_runs_each_declared_test_script():
    planned = observer.plan(record([entry("b", "mocha"), entry(".", "jest"), {
        "root": "py", "runner": "pytest", "declared_in": "py/pytest.ini", "args": []}], units=(".", "b"),
        toolchains=[{"tool": "node", "version": "20.11.1", "declared_in": ".nvmrc"},
                    {"tool": "python", "version": "3.12", "declared_in": ".python-version"}]), [], None)
    assert planned["gaps"] == []
    assert planned["runs"] == [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"},
                               {"root": "b", "runner": "mocha", "declared_in": "b/package.json#scripts.test"}]
    assert planned["roots"] == ["", "b"]  # the package folders the pre-map names: where the restores run
    assert planned["toolchains"] == [{"tool": "node", "version": "20.11.1", "declared_in": ".nvmrc"}]


def test_no_declared_test_script_is_a_gap_and_nothing_runs():
    planned = observer.plan(record([{"root": ".", "runner": "pytest", "declared_in": "pytest.ini", "args": []}]),
                            [], None)
    assert planned["runs"] == []
    [gap] = planned["gaps"]
    assert gap["kind"] == "no_test_command" and "test script" in gap["detail"]


def test_a_runner_the_recorder_cannot_observe_is_a_gap_with_its_cause():
    planned = observer.plan(record([entry(".", "bun"), entry("b", "node:test"), entry("v", "vitest")],
                                   units=(".", "b", "v")), [], None)
    assert [run["root"] for run in planned["runs"]] == ["b", "v"]  # Vitest's Vite prints with a map: it runs
    [gap] = planned["gaps"]
    assert gap["kind"] == "runner_not_observed" and gap["path"] == "package.json#scripts.test"
    assert gap["runner"] == "bun" and "JavaScriptCore" in gap["detail"]


ASPIRE_HOST = ('<Project Sdk="Aspire.AppHost.Sdk/13.6.0">\n  <PropertyGroup><OutputType>Exe</OutputType>'
               '</PropertyGroup>\n</Project>\n')
ESHOP = {"package.json": package(None, **{"test:e2e": "playwright test"}),
         "playwright.config.ts": "export default defineConfig({\n  testDir: './e2e',\n  webServer: {\n"
                                 "    command: 'dotnet run --project src/eShop.AppHost/eShop.AppHost.csproj',\n"
                                 "    url: 'http://localhost:5045',\n  },\n});\n",
         "src/eShop.AppHost/eShop.AppHost.csproj": ASPIRE_HOST}


def test_playwright_s_tests_whose_web_server_is_an_aspire_app_host_need_a_container_engine(tmp_path):
    """eShop's only JavaScript tests are Playwright's (`test:e2e`), whose webServer is `dotnet run` of its Aspire app
    host: the host starts Redis, RabbitMQ and PostgreSQL as containers, which the execution cannot, so the script is
    the gap a C# test project that is such a host is (`dynamic/dotnet.py`), with the line that names the host."""
    tests = declared(tmp_path, ESHOP)
    assert tests == [{"root": ".", "runner": "playwright", "declared_in": "package.json#scripts.test:e2e", "args": []}]
    planned = observer.plan(record(tests), sorted(ESHOP), ESHOP.get)
    assert planned["runs"] == []
    [gap] = planned["gaps"]
    assert (gap["kind"], gap["path"], gap["runner"]) == ("tests_need_container_engine", "package.json#scripts.test:e2e",
                                                         "playwright")
    assert "playwright.config.ts:4" in gap["detail"] and "src/eShop.AppHost/eShop.AppHost.csproj" in gap["detail"]
    assert "Aspire app host" in gap["detail"] and "container engine" in gap["detail"]


def test_a_playwright_web_server_that_is_no_aspire_app_host_runs():
    """A webServer that starts a dev server, or `dotnet run` of a project that is no app host, starts in the
    container: the tests run, and their webServer's process inherits the recorder. Playwright stops it with SIGKILL
    unless `gracefulShutdown` says otherwise; the recorder writes as it goes, so what it ran up to its last write is
    recorded (`test_a_process_killed_with_sigkill_leaves_the_calls_it_made_before`)."""
    web = {"api/Api.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web" />'}
    e2e = {**entry(".", "playwright"), "declared_in": "package.json#scripts.test:e2e"}
    for command, files in (("bun run dev", {}), ("dotnet run --project api/Api.csproj", web)):
        files = {**ESHOP, **files, "playwright.config.ts": ESHOP["playwright.config.ts"].replace(
            "dotnet run --project src/eShop.AppHost/eShop.AppHost.csproj", command)}
        planned = observer.plan(record([e2e]), sorted(files), files.get)
        assert planned["gaps"] == []
        assert planned["runs"] == [{key: e2e[key] for key in ("root", "runner", "declared_in")}]


def test_fastapi_s_playwright_tests_run_as_before(tmp_path):
    """The full-stack FastAPI template: the root `test` is `bun run --filter frontend test`, the frontend's `bunx
    playwright test`, whose webServer is `bun run dev`. Both scripts run, as before Playwright was a runner: with
    the stack up, those tests reach the backend."""
    root = {"name": "fastapi-full-stack-template", "workspaces": ["frontend"],
            "scripts": {"test": "bun run --filter frontend test", "test:ui": "bun run --filter frontend test:ui"}}
    files = {"package.json": json.dumps(root),
             "frontend/package.json": package("bunx playwright test", **{"test:ui": "bunx playwright test --ui"}),
             "frontend/playwright.config.ts": "export default defineConfig({\n  webServer: "
                                              "process.env.PLAYWRIGHT_BASE_URL\n    ? undefined\n    : {\n"
                                              "        command: 'bun run dev',\n        url: baseURL,\n      },\n"
                                              "});\n"}
    tests = declared(tmp_path, files)
    planned = observer.plan(record(tests, units=(".", "frontend")), sorted(files), files.get)
    assert planned["gaps"] == []
    assert planned["runs"] == [{"root": ".", "runner": "npm", "declared_in": "package.json#scripts.test"},
                               {"root": "frontend", "runner": "playwright",
                                "declared_in": "frontend/package.json#scripts.test"}]
    played = Played({}, {"execute.log": "DAODAN-DYNAMIC 0 exit 1 3\nDAODAN-DYNAMIC 1 exit 1 2\n"})
    observe(tmp_path, played, runs=planned["runs"], files=files)
    execute = played.given["command"][-1]
    assert "\nrun 0 . test\n" in execute and "\nrun 1 frontend test\n" in execute


def test_a_script_that_runs_bun_has_the_bun_the_project_declares(tmp_path):
    """real-app-full-stack-fastapi: `test` is `bun run --filter frontend test`, and the frontend's `bunx
    playwright test`; its workflows set up Bun 1.3.12. The preparation installs that Bun with mise beside the
    stated Node, so the script runs: what Bun's engine runs itself is not recorded, what it starts on Node is."""
    bun = {"tool": "bun", "version": "1.3.12", "declared_in": ".github/workflows/playwright.yml"}
    planned = observer.plan(record([entry(".", "npm")], toolchains=[bun, {"tool": "python", "version": "3.14",
                                                                         "declared_in": ".python-version"}]), [], None)
    assert planned["runs"] and planned["toolchains"] == [bun]
    prepare, _execute, chains = observer.scripts(planned, [])
    assert "install bun@1.3.12" in prepare and set(preparation.GITHUB) <= set(chains["hosts"])


def test_a_run_declared_by_another_script_runs_that_script(tmp_path):
    frontend = {**entry(".", "jest"), "declared_in": "package.json#scripts.frontend:test"}
    planned = observer.plan(record([entry(".", "jest"), frontend]), [], None)
    assert planned["runs"] == [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"},
                               {"root": ".", "runner": "jest", "declared_in": "package.json#scripts.frontend:test"}]
    played = Played({"tests-1.log": "No tests found, exiting with code 1\n"},
                    {"execute.log": "DAODAN-DYNAMIC 0 exit 0 3\nDAODAN-DYNAMIC 1 exit 1 2\n"})
    result = observe(tmp_path, played, runs=planned["runs"])
    execute = played.given["command"][-1]
    assert f'timeout -k 30 {observer.LIMIT} npm run "$3"' in execute
    assert "\nrun 0 . test\n" in execute and "\nrun 1 . frontend:test\n" in execute
    assert [test["declared_in"] for test in result["runs"]] == ["package.json#scripts.test",
                                                                 "package.json#scripts.frontend:test"]
    assert any(gap["detail"].startswith("npm run frontend:test in . exited with code 1") for gap in result["gaps"])


def test_tests_no_declared_command_runs_are_said_with_the_runs_or_in_their_place(tmp_path):
    named = {"kind": "tests_not_declared", "path": "package.json", "runner": "jest", "scripts": ["frontend:test"],
             "detail": "package.json: frontend:test starts jest in . and its `test` script does not",
             "source": "npm-tests@daodan/premap/v4"}
    said = {key: value for key, value in named.items() if key != "source"}
    planned = observer.plan(record([entry(".", "jest")], gaps=[named]), [], None)
    assert planned["gaps"] == [] and planned["unrun"] == [said]  # with the runs' outcome, where a language's is
    played = Played({"tests-0.log": "ok\n"}, {"execute.log": "DAODAN-DYNAMIC 0 exit 0 3\n"})
    assert said in observe(tmp_path, played, unrun=planned["unrun"])["gaps"]
    planned = observer.plan(record([], gaps=[named]), [], None)  # nothing runs: the reason why
    assert planned["runs"] == [] and [gap["kind"] for gap in planned["gaps"]] == ["no_test_command",
                                                                                  "tests_not_declared"]


# --- the observation: one container run ------------------------------------------------------------------------

def site(file: str, line: int, column: int, name: str, *callees: dict) -> dict:
    return {"file": file, "line": line, "column": column, "name": name, "callees": list(callees)}


FIRST = {"kind": "project", "file": "src/index.js", "name": "first", "line": 2, "column": 0, "type": "function"}
LODASH = {"kind": "package", "module": "lodash", "version": "4.17.21", "name": "head", "line": 10}


def observed(*sites: dict, unobserved=(), final: bool = True) -> str:
    return json.dumps({"exact": True, "final": final, "node": "24.22.3", "stats": {}, "unobserved": list(unobserved),
                       "sites": list(sites)})


class Played:
    """In place of `container.run_in_container`: keeps what it is given, plays `files` (under the outputs' folder)
    and `logs` (the phases' logs) into the run's folder, and answers `result`."""

    def __init__(self, files: dict | None = None, logs: dict | None = None, result: dict | None = None):
        self.files, self.logs, self.result, self.given = files or {}, logs or {}, result, None

    def __call__(self, project, command, **options):
        self.given = {"project": project, "command": command, **options}
        out_dir = Path(options["out_dir"])
        for name, text in self.logs.items():
            write(out_dir, {name: text})
        write(out_dir / "out", self.files)
        return self.result or {"state": "done", "exit_code": 0, "outputs": sorted(self.files)}


def observe(tmp_path, played: Played, runs: list[dict] | None = None, files: dict = PROJECT, free=64 * 2**30,
            **planned) -> dict:
    """The observer over `files` with `played` as the container, on a host with `free` bytes of memory free."""
    project = write(tmp_path / "proj", files)
    runs = runs if runs is not None else [{"root": ".", "runner": "node:test",
                                           "declared_in": "package.json#scripts.test"}]
    with mock.patch.object(container, "run_in_container", played), \
            mock.patch.object(container, "free_memory", return_value=free), \
            mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)):
        result = observer.observe(project, {"runs": runs, "gaps": [], "roots": [""], "toolchains": [], **planned},
                                  tmp_path / "runs")
        played.inputs = played.given["inputs"]() if played.given else None
    return result


def test_the_preparation_reaches_the_hosts_the_project_declares(tmp_path):
    played = Played({"tests-0.log": "ok\n"}, {"execute.log": "DAODAN-DYNAMIC 0 exit 0 3\n"})
    observe(tmp_path, played, declared={"hosts": ("npm.corp.example",), "where": {}})  # as dynamic.run adds it
    assert "npm.corp.example" in played.given["registries"]


def test_what_the_copy_of_the_project_left_out_is_a_gap_of_the_run(tmp_path):
    """A link Git tracks to outside the project stays out of the copy (`container.copy_perimeter`)."""
    left = {"kind": "link_outside", "path": "x.js", "target": "../y.js", "detail": "x.js links outside"}
    played = Played({"tests-0.log": "ok\n"}, {"execute.log": "DAODAN-DYNAMIC 0 exit 0 3\n"},
                    {"state": "done", "exit_code": 0, "outputs": [], "gaps": [left]})
    assert left in observe(tmp_path, played)["gaps"]


def test_the_tests_run_on_the_cpus_and_memory_of_the_ci_runner(tmp_path):
    """mix-real-tududi: Jest starts a worker per CPU it sees but one, and the engine's host showed it 20; workers
    under the recorder take 2 to 3 GB each, and the 4 GB container killed them (SIGKILL). The tests run as on
    the runner GitHub hosts for the CI (ubuntu-latest: 4 CPUs, 16 GB): the memory, and the first 4 CPUs the
    container may use, the affinity runners count their workers by. That shape is the ceiling: a host with less
    memory free pins as many CPUs as it carries at `WORKER` each (tududi's Jest: 4 processes, 9.9 GB), at least
    one, with that memory; with not even one, no container starts and the gap says why. Each run says its shape."""
    assert (observer.CPUS, observer.MEMORY, observer.WORKER) == (4, 16 * 2**30, 5 * 2**29)
    for free, cpus, memory in ((64 * 2**30, 4, 16 * 2**30), (None, 4, 16 * 2**30), (12 * 2**30, 4, 10 * 2**30),
                               (6 * 2**30, 2, 5 * 2**30), (3 * 2**30, 1, 5 * 2**29)):
        played = Played({"tests-0.log": "ok\n"}, {"execute.log": "DAODAN-DYNAMIC 0 exit 0 3\n"})
        [run] = observe(tmp_path, played, free=free)["runs"]
        assert (played.given["memory"], run["cpus"], run["memory"]) == (memory, cpus, memory)
        execute = played.given["command"][-1]
        assert observer.pinned(cpus) in execute and '${cpus:+taskset -c "$cpus"} timeout' in execute
    played = Played()
    result = observe(tmp_path, played, free=2 * 2**30)
    assert played.given is None and result["state"] == "gap" and "2.0 GB of memory free" in result["cause"]
    if shutil.which("taskset") is None or not hasattr(os, "sched_getaffinity"):
        pytest.skip("taskset and CPU affinity are Linux's")
    done = subprocess.run(["sh", "-c", f'{observer.pinned(observer.CPUS)}; echo "$cpus"'], capture_output=True,
                          text=True)
    chosen = [int(cpu) for cpu in done.stdout.strip().split(",")]
    allowed = sorted(os.sched_getaffinity(0))
    assert chosen == allowed[:observer.CPUS]


def test_the_tests_run_as_declared_under_the_recorder_and_only_in_the_container(tmp_path):
    played = Played({"observed-0-7-0.json": observed(site("test/index.test.js", 5, 25, "first", FIRST)),
                     "tests-0.log": "ok\n"}, {"execute.log": "DAODAN-DYNAMIC 0 exit 0 3\n"})
    result = observe(tmp_path, played, files={**PROJECT, "package-lock.json": "{}"})
    given = played.given
    prepare, execute = given["prepare"][-1], given["command"][-1]
    # the preparation, with the registries: Node, the Babel the recorder prints with, the project's own restore
    assert "node-v" in prepare and f"@babel/core@{observer.BABEL}" in prepare
    assert "npm ci" in prepare and "for f in '.'" in prepare
    assert set(preparation.NODE_REGISTRIES) <= set(given["registries"])
    # the execution: the declared script, the recorder preloaded, nothing of the project changed
    assert 'NODE_OPTIONS="--require /daodan/state/in/javascript_record.js"' in execute
    assert "DYN_ROOT=/work" in execute and "DYN_BABEL=/daodan/state/tools/npm/lib/node_modules/@babel/core" in execute
    assert "TURBO_ENV_MODE=loose" in execute  # Turborepo's tasks get the recorder's variables too
    assert f'timeout -k 30 {observer.LIMIT} npm run "$3"' in execute and "\nrun 0 . test\n" in execute
    assert "npm ci" not in execute and "npm install" not in execute
    assert played.inputs["/daodan/state/in/javascript_record.js"] == observer.RECORDER
    assert given["outputs"] == ["/daodan/out"] and given["env"]["CI"] == "true"
    assert result["state"] == "ran" and result["gaps"] == []
    assert result["runs"] == [{"root": ".", "runner": "node:test", "declared_in": "package.json#scripts.test",
                               "state": "ran", "exit_code": 0, "seconds": 3, "processes": 1,
                               "cpus": observer.CPUS, "memory": observer.MEMORY}]
    assert result["sites"] == [{**site("test/index.test.js", 5, 25, "first", FIRST), "role": "call"}]


def test_the_sites_of_every_process_are_one_observation(tmp_path):
    native = {"kind": "native", "name": "map", "line": 0}
    mocked = {"kind": "package", "module": "jest-mock", "version": "29.7.0", "name": "mockConstructor", "line": 3}
    unplaced = {"kind": "project", "file": "src/index.js", "name": "first", "line": 2}
    played = Played({
        "observed-0-7-0.json": observed(site("a.js", 1, 2, "f", FIRST), site("a.js", 2, 0, "map", native)),
        "observed-0-8-0.json": observed(site("a.js", 1, 2, "f", LODASH, mocked), site("a.js", 3, 0, "g", unplaced)),
        "observed-0-9-0.json": '{"exact": true, "sites": [',  # a process killed while it wrote
    }, {"execute.log": "DAODAN-DYNAMIC 0 exit 0 9\n"})
    result = observe(tmp_path, played)
    by_place = {(found["line"], found["name"]): found for found in result["sites"]}
    assert all(found["role"] == "call" for found in result["sites"])
    callees = by_place[(1, "f")]["callees"]
    assert FIRST in callees and LODASH in callees and {**mocked, "mock": True} in callees  # a mock stands for another
    assert by_place[(2, "map")]["callees"] == [{**native, "version": "24.22.3"}]  # the runtime's, at Node's version
    assert observer.external(native | {"version": "24.22.3"}) == {"manager": "node", "package": "node",
                                                                  "version": "24.22.3"}
    assert observer.external(LODASH) == {"manager": "npm", "package": "lodash", "version": "4.17.21"}
    # a project callee the recorder could not place in its source keeps its line, and it is said
    assert by_place[(3, "g")]["callees"] == [{**unplaced, "column": None, "type": "function"}]
    [gap] = result["gaps"]
    assert gap["kind"] == "callee_unplaced" and gap["count"] == 1
    assert result["runs"][0]["processes"] == 3


@pytest.mark.parametrize("mark, files, kind, state, said", [
    ("exit 1 4", {"tests-0.log": "sh: 1: jest: not found\n"}, "tests_not_started", "not_started", "jest: not found"),
    ("exit 1 4", {"tests-0.log": "1 failing\n", "observed-0-7-0.json": observed(site("a.js", 1, 2, "f", FIRST))},
     "tests_failed", "ran", "1 failing"),
    ("exit 124 3600", {"tests-0.log": "", "observed-0-7-0.json": observed(site("a.js", 1, 2, "f", FIRST))},
     "tests_timeout", "timeout", "3600 s"),
    ("exit 0 2", {"tests-0.log": "ok\n"}, "nothing_recorded", "ran", "no call"),
    ("exit 0 2", {"tests-0.log": "ok\n", "observed-0-7-0.json": observed(site("a.js", 1, 2, "f", FIRST),
                                                                         unobserved=["src/a.ts", "src/b.ts"])},
     "not_observed", "ran", "2 files"),
    ("exit 1 2", {"tests-0.log": "Error: connect ECONNREFUSED 127.0.0.1:5432\n",
                  "observed-0-7-0.json": observed(site("a.js", 1, 2, "f", FIRST))},
     "services_unreachable", "ran", "(127.0.0.1:5432 ×1): the tests run with no network and with only the services"),
    ("exit 0 2", {"tests-0.log": "ok\n", "observed-0-7-0.json": observed(site("a.js", 1, 2, "f", FIRST)),
                  "observed-0-9-0.json": observed(site("a.js", 2, 0, "f", FIRST), final=False)},
     "processes_killed", "ran", "1 process of the run ended with no exit handler"),
    (None, {}, "tests_not_started", "not_started", "before the tests' exit"),
    ("exit 0 1", {"tests-0.log": "ℹ tests 0\nℹ suites 0\nℹ pass 0\n"}, "no_tests", "no_tests", "no test"),
])
def test_what_did_not_happen_is_a_gap_with_its_cause(tmp_path, mark, files, kind, state, said):
    played = Played(files, {"execute.log": f"DAODAN-DYNAMIC 0 {mark}\n" if mark else ""})
    result = observe(tmp_path, played)
    assert result["state"] == "ran" and result["runs"][0]["state"] == state
    gap = next(gap for gap in result["gaps"] if gap["kind"] == kind)
    assert gap["path"] == "." and said in gap["detail"]


def test_a_turbo_run_that_recorded_nothing_names_turbo_and_why(tmp_path):
    """Turborepo's strict env mode passes NODE_OPTIONS but not the recorder's own variables: the run sets
    TURBO_ENV_MODE=loose, which a turbo before 2.1.0, or a script's --env-mode=strict, does not follow."""
    [run] = observer.plan(record([entry(".", "turbo")]), [], None)["runs"]
    played = Played({"tests-0.log": "Tasks:    2 successful, 2 total\n"},
                    {"execute.log": "DAODAN-DYNAMIC 0 exit 0 4\n"})
    [gap] = observe(tmp_path, played, runs=[run])["gaps"]
    assert gap["kind"] == "nothing_recorded" and gap["runner"] == "turbo"
    assert "TURBO_ENV_MODE=loose" in gap["detail"] and "2.1.0" in gap["detail"] and "--env-mode" in gap["detail"]


def test_the_error_above_the_runner_s_summary_is_said(tmp_path):
    """`node --test test/` on Node 21 and later: a folder is no pattern, Node runs it as a module and fails, and
    the runner's summary below the error fills the log's tail."""
    log = ("> node --test test/\n\nnode:internal/modules/cjs/loader:1568\n  throw err;\n  ^\n\n"
           "Error: Cannot find module '/work/test'\n    at Module._resolveFilename (node:internal/...)\n"
           + "".join(f"ℹ line {n}\n" for n in range(12)) + "✖ test (239ms)\n  'test failed'\n")
    played = Played({"tests-0.log": log}, {"execute.log": "DAODAN-DYNAMIC 0 exit 1 0\n"})
    [gap] = observe(tmp_path, played)["gaps"]
    assert gap["kind"] == "tests_not_started" and "Error: Cannot find module '/work/test'" in gap["detail"]
    assert "'test failed'" in gap["detail"]


def test_a_restore_that_failed_and_a_missing_tool_are_gaps(tmp_path):
    played = Played({"tests-0.log": "Cannot find module 'ms'\n"}, {
        "prepare.log": "DAODAN-RESTORE-FAILED npm .\nnpm error code E404\nDAODAN-RESTORE-END\n",
        "execute.log": "DAODAN-DYNAMIC 0 exit 1 1\n"})
    result = observe(tmp_path, played)
    kinds = [gap["kind"] for gap in result["gaps"]]
    assert kinds == ["restore_failed", "tests_not_started"]
    played = Played(logs={"prepare.log": f"DAODAN-MISSING @babel/core@{observer.BABEL}\n"},
                    result={"state": "failed", "cause": "the preparation exited with code 70"})
    result = observe(tmp_path, played)
    assert result["state"] == "failed" and "@babel/core" in result["cause"] and result["sites"] == []


def test_without_a_container_the_observation_is_a_gap(tmp_path):
    played = Played(result={"state": "gap", "cause": "no container engine", "remedy": "install one"})
    result = observe(tmp_path, played)
    assert (result["state"], result["cause"], result["remedy"]) == ("gap", "no container engine", "install one")
    assert result["sites"] == [] and result["runs"] == []


def test_a_former_observation_is_not_this_run_s(tmp_path):
    write(tmp_path / "runs/out", {"observed-0-1-0.json": observed(site("old.js", 1, 2, "f", FIRST))})
    played = Played({"tests-0.log": "ok\n"}, {"execute.log": "DAODAN-DYNAMIC 0 exit 0 1\n"})
    assert observe(tmp_path, played)["sites"] == []


# --- the recorder, under a real Node ---------------------------------------------------------------------------

def babel() -> str | None:
    """The folder of a @babel/core for the recorder: DAODAN_TEST_BABEL, else the one this repository resolves."""
    named = os.environ.get("DAODAN_TEST_BABEL")
    if named:
        return named if (Path(named) / "package.json").is_file() else None
    found = subprocess.run(["node", "-p", "require('path').dirname(require.resolve('@babel/core/package.json'))"],
                           cwd=HERE.parent, capture_output=True, text=True)
    return found.stdout.strip() if found.returncode == 0 else None


@pytest.fixture(scope="module")
def node():
    if shutil.which("node") is None:
        pytest.skip("Node is not installed: the recorder runs only under a real Node")
    found = babel()
    if found is None:
        pytest.skip("no @babel/core for the recorder: name its folder in DAODAN_TEST_BABEL")
    return found


def recorded(project: Path, out: Path, babel_dir: str, *command: str, env: dict | None = None) -> list[dict]:
    """The observation files of `command` (default: `node --test`) run in `project` under the recorder."""
    out.mkdir(parents=True, exist_ok=True)
    environment = {key: value for key, value in os.environ.items() if not key.startswith(("NODE_", "DYN_"))}
    environment.update({"NODE_OPTIONS": f"--require {observer.RECORDER.as_posix()}", "DYN_ROOT": str(project),
                        "DYN_OUT": str(out / "observed-0-%p.json"), "DYN_BABEL": babel_dir, **(env or {})})
    done = subprocess.run(["node", *(command or ("--test",))], cwd=project, env=environment, capture_output=True,
                          text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(out.glob("observed-0-*.json"))]


def places(sites: list[dict]) -> dict:
    """`{(file, line, column, name): {callee}}`, a callee as its declaration's place or its module."""
    def end(callee: dict) -> str:
        if callee["kind"] == "project":
            return f"{callee['file']}:{callee['line']}:{callee.get('column')} {callee['name']} {callee.get('type')}"
        return f"{callee['kind']} {callee.get('module', '')} {callee['name']}".replace("  ", " ")
    return {(found["file"], found["line"], found["column"], found["name"]): {end(callee) for callee in
                                                                              found["callees"]} for found in sites}


RECORDED = {
    ("test/index.test.js", 4, 0, "test"): {"runtime node:internal/test_runner/harness test"},
    ("test/index.test.js", 5, 9, "strictEqual"): {"runtime node:assert strictEqual"},
    ("test/index.test.js", 5, 25, "first"): {"src/index.js:2:0 first function"},
    ("test/index.test.js", 6, 9, "strictEqual"): {"runtime node:assert strictEqual"},
    ("test/index.test.js", 6, 25, "apply"): {"src/index.js:4:33 apply function"},
    ("src/index.js", 4, 44, "fn"): {"src/index.js:2:0 first function"},  # a callee that is a parameter
    ("test/index.test.js", 7, 9, "strictEqual"): {"runtime node:assert strictEqual"},
    ("test/index.test.js", 7, 31, "run"): {"src/index.js:2:0 first function"},  # a method of an object built at run time
    ("test/index.test.js", 8, 9, "strictEqual"): {"runtime node:assert strictEqual"},
    ("test/index.test.js", 8, 29, "make"): {"src/index.js:1:33 make function"},
    ("src/index.js", 1, 60, "Box"): {"src/index.js:1:0 Box class"},
    ("test/index.test.js", 8, 36, "size"): {"src/index.js:1:12 size function"},  # a method on an untyped value
    ("test/index.test.js", 9, 9, "strictEqual"): {"runtime node:assert strictEqual"},
    ("test/index.test.js", 9, 25, "base"): {"src/index.js:4:69 base function"},
    ("src/index.js", 4, 79, "basename"): {"runtime node:path basename"},
    ("test/index.test.js", 11, 9, "strictEqual"): {"runtime node:assert strictEqual"},
    ("test/index.test.js", 11, 26, "twice"): {"src/more.mjs:0:21 twice function"},  # an ES module, as written
    ("src/more.mjs", 0, 32, "fn"): {"src/more.mjs:1:7 inc function"},
    ("src/more.mjs", 0, 35, "fn"): {"src/more.mjs:1:7 inc function"},
}


def test_the_recorder_sees_every_call_of_the_sources_node_runs_as_written(tmp_path, node):
    project = write(tmp_path / "proj", PROJECT)
    files = recorded(project, tmp_path / "out", node)
    assert len(files) == 1 and files[0]["exact"] is True and files[0]["unobserved"] == []  # the runner's own
    # process has no inspector and records nothing; the test file's process is the observation
    assert places(files[0]["sites"]) == RECORDED
    assert files[0]["node"] == subprocess.run(["node", "-p", "process.versions.node"], capture_output=True,
                                              text=True).stdout.strip()


def test_code_another_tool_printed_is_not_recorded_and_its_file_is_named(tmp_path, node):
    project = write(tmp_path / "proj", {
        "lib.js": "module.exports = () => 1;\n",
        "main.js": 'const Module = require("module");\nconst path = require("path");\n'
                   'const file = path.join(__dirname, "lib.js");\nconst loaded = new Module(file);\n'
                   'loaded._compile("module.exports = () => 2;", file);\nloaded.exports();\n'})
    [file] = recorded(project, tmp_path / "out", node, "main.js")
    assert file["unobserved"] == ["lib.js"]
    assert ("main.js", 5, 7, "exports") in places(file["sites"])  # the caller is a source as written


def test_a_babel_the_run_loads_itself_prints_with_the_recorder_in_every_realm(tmp_path, node):
    """As babel-jest does: the run's own @babel/core prints a source, which runs in a context of its own."""
    project = write(tmp_path / "proj", {
        "lib.txt": "const pick = xs => xs.at(0);\npick([1]);\n",
        "harness.js": 'const fs = require("fs");\nconst path = require("path");\nconst vm = require("vm");\n'
                      'const file = path.join(__dirname, "lib.txt");\n'
                      'const printed = require("@babel/core").transformSync(fs.readFileSync(file, "utf8"),\n'
                      '  { filename: file, babelrc: false, configFile: false, sourceMaps: "both" });\n'
                      'vm.runInContext(printed.code, vm.createContext({}), { filename: file });\n'})
    [file] = recorded(project, tmp_path / "out", node, "harness.js",
                      env={"NODE_PATH": str(Path(node).parent.parent)})
    found = places(file["sites"])
    assert found[("lib.txt", 0, 22, "at")] == {"native at"}
    assert found[("lib.txt", 1, 0, "pick")] == {"lib.txt:0:13 pick function"}  # placed through the run's source map
    assert file["unobserved"] == []


HARNESS = '''const fs = require("fs");
const path = require("path");
const vm = require("vm");
const tool = require(process.env.TOOL);  // a Babel required by its folder: another tool, which is not hooked
const print = rel => {
  const file = path.join(__dirname, rel);
  return [file, tool.transformSync(fs.readFileSync(file, "utf8"),
    { filename: file, babelrc: false, configFile: false, compact: true, sourceMaps: "inline" }).code];
};
const [lib, libCode] = print("src/lib.js");
const prefix = "'use strict';async (module, exports)=>{{";
const one = { exports: {} };
vm.runInThisContext(`${prefix}${libCode}\\n}}`, { filename: lib, columnOffset: -prefix.length })(one, one.exports);
const [other, otherCode] = print("src/other.js");
const two = { exports: {} };
vm.compileFunction(otherCode, ["module", "exports"], { filename: other })(two, two.exports);
one.exports.run();
two.exports.go();
'''


def test_code_another_tool_printed_runs_recorded_through_its_inline_map(tmp_path, node):
    """As Vitest evaluates a module (wrapped, the wrapper's columns taken back by columnOffset) and Jest does
    (a function's body): another tool printed the code on one line, with its source map inline."""
    project = write(tmp_path / "proj", {
        "src/lib.js": "function inc(v) { return v + 1; } const twice = f => x => f(f(x));\n"
                      "module.exports = { inc, twice, run: () => twice(inc)(1) };\n",
        "src/other.js": "function half(n) { return n / 2; }\nexports.go = () => half(4);\n",
        "harness.js": HARNESS})
    [file] = recorded(project, tmp_path / "out", node, "harness.js", env={"TOOL": node})
    found = places(file["sites"])
    assert found[("src/lib.js", 0, 58, "f")] == found[("src/lib.js", 0, 60, "f")] == {"src/lib.js:0:0 inc function"}
    assert found[("src/lib.js", 1, 42, "twice")] == {"src/lib.js:0:48 twice function"}
    assert found[("src/other.js", 1, 19, "half")] == {"src/other.js:0:0 half function"}
    assert file["unobserved"] == []


BUNDLED = '''const fs = require("fs");
const path = require("path");
const vm = require("vm");
const tool = require(process.env.TOOL);
const lib = path.join(__dirname, "src/lib.js");
const code = tool.transformSync(fs.readFileSync(lib, "utf8"), { filename: lib, sourceFileName: "src/lib.js",
  babelrc: false, configFile: false, compact: true, sourceMaps: "inline" }).code;
const prefix = "'use strict';async (module, exports)=>{{";
const one = { exports: {} };
vm.runInThisContext(`${prefix}${code}\\n}}`, { filename: path.join(__dirname, "chunk-L.js"),
  columnOffset: -prefix.length })(one, one.exports);
one.exports.run();
'''


def test_a_bundle_no_file_holds_runs_recorded_in_the_files_its_inline_map_names(tmp_path, node):
    """real-app-jhipster-sample: Angular's unit-test builder bundles the sources into chunks (`chunk-*.js`, held
    in memory, no file of the project) that Vitest evaluates with their source map inline, whose sources are the
    files as written: a call is a site of the file the map leads to, where the same name is written there, and a
    function the bundle defines is placed in that file."""
    project = write(tmp_path / "proj", {
        "src/lib.js": "function inc(v) { return v + 1; } const twice = f => x => f(f(x));\n"
                      "module.exports = { inc, twice, run: () => twice(inc)(1) };\n",
        "bundle.js": BUNDLED})
    [file] = recorded(project, tmp_path / "out", node, "bundle.js", env={"TOOL": node})
    found = places(file["sites"])
    assert found[("src/lib.js", 0, 58, "f")] == found[("src/lib.js", 0, 60, "f")] == {"src/lib.js:0:0 inc function"}
    assert found[("src/lib.js", 1, 42, "twice")] == {"src/lib.js:0:48 twice function"}
    assert found[("bundle.js", 11, 12, "run")] == {"src/lib.js:1:36 run function"}
    assert file["unobserved"] == []


def test_typescript_node_strips_itself_is_recorded_as_written(tmp_path, node):
    """As `node --test "test/*.test.ts"` on a Node that strips the types itself, an ES module and a CommonJS one."""
    stripping = subprocess.run(["node", "-p", "Boolean(process.features.typescript)"], capture_output=True, text=True)
    if stripping.stdout.strip() != "true":
        pytest.skip("this Node does not strip TypeScript types (22.18, 23.6 and later do)")
    project = write(tmp_path / "proj", {
        "package.json": '{"type": "module"}\n',
        "src/lib.ts": "export function add(a: number, b: number): number { return a + b; }\n",
        "src/old.cts": "function half(n: number): number { return n / 2; }\nmodule.exports = { half };\n",
        "test/lib.test.ts": 'import { test } from "node:test";\nimport { add } from "../src/lib.ts";\n'
                            'import { createRequire } from "node:module";\n'
                            'const { half } = createRequire(import.meta.url)("../src/old.cts");\n\n'
                            'test("add", () => { add(1, 2); half(4); });\n'})
    [file] = recorded(project, tmp_path / "out", node, "--test", "test/*.test.ts")
    found = places(file["sites"])
    assert found[("test/lib.test.ts", 5, 20, "add")] == {"src/lib.ts:0:7 add function"}
    assert found[("test/lib.test.ts", 5, 31, "half")] == {"src/old.cts:0:0 half function"}
    assert file["unobserved"] == []


def hidden(tmp_path, *names: str) -> dict:
    """The recorder's environment under a Node without the module hooks `names`, as an older Node is."""
    lines = "".join(f"delete Module.{name};\nif (Module.{name}) Module.{name} = undefined;\n" for name in names)
    hide = write(tmp_path / "tools", {"hide.js": f'const Module = require("module");\n{lines}'})
    return {"NODE_OPTIONS": f"--require {(hide / 'hide.js').as_posix()} --require {observer.RECORDER.as_posix()}"}


def test_an_es_module_under_a_node_without_register_hooks_is_printed_on_the_hooks_thread(tmp_path, node):
    """mix-infra-gha: Node 20.18.1, which its .nvmrc states, has no module.registerHooks (22.15): its ES modules
    are printed by the hooks `module.register` runs on a thread of their own (18.19, 20.6), and recorded."""
    project = write(tmp_path / "proj", PROJECT)
    [file] = recorded(project, tmp_path / "out", node, env=hidden(tmp_path, "registerHooks"))
    assert file["unobserved"] == []
    found = places(file["sites"])
    assert found[("test/index.test.js", 11, 26, "twice")] == {"src/more.mjs:0:21 twice function"}
    assert found[("src/more.mjs", 0, 32, "fn")] == {"src/more.mjs:1:7 inc function"}


def test_a_file_that_ran_where_the_recorder_has_no_hook_is_named(tmp_path, node):
    """As under a Node with neither module hook (before 18.19 and 20.6): an ES module runs as it is, and is said."""
    project = write(tmp_path / "proj", PROJECT)
    [file] = recorded(project, tmp_path / "out", node, env=hidden(tmp_path, "registerHooks", "register"))
    assert file["unobserved"] == ["src/more.mjs"]
    assert ("test/index.test.js", 5, 25, "first") in places(file["sites"])


SERVER = {"lib.js": "function first(xs) { return xs[0]; }\nfunction later(xs) { return xs.length; }\n"
                    "module.exports = { first, later };\n",
          "server.js": "const lib = require('./lib');\nlib.first([1]);\nconsole.log('called');\n"
                       "process.stdin.once('data', () => { lib.later([2]); console.log('later'); });\n"
                       "setInterval(() => {}, 1000);\n"}


def test_a_process_killed_with_sigkill_leaves_the_calls_it_made_before(tmp_path, node):
    """Playwright stops its webServer with SIGKILL, as a runner may a worker that does not end: no handler runs. The
    recorder writes what it saw as it goes (`EVERY`), so the file of a killed process holds every call made before
    its last write."""
    project = write(tmp_path / "proj", SERVER)
    out = tmp_path / "out"
    out.mkdir()
    environment = {key: value for key, value in os.environ.items() if not key.startswith(("NODE_", "DYN_"))}
    environment.update({"NODE_OPTIONS": f"--require {observer.RECORDER.as_posix()}", "DYN_ROOT": str(project),
                        "DYN_OUT": str(out / "observed-0-%p.json"), "DYN_BABEL": node})
    server = subprocess.Popen(["node", "server.js"], cwd=project, env=environment, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, text=True)
    try:
        assert server.stdout.readline().strip() == "called"

        def written(*names: str) -> dict:
            for _ in range(100):  # up to 10 s: the recorder writes within its interval
                for path in out.glob("observed-0-*.json"):
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if set(names) <= {site["name"] for site in data["sites"]}:
                        return data
                time.sleep(0.1)
            raise AssertionError(f"no observation holds {names}: {sorted(p.name for p in out.iterdir())}")
        written("first")
        server.stdin.write("go\n")
        server.stdin.flush()
        assert server.stdout.readline().strip() == "later"
        written("first", "later")  # a call after a write: the next write holds it
    finally:
        server.send_signal(signal.SIGKILL)
        server.wait(timeout=30)
    assert server.returncode == -signal.SIGKILL
    [path] = out.glob("observed-0-*.json")  # the last write, whole: a write is a rename
    found = places(json.loads(path.read_text(encoding="utf-8"))["sites"])
    lines = SERVER["server.js"].split("\n")
    assert found[("server.js", 1, lines[1].index("first"), "first")] == {"lib.js:0:0 first function"}
    assert found[("server.js", 3, lines[3].index("later"), "later")] == {"lib.js:1:0 later function"}
    assert not list(out.glob("*.tmp"))


def recorder(project: Path, out: Path, babel_dir: str) -> dict:
    """The environment a script runs in under the recorder, as the observer sets it."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith(("NODE_", "DYN_"))}
    environment.update({"NODE_OPTIONS": f"--require {observer.RECORDER.as_posix()}", "DYN_ROOT": str(project),
                        "DYN_OUT": str(out / "observed-0-%p.json"), "DYN_BABEL": babel_dir})
    return environment


# 3,000 functions, each called from a site of its own, in five waves of 0.6 s through a fifth of the sites each:
# the sites grow while the process runs, and the recorder writes them as it goes.
FUNCTIONS, WAVES = 3000, 5
WAVED = {"lib.js": "".join(f"function f{n}(x) {{ return x + {n}; }}\n" for n in range(FUNCTIONS))
         + "module.exports = { " + ", ".join(f"f{n}" for n in range(FUNCTIONS)) + " };\n",
         "main.js": f"const {{ {', '.join(f'f{n}' for n in range(FUNCTIONS))} }} = require('./lib');\n"
         + "".join(f"function w{w}(t) {{\n" + "".join(f"  t += f{n}(t & 7);\n" for n in range(w, FUNCTIONS, WAVES))
                   + "  return t;\n}\n" for w in range(WAVES))
         + f"const waves = [{', '.join(f'w{w}' for w in range(WAVES))}];\nlet total = 0, calls = 0;\n"
         + "const started = Date.now();\n(async () => {\n  for (const wave of waves) {\n"
         + "    const until = Date.now() + 600;\n    while (Date.now() < until) {\n"
         + f"      for (let i = 0; i < 100; i++) {{ total = wave(total) & 0xffff; calls += {FUNCTIONS // WAVES}; }}\n"
         + "      await new Promise(resolve => setImmediate(resolve));\n    }\n  }\n"
         + "  console.log(JSON.stringify({ calls, ms: Date.now() - started }));\n})();\n"}


def test_the_writes_while_a_process_runs_take_less_than_a_tenth_of_its_time(tmp_path, node):
    """What writing as it goes costs (D-292): a write at most every second, and never sooner than ten times the last
    one's length after it, so the writes take less than a tenth of the run, whatever the sites. The calls the run
    made and the writes' share are printed: the measure of the cost."""
    project = write(tmp_path / "proj", WAVED)
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", "main.js"], cwd=project, env=recorder(project, out, node), capture_output=True,
                          text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-2000:]
    run = json.loads(done.stdout.strip().splitlines()[-1])
    [path] = out.glob("observed-0-*.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    stats = data["stats"]
    print("WAVED", json.dumps({**run, **stats, "bytes": path.stat().st_size}))
    assert data["final"] is True and stats["sites"] >= FUNCTIONS
    assert stats["writes"] >= 2  # the waves after the first wrote what they added
    assert stats["writing_ms"] < run["ms"] / 10


PLAYWRIGHT = "1.64.1"  # @playwright/test on npm, the version the proof below ran with
WEB_SERVER = {
    "package.json": json.dumps({"name": "pw", "private": True, "scripts": {"test:e2e": "playwright test"}}),
    "lib.js": "function answer(url) {\n  return url.length;\n}\nmodule.exports = { answer };\n",
    "server.js": "const http = require('http');\nconst { answer } = require('./lib');\n"
                 "http.createServer((req, res) => { res.end(String(answer(req.url))); }).listen(4173, '127.0.0.1');\n",
    "e2e/server.spec.js": "const { test, expect } = require('@playwright/test');\n"
                          "test('server', async ({ request }) => {\n"
                          "  const reply = await request.get('http://127.0.0.1:4173/abc');\n"
                          "  expect(await reply.text()).toBe('4');\n"
                          "  await new Promise(resolve => setTimeout(resolve, 2500));  // the server writes\n});\n",
    "playwright.config.js": "module.exports = {\n  testDir: './e2e',\n  workers: 1,\n  webServer: {\n"
                            "    command: 'node server.js',\n    url: 'http://127.0.0.1:4173/health',\n"
                            "    reuseExistingServer: false,\n  },\n};\n",
}


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_modal_playwright_s_web_server_is_recorded_when_playwright_kills_it(tmp_path, node):
    """D-198, D-292: `playwright test` (@playwright/test from npm) whose webServer is a Node server the spec calls
    over HTTP, run under the recorder as the observer runs a script. The server inherits NODE_OPTIONS; Playwright
    stops it with SIGKILL, so its file is the last one it wrote while it ran (`final: false`), with the calls the
    spec's request reached; with `gracefulShutdown` sending SIGTERM it writes at its exit."""
    npm = shutil.which("npm")
    project = write(tmp_path / "proj", WEB_SERVER)
    subprocess.run([npm, "install", "--no-audit", "--no-fund", "--ignore-scripts", f"@playwright/test@{PLAYWRIGHT}"],
                   cwd=project, check=True, capture_output=True, timeout=600)
    for shutdown, final in (("", False), ("    gracefulShutdown: { signal: 'SIGTERM', timeout: 5000 },\n", True)):
        (project / "playwright.config.js").write_text(WEB_SERVER["playwright.config.js"].replace(
            "  },\n};", f"{shutdown}  }},\n}};"), encoding="utf-8")
        out = tmp_path / f"out-{final}"
        out.mkdir()
        done = subprocess.run([npm, "run", "test:e2e"], cwd=project, env={**recorder(project, out, node), "CI": "1"},
                              capture_output=True, text=True, timeout=600)
        assert done.returncode == 0, (done.stdout + done.stderr)[-2000:]
        files = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(out.glob("observed-0-*.json"))]
        [server] = [data for data in files if any(site["file"] == "server.js" for site in data["sites"])]
        assert server["final"] is final
        found = places(server["sites"])
        column = WEB_SERVER["server.js"].split(chr(10))[2].index("answer")
        assert found[("server.js", 2, column, "answer")] == {"lib.js:0:0 answer function"}
        tests = [data for data in files if data is not server]
        assert any(site["file"] == "e2e/server.spec.js" for data in tests for site in data["sites"])
        assert all(data["final"] is True for data in tests)


# --- the join: what the recorder saw, on the snapshot's references ---------------------------------------------

def test_an_observed_site_joins_the_reference_at_the_same_name_position(tmp_path, monkeypatch):
    project = write(tmp_path / "proj", PROJECT)
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)

    def callee(end: str) -> dict:
        if end.startswith("runtime "):
            return {"kind": "runtime", "module": end.split()[1], "name": end.split()[2], "line": 0}
        place, name, kind = end.split()
        file, line, column = place.split(":")
        return {"kind": "project", "file": file, "line": int(line), "column": int(column), "name": name, "type": kind}

    sites = [site(*key, *(callee(end) for end in sorted(ends))) for key, ends in RECORDED.items()]
    played = Played({"observed-0-7-0.json": observed(*sites), "tests-0.log": "ok\n"},
                    {"execute.log": "DAODAN-DYNAMIC 0 exit 0 1\n"})
    sites = observe(tmp_path / "run", played)["sites"]
    with code_graph.Snapshot(manifest) as snap:
        rows, facts = dynamic.join(snap, "javascript", sites, [], observer)
        names = {identity: (rel, span[0], parts[-1] if parts else "")
                 for identity, rel, _kind, _resolution, _target, span, parts, _reason in snap.references("javascript")}
    assert facts["recorded"] == len(RECORDED) == facts["placed"] and not facts["unjoined"]
    assert all(row["confidence"] == "observed" and row["resolver"] == dynamic.resolver(observer) for row in rows)
    found: dict = {}
    for row in rows:
        end = row["target_id"] or row["external"]["package"]
        found.setdefault(names[row["reference_id"]], set()).add((row["verdict"], end))
    test, index = "test/index.test.js", "src/index.js"
    assert found[(test, 6, "first")] == {("project-callable", f"{index}::function@3:0")}
    assert found[(index, 5, "fn")] == {("project-callable", f"{index}::function@3:0")}
    assert found[(test, 8, "run")] == {("project-callable", f"{index}::function@3:0")}
    assert found[(test, 9, "size")] == {("project-callable", f"{index}::method@2:12")}
    assert found[(test, 9, "make")] == {("project-callable", f"{index}::method@2:33")}
    assert found[(index, 2, "Box")] == {("project-callable", f"{index}::class@2:0")}
    assert found[(test, 7, "apply")] == {("project-callable", f"{index}::function@5:33")}
    assert found[(test, 12, "twice")] == {("project-callable", "src/more.mjs::function@1:21")}
    assert found[("src/more.mjs", 1, "fn")] == {("project-callable", "src/more.mjs::function@2:7")}
    assert found[(index, 5, "basename")] == {("external", "node")}
    assert facts["files"]["executed"] == 3
