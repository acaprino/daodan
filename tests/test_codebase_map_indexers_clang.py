"""The C and C++ indexer's run: the units the pre-map gives, the container run with no network, CMake's own
record of what a unit asks FetchContent for, and the contract built from what comes back.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_clang.py

Every test fakes the container except the smoke test at the end, which indexes `fixtures/clang-index/fetch` in a
real one and only with DAODAN_CLANG_SMOKE=1.
"""
from __future__ import annotations

import io
import json
import os
import posixpath
import re
import shlex
import shutil
import sys
import tarfile
from pathlib import Path, PurePosixPath
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import code_graph  # noqa: E402
import container  # noqa: E402
import egress  # noqa: E402
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


def test_a_recorded_url_gives_its_host_when_the_proxy_can_open_it():
    """`urllib.parse.urlsplit` reads the host; the proxy opens https at port 443 only. git's scp form, which
    urlsplit reads as no URL, a local path and another scheme or port give none."""
    assert clang_run._host("https://github.com/fmtlib/fmt.git") == "github.com"
    assert clang_run._host("https://user@GitHub.com:443/x/y/archive/v1.tar.gz") == "github.com"
    for url in ("git@github.com:fmtlib/fmt.git", "/srv/mirror/fmt", "file:///srv/fmt", "http://a.example/x.tgz",
                "git://a.example/x.git", "ssh://git@a.example/x.git", "https://a.example:8443/x", "https://[::1/x",
                "https://a.example:port/x"):
        assert clang_run._host(url) is None, url
    fetched = [FMT, {"name": "z", "urls": ["git@github.com:z/z.git", "https://a.example/z.tgz"]}]
    assert clang_run.hosts(fetched) == (["a.example", "github.com"], ["git@github.com:z/z.git"])


def test_the_configure_that_downloads_has_fetchcontent_download_into_a_folder_of_its_own(tmp_path):
    command = clang_run.configure_command("cmake", {"root": "."}, tmp_path / "b", tmp_path / "f.log", tmp_path / "d")
    assert f"-DFETCHCONTENT_BASE_DIR={tmp_path / 'd'}" in command
    assert not any("FULLY_DISCONNECTED" in word for word in command)
    assert f"-DDAODAN_FETCH_LOG={tmp_path / 'f.log'}" in command  # the provider still records
    run, calls = _runner(1, LINK_ERROR, RECORD)
    steps, state = clang_run.configure(run, "cmake", {"root": "."}, tmp_path / "b", tmp_path / "f.log", tmp_path / "d")
    assert len(calls) == len(steps) == 1  # one configure: no second attempt
    assert state == {"state": "failed", "fetched": [FMT], "error": LINK_ERROR,
                     "cause": "the configure ended with exit code 1, FetchContent downloading from github.com "
                              "through the proxy"}


def test_the_preparation_configures_a_fetch_unit_and_the_execution_keeps_the_projects_commands(tmp_path):
    """A unit whose hosts the user allows is configured in the preparation, through the proxy, FetchContent
    downloading into its own folder; the execution takes that database, without the dependencies' commands."""
    prepared, scratch, tools, work = tmp_path / "prepared", tmp_path / "scratch", _tools(tmp_path / "tools"), \
        tmp_path / "work"
    deps = prepared / "0" / "deps"
    database = [{"directory": str(work), "file": str(work / "main.cpp"), "arguments": ["c++", "-c", "main.cpp"]},
                {"directory": str(deps), "file": str(deps / "fmt-src/src/format.cc"), "arguments": ["c++", "-c"]}]
    plan = tmp_path / "units.json"
    plan.write_text(json.dumps([{"root": ".", "fetch": True}]), encoding="utf-8")
    run, calls = _tool(0, "-- Generating done\n",
                       {prepared / "0/build/compile_commands.json": json.dumps(database)})
    with mock.patch.multiple(clang_run, PREPARED=prepared, SCRATCH=scratch, TOOLS=tools, run=run):
        assert clang_run.main(["clang_run.py", "prepare", str(plan), "/t/cmake"]) == 0
    configures = [command for command, _cwd in calls if "-S" in command]
    assert len(configures) == 1 and f"-DFETCHCONTENT_BASE_DIR={deps}" in configures[0]
    assert (scratch / "provider.cmake").read_text(encoding="utf-8") == clang_run.PROVIDER
    held = json.loads((prepared / "0/configure.json").read_text(encoding="utf-8"))
    assert held["state"] == {"state": "configured"} and [step["step"] for step in held["steps"]] == ["configure"]
    with mock.patch.multiple(clang_run, PREPARED=prepared, WORK=work):
        steps, state = clang_run.downloaded(0, tmp_path / "b")
        assert clang_run.compiled(tmp_path / "b/compile_commands.json") == {"main.cpp": 1}
        assert (steps, state) == (held["steps"], held["state"])
        assert clang_run.downloaded(1, tmp_path / "b1")[1] == {
            "state": "failed", "cause": "the preparation recorded no configure: its output is in the run's prepare.log"}


def test_the_compilation_database_counts_the_commands_of_each_file(tmp_path):
    work = PurePosixPath(str(clang_run.WORK))
    compdb = tmp_path / "compile_commands.json"
    compdb.write_text(json.dumps([{"directory": str(work / "build"), "file": "../util.c"},
                                  {"directory": str(work), "file": "util.c"},
                                  {"directory": str(work), "file": "main.c"}]), encoding="utf-8")
    assert clang_run.compiled(compdb) == {"main.c": 1, "util.c": 2}


def _tools(folder: Path) -> Path:
    """The copy's tools folder: scip-clang, and clang's builtin headers as `clang.clang_headers` packs them."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "scip-clang").write_bytes(b"")
    with tarfile.open(folder / f"clang-{clang.CLANG_HEADERS[0]}-headers.tar", "w") as bundle:
        data = b"typedef __SIZE_TYPE__ size_t;\n"
        entry = tarfile.TarInfo("include/stddef.h")
        entry.size = len(data)
        bundle.addfile(entry, io.BytesIO(data))
    return folder


def test_a_gcc_command_reads_the_builtin_headers_of_the_clang_scip_clang_is_built_on(tmp_path):
    """scip-clang gives a command of GCC, as clang's resource folder, GCC's install folder: clang then reads GCC's
    builtin headers, whose intrinsics call builtins clang lacks (3,492 errors from mmintrin.h on, for one C and
    one C++ file using _mm_pause, measured). So each command of a compiler that is not clang drops them
    (`-nobuiltininc`), reads clang's own (`-isystem`), and last the compiler's include folder (`-idirafter`), for
    the headers clang has none of (omp.h, quadmath.h). A clang keeps its own; a command that drops the builtin
    headers itself is left as it is; a `--` ends the options. Each compiler is asked once."""
    gcc_include = tmp_path / "gcc/include"
    gcc_include.mkdir(parents=True)
    headers, compdb, target = tmp_path / "clang/include", tmp_path / "compile_commands.json", tmp_path / "given.json"
    entries = [{"directory": "/w", "file": "a.c", "arguments": ["/usr/bin/gcc", "-O2", "-c", "a.c"]},
               {"directory": "/w/b", "file": "../b.c", "command": 'cc -DX="1 2" -c ../b.c -o b.o'},
               {"directory": "/w", "file": "c.cc", "arguments": ["clang++", "-c", "c.cc"]},
               {"directory": "/w", "file": "k.c", "arguments": ["gcc", "-nostdinc", "-c", "k.c"]},
               {"directory": "/w", "file": "d.c", "arguments": ["/usr/bin/gcc", "-c", "--", "d.c"]},
               {"directory": "/w", "file": "e.c", "arguments": ["gone-gcc", "-c", "e.c"]}]
    compdb.write_text(json.dumps(entries), encoding="utf-8")
    calls = []

    def run(command, cwd, timeout=3600, stdout=None):
        calls.append(command)
        if command[0] == "gone-gcc":
            raise FileNotFoundError(2, "No such file or directory", "gone-gcc")
        if command[1] == "-print-resource-dir":
            return (0, "/usr/lib/llvm-18/lib/clang/18\n", 0.1) if command[0].startswith("clang") else \
                (1, "gcc: error: unrecognized command-line option '-print-resource-dir'\n", 0.1)
        return 0, f"{gcc_include}\n", 0.1
    clang_run.builtin_headers(run, compdb, target, headers)
    extra = ["-nobuiltininc", "-isystem", str(headers), "-idirafter", str(gcc_include)]
    given = json.loads(target.read_text(encoding="utf-8"))
    assert given[0]["arguments"] == ["/usr/bin/gcc", "-O2", "-c", "a.c", *extra]
    assert shlex.split(given[1]["command"]) == ["cc", "-DX=1 2", "-c", "../b.c", "-o", "b.o", *extra]
    assert given[2:4] == entries[2:4]
    assert given[4]["arguments"] == ["/usr/bin/gcc", "-c", *extra, "--", "d.c"]
    assert given[5]["arguments"] == ["gone-gcc", "-c", "e.c", *extra[:3]]
    assert [command[0] for command in calls] == ["/usr/bin/gcc", "/usr/bin/gcc", "cc", "cc", "clang++", "gone-gcc",
                                                 "gone-gcc"]
    assert json.loads(compdb.read_text(encoding="utf-8")) == entries  # the build's own, which `compiled` counts


def test_the_report_is_written_into_the_folder_the_caller_names_under_the_scratch_folder(tmp_path):
    """`index()` names the report's folder under the script's scratch folder (`clang.OUT`): emptying the scratch
    folder at the start leaves that folder for the report."""
    scratch, tools, plan = tmp_path / "scratch", tmp_path / "tools", tmp_path / "units.json"
    out = scratch / PurePosixPath(clang.OUT).relative_to(clang_run.SCRATCH.as_posix()).as_posix()
    _tools(tools)
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
    _tools(tools)
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
                       "lib/unused.c": "no compile command: the build compiles other files of lib, not this one"}
    # Another build's file beside the CMakeLists.txt CMake indexed does not speak for the folder.
    both = {"units": [{**win, "root": "."}, {"root": ".", "state": "indexed"}]}
    assert clang.missing(None, ["a.c"], both) == {"a.c": "no compile command: no build compiles a file of the root"}
    # A build that stopped says so beside what it compiled. mix-real-zlib: contrib/minizip's makefile compiles
    # neither mztools.c nor iowin32.c (only its autotools build does), and contrib/infback9 has no build at all.
    stopped = {"compiled": {"contrib/minizip/zip.c": 1},
               "units": [{"root": "contrib/minizip", "build": "make", "state": "indexed",
                          "cause": "make ended with exit code 2"}, {"root": ".", "state": "indexed"}]}
    assert clang.missing(None, ["contrib/minizip/mztools.c", "contrib/infback9/infback9.c"], stopped) == {
        "contrib/minizip/mztools.c": "no compile command: the build compiles other files of contrib/minizip, not this "
                                     "one; make ended with exit code 2",
        "contrib/infback9/infback9.c": "no compile command: no build compiles a file of contrib/infback9"}


def test_a_file_nothing_failed_for_is_said_so():
    """mix-real-zlib's C++, contrib/iostream*, which no build compiles: a language none of whose files is indexed
    for such reasons only is `unavailable`, not `failed` (`engine_pass.index_stage`). A file a build would compile
    but the build stopped, or whose unit failed, is no such file; one whose only build cannot run here is."""
    win = {"root": "win", "state": "unavailable", "kind": "no-database", "cause": MSBUILD}
    stopped = {"root": "lib", "state": "indexed", "cause": "make ended with exit code 2"}
    configs = {"compiled": {"lib/a.c": 1}, "units": [win, {"root": "gen", "state": "failed", "cause": "boom"},
                                                   stopped, {"root": "ok", "state": "indexed"}]}
    reasons = clang.missing(None, ["win/main.cpp", "tools/x.cc", "ok/x.h", "ok/x.cc", "gen/g.cc", "lib/b.cc",
                                   "lib/a.c"], configs)
    assert {rel: clang.nothing_failed(reason) for rel, reason in reasons.items()} == {
        "win/main.cpp": True, "tools/x.cc": True, "ok/x.h": True, "ok/x.cc": True,
        "gen/g.cc": False, "lib/b.cc": False, "lib/a.c": False}


# ---------------------------------------------------------------------------------------------------------------
# What the reader reads from tree-sitter's tokens


DIRECTIVES_C = ("int f(int n) {\n"
                "  return g(n,\n"
                "#  if WIDE\n"
                "    h(n)\n"
                "#else\n"
                "    0\n"
                "#endif\n"
                "  );\n"
                "}\n"
                "/*\n"
                "#if NOT_A_DIRECTIVE\n"
                "*/\n"
                "#endif\n")


def test_the_directives_are_the_grammars_tokens_inside_an_expression_and_never_in_a_comment(tmp_path):
    """gzlib.c's `#ifdef WIDECHAR` inside an expression: the grammar reads it in an ERROR node, with its `#else` and
    `#endif`; an `#endif` with no `#if` open is a `preproc_directive` that names it; a line of a comment that reads
    like a directive is no directive (a pattern on the line's text took it for one)."""
    (tmp_path / "run.c").write_text(DIRECTIVES_C, encoding="utf-8")
    index = code_graph.Index(tmp_path)
    directives = clang._directives(index, "run.c")
    assert directives == {3: "#if", 5: "#else", 7: "#endif", 13: "#endif"}
    assert clang._branch(directives, 4) == (3, 3, 5)
    assert clang._branch(directives, 6) == (5, 3, 7)
    assert clang._branch(directives, 12) is None


ARGUMENTS_C = ("#define CHECK(x, m) (x)\n"
               "int run(int n) { CHECK(n > twice(n) /* skip */, \"no name\"); return n; }\n"
               "int two(int n) {\n"
               "    return CHECK(n,\n"
               "        twice(n));\n"
               "}\n")


def test_a_macros_arguments_are_the_names_among_the_tokens_of_its_parentheses(tmp_path):
    """The names a macro's arguments write, across lines; none in a comment or a string; none without parentheses
    right after the name."""
    (tmp_path / "run.c").write_text(ARGUMENTS_C, encoding="utf-8")
    index = code_graph.Index(tmp_path)
    assert clang._arguments(index, "run.c", 2, 22) == [(2, 23, b"n"), (2, 27, b"twice"), (2, 33, b"n")]
    assert clang._arguments(index, "run.c", 4, 16) == [(4, 17, b"n"), (5, 8, b"twice"), (5, 14, b"n")]
    assert clang._arguments(index, "run.c", 2, 13) == []  # `n)`: no list after the name


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


PUBLIC = [(0, 0, 0, "", ("140.82.121.4", 0))]  # what a lookup of a host that asks answers in these tests


def _index(tmp_path, report, units, workspace=None, state="done", cpus=1, **extra):
    run, seen = _fake_run(tmp_path, report, state, **extra)
    with mock.patch.object(container, "run_in_container", run), mock.patch.object(clang, "tools", return_value=TOOLS), \
            mock.patch.object(container, "architecture", return_value="x64"), \
            mock.patch.object(egress.socket, "getaddrinfo", lambda *_, **__: PUBLIC):
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
    assert reasons["orphan.c"] == "no compile command: the build compiles other files of the root, not this one"


def test_what_the_copy_of_the_project_left_out_is_a_gap_of_the_index(tmp_path):
    """A link Git tracks to outside the project stays out of the copy (`container.copy_perimeter`), and the
    container's result says so."""
    left = {"kind": "link_outside", "path": "x.c", "target": "../y.c", "detail": "x.c links outside"}
    report = {"peak_mb": 1, "units": [{"root": ".", "state": "indexed", "index": "index-0.scip", "compiled": {},
                                       "steps": []}]}
    result, _seen = _index(tmp_path, report, [UNIT], gaps=[left])
    assert left in result.get("gaps", [])


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


def _index_again(tmp_path, reports: list):
    """`index()` of `UNIT` with each container run bringing back the next of `reports` (None: a run that timed
    out); what each run was asked. Names resolve to a public address, with no lookup."""
    runs, seen = list(reports), []

    def run(project, command, **options):
        report = runs.pop(0)
        fake, asked = _fake_run(tmp_path, report, "done" if report else "timeout")
        seen.append(asked)
        return fake(project, command, **options)

    with mock.patch.object(container, "run_in_container", run), mock.patch.object(clang, "tools", return_value=TOOLS), \
            mock.patch.object(container, "architecture", return_value="x64"), \
            mock.patch.object(egress.socket, "getaddrinfo", lambda *_, **__: PUBLIC):
        return clang.index(tmp_path / "project", tmp_path / "work", units=[UNIT]), seen


FETCHING = {"peak_mb": 1, "units": [{**UNAVAILABLE, "root": "."}]}


def test_the_hosts_fetchcontent_needs_ask_and_the_configure_downloads_after_the_yes(tmp_path):
    """github.com is not canonical: it asks, as every host does (`egress.preflight`), and the unit stays unavailable
    after one run. After the user's yes the next analysis configures it again, in a second run's preparation open
    to that host only, and indexes it."""
    project = str((tmp_path / "project").resolve())
    result, seen = _index_again(tmp_path, [FETCHING])
    assert len(seen) == 1 and result["units"][0]["kind"] == "download-outside-registries"
    gap, = [gap for gap in result["gaps"] if gap["kind"] == "approval_required"]
    assert gap["hosts"] == ["github.com"] and gap["detail"].startswith("the step ran without hosts")
    assert [row["host"] for row in egress.pending(project)] == ["github.com"]
    egress.reply(project, ["github.com"], "once")  # the user's answer, in the app
    again = {"peak_mb": 2, "units": [{"root": ".", "build": "cmake", "state": "indexed", "index": "index-0.scip",
                                      "compiled": {"main.cpp": 1},
                                      "steps": [{"step": "configure", "returncode": 0, "seconds": 9.0, "tail": ""}]}]}
    result, seen = _index_again(tmp_path, [FETCHING, again])
    assert len(seen) == 2 and "prepare" not in seen[0]
    assert json.loads(seen[1]["inputs"][f"{clang.TOOLS}/units.json"].read_text(encoding="utf-8")) == \
        [{"root": ".", "fetch": True}]
    assert seen[1]["prepare"][-1].rstrip().endswith(
        f"python3 {clang.TOOLS}/clang_run.py prepare {clang.TOOLS}/units.json || true")
    assert seen[1]["registries"] == ("github.com",)
    assert "gaps" not in result and "state" not in result
    assert [(unit["root"], unit["state"]) for unit in result["units"]] == [(".", "indexed")]
    assert result["indexes"] == [[str((tmp_path / "work/fetch/index-0.scip").resolve()), ""]]
    assert result["configs"]["compiled"] == {"main.cpp": 1}
    assert [run["step"] for run in result["runs"]] == ["configure", "configure"]


def test_a_refused_host_is_denied_and_a_url_the_proxy_cannot_open_stays_the_cause(tmp_path, monkeypatch):
    project = str((tmp_path / "project").resolve())
    monkeypatch.setattr(egress, "project_file_of", lambda name: tmp_path / "project.daodan")  # the project's lists
    egress.respond("github.com", project, "block")
    result, seen = _index_again(tmp_path, [FETCHING])
    assert len(seen) == 1 and not egress.pending(project)
    assert [(gap["kind"], gap["host"]) for gap in result["gaps"]] == [("host_denied", "github.com")]
    scp = {"name": "fmt", "urls": ["git@github.com:fmtlib/fmt.git"]}
    result, seen = _index_again(tmp_path, [{"peak_mb": 1, "units": [{**UNAVAILABLE, "root": ".", "fetched": [scp]}]}])
    assert len(seen) == 1 and "gaps" not in result and not egress.pending(project)
    assert result["units"][0]["cause"].endswith(
        "; the proxy opens none of git@github.com:fmtlib/fmt.git: it opens https URLs at port 443 only, and git's "
        "scp form (user@host:path) names no URL")


def test_a_second_run_that_brings_back_no_unit_leaves_it_with_that_runs_cause(tmp_path, monkeypatch):
    monkeypatch.setattr(egress, "project_file_of", lambda name: tmp_path / "project.daodan")  # the project's lists
    egress.respond("github.com", str((tmp_path / "project").resolve()), "always")
    result, seen = _index_again(tmp_path, [FETCHING, None])
    assert len(seen) == 2 and result["state"] == "unavailable" and result["units"][0]["state"] == "unavailable"
    assert result["units"][0]["cause"].endswith("; the configure with its downloads gave no state: scip-clang wrote "
                                                "no index (the container run ended timeout)")


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


def test_the_preparation_reaches_the_hosts_the_project_declares(tmp_path):
    _result, seen = _index_stated(tmp_path, STATED, declared={"hosts": ("conan.corp.example",), "where": {}})
    assert "conan.corp.example" in seen["registries"]


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
            mock.patch.object(clang, "CMAKE", (clang.CMAKE[0], clang.CMAKE[1], digest)), \
            mock.patch.object(clang, "clang_headers", lambda: Path("headers.tar")):
        first = clang.tools()
        second = clang.tools()
        (tmp_path / "scip-clang" / clang.VERSION / "scip-clang-x86_64-linux").write_bytes(b"tampered")
        third = clang.tools()
    assert first == second == third and len(calls) == 3  # two first downloads, one for the tampered binary
    assert first[f"{clang.TOOLS}/clang_run.py"] == Path(clang.__file__).with_name("clang_run.py")
    assert first[f"{clang.TOOLS}/clang-{clang.CLANG_HEADERS[0]}-headers.tar"] == Path("headers.tar")

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


def test_a_makefile_a_configure_script_writes_is_made_once_the_configure_ran(tmp_path):
    """mix-real-zlib's root: its own `configure`, no Autotools', writes Makefile from Makefile.in, as the pre-map
    ran it (`premap.make`): the configure first, with its defaults, in the unit's folder; one that fails says so."""
    units = [{"name": "libz.a", "kind": "make-target", "root": ".", "config": {"configure": "configure"}},
             {"name": "infcover", "kind": "make-target", "root": ".", "config": {"configure": "configure"}}]
    assert clang.builds(units, [], lambda root: root) == [
        {"root": ".", "build": "make", "targets": ["libz.a", "infcover"], "configure": True}]
    build, unit = tmp_path / "build", {"root": ".", "build": "make", "targets": ["infcover"], "configure": True}
    out = build / "compile_commands.json"
    run, calls = _tool(0, writes={out: "[]"})
    steps, state = clang_run.make(run, unit, build, 2)
    assert calls[0] == (["sh", "-c", clang_run.CONFIGURE], clang_run.WORK)
    assert calls[1][0][:4] == ["bear", "--output", str(out), "--"] and state == {"state": "configured"}
    assert [step["step"] for step in steps] == ["configure", "make under Bear"]
    run, calls = _tool(1, "Compiler error reporting is too harsh for ./configure (perhaps remove -Werror).\n")
    steps, state = clang_run.make(run, unit, tmp_path / "b2", 2)
    assert len(calls) == 1 and state["cause"] == (
        "configure ended with exit code 1: Compiler error reporting is too harsh for ./configure (perhaps remove "
        "-Werror).")


def test_an_autotools_project_is_regenerated_configured_apart_and_made_under_bear(tmp_path):
    """mix-real-zlib's contrib/minizip: `autoreconf` writes the configure script a checkout lacks, the configure
    runs in a build folder of its own (a VPATH build: the copy's own Makefile stays the project's), and make runs
    there under Bear, going on past an error. A step that fails says which, with the tool's own words."""
    assert clang.builds([{"name": "minizip", "kind": "autotools-project", "root": "contrib/minizip"}], [],
                        lambda root: root) == [{"root": "contrib/minizip", "build": "autotools"}]
    assert "autotools-project" in clang.UNIT_KINDS and "autotools" in clang_run.BEAR_BUILDS
    build = tmp_path / "build"
    out = build / "compile_commands.json"
    unit = {"root": "contrib/minizip", "build": "autotools"}
    source = clang_run.WORK / "contrib/minizip"
    run, calls = _tool(0, writes={out: "[]"})
    steps, state = clang_run.autotools(run, unit, build, 2)
    assert calls == [(["autoreconf", "-fi"], source), ([str(source / "configure")], build),
                     (["bear", "--output", str(out), "--", "make", "-k", "-j2"], build)]
    assert state == {"state": "configured"}
    assert [step["step"] for step in steps] == ["autoreconf", "configure", "make under Bear"]
    run, _calls = _tool(1, "configure.ac:7: error: possibly undefined macro: LT_INIT\n")
    _steps, state = clang_run.autotools(run, unit, tmp_path / "b2", 2)
    assert state["state"] == "failed" and state["cause"] == (
        "autoreconf ended with exit code 1: configure.ac:7: error: possibly undefined macro: LT_INIT")


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
    _tools(tools)
    work.mkdir()
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
    assert calls.count(install) == 1 and calls.index(install) == 3  # after Meson's setup, its compiler asked, its index
    assert [step["step"] for step in results[1]["steps"]] == ["install Bear", "make under Bear", "index"]
    # Bear that does not install: the builds that run under it say so.
    install = f"dpkg -i {tmp_path / 'again/tools'}/bear/*.deb"
    failed, _calls = _main(tmp_path / "again", units[1:2], {install: (1, "dpkg: error: cannot access archive\n", {})})
    assert failed[0]["state"] == "failed"
    assert failed[0]["cause"] == "install Bear ended with exit code 1: dpkg: error: cannot access archive"


def test_scip_clang_reads_the_database_with_clangs_builtin_headers_and_names_their_package(tmp_path):
    """The headers the copy carries are unpacked once; scip-clang reads each database as `builtin_headers` gives
    it, while the files compiled are counted from the build's own; the headers' folder is the package `clang` at
    their version, the identity scip-clang writes in their symbols."""
    work = tmp_path / "work"
    database = [{"directory": str(work), "file": "a.c", "arguments": ["gcc", "-c", "a.c"]}]
    answers = {"make": (0, "", {tmp_path / "scratch/build-0/compile_commands.json": json.dumps(database)}),
               "-print-resource-dir": (1, "gcc: error: unrecognized command-line option\n", {}),
               "-print-file-name=include": (0, "include\n", {})}  # GCC's answer when it has no such folder
    results, calls = _main(tmp_path, [{"root": ".", "build": "make", "targets": ["all"]}], answers)
    headers = tmp_path / "scratch/clang/include"
    index, = (command for command in calls if any(word.startswith("--compdb-path=") for word in command))
    given = Path(next(word for word in index if word.startswith("--compdb-path=")).split("=", 1)[1])
    assert json.loads(given.read_text(encoding="utf-8"))[0]["arguments"] == \
        ["gcc", "-c", "a.c", "-nobuiltininc", "-isystem", str(headers)]
    assert results[0]["compiled"] == {"a.c": 1} and (headers / "stddef.h").is_file()
    packages = json.loads((tmp_path / "scratch/package-map.json").read_text(encoding="utf-8"))
    assert {"path": str(headers), "package": f"clang@{clang.CLANG_HEADERS[0]}"} in packages


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
            mock.patch.object(clang, "_sha256", lambda path: ""), \
            mock.patch.object(clang, "clang_headers", lambda: Path("headers.tar")):
        carried = clang.tools({"meson", "make", "bazel", "go"})
        cmake_only = clang.tools()
    names = {path.removeprefix(f"{clang.TOOLS}/") for path in carried}
    headers = f"clang-{clang.CLANG_HEADERS[0]}-headers.tar"
    assert {"meson.whl", "ninja.whl", "bazel", "go.tar.gz", "scip-clang", "clang_run.py", headers} <= names
    assert f"{clang.TOOLS}/{headers}" in cmake_only
    assert sorted(name for name in names if name.startswith("bear/")) == sorted(
        f"bear/{posixpath.basename(url)}" for url, _digest in clang.BEAR)
    assert all(url.startswith("https://archive.ubuntu.com/ubuntu/pool/") and len(digest) == 64
               for url, digest in clang.BEAR)
    assert not any(name.startswith("bear/") or name.endswith(".whl") for name in cmake_only)


def test_clangs_builtin_headers_come_from_its_release_source_packed_once(tmp_path):
    """The builtin headers of the clang scip-clang v0.4.1 is built on (LLVM 21.1.8, its Version.h's commit): the
    folder lib/Headers of clang's release source, which clang installs as its resource folder's include, packed
    once under `include/` beside the archive, and nothing else of the source. Every run carries them."""
    version, url, digest = clang.CLANG_HEADERS
    assert (version, url) == ("21.1.8", "https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8/"
                                        "clang-21.1.8.src.tar.xz") and len(digest) == 64
    source = tmp_path / "fetched" / posixpath.basename(url)
    source.parent.mkdir()
    with tarfile.open(source, "w:xz") as bundle:
        for name in ("lib/Headers/xmmintrin.h", "lib/Headers/cuda_wrappers/new", "lib/Sema/Sema.cpp"):
            entry = tarfile.TarInfo(f"clang-{version}.src/{name}")
            entry.size = len(name)
            bundle.addfile(entry, io.BytesIO(name.encode()))
    with mock.patch.object(preparation, "fetched", lambda url, digest, name: source):
        packed = clang.clang_headers()
        with mock.patch("tarfile.open", side_effect=AssertionError("packed again")):
            assert clang.clang_headers() == packed
    assert packed == source.with_name(f"clang-{version}-headers.tar")
    with tarfile.open(packed) as bundle:
        assert sorted(bundle.getnames()) == ["include/cuda_wrappers/new", "include/xmmintrin.h"]
        assert bundle.extractfile("include/xmmintrin.h").read() == b"lib/Headers/xmmintrin.h"


# ---------------------------------------------------------------------------------------------------------------
# A real container, only on request: the provider path on a real run.

SMOKE = os.environ.get("DAODAN_CLANG_SMOKE") == "1"


@pytest.mark.skipif(not SMOKE, reason="set DAODAN_CLANG_SMOKE=1 to index the fixture in a real container")
def test_smoke_fmt_from_github_asks_and_after_the_yes_is_downloaded_through_the_proxy(tmp_path):
    """fmt comes from github.com, which always asks (plan T0.C.1): the run with no network never downloads it,
    CMake's provider records it, the unit is not indexed and github.com waits for the user. The answer is recorded
    here, "once", as the app records it; the next analysis configures the unit again in its preparation, git
    cloning fmt through Daodan's proxy, and indexes the project's two files, none of fmt's."""
    fixture = HERE / "fixtures/clang-index/fetch"
    project = str(fixture.resolve())
    unit = {"name": "fetchfixture", "kind": "cmake-target", "root": ".", "manifest": "CMakeLists.txt"}
    result = clang.index(fixture, tmp_path / "work", units=[unit])
    assert result["state"] == "unavailable", result
    state = result["units"][0]
    assert state["kind"] == "download-outside-registries" and state["fetched"] == [FMT]
    assert "CMake Error" in state["error"] and "github.com" in result["reason"]
    assert [gap["hosts"] for gap in result["gaps"] if gap["kind"] == "approval_required"] == [["github.com"]]
    assert [row["host"] for row in egress.pending(project)] == ["github.com"]
    egress.reply(project, ["github.com"], "once")
    result = clang.index(fixture, tmp_path / "again", units=[unit])
    assert "state" not in result, result
    assert [(item["root"], item["state"]) for item in result["units"]] == [(".", "indexed")], result["units"]
    assert result["configs"]["compiled"] == {"main.cpp": 1, "plain.cpp": 1}
    assert not [gap for gap in result.get("gaps") or () if gap["kind"] in ("approval_required", "host_denied")]
    index = code_graph.Index(fixture)
    for path, prefix in result["indexes"]:
        index.load(Path(path), prefix)
    assert sorted(index.documents) == ["main.cpp", "plain.cpp"]


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
    snapshot.read_project(project, manifest)
    given = clang.structure(premap.ensure(manifest))  # the units the stage hands the indexer
    assert {unit["kind"] for unit in given["units"]} == {"cmake-target"}
    result = clang.index(project, tmp_path / "work", cpus=2, **given)
    assert "state" not in result, result
    assert [u["state"] for u in result["units"]] == ["indexed"], result["units"]
    assert _occurrences(project, result["indexes"]) == _occurrences(fixture, [(fixture / "index.scip", "")])
