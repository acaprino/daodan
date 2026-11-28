"""rust-analyzer's index: project code (build scripts, procedural macros) only in Daodan's container, none on the host.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_rust.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import code_graph  # noqa: E402
import container  # noqa: E402
import engine_tools  # noqa: E402
import preparation  # noqa: E402
from indexers import rust  # noqa: E402

INDEX = ROOT / "tests/fixtures/code-graph/rust/index.scip"
CRATES = "registry+https://github.com/rust-lang/crates.io-index"
# What `cargo check --message-format=json` prints when two build scripts and a procedural macro fail
# (hoppscotch's Tauri apps: a -sys crate without its system library, the app's own script).
CHECKED = "\n".join(json.dumps(item) for item in (
    {"reason": "build-script-executed", "package_id": f"{CRATES}#serde@1.0.228",
     "linked_libs": [], "linked_paths": [], "cfgs": ["no_core"], "env": [], "out_dir": "/tmp/t/build/serde-1/out"},
    {"reason": "build-script-executed", "package_id": "path+file:///work/apps/app#0.1.0", "linked_libs": [],
     "linked_paths": [], "cfgs": ["desktop", "desktop"], "env": [], "out_dir": "/tmp/t/build/app-1/out"},
    {"reason": "compiler-message", "package_id": f"{CRATES}#bad-macro@0.1.0",
     "manifest_path": "/daodan/state/cargo/registry/src/index.crates.io-0/bad-macro-0.1.0/Cargo.toml",
     "target": {"kind": ["proc-macro"], "crate_types": ["proc-macro"], "name": "bad_macro", "src_path": "/x/lib.rs"},
     "message": {"rendered": "error[E0425]: cannot find value `x` in this scope\n", "level": "error",
                 "message": "cannot find value `x` in this scope", "spans": [], "children": []}},
    {"reason": "compiler-message", "package_id": "path+file:///work/apps/agent#0.1.18",
     "manifest_path": "/work/apps/agent/Cargo.toml",
     "target": {"kind": ["lib"], "crate_types": ["lib"], "name": "agent", "src_path": "/work/apps/agent/src/lib.rs"},
     "message": {"rendered": "error[E0433]: failed to resolve\n", "level": "error", "message": "failed to resolve",
                 "spans": [], "children": []}},
    {"reason": "build-finished", "success": False})) + "\n"
FAILED = """error: failed to run custom build command for `glib-sys v0.18.1`

Caused by:
  process didn't exit successfully: `/tmp/daodan-rust-target/debug/build/glib-sys-a/build-script-build` (exit status: 1)
  --- stdout
  cargo:rerun-if-env-changed=GLIB_2.0_NO_PKG_CONFIG
  --- stderr

  pkg-config exited with status code 1
  > PKG_CONFIG_ALLOW_SYSTEM_CFLAGS=1 pkg-config --libs --cflags glib-2.0 'glib-2.0 >= 2.70'

  The system library `glib-2.0` required by crate `glib-sys` was not found.
warning: build failed, waiting for other jobs to finish...
error: failed to run custom build command for `agent v0.1.18 (/work/apps/agent)`

Caused by:
  process didn't exit successfully: `/tmp/t/debug/build/agent-b/build-script-build` (exit status: 101)
  --- stderr
  thread 'main' panicked at build.rs:2:5:
  frontendDist ../dist does not exist
"""


def test_rust_analyzer_never_runs_on_the_host(tmp_path, monkeypatch):
    """rust-analyzer's `scip` runs `cargo check` for the build scripts and builds the procedural macros whatever
    `buildScripts.enable` and `procMacro.enable` say (cli/scip.rs at the pinned release: `load_out_dirs_from_check:
    true`, the sysroot's server; measured on Modal: the build script ran, `thiserror-impl` was built and expanded),
    and a `rust-project.json` or `.cargo/config.toml` names other programs it starts. So it runs only in Daodan's
    container: the pass hands it the engine, and nothing of it starts here."""
    assert rust.NEEDS_CONTAINER and rust.BOXED == {"cargo": {"features": "all"}}
    started = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: started.append(args) or pytest.fail("a process"))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: started.append(args) or pytest.fail("a process"))
    result = rust.index(ROOT / "tests/fixtures/code-graph/rust", tmp_path / "work", roots={""}, boxes=[])
    assert result["state"] == "unavailable" and result["indexes"] == [] and started == []


def test_the_structure_names_the_containers_runs_and_their_rust():
    """One run per Cargo workspace's root and per crate outside one, as Cargo builds them; the Rust a rustup file
    names (a `rust-version` is a minimum, never installed)."""
    record = {"units": [{"kind": "cargo-crate", "root": ".", "registries": ["https://gitlab.com/a/b.git"]},
                        {"kind": "cargo-crate", "root": "tools"}, {"kind": "cargo-crate", "root": "ws/x"},
                        {"kind": "cargo-crate", "root": "ws/y"}],
              "workspace": [{"tool": "cargo", "root": "ws", "members": ["ws/x", "ws/y"]}],
              "toolchains": [{"tool": "rust", "version": "1.82.0", "declared_in": "rust-toolchain.toml"},
                             {"tool": "rust", "version": "1.70", "declared_in": "Cargo.toml"}]}
    given = rust.structure(record)
    assert given["boxes"] == [".", "tools", "ws"] and given["roots"] == {"", "tools", "ws", "ws/x", "ws/y"}
    assert given["toolchains"] == [record["toolchains"][0]] and "declared" not in given  # the pass's, as for every
    # analyzer whose build runs in a container


def test_the_container_prepares_rust_and_the_crates_then_checks_and_indexes_with_no_network():
    prepare, execute, needs = rust.scripts([".", "ws"], [])
    assert "cargo fetch" in prepare and preparation.restore("cargo", [".", "ws"]) in prepare
    tools = preparation.setup(["rust"])  # Daodan's rustc and cargo, as root before the preparation (`T3.A.6b`)
    assert needs["tools"] == {"lines": tools["lines"], "caps": tools["caps"]} and tools["lines"][0] not in prepare
    assert all(name in prepare for name in ("rust-std.tar.xz", "rust-src.tar.xz"))
    assert {name for _url, _digest, name in needs["files"]} >= {"rustc.tar.xz", "cargo.tar.xz", "rust-std.tar.xz",
                                                                 "rust-src.tar.xz"}
    assert "CARGO_NET_OFFLINE=true" in execute and "mise" not in prepare
    assert f"chmod 755 {rust.ANALYZER}" in prepare  # the copy carries a file's bytes, not its mode
    # The same check rust-analyzer starts, through its own compiler wrapper, so its run finds the scripts done.
    assert "RUSTC_WRAPPER=" in execute and "RA_RUSTC_WRAPPER=1" in execute
    assert "cargo check --quiet --workspace --message-format=json --all-features --keep-going --all-targets" in execute
    assert execute.count(f"{rust.ANALYZER} scip . --output") == 2 and "cd /work/ws" in execute
    # A rustup file's Rust, with mise, and its standard library's sources, which rust-analyzer reads.
    prepare, _execute, needs = rust.scripts(["."], [{"tool": "rust", "version": "1.82.0",
                                                     "declared_in": "rust-toolchain.toml"}])
    assert "install rust@1.82.0" in prepare and "rustup component add rust-src" in prepare
    assert {name for _url, _digest, name in needs["files"]} >= {"mise"}


def test_each_build_script_or_procedural_macro_that_fails_is_a_gap_and_its_crate_reads_as_on_the_host():
    gaps, failed, cfgs = rust.built(".", CHECKED, FAILED, 101)
    assert failed == ["apps/agent"]  # a crate of the project whose build script failed: its cfgs are not set
    assert cfgs == {"apps/app": ["desktop"]}  # what each crate of the project's build script set
    assert [(gap["kind"], gap["path"]) for gap in gaps] == [
        ("build_script_failed", "."), ("build_script_failed", "apps/agent"), ("proc_macro_not_built", ".")]
    assert gaps[0]["detail"] == ("the build script of glib-sys 0.18.1 failed: The system library `glib-2.0` required "
                                 "by crate `glib-sys` was not found: " + rust.FALLBACK.format("glib-sys"))
    assert gaps[1]["detail"].startswith("the build script of agent 0.1.18 failed: thread 'main' panicked at "
                                        "build.rs:2:5: frontendDist ../dist does not exist: ")
    assert gaps[2]["detail"] == ("the procedural macro bad-macro 0.1.0 did not build: cannot find value `x` in this "
                                 "scope: " + rust.UNEXPANDED)
    # A check that ran no build script at all: the root reads as with build scripts off.
    gaps, failed, _cfgs = rust.built("ws", "", "error: failed to get `x` as a dependency of package `y`\n", 101)
    assert failed == ["ws"] and gaps == [{"kind": "build_scripts_not_run", "path": "ws", "detail": (
        "cargo check in ws ran no build script (exit code 101): error: failed to get `x` as a dependency of package "
        "`y`: " + rust.FALLBACK.format("ws"))}]
    assert rust.built(".", CHECKED.splitlines()[0], "", 0) == ([], [], {})
    # system-deps (the gtk-rs crates) prints its error on stdout, as cargo warnings.
    printed = ("error: failed to run custom build command for `soup3-sys v0.5.0`\n\nCaused by:\n  process didn't exit "
               "successfully: `/tmp/t/debug/build/soup3-sys-e1/build-script-build` (exit status: 1)\n  --- stdout\n"
               "  cargo:rerun-if-env-changed=SOUP3_NO_PKG_CONFIG\n  cargo:warning=\n  The system library `libsoup-3.0` "
               "required by crate `soup3-sys` was not found.\n")
    assert rust.built(".", "", printed, 101)[0][0]["detail"].startswith(
        "the build script of soup3-sys 0.5.0 failed: The system library `libsoup-3.0` required by crate `soup3-sys` "
        "was not found: ")
    silent = printed.split("  --- stdout")[0]
    assert rust.built(".", "", silent, 101)[0][0]["detail"].startswith(
        "the build script of soup3-sys 0.5.0 failed: process didn't exit successfully: its build script (exit status")


class _Engine:
    name = "test"


def _boxed(tmp_path, monkeypatch, outcome, written):
    """`rust.index` with the engine the pass found and a container run that leaves `written` in its out folder."""
    project = tmp_path / "project"
    shutil.copytree(ROOT / "tests/fixtures/code-graph/rust", project, ignore=shutil.ignore_patterns("index.scip"))
    (project / "tools/src").mkdir(parents=True)
    (project / "tools/Cargo.toml").write_text('[package]\nname = "tools"\nversion = "0.1.0"\n', encoding="utf-8")
    (project / "tools/src/main.rs").write_text("fn main() {}\n", encoding="utf-8")
    asked = {}

    def run_in_container(project_dir, command, **options):
        asked.update(options, command=command)
        back = Path(options["out_dir"]) / "rust-analyzer"
        back.mkdir(parents=True)
        for name, data in written.items():
            (back / name).write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        (Path(options["out_dir"]) / "prepare.log").write_text("", encoding="utf-8")
        return outcome

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(rust, "_analyzer", lambda: tmp_path / "rust-analyzer")
    monkeypatch.setattr(preparation, "fetched", lambda url, digest, name: tmp_path / name)
    result = rust.index(project, tmp_path / "work", roots={"", "tools"}, boxes=[".", "tools"], toolchains=[],
                        declared={"hosts": ("gitlab.com",), "where": {}}, engine=_Engine())
    return result, asked


def test_the_index_runs_in_the_container_and_a_root_it_gave_no_index_of_is_a_run_without_one(tmp_path, monkeypatch):
    written = {"version.txt": "rust-analyzer 1.0.0 (abc 2026-11-09)\n", "libexec.txt": "rust-analyzer-proc-macro-srv\n",
               "check-0.code": "101\n", "check-0.json": CHECKED, "check-0.err": FAILED, "scip-0.code": "0\n",
               "scip-0.log": "Generating SCIP finished\n", "index-0.scip": INDEX.read_bytes(),
               "check-1.code": "0\n", "check-1.json": "", "check-1.err": "", "scip-1.code": "1\n",
               "scip-1.log": "error: failed to load workspace\n"}
    result, asked = _boxed(tmp_path, monkeypatch, {"state": "done", "exit_code": 0}, written)
    assert "gitlab.com" in asked["registries"] and asked["memory"] == rust.MEMORY and asked["image"] == rust.IMAGE
    assert [prefix for _path, prefix in result["indexes"]] == [""] and result["build"].startswith("rust-ana")
    assert (result["indexer"]["version"], result["toolchain"], result["config"]) == (
        engine_tools.RUST_ANALYZER_RELEASE, preparation.NEEDS["rust"]["version"], rust.BOXED)
    kinds = [(gap["kind"], gap.get("path")) for gap in result["gaps"]]
    assert kinds == [("build_script_failed", "."), ("build_script_failed", "apps/agent"),
                     ("proc_macro_not_built", ".")]
    # The root rust-analyzer wrote no index of: a run without one, with its words, which the pass makes a gap, and
    # the reason its files have no document. Nothing reads it on the host.
    tools = next(run for run in result["runs"] if run["prefix"] == "tools")
    assert tools["index"] is None and "failed to load workspace" in tools["stderr_tail"]
    assert result["configs"]["failed"] == {"tools": "exit code 1"}
    # Beside the container's index, what it was built with: the cfgs of the build scripts that ran are set.
    boxed = Path(result["indexes"][0][0])
    assert json.loads(boxed.with_suffix(".cfg.json").read_text(encoding="utf-8")) == {
        "target": "container", "scripts": True, "failed": ["apps/agent"], "cfgs": {"apps/app": ["desktop"]}}
    index = code_graph.Index(tmp_path / "project")
    for path, prefix in result["indexes"]:
        index.load(Path(path), prefix)
    assert rust._configuration(index, "src/lib.rs") == (rust.CONTAINER, True, [])
    assert rust._configuration(index, "apps/agent/src/lib.rs") == (rust.CONTAINER, "failed", [])
    assert rust._configuration(index, "apps/app/src/main.rs") == (rust.CONTAINER, True, ["desktop"])
    assert rust._configuration(index, "tools/src/main.rs") == (rust.CONTAINER, True, [])  # the root's run's
    # A cfg a build script that ran did not set is false; one it set, or one rust-analyzer may set, is not.
    assert rust._cfg("desktop", rust.CONTAINER, True, []) is False and rust._cfg("desktop", rust.CONTAINER, True,
                                                                                ["desktop"]) is True
    assert rust._cfg("test", rust.CONTAINER, True, []) is None and rust._cfg("windows", rust.CONTAINER, True) is False


def test_a_container_that_does_not_run_is_the_cause_and_nothing_runs_on_the_host(tmp_path, monkeypatch):
    """No step falls back to a host run (AGENTS.md): the language is unavailable, or failed, with the cause."""
    result, _asked = _boxed(tmp_path, monkeypatch, {"state": "gap", "cause": "no engine", "remedy": "start"}, {})
    assert (result["state"], result["indexes"], result["install"]) == ("unavailable", [], "start")
    assert result["reason"] == "rust-analyzer runs only in Daodan's container: no engine"
    result, _asked = _boxed(tmp_path / "b", monkeypatch, {"state": "timeout"}, {})
    assert result["state"] == "failed" and result["reason"].startswith("the container run of rust-analyzer ended "
                                                                         "timeout")
