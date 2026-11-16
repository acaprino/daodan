"""The C and C++ indexer's run: the units the pre-map gives, the container run with no network, CMake's own
record of what a unit asks FetchContent for, and the contract built from what comes back.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_clang.py

Every test fakes the container except the smoke test at the end, which indexes `fixtures/clang-index/fetch` in a
real one and only with DAODAN_CLANG_SMOKE=1.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import shutil
import sys
from pathlib import Path, PurePosixPath
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import code_graph  # noqa: E402
import container  # noqa: E402
import preparation  # noqa: E402
from indexers import clang, clang_run  # noqa: E402

FMT = {"name": "fmt", "urls": ["https://github.com/fmtlib/fmt.git"]}
# CMake 3.28's message when a target links to a target nothing defines (policy CMP0028).
LINK_ERROR = '''CMake Error at CMakeLists.txt:8 (target_link_libraries):
  Target "app" links to:

    fmt::fmt

  but the target was not found.  Possible reasons include:

    * There is a typo in the target name.
    * A find_package call is missing for an IMPORTED target.
    * An ALIAS target is missing.

-- Generating done (0.0s)
CMake Generate step failed.  Build files cannot be regenerated correctly.
'''


# ---------------------------------------------------------------------------------------------------------------
# In the container: clang_run.py


def test_the_configure_never_downloads_and_hands_cmake_the_recording_provider(tmp_path):
    command = clang_run.configure_command("cmake", {"root": "lib"}, tmp_path / "build", tmp_path / "fetch.log")
    assert command == ["cmake", "-S", str(clang_run.WORK / "lib"), "-B", str(tmp_path / "build"),
                       "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
                       f"-DCMAKE_PROJECT_TOP_LEVEL_INCLUDES={clang_run.SCRATCH / 'provider.cmake'}",
                       f"-DDAODAN_FETCH_LOG={tmp_path / 'fetch.log'}"]


def test_the_configure_reads_the_initial_cache_the_restore_wrote(tmp_path):
    """The pre-map's configure reads the initial cache vcpkg's or Conan's install writes (`-C`), which names the
    manager's toolchain file: so does this one, once the preparation's restore wrote it."""
    init = tmp_path / "init.cmake"
    unit = {"root": ".", "init": str(init)}
    assert "-C" not in clang_run.configure_command("cmake", unit, tmp_path / "b", tmp_path / "f.log")  # it failed
    init.write_text('set(CMAKE_TOOLCHAIN_FILE "/t/vcpkg.cmake" CACHE FILEPATH "")\n', encoding="utf-8")
    assert clang_run.configure_command("cmake", unit, tmp_path / "b", tmp_path / "f.log")[:4] == \
        ["cmake", "-C", str(init), "-S"]


def test_the_provider_records_each_fetchcontent_dependency_and_supplies_none():
    """CMake's dependency provider is called for each FetchContent_MakeAvailable with the details the project
    declared. It writes the name and the URLs and returns without populating, so FetchContent goes on with
    downloads disabled. CMake takes as provider only a command already defined."""
    provider = clang_run.PROVIDER
    assert "cmake_language(SET_DEPENDENCY_PROVIDER daodan_record_fetch" in provider
    assert provider.index("function(daodan_record_fetch ") < provider.index("cmake_language(SET_DEPENDENCY_PROVIDER")
    assert "SUPPORTED_METHODS FETCHCONTENT_MAKEAVAILABLE_SERIAL)" in provider
    assert 'file(APPEND "${DAODAN_FETCH_LOG}"' in provider
    assert "FetchContent_SetPopulated" not in provider and "file(DOWNLOAD" not in provider


def test_the_record_gives_each_dependency_once_with_its_urls(tmp_path):
    log = tmp_path / "fetch.log"
    assert clang_run.fetch_record(log) == []
    log.write_text("fmt\thttps://github.com/fmtlib/fmt.git\nlocal\nfmt\thttps://github.com/fmtlib/fmt.git\n"
                   "zstd\thttps://a.example/zstd.tar.gz\thttps://b.example/zstd.tar.gz\n", encoding="utf-8")
    assert clang_run.fetch_record(log) == [FMT, {"name": "zstd", "urls": ["https://a.example/zstd.tar.gz",
                                                                       "https://b.example/zstd.tar.gz"]}]


def _runner(code, output, record=""):
    """A fake `run` answering each command with `(code, output)`; a configure writes `record` where the
    provider would."""
    calls = []

    def run(command, cwd, timeout=3600):
        calls.append(command)
        for argument in command:
            if argument.startswith("-DDAODAN_FETCH_LOG=") and record:
                Path(argument.split("=", 1)[1]).write_text(record, encoding="utf-8")
        return code, output, 1.0
    return run, calls


RECORD = "fmt\thttps://github.com/fmtlib/fmt.git\n"


def test_a_failed_configure_after_a_fetch_request_is_unavailable_with_what_cmake_recorded(tmp_path):
    run, calls = _runner(1, LINK_ERROR, RECORD)
    steps, state = clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b", tmp_path / "fetch.log")
    assert len(calls) == 1 and [step["step"] for step in steps] == ["configure"]
    assert state == {"state": "unavailable", "kind": "download-outside-registries", "fetched": [FMT],
                     "error": LINK_ERROR, "cause": "the configure needs what FetchContent would download from "
                                                   "github.com, outside the allowed registries"}


def test_a_failed_configure_without_a_fetch_request_failed_and_names_what_is_not_recorded(tmp_path):
    uncovered = "FetchContent asked for nothing; file(DOWNLOAD) and ExternalProject are not recorded"
    run, _calls = _runner(1, LINK_ERROR)
    _steps, state = clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b", tmp_path / "fetch.log")
    assert state == {"state": "failed", "error": LINK_ERROR,
                     "cause": f"the configure ended with exit code 1; {uncovered}"}
    run, _calls = _runner(None, "")
    _steps, state = clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b2", tmp_path / "fetch2.log")
    assert state == {"state": "failed", "error": "", "cause": f"the configure timed out; {uncovered}"}


# CMake 3.28's message when the folder of a submodule that is not checked out is added.
SUBMODULE_ERROR = '''CMake Error at CMakeLists.txt:7 (add_subdirectory):
  add_subdirectory given source "third_party/fmt" which is not an existing
  directory.


-- Configuring incomplete, errors occurred!
'''


def test_a_configure_that_reads_a_submodule_not_checked_out_is_unavailable_and_names_it(tmp_path):
    """The pre-map names the submodules whose folder is missing or empty; one CMake's output names is the cause."""
    run, _calls = _runner(1, SUBMODULE_ERROR)
    unit = {"root": ".", "absent": ["docs/theme", "third_party/fmt"]}
    _steps, state = clang_run.configure(run, "cmake", unit, tmp_path / "b", tmp_path / "fetch.log")
    assert state == {"state": "unavailable", "kind": "submodule-absent", "error": SUBMODULE_ERROR,
                     "cause": "the configure reads third_party/fmt: a git submodule not checked out "
                              "(git submodule update --init)"}
    _steps, other = clang_run.configure(run, "cmake", {"root": ".", "absent": ["third_party/fm"]}, tmp_path / "b2",
                                        tmp_path / "fetch2.log")
    assert other["state"] == "failed"  # a path CMake does not name, a prefix of one included
    report = {"peak_mb": None, "units": [{"root": ".", **state, "steps": [], "compiled": {}, "index": None}]}
    result, _seen = _index(tmp_path, report, [UNIT])
    assert (result["state"], result["reason"]) == ("unavailable", f".: {state['cause']}")


def test_a_configure_that_succeeds_is_configured_whatever_the_provider_recorded(tmp_path):
    run, _calls = _runner(0, "-- Generating done\n", RECORD)
    assert clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b", tmp_path / "fetch.log")[1] == \
        {"state": "configured"}


def test_no_second_attempt_is_taken_today(tmp_path):
    """The place for a second configure exists; until the map-driven round counts the units that need one, it
    gives no arguments, so a failed configure runs once."""
    assert clang_run.second_attempt({"root": "."}, LINK_ERROR) is None
    run, calls = _runner(1, LINK_ERROR, RECORD)
    steps, _state = clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b", tmp_path / "fetch.log")
    assert len(calls) == len(steps) == 1


def test_the_compilation_database_counts_the_commands_of_each_file(tmp_path):
    work = PurePosixPath(str(clang_run.WORK))
    compdb = tmp_path / "compile_commands.json"
    compdb.write_text(json.dumps([{"directory": str(work / "build"), "file": "../util.c"},
                                  {"directory": str(work), "file": "util.c"},
                                  {"directory": str(work), "file": "main.c"}]), encoding="utf-8")
    assert clang_run.compiled(compdb) == {"main.c": 1, "util.c": 2}


def test_the_report_is_written_into_the_folder_the_caller_names_under_the_scratch_folder(tmp_path):
    """`index()` names the report's folder under the script's scratch folder (`clang.OUT`): emptying the scratch
    folder at the start leaves that folder for the report."""
    scratch, tools, plan = tmp_path / "scratch", tmp_path / "tools", tmp_path / "units.json"
    out = scratch / PurePosixPath(clang.OUT).relative_to(clang_run.SCRATCH.as_posix()).as_posix()
    tools.mkdir()
    (tools / "scip-clang").write_bytes(b"")
    plan.write_text(json.dumps([{"root": "."}]), encoding="utf-8")
    run, _calls = _runner(1, LINK_ERROR, RECORD)
    with mock.patch.multiple(clang_run, SCRATCH=scratch, TOOLS=tools, run=run, package_map=lambda project: []):
        assert clang_run.main(["clang_run.py", str(plan), str(out), "1"]) == 0
    report = json.loads((out / "result.json").read_text(encoding="utf-8"))
    assert [(unit["root"], unit["state"], unit["fetched"]) for unit in report["units"]] == [(".", "unavailable", [FMT])]


def test_a_unit_that_configures_without_a_compilation_database_failed_and_says_why(tmp_path):
    """CMake writes no compile_commands.json for a project without a C or C++ target, or for a generator that
    exports none: the unit is not left `configured`, a state without a cause the host cannot report."""
    scratch, tools, plan, out = tmp_path / "scratch", tmp_path / "tools", tmp_path / "units.json", tmp_path / "out"
    tools.mkdir()
    (tools / "scip-clang").write_bytes(b"")
    plan.write_text(json.dumps([{"root": "docs"}]), encoding="utf-8")
    run, _calls = _runner(0, "-- Generating done\n")
    with mock.patch.multiple(clang_run, SCRATCH=scratch, TOOLS=tools, run=run, package_map=lambda project: []):
        assert clang_run.main(["clang_run.py", str(plan), str(out), "1"]) == 0
    unit, = json.loads((out / "result.json").read_text(encoding="utf-8"))["units"]
    assert (unit["root"], unit["state"], unit["index"]) == ("docs", "failed", None)
    assert unit["cause"] == "no compilation database: the configure wrote no compile_commands.json"
    assert [step["step"] for step in unit["steps"]] == ["configure"]


# ---------------------------------------------------------------------------------------------------------------
# On the host: index()


UNIT = {"name": "app", "kind": "cmake-target", "root": ".", "manifest": "CMakeLists.txt"}


def test_without_a_c_or_cpp_unit_the_index_is_unavailable(tmp_path):
    """C code that nothing builds (a vendored folder) has no command: no build of the pre-map compiles it."""
    result = clang.index(tmp_path, tmp_path / "work", units=[{"name": "web", "kind": "npm-package", "root": "web"}])
    assert (result["state"], result["reason"]) == ("unavailable", clang.NO_UNIT)
    assert clang.NO_UNIT == "no C or C++ unit in the pre-map: no build of the project compiles C or C++"


MSBUILD = "built with MSBuild: Daodan takes no compilation database from MSBuild"


def test_an_msbuild_project_is_stated_once_per_folder(tmp_path):
    """Several project files share a folder: the folder is stated once."""
    app = {"name": "app", "kind": "msbuild-project", "root": "win"}
    alone = clang.index(tmp_path, tmp_path / "work", units=[app, {**app, "name": "lib"}])
    assert (alone["state"], alone["reason"]) == ("unavailable", MSBUILD)
    assert clang.unbuilt([UNIT, app, {**app, "name": "lib"}, {"name": "m", "kind": "meson-target", "root": "m"}]) == [
        {"root": "win", "state": "unavailable", "kind": "no-database", "cause": MSBUILD}]
    assert "msbuild-project" in clang.UNIT_KINDS


def test_a_file_without_a_document_names_its_own_cause():
    win = {"root": "win", "state": "unavailable", "kind": "no-database", "cause": MSBUILD}
    configs = {"compiled": {"lib/a.c": 1}, "units": [win, {"root": "lib", "state": "indexed"}]}
    reasons = clang.missing(None, ["win/main.cpp", "tools/gen.c", "tools/gen.h", "lib/a.c", "lib/unused.c"], configs)
    assert reasons == {"win/main.cpp": f"the index of unit win is unavailable: {MSBUILD}",
                       "tools/gen.c": "in no C or C++ unit of the pre-map",
                       "tools/gen.h": "header no indexed translation unit includes in an active branch",
                       "lib/a.c": "compiled, yet no document in the index",
                       "lib/unused.c": "no compile command: not built by the default configuration"}
    # Another build's file beside the CMakeLists.txt CMake indexed does not speak for the folder.
    both = {"units": [{**win, "root": "."}, {"root": ".", "state": "indexed"}]}
    assert clang.missing(None, ["a.c"], both) == {"a.c": "no compile command: not built by the default configuration"}
    # A build that stopped before compiling a file says so.
    stopped = {"units": [{"root": "c", "build": "make", "state": "indexed", "cause": "make ended with exit code 2"}]}
    assert clang.missing(None, ["c/late.c"], stopped) == {"c/late.c": "no compile command: make ended with exit code 2"}


def test_a_workspace_is_configured_once_at_its_root():
    """Members of a CMake workspace (`add_subdirectory`) are configured from the workspace's root; a unit in no
    workspace from its own; units of other build tools and languages are left to their indexers. The states are
    the dynamic step's (`dynamic/clang.py`): it configures with CMake only."""
    units = [UNIT, {**UNIT, "name": "lib", "root": "lib"}, {**UNIT, "name": "cli", "root": "apps/cli"},
             {**UNIT, "name": "gen", "root": "tools/gen"}, {"name": "web", "kind": "npm-package", "root": "web"},
             {"name": "m", "kind": "meson-target", "root": "m"}, {"name": "g", "kind": "go-module", "root": "g"}]
    workspace = [{"tool": "cmake", "root": ".", "members": ["lib", "apps/cli"]},
                 {"tool": "npm", "root": ".", "members": ["web"]}]
    roots, states = clang.configure_roots(units, workspace)
    assert roots == [".", "tools/gen"]
    assert states == [{"root": "m", "state": "unavailable", "kind": "not-cmake",
                       "cause": "built with meson: Daodan configures C and C++ units with CMake only"}]


def test_scip_clang_needs_an_x86_64_machine(tmp_path):
    with mock.patch.object(container, "architecture", return_value="arm64"):
        result = clang.index(tmp_path, tmp_path / "work", units=[UNIT])
    assert result["state"] == "unavailable" and "x86_64" in result["reason"]


def _fake_run(tmp_path, report: dict | None, state: str = "done", **extra):
    """A `run_in_container` that records its call and brings back `report` and the index files it names."""
    seen = {}

    def run(project, command, **options):
        seen.update(options)
        seen.update(project=project, command=command, inputs=options["inputs"]())
        back = Path(options["out_dir"]) / PurePosixPath(clang.OUT).name
        back.mkdir(parents=True, exist_ok=True)
        if report is not None:
            (back / "result.json").write_text(json.dumps(report), encoding="utf-8")
            for unit in report["units"]:
                if unit["index"]:
                    (back / unit["index"]).write_bytes(b"\x0a\x00")
        return {"state": state, "exit_code": 0 if state == "done" else None, "outputs": [], **extra}
    return run, seen


TOOLS = {f"{clang.TOOLS}/scip-clang": Path("scip-clang"), f"{clang.TOOLS}/cmake.tar.gz": Path("cmake.tar.gz"),
         f"{clang.TOOLS}/clang_run.py": Path("clang_run.py")}
UNAVAILABLE = {"root": "vendor", "state": "unavailable", "kind": "download-outside-registries", "fetched": [FMT],
               "cause": "the configure needs what FetchContent would download from github.com, outside the allowed "
                        "registries",
               "error": LINK_ERROR, "steps": [{"step": "configure", "returncode": 1, "seconds": 2.0,
                                               "tail": LINK_ERROR}],
               "compiled": {}, "index": None}


def _index(tmp_path, report, units, workspace=None, state="done", cpus=1, **extra):
    run, seen = _fake_run(tmp_path, report, state, **extra)
    with mock.patch.object(container, "run_in_container", run), mock.patch.object(clang, "tools", return_value=TOOLS), \
            mock.patch.object(container, "architecture", return_value="x64"):
        return clang.index(tmp_path / "project", tmp_path / "work", units=units, workspace=workspace, cpus=cpus), seen


def test_one_run_with_no_network_indexes_the_units_that_configure_and_states_the_others(tmp_path):
    report = {"peak_mb": 210, "units": [
        {"root": ".", "state": "indexed", "index": "index-0.scip", "compiled": {"main.c": 1, "util.c": 2},
         "steps": [{"step": "configure", "returncode": 0, "seconds": 2.0, "tail": ""},
                   {"step": "index", "returncode": 0, "seconds": 4.0, "tail": "", "diagnostics": {"errors": 0}}]},
        UNAVAILABLE]}
    units = [UNIT, {**UNIT, "name": "vendor", "root": "vendor"}, {"name": "w", "kind": "msbuild-project", "root": "m"}]
    result, seen = _index(tmp_path, report, units)
    assert seen["image"] == clang.IMAGE and seen["outputs"] == [clang.OUT] and "prepare" not in seen
    assert seen["command"] == ["python3", f"{clang.TOOLS}/clang_run.py", f"{clang.TOOLS}/units.json", clang.OUT, "1"]
    assert seen["cpus"] == 1
    assert set(seen["inputs"]) == set(TOOLS) | {f"{clang.TOOLS}/units.json"}
    assert json.loads(seen["inputs"][f"{clang.TOOLS}/units.json"].read_text(encoding="utf-8")) == \
        [{"root": "."}, {"root": "vendor"}]
    assert result["indexes"] == [[str((tmp_path / "work" / "index-0.scip").resolve()), ""]]
    assert result["units"][2]["error"] == LINK_ERROR and result["units"][2]["fetched"] == [FMT]
    assert [(unit["root"], unit["state"], unit.get("kind")) for unit in result["units"]] == \
        [("m", "unavailable", "no-database"), (".", "indexed", None),
         ("vendor", "unavailable", "download-outside-registries")]
    assert result["configs"]["compiled"] == {"main.c": 1, "util.c": 2}
    assert [run["step"] for run in result["runs"]] == ["configure", "index", "configure"]
    assert result["indexer"] == {"name": "scip-clang", "version": clang.VERSION, "seconds": 8.0, "peak_mb": 210}
    # A file of a unit left unindexed says why it has no document.
    reasons = clang.missing(None, ["vendor/app.cpp", "m/x.c", "orphan.c"], clang.tasks(result["configs"]))
    assert reasons["vendor/app.cpp"] == f"the index of unit vendor is unavailable: {UNAVAILABLE['cause']}"
    assert reasons["m/x.c"] == f"the index of unit m is unavailable: {MSBUILD}"
    assert reasons["orphan.c"] == "no compile command: not built by the default configuration"


def test_scip_clang_runs_as_many_jobs_as_the_caller_gives_the_container(tmp_path):
    """The share is the caller's: the container's CPU limit and scip-clang's jobs, never the machine's count."""
    assert clang_run.index_command(Path("scip-clang"), Path("cc.json"), Path("pm.json"), 3) == \
        ["scip-clang", "--compdb-path=cc.json", "--package-map-path=pm.json", "--jobs=3", "--show-compiler-diagnostics"]
    assert "cpu_count" not in Path(clang_run.__file__).read_text(encoding="utf-8")
    _result, seen = _index(tmp_path, None, [UNIT], cpus=3)
    assert seen["cpus"] == 3 and seen["command"][-1] == "3"


def test_without_an_index_the_result_is_unavailable_when_no_unit_failed(tmp_path):
    result, _seen = _index(tmp_path, {"peak_mb": None, "units": [{**UNAVAILABLE, "root": "."}]}, [UNIT])
    assert result["state"] == "unavailable" and result["reason"] == f".: {UNAVAILABLE['cause']}"
    assert result["units"][0]["kind"] == "download-outside-registries" and result["indexes"] == []


def test_a_container_gap_is_unavailable_and_a_run_without_report_failed(tmp_path):
    gap, _seen = _index(tmp_path, None, [UNIT], None, "gap", cause="no engine", remedy="install WSL")
    assert (gap["state"], gap["reason"], gap["install"]) == ("unavailable", "no engine", "install WSL")
    failed, _seen = _index(tmp_path / "again", None, [UNIT], None, "timeout")
    assert failed["state"] == "failed" and "timeout" in failed["reason"]


INDEXED = {"peak_mb": 1, "units": [{"root": ".", "state": "indexed", "index": "index-0.scip", "compiled": {"a.c": 1},
                                    "steps": [{"step": "configure", "returncode": 0, "seconds": 1.0, "tail": ""}]}]}
STATED = [{"tool": "cmake", "version": "3.31", "declared_in": "CMakeLists.txt#cmake_minimum_required"}]


def _index_stated(tmp_path, toolchains, prepared: str = "", files: dict | None = None, **options):
    """`index()` with the pre-map's `toolchains` over a project holding `files`, and a container run whose
    preparation printed `prepared`."""
    project = tmp_path / "project"
    for rel, text in (files or {}).items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    run, seen = _fake_run(tmp_path, INDEXED)

    def logged(project, command, **options):
        if prepared:
            Path(options["out_dir"]).mkdir(parents=True, exist_ok=True)
            (Path(options["out_dir"]) / "prepare.log").write_text(prepared, encoding="utf-8")
        return run(project, command, **options)

    with mock.patch.object(container, "run_in_container", logged), \
            mock.patch.object(clang, "tools", return_value=TOOLS), \
            mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)), \
            mock.patch.object(container, "architecture", return_value="x64"):
        result = clang.index(project, tmp_path / "work", units=[UNIT], toolchains=toolchains, **options)
    return result, seen


def test_a_cmake_the_pre_map_states_above_the_pin_is_installed_by_the_preparation(tmp_path):
    """A CMake minimum the pin does not meet: mise installs the version stated in the preparation, the only
    phase with a network (mise's hosts), and the configure runs with it, with no network."""
    result, seen = _index_stated(tmp_path, STATED)
    assert "install cmake@3.31" in seen["prepare"][-1]
    assert "github.com" in seen["registries"]
    assert seen["inputs"][f"{preparation.IN}/mise"] == Path("mise")
    assert seen["command"][-1] == f"{preparation.T}/bin/cmake"
    assert all(path.startswith(container.STATE) for path in seen["inputs"])  # what a preparation keeps
    assert result["indexes"] and "gaps" not in result


def test_a_cmake_the_pin_meets_runs_in_one_phase_with_no_network(tmp_path):
    result, seen = _index_stated(tmp_path, [{**STATED[0], "version": "3.16"}])
    assert "prepare" not in seen and len(seen["command"]) == 5 and result["indexes"]


def test_a_cmake_the_preparation_could_not_install_is_a_gap_and_the_pin_configures(tmp_path):
    result, _seen = _index_stated(tmp_path, STATED, prepared="DAODAN-MISSING cmake@3.31\n")
    assert result["indexes"]
    assert [(gap["kind"], gap["tool"], gap["version"]) for gap in result["gaps"]] == [
        ("toolchain_unavailable", "cmake", "3.31")]
    assert clang_run.cmake_tool(str(tmp_path / "absent"), tmp_path) == "cmake"  # the pin, unpacked


def test_the_stage_is_handed_the_cmake_the_pre_map_states():
    record = {"units": [], "workspace": [], "toolchains": [*STATED, {"tool": "java", "version": "21"}]}
    assert clang.structure(record)["toolchains"] == STATED


def _plan(seen) -> list[dict]:
    return json.loads(seen["inputs"][f"{clang.TOOLS}/units.json"].read_text(encoding="utf-8"))


def test_a_root_that_declares_vcpkg_is_restored_as_the_pre_maps_configure_restores_it(tmp_path):
    """vcpkg's install in manifest mode runs in the preparation, with the registries and GitHub open, and writes
    the initial cache that names its toolchain file; the configure of that root reads it (`premap.cmake`)."""
    result, seen = _index_stated(tmp_path, [], files={"vcpkg.json": '{"dependencies": ["fmt"]}'})
    script = seen["prepare"][-1]
    assert "git clone -q --filter=blob:none https://github.com/microsoft/vcpkg" in script
    assert f"tar -xzf {clang.TOOLS}/cmake.tar.gz -C {preparation.T}" in script  # a CMake to build ports with
    assert "( cd /work && mkdir -p /daodan/state/prep/root && sh -c " in script and "prepare root )" in script
    assert "vcpkg install --x-manifest-root=." in script and "conan install" not in script
    assert seen["inputs"][f"{preparation.IN}/vcpkg"] == Path("vcpkg")
    assert {"github.com", *container.REGISTRIES} <= set(seen["registries"])
    assert seen["env"]["VCPKG_ROOT"] == preparation.ENV["VCPKG_ROOT"] and seen["env"]["PATH"] == preparation.PATH
    assert _plan(seen) == [{"root": ".", "init": "/daodan/state/prep/root/init.cmake"}]
    assert result["indexes"] and "gaps" not in result
    failed, _seen = _index_stated(tmp_path / "failed", [], files={"vcpkg.json": "{}"}, prepared=(
        "DAODAN-RESTORE-FAILED vcpkg .\nerror: building fmt:x64-linux failed\nDAODAN-RESTORE-END\n"))
    assert failed["gaps"] == [{"kind": "restore_failed", "manager": "vcpkg", "path": ".",
                               "detail": "error: building fmt:x64-linux failed"}]


def test_a_root_that_declares_both_managers_is_restored_by_the_one_the_pre_map_chose(tmp_path):
    """The one a configure preset's CMAKE_TOOLCHAIN_FILE names, else vcpkg."""
    both = {"vcpkg.json": "{}", "conanfile.txt": "[requires]\nfmt/10.2.1\n"}
    _result, seen = _index_stated(tmp_path / "vcpkg", [], files=both)
    assert "vcpkg install" in seen["prepare"][-1] and "conan install" not in seen["prepare"][-1]
    presets = {"version": 3, "configurePresets": [
        {"name": "conan", "cacheVariables": {"CMAKE_TOOLCHAIN_FILE": "build/conan_toolchain.cmake"}}]}
    _result, seen = _index_stated(tmp_path / "conan", [], files={**both, "CMakePresets.json": json.dumps(presets)})
    assert "conan install" in seen["prepare"][-1] and "vcpkg install" not in seen["prepare"][-1]
    assert seen["inputs"][f"{preparation.IN}/uv.tar.gz"] == Path("uv.tar.gz")
    assert "center2.conan.io" in seen["registries"]


def test_the_submodules_the_pre_map_finds_absent_go_to_each_configure(tmp_path):
    record = {"units": [], "workspace": [], "toolchains": [], "gaps": [
        {"kind": "submodule_absent", "path": "third_party/fmt", "detail": "not checked out"},
        {"kind": "model_failed", "path": ".", "detail": "cmake configure: CMake Error"}]}
    assert clang.structure(record)["absent"] == ["third_party/fmt"]
    _result, seen = _index_stated(tmp_path, [], absent=["third_party/fmt"])
    assert _plan(seen) == [{"root": ".", "absent": ["third_party/fmt"]}] and "prepare" not in seen


def test_the_tools_are_downloaded_once_and_checked_each_time(tmp_path):
    calls = []

    def download(url, target, *, sha256=None):
        calls.append(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"tool")
        return target
    import hashlib
    digest = hashlib.sha256(b"tool").hexdigest()
    with mock.patch("resolve_edges.shared_engine_dir", lambda name: tmp_path / name), \
            mock.patch("resolve_edges.download", download), mock.patch.object(clang, "SHA256", digest), \
            mock.patch.object(clang, "CMAKE", (clang.CMAKE[0], clang.CMAKE[1], digest)):
        first = clang.tools()
        second = clang.tools()
        (tmp_path / "scip-clang" / clang.VERSION / "scip-clang-x86_64-linux").write_bytes(b"tampered")
        third = clang.tools()
    assert first == second == third and len(calls) == 3  # two first downloads, one for the tampered binary
    assert first[f"{clang.TOOLS}/clang_run.py"] == Path(clang.__file__).with_name("clang_run.py")

    def broken(url, target, *, sha256=None):
        raise ValueError(f"checksum mismatch for {url}")
    with mock.patch("resolve_edges.shared_engine_dir", lambda name: tmp_path / "other" / name), \
            mock.patch("resolve_edges.download", broken), pytest.raises(container.Gap) as gap:
        clang.tools()
    assert "could not be downloaded and verified" in gap.value.cause


# ---------------------------------------------------------------------------------------------------------------
# The other builds: Meson's setup, Make and cgo under Bear, Bazel's compile actions


def _tool(code, output="", writes=None):
    """A fake `run` answering each command with `(code, output)`; it writes `writes` (path -> text) as the tool
    would, and the standard output a command sends to a file as `stdout` gives it."""
    calls = []

    def run(command, cwd, timeout=3600, stdout=None):
        calls.append((command, cwd))
        for path, text in {**(writes or {}), **({stdout: output} if stdout else {})}.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(text, encoding="utf-8")
        return code, output, 1.0
    return run, calls


MESON_ERROR = 'Run-time dependency zlib found: NO (tried pkgconfig and cmake)\n\nERROR: Dependency "zlib" not found\n'


def test_meson_writes_the_database_at_setup_with_wraps_never_downloaded(tmp_path):
    """Meson's Ninja backend writes compile_commands.json at setup (scip-clang's README); the setup runs the
    project's meson.build, so it runs here, with no network and wraps never downloaded."""
    build = tmp_path / "build"
    run, calls = _tool(0, writes={build / "compile_commands.json": "[]"})
    env = {"PYTHONPATH": "/m", "NINJA": "/n"}
    steps, state = clang_run.meson(run, {"root": "lib", "build": "meson"}, build, env)
    assert calls == [(["env", "PYTHONPATH=/m", "NINJA=/n", "python3", "-m", "mesonbuild.mesonmain", "setup",
                       "--wrap-mode", "nodownload", str(build)], clang_run.WORK / "lib")]
    assert state == {"state": "configured"} and [step["step"] for step in steps] == ["meson setup"]
    run, _calls = _tool(1, MESON_ERROR)
    _steps, state = clang_run.meson(run, {"root": ".", "build": "meson"}, tmp_path / "b2", env)
    assert state == {"state": "failed", "error": MESON_ERROR,
                     "cause": 'meson setup ended with exit code 1: ERROR: Dependency "zlib" not found'}


def test_make_runs_under_bear_with_the_targets_the_pre_map_states(tmp_path):
    """Bear records each compiler the build runs (scip-clang's README: `bear -- make`): the project's own make in
    the unit's folder, every target remade (`-B`: the copy may hold its outputs), going on past an error (`-k`)."""
    build = tmp_path / "build"
    out = build / "compile_commands.json"
    unit = {"root": "src", "build": "make", "targets": ["build/libmini.a", "build/mini"]}
    run, calls = _tool(0, writes={out: "[]"})
    _steps, state = clang_run.make(run, unit, build, 2)
    assert calls == [(["bear", "--output", str(out), "--", "make", "-B", "-k", "-j2", "build/libmini.a", "build/mini"],
                      clang_run.WORK / "src")]
    assert state == {"state": "configured"}
    # A build that stops is made once more, appending, without remaking what is made: in gVisor Bear's report of a
    # process fails now and then. One that stops again keeps what Bear saw, and says why the other files have none.
    run, calls = _tool(2, "make: *** [Makefile:20: build/mini] Error 1\n", writes={out: "[]"})
    steps, state = clang_run.make(run, unit, build, 2)
    assert calls[1] == (["bear", "--append", "--output", str(out), "--", "make", "-k", "-j2", "build/libmini.a",
                         "build/mini"], clang_run.WORK / "src")
    assert [step["step"] for step in steps] == ["make under Bear", "make under Bear again"]
    assert state == {"state": "configured", "cause": "make ended with exit code 2"}
    run, _calls = _tool(1, "bear: failed with: Events db open failed\n")
    state = clang_run.make(run, unit, tmp_path / "b2", 2)[1]
    assert state == {"state": "failed", "error": "bear: failed with: Events db open failed\n",
                     "cause": "make under Bear ended with exit code 1: bear: failed with: Events db open failed"}


def test_cgo_is_built_by_go_under_bear_wrappers_and_only_the_copys_files_are_kept(tmp_path):
    """The go command starts the C compiler without the C library's exec, which Bear's preload intercepts: Bear's
    compiler wrappers on the path see each compile. The standard library's C files and cgo's generated files are
    not the project's: only commands for files of the copy are kept."""
    build = tmp_path / "build"
    out = build / "compile_commands.json"
    work = PurePosixPath(str(clang_run.WORK))
    entries = [{"directory": str(work / "sum"), "file": str(work / "sum/fastsum.c"), "arguments": ["gcc", "-c"]},
               {"directory": "/tmp/go-build1/b002", "file": "/tmp/go-build1/b002/sum.cgo2.c", "arguments": ["gcc"]},
               {"directory": "/t/go/src/runtime/cgo", "file": "gcc_util.c", "arguments": ["gcc"]}]
    run, calls = _tool(0, writes={out: json.dumps(entries)})
    unit = {"root": ".", "build": "go", "packages": ["example.com/fastsum/sum"]}
    _steps, state = clang_run.go(run, "/t/go/bin/go", unit, build, None)
    (command, cwd), = calls
    assert command[:6] == ["bear", "--force-wrapper", "--output", str(out), "--", "env"]
    assert {"CGO_ENABLED=1", "GOPROXY=off", "GOTOOLCHAIN=local", "GOFLAGS=", f"GOPATH={clang_run.GOPATH}"} <= set(command)
    assert command[-4:] == ["/t/go/bin/go", "build", "-work", "example.com/fastsum/sum"]
    assert cwd == clang_run.WORK and state == {"state": "configured"}
    assert [entry["file"] for entry in json.loads(out.read_text(encoding="utf-8"))] == [str(work / "sum/fastsum.c")]
    # Modules the preparation could not download: Go's own error, and no build.
    download = {"step": "go mod download", "returncode": 1, "seconds": 2.0,
                "tail": "go: example.com/x@v1.0.0: reading https://proxy.golang.org/example.com/x/@v/v1.0.0.mod: "
                        "404 Not Found\n"}
    run, calls = _tool(0)
    steps, state = clang_run.go(run, "/t/go/bin/go", {**unit, "download": True}, tmp_path / "b2", download)
    assert calls == [] and steps == [download] and state["state"] == "failed"
    assert state["cause"] == ("go mod download ended with exit code 1: go: example.com/x@v1.0.0: reading "
                              "https://proxy.golang.org/example.com/x/@v/v1.0.0.mod: 404 Not Found")


AQUERY = {"actions": [
    {"mnemonic": "CppCompile", "arguments": ["/usr/bin/gcc", "-iquote", ".", "-iquote", "external/googletest~",
                                             "-c", "test/greet_test.cc", "-o", "bazel-out/k8/bin/greet_test.pic.o"]},
    {"mnemonic": "CppCompile", "arguments": ["/usr/bin/gcc", "-MD", "-MF", "bazel-out/k8/bin/g.pic.d", "-DGREET_LOUD=1",
                                             "-fno-canonical-system-headers", "-c", "lib/greet.cc", "-o", "g.o"]}]}


def test_bazels_compile_actions_are_commands_run_from_the_workspace(tmp_path):
    """`bazel aquery` gives the compile actions Bazel's analysis plans with their command lines, as hedron's
    extractor reads them: each is a command run from the workspace's root, where `external` leads to the output
    base's external repositories, the paths the actions name. The dependency file an action writes is left out:
    its folder under `bazel-out` is not there, nothing being built, and clang rejects gcc's flag for it."""
    prepared, base, work = tmp_path / "prepared", tmp_path / "base", tmp_path / "work"
    (base / "external").mkdir(parents=True)
    (work / "ws").mkdir(parents=True)
    prepared.mkdir()
    (prepared / "aquery.json").write_text(json.dumps(AQUERY), encoding="utf-8")
    (prepared / "output_base").write_text(f"{base}\n", encoding="utf-8")
    record = {"step": "bazel aquery", "returncode": 0, "seconds": 3.0, "tail": ""}
    unit = {"root": "ws", "build": "bazel"}
    with mock.patch.object(clang_run, "WORK", work):
        steps, state = clang_run.bazel(unit, tmp_path / "build", record, prepared)
    assert (steps, state) == ([record], {"state": "configured"})
    assert (work / "ws/external").resolve() == (base / "external").resolve()
    assert json.loads((tmp_path / "build/compile_commands.json").read_text(encoding="utf-8")) == [
        {"directory": str(work / "ws"), "arguments": AQUERY["actions"][0]["arguments"], "file": "test/greet_test.cc"},
        {"directory": str(work / "ws"), "arguments": ["/usr/bin/gcc", "-DGREET_LOUD=1", "-c", "lib/greet.cc", "-o", "g.o"],
         "file": "lib/greet.cc"}]
    # Bazel's own error when its aquery failed; when the preparation recorded none, where to look.
    error = "ERROR: Error computing the main repository mapping: error accessing registry https://bcr.bazel.build/\n"
    _steps, state = clang_run.bazel(unit, tmp_path / "b2", {**record, "returncode": 2, "tail": error}, prepared)
    assert state == {"state": "failed", "error": error, "cause": "bazel aquery ended with exit code 2: "
                     "ERROR: Error computing the main repository mapping: error accessing registry https://bcr.bazel.build/"}
    assert clang_run.bazel(unit, tmp_path / "b3", None, prepared)[1] == {
        "state": "failed", "cause": "the preparation recorded no bazel aquery: its output is in the run's prepare.log"}


def test_the_preparation_runs_bazels_aquery_and_gos_download_and_records_each(tmp_path):
    """The preparation is the only phase with a network: there Bazel's aquery fetches what its analysis reads
    and Go downloads the modules a cgo build needs; the execution reads what each recorded."""
    plan = tmp_path / "units.json"
    plan.write_text(json.dumps([{"root": "."}, {"root": "ws", "build": "bazel"},
                                {"root": "mod", "build": "go", "packages": ["m/p"], "download": True},
                                {"root": "m2", "build": "go", "packages": ["m2/p"]}]), encoding="utf-8")
    run, calls = _tool(0, '{"actions": []}')
    with mock.patch.multiple(clang_run, PREPARED=tmp_path / "prepared", run=run, bazel_tool=lambda: "/t/bazel",
                             go_tool=lambda: "/t/go"):
        assert clang_run.main(["clang_run.py", "prepare", str(plan)]) == 0
    assert [(command[:4], cwd) for command, cwd in calls] == [
        (["/t/bazel", "--max_idle_secs=5", "aquery", 'mnemonic("CppCompile", //...)'], clang_run.WORK / "ws"),
        (["/t/bazel", "--max_idle_secs=5", "info", "output_base"], clang_run.WORK / "ws"),
        (["env", f"GOPATH={clang_run.GOPATH}", "GOFLAGS=-mod=mod", "GOTOOLCHAIN=local"], clang_run.WORK / "mod")]
    assert calls[0][0][4:] == ["--output=jsonproto", "--include_artifacts=false", "--keep_going"]
    assert calls[2][0][-3:] == ["/t/go", "mod", "download"]
    steps = {n: json.loads((tmp_path / f"prepared/{n}/step.json").read_text(encoding="utf-8")) for n in ("1", "2")}
    assert [steps[n]["step"] for n in ("1", "2")] == ["bazel aquery", "go mod download"]
    assert (tmp_path / "prepared/1/aquery.json").is_file() and not (tmp_path / "prepared/3").exists()


def _main(tmp_path, units, answers):
    """`clang_run.main` over `units` in a scratch copy, each command answered by the first of `answers` (a word of
    the command -> `(code, output, writes)`) it holds; scip-clang writes an index."""
    scratch, tools, work, out, plan = (tmp_path / name for name in ("scratch", "tools", "work", "out", "units.json"))
    tools.mkdir(parents=True)
    work.mkdir()
    (tools / "scip-clang").write_bytes(b"")
    plan.write_text(json.dumps(units), encoding="utf-8")
    calls = []

    def run(command, cwd, timeout=3600, stdout=None):
        calls.append(command)
        if any("--compdb-path=" in word for word in command):
            (work / "index.scip").write_bytes(b"\x0a\x00")
            return 0, "", 1.0
        code, output, writes = next((answer for word, answer in answers.items() if word in command), (0, "", {}))
        for path, text in writes.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(text, encoding="utf-8")
        return code, output, 1.0
    with mock.patch.multiple(clang_run, SCRATCH=scratch, TOOLS=tools, WORK=work, run=run, package_map=lambda project: [],
                             meson_tools=lambda: {"PYTHONPATH": "/m", "NINJA": "/n"}, go_tool=lambda: "/t/go",
                             PREPARED=tmp_path / "prepared"):
        assert clang_run.main(["clang_run.py", str(plan), str(out), "2"]) == 0
    return json.loads((out / "result.json").read_text(encoding="utf-8"))["units"], calls


def test_each_unit_states_the_build_that_gave_its_commands(tmp_path):
    """Bear is installed once, from the packages the copy carries, before the first build that runs under it; a
    database that names no file of the copy is no index."""
    database = [{"directory": str(tmp_path / "work"), "file": str(tmp_path / "work/a.c"), "arguments": ["cc", "-c"]}]
    units = [{"root": "m", "build": "meson"}, {"root": "c", "build": "make", "targets": ["app"]},
             {"root": "g", "build": "go", "packages": ["g/p"]}]
    answers = {"mesonbuild.mesonmain": (0, "", {tmp_path / "scratch/build-0/compile_commands.json": json.dumps(database)}),
               "make": (0, "", {tmp_path / "scratch/build-1/compile_commands.json": json.dumps(database)}),
               "/t/go": (0, "", {tmp_path / "scratch/build-2/compile_commands.json": "[]"})}
    results, calls = _main(tmp_path, units, answers)
    assert [(unit["root"], unit["build"], unit["state"]) for unit in results] == [
        ("m", "meson", "indexed"), ("c", "make", "indexed"), ("g", "go", "failed")]
    assert results[2]["cause"] == "go build under Bear gave no compile command"
    install = ["sh", "-c", f"dpkg -i {tmp_path / 'tools'}/bear/*.deb"]
    assert calls.count(install) == 1 and calls.index(install) == 2  # after Meson's setup and its index
    assert [step["step"] for step in results[1]["steps"]] == ["install Bear", "make under Bear", "index"]
    # Bear that does not install: the builds that run under it say so.
    install = f"dpkg -i {tmp_path / 'again/tools'}/bear/*.deb"
    failed, _calls = _main(tmp_path / "again", units[1:2], {install: (1, "dpkg: error: cannot access archive\n", {})})
    assert failed[0]["state"] == "failed"
    assert failed[0]["cause"] == "install Bear ended with exit code 1: dpkg: error: cannot access archive"


def _index_builds(tmp_path, units, workspace=None, toolchains=(), files=None, report=INDEXED):
    """`index()` over `units` of a project holding `files`, with the container faked and nothing downloaded."""
    project = tmp_path / "project"
    for rel in files or ():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text("", encoding="utf-8")
    run, seen = _fake_run(tmp_path, report)
    with mock.patch.object(container, "run_in_container", run), \
            mock.patch.object(clang, "tools", lambda builds=(): {**TOOLS, "builds": sorted(builds)}), \
            mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)), \
            mock.patch.object(container, "architecture", return_value="x64"):
        result = clang.index(project, tmp_path / "work", units=units, workspace=workspace, toolchains=toolchains)
    return result, seen


def test_each_build_tool_gives_its_units_a_build():
    """Meson configures from the top folder of its meson.build files, Make runs per folder with the targets the
    pre-map states there, Bazel from its workspace's root, Go per module with the packages whose C files cgo
    compiles: each once."""
    units = [{"name": "imgconv", "kind": "meson-target", "root": "."},
             {"name": "img", "kind": "meson-target", "root": "libimg"},
             {"name": "build/mini", "kind": "make-target", "root": "c"},
             {"name": "build/libmini.a", "kind": "make-target", "root": "c"},
             {"name": "//lib:greet", "kind": "bazel-target", "root": "bz/lib"},
             {"name": "//app:app", "kind": "bazel-target", "root": "bz/app"},
             {"name": "example.com/fastsum", "kind": "go-module", "root": "g", "registries": ["https://proxy.golang.org"],
              "config": {"cgo": [{"package": "example.com/fastsum/sum", "c_files": ["g/sum/fastsum.c"]},
                                 {"package": "example.com/fastsum/inline", "c_files": []}]}},
             {"name": "example.com/pure", "kind": "go-module", "root": "p"}]
    workspace = [{"tool": "bazel", "root": "bz", "members": ["bz/app", "bz/lib"]}]
    tops = {"libimg": "."}
    assert clang.builds(units, workspace, lambda root: tops.get(root, root)) == [
        {"root": ".", "build": "meson"}, {"root": "c", "build": "make", "targets": ["build/mini", "build/libmini.a"]},
        {"root": "bz", "build": "bazel"},
        {"root": "g", "build": "go", "packages": ["example.com/fastsum/sum"], "download": True}]


def test_meson_configures_from_the_top_folder_holding_a_meson_build(tmp_path):
    """Meson reads a subdir's meson.build only from the project's: the outermost folder holding one, from the
    checkout's root down to the unit's."""
    for rel in ("meson.build", "libimg/meson.build", "libimg/x/meson.build", "other/y/meson.build"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("", encoding="utf-8")
    assert clang.meson_top(tmp_path, "libimg/x") == "."
    (tmp_path / "meson.build").unlink()
    assert (clang.meson_top(tmp_path, "libimg/x"), clang.meson_top(tmp_path, "other/y")) == ("libimg", "other/y")


def test_the_stage_is_handed_the_go_modules_whose_c_files_cgo_compiles():
    cgo = {"name": "m", "kind": "go-module", "root": ".", "config": {"cgo": [{"package": "m/sum", "c_files": ["s.c"]}]}}
    record = {"units": [cgo, {"name": "pure", "kind": "go-module", "root": "p"},
                        {"name": "inline", "kind": "go-module", "root": "i",
                         "config": {"cgo": [{"package": "i", "c_files": []}]}},
                        {"name": "py", "kind": "python-project", "root": "."}],
              "workspace": [], "toolchains": [{"tool": "bazel", "version": "7.4.1"}, {"tool": "go", "version": "1.22"},
                                              {"tool": "node", "version": "22"}]}
    given = clang.structure(record)
    assert given["units"] == [cgo] and [item["tool"] for item in given["toolchains"]] == ["bazel", "go"]
    assert "go-module" in clang.UNIT_KINDS


BAZEL_UNITS = [{"name": "//lib:greet", "kind": "bazel-target", "root": "lib"}]
BAZEL_WORKSPACE = [{"tool": "bazel", "root": ".", "members": ["lib"]}]


def test_bazel_runs_its_aquery_in_the_preparation_with_bazels_hosts(tmp_path):
    """Bazel's network needs, the module graph and the rules its analysis loads, are met in the preparation, with
    the registries and Bazel's hosts open; with the memory its server needs. A version the project states
    (`.bazelversion`) is installed by mise; else the pin runs."""
    stated = [{"tool": "bazel", "version": "7.4.1", "declared_in": ".bazelversion"}]
    result, seen = _index_builds(tmp_path, BAZEL_UNITS, BAZEL_WORKSPACE, stated)
    script = seen["prepare"][-1]
    assert "install bazel@7.4.1" in script
    assert script.rstrip().endswith(f"python3 {clang.TOOLS}/clang_run.py prepare {clang.TOOLS}/units.json || true")
    assert {"bcr.bazel.build", "mirror.bazel.build", *container.REGISTRIES} <= set(seen["registries"])
    assert seen["memory"] >= 3 * 2**30 and seen["inputs"]["builds"] == ["bazel"]
    assert _plan(seen) == [{"root": ".", "build": "bazel"}] and result["indexes"]
    pinned, seen = _index_builds(tmp_path / "pin", BAZEL_UNITS, BAZEL_WORKSPACE)
    assert "mise" not in seen["prepare"][-1] and "clang_run.py prepare" in seen["prepare"][-1]


def test_cgo_downloads_its_modules_in_the_preparation_only_when_it_requires_some(tmp_path):
    cgo = {"name": "m", "kind": "go-module", "root": ".", "registries": ["https://proxy.golang.org"],
           "config": {"cgo": [{"package": "m/sum", "c_files": ["sum/f.c"]}]}}
    _result, seen = _index_builds(tmp_path, [cgo])
    assert "clang_run.py prepare" in seen["prepare"][-1] and set(container.REGISTRIES) <= set(seen["registries"])
    assert _plan(seen) == [{"root": ".", "build": "go", "packages": ["m/sum"], "download": True}]
    alone = {key: value for key, value in cgo.items() if key != "registries"}
    _result, seen = _index_builds(tmp_path / "alone", [alone])
    assert "prepare" not in seen and seen["inputs"]["builds"] == ["go"]
    # A Go the project states above the pin is installed by mise; one the pin meets is not.
    _result, seen = _index_builds(tmp_path / "newer", [alone], toolchains=[{"tool": "go", "version": "1.99.0"}])
    assert "install go@1.99.0" in seen["prepare"][-1]
    _result, seen = _index_builds(tmp_path / "older", [alone], toolchains=[{"tool": "go", "version": "1.22"}])
    assert "prepare" not in seen


def test_meson_and_make_need_no_preparation(tmp_path):
    units = [{"name": "x", "kind": "meson-target", "root": "sub"}, {"name": "app", "kind": "make-target", "root": "c"}]
    _result, seen = _index_builds(tmp_path, units, files=["meson.build", "sub/meson.build"])
    assert "prepare" not in seen and seen["inputs"]["builds"] == ["make", "meson"]
    assert _plan(seen) == [{"root": ".", "build": "meson"}, {"root": "c", "build": "make", "targets": ["app"]}]


def test_each_build_carries_the_tools_it_runs(tmp_path):
    """Bear for Make and cgo: Ubuntu 24.04's own packages, the image's distribution, installed with dpkg from the
    copy; Meson and its Ninja; Go's and Bazel's pins, which the preparation replaces with a version the project
    states. Each downloaded once and checked by sha256."""
    with mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)), \
            mock.patch("resolve_edges.shared_engine_dir", lambda name: tmp_path / name), \
            mock.patch("resolve_edges.download", lambda url, target, *, sha256=None: target), \
            mock.patch.object(clang, "_sha256", lambda path: ""):
        carried = clang.tools({"meson", "make", "bazel", "go"})
        cmake_only = clang.tools()
    names = {path.removeprefix(f"{clang.TOOLS}/") for path in carried}
    assert {"meson.whl", "ninja.whl", "bazel", "go.tar.gz", "scip-clang", "clang_run.py"} <= names
    assert sorted(name for name in names if name.startswith("bear/")) == sorted(
        f"bear/{posixpath.basename(url)}" for url, _digest in clang.BEAR)
    assert all(url.startswith("https://archive.ubuntu.com/ubuntu/pool/") and len(digest) == 64
               for url, digest in clang.BEAR)
    assert not any(name.startswith("bear/") or name.endswith(".whl") for name in cmake_only)


# ---------------------------------------------------------------------------------------------------------------
# A real container, only on request: the provider path on a real run.

SMOKE = os.environ.get("DAODAN_CLANG_SMOKE") == "1"


@pytest.mark.skipif(not SMOKE, reason="set DAODAN_CLANG_SMOKE=1 to index the fixture in a real container")
def test_smoke_cmake_records_fmt_from_github_and_the_unit_is_unavailable(tmp_path):
    """fmt comes from github.com, outside the allowed registries: never downloaded. CMake's provider records it,
    the configure fails on the missing target, the unit is not indexed."""
    unit = {"name": "fetchfixture", "kind": "cmake-target", "root": ".", "manifest": "CMakeLists.txt"}
    result = clang.index(HERE / "fixtures/clang-index/fetch", tmp_path / "work", units=[unit])
    assert result["state"] == "unavailable", result
    state = result["units"][0]
    assert state["kind"] == "download-outside-registries" and state["fetched"] == [FMT]
    assert "CMake Error" in state["error"] and "github.com" in result["reason"]


def _occurrences(root: Path, indexes) -> dict:
    """Every occurrence of every document. A symbol of a system package is named with the version of the package
    the image carries (`libc6-dev 2.39-0ubuntu8.9`): that version is the image's, not the project's, and is left
    out of the comparison."""
    index = code_graph.Index(root)
    for path, prefix in indexes:
        index.load(Path(path), prefix)
    system = re.compile(r"^(cxx \. (?!project )\S+) \S+\$ ")
    return {rel: sorted((o.line, o.start, o.end_line, o.end, system.sub(lambda m: m.group(1) + " $ ", o.key),
                         o.definition) for o in found) for rel, found in index.documents.items()}


@pytest.mark.skipif(not SMOKE, reason="set DAODAN_CLANG_SMOKE=1 to index the fixtures in a real container")
@pytest.mark.parametrize("language", ["c", "cpp"])
def test_smoke_a_unit_that_configures_is_indexed_and_its_index_comes_back(tmp_path, language):
    """The whole path on a real engine, from the pre-map's units: CMake configures, scip-clang runs with the
    jobs it is given, the index returns through the writer, and it says what the fixture's stored index says."""
    fixture = HERE / "fixtures/code-graph" / language
    project = tmp_path / "project"
    shutil.copytree(fixture, project, ignore=shutil.ignore_patterns("index.scip", "expected.json"))
    import premap
    import snapshot
    manifest = tmp_path / "snapshot" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    given = clang.structure(premap.ensure(manifest))  # the units the stage hands the indexer
    assert {unit["kind"] for unit in given["units"]} == {"cmake-target"}
    result = clang.index(project, tmp_path / "work", cpus=2, **given)
    assert "state" not in result, result
    assert [u["state"] for u in result["units"]] == ["indexed"], result["units"]
    assert _occurrences(project, result["indexes"]) == _occurrences(fixture, [(fixture / "index.scip", "")])
