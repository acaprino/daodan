"""The preparation's dependency restores: each package manager's own command, run in Daodan's container.

The answers are in `tests/fixtures/premap/restore/<manager>.json`, recorded once in a real container from the
projects beside them (`tests/fixtures/premap/restore/<manager>/`): `good` restores, `bad` names a package no
registry has.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import preparation  # noqa: E402

ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "restore"


def recorded(manager):
    stored = json.loads((ANSWERS / f"{manager}.json").read_text(encoding="utf-8"))
    assert stored["line"] == preparation.restore(manager, ["good", "bad"]), "the recorded line is not the current one"
    return stored["result"]


def test_gradle_resolves_every_configuration_and_a_package_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("gradle")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "gradle", "bad")]
    assert "org.example.missing:nothing:9.9.9" in gaps[0]["detail"]


def test_maven_goes_offline_and_a_package_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("maven")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "maven", "bad")]
    assert "org.example.missing:nothing" in gaps[0]["detail"]


def test_a_restore_runs_where_the_build_starts_and_its_hosts_are_declared_once():
    files = ["settings.gradle", "app/build.gradle", "lib/build.gradle", "tools/x/build.gradle.kts", "pom.xml",
             "core/pom.xml", "other/pom.xml"]
    assert preparation.restores(files) == {"gradle": ["."], "maven": ["."]}
    assert preparation.restores(["a/pom.xml", "b/pom.xml", "b/c/pom.xml"]) == {"maven": ["a", "b"]}
    assert set(preparation.RESTORES["gradle"]["hosts"]) >= {"plugins.gradle.org", "services.gradle.org"}


def test_every_restore_line_reports_its_failure_and_the_run_goes_on():
    for manager in preparation.RESTORES:
        line = preparation.restore(manager, ["x"])
        assert "DAODAN-RESTORE-FAILED" in line and line.endswith("true"), manager


def test_npm_installs_without_scripts_and_a_package_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("npm")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "npm", "bad")]
    assert "@example-missing/nothing" in gaps[0]["detail"]


def test_pnpm_installs_from_its_lockfile_and_one_out_of_date_is_a_gap():
    gaps = preparation.restore_gaps(recorded("pnpm")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "pnpm", "bad")]
    assert "OUTDATED_LOCKFILE" in gaps[0]["detail"]


def test_yarn_installs_from_its_lockfile_and_one_out_of_date_is_a_gap():
    gaps = preparation.restore_gaps(recorded("yarn")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "yarn", "bad")]
    assert "lockfile" in gaps[0]["detail"].lower()


FAKE_NPM = """#!/bin/sh
echo "npm $*" >> "$CALLS"
[ -n "${REFUSE:-}" ] && { echo "npm error code EBADENGINE" >&2; exit 1; }
while [ $# -gt 0 ]; do [ "$1" = --prefix ] && prefix=$2; shift; done
mkdir -p "$prefix/bin" && printf '#!/bin/sh\\necho "installed corepack $*" >> "$CALLS"\\n' > "$prefix/bin/corepack"
chmod 755 "$prefix/bin/corepack"
"""


def test_pnpm_and_yarn_run_a_corepack_with_npms_current_key_and_none_installed_is_a_gap(tmp_path):
    """mix-infra-gha on Node 20.18.1: the corepack a Node ships may predate npm's registry key of January 2025
    ("Cannot find matching keyid"), and from Node 25 none ships. The line installs one with the Node's own npm,
    apart and first on the path, from 0.31.0, the first release with that key; npm takes the newest whose engines
    take that Node. When npm installs none, the Node's own corepack runs and the preparation names what it lacks."""
    import os
    import subprocess
    programs = tmp_path / "programs"
    programs.mkdir()
    for name, text in (("npm", FAKE_NPM), ("corepack", '#!/bin/sh\necho "bundled corepack $*" >> "$CALLS"\n')):
        (programs / name).write_text(text, encoding="utf-8", newline="\n")
        (programs / name).chmod(0o755)
    (tmp_path / "web").mkdir()
    plan = preparation.node_prepare(["web/package.json", "web/pnpm-lock.yaml"], lambda rel: "{}")
    for refuse in ("", "1"):
        tools, calls = tmp_path / f"tools{refuse}", tmp_path / f"calls{refuse}"
        done = subprocess.run(["sh", "-c", plan["lines"][0].replace(preparation.T, str(tools))], cwd=tmp_path,
                              env={**os.environ, "PATH": f"{programs}:{os.environ['PATH']}", "CALLS": str(calls),
                                   "REFUSE": refuse}, capture_output=True, text=True, timeout=60)
        ran = calls.read_text(encoding="utf-8").splitlines()
        assert ran[0] == (f"npm install -g --prefix {tools}/corepack --engine-strict --no-audit --no-fund"
                          " --loglevel=error corepack@>=0.31.0 <=0.36.0")
        assert ran[1:] == [f"{'bundled' if refuse else 'installed'} corepack pnpm install --frozen-lockfile"]
        assert preparation.missing(done.stderr) == ([{
            "kind": "toolchain_unavailable", "tool": "corepack", "version": ">=0.31.0",
            "detail": "corepack >=0.31.0: the preparation could not install it (its output is in the run's log)"}]
            if refuse else [])
    # npm comes with Node: its restore needs no corepack.
    assert "corepack" not in preparation.node_prepare(["package.json"], lambda rel: "{}")["lines"][0]


def test_one_node_folder_has_one_manager_its_lockfile_names():
    """A workspace's members restore with its root, whatever manager the root uses; a folder with its own
    lockfile is a project of its own."""
    assert preparation.restores(["package.json", "pnpm-lock.yaml", "packages/a/package.json"]) == {"pnpm": ["."]}
    files = ["package.json", "packages/a/package.json", "web/package.json", "web/pnpm-lock.yaml",
             "site/package.json", "site/yarn.lock"]
    assert preparation.restores(files) == {"npm": ["."], "pnpm": ["web"], "yarn": ["site"]}


def test_uv_syncs_its_lockfile_and_one_out_of_date_is_a_gap():
    gaps = preparation.restore_gaps(recorded("uv")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "uv", "bad")]
    assert "needs to be updated" in gaps[0]["detail"]


def test_poetry_installs_its_lockfile_and_one_out_of_date_is_a_gap():
    gaps = preparation.restore_gaps(recorded("poetry")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "poetry", "bad")]
    assert "poetry.lock" in gaps[0]["detail"]


def test_pip_requirements_install_into_a_separate_environment_and_a_missing_package_is_a_gap():
    gaps = preparation.restore_gaps(recorded("pip")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "pip", "bad")]
    assert "example-missing-nothing" in gaps[0]["detail"]


def test_one_python_folder_has_one_manager_its_lockfile_names():
    files = ["pyproject.toml", "uv.lock", "packages/a/pyproject.toml", "svc/pyproject.toml", "svc/poetry.lock",
             "tools/requirements.txt"]
    assert preparation.restores(files) == {"uv": ["."], "poetry": ["svc"]}
    assert preparation.restores(["tools/requirements.txt", "api/pyproject.toml"]) == {"pip": ["api", "tools"]}


def test_a_restore_names_what_it_needs_from_the_preparation():
    assert preparation.RESTORES["uv"]["needs"] == ["uv"] and preparation.RESTORES["poetry"]["needs"] == ["poetry"]
    assert all(n in preparation.NEEDS for spec in preparation.RESTORES.values() for n in spec.get("needs", ()))


def test_go_downloads_each_module_and_one_no_proxy_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("go")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "go", "bad")]
    assert "example.com/missing" in gaps[0]["detail"]


def test_cargo_fetches_the_crates_and_one_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("cargo")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "cargo", "bad")]
    assert "example-missing-nothing" in gaps[0]["detail"]


def test_every_go_module_restores_on_its_own_and_a_cargo_workspace_from_its_root():
    files = ["go.mod", "tools/go.mod", "Cargo.toml", "crates/a/Cargo.toml"]
    assert preparation.restores(files) == {"go": [".", "tools"], "cargo": ["."]}


def test_dotnet_restores_the_solution_or_the_project_and_a_package_no_feed_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("dotnet")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "dotnet", "bad")]
    assert "Example.Missing.Nothing" in gaps[0]["detail"]


def test_a_dotnet_solution_restores_the_projects_below_it():
    files = ["App.sln", "src/App/App.csproj", "tests/T/T.fsproj", "tools/x/x.csproj"]
    assert preparation.restores(files) == {"dotnet": ["."]}
    assert preparation.restores(["a/A.csproj", "b/B.vbproj"]) == {"dotnet": ["a", "b"]}
