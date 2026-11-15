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
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

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
    snapshot.write_snapshot(project, manifest)
    return project, manifest


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


def test_a_setup_that_installs_from_a_registry_runs_in_the_preparation(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"tsconfig.json": "{}\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)([command("tsc")])
    first = calls[0]["commands"][0]
    assert first["network"] == "registries" and "typescript@6.0.3" in first["argv"][-1]
    assert calls[0]["commands"][1]["network"] == "none"


def test_bazel_reaches_its_own_hosts_beside_the_registries_and_no_other_tool_does(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"MODULE.bazel": "module(name = 'x')\n"})
    calls, fake = recorder()
    with mock.patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)([command("bazel", "registries")])
        container_runner.runner(manifest)([command("cmake")])
    bazel_run, cmake_run = calls
    assert set(bazel_run["registries"]) - set(container.REGISTRIES) == {
        "bcr.bazel.build", "github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com",
        "mirror.bazel.build", "codeload.github.com"}
    assert cmake_run["registries"] == container.REGISTRIES and cmake_run["commands"][0]["network"] == "none"


def test_without_an_engine_the_source_states_nothing_and_its_gap_says_why(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"Cargo.toml": "[package]\nname = 'a'\nversion = '0.1.0'\n"})
    _, fake = recorder(state="gap")
    with mock.patch.object(container, "run_commands", fake):
        record = premap.write(manifest, sources=(premap.cargo,), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g["kind"] == "source_failed"]
    assert "no engine" in gap["detail"] and not record["units"]


def test_a_failed_setup_fails_the_source(tmp_path, no_download):
    _, manifest = manifest_of(tmp_path, {"go.mod": "module m\n"})
    _, fake = recorder(answers=[])
    with mock.patch.object(container, "run_commands", lambda *a, **k: {
            **fake(*a, **k), "results": [{"returncode": 2, "stdout": "", "stderr": "tar: go.tar.gz: not found"}, {}]}):
        with pytest.raises(RuntimeError, match="not found"):
            container_runner.runner(manifest)([command("go")])


def test_every_model_source_of_the_premap_has_a_setup():
    tools = {"go": premap.go, "cargo": premap.cargo, "uv": premap.uv, "tsc": premap.tsc, "npm": premap.npm,
             "renovate": premap.renovate, "daodan-enry": premap.enry, "cmake": premap.cmake, "meson": premap.meson,
             "bazel": premap.bazel}
    assert {s for s in premap.SOURCES if hasattr(s, "commands")} == set(tools.values())
    assert set(tools) <= set(container_runner.TOOLS)


# ------------------------------------------------- smoke, on a real engine

SMOKE = os.environ.get("DAODAN_PREMAP_SMOKE") == "1"
CORPUS = ROOT / "benchmarks/project-model/fixtures"
CASES = {  # tool -> (corpus fixture, the source), one project each
    "go": ("sys-go-buildtags", premap.go), "cargo": ("sys-rust-features", premap.cargo),
    "uv": ("py-uv-workspace", premap.uv), "tsc": ("js-vite-react-ts", premap.tsc),
    "npm": ("js-npm-workspaces", premap.npm), "renovate": ("js-npm-single", premap.renovate),
    "daodan-enry": ("js-vendored-generated", premap.enry), "cmake": ("sys-cmake-targets", premap.cmake),
    "meson": ("sys-meson", premap.meson), "bazel": ("sys-bazel", premap.bazel)}


@pytest.mark.skipif(not SMOKE, reason="set DAODAN_PREMAP_SMOKE=1 to run each source in a real container")
@pytest.mark.parametrize("tool", sorted(CASES))
def test_smoke_each_tool_runs_in_the_container_and_states_its_facts(tmp_path, tool):
    name, source = CASES[tool]
    engine = container.find_engine()
    held = lambda: (container.cli(engine, "ps", "-a", "-q").stdout, container.cli(engine, "volume", "ls", "-q").stdout)  # noqa: E731
    before = held()
    project = tmp_path / "proj"
    shutil.copytree(CORPUS / name, project, ignore=shutil.ignore_patterns("expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    record = premap.write(manifest, sources=(source,), runner=container_runner.runner(manifest, engine=engine))
    print(json.dumps({"tool": tool, "sources": record["sources"], "units": len(record["units"]),
                      "gaps": record["gaps"][:5]}, indent=1)[:3000])
    [status] = record["sources"]
    assert status["state"] == "ran", status
    assert not [g for g in record["gaps"] if g["kind"] in ("source_failed", "model_failed")]
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
    assert all("DAODAN-MISSING" in line for line in lines) and "vcpkg@2026-10-29" in lines[0]
