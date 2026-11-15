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


def test_each_configure_preset_is_configured_with_the_compiler_its_toolchain_file_names(tmp_path):
    """`host` builds the driver and the tests; `cortex-m4`'s toolchain file sets arm-none-eabi-gcc, which the
    preparation brings, and defines `sensor_fw`, built only when cross compiling."""
    record = build(tmp_path, "sys-cmake-presets")
    units = targets(record)
    assert set(units) == {"sensor_driver", "sensor_tests", "sensor_fw"}
    assert units["sensor_fw"]["depends_on"] == ["sensor_driver"] and units["sensor_fw"]["root"] == "firmware"
    assert units["sensor_driver"]["config"]["presets"] == ["cortex-m4", "host"] or \
        sorted(units["sensor_driver"]["config"]["presets"]) == ["cortex-m4", "host"]
    assert units["sensor_tests"]["config"]["presets"] == ["host"]
    assert units["sensor_fw"]["config"]["presets"] == ["cortex-m4"]
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_a_project_below_the_top_that_no_one_adds_is_configured_on_its_own(tmp_path):
    record = build(tmp_path, "nested-project")
    units = targets(record)
    assert {n: (u["root"], u["manifest"]) for n, u in units.items()} == {
        "core": ("core", "core/CMakeLists.txt"), "gen": ("tools/gen", "tools/gen/CMakeLists.txt")}
    assert {"tool": "cmake", "version": "3.20", "declared_in": "tools/gen/CMakeLists.txt#cmake_minimum_required",
            "sources": ["cmake@4.4.5"]} in record["toolchains"]
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_vcpkg_installs_the_manifest_before_the_configure_and_wins_over_conan(tmp_path):
    """vcpkg.json and conanfile.txt both declared, no preset naming one: vcpkg, with a `choice` gap."""
    record = build(tmp_path, "sys-cpp-vcpkg-conan")
    [imgtool] = targets(record).values()
    assert (imgtool["name"], imgtool["root"], imgtool["config"]["sources"]) == ("imgtool", "src", ["src/main.cpp"])
    [choice] = [g for g in record["gaps"] if g["kind"] == "choice"]
    assert "vcpkg prepares" in choice["detail"]
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_")]


def test_conan_installs_the_lockfile_before_the_configure(tmp_path):
    record = build(tmp_path, "conan-only")
    [imgtool] = targets(record).values()
    assert (imgtool["name"], imgtool["root"]) == ("imgtool", "src")
    assert not [g for g in record["gaps"] if g["kind"].startswith("model_") or g["kind"] == "choice"]


def test_a_preset_whose_compiler_no_need_brings_is_a_gap_naming_it(tmp_path):
    """The preset's toolchain file names a compiler no need brings: CMake's error names it; the plain configure
    still gives its target."""
    record = build(tmp_path, "unknown-compiler")
    assert set(targets(record)) == {"probe"}
    [gap] = [g for g in record["gaps"] if g["kind"] == "model_failed"]
    assert gap["preset"] == "riscv" and "riscv64-unknown-elf-gcc" in gap["detail"]


def test_commands_prepare_the_dependencies_and_the_compilers_first():
    texts = {"CMakeLists.txt": "project(a)\n", "vcpkg.json": "{}", "conanfile.txt": "[requires]\n",
             "CMakePresets.json": json.dumps({"configurePresets": [
                 {"name": "base", "hidden": True, "toolchainFile": "${sourceDir}/cmake/arm.cmake"},
                 {"name": "m4", "inherits": "base"}, {"name": "host"},
                 {"name": "conan", "cacheVariables": {"CMAKE_TOOLCHAIN_FILE": "build/conan_toolchain.cmake"}}]}),
             "cmake/arm.cmake": "set(CMAKE_C_COMPILER arm-none-eabi-gcc)\n", "lib/conanfile.py": "",
             "lib/CMakeLists.txt": "project(l)\n"}

    class Inventory:
        files = list(texts)
        headers = dict.fromkeys(texts)
        text = staticmethod(texts.__getitem__)

    class Context:
        inventory = Inventory()

    commands = cmake.commands(Context())
    first, *configures = [c for c in commands if c["cwd"] == "."]
    assert (first["argv"][3], first["network"], first["needs"]) == ("prepare", "registries", ["conan"])
    assert "conan prepares" in first["choice"]
    assert {c["argv"][4]: c.get("needs") for c in configures} == {"": None, "m4": ["arm-none-eabi"], "host": None,
                                                                   "conan": None}
    lib = [c for c in commands if c["cwd"] == "lib"]
    assert lib[0]["needs"] == ["conan"] and "choice" not in lib[0]


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
    assert [(c["cwd"], c["argv"][4]) for c in commands] == [(".", ""), (".", "dev"), ("tools/gen", "")]
    assert {c["network"] for c in commands} == {"none"} and {c["tool"] for c in commands} == {"cmake"}


def test_a_restore_that_fails_is_a_gap_naming_the_manager_and_the_reason():
    """The prepare command's answer is shaped by hand: a real vcpkg failure needs a port that does not build."""
    prepare = {"tool": "cmake", "argv": ["sh", "-c", "x", "prepare", "root"], "cwd": ".", "env": {},
               "network": "registries", "needs": ["vcpkg"]}
    failed = {"returncode": 1, "stdout": "", "root": "/work",
              "stderr": "error: building fmt:x64-linux failed with: BUILD_FAILED\n"}
    record = cmake.read(None, [prepare], [failed])
    [gap] = [g for g in record["gaps"] if g["kind"] == "restore_failed"]
    assert (gap["manager"], gap["path"]) == ("vcpkg", ".") and "BUILD_FAILED" in gap["detail"]
