"""The CMake source of the pre-map: CMake's file API answers, recorded once in a Linux container, read into units.

The answers are in `tests/fixtures/premap/cmake/<fixture>.json`, captured from the benchmark fixture of the same
name (`benchmarks/project-model/fixtures/`) with CMake 4.4.5 in `buildpack-deps:noble`.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import premap  # noqa: E402
from premap import cmake  # noqa: E402
import snapshot  # noqa: E402

CORPUS = ROOT / "benchmarks/project-model/fixtures"
ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "cmake"


def replay(name):
    stored = json.loads((ANSWERS / f"{name}.json").read_text(encoding="utf-8"))
    table = {json.dumps(run["command"], sort_keys=True): run["result"] for run in stored["runs"]}
    return lambda commands: [table[json.dumps(command, sort_keys=True)] for command in commands]


def build(tmp_path, name, sources=(cmake,)):
    project = tmp_path / "proj"
    own = ANSWERS / name  # a project written for this source, beside its answers
    shutil.copytree(own if own.is_dir() else CORPUS / name, project, ignore=shutil.ignore_patterns("expected.json"))
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return premap.write(manifest, sources=sources, runner=replay(name))


def targets(record):
    return {u["name"]: u for u in record["units"] if u["kind"] == "cmake-target"}


def test_each_target_is_a_unit_with_its_folder_sources_and_links(tmp_path):
    record = build(tmp_path, "sys-cmake-targets")
    units = targets(record)
    assert set(units) == {"calc_core", "calc"}
    core, app = units["calc_core"], units["calc"]
    assert (core["root"], core["manifest"], core["source_roots"]) == ("core", "core/CMakeLists.txt", ["core/src"])
    assert (app["root"], app["manifest"], app["depends_on"]) == ("app", "app/CMakeLists.txt", ["calc_core"])
    assert core["config"]["type"] == "STATIC_LIBRARY" and app["config"]["type"] == "EXECUTABLE"
    assert core["config"]["sources"] == ["core/src/archive.cpp", "core/src/expr.cpp"]
    assert core["config"]["include_dirs"] == ["core/include", "core/src"]
    assert app["config"]["include_dirs"] == ["core/include"]
    assert core["config"]["build_tags"] == app["config"]["build_tags"] == ["CALC_WITH_ZLIB=1"]
    assert all(u["sources"] == ["cmake@4.4.5"] and u["run"]["executes_project_code"] for u in units.values())
    assert {"tool": "cmake", "version": "3.20", "declared_in": "CMakeLists.txt#cmake_minimum_required",
            "sources": ["cmake@4.4.5"]} in record["toolchains"]
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_beside_the_file_readers_the_project_folder_without_a_target_is_superseded(tmp_path):
    """modules.py reads `project(calc)` at the top as a unit; CMake defines no target there."""
    record = build(tmp_path, "sys-cmake-targets", sources=(*[s for s in premap.SOURCES if not hasattr(s, "commands")],
                                                           cmake))
    assert sorted((u["root"], u["name"]) for u in record["units"] if u["kind"] == "cmake-target") == [
        ("app", "calc"), ("core", "calc_core")]
    [gap] = [g for g in record["gaps"] if g["kind"] == "superseded"]
    assert gap["path"] == "."


def test_an_interface_library_is_a_unit_and_its_users_depend_on_it(tmp_path):
    units = targets(build(tmp_path, "sys-cpp-header-only"))
    assert set(units) == {"ringbuf", "ringbuf_tests"}
    assert units["ringbuf"]["config"]["type"] == "INTERFACE_LIBRARY" and units["ringbuf"]["root"] == "."
    assert units["ringbuf_tests"]["depends_on"] == ["ringbuf"]
    assert units["ringbuf_tests"]["config"]["include_dirs"] == ["include"]


def test_targets_of_folders_below_the_top_keep_their_own_folder(tmp_path):
    units = targets(build(tmp_path, "sys-c-macro-annotations"))
    assert {n: (u["root"], u["depends_on"]) for n, u in units.items()} == {
        "zmini": ("c", []), "zminipp": ("cpp", ["zmini"])}
    assert units["zminipp"]["config"]["include_dirs"] == ["cpp", "include"]


def test_each_configure_preset_is_configured_and_names_the_targets_it_defines(tmp_path):
    """`host` builds the driver and the tests; `cortex-m4` needs an ARM cross compiler the container lacks, so its
    configure fails, and `sensor_fw`, defined only when cross compiling, stays unknown with a gap."""
    record = build(tmp_path, "sys-cmake-presets")
    units = targets(record)
    assert set(units) == {"sensor_driver", "sensor_tests"}
    assert units["sensor_tests"]["depends_on"] == ["sensor_driver"]
    assert units["sensor_driver"]["config"]["presets"] == units["sensor_tests"]["config"]["presets"] == ["host"]
    [gap] = [g for g in record["gaps"] if g["kind"] == "model_failed"]
    assert (gap["path"], gap["preset"]) == (".", "cortex-m4")


def test_a_project_below_the_top_that_no_one_adds_is_configured_on_its_own(tmp_path):
    record = build(tmp_path, "nested-project")
    units = targets(record)
    assert {n: (u["root"], u["manifest"]) for n, u in units.items()} == {
        "core": ("core", "core/CMakeLists.txt"), "gen": ("tools/gen", "tools/gen/CMakeLists.txt")}
    assert {"tool": "cmake", "version": "3.20", "declared_in": "tools/gen/CMakeLists.txt#cmake_minimum_required",
            "sources": ["cmake@4.4.5"]} in record["toolchains"]
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_a_failed_configure_is_a_gap_and_states_no_unit(tmp_path):
    record = build(tmp_path, "sys-cpp-vcpkg-conan")
    assert targets(record) == {}
    [gap] = [g for g in record["gaps"] if g["kind"] == "model_failed"]
    assert gap["path"] == "." and "fmt" in gap["detail"] and gap["source"] == "cmake@4.4.5"


def test_commands_configure_the_tops_the_projects_below_them_and_each_preset():
    texts = {"CMakeLists.txt": "project(a)\nadd_subdirectory(lib)\n", "lib/CMakeLists.txt": "add_library(l l.c)\n",
             "tools/gen/CMakeLists.txt": "cmake_minimum_required(VERSION 3.20)\n  Project (gen C)\n",
             "CMakePresets.json": '{"configurePresets": [{"name": "base", "hidden": true}, {"name": "dev"}]}'}

    class Inventory:
        files = [*texts, "src/a.c"]
        headers = dict.fromkeys(texts)
        text = staticmethod(texts.__getitem__)

    class Context:
        inventory = Inventory()

    commands = cmake.commands(Context())
    assert [(c["cwd"], c["argv"][-1]) for c in commands] == [(".", ""), (".", "dev"), ("tools/gen", "")]
    assert {c["network"] for c in commands} == {"none"} and {c["tool"] for c in commands} == {"cmake"}
