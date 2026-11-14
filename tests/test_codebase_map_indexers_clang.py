"""The C and C++ indexer's run: the units the pre-map gives, the container run with no network, the state of a
unit whose configure needs a download outside the allowed registries, and the contract built from what comes back.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_clang.py

Every test fakes the container except the smoke test at the end, which indexes `fixtures/clang-index/fetch` in a
real one and only with DAODAN_CLANG_SMOKE=1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path, PurePosixPath
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
from indexers import clang, clang_run  # noqa: E402

FMT = {"name": "fmt", "url": "https://github.com/fmtlib/fmt.git"}
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


def test_the_configure_never_downloads_and_points_each_fetched_dependency_at_an_empty_directory(tmp_path):
    unit = {"root": "lib", "configure": ["-DWITH_TESTS=OFF"], "fetched": [FMT]}
    command = clang_run.configure_command("cmake", unit, tmp_path / "build", tmp_path / "empty")
    assert command[:5] == ["cmake", "-S", str(clang_run.WORK / "lib"), "-B", str(tmp_path / "build")]
    assert "-DFETCHCONTENT_FULLY_DISCONNECTED=ON" in command and "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON" in command
    assert f"-DFETCHCONTENT_SOURCE_DIR_FMT={tmp_path / 'empty' / 'fmt'}" in command
    assert command[-1] == "-DWITH_TESTS=OFF"


def _runner(code, output):
    calls = []

    def run(command, cwd, timeout=3600):
        calls.append(command)
        return code, output, 1.0
    return run, calls


def test_a_unit_that_needs_an_undownloaded_dependency_is_unavailable_with_cmakes_error(tmp_path):
    run, calls = _runner(1, LINK_ERROR)
    steps, state = clang_run.configure(run, "cmake", {"root": ".", "fetched": [FMT]}, tmp_path / "b", tmp_path / "e")
    assert len(calls) == 1 and [step["step"] for step in steps] == ["configure"]
    assert state == {"state": "unavailable", "kind": "download-outside-registries", "urls": [FMT["url"]],
                     "cause": "the configure needs what the unit downloads from github.com, outside the allowed "
                              "registries: CMake Error at CMakeLists.txt:8 (target_link_libraries): "
                              "Target \"app\" links to:"}
    assert (tmp_path / "e" / "fmt" / "CMakeLists.txt").read_text(encoding="utf-8") == \
        f"# Not downloaded by Daodan: {FMT['url']}\n"


def test_a_unit_that_fetches_nothing_and_cannot_configure_failed(tmp_path):
    run, _calls = _runner(1, LINK_ERROR)
    _steps, state = clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b", tmp_path / "e")
    assert state == {"state": "failed", "cause": "the configure failed: CMake Error at CMakeLists.txt:8 "
                                                 "(target_link_libraries): Target \"app\" links to:"}
    run, _calls = _runner(None, "")
    _steps, state = clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b", tmp_path / "e")
    assert state == {"state": "failed", "cause": "the configure failed: timed out"}
    run, _calls = _runner(0, "-- Generating done\n")
    assert clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b", tmp_path / "e")[1] == {"state": "configured"}


def test_the_compilation_database_counts_the_commands_of_each_file(tmp_path):
    work = PurePosixPath(str(clang_run.WORK))
    compdb = tmp_path / "compile_commands.json"
    compdb.write_text(json.dumps([{"directory": str(work / "build"), "file": "../util.c"},
                                  {"directory": str(work), "file": "util.c"},
                                  {"directory": str(work), "file": "main.c"}]), encoding="utf-8")
    assert clang_run.compiled(compdb) == {"main.c": 1, "util.c": 2}


# ---------------------------------------------------------------------------------------------------------------
# On the host: index()


UNIT = {"root": ".", "build": "cmake", "configure": [], "generated": [], "fetched": [FMT]}


def test_without_a_cmake_unit_the_index_is_unavailable(tmp_path):
    result = clang.index(tmp_path, tmp_path / "work", units=[])
    assert result["state"] == "unavailable" and result["reason"].startswith("no C or C++ unit built with CMake")
    meson = clang.index(tmp_path, tmp_path / "work", units=[{"root": ".", "build": "meson"}])
    assert meson["state"] == "unavailable" and "built with meson" in meson["reason"]


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
UNAVAILABLE = {"root": "vendor", "state": "unavailable", "kind": "download-outside-registries", "urls": [FMT["url"]],
               "cause": "the configure needs what the unit downloads from github.com, outside the allowed registries: "
                        "CMake Error at CMakeLists.txt:8 (target_link_libraries): Target \"app\" links to:",
               "steps": [{"step": "configure", "returncode": 1, "seconds": 2.0, "tail": LINK_ERROR}],
               "compiled": {}, "index": None}


def _index(tmp_path, report, units, state="done", **extra):
    run, seen = _fake_run(tmp_path, report, state, **extra)
    with mock.patch.object(container, "run_in_container", run), mock.patch.object(clang, "tools", return_value=TOOLS), \
            mock.patch.object(container, "architecture", return_value="x64"):
        return clang.index(tmp_path / "project", tmp_path / "work", units=units), seen


def test_one_run_with_no_network_indexes_the_units_that_configure_and_states_the_others(tmp_path):
    report = {"peak_mb": 210, "units": [
        {"root": ".", "state": "indexed", "index": "index-0.scip", "compiled": {"main.c": 1, "util.c": 2},
         "steps": [{"step": "configure", "returncode": 0, "seconds": 2.0, "tail": ""},
                   {"step": "index", "returncode": 0, "seconds": 4.0, "tail": "", "diagnostics": {"errors": 0}}]},
        UNAVAILABLE]}
    units = [{"root": ".", "build": "cmake"}, {**UNIT, "root": "vendor"}, {"root": "m", "build": "meson"}]
    result, seen = _index(tmp_path, report, units)
    assert seen["image"] == clang.IMAGE and seen["outputs"] == [clang.OUT] and "prepare" not in seen
    assert seen["command"] == ["python3", f"{clang.TOOLS}/clang_run.py", f"{clang.TOOLS}/units.json", clang.OUT]
    assert set(seen["inputs"]) == set(TOOLS) | {f"{clang.TOOLS}/units.json"}
    assert json.loads(seen["inputs"][f"{clang.TOOLS}/units.json"].read_text(encoding="utf-8")) == \
        [{"root": ".", "configure": [], "generated": [], "fetched": []},
         {"root": "vendor", "configure": [], "generated": [], "fetched": [FMT]}]
    assert result["indexes"] == [[str((tmp_path / "work" / "index-0.scip").resolve()), ""]]
    assert [(unit["root"], unit["state"], unit.get("kind")) for unit in result["units"]] == \
        [("m", "unavailable", "not-cmake"), (".", "indexed", None), ("vendor", "unavailable", "download-outside-registries")]
    assert result["configs"]["compiled"] == {"main.c": 1, "util.c": 2}
    assert [run["step"] for run in result["runs"]] == ["configure", "index", "configure"]
    assert result["indexer"] == {"name": "scip-clang", "version": clang.VERSION, "seconds": 8.0, "peak_mb": 210}
    # A file of a unit left unindexed says why it has no document.
    reasons = clang.missing(None, ["vendor/app.cpp", "m/x.c", "orphan.c"], clang.tasks(result["configs"]))
    assert reasons["vendor/app.cpp"] == f"the index of unit vendor is unavailable: {UNAVAILABLE['cause']}"
    assert reasons["m/x.c"].startswith("the index of unit m is unavailable: built with meson")
    assert reasons["orphan.c"] == "no compile command: not built by the default configuration"


def test_without_an_index_the_result_is_unavailable_when_no_unit_failed(tmp_path):
    result, _seen = _index(tmp_path, {"peak_mb": None, "units": [{**UNAVAILABLE, "root": "."}]}, [UNIT])
    assert result["state"] == "unavailable" and result["reason"] == f".: {UNAVAILABLE['cause']}"
    assert result["units"][0]["kind"] == "download-outside-registries" and result["indexes"] == []


def test_a_container_gap_is_unavailable_and_a_run_without_report_failed(tmp_path):
    gap, _seen = _index(tmp_path, None, [UNIT], "gap", cause="no engine", remedy="install WSL")
    assert (gap["state"], gap["reason"], gap["install"]) == ("unavailable", "no engine", "install WSL")
    failed, _seen = _index(tmp_path / "again", None, [UNIT], "timeout")
    assert failed["state"] == "failed" and "timeout" in failed["reason"]


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
# A real container, only on request.

SMOKE = os.environ.get("DAODAN_CLANG_SMOKE") == "1"


@pytest.mark.skipif(not SMOKE, reason="set DAODAN_CLANG_SMOKE=1 to index the fixture in a real container")
def test_smoke_a_unit_that_fetches_fmt_from_github_is_unavailable_with_cmakes_error(tmp_path):
    """fmt comes from github.com, outside the allowed registries: never downloaded, the unit is not indexed."""
    unit = {"root": ".", "build": "cmake", "configure": [], "generated": [],
            "fetched": [{"name": "fmt", "url": "https://github.com/fmtlib/fmt.git"}]}
    result = clang.index(HERE / "fixtures/clang-index/fetch", tmp_path / "work", units=[unit])
    assert result["state"] == "unavailable", result
    assert result["units"][0]["kind"] == "download-outside-registries"
    assert "github.com" in result["reason"] and "CMake Error" in result["reason"]
