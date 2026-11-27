"""The runner of the pre-map's model commands: what it hands Daodan's container runner, and what it answers.

`container.run_commands` is replaced by a recorder: the real run is the smoke at the end, on a real engine only
with DAODAN_PREMAP_SMOKE=1 (one project per tool, the engine left as it was found).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import container  # noqa: E402
import premap  # noqa: E402
from premap import container_runner  # noqa: E402
import snapshot  # noqa: E402


def manifest_of(tmp_path, files):
    project = tmp_path / "proj"
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    return project, manifest


def bound(manifest, record) -> list[dict]:
    """The rows of the pre-map as the links bind them (`binder.bind`, as `flows.link_facts` calls it): the pre-map's rows are on
    the module with their `exports`, and the binder ties each to its function."""
    import binder
    import flows
    import semantic_store
    from snapshot_store import open_snapshot
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        return binder.bind(record.get("framework_entries", []), flows.Facts(store, db), semantic_store._Resolver(db))


def recorder(answers=None, state="done"):
    calls = []

    def run_commands(project, commands, **options):
        calls.append({"project": project, "commands": commands, **options})
        given = [{"returncode": 0, "stdout": "", "stderr": ""}] + (answers or [
            {"returncode": 0, "stdout": f"out {n}", "stderr": ""} for n in range(len(commands) - 1)])
        return {"state": state, "root": "/work", "results": given, "cause": "no engine", "remedy": "start one"}
    return calls, run_commands


def command(tool, network="none", **fields):
    return {"tool": tool, "argv": [tool, "x"], "cwd": ".", "env": {"A": "1"}, "network": network, **fields}


@pytest.fixture
def no_download(monkeypatch):
    monkeypatch.setattr(container_runner, "fetched", lambda url, sha, name: Path("/host") / name)


def test_one_container_run_per_source_with_its_setup_first_and_its_answers_back(tmp_path, no_download):
    project, manifest = manifest_of(tmp_path, {"go.mod": "module m\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        answers = container_runner.runner(manifest)([command("go", "registries"), command("go")])
    [call] = calls
    assert call["project"] == project and call["image"] == container_runner.IMAGE
    first, *rest = call["commands"]
    assert first["network"] == "registries" and "go.tar.gz" in first["argv"][-1]  # unpacked before the preparation
    assert [c["argv"] for c in rest] == [["go", "x"], ["go", "x"]]
    assert rest[0]["env"]["A"] == "1" and rest[0]["env"]["PATH"].startswith(container_runner.T)
    assert call["inputs"]() == {f"{container_runner.IN}/go.tar.gz": Path("/host/go.tar.gz")}
    assert call["registries"] == container.REGISTRIES
    assert call["out_dir"] == manifest.parent / "premap-runs" / "go"
    assert answers == [{"returncode": 0, "stdout": "out 0", "stderr": "", "root": "/work"},
                       {"returncode": 0, "stdout": "out 1", "stderr": "", "root": "/work"}]


def test_what_the_copy_of_the_project_left_out_rides_on_the_first_answer(tmp_path, no_download):
    """A link Git tracks to outside the project stays out of the copy (`container.copy_perimeter`): a gap of the
    run, as the preparation's are."""
    left = {"kind": "link_outside", "path": "x.go", "target": "../y.go", "detail": "x.go links outside"}
    _, manifest = manifest_of(tmp_path, {"go.mod": "module m\n"})
    _calls, fake = recorder()
    with mock.patch.object(container, "run_commands", lambda *given, **options: {**fake(*given, **options),
                                                                                  "gaps": [left]}):
        answers = container_runner.runner(manifest)([command("go", "registries")])
    assert answers[0]["gaps"] == [left]


def test_a_setup_that_installs_from_a_registry_runs_in_the_preparation(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"tsconfig.json": "{}\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)([command("tsc")])
    first = calls[0]["commands"][0]
    assert first["network"] == "registries" and "typescript@6.0.3" in first["argv"][-1]
    assert calls[0]["commands"][1]["network"] == "none"


SVELTEKIT = {"package.json": '{"name": "notes", "devDependencies": {"@sveltejs/kit": "^2.7.0"}}\n',
             "tsconfig.json": '{"extends": "./.svelte-kit/tsconfig.json"}\n', "src/lib/index.ts": "export {};\n",
             "docs/package.json": '{"name": "docs", "packageManager": "yarn@4.5.0"}\n', "docs/yarn.lock": "\n"}


def test_tsc_reads_the_tsconfigs_after_the_packages_are_restored_with_what_their_install_generates(tmp_path,
                                                                                                    no_download):
    """A tsconfig extends a file of an installed package, or one a framework generates when the packages are
    installed (SvelteKit's `.svelte-kit/tsconfig.json`): the setup restores each package folder of the snapshot the
    project's own way, lifecycle scripts included, before any `tsc --showConfig`; the commands stay tsc's own."""
    import preparation
    from snapshot_store import open_snapshot
    project, manifest = manifest_of(tmp_path, SVELTEKIT)
    with open_snapshot(manifest) as store:
        asked = premap.tsc.commands(premap.Context(manifest, store))
    assert [c["argv"] for c in asked] == [["tsc", "--showConfig", "-p", "tsconfig.json"]]
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)(asked)
    first, *rest = calls[0]["commands"]
    assert [c["argv"] for c in rest] == [c["argv"] for c in asked] and rest[0]["network"] == "none"
    setup = first["argv"][-1]
    plan = preparation.node_prepare(["package.json", "docs/package.json", "docs/yarn.lock"],
                                    lambda rel: (project / rel).read_text(encoding="utf-8"))
    assert plan["restores"] == {"npm": ["."], "yarn": ["docs"]}
    assert first["network"] == "registries" and first["cwd"] == "."
    assert setup.index("typescript@6.0.3") < setup.index(f"( {plan['lines'][0]} )") < setup.index(
        f"( {plan['lines'][1]} )")
    assert "npm install --no-audit --no-fund" in plan["lines"][0]  # with its lifecycle scripts, in the container
    assert set(calls[0]["registries"]) - set(container.REGISTRIES) == set()  # corepack's host is a registry now
    assert "repo.yarnpkg.com" in calls[0]["registries"]
    assert calls[0]["memory"] == 3 * 2**30


FIXTURE = ROOT / "benchmarks/project-model/fixtures/js-sveltekit"


def test_a_package_with_only_its_manifest_is_installed_by_npm_with_its_lifecycle_scripts(tmp_path, no_download):
    """js-sveltekit: a package.json with devDependencies, no lockfile, no `packageManager`. npm, the default
    manager, resolves and installs there with the lifecycle scripts (SvelteKit's writes the tsconfig the project's
    extends) before tsc reads it."""
    import preparation
    from snapshot_store import open_snapshot
    files = {path.relative_to(FIXTURE).as_posix(): path.read_text(encoding="utf-8")
             for path in sorted(FIXTURE.rglob("*")) if path.is_file() and path.name != "expected.json"}
    assert "package.json" in files and not {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"} & set(files)
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        asked = premap.tsc.commands(premap.Context(manifest, store))
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        [answer] = container_runner.runner(manifest)(asked)
    first = calls[0]["commands"][0]
    line = preparation.restore("npm", ["."], scripts=True)
    assert "timeout 600 sh -c 'if [ -f package-lock.json ]" in line and "npm install --no-audit --no-fund" in line
    assert f"( {line} )" in first["argv"][-1] and first["network"] == "registries"
    assert "gaps" not in answer


def test_each_nested_app_with_its_own_lockfile_is_restored_beside_the_root_and_no_gap_is_left(tmp_path, no_download):
    """A root and independent apps below, each with its own package.json and package-lock.json, no workspaces."""
    import preparation
    apps = ("admin-app", "landing-app")
    files = {"package.json": '{"name": "root", "dependencies": {"ms": "2.1.3"}}\n', "package-lock.json": "{}\n",
             "tsconfig.json": "{}\n"}
    for app in apps:
        files[f"{app}/package.json"] = '{"name": "' + app + '", "dependencies": {"ms": "2.1.3"}}\n'
        files[f"{app}/package-lock.json"] = "{}\n"
    _, manifest = manifest_of(tmp_path, files)
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        [answer] = container_runner.runner(manifest)([command("tsc")])
    line = preparation.restore("npm", [".", *apps], scripts=True)
    assert f"( {line} )" in calls[0]["commands"][0]["argv"][-1]
    assert "gaps" not in answer


def test_a_package_folder_no_restore_installs_is_a_gap_on_the_answers(tmp_path, no_download):
    """A package under the root's restore that its workspaces do not name declares dependencies nobody installs."""
    _, manifest = manifest_of(tmp_path, {
        "package.json": '{"name": "root", "workspaces": ["packages/*"]}\n', "tsconfig.json": "{}\n",
        "packages/ui/package.json": '{"name": "ui", "dependencies": {"ms": "2.1.3"}}\n',
        "tools/gen/package.json": '{"name": "gen", "dependencies": {"chalk": "5.3.0"}}\n',
        "tools/empty/package.json": '{"name": "empty"}\n'})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        [answer] = container_runner.runner(manifest)([command("tsc")])
    assert answer["gaps"] == [{"kind": "restore_failed", "manager": "npm", "path": "tools/gen",
                               "detail": "its packages are not installed: no workspace above names this folder"}]


def test_a_restore_or_a_generation_that_fails_before_tsc_is_a_gap_on_the_answers(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, SVELTEKIT)
    setup = {"returncode": 0, "stdout": "", "stderr": (
        "DAODAN-GENERATE-FAILED npm .\nnpm error command sh -c node postinstall.js\nDAODAN-GENERATE-END\n"
        "DAODAN-RESTORE-FAILED yarn docs\nYN0001: Error: no lockfile entry\nDAODAN-RESTORE-END\n")}
    calls, fake = recorder()

    def run_commands(project, commands, **options):
        result = fake(project, commands, **options)
        result["results"][0] = setup
        return result

    with mock.patch.object(container, "run_commands", run_commands):
        [answer] = container_runner.runner(manifest)([command("tsc")])
    assert [(g["kind"], g["manager"], g["path"]) for g in answer["gaps"]] == [
        ("restore_failed", "yarn", "docs"), ("generation_failed", "npm", ".")]
    assert answer["returncode"] == 0  # the tsconfigs are still read


def test_only_tsc_restores_the_packages_before_its_commands(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, SVELTEKIT)
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)([command("npm")])
    assert "install" not in calls[0]["commands"][0]["argv"][-1] and calls[0]["registries"] == container.REGISTRIES


def test_bazel_reaches_its_own_hosts_beside_the_registries_and_no_other_tool_does(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"MODULE.bazel": "module(name = 'x')\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)([command("bazel", "registries")])
        container_runner.runner(manifest)([command("cmake")])
    bazel_run, cmake_run = calls
    assert set(bazel_run["registries"]) - set(container.REGISTRIES) == {
        "github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com", "codeload.github.com"}
    assert {"bcr.bazel.build", "mirror.bazel.build"} <= set(container.REGISTRIES)
    assert cmake_run["registries"] == container.REGISTRIES and cmake_run["commands"][0]["network"] == "none"


def test_without_an_engine_the_source_states_nothing_and_its_gap_says_why(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"Cargo.toml": "[package]\nname = 'a'\nversion = '0.1.0'\n"})
    _, fake = recorder(state="gap")
    with mock.patch.object(container, "run_commands", fake):
        record = premap.write(manifest, sources=(premap.cargo,), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g["kind"] == "model_not_run"]
    assert "no engine" in json.dumps(gap) and not record["units"]


def test_a_failed_setup_fails_the_source(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"go.mod": "module m\n"})
    _, fake = recorder(answers=[])
    with mock.patch.object(container, "run_commands", lambda *a, **k: {
            **fake(*a, **k), "results": [{"returncode": 2, "stdout": "", "stderr": "tar: go.tar.gz: not found"}, {}]}):
        with pytest.raises(RuntimeError, match="not found"):
            container_runner.runner(manifest)([command("go")])


def test_every_model_source_of_the_premap_has_a_setup():
    tools = {"go": premap.go, "cargo": premap.cargo, "uv": premap.uv, "tsc": premap.tsc, "npm": premap.npm,
             "renovate": premap.renovate, "compose": premap.compose, "daodan-enry": premap.enry,
             "daodan-dockerfile": premap.dockerfile, "cmake": premap.cmake, "meson": premap.meson,
             "bazel": premap.bazel, "make": premap.make, "gradle": premap.gradle, "maven": premap.maven,
             "sbt": premap.sbt, "dotnet": premap.dotnet, "noir": premap.noir, "next": premap.nextjs,
             "react-router": premap.react_router, "nuxt": premap.nuxt, "sveltekit": premap.sveltekit, "angular": premap.angular, "astro": premap.astro}
    assert {s for s in premap.SOURCES if hasattr(s, "commands")} == set(tools.values())
    assert set(tools) <= set(container_runner.TOOLS)


# ------------------------------------------------- smoke, on a real engine

SMOKE = os.environ.get("DAODAN_PREMAP_SMOKE") == "1"
CORPUS = ROOT / "benchmarks/project-model/fixtures"
CASES = {  # tool -> (corpus fixture, or the folder of one, the source), one project each
    "noir": ("js-nextjs", premap.noir),
    "next": (ROOT / "benchmarks/system-map/real-paths/next-shop", premap.nextjs),  # js-nextjs is Next.js 14: no typegen
    "react-router": (ROOT / "benchmarks/react-router-routes/fixture/framework", premap.react_router),
    "nuxt": (ROOT / "benchmarks/nuxt-routes/fixture/nuxt3", premap.nuxt),
    "go": ("sys-go-buildtags", premap.go), "cargo": ("sys-rust-features", premap.cargo),
    "uv": ("py-uv-workspace", premap.uv), "tsc": ("js-vite-react-ts", premap.tsc),
    "npm": ("js-npm-workspaces", premap.npm), "renovate": ("js-npm-single", premap.renovate),
    "daodan-enry": ("js-vendored-generated", premap.enry), "cmake": ("sys-cmake-targets", premap.cmake),
    "meson": ("sys-meson", premap.meson), "bazel": ("sys-bazel", premap.bazel),
    "make": ("sys-make-plain", premap.make), "gradle": ("jvm-gradle-groovy-wrapper", premap.gradle),
    "maven": ("jvm-maven-multi-bom-profile", premap.maven), "sbt": ("jvm-sbt-two-subprojects", premap.sbt),
    "dotnet": ("mix-dotnet-central", premap.dotnet)}
FIRST = {"dotnet": (premap.renovate,)}  # global.json pins the SDK: Renovate reads it, the preparation installs it


@pytest.mark.skipif(not SMOKE, reason="set DAODAN_PREMAP_SMOKE=1 to run each source in a real container")
@pytest.mark.parametrize("tool", sorted(CASES))
def test_smoke_each_tool_runs_in_the_container_and_states_its_facts(tmp_path, tool):
    name, source = CASES[tool]
    sources = (*FIRST.get(tool, ()), source)  # what states the toolchain the tool runs on, then the tool
    engine = container.find_engine()
    held = lambda: (container.cli(engine, "ps", "-a", "-q").stdout, container.cli(engine, "volume", "ls", "-q").stdout)  # noqa: E731
    before = held()
    project = tmp_path / "proj"
    shutil.copytree(CORPUS / name, project, ignore=shutil.ignore_patterns("expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    record = premap.write(manifest, sources=sources, runner=container_runner.runner(manifest, engine=engine))
    print(json.dumps({"tool": tool, "sources": record["sources"], "units": len(record["units"]),
                      "gaps": record["gaps"][:5]}, indent=1)[:3000])
    assert [s["state"] for s in record["sources"]] == ["ran"] * len(sources), record["sources"]
    assert not [g for g in record["gaps"] if g["kind"] in ("source_failed", "model_failed")]
    if tool == "noir":
        assert any(r["method"] == "GET" and r["path"] == "/api/health" for r in premap.noir.recorded(manifest))
    if tool == "next":
        assert {(r["path"], r["site"]) for r in record["framework_entries"]} >= {
            ("/api/pay", "app/api/pay/route.ts"), ("/checkout", "app/checkout/page.tsx")}
    if tool == "react-router":
        assert {(r["path"], r.get("handler")) for r in record["framework_entries"]} >= {("/api/pay", "action"), ("/checkout", "default")}
    if tool == "nuxt":
        assert {(r["path"], r.get("method"), r["site"].split(":")[0]) for r in record["framework_entries"]} >= {
            ("/api/hello", "GET", "server/api/hello.get.ts"), ("/api/users", "POST", "server/api/users/index.post.ts")}
    assert held() == before


def test_the_stated_toolchains_are_installed_by_mise_at_their_version_and_the_rest_are_gaps():
    import preparation
    plan = preparation.toolchains([{"tool": "node", "version": "20.11.0"}, {"tool": "go", "version": "1.22"},
                                   {"tool": "node", "version": ">=20"}, {"tool": "fortran", "version": "2018"}])
    assert plan["files"] == [preparation.MISE]
    installs = [line for line in plan["lines"] if " install " in line]
    assert [line.split(" install ")[1].split(" ")[0] for line in installs] == ["go@1.22", "node@20.11.0"]
    assert all("DAODAN-MISSING" in line for line in installs)  # a failed install leaves the run going
    assert {"nodejs.org", "go.dev", "mise-versions.jdx.dev"} <= set(plan["hosts"])
    assert sorted((g["tool"], g["version"]) for g in plan["gaps"]) == [("fortran", "2018"), ("node", ">=20")]
    assert preparation.toolchains([]) == {"files": [], "lines": [], "hosts": (), "gaps": []}


def test_the_go_lines_are_minimums_and_the_highest_builds_every_module():
    """mix-real-chi states go 1.24 in go.mod, 1.22 and 1.16 in two example modules. A go line is the least Go its
    module or workspace needs, a toolchain line (goV) the toolchain it prefers, and the go command runs its own
    toolchain when that is at least as new as both, else the newer one they name (go.dev/doc/toolchain): the
    highest of them builds every module, and a version a file pins runs only when it is newer still. sys-go-toolchain
    pins 1.22.5 in .tool-versions, its go.mod says go 1.23.4 and toolchain go1.24.1: Go itself runs 1.24.1. Any other
    statement keeps one version per tool per run."""
    import preparation

    def chosen(stated):
        plan = preparation.toolchains(stated)
        return ([line.split(" install ")[1].split(" ")[0] for line in plan["lines"] if " install " in line],
                [(g["tool"], g["version"], g["path"], g["detail"]) for g in plan["gaps"]])

    assert chosen([{"tool": "go", "version": "1.22", "declared_in": "_examples/rest/go.mod"},
                   {"tool": "go", "version": "1.16", "declared_in": "_examples/versions/go.mod"},
                   {"tool": "go", "version": "1.24", "declared_in": "go.mod"}]) == (["go@1.24"], [])
    assert chosen([{"tool": "go", "version": "1.22.5", "declared_in": ".tool-versions"},
                   {"tool": "go", "version": "1.23.4", "declared_in": "go.mod#go"},
                   {"tool": "go", "version": "go1.24.1", "declared_in": "go.mod#toolchain"}]) == (["go@1.24.1"], [])
    assert chosen([{"tool": "go", "version": "1.25.0", "declared_in": ".go-version"},
                   {"tool": "go", "version": "1.24", "declared_in": "tools/go.work"}]) == (["go@1.25.0"], [])
    assert chosen([{"tool": "go", "version": "1.22", "declared_in": "Dockerfile"},
                   {"tool": "go", "version": "1.23", "declared_in": ".go-version"},
                   {"tool": "go", "version": "1.24", "declared_in": "go.mod"},
                   {"tool": "node", "version": "20.11.0", "declared_in": ".nvmrc"},
                   {"tool": "node", "version": "22", "declared_in": "Dockerfile"}]) == (["go@1.24", "node@20.11.0"], [
        ("go", "1.23", ".go-version", "go 1.23: go 1.24 runs these commands: one version per tool per run"),
        ("node", "22", "Dockerfile", "node 22: node 20.11.0 runs these commands: one version per tool per run")])


def test_the_runner_prepares_the_toolchains_in_the_preparation(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"go.mod": "module m\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        container_runner.runner(manifest, toolchains=[{"tool": "go", "version": "1.22.4"}])([command("go")])
    first = calls[0]["commands"][0]
    assert first["network"] == "registries" and "install go@1.22.4" in first["argv"][-1]
    assert "go.dev" in calls[0]["registries"] and f"{container_runner.IN}/mise" in calls[0]["inputs"]()


def test_only_the_toolchains_a_tool_runs_on_are_installed(tmp_path, no_download):
    """Go's commands get the project's Go, not its Node; the Node a tsc command runs on is the project's."""
    _, manifest = manifest_of(tmp_path, {"go.mod": "module m\n"})
    stated = [{"tool": "go", "version": "1.22.4"}, {"tool": "node", "version": "20.11.0"}]
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        run = container_runner.runner(manifest, toolchains=stated)
        run([command("go")])
        run([command("tsc", "registries")])
    go_setup, tsc_setup = (c["commands"][0]["argv"][-1] for c in calls)
    assert "install go@1.22.4" in go_setup and "node@" not in go_setup
    assert "install node@20.11.0" in tsc_setup and "go@" not in tsc_setup


def test_a_toolchain_the_preparation_could_not_install_is_a_gap_on_the_answers(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"go.mod": "module m\n"})
    setup = {"returncode": 0, "stdout": "", "stderr": "mise ERROR no such version\nDAODAN-MISSING go@1.99.9\n"}
    calls, fake = recorder()

    def run_commands(project, commands, **options):
        result = fake(project, commands, **options)
        result["results"][0] = setup
        return result

    with mock.patch.object(container, "run_commands", run_commands):
        answers = container_runner.runner(manifest, toolchains=[{"tool": "go", "version": "1.99.9"}])(
            [command("go"), command("go")])
    gaps = [g for a in answers for g in a.get("gaps", ())]
    assert [(g["kind"], g["tool"], g["version"]) for g in gaps] == [("toolchain_unavailable", "go", "1.99.9")]
    assert "1.99.9" in gaps[0]["detail"]


def test_a_stated_version_that_is_a_range_is_a_gap_and_the_run_goes_on(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"go.mod": "module m\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        answers = container_runner.runner(manifest, toolchains=[{"tool": "go", "version": ">=1.21"}])(
            [command("go")])
    assert "mise" not in calls[0]["commands"][0]["argv"][-1]
    assert [(g["kind"], g["version"]) for g in answers[0]["gaps"]] == [("toolchain_unavailable", ">=1.21")]


def test_every_need_names_the_version_a_failed_install_reports():
    import preparation
    assert all(spec.get("version") for spec in preparation.NEEDS.values())
    lines = preparation.setup(set(preparation.NEEDS))["lines"]
    assert all("DAODAN-MISSING" in line for line in lines) and any("vcpkg@2026-10-29" in line for line in lines)


def test_cargo_runs_on_the_rust_the_project_states_behind_mise():
    import preparation
    first, *_ = container_runner.plan("cargo", [command("cargo")], [{"tool": "rust", "version": "1.80.0"}])
    assert "install rust@1.80.0" in first["argv"][-1] and first["network"] == "registries"
    [line] = [x for x in preparation.toolchains([{"tool": "rust", "version": "1.80.0"}])["lines"] if " install " in x]
    assert "bin-paths rust@1.80.0" in line and " x rust@1.80.0 -- " in line  # rustup's proxies need mise's env


def test_dotnet_runs_on_the_sdk_the_project_states(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"global.json": '{"sdk": {"version": "8.0.404"}}\n'})
    calls, fake = recorder()
    stated = [{"tool": "dotnet", "version": "8.0.404", "declared_in": "global.json"},
              {"tool": "dotnet-target", "version": "net8.0", "declared_in": "a.csproj#TargetFramework"}]
    with mock.patch.object(container, "run_commands", fake):
        answers = container_runner.runner(manifest)([command("dotnet")], toolchains=stated)
    setup = calls[0]["commands"][0]["argv"][2]
    assert " install dotnet@8.0.404 " in setup and "net8.0" not in setup
    assert "dot.net" in calls[0]["registries"]  # where mise takes Microsoft's install script
    assert "gaps" not in answers[0]  # the target framework is not a toolchain to install


def test_the_jvm_build_tools_run_on_the_common_base_with_the_jdk_and_the_proxy_set_for_java(tmp_path, no_download):
    import preparation
    _, manifest = manifest_of(tmp_path, {"pom.xml": "<project/>\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        for tool in ("maven", "gradle", "sbt"):
            container_runner.runner(manifest)([command(tool, "registries"), command(tool)])
        container_runner.runner(manifest)([command("dotnet")])
    images = [c["image"] for c in calls]
    assert images[:3] == [preparation.IMAGE] * 3 and images[3] == container_runner.IMAGE
    jdk = preparation.JDK_IN.rsplit("/", 1)[1]
    for call, tool in zip(calls[:3], ("maven", "gradle", "sbt")):
        assert call["inputs"]()[preparation.JDK_IN] == Path("/host") / jdk  # carried in like the build tool
        setup = call["commands"][0]["argv"][-1]  # the JDK first: `jar` unpacks the build tool
        assert setup.index(preparation.UNPACK_JDK) < setup.index(container_runner.TOOLS[tool]["setup"][-1])
        for given in call["commands"][1:]:  # the JVM ignores HTTPS_PROXY: each command gets Java's own settings;
            script = given["argv"][2]       # the execution's container keeps the state volume, not the link
            assert script.startswith(preparation.UNPACK_JDK) and preparation.JAVA_PROXY in script
            assert given["argv"][-2:] == [tool, "x"]
    assert calls[3]["commands"][1]["argv"] == ["dotnet", "x"]


def test_the_jdk_of_the_jvm_build_tools_is_temurin_s_checked_by_the_sha256_daodan_pins(tmp_path, monkeypatch):
    import preparation
    asked = []
    monkeypatch.setattr(container_runner, "fetched", lambda url, sha, name: asked.append((url, sha, name))
                        or Path("/host") / name)
    _, manifest = manifest_of(tmp_path, {"pom.xml": "<project/>\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)([command("maven", "registries")])
    calls[0]["inputs"]()
    assert (*preparation.TEMURIN, preparation.JDK_IN.rsplit("/", 1)[1]) in asked


def test_a_gradle_build_that_asks_for_a_newer_jvm_runs_again_on_the_jdk_the_project_states_or_gradle_names(
        tmp_path, no_download):
    """real-app-kotlinconf: a plugin of the build needs JVM 21 and Gradle runs on the image's 17. The model runs
    again on the JDK the project states at or above 21 (its devcontainer's), else on the 21 Gradle's error names,
    which is a gap; the second run installs it with mise and Gradle runs on it (JAVA_HOME)."""
    _, manifest = manifest_of(tmp_path, {"settings.gradle.kts": 'rootProject.name = "k"\n'})
    asked = {"returncode": 1, "stdout": "", "stderr": "> Dependency requires at least JVM runtime version 21. This "
                                                      "build uses a Java 17 JVM.\n"}
    image = {"tool": "java", "version": "21", "declared_in": ".devcontainer/devcontainer.json"}
    for stated, installed, kinds in (([], "java@21", ["jdk_from_build_error"]),
                                     ([{**image, "version": "25"}], "java@25", []),
                                     ([{**image, "version": "17"}], "java@21", ["jdk_from_build_error"])):
        calls = []

        def run_commands(project, commands, **options):
            calls.append({"commands": commands, **options})
            answer = asked if len(calls) == 1 else {"returncode": 0, "stdout": "", "stderr": ""}
            return {"state": "done", "root": "/work", "results": [{"returncode": 0, "stdout": "", "stderr": ""},
                                                                  answer]}
        with mock.patch.object(container, "run_commands", run_commands):
            [answer] = container_runner.runner(manifest)([command("gradle", "registries")], stated)
        assert len(calls) == 2, stated
        assert "install java@" not in calls[0]["commands"][0]["argv"][2]
        assert f"install {installed}" in calls[1]["commands"][0]["argv"][2]
        assert "JAVA_HOME" in calls[1]["commands"][1]["argv"][2]
        assert answer["returncode"] == 0
        assert [g["kind"] for g in answer.get("gaps", [])] == kinds
        assert all("JVM runtime version 21" in g["detail"] for g in answer.get("gaps", []))


def test_a_gradle_build_that_fails_runs_again_reaching_the_repositories_its_settings_declare(tmp_path, no_download):
    """real-app-kotlinconf: a plugin of `pluginManagement` comes from a repository the settings declare, which is
    no registry. The settings record names it before the configure fails; a second run reaches it, and one that
    fails too is a gap naming the hosts. A build that does not fail runs once."""
    _, manifest = manifest_of(tmp_path, {"settings.gradle.kts": 'rootProject.name = "k"\n'})
    build = "\x1e" + json.dumps({"kind": "build", "root": "/work", "name": "k", "nested": False, "gradle": "9.9.1",
                                 "projects": [], "repositories": ["https://plugins.gradle.org/m2",
                                                                  "https://maven.example.dev/releases"]})
    failed = {"returncode": 1, "stdout": build + "\n", "stderr": "Could not resolve all artifacts for configuration"
                                                                 " 'classpath'.\n"}
    for first, second, kinds in ((1, 0, []), (1, 1, ["declared_hosts_failed"]), (0, 0, [])):
        calls = []

        def run_commands(project, commands, **options):
            calls.append(options)
            code = first if len(calls) == 1 else second
            return {"state": "done", "root": "/work", "results": [{"returncode": 0, "stdout": "", "stderr": ""},
                                                                  {**failed, "returncode": code}]}
        with mock.patch.object(container, "run_commands", run_commands):
            [answer] = container_runner.runner(manifest)([command("gradle", "registries")])
        assert len(calls) == (2 if first else 1) and "maven.example.dev" not in calls[0]["registries"]
        assert not first or "maven.example.dev" in calls[1]["registries"]
        assert answer["returncode"] == (second if first else 0)
        assert [g["kind"] for g in answer.get("gaps", [])] == kinds
        assert all("maven.example.dev" in g["detail"] for g in answer.get("gaps", []))
