"""The C and C++ observer: its plan from the pre-map, the readers of Callgrind's outputs on a CMake project with a
shared library, the join of what they read, and its container run against the fake Docker-compatible command line
of `test_codebase_map_container.py`.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_dynamic_clang.py

The observation is written by hand in the recorders' formats: the Callgrind outputs of CTest and of the test it
runs (cl-format.html), and the calls the container's reader makes of them. The fake container never runs a command.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import code_graph  # noqa: E402
import container  # noqa: E402
import dynamic  # noqa: E402
import preparation  # noqa: E402
import snapshot  # noqa: E402
from dynamic import callgrind, callgrind_sites  # noqa: E402
from dynamic import clang as observer  # noqa: E402
from indexers import clang as index  # noqa: E402
from test_codebase_map_container import FAKE_CLI, tree_digest  # noqa: E402
from test_codebase_map_indexers_jvm import PLAY  # noqa: E402

HEADER = '''struct shape {
    int side;
    int (*area)(const struct shape *);
};

int square_area(const struct shape *s);
int total(const struct shape *shapes, int n);
'''
SOURCE = '''#include "shapes.h"

int square_area(const struct shape *s)
{
    return s->side * s->side;
}

static int twice(int x) { return x * 2; }

int total(const struct shape *shapes, int n)
{
    int sum = 0;
    for (int i = 0; i < n; i++)
        sum += shapes[i].area(&shapes[i]);
    return twice(sum);
}
'''
TEST = '''#include "shapes.h"
#include <stdio.h>

int main(void)
{
    struct shape one = {2, square_area};
    int got = total(&one, 1);
    printf("%d\\n", got);
    return got == 8 ? 0 : 1;
}
'''
LISTS = '''cmake_minimum_required(VERSION 3.20)
project(shapes C)
enable_testing()
add_library(shapes SHARED shapes.c)
add_executable(test_shapes test_shapes.c)
target_link_libraries(test_shapes shapes)
add_test(NAME shapes COMMAND test_shapes)
'''
FILES = {"CMakeLists.txt": LISTS, "shapes.h": HEADER, "shapes.c": SOURCE, "test_shapes.c": TEST}
LIB, MAIN = "shapes.c", "test_shapes.c"
BUILD = "/daodan/state/build/root"
EXE, SHARED, LIBC = f"{BUILD}/test_shapes", f"{BUILD}/libshapes.so", "/usr/lib/x86_64-linux-gnu/libc.so.6"
CTEST = "/daodan/state/tools/cmake/bin/ctest"
EXE_BASE, SHARED_BASE = 0x108000, 0x4853000

# CTest's own trace, then its test's: the test executable calls into its shared library and the C library.
CTEST_TRACE = f"""# callgrind format
version: 1
creator: callgrind-3.22.0
pid: 7
cmd:  {CTEST} --output-on-failure --timeout 1800
part: 1

positions: instr line
events: Ir
summary: 902114

ob={CTEST}
fl=???
fn=main
0x52c000 0 12
cob={LIBC}
cfn=execve
calls=1 0x4a9e000 0
0x52c040 0 4
"""
TEST_TRACE = f"""# callgrind format
version: 1
creator: callgrind-3.22.0
pid: 9
cmd:  {EXE}
part: 1

positions: instr line
events: Ir
summary: 1904

ob={LIBC}
fl=???
fn=(below main)
0x48c2000 0 8
cob={EXE}
cfi=/work/{MAIN}
cfn=main
calls=1 0x109149 5
0x48c2010 0 600

ob={EXE}
fl=/work/{MAIN}
fn=main
0x109149 5 9
cob={SHARED}
cfi=/work/{LIB}
cfn=total
calls=1 0x4854120 10
0x109180 7 41
cob={LIBC}
cfi=???
cfn=printf
calls=1 0x48f0100 0
0x109190 8 520

ob={SHARED}
fl=/work/{LIB}
fn=total
0x4854120 10 14
cfn=square_area
calls=1 0x4854100 3
0x4854150 14 9
cfn=twice
calls=1 0x4854110 8
0x4854170 15 6
"""
ROWS = {  # each object's line table, by offset: file, line, column from 1
    EXE: {0x1180: (MAIN, 7, 15), 0x1190: (MAIN, 8, 5), 0x1149: (MAIN, 5, 1)},
    SHARED: {0x1150: (LIB, 14, 16), 0x1170: (LIB, 15, 12), 0x1120: (LIB, 10, 5), 0x1100: (LIB, 3, 5),
             0x1110: (LIB, 8, 12)}}
SYMBOLS = {EXE: {0x1149, 0x1050}, SHARED: {0x1100, 0x1110, 0x1120, 0x1000}}


def objects(path: str):
    if path not in ROWS:
        return None
    return SYMBOLS[path], lambda offsets: {offset: (f"/work/{ROWS[path][offset][0]}", *ROWS[path][offset][1:])
                                           for offset in offsets if offset in ROWS[path]}


CALLS = [
    [f"/work/{LIB}", 14, 16, f"/work/{LIB}", 3, 5, "square_area", SHARED, 1],
    [f"/work/{LIB}", 15, 12, f"/work/{LIB}", 8, 12, "twice", SHARED, 1],
    [f"/work/{MAIN}", 7, 15, f"/work/{LIB}", 10, 5, "total", SHARED, 1],
    [f"/work/{MAIN}", 8, 5, "???", 0, 0, "printf", LIBC, 1]]
UNREAD = {"made outside the project": 2}


def observation(folder: Path, calls=CALLS, unread=UNREAD) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "calls.json").write_text(json.dumps({"processes": 2, "calls": calls, "unread": unread}),
                                       encoding="utf-8")
    return folder


def write_project(folder: Path, files: dict = FILES) -> Path:
    for rel, text in files.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(text, encoding="utf-8", newline="\n")
    return folder


def by_place(sites: list[dict]) -> dict:
    return {(site["file"], site["line"], site["column"], site["name"]): sorted(c["name"] for c in site["callees"])
            for site in sites}


# ------------------------------------------------------------------ the readers

def test_a_shared_librarys_calls_are_read_at_its_own_load_address():
    found = callgrind_sites.document([CTEST_TRACE, TEST_TRACE], "/work", objects)
    assert found == {"processes": 2, "calls": CALLS, "unread": UNREAD}  # CTest's and the C library's calls: outside


def test_a_call_through_a_function_pointer_is_a_site_at_its_field_with_the_function_it_reached(tmp_path):
    project = write_project(tmp_path / "project")
    sites, facts = callgrind.read(observation(tmp_path / "observed"), project)
    assert by_place(sites) == {(LIB, 13, 25, "area"): ["square_area"], (LIB, 14, 11, "twice"): ["twice"],
                               (MAIN, 6, 14, "total"): ["total"], (MAIN, 7, 4, "printf"): ["printf"]}
    [site] = [site for site in sites if site["name"] == "area"]
    assert site["callees"] == [{"kind": "project", "file": LIB, "line": 2, "column": 0, "name": "square_area",
                                "type": "function"}]
    [twice] = [site for site in sites if site["name"] == "twice"]
    assert twice["callees"][0]["line"] == 7  # where the definition starts: `static`, as the snapshot declares it
    [printf] = [site for site in sites if site["name"] == "printf"]
    assert observer.external(printf["callees"][0]) == {"manager": "system", "package": "libc.so.6", "version": None}
    assert facts == {"processes": 2, "calls": 4, "unplaced": UNREAD}


def test_the_sites_join_the_snapshots_references(tmp_path):
    project = write_project(tmp_path / "project")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    sites, _facts = callgrind.read(observation(tmp_path / "observed"), project)
    with code_graph.Snapshot(manifest) as snap:
        rows, facts = dynamic.join(snap, "c", sites, [], observer)
        names = {identity: (rel, span[0], parts[-1] if parts else "")
                 for identity, rel, _kind, _resolution, _target, span, parts, _reason in snap.references("c")}
        square, twice, total = (snap.function_at(LIB, 3, 0), snap.function_at(LIB, 8, 0), snap.function_at(LIB, 10, 0))
    assert None not in (square, twice, total)
    found: dict = {}
    for row in rows:
        found.setdefault(names[row["reference_id"]], set()).add((row["verdict"], row["target_id"]))
    assert found[(LIB, 14, "area")] == {("project-callable", square)}
    assert found[(LIB, 15, "twice")] == {("project-callable", twice)}
    assert found[(MAIN, 7, "total")] == {("project-callable", total)}
    assert {verdict for verdict, _target in found[(MAIN, 8, "printf")]} == {"external"}
    assert facts["joined"] == 4


# ------------------------------------------------------------------ the plan

def record(*roots: str, kind: str = "cmake-target", toolchains=()) -> dict:
    return {"units": [{"kind": kind, "root": root, "name": f"t{number}"} for number, root in enumerate(roots)],
            "workspace": [], "toolchains": list(toolchains)}


def reader(texts: dict):
    return lambda rel: texts.get(rel, "")


def test_a_cmake_root_that_declares_tests_is_a_run_of_ctest_after_its_build():
    planned = observer.plan(record("."), sorted(FILES), reader(FILES))
    assert planned["runs"] == [{"root": ".", "runner": "ctest", "argv": observer.ARGV}]
    assert planned["gaps"] == []


def test_a_root_without_add_test_or_enable_testing_is_a_gap():
    files = {"a/CMakeLists.txt": "project(a C)\nenable_testing()\nadd_executable(a a.c)\n",
             "b/CMakeLists.txt": "project(b C)\nadd_test(NAME b COMMAND b)\n", "b/b.c": ""}
    planned = observer.plan(record("a", "b"), sorted(files), reader(files))
    assert planned["runs"] == []
    assert [(gap["kind"], gap["path"]) for gap in planned["gaps"]] == [("no_tests", "a"), ("no_tests", "b")]
    assert "add_test" in planned["gaps"][0]["detail"]


def test_tests_a_subfolder_adds_run_from_the_top_configure():
    files = {"CMakeLists.txt": "project(ringbuf CXX)\nif(PROJECT_IS_TOP_LEVEL)\n  enable_testing()\n"
                               "  add_subdirectory(tests)\nendif()\n",
             "tests/CMakeLists.txt": "add_executable(t t.cpp)\nadd_test(NAME ring COMMAND t)\n"}
    planned = observer.plan(record(".", "tests"), sorted(files), reader(files))
    assert [run["root"] for run in planned["runs"]] == ["."] and planned["gaps"] == []


def test_the_fixtures_tests_run_from_the_root_the_pre_map_names_by_the_empty_path():
    """sys-cpp-header-only: a header-only library at the root, named by the empty path, its test in tests/."""
    fixture = HERE.parent / "benchmarks/project-model/fixtures/sys-cpp-header-only"
    record = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
    assert [unit["root"] for unit in record["units"]] == ["", "tests"]
    files = sorted(path.relative_to(fixture).as_posix() for path in fixture.rglob("*") if path.is_file())
    planned = observer.plan({**record, "workspace": []}, files, lambda rel: (fixture / rel).read_text(encoding="utf-8"))
    assert [(run["root"], run["runner"]) for run in planned["runs"]] == [(".", "ctest")]
    assert planned["gaps"] == []


def test_tests_declared_in_an_included_cmake_file_and_by_googletest_count():
    files = {"CMakeLists.txt": "project(a CXX)\ninclude(CTest)\ninclude(cmake/tests.cmake)\n",
             "cmake/tests.cmake": "  gtest_discover_tests(unit_tests)\n"}
    assert [run["root"] for run in observer.plan(record("."), sorted(files), reader(files))["runs"]] == ["."]


def test_a_unit_another_build_makes_is_a_gap_naming_it():
    planned = observer.plan(record("native", kind="meson-target"), ["native/meson.build"], reader({}))
    assert planned["runs"] == []
    [gap] = planned["gaps"]
    assert (gap["kind"], gap["path"]) == ("runner_not_observed", "native") and "meson" in gap["detail"]


def test_without_a_native_unit_the_plan_says_so():
    planned = observer.plan({"units": [{"kind": "cargo-crate", "root": "."}]}, ["Cargo.toml"], reader({}))
    assert planned["runs"] == [] and planned["gaps"][0]["kind"] == "no_tests"


def test_a_cmake_above_the_pin_comes_from_the_pre_map():
    stated = [{"tool": "cmake", "version": "3.31.2", "declared_in": "CMakeLists.txt"}]
    planned = observer.plan(record(".", toolchains=stated), sorted(FILES), reader(FILES))
    assert planned["toolchains"] == stated


# ------------------------------------------------------------------ the container run

class ObserveTest(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="daodan-dynamic-clang-test-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.state = self.scratch / "state"
        for name in ("containers", "images", "play"):
            (self.state / name).mkdir(parents=True)
        fake = self.scratch / "fake_docker.py"
        fake.write_text(PLAY.replace('["bash", "-c"]', '["sh", "-c"]') + FAKE_CLI, encoding="utf-8")
        self.engine = container.Engine("fake", (sys.executable, str(fake), str(self.state)))
        self.project = write_project(self.scratch / "project")
        self.out = self.scratch / "out"
        tool = self.scratch / "tool.bin"
        tool.write_bytes(b"a pinned download")
        for patcher in (mock.patch.object(preparation, "fetched", return_value=tool),
                        mock.patch.object(container, "free_memory", return_value=64 * 2**30),
                        mock.patch("time.sleep")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def play(self, phase: str, files: dict | None = None, text: str = "", code: int = 0):
        folder = self.state / "play" / phase
        for rel, content in (files or {}).items():
            target = folder / "fs" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "log").write_text(text, encoding="utf-8")
        (folder / "code").write_text(str(code))

    def play_run(self, log: str = f"Test project {BUILD}\n    Start 1: shapes\n1/1 Test #1: shapes ........   Passed"
                                  "   12.31 sec\n\n100% tests passed, 0 tests failed out of 1\n",
                 code: int = 0, **files: str | None):
        out = observer.OUT.lstrip("/")
        given = {"calls.json": json.dumps({"processes": 2, "calls": CALLS, "unread": UNREAD}), "recorder.code": "0\n",
                 "sites.code": "0\n", "tests-0.log": log, "tests-0.code": f"{code}\n", **files}
        self.play("execute", {f"{out}/{name}": text for name, text in given.items() if text is not None})

    def observe(self, record_: dict | None = None, **options) -> dict:
        files = sorted(path.relative_to(self.project).as_posix() for path in self.project.rglob("*") if path.is_file())

        def read(rel: str) -> str:
            return (self.project / rel).read_text(encoding="utf-8")

        planned = observer.plan(record_ or record("."), files, read)
        return observer.observe(self.project, planned, self.out, options.pop("engine", self.engine), **options)

    def created(self) -> list[list[str]]:
        path = self.state / "calls.jsonl"
        calls = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        return [call for call in calls if call[0] == "create"]

    def script(self, phase: str) -> str:
        return (self.state / "scripts" / f"{phase}.sh").read_text(encoding="utf-8")

    def test_the_tests_run_under_the_recorder_and_their_calls_come_back_as_sites(self):
        self.play_run()
        result = self.observe()
        self.assertEqual(result["state"], "ran")
        self.assertIsNone(dynamic.malformed(result))
        self.assertEqual(by_place(result["sites"])[(LIB, 13, 25, "area")], ["square_area"])
        self.assertEqual(result["gaps"], [])
        [run] = result["runs"]
        self.assertEqual((run["root"], run["runner"], run["argv"], run["state"], run["exit_code"], run["tests"]),
                         (".", "ctest", observer.ARGV, "ran", 0, {"passed": 1, "failed": 0}))

    def test_the_build_is_a_debug_build_and_ctest_runs_under_callgrind_with_no_network(self):
        self.play_run()
        self.observe()
        _proxy, _prepare, execute = self.created()
        self.assertEqual(execute[execute.index("--network") + 1], "none")
        prepared, executed = self.script("prepare"), self.script("execute")
        self.assertIn("cmake-3.28.3-linux-x86_64", prepared)
        self.assertIn("dpkg-deb -x", prepared)
        self.assertIn("-DCMAKE_BUILD_TYPE=Debug", executed)
        self.assertIn(f"{BUILD}", executed)
        self.assertIn("--tool=callgrind", executed)
        self.assertLess(executed.index("cmake --build"), executed.index("--dump-instr=yes"))
        self.assertLess(executed.index("recorder.code"), executed.index("-DCMAKE_BUILD_TYPE=Debug"))
        self.assertLess(executed.index("-DCMAKE_BUILD_TYPE=Debug"), executed.index("callgrind_sites.py"))

    def test_vcpkg_restores_in_the_preparation_and_the_configure_reads_its_toolchain(self):
        (self.project / "vcpkg.json").write_text('{"dependencies": ["fmt"]}', encoding="utf-8")
        self.play_run()
        self.observe()
        proxy, _prepare, _execute = self.created()
        self.assertIn("github.com", proxy)
        prepared, executed = self.script("prepare"), self.script("execute")
        self.assertIn("vcpkg install", prepared)
        self.assertIn("DAODAN-RESTORE-FAILED vcpkg", prepared)
        self.assertIn("/daodan/state/prep/root/init.cmake", executed)

    def test_the_restore_is_the_analyzers_own_where_a_preset_names_conan_beside_vcpkg(self):
        """The observer restores a root as the C and C++ analyzer does (`indexers.clang.restores`, the pre-map's
        choice): the manager a configure preset's CMAKE_TOOLCHAIN_FILE names, else vcpkg."""
        presets = {"version": 3, "configurePresets": [
            {"name": "conan", "cacheVariables": {"CMAKE_TOOLCHAIN_FILE": "build/conan_toolchain.cmake"}}]}
        for name, text in {"vcpkg.json": '{"dependencies": ["fmt"]}', "conanfile.txt": "[requires]\nfmt/10.2.1\n",
                           "CMakePresets.json": json.dumps(presets)}.items():
            (self.project / name).write_text(text, encoding="utf-8")
        self.play_run()
        self.observe()
        prepared = self.script("prepare")
        self.assertIn(index.restores(self.project, ["."])["."]["line"], prepared)
        self.assertNotIn("vcpkg install", prepared)
        proxy, _prepare, _execute = self.created()
        self.assertIn("center2.conan.io", proxy)

    def test_the_project_is_not_changed_and_the_recorder_is_carried(self):
        before = tree_digest(self.project)
        self.play_run()
        self.observe()
        self.assertEqual(tree_digest(self.project), before)
        prepare = self.created()[1]
        carried = self.state / "containers" / prepare[prepare.index("--name") + 1] / "fs"
        for name in ("callgrind_sites.py", "valgrind.deb", "pyelftools.whl", "cmake.tar.gz"):
            self.assertTrue((carried / preparation.IN.lstrip("/") / name).is_file(), name)

    def test_a_configure_or_build_that_fails_is_a_gap_with_its_words(self):
        log = ("-- The C compiler identification is GNU 13.3.0\nCMake Error at CMakeLists.txt:4 (find_package):\n"
               "  Could not find a package configuration file provided by \"fmt\"\n-- Configuring incomplete\n")
        self.play_run(log, 1, **{"calls.json": json.dumps({"processes": 0, "calls": [], "unread": {}})})
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual((gap["kind"], gap["path"], result["runs"][0]["state"]),
                         ("tests_not_started", ".", "not_started"))
        self.assertIn("Could not find a package", gap["detail"])

    def test_failing_tests_are_said_and_what_they_called_is_kept(self):
        log = (f"Test project {BUILD}\n1/2 Test #1: shapes ...   Passed\n2/2 Test #2: other ...***Failed\n\n"
               "50% tests passed, 1 tests failed out of 2\n\nThe following tests FAILED:\n\t  2 - other (Failed)\n")
        self.play_run(log, 8)
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual((gap["kind"], gap["path"]), ("tests_failed", "."))
        self.assertEqual(result["runs"][0]["tests"], {"passed": 1, "failed": 1})
        self.assertTrue(result["sites"])

    def test_a_build_that_declares_no_test_with_its_options_is_a_gap(self):
        self.play_run(f"Test project {BUILD}\nNo tests were found!!!\n", 0)
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual((gap["kind"], gap["path"], result["runs"][0]["state"]), ("no_tests", ".", "no_tests"))

    def test_a_run_that_outlasts_its_time_is_a_gap_and_keeps_what_it_recorded(self):
        self.play_run(f"Test project {BUILD}\n    Start 1: shapes\n", 124)
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual((gap["kind"], result["runs"][0]["state"]), ("tests_timeout", "timeout"))
        self.assertTrue(result["sites"])

    def test_a_valgrind_that_does_not_run_here_is_a_gap_and_no_test_runs(self):
        self.play_run(**{"recorder.code": "1\n", "recorder.log": "valgrind: m_ume.c: can't load\n",
                         "tests-0.log": None, "tests-0.code": None, "calls.json": None})
        result = self.observe()
        self.assertEqual([gap["kind"] for gap in result["gaps"]], ["recorder_failed"])
        self.assertEqual((result["sites"], result["runs"]), ([], []))
