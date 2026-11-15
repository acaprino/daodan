"""The C and C++ indexer's run: the units the pre-map gives, the container run with no network, CMake's own
record of what a unit asks FetchContent for, and the contract built from what comes back.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_clang.py

Every test fakes the container except the smoke test at the end, which indexes `fixtures/clang-index/fetch` in a
real one and only with DAODAN_CLANG_SMOKE=1.
"""
from __future__ import annotations

import json
import os
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


def test_without_a_cmake_unit_the_index_is_unavailable(tmp_path):
    result = clang.index(tmp_path, tmp_path / "work", units=[{"name": "web", "kind": "npm-package", "root": "web"}])
    assert result["state"] == "unavailable" and result["reason"].startswith("no C or C++ unit built with CMake")
    meson = clang.index(tmp_path, tmp_path / "work", units=[{"name": "m", "kind": "meson-target", "root": "."}])
    assert meson["state"] == "unavailable" and "built with meson" in meson["reason"]


MSBUILD = "built with MSBuild: Daodan configures C and C++ units with CMake only"


def test_an_msbuild_project_is_stated_like_every_build_cmake_does_not_configure(tmp_path):
    """Several project files share a folder: the folder is stated once."""
    app = {"name": "app", "kind": "msbuild-project", "root": "win"}
    alone = clang.index(tmp_path, tmp_path / "work", units=[app, {**app, "name": "lib"}])
    assert alone["state"] == "unavailable"
    assert alone["reason"] == f"no C or C++ unit built with CMake in the pre-map; {MSBUILD}"
    roots, states = clang.configure_roots([UNIT, app, {**app, "name": "lib"}], None)
    assert roots == ["."]
    assert states == [{"root": "win", "state": "unavailable", "kind": "not-cmake", "cause": MSBUILD}]
    assert "msbuild-project" in clang.UNIT_KINDS


def test_a_file_without_a_document_names_its_own_cause():
    win = {"root": "win", "state": "unavailable", "kind": "not-cmake", "cause": MSBUILD}
    configs = {"compiled": {"lib/a.c": 1}, "units": [win, {"root": "lib", "state": "indexed"}]}
    reasons = clang.missing(None, ["win/main.cpp", "tools/gen.c", "tools/gen.h", "lib/a.c", "lib/unused.c"], configs)
    assert reasons == {"win/main.cpp": f"the index of unit win is unavailable: {MSBUILD}",
                       "tools/gen.c": "in no CMake unit of the pre-map",
                       "tools/gen.h": "header no indexed translation unit includes in an active branch",
                       "lib/a.c": "compiled, yet no document in the index",
                       "lib/unused.c": "no compile command: not built by the default configuration"}
    # Another build's file beside the CMakeLists.txt CMake indexed does not speak for the folder.
    both = {"units": [{**win, "root": "."}, {"root": ".", "state": "indexed"}]}
    assert clang.missing(None, ["a.c"], both) == {"a.c": "no compile command: not built by the default configuration"}


def test_a_workspace_is_configured_once_at_its_root():
    """Members of a CMake workspace (`add_subdirectory`) are configured from the workspace's root; a unit in no
    workspace from its own; units of other build tools and languages are left to their indexers."""
    units = [UNIT, {**UNIT, "name": "lib", "root": "lib"}, {**UNIT, "name": "cli", "root": "apps/cli"},
             {**UNIT, "name": "gen", "root": "tools/gen"}, {"name": "web", "kind": "npm-package", "root": "web"},
             {"name": "m", "kind": "meson-target", "root": "m"}]
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
    units = [UNIT, {**UNIT, "name": "vendor", "root": "vendor"}, {"name": "m", "kind": "meson-target", "root": "m"}]
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
        [("m", "unavailable", "not-cmake"), (".", "indexed", None),
         ("vendor", "unavailable", "download-outside-registries")]
    assert result["configs"]["compiled"] == {"main.c": 1, "util.c": 2}
    assert [run["step"] for run in result["runs"]] == ["configure", "index", "configure"]
    assert result["indexer"] == {"name": "scip-clang", "version": clang.VERSION, "seconds": 8.0, "peak_mb": 210}
    # A file of a unit left unindexed says why it has no document.
    reasons = clang.missing(None, ["vendor/app.cpp", "m/x.c", "orphan.c"], clang.tasks(result["configs"]))
    assert reasons["vendor/app.cpp"] == f"the index of unit vendor is unavailable: {UNAVAILABLE['cause']}"
    assert reasons["m/x.c"].startswith("the index of unit m is unavailable: built with meson")
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


def _index_stated(tmp_path, toolchains, prepared: str = ""):
    """`index()` with the pre-map's `toolchains` and a container run whose preparation printed `prepared`."""
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
        result = clang.index(tmp_path / "project", tmp_path / "work", units=[UNIT], toolchains=toolchains)
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
