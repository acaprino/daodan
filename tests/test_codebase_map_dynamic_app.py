"""Starting the app the project declares in the container, waiting for its port, stopping it (plan task 11.2).

The planning and the reading of the outcome run here, the container played by a double (as the observer's tests do).
The driver, `dynamic/app.cjs`, starts code, so its tests run only on Modal (`tests/modal_pytest.py`).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_dynamic_app.py
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import container  # noqa: E402
import preparation  # noqa: E402
from dynamic import app  # noqa: E402
from test_codebase_map_dynamic_javascript import Played, write  # noqa: E402


def start(root: str, mode: str, script: str | None = None, runner: str = "npm", port=None, needs_build=False) -> dict:
    """A `starts` entry as `premap/npm_start.py` writes it."""
    return {"root": root, "mode": mode, "runner": runner, "argv": [runner, "run", script or mode], "surface": "web",
            "declared_in": f"{root}/package.json#scripts.{script or mode}"
            if root != "." else f"package.json#scripts.{script or mode}", "port": port, "needs_build": needs_build}


def build(root: str, runner: str = "npm") -> dict:
    return {"root": root, "runner": runner, "argv": [runner, "run", "build"],
            "declared_in": f"{root}/package.json#scripts.build" if root != "." else "package.json#scripts.build"}


# --- the plan --------------------------------------------------------------------------------------------------

def test_the_plan_starts_each_module_by_its_start_script_else_its_dev_script():
    record = {"starts": [start(".", "dev"), start(".", "start"), start("web", "dev", port=5000)]}
    planned = app.plan(record)
    assert [(one["root"], one["mode"], one["port"]) for one in planned["apps"]] == [(".", "start", None),
                                                                                    ("web", "dev", 5000)]
    assert planned["gaps"] == []


def test_a_start_that_needs_a_build_runs_the_modules_build_first():
    record = {"starts": [start("a", "start", needs_build=True), start("b", "dev")], "builds": [build("a")]}
    one, other = app.plan(record)["apps"]
    assert one["build"]["declared_in"] == "a/package.json#scripts.build" and "build" not in other


def test_a_start_that_needs_a_build_nobody_declares_does_not_run_and_says_why():
    record = {"starts": [start(".", "start", needs_build=True)],
              "gaps": [{"kind": "build_command_missing", "path": "package.json", "detail": "no build", "source": "x"}]}
    planned = app.plan(record)
    assert planned["apps"] == [] and [gap["kind"] for gap in planned["gaps"]] == ["build_command_missing"]


def test_pnpm_yarn_and_node_s_own_programs_run_and_a_runner_with_no_preparation_is_a_gap_with_its_name():
    """Node's own programs and the managers corepack runs as the restores do (`preparation.RESTORES`' `before`) have
    their preparation; a program none prepares is `start_runner_not_supported`, naming it."""
    assert set(app.COREPACK) == {"pnpm", "yarn"}
    user = {**start("api", "start", runner="node"), "argv": ["node", "server.js"], "declared_in": "commands.json"}
    planned = app.plan({"starts": [start(".", "dev", runner="pnpm"), start("web", "dev", runner="yarn"), user,
                                   start("deno", "dev", runner="deno")]})
    assert [(one["root"], one["argv"]) for one in planned["apps"]] == [
        (".", ["pnpm", "run", "dev"]), ("api", ["node", "server.js"]), ("web", ["yarn", "run", "dev"])]
    assert [(gap["kind"], gap["runner"], gap["path"]) for gap in planned["gaps"]] == [
        ("start_runner_not_supported", "deno", "deno/package.json#scripts.dev")]
    assert "no preparation" in planned["gaps"][0]["detail"]


def test_bun_runs_at_the_exact_version_the_pre_map_states_and_without_one_is_a_gap():
    """mise installs Bun at the version the project states (`preparation.toolchains`), never one it would pick."""
    record = {"starts": [start(".", "start", runner="bun")]}
    stated = app.plan({**record, "toolchains": [{"tool": "bun", "version": "1.2.2", "declared_in": ".bun-version"}]})
    assert [one["argv"] for one in stated["apps"]] == [["bun", "run", "start"]] and stated["gaps"] == []
    assert stated["toolchains"] == [{"tool": "bun", "version": "1.2.2", "declared_in": ".bun-version"}]
    for toolchains in ([], [{"tool": "bun", "version": ">=1.1", "declared_in": "package.json#engines"}]):
        planned = app.plan({**record, "toolchains": toolchains})
        assert planned["apps"] == [] and [(gap["kind"], gap["runner"]) for gap in planned["gaps"]] == [
            ("start_runner_not_supported", "bun")]
        assert "no exact bun version" in planned["gaps"][0]["detail"]


def test_a_build_whose_runner_has_no_preparation_keeps_its_start_from_running():
    record = {"starts": [start(".", "start", needs_build=True)], "builds": [build(".", runner="deno")]}
    planned = app.plan(record)
    assert planned["apps"] == []
    assert [(gap["kind"], gap["path"]) for gap in planned["gaps"]] == [
        ("start_runner_not_supported", "package.json#scripts.build")]


def test_the_chosen_start_of_a_folder_is_the_user_s_then_the_assistant_s_then_the_project_s_start_before_dev():
    mine = {**start("web", "start"), "argv": ["npm", "run", "serve"], "by": "assistant", "declared_in": "commands.json"}
    found = app.chosen({"starts": [start("web", "dev"), start("web", "start"), mine, start("api", "dev")]})
    assert {root: entry["argv"] for root, entry in found.items()} == {
        "web": ["npm", "run", "serve"], "api": ["npm", "run", "dev"]}


def test_a_project_declaring_no_start_is_a_gap_and_nothing_runs():
    planned = app.plan({"gaps": [{"kind": "no_start_command", "path": "t/package.json", "detail": "only tests",
                                  "source": "x"}]})
    assert planned["apps"] == []
    assert [gap["kind"] for gap in planned["gaps"]] == ["no_start_command", "no_start_command"]


def surfaced(deferred: bool) -> tuple[str, str]:
    """A technology whose registry entry decides a surface the exploration runs (`deferred` False) or does not run yet,
    and that surface: read from the registry, never named here."""
    import service_registry
    return next((entry["id"], entry["surface"]) for entry in service_registry.load()["entries"]
                if entry.get("surface") and (entry["surface"] not in app.ACTIVE) is deferred)


def module(root: str, *idents: str) -> dict:
    """A physical module of the stack record (`technologies.derive`), in `root`, declaring `idents` in its manifest."""
    return {"id": f"m@{root}", "name": f"m-{root}", "paths": [root], "technologies": list(idents),
            "technology_evidence": {ident: {"path": f"{root}/package.json", "line": 3} for ident in idents}}


def test_the_active_surfaces_are_of_the_registry_and_the_others_wait():
    import registry_build
    assert set(app.ACTIVE) < set(registry_build.SURFACES)


def test_a_module_on_a_surface_not_run_yet_and_with_no_start_is_a_gap_with_the_technology_and_its_file():
    ident, surface = surfaced(deferred=True)
    planned = app.plan({"starts": [start("web", "dev")]}, units=[module("mobile", ident)])
    assert [one["root"] for one in planned["apps"]] == ["web"]  # the other app still starts
    (gap,) = planned["gaps"]
    assert {key: gap[key] for key in ("kind", "root", "module", "technology", "path", "line")} == {
        "kind": f"ui_execution_deferred:{surface}", "root": "mobile", "module": "m@mobile", "technology": ident,
        "path": "mobile/package.json", "line": 3}
    assert ident in gap["detail"] and surface in gap["detail"] and gap["remedy"]


def test_a_module_whose_folder_starts_on_an_active_surface_or_whose_surface_runs_is_no_gap():
    deferred, _ = surfaced(deferred=True)
    active, _ = surfaced(deferred=False)
    planned = app.plan({"starts": [start("web", "dev")]},  # a start that states no surface opens an address: `web`
                       units=[module("web", deferred), module("desk", active), module("lib", "no-such-technology")])
    assert [one["root"] for one in planned["apps"]] == ["web"] and planned["gaps"] == []


def test_a_start_on_a_surface_not_run_yet_does_not_start_whatever_its_runner():
    _, surface = surfaced(deferred=True)
    stated = {**start("mobile", "start", runner="flutter"), "surface": surface, "declared_in": "commands.json"}
    planned = app.plan({"starts": [stated]})
    assert planned["apps"] == []
    assert [(gap["kind"], gap["root"], gap["path"]) for gap in planned["gaps"]] == [
        (f"ui_execution_deferred:{surface}", "mobile", "commands.json")]


def test_the_pages_nextjs_declares_under_an_apps_folder_are_its_seeds():
    record, pages = {"starts": [start("web", "dev")]}, [
        {"shape": "AppPageConfig", "page": True, "schema": "/about", "site": "web/app/about/page.tsx", "path": "/about"},
        {"shape": "AppPageConfig", "page": True, "schema": "/{}", "site": "web/app/[id]/page.tsx", "path": "/[id]"},  # a pattern: no page to open
        {"shape": "RouteHandlerConfig", "schema": "/api/x", "site": "web/app/api/x/route.ts", "path": "/api/x"},  # an endpoint, not a page
        {"shape": "AppPageConfig", "page": True, "schema": "/other", "site": "other/app/page.tsx", "path": "/other"}]  # another app's
    planned = app.plan(record, explore=True, pages=pages)
    assert planned["apps"][0]["seeds"] == ["/about"]
    assert "'[\"/about\"]'" in app.scripts(planned, [])[1] or '["/about"]' in app.scripts(planned, [])[1]


# --- the scripts: the command is the declared one --------------------------------------------------------------

def test_the_execution_runs_the_declared_command_and_never_one_of_ours():
    planned = {"apps": [{**start("web", "dev", port=5173), "build": build("web")}, start(".", "start")],
               "gaps": [], "roots": ["web"], "toolchains": []}
    prepare, execute = app.scripts(planned, ["npm ci"])
    assert "npm ci" in prepare and "set -u" in execute
    assert "npm run build" in execute and "npm run dev" in execute and "npm run start" in execute
    assert execute.index("npm run build") < execute.index("npm run dev")
    assert "--host" not in execute and "--port" not in execute  # the declared command is not changed
    assert "5173" in execute  # the declared port is the driver's to wait on
    assert "corepack" not in prepare and "corepack" not in execute  # npm's: nothing of corepack


def test_pnpm_and_yarn_get_corepack_s_shims_and_their_manager_fetched_while_the_preparation_has_the_network():
    """The declared words run as written (`pnpm run dev`, never `corepack pnpm …`): corepack's shims are on the path,
    each folder's manager is fetched in the preparation, and the execution, with no network, does not prompt."""
    planned = {"apps": [{**start("web", "start", runner="pnpm", needs_build=True), "build": build("web", "pnpm")},
                        start("docs", "dev", runner="yarn"), start(".", "dev")], "gaps": [], "roots": [], "toolchains": []}
    prepare, execute = app.scripts(planned, ["corepack pnpm install"])
    assert preparation.COREPACK_INSTALL in prepare
    assert f"corepack enable --install-directory {app.T}/bin pnpm yarn" in prepare
    assert "( cd /work/web && pnpm --version )" in prepare and "( cd /work/docs && yarn --version )" in prepare
    assert prepare.index("corepack pnpm install") < prepare.index("corepack enable")
    assert preparation.COREPACK in execute
    assert "pnpm run build" in execute and "'pnpm run start'" in execute and "'yarn run dev'" in execute
    assert "corepack pnpm" not in execute


# --- the outcome, read back ------------------------------------------------------------------------------------

def observe(tmp_path, played: Played, apps: list[dict] | None = None, **more) -> dict:
    project = write(tmp_path / "proj", {"package.json": json.dumps({"scripts": {"dev": "vite"}})})
    planned = {"apps": apps if apps is not None else [start(".", "dev")], "gaps": [], "roots": [""], "toolchains": [],
               **more}
    with mock.patch.object(container, "run_in_container", played), \
            mock.patch.object(container, "free_memory", return_value=64 * 2**30), \
            mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)):
        return app.observe(project, planned, tmp_path / "runs")


def result(**more) -> str:
    return json.dumps({"state": "ready", "address": "http://localhost:5173/", "port": 5173, "seconds": 1,
                       "stopped": "term", "left": [], "tail": "", **more})


def test_an_app_that_answered_and_stopped_is_ready_with_its_address(tmp_path):
    played = Played({"app-0.json": result()}, {"execute.log": "DAODAN-APP 0 exit 0 4\n"})
    seen = observe(tmp_path, played)
    assert seen["state"] == "ran" and seen["gaps"] == []
    assert seen["apps"] == [{"root": ".", "mode": "dev", "declared_in": "package.json#scripts.dev", "state": "ready",
                             "address": "http://localhost:5173/", "port": 5173, "seconds": 1, "stopped": "term"}]
    assert played.given["command"][:2] == ["sh", "-c"] and played.given["prepare"][:2] == ["sh", "-c"]
    assert "blind" not in played.given and "block_network" not in played.given  # the default: no network


def test_an_app_that_exits_before_its_port_answers_is_a_gap_with_the_log(tmp_path):
    played = Played({"app-0.json": result(state="exited", address=None, port=None, exit=1,
                                          tail="Error: Cannot find module 'vite'")},
                    {"execute.log": "DAODAN-APP 0 exit 0 2\n"})
    seen = observe(tmp_path, played)
    [gap] = seen["gaps"]
    assert gap["kind"] == "app_not_started" and "exited with code 1" in gap["detail"]
    assert "Cannot find module 'vite'" in gap["detail"] and gap["path"] == "package.json#scripts.dev"
    assert seen["apps"][0]["state"] == "not_started"


def test_a_port_that_never_answers_is_not_ready_and_one_never_told_is_not_declared(tmp_path):
    played = Played({"app-0.json": result(state="not_ready", address=None, tail="compiling..."),
                     "app-1.json": result(state="no_address", address=None, port=None, tail="listening")},
                    {"execute.log": "DAODAN-APP 0 exit 0 90\nDAODAN-APP 1 exit 0 90\n"})
    seen = observe(tmp_path, played, [start(".", "dev", port=5173), start("b", "start")])
    assert [gap["kind"] for gap in seen["gaps"]] == ["not_ready", "port_not_declared"]
    assert "compiling..." in seen["gaps"][0]["detail"] and "5173" in seen["gaps"][0]["detail"]


def test_a_process_that_survives_the_stop_is_a_gap(tmp_path):
    played = Played({"app-0.json": result(stopped="left", left=["4242 node server.js"])},
                    {"execute.log": "DAODAN-APP 0 exit 0 14\n"})
    seen = observe(tmp_path, played)
    assert [gap["kind"] for gap in seen["gaps"]] == ["app_not_stopped"] and seen["apps"][0]["state"] == "ready"
    assert "4242 node server.js" in seen["gaps"][0]["detail"]


def test_a_failed_build_is_a_gap_with_the_log_and_the_app_does_not_start(tmp_path):
    played = Played({"build-0.log": "error TS2304: Cannot find name 'x'\n"},
                    {"execute.log": "DAODAN-APP 0 build 2 7\n"})
    seen = observe(tmp_path, played, [{**start(".", "start", needs_build=True), "build": build(".")}])
    [gap] = seen["gaps"]
    assert gap["kind"] == "build_failed" and "TS2304" in gap["detail"] and "exited with code 2" in gap["detail"]
    assert seen["apps"][0]["state"] == "not_started"


def test_the_preparation_reaches_the_hosts_of_the_manager_corepack_fetches(tmp_path):
    played = Played({"app-0.json": result()}, {"execute.log": "DAODAN-APP 0 exit 0 4\n"})
    observe(tmp_path, played, [start(".", "dev", runner="yarn")])
    assert set(preparation.RESTORES["yarn"]["hosts"]) <= set(played.given["registries"])


def test_a_host_the_proxy_refused_and_nobody_answered_is_the_approval_gap_of_a_run_that_went_on(tmp_path):
    """The browser's or mise's download outside the canonical hosts asks (`egress`): the run goes on without it, and the
    gap names the host to answer in the app, not only the browser that is missing."""
    asked = [{"host": "storage.googleapis.com", "port": "443", "declared_in": []}]
    played = Played({"app-0.json": result()}, {"execute.log": "DAODAN-APP 0 exit 0 4\n"},
                    {"state": "done", "exit_code": 0, "outputs": [], "asked": asked})
    seen = observe(tmp_path, played)
    [gap] = [gap for gap in seen["gaps"] if gap["kind"] == "approval_required"]
    assert gap["hosts"] == ["storage.googleapis.com"] and "storage.googleapis.com:443" in gap["detail"]


def test_a_driver_that_wrote_nothing_is_a_gap_not_a_silence(tmp_path):
    seen = observe(tmp_path, Played({}, {"execute.log": ""}))
    assert [gap["kind"] for gap in seen["gaps"]] == ["app_not_started"]


# --- the exploration: the browser in the preparation, the exploring driver in the execution ---------------------

def test_exploring_adds_the_browser_to_the_preparation_and_the_exploring_driver_to_the_execution():
    planned = {"apps": [start(".", "dev")], "gaps": [], "roots": [""], "toolchains": [], "explore": True,
               "seeds": ["/admin"]}
    prepare, execute = app.scripts(planned, [])
    assert f"playwright-core@{app.PLAYWRIGHT}" in prepare and "install --with-deps --only-shell chromium" in prepare
    assert "explore.cjs" in execute and "DAODAN_PLAYWRIGHT=" in execute and '["/admin"]' in execute
    prepare, execute = app.scripts({**planned, "explore": False}, [])
    assert "playwright" not in prepare and "explore.cjs" not in execute and "app.cjs" in execute


def test_the_counts_and_the_gaps_of_the_exploration_come_back_with_the_app(tmp_path):
    totals = {"pages": 2, "controls": 5, "pressed": 3, "skipped": 2, "failed": 0}
    explored = json.dumps({"totals": totals, "pages": [], "gaps": [{"kind": "explore_cap", "detail": "stopped"}]})
    played = Played({"app-0.json": result(), "explore-0.json": explored}, {"execute.log": "DAODAN-APP 0 exit 0 40\n"})
    seen = observe(tmp_path, played, explore=True)
    assert seen["apps"][0]["explored"] == totals and [gap["kind"] for gap in seen["gaps"]] == ["explore_cap"]
    assert played.given["keep_root"] is True  # the browser's system packages are the preparation's, kept for the run
    assert {"cdn.playwright.dev", "archive.ubuntu.com"} <= set(played.given["registries"])
    assert Path(played.given["inputs"]().get(f"{app.IN}/explore.cjs")).name == "explore.cjs"
    assert f"{app.IN}/app.cjs" in played.given["inputs"]()


def test_an_exploration_that_wrote_nothing_is_a_gap_with_the_drivers_reason(tmp_path):
    played = Played({"app-0.json": result(between_error="Error: browserType.launch: missing")},
                    {"execute.log": "DAODAN-APP 0 exit 0 40\n"})
    seen = observe(tmp_path, played, explore=True)
    assert [gap["kind"] for gap in seen["gaps"]] == ["explore_failed"] and "missing" in seen["gaps"][0]["detail"]
    assert "explored" not in seen["apps"][0]


# --- the driver, on Modal only: it starts code -----------------------------------------------------------------

MODAL = pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="starts code: Modal only (tests/modal_pytest.py)")
LISTEN = ("const http = require('http');\n"
          "const server = http.createServer((q, r) => r.end('ok')).listen({port}, '127.0.0.1', () => {announce});\n")


def drive(tmp_path, files: dict, port: int | None = None, limit: int = 20, command: str = "node server.js") -> dict:
    project = write(tmp_path / "proj", files)
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", str(SCRIPTS / "dynamic/app.cjs"), str(out), "0", str(project),
                           str(port or "-"), str(limit), command], capture_output=True, text=True, timeout=limit + 60)
    assert done.returncode == 0, done.stderr[-1500:]
    return json.loads((out / "app-0.json").read_text(encoding="utf-8"))


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _cmdline(pid: str) -> bytes:
    try:
        return Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return b""


def closed(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", port)) != 0


@MODAL
def test_on_modal_a_declared_port_is_waited_for_and_the_app_is_stopped_with_its_children(tmp_path):
    port = free_port()
    server = (LISTEN.format(port=port, announce="{}") +
              "require('child_process').spawn('sleep', ['300'], {stdio: 'ignore'});\n")  # a child of the app
    found = drive(tmp_path, {"server.js": server}, port=port)
    assert found["state"] == "ready" and found["port"] == port and found["stopped"] == "term"
    assert found["address"].endswith(f":{port}/") and found["left"] == []
    assert closed(port)
    assert not [pid for pid in os.listdir("/proc") if pid.isdigit() and b"sleep\x00300" in _cmdline(pid)]


@MODAL
def test_on_modal_the_address_the_app_prints_is_used_verbatim_when_no_port_is_declared(tmp_path):
    port = free_port()
    server = LISTEN.format(port=port, announce=f"console.log('  Local: http://localhost:{port}/')")
    found = drive(tmp_path, {"server.js": server})
    assert found["state"] == "ready" and found["address"] == f"http://localhost:{port}/" and found["port"] == port
    assert closed(port)


@MODAL
def test_on_modal_an_app_that_prints_no_address_and_declares_no_port_is_never_scanned(tmp_path):
    port = free_port()  # listening, but nobody says where: the driver does not look
    found = drive(tmp_path, {"server.js": LISTEN.format(port=port, announce="{}")}, limit=6)
    assert found["state"] == "no_address" and found["address"] is None
    assert closed(port)


@MODAL
def test_on_modal_an_app_that_exits_at_once_is_exited_with_its_code_and_its_last_lines(tmp_path):
    found = drive(tmp_path, {"server.js": "console.error('Error: no config'); process.exit(3);\n"}, port=free_port())
    assert found["state"] == "exited" and found["exit"] == 3 and "Error: no config" in found["tail"]


@MODAL
def test_on_modal_a_port_nobody_opens_is_not_ready_after_the_limit(tmp_path):
    started = time.monotonic()
    found = drive(tmp_path, {"server.js": "console.log('compiling'); setInterval(() => {}, 1000);\n"},
                  port=free_port(), limit=5)
    assert found["state"] == "not_ready" and "compiling" in found["tail"] and time.monotonic() - started < 40


@MODAL
def test_on_modal_an_app_that_ignores_sigterm_is_killed_and_nothing_is_left(tmp_path):
    port = free_port()
    server = ("process.on('SIGTERM', () => {});\n" +
              LISTEN.format(port=port, announce="{}"))
    found = drive(tmp_path, {"server.js": server}, port=port)
    assert found["state"] == "ready" and found["stopped"] == "kill" and found["left"] == []
    assert closed(port)


@MODAL
def test_on_modal_the_vite_fixture_starts_with_its_declared_command_and_stops_clean(tmp_path):
    """`js-vite-react-ts` with its real dependencies (the restore's `npm install`, here with the network Modal's
    test container has): `npm run dev` prints its address, the driver takes it, and nothing of the app is left."""
    fixture = SCRIPTS.parents[1] / "benchmarks/project-model/fixtures/js-vite-react-ts"
    project = tmp_path / "proj"
    shutil.copytree(fixture, project, ignore=shutil.ignore_patterns("node_modules", "expected.json"))
    subprocess.run([shutil.which("npm"), "install", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=project,
                   check=True, capture_output=True, timeout=600)
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", str(SCRIPTS / "dynamic/app.cjs"), str(out), "0", str(project), "-", "90",
                           "npm run dev"], capture_output=True, text=True, timeout=150)
    assert done.returncode == 0, done.stderr[-1500:]
    found = json.loads((out / "app-0.json").read_text(encoding="utf-8"))
    assert found["state"] == "ready" and found["address"].startswith("http://localhost:") and found["left"] == []
    assert closed(found["port"]) and found["stopped"] in ("term", "kill")


def test_the_pages_the_exploration_saw_are_kept_beside_the_manifest_for_the_entries(tmp_path):
    import observed_entries
    pages = [{"url": "http://localhost:5173/", "controls": [{"role": "button", "name": "Save", "state": "pressed"}]}]
    played = Played({"app-0.json": result(), "explore-0.json": json.dumps({"totals": {}, "pages": pages, "gaps": []})},
                    {"execute.log": "DAODAN-APP 0 exit 0 40\n"})
    observe(tmp_path, played, explore=True)
    manifest = tmp_path / "manifest.sqlite"
    planned = {"apps": [start(".", "dev")]}
    assert app.record(manifest, planned, tmp_path / "runs") == 1
    assert json.loads((tmp_path / observed_entries.FILE).read_text(encoding="utf-8"))["apps"] == [
        {"declared_in": "package.json#scripts.dev", "pages": pages}]
    assert app.record(tmp_path / "none" / "manifest.sqlite", planned, tmp_path / "nowhere") == 0


def test_a_run_that_explored_nothing_takes_away_the_pages_of_a_former_one(tmp_path):
    import observed_entries
    (tmp_path / observed_entries.FILE).write_text('{"apps": [{"pages": []}]}', encoding="utf-8")
    assert app.record(tmp_path / "manifest.sqlite", {"apps": [start(".", "dev")]}, tmp_path / "nowhere") == 0
    assert not (tmp_path / observed_entries.FILE).exists()  # another snapshot's controls are not this one's


# --- the step: plan, explore, keep, and reuse on the same snapshot ----------------------------------------------

def explorer(calls: list):
    """`app.observe` as a double: it explores one page and counts the runs."""
    def observe(project, planned, out_dir, engine=None):
        calls.append(planned)
        back = Path(out_dir) / Path(app.OUT).name
        back.mkdir(parents=True, exist_ok=True)
        pages = [{"url": "http://localhost:5173/", "controls": [{"role": "button", "name": "Save", "state": "pressed"}]}]
        (back / "explore-0.json").write_text(json.dumps({"pages": pages}), encoding="utf-8")
        return {"state": "ran", "apps": [{"state": "ready"}], "gaps": [{"kind": "explore_cap", "detail": "stopped"}]}
    return observe


def test_the_step_explores_keeps_the_pages_and_reuses_them_while_the_snapshot_and_the_plan_stay(tmp_path):
    import observed_entries
    record = {"starts": [start(".", "dev")], "builds": []}
    manifest, calls = tmp_path / "manifest.sqlite", []
    with mock.patch.object(app, "observe", explorer(calls)):
        first = app.explore(manifest, tmp_path, record, "digest-1", tmp_path / "runs")
        again = app.explore(manifest, tmp_path, record, "digest-1", tmp_path / "runs")
        later = app.explore(manifest, tmp_path, record, "digest-2", tmp_path / "runs")
    assert (first["state"], first["kept"], first.get("reused")) == ("ran", 1, None) and len(calls) == 2
    assert again["reused"] is True and [gap["kind"] for gap in again["gaps"]] == ["explore_cap"]  # the gaps are said again
    assert later.get("reused") is None and (tmp_path / observed_entries.FILE).is_file()
    assert calls[0]["explore"] is True


def test_a_run_that_asked_for_hosts_nobody_answered_is_not_kept_so_the_next_analysis_runs_again(tmp_path):
    """The gap's remedy is to answer in the app and analyze again: the same snapshot and plan run again, not the run
    that went without the hosts."""
    record = {"starts": [start(".", "dev")], "builds": []}
    calls = []
    asking = explorer(calls)

    def observe(project, planned, out_dir, engine=None):
        seen = asking(project, planned, out_dir, engine)
        return {**seen, "gaps": [{"kind": "approval_required", "hosts": ["storage.googleapis.com"], "detail": "ask"}]}
    with mock.patch.object(app, "observe", observe):
        first = app.explore(tmp_path / "manifest.sqlite", tmp_path, record, "digest-1", tmp_path / "runs")
        again = app.explore(tmp_path / "manifest.sqlite", tmp_path, record, "digest-1", tmp_path / "runs")
    assert len(calls) == 2 and first.get("reused") is None and again.get("reused") is None


def test_a_project_with_no_app_to_start_runs_nothing_and_leaves_no_pages(tmp_path):
    with mock.patch.object(container, "run_in_container", side_effect=AssertionError("no container")):
        seen = app.explore(tmp_path / "manifest.sqlite", tmp_path, {"starts": [], "builds": []}, "d", tmp_path / "runs")
    assert seen["state"] == "ran" and seen["kept"] == 0 and [g["kind"] for g in seen["gaps"]] == ["no_start_command"]
    assert not (tmp_path / "observed-controls.json").exists()


def test_the_step_takes_the_modules_of_the_stack_record_beside_the_manifest(tmp_path):
    import technologies
    ident, surface = surfaced(deferred=True)
    manifest = tmp_path / "manifest.sqlite"
    technologies.path(manifest).write_text(json.dumps({"schema": technologies.SCHEMA, "technologies": [],
                                                       "units": [module("mobile", ident)]}), encoding="utf-8")
    with mock.patch.object(container, "run_in_container", side_effect=AssertionError("no container")):
        seen = app.explore(manifest, tmp_path, {"starts": [], "builds": []}, "d", tmp_path / "runs")
    assert [g["kind"] for g in seen["gaps"]] == ["no_start_command", f"ui_execution_deferred:{surface}"]


# --- the example `.env` files the project publishes are the app's test values --------------------------------------

def test_a_star_exports_every_variable_of_an_example_file_and_a_name_only_its_own():
    values = {"web/.env.example": {"A": "1", "B": "2"}, "other/.env": {"C": "3", "D": "4"}}
    assert container.exported([("*", "web/.env.example"), ("C", "other/.env"), ("Z", "other/.env")], values) == {
        "A": "1", "B": "2", "C": "3"}
    assert container.exported([("*", "none/.env.example")], values) == {}


def tracked_project(tmp_path, files: dict) -> Path:
    import subprocess
    project = write(tmp_path / "proj", files)
    for command in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"]):
        subprocess.run(["git", *command], cwd=project, check=True)
    return project


def test_the_app_gets_the_values_of_the_example_env_files_git_tracks_in_its_own_folder(tmp_path):
    project = tracked_project(tmp_path, {
        "package.json": "{}", ".env.example": "ROOT=1\n", "web/package.json": "{}", "web/.env.example": "VITE_KEY=test\n",
        "web/.env.development": "SECRET=real\n", "web/.env.local.sample": "SAMPLE=1\n", "api/.env.example": "API=1\n"})
    played = Played({"app-0.json": result()}, {"execute.log": "DAODAN-APP 0 exit 0 4\n"})
    planned = {"apps": [start("web", "dev")], "gaps": [], "roots": [""], "toolchains": []}
    with mock.patch.object(container, "run_in_container", played), \
            mock.patch.object(container, "free_memory", return_value=64 * 2**30), \
            mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)):
        app.observe(project, planned, tmp_path / "runs")
    assert played.given["dotenv_env"] == [("*", "web/.env.example"), ("*", "web/.env.local.sample")]  # never `.env.development`


def test_a_project_outside_git_gets_none(tmp_path):
    played = Played({"app-0.json": result()}, {"execute.log": "DAODAN-APP 0 exit 0 4\n"})
    observe(tmp_path, played)
    assert played.given["dotenv_env"] == []
