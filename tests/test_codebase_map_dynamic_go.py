"""The Go observer: its plan from the pre-map, its reader of the recorder's files, the join of what it reads, and
its container run against the fake Docker-compatible command line of `test_codebase_map_container.py`.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_dynamic_go.py

The observation the reader and the join are given is written by hand in the recorder's format (`go_record.go`):
the table of the small module below and the calls its test makes. Where Daodan's Go is installed (never
downloaded here), the recorder itself rewrites a copy of the module and runs its test: its files must be the
hand-written ones. The fake container never runs a command: each test checks what `observe` sends and reads.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import code_graph  # noqa: E402
import container  # noqa: E402
import egress  # noqa: E402
import dynamic  # noqa: E402
import engine_tools  # noqa: E402
import preparation  # noqa: E402
import snapshot  # noqa: E402
from dynamic import go as observer  # noqa: E402
from test_codebase_map_container import FAKE_CLI, tree_digest  # noqa: E402
from test_codebase_map_indexers_jvm import PLAY  # noqa: E402

SOURCE = '''package shapes

type Shape interface{ Area() int }

type Square struct{ Side int }

func (s Square) Area() int { return s.Side * s.Side }

func Double(x int) int { return x * 2 }

func Apply(f func(int) int, x int) int {
	return f(x)
}

var table = map[string]func(int) int{"double": Double}

func Total(shapes []Shape) int {
	total := 0
	for _, s := range shapes {
		total += s.Area()
	}
	return Apply(Double, total) + Apply(func(x int) int { return x }, Double(1)) + table["double"](2)
}

func Idle() int { return Double(0) }
'''
TEST = '''package shapes

import "testing"

func TestTotal(t *testing.T) {
	if got := Total([]Shape{Square{2}}); got != 14 {
		t.Fatalf("got %d", got)
	}
}
'''
FILES = {"go.mod": "module example.com/app\n\ngo 1.21\n", "shapes/shapes.go": SOURCE, "shapes/shapes_test.go": TEST}
GO, GO_TEST = "shapes/shapes.go", "shapes/shapes_test.go"
LAST = SOURCE.split("\n")[21]  # the line of five calls


def column(line: str, text: str, nth: int = 0) -> int:
    """The byte column, from 1, of the `nth` `text` in `line`."""
    at = -1
    for _ in range(nth + 1):
        at = line.index(text, at + 1)
    return at + 1


# The recorder's table of the module: every function by id, each file's line count and its calls in order.
TABLE = {
    "modules": {".": "example.com/app"},
    "functions": [[GO, 7, 1, "Square.Area"], [GO, 9, 1, "Double"], [GO, 11, 1, "Apply"], [GO, 17, 1, "Total"],
                  [GO, 22, column(LAST, "func("), "(func)"], [GO, 25, 1, "Idle"], [GO_TEST, 5, 1, "TestTotal"]],
    "files": {GO: {"lines": 25, "calls": [
        [12, 9, "f"], [20, 14, "Area"], [22, column(LAST, "Apply"), "Apply"], [22, column(LAST, "Apply", 1), "Apply"],
        [22, column(LAST, "Double", 1), "Double"], [22, column(LAST, "table"), ""], [25, 26, "Double"]]},
        GO_TEST: {"lines": 9, "calls": [[6, 12, "Total"], [7, 5, "Fatalf"]]}},
    "skipped": {},
}
AREA, DOUBLE, APPLY, TOTAL, LITERAL, IDLE, TEST_TOTAL = range(7)
# What the module's test makes the recorder write: the function entered, its caller's file and line. A line past
# the file's last (25 and 9) names a call: 26 is the first of shapes.go, `f(x)`.
CALLS = [(TEST_TOTAL, "/usr/local/go/src/testing/testing.go", 1934), (TOTAL, f"/work/{GO_TEST}", 10),
         (AREA, f"/work/{GO}", 27), (APPLY, f"/work/{GO}", 28), (DOUBLE, f"/work/{GO}", 26),
         (DOUBLE, f"/work/{GO}", 30), (APPLY, f"/work/{GO}", 29), (LITERAL, f"/work/{GO}", 26),
         (DOUBLE, f"/work/{GO}", 31)]


def observation(folder: Path, table: dict = TABLE, calls=CALLS) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "table.json").write_text(json.dumps(table), encoding="utf-8")
    (folder / "calls.tsv").write_text("".join(f"{i}\t{file}\t{line}\n" for i, file, line in calls), encoding="utf-8")
    return folder


def write_project(folder: Path, files: dict = FILES) -> Path:
    for rel, text in files.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(text, encoding="utf-8", newline="\n")
    return folder


def by_place(sites: list[dict]) -> dict:
    return {(site["file"], site["line"], site["column"], site["name"]): sorted(c["name"] for c in site["callees"])
            for site in sites}


# ------------------------------------------------------------------ the reader

def test_a_recorded_call_is_a_site_at_its_callee_name_with_the_functions_entered_from_it(tmp_path):
    sites, facts = observer.read(observation(tmp_path))
    assert all(site["role"] == "call" for site in sites)
    places = by_place(sites)
    assert places[(GO, 11, 8, "f")] == ["(func)", "Double"]  # a function value: what the run passed
    assert places[(GO, 19, 13, "Area")] == ["Square.Area"]  # an interface's method: the type that was there
    assert places[(GO_TEST, 5, 11, "Total")] == ["Total"]
    [site] = [site for site in sites if site["name"] == "f"]
    assert {"kind": "project", "file": GO, "line": 8, "column": 0, "name": "Double", "type": "function"} \
        in site["callees"]  # lines from 0, byte columns from 0: where the snapshot declares the function
    assert facts["functions"] == 7 and facts["entered"] == 6  # Idle: no test reaches it


def test_two_calls_on_one_line_are_two_sites(tmp_path):
    places = by_place(observer.read(observation(tmp_path))[0])
    first, second = column(LAST, "Apply") - 1, column(LAST, "Apply", 1) - 1
    assert places[(GO, 21, first, "Apply")] == places[(GO, 21, second, "Apply")] == ["Apply"]
    assert places[(GO, 21, column(LAST, "Double", 1) - 1, "Double")] == ["Double"]
    assert places[(GO, 21, column(LAST, "table") - 1, "")] == ["Double"]  # a computed callee: where it starts
    assert len([place for place in places if place[:2] == (GO, 21)]) == 4


def test_an_entry_with_no_call_site_is_counted_by_its_cause_and_never_placed(tmp_path):
    table = {**TABLE, "skipped": {GO_TEST: 'import "C": cgo prints the file again'}}
    calls = [(TEST_TOTAL, "/usr/local/go/src/testing/testing.go", 1934),  # started by the standard library
             (TOTAL, f"/work/{GO_TEST}", 6),  # a file whose sites the recorder left alone
             (DOUBLE, f"/work/{GO}", 23),  # a line of the file, not a call's number: a deferred call
             (DOUBLE, "", 0), (AREA, f"/work/{GO}", 27)]
    sites, facts = observer.read(observation(tmp_path, table, calls))
    assert list(by_place(sites)) == [(GO, 19, 13, "Area")]
    assert facts["unplaced"] == {"called from outside the modules": 2, "not at a call (a deferred call)": 1,
                                 'import "C": cgo prints the file again': 1}


def test_a_trimmed_path_is_read_through_its_module(tmp_path):
    """`-trimpath` names a file by its module's path, not by its folder."""
    table = {"modules": {"svc/api": "example.com/api"}, "functions": [["svc/api/a.go", 3, 1, "A"]],
             "files": {"svc/api/a.go": {"lines": 5, "calls": [[4, 9, "A"]]}}, "skipped": {}}
    sites, _facts = observer.read(observation(tmp_path, table, [(0, "example.com/api/a.go", 6)]))
    assert by_place(sites) == {("svc/api/a.go", 3, 8, "A"): ["A"]}


def test_a_line_cut_by_a_killed_process_is_no_record(tmp_path):
    folder = observation(tmp_path)
    with (folder / "calls.tsv").open("a", encoding="utf-8") as stream:
        stream.write(f"{AREA}\t/work/{GO}")
    assert observer.read(folder)[1]["records"] == len(CALLS)


def test_without_the_recorders_files_nothing_is_read(tmp_path):
    assert observer.read(tmp_path) == ([], {})


# ------------------------------------------------------------------ the join

def test_the_sites_join_the_snapshots_references_and_close_what_only_a_run_shows(tmp_path):
    project = write_project(tmp_path / "project")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    sites, _facts = observer.read(observation(tmp_path / "observed"))
    with code_graph.Snapshot(manifest) as snap:
        rows, facts = dynamic.join(snap, "go", sites, [], observer)
        names = {identity: (rel, span[0], parts[-1] if parts else "")
                 for identity, rel, _kind, _resolution, _target, span, parts, _reason in snap.references("go")}
    found: dict = {}
    for row in rows:
        assert row["confidence"] == "observed" and row["resolver"] == dynamic.resolver(observer)
        found.setdefault(names[row["reference_id"]], set()).add((row["verdict"], row["target_id"]))
    literal = f"{GO}::function@22:{column(LAST, 'func(') - 1}"
    assert found[(GO, 12, "f")] == {("project-callable", f"{GO}::function@9:0"), ("project-callable", literal)}
    assert found[(GO, 20, "Area")] == {("project-callable", f"{GO}::function@7:0")}
    assert found[(GO, 22, "")] == {("project-callable", f"{GO}::function@9:0")}  # table["double"](2)
    assert found[(GO_TEST, 6, "Total")] == {("project-callable", f"{GO}::function@17:0")}
    assert facts["recorded"] == facts["placed"] == len(sites) and not facts["unjoined"]


# ------------------------------------------------------------------ the plan

def record(*roots: str, toolchains=()) -> dict:
    return {"units": [{"kind": "go-module", "root": root, "name": f"example.com/{root}"} for root in roots],
            "toolchains": list(toolchains)}


def test_each_go_module_with_tests_is_a_run_of_go_test():
    files = ["go.mod", "a.go", "a_test.go", "tools/go.mod", "tools/t.go", "tools/t_test.go"]
    planned = observer.plan(record(".", "tools"), files, None)
    assert [(run["root"], run["argv"]) for run in planned["runs"]] == [
        (".", ["go", "test", "-vet=off", "./..."]), ("tools", ["go", "test", "-vet=off", "./..."])]
    assert planned["gaps"] == []


def test_a_module_without_a_test_file_is_a_gap_and_tests_of_a_nested_module_are_not_its_own():
    files = ["go.mod", "a.go", "tools/go.mod", "tools/t.go", "tools/t_test.go", "testdata/x_test.go"]
    planned = observer.plan(record(".", "tools"), files, None)
    assert [run["root"] for run in planned["runs"]] == ["tools"]
    [gap] = planned["gaps"]
    assert (gap["kind"], gap["path"]) == ("no_tests", ".") and "_test.go" in gap["detail"]


def test_the_root_module_the_pre_map_names_by_the_empty_path_is_planned_once():
    """The pre-map's units of sys-go-single: the root module's folder is the empty path (module_graph), or `.`."""
    fixture = HERE.parent / "benchmarks/project-model/fixtures/sys-go-single"
    units = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))["units"]
    assert [unit["root"] for unit in units] == [""]
    files = sorted(path.relative_to(fixture).as_posix() for path in fixture.rglob("*") if path.is_file())
    assert any(rel.endswith("_test.go") for rel in files)
    for given in (units, [*units, {**units[0], "root": "."}]):
        planned = observer.plan({"units": given}, files, None)
        assert [(run["root"], run["runner"]) for run in planned["runs"]] == [(".", "go test")]
        assert planned["gaps"] == []


def test_the_command_a_ci_step_declares_for_a_module_comes_before_the_convention():
    """`go test -tags e2e ./...` of a CI step (`renovate._ci_tests`) runs in its module in place of `ARGV`, with
    the step as `declared_in` (its steps before it are the module's `ci_steps`); a user's command comes first."""
    files = ["go.mod", "a.go", "a_test.go", "tools/go.mod", "tools/t.go", "tools/t_test.go"]
    ci = {"root": ".", "runner": "go test", "argv": ["go", "test", "-tags", "e2e", "./..."], "source": "ci",
          "declared_in": ".github/workflows/ci.yml#jobs.test.steps.2"}
    user = {**ci, "argv": ["go", "test", "-run", "TestOne", "./..."], "by": "user", "declared_in": None}
    planned = observer.plan({**record(".", "tools"), "tests": [ci]}, files, None)
    assert planned["runs"] == [
        {"root": ".", "runner": "go test", "argv": ci["argv"], "declared_in": ci["declared_in"]},
        {"root": "tools", "runner": "go test", "argv": observer.ARGV}]
    assert dynamic.declared({"tests": [ci, user]}, "go test", "") is user
    assert dynamic.declared({"tests": [ci]}, "cargo test", ".") is None


def test_without_a_go_module_the_plan_says_so():
    planned = observer.plan({"units": [{"kind": "cargo-package", "root": "."}]}, ["main.go"], None)
    assert planned["runs"] == [] and planned["gaps"][0]["kind"] == "no_tests"
    assert "no Go module" in planned["gaps"][0]["detail"]


# ------------------------------------------------------------------ the real recorder

def daodan_go() -> str | None:
    """Daodan's Go where it is already installed, else the machine's: never downloaded by a test."""
    own = engine_tools.shared_engine_dir("go") / engine_tools.GO_VERSION / "go" / "bin" / engine_tools.executable_name(
        "go")
    return str(own) if own.is_file() else shutil.which("go")


@pytest.fixture(scope="module")
def recorded(tmp_path_factory):
    go = daodan_go()
    if go is None:
        pytest.skip("no Go toolchain here: Daodan's is not installed and none is on the path")
    folder = tmp_path_factory.mktemp("go-recorder")
    copy, out = write_project(folder / "copy"), folder / "out"
    out.mkdir()
    env = {**os.environ, "GOFLAGS": "", "GOPROXY": "off", "GOTOOLCHAIN": "local", "GOTELEMETRY": "off",
           "GOENV": "off", "GOWORK": "off", "GOCACHE": str(folder / "cache"), "GOPATH": str(folder / "path")}
    done = subprocess.run([go, "run", str(observer.RECORDER), str(copy), str(out / "table.json"), "."],
                          cwd=out, env=env, capture_output=True, text=True, timeout=600)
    assert done.returncode == 0, done.stderr
    done = subprocess.run([go, "test", "-vet=off", "./..."], cwd=copy, capture_output=True, text=True, timeout=600,
                          env={**env, "DAODAN_GO_RECORD": str(out / "calls.tsv")})
    assert done.returncode == 0, done.stdout + done.stderr
    return copy, out


def test_the_recorder_writes_the_table_the_reader_is_tested_with(recorded):
    _copy, out = recorded
    assert json.loads((out / "table.json").read_text(encoding="utf-8")) == TABLE


def test_the_recorder_keeps_every_line_where_it_was(recorded):
    copy, _out = recorded
    rewritten = (copy / GO).read_text(encoding="utf-8").split("\n")
    assert len(rewritten) == len(SOURCE.split("\n"))
    assert rewritten[11] == "\treturn f/*line :26:1*/(/*line :12:11*/x)"
    assert rewritten[8] == "func Double(x int) int {daodanrec.Enter(1); return x * 2 }"
    assert rewritten[0] == 'package shapes; import daodanrec "example.com/app/daodanrec"'


def test_the_recorded_run_reads_as_the_hand_written_one(recorded):
    copy, out = recorded
    sites, facts = observer.read(out, root=copy.as_posix())
    assert by_place(sites) == by_place(observer.read(observation(out / "by-hand"))[0])
    assert facts["unplaced"] == {"called from outside the modules": 1}  # the test function, started by `testing`


# ------------------------------------------------------------------ the container run

class ObserveTest(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="daodan-dynamic-go-test-"))
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

    def play_run(self, log: str = "ok  \texample.com/app/shapes\t0.031s\n", code: int = 0, **files: str):
        """What a run leaves in the recorder's folder: its table, the calls, each module's log and exit code."""
        out = observer.OUT.lstrip("/")
        calls = "".join(f"{i}\t{file}\t{line}\n" for i, file, line in CALLS)
        given = {"table.json": json.dumps(TABLE), "calls.tsv": calls, "recorder.code": "0\n", "tests-0.log": log,
                 "tests-0.code": f"{code}\n", **files}
        self.play("execute", {f"{out}/{name}": text for name, text in given.items() if text is not None})

    def observe(self, record_: dict | None = None, **options) -> dict:
        files = sorted(path.relative_to(self.project).as_posix() for path in self.project.rglob("*") if path.is_file())
        planned = observer.plan(record_ or record("."), files, None)
        if "declared" in options:  # what dynamic.run adds to every plan: the hosts the project declares
            planned["declared"] = {"hosts": options.pop("declared"), "where": {}}
        return observer.observe(self.project, planned, self.out, options.pop("engine", self.engine), **options)

    def calls(self) -> list[list[str]]:
        path = self.state / "calls.jsonl"
        return [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def created(self) -> list[list[str]]:
        return [call for call in self.calls() if call[0] == "create"]

    def script(self, phase: str) -> str:
        return (self.state / "scripts" / f"{phase}.sh").read_text(encoding="utf-8")

    def test_the_tests_run_under_the_recorder_and_their_calls_come_back_as_sites(self):
        self.play_run()
        result = self.observe()
        self.assertEqual(result["state"], "ran")
        self.assertIsNone(dynamic.malformed(result))
        self.assertEqual(by_place(result["sites"])[(GO, 11, 8, "f")], ["(func)", "Double"])
        self.assertEqual(result["gaps"], [])
        [run] = result["runs"]
        self.assertEqual((run["root"], run["runner"], run["argv"], run["state"], run["exit_code"]),
                         (".", "go test", ["go", "test", "-vet=off", "./..."], "ran", 0))
        self.assertEqual(run["packages"], {"passed": 1})
        self.assertEqual(result["facts"]["entered"], 6)

    def test_what_the_copy_of_the_project_left_out_is_a_gap_of_the_run(self):
        """A link Git tracks to outside the project stays out of the copy (`container.copy_perimeter`)."""
        left = {"kind": "link_outside", "path": "x.go", "target": "../y.go", "detail": "x.go links outside"}
        copied = container.copy_perimeter
        self.play_run()
        with mock.patch.object(container, "copy_perimeter", lambda *given: {**copied(*given), "gaps": [left]}):
            self.assertIn(left, self.observe()["gaps"])

    def test_the_preparation_reaches_the_hosts_the_project_declares(self):
        egress.respond("mirror.corp.example", str(self.project), "once")  # approved for this analysis: it opens only then
        self.play_run()
        self.observe(declared=("mirror.corp.example",))
        self.assertIn("mirror.corp.example", self.created()[1])  # after `own`: the proxy

    def test_the_dependencies_arrive_in_the_preparation_and_the_tests_run_with_no_network(self):
        self.play_run()
        self.observe()
        _owned, proxy, _tools, prepare, execute = self.created()  # `T3.A`: the copy given to 65532, the recipes as root
        for host in ("proxy.golang.org", "sum.golang.org"):
            self.assertIn(host, proxy)
        self.assertTrue(prepare[prepare.index("--network") + 1].startswith("daodan-net-"))
        self.assertEqual(execute[execute.index("--network") + 1], "none")
        prepared, executed = self.script("prepare"), self.script("execute")
        self.assertIn("export GOPROXY=off", executed)  # nothing asks the network that is not there
        self.assertNotIn("GOPROXY=off", " ".join(prepare))
        self.assertIn("go mod download", prepared)
        self.assertNotIn("go test", prepared)
        self.assertNotIn("go mod download", executed)
        self.assertLess(executed.index("go_record.go"), executed.index("daodan-go-record /work"))
        self.assertLess(executed.index("daodan-go-record /work"), executed.index("go test -vet=off ./..."))
        self.assertIn("DAODAN_GO_RECORD=$OUT/calls.tsv", executed)
        self.assertIn(f"OUT={observer.OUT}\n", executed)

    def test_the_recorder_is_carried_into_the_copy_and_the_project_is_not_changed(self):
        before = tree_digest(self.project)
        self.play_run()
        self.observe()
        self.assertEqual(tree_digest(self.project), before)
        prepare = self.created()[0]  # `own`: the copy goes in there, given to 65532
        carried = self.state / "containers" / prepare[prepare.index("--name") + 1] / "fs"
        self.assertEqual((carried / preparation.IN.lstrip("/") / "go_record.go").read_bytes(),
                         observer.RECORDER.read_bytes())
        self.assertEqual((carried / "work/shapes/shapes.go").read_text(encoding="utf-8"), SOURCE)

    def test_a_go_version_the_pre_map_states_is_installed_by_the_preparation(self):
        self.play_run()
        self.observe(record(".", toolchains=[{"tool": "go", "version": "1.22.4", "declared_in": "go.mod"},
                                             {"tool": "node", "version": "20.1.0", "declared_in": ".nvmrc"}]))
        self.assertIn("install go@1.22.4", self.script("prepare"))
        self.assertNotIn("node@", self.script("prepare"))
        self.assertIn("go.dev", self.created()[1])  # after `own`: the proxy

    def test_each_module_runs_in_its_folder_and_one_recorder_run_rewrites_them_all(self):
        write_project(self.project / "tools", {"go.mod": "module example.com/tools\n", "t.go": "package tools\n",
                                               "t_test.go": "package tools\n"})
        self.play_run(**{"tests-1.log": "ok  \texample.com/tools\t0.01s\n", "tests-1.code": "0\n"})
        result = self.observe(record(".", "tools"))
        executed = self.script("execute")
        self.assertIn("daodan-go-record /work $OUT/table.json . tools", executed)
        self.assertIn("cd /work/tools", executed)
        self.assertEqual([run["root"] for run in result["runs"]], [".", "tools"])
        self.assertIn("'.' 'tools'", self.script("prepare"))  # go mod download in each

    def test_packages_that_do_not_build_are_a_gap_with_the_compilers_words(self):
        log = ("# example.com/app/shapes [example.com/app/shapes.test]\nshapes/shapes_test.go:6:12: undefined: Totl\n"
               "FAIL\texample.com/app/shapes [build failed]\nok  \texample.com/app/other\t0.2s\nFAIL\n")
        self.play_run(log, 1)
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual((gap["kind"], gap["path"]), ("tests_not_started", "."))
        self.assertIn("undefined: Totl", gap["detail"])
        self.assertEqual(result["runs"][0]["packages"], {"passed": 1, "not_built": 1})
        self.assertEqual(result["runs"][0]["state"], "ran")  # one package's tests ran: the run is kept
        self.assertTrue(result["sites"])  # what the other packages' tests called is kept

    def test_a_module_whose_packages_all_fail_to_build_ran_no_test(self):
        self.play_run("FAIL\texample.com/app/shapes [build failed]\nFAIL\n", 1)
        result = self.observe()
        self.assertEqual((result["runs"][0]["state"], [gap["kind"] for gap in result["gaps"]]),
                         ("not_started", ["tests_not_started"]))
        self.play_run("?   \texample.com/app/shapes\t[no test files]\n", 0)
        result = self.observe()
        self.assertEqual((result["runs"][0]["state"], [gap["kind"] for gap in result["gaps"]]),
                         ("no_tests", ["no_tests"]))

    def test_files_the_recorder_gave_no_site_numbers_are_a_gap_by_cause(self):
        table = {**TABLE, "skipped": {"shapes/c.go": 'import "C": cgo prints the file again',
                                      "shapes/d.go": 'import "C": cgo prints the file again',
                                      "shapes/y.go": "line directives of its own"}}
        self.play_run(**{"table.json": json.dumps(table)})
        result = self.observe()
        self.assertEqual([(gap["kind"], gap["path"]) for gap in result["gaps"]],
                         [("sites_unrecorded", "shapes/c.go"), ("sites_unrecorded", "shapes/y.go")])
        self.assertIn('2 Go files (import "C": cgo prints the file again)', result["gaps"][0]["detail"])

    def test_failing_tests_are_said_and_what_they_called_is_kept(self):
        self.play_run("--- FAIL: TestTotal (0.00s)\nFAIL\nFAIL\texample.com/app/shapes\t0.03s\nFAIL\n", 1)
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual((gap["kind"], gap["path"]), ("tests_failed", "."))
        self.assertIn("TestTotal", gap["detail"])
        self.assertEqual((result["runs"][0]["exit_code"], result["runs"][0]["packages"]), (1, {"failed": 1}))
        self.assertEqual(result["runs"][0]["state"], "ran")
        self.assertTrue(result["sites"])

    def test_a_module_that_outlasts_its_time_is_a_gap_and_keeps_what_it_recorded(self):
        self.play_run("", 124)
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual((gap["kind"], gap["path"], result["runs"][0]["state"]), ("tests_timeout", ".", "timeout"))
        self.assertIn(str(observer.LIMIT), gap["detail"])
        self.assertTrue(result["sites"])

    def test_a_module_that_is_killed_is_said_killed_and_keeps_what_it_recorded(self):
        self.play_run("", 137)
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual((gap["kind"], gap["path"], result["runs"][0]["state"]), ("tests_killed", ".", "killed"))
        self.assertIn("memory limit", gap["detail"])
        self.assertTrue(result["sites"])

    def test_a_recorder_that_fails_is_a_gap_and_no_test_runs_unrecorded(self):
        self.play_run(**{"recorder.code": "1\n", "recorder.log": "go_record: go.mod names no module\n",
                         "tests-0.log": None, "tests-0.code": None, "calls.tsv": None, "table.json": None})
        result = self.observe()
        [gap] = result["gaps"]
        self.assertEqual(gap["kind"], "recorder_failed")
        self.assertIn("go.mod names no module", gap["detail"])
        self.assertEqual((result["sites"], result["runs"]), ([], []))
        self.assertIn('if [ "$(cat $OUT/recorder.code)" = 0 ]', self.script("execute"))

    def test_a_restore_that_fails_and_a_toolchain_that_did_not_install_are_gaps_and_the_run_goes_on(self):
        self.play("prepare", text="DAODAN-MISSING go@1.27.3\nDAODAN-RESTORE-FAILED go .\ngo: example.com/x@v1: "
                                  "reading https://proxy.golang.org: 403\nDAODAN-RESTORE-END\n")
        self.play_run()
        result = self.observe()
        self.assertEqual(sorted(gap["kind"] for gap in result["gaps"]), ["restore_failed", "toolchain_unavailable"])
        self.assertEqual(result["state"], "ran")

    def test_a_preparation_that_fails_is_failed_with_its_cause(self):
        self.play("prepare", text="tar: short read\n", code=2)
        result = self.observe()
        self.assertEqual(result["state"], "failed")
        self.assertIn("preparation exited with code 2", result["cause"])
        self.assertIn("prepare.log", result["remedy"])
        self.assertEqual((result["sites"], result["runs"]), ([], []))

    def test_without_a_container_engine_the_state_is_a_gap_with_cause_and_remedy(self):
        cause, remedy = "no container engine answers: neither docker nor podman", "start Docker or Podman"
        with mock.patch.object(container, "find_engine", side_effect=container.Gap(cause, remedy)):
            result = self.observe(engine=None)
        self.assertEqual((result["state"], result["cause"], result["remedy"]), ("gap", cause, remedy))
        self.assertEqual((result["sites"], self.created()), ([], []))

    def test_with_nothing_to_run_no_container_starts(self):
        (self.project / GO_TEST).unlink()
        result = self.observe()
        self.assertEqual((result["state"], result["sites"], result["runs"]), ("ran", [], []))
        self.assertEqual(self.calls(), [])
