"""The dynamic step: observed sites joined to the snapshot's references, saved in the edge store beside the static
rows, counted apart in the coverage and read by the edge view; then the step itself, its events and its gaps.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_dynamic.py

The observation is a real one: the plugin's recorder runs the small project's own pytest suite in a child process
of this interpreter (Python 3.12+), as the container runs it. The static rows are written by hand: a store as an
analyzer leaves it, with holes where no index answers. No container starts: the step's tests give it a fake
`container.run_in_container` that plays that observation into the output folder.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import code_graph  # noqa: E402
import container  # noqa: E402
import dynamic  # noqa: E402
import edge_view  # noqa: E402
import pipeline  # noqa: E402
import resolve_edges as rx  # noqa: E402
import snapshot  # noqa: E402
from dynamic import python as observer  # noqa: E402

LIB = '''import functools


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args):
        return fn(*args)
    return wrapper


@trace
def add(a, b):
    return a + b


class Box:
    def __init__(self, v):
        self.v = v

    @property
    def twice(self):
        return self.v * 2

    def get(self):
        return self.v


def build(kind):
    return {"box": Box}[kind](3)


def apply(fn, value):
    return fn(value)


def unused():
    return add(1, 1)
'''
# The tests reach the scripts as Daodan's own do: a path put on sys.path at run time, nothing a reader resolves.
TEST = '''import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lib  # noqa: E402


def test_add():
    assert lib.add(1, 2) == 3
    box = lib.build("box")
    assert box.get() == 3 and box.twice == 6
    assert lib.apply(lambda v: v + 1, 1) == 2
    assert type(box)(4).get() == 4
'''
FILES = {"scripts/lib.py": LIB, "scripts/idle.py": "def idle():\n    return len('x')\n",
         "tests/test_lib.py": TEST, "tests/conftest.py": ""}
ADD, BOX, GET, TWICE, BUILD, APPLY = (f"scripts/lib.py::{name}" for name in (
    "function@12:0", "class@16:0", "function@24:4", "function@21:4", "function@28:0", "function@32:0"))
LAMBDA = "tests/test_lib.py::function@12:21"
STATIC = "scip-python@test"
RESOLVER = dynamic.resolver(observer)


def write_project(folder: Path, files: dict = FILES) -> tuple[Path, Path]:
    project = folder / "project"
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = folder / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return project, manifest


def recorded(project: Path, folder: Path, *command: str) -> Path:
    """The folder of the observation files of `command` (default: pytest on `tests`) run under the recorder."""
    subprocess.run([sys.executable, "-I", str(observer.RECORDER), "site", str(folder / "site")], check=True)
    out = folder / "observed"
    out.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items() if not key.startswith(("PYTHON", "DYN_"))}
    env.update(PYTHONPATH=str(folder / "site"), DYN_ROOT=str(project), DYN_OUT=str(out / "observed-0-%p.json"),
               PYTHONDONTWRITEBYTECODE="1")
    done = subprocess.run([sys.executable, *(command or ("-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"))],
                          cwd=project, env=env, capture_output=True, text=True)
    (out / "tests-0.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    assert done.returncode == 0, done.stdout + done.stderr
    return out


def static_store(manifest: Path, proven: dict | None = None) -> Path:
    """The store a static analyzer leaves: an end where `proven` names one (`{(file, line, name): end}`, an end a
    declaration id or a package), a hole at every other call and read."""
    out = rx.default_edge_store(manifest)
    with code_graph.Snapshot(manifest) as snap:
        callers = {identity: caller for identity, caller in snap.connection.execute(
            "SELECT id, caller FROM sem_references")}
        edges, holes, sites = [], [], []
        for identity, rel, kind, resolution, _target, span, parts, reason in snap.references("python"):
            place = {"reference_id": identity, "file": rel, "language": "python", "kind": kind,
                     "caller": callers[identity], "l0": span[0], "c0": span[1], "resolver": STATIC}
            sites.append({"reference_id": identity, "kind": kind, "site": f"{rel}:{span[0]}",
                          "lexical": resolution == "resolved"})
            end = (proven or {}).get((rel, span[0], parts[-1] if parts else ""))
            if end is None:
                holes.append({**place, "class": "no-occurrence", "reason": reason})
            elif "::" in end:
                edges.append({**place, "verdict": "project-callable", "target_id": end, "symbol": end,
                              "confidence": "confirmed", "external": None, "payload": {"chain": [], "detail": ""}})
            else:
                edges.append({**place, "verdict": "external", "target_id": None, "symbol": f"scip {end}",
                              "confidence": "confirmed", "payload": {"chain": [], "detail": ""},
                              "external": {"manager": "python", "package": end, "version": "3.13"}})
        files = {"snapshot": len(snap.checkout), "indexed": len(snap.checkout), "missing": []}
        coverage = rx.language_coverage(sites, edges, holes, files)
        indexer = {"name": "scip-python", "version": "test", "seconds": 0, "peak_mb": None}
        code_graph.write_store(snap, out, {}, STATIC, rows={"python": (edges, holes, coverage, indexer)})
    return out


def observed_rows(manifest: Path, sites: list[dict]) -> tuple[list[dict], dict]:
    with code_graph.Snapshot(manifest) as snap:
        edges, _binding, reason = rx.read_edge_store(rx.default_edge_store(manifest), snap.store)
        assert reason is None
        return dynamic.join(snap, "python", sites, edges, observer)


def ends(rows: list[dict], manifest: Path) -> dict:
    """`{(file, line, last name): {(verdict, target or package)}}` of observed rows."""
    with code_graph.Snapshot(manifest) as snap:
        names = {identity: (rel, span[0], parts[-1] if parts else "")
                 for identity, rel, _kind, _resolution, _target, span, parts, _reason in snap.references("python")}
    out: dict = {}
    for row in rows:
        end = row["target_id"] or (row.get("external") or {}).get("package") or row["symbol"]
        out.setdefault(names[row["reference_id"]], set()).add((row["verdict"], end))
    return out


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    folder = tmp_path_factory.mktemp("dynamic")
    project, manifest = write_project(folder)
    played = recorded(project, folder)
    return played, manifest, observer.sites(played)


def test_an_observed_site_joins_the_reference_at_the_same_name_position(case):
    """What only the run shows: a script reached through sys.path, a decorated function through its wrapper, a
    method and a property on an untyped value, a callee that is a parameter, a computed callee."""
    _played, manifest, sites = case
    static_store(manifest)
    rows, _facts = observed_rows(manifest, sites)
    assert all(row["confidence"] == "observed" and row["resolver"] == RESOLVER and row["language"] == "python"
               for row in rows)
    found = ends(rows, manifest)
    test = "tests/test_lib.py"
    assert found[(test, 9, "add")] == {("project-callable", ADD)}  # the wrapper stands for the function it wraps
    assert found[(test, 10, "build")] == {("project-callable", BUILD)}
    assert found[(test, 11, "get")] == {("project-callable", GET)}
    assert found[(test, 11, "twice")] == {("project-callable", TWICE)}  # a read that runs a property
    assert found[(test, 13, "")] == {("project-callable", BOX)}  # type(box)(4): a class called is its class
    assert found[("scripts/lib.py", 29, "")] == {("project-callable", BOX)}
    assert found[("scripts/lib.py", 33, "fn")] == {("project-callable", LAMBDA)}
    assert found[(test, 4, "str")] == {("external", "python-stdlib")}
    [wrapped] = [row for row in rows if row["target_id"] == ADD and row["file"] == test]
    assert wrapped["payload"]["chain"] == ["wraps"] and "wrapper" in wrapped["payload"]["detail"]
    [outside] = [row for row in rows if row["file"] == test and row["l0"] == 4 and row["symbol"].endswith(".str")]
    assert outside["external"]["manager"] == "python" and outside["external"]["version"].startswith("3.")


def test_the_join_says_what_it_did_not_place_and_what_no_test_executed(case):
    _played, manifest, sites = case
    static_store(manifest)
    _rows, facts = observed_rows(manifest, sites)
    assert facts["recorded"] == len(sites) and facts["joined"] > 0
    # implicit calls have no reference in the snapshot: counted by how they are reached, never dropped in silence
    assert facts["unjoined"]["BINARY_OP"] >= 1 and sum(facts["unjoined"].values()) + facts["placed"] == len(sites)
    assert facts["files"] == {"executed": 2, "not_executed": ["scripts/idle.py"]}  # a file with calls, never run


def test_an_observed_edge_agrees_with_a_proven_one_or_is_a_conflict_never_a_choice(case):
    _played, manifest, sites = case
    test = "tests/test_lib.py"
    static_store(manifest, {(test, 9, "add"): ADD, (test, 10, "build"): APPLY, (test, 4, "str"): "python-stdlib",
                            (test, 11, "get"): "requests"})
    rows, facts = observed_rows(manifest, sites)
    assert facts["agree"] == 2 and facts["conflicts"]["count"] == 2
    by_site = {example["site"]: example for example in facts["conflicts"]["examples"]}
    assert by_site[f"{test}:10 build"] == {"site": f"{test}:10 build", "proven": [APPLY], "observed": [BUILD]}
    assert by_site[f"{test}:11 get"]["proven"] == ["requests"] and by_site[f"{test}:11 get"]["observed"] == [GET]
    flagged = {(row["l0"], row["target_id"]) for row in rows if row["payload"].get("conflict")}
    assert flagged == {(10, BUILD), (11, GET)}


def test_the_store_keeps_observed_edges_apart_and_closes_the_holes_they_answer(case):
    _played, manifest, sites = case
    test = "tests/test_lib.py"
    out = static_store(manifest, {(test, 9, "add"): ADD, (test, 4, "str"): "python-stdlib"})
    with code_graph.Snapshot(manifest) as snap:
        _edges, binding, _reason = rx.read_edge_store(out, snap.store)
        before = binding["languages"]["python"]["coverage"]
        assert "observed" not in before and "observed" not in before["answered"]
        rows, facts = observed_rows(manifest, sites)
        for _again in range(2):  # a second observation takes the place of the first
            coverage = code_graph.write_observed(snap, out, "python", rows, {"resolver": RESOLVER, **facts})
        edges, binding, reason = rx.read_edge_store(out, snap.store)
        assert reason is None and binding["languages"]["python"]["coverage"] == coverage
    holes = rx.read_edge_holes(out)
    assert len([edge for edge in edges if edge["confidence"] == "observed"]) == len(rows)
    assert len(holes) == sum(hole["count"] for hole in before["holes"].values()) + before["answered"]["lexical"]
    closed = coverage["observed"]["closed"]["no-occurrence"]
    assert closed >= 6 and coverage["answered"]["observed"] == closed
    # the static numbers stay comparable: what the analyzer answered is counted as before
    assert {key: value for key, value in coverage["answered"].items() if key != "observed"} == before["answered"]
    assert coverage["holes"]["no-occurrence"]["count"] == before["holes"]["no-occurrence"]["count"] - closed
    assert coverage["sites"] == before["sites"] == sum(coverage["answered"].values()) + sum(
        hole["count"] for hole in coverage["holes"].values())
    assert coverage["observed"]["sites"] == facts["joined"] and coverage["observed"]["edges"] == len(rows)
    assert coverage["observed"]["resolver"] == RESOLVER and coverage["observed"]["files"] == facts["files"]
    assert coverage["state"] == "lower-bound"  # holes are left


def test_the_edge_view_answers_with_an_observed_edge_only_where_nothing_proven_does(case):
    _played, manifest, sites = case
    test = "tests/test_lib.py"
    out = static_store(manifest, {(test, 10, "build"): APPLY})
    with code_graph.Snapshot(manifest) as snap:
        rows, facts = observed_rows(manifest, sites)
        code_graph.write_observed(snap, out, "python", rows, {"resolver": RESOLVER, **facts})
    view = edge_view.load_edge_view(manifest)
    assert view["coverage"]["status"] == "lower-bound" and not view["gaps"]
    calls = {(record["file"], record["span"][0], (record.get("parts") or [""])[-1]): record
             for record in view["references"]}
    reached = calls[(test, 11, "get")]
    assert (reached["target_id"], reached["confidence"], reached["provenance"]) == (GET, "observed", [RESOLVER])
    assert reached["hole"] == "no-occurrence"  # what the static step could not answer stays said
    assert calls[(test, 10, "build")]["target_id"] == APPLY  # the proven edge stands, the conflict is reported
    assert calls[(test, 10, "build")]["confidence"] == "confirmed"
    read = next(record for record in view["reads"] if record["file"] == test and record["span"][0] == 11)
    assert (read["target_id"], read["confidence"]) == (TWICE, "observed")
    lexical = next(record for record in view["reads"] if record["file"] == "scripts/lib.py"
                   and record["span"][0] == 8)  # `return wrapper`, resolved lexically
    assert lexical["confidence"] == "confirmed" and lexical["resolver"] != RESOLVER


def test_a_mock_is_not_a_destination(tmp_path):
    files = {"lib.py": "def real():\n    return 1\n\n\ndef call():\n    return real()\n",
             "test_lib.py": "from unittest import mock\n\nimport lib\n\n\ndef test_call():\n"
                            "    with mock.patch.object(lib, 'real') as fake:\n        lib.call()\n"
                            "    assert fake.called\n",
             "conftest.py": ""}
    project, manifest = write_project(tmp_path, files)
    sites = observer.sites(recorded(project, tmp_path, "-m", "pytest", "-q", "-p", "no:cacheprovider"))
    static_store(manifest)
    rows, facts = observed_rows(manifest, sites)
    assert ("lib.py", 6, "real") not in ends(rows, manifest) and facts["mocked"] == 1


# ------------------------------------------------------------------ sampled pairs

SAMPLED_LIB = '''def one(box):
    return 1


class Box:
    def get(self):
        return 1

    def put(self, fn):
        return fn(self)


def use(box):
    return box.get() + box.put(one)


def twice(box):
    return box.get() + box.get()
'''
AT = {name: f"lib.py::function@{at}" for name, at in (("one", "1:0"), ("get", "6:4"), ("put", "9:4"),
                                                         ("use", "13:0"), ("twice", "17:0"))}


def frame(name: str, line: int, column: int | None = 0) -> dict:
    """A function of lib.py as a profiler's frame names it: its line from 0, its column when the profiler has it."""
    return {"kind": "project", "file": "lib.py", "line": line, "column": column, "name": name, "type": "function"}


# What a profiler gives: caller and callee of one stack, with the line of the call when it has it.
PAIRS = [{"caller": frame("use", 12), "callee": frame("get", 5, 4), "line": 13},
         {"caller": frame("use", 12, None), "callee": frame("put", 8, None), "line": 13},
         {"caller": frame("put", 8, 4), "callee": frame("one", 0), "line": 9},  # through a parameter: `fn`
         {"caller": frame("twice", 16), "callee": frame("get", 5, 4), "line": 17},  # two calls of `get` there
         {"caller": frame("twice", 16), "callee": frame("get", 5, 4), "line": None}]
SAMPLER = dynamic.resolver(observer, sampled=True)


def test_a_sampled_pair_closes_the_hole_of_the_one_call_its_line_names_else_joins_two_declarations(tmp_path):
    """A pair is placed on the call of its line in the caller with the callee's name when there is one only; else
    it is an edge between the two declarations that answers no reference. Where the exact recorder saw the same
    call, the exact end closes the hole; the two are counted apart."""
    _project, manifest = write_project(tmp_path, {"lib.py": SAMPLED_LIB})
    out = static_store(manifest)
    exact = [{"file": "lib.py", "line": 13, "column": 15, "name": "get", "role": "call",
              "callees": [frame("get", 5, 4)]}]
    with code_graph.Snapshot(manifest) as snap:
        edges, _binding, _reason = rx.read_edge_store(out, snap.store)
        rows, facts = dynamic.join(snap, "python", exact, edges, observer)
        sampled, said = dynamic.join_sampled(snap, "python", PAIRS, observer)
        assert SAMPLER != RESOLVER and all(row["confidence"] == "sampled" and row["resolver"] == SAMPLER
                                           for row in sampled)
        assert {(row["l0"], row["target_id"]) for row in sampled if row["reference_id"]} == {
            (14, AT["get"]), (14, AT["put"])}
        assert {(row["caller"], row["l0"], row["target_id"], row["payload"]["unplaced"]) for row in sampled
                if row["reference_id"] is None} == {(AT["put"], 10, AT["one"], "not-found"),
                                                    (AT["twice"], 18, AT["get"], "ambiguous"),
                                                    (AT["twice"], None, AT["get"], "no-line")}
        assert said == {"pairs": 5, "placed": 2, "unplaced": {"ambiguous": 1, "no-line": 1, "not-found": 1}}
        coverage = code_graph.write_observed(snap, out, "python", rows + sampled,
                                             {"resolver": RESOLVER, **facts, "sampled": {"resolver": SAMPLER, **said}})
    assert (coverage["answered"]["observed"], coverage["answered"]["sampled"]) == (1, 1)
    assert coverage["observed"]["closed"] == coverage["sampled"]["closed"] == {"no-occurrence": 1}
    assert (coverage["sampled"]["sites"], coverage["sampled"]["edges"]) == (2, 5)
    assert coverage["sampled"]["resolver"] == SAMPLER and coverage["sampled"]["pairs"] == 5
    assert coverage["sites"] == sum(coverage["answered"].values()) + sum(
        hole["count"] for hole in coverage["holes"].values())
    view = edge_view.load_edge_view(manifest)
    calls = {(record["file"], record["span"][0], (record.get("parts") or [""])[-1]): record
             for record in view["references"]}
    assert (calls[("lib.py", 14, "get")]["target_id"], calls[("lib.py", 14, "get")]["confidence"]) == (
        AT["get"], "observed")  # the exact end first
    put = calls[("lib.py", 14, "put")]
    assert (put["target_id"], put["confidence"], put["provenance"]) == (AT["put"], "sampled", [SAMPLER])
    assert calls[("lib.py", 10, "fn")]["target_id"] is None  # an edge between declarations answers no call


# ------------------------------------------------------------------ the step

class Container:
    """The fake `container.run_in_container`: it plays the recorded run's outputs into the output folder."""

    def __init__(self, played: Path, prepare: str = ""):
        self.played, self.prepare, self.calls = played, prepare, []

    def __call__(self, project, command, **given):
        self.calls.append({"project": project, "command": command, **given})
        out_dir = Path(given["out_dir"])
        shutil.copytree(self.played, out_dir / "out", dirs_exist_ok=True)
        (out_dir / "prepare.log").write_text(self.prepare, encoding="utf-8")
        (out_dir / "execute.log").write_text("DAODAN-DYNAMIC 0 python 3.13.18 1\nDAODAN-DYNAMIC 0 exit 0 7\n",
                                             encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": []}


def step(manifest: Path, box=None, engine=container.Engine("fake", ("fake",))) -> tuple[dict, list[dict], mock.Mock]:
    """The dynamic step alone, with `box` as the container (none may start without one) and `engine` found."""
    seen: list[dict] = []
    bus = pipeline.events.Bus()
    bus.subscribe(seen.append)
    box = box or mock.Mock(side_effect=AssertionError("a container started"))
    found = {"side_effect": engine} if isinstance(engine, Exception) else {"return_value": engine}
    with mock.patch.object(container, "find_engine", **found) as asked, \
            mock.patch.object(container, "run_in_container", side_effect=box):
        result = pipeline.Dynamic.run(pipeline.Context(manifest, bus))
    return result, seen, asked


def gaps(seen: list[dict], kind: str) -> list[dict]:
    return [event["data"]["gap"] for event in seen if event["kind"] == "gap" and event["data"]["gap"]["kind"] == kind]


def test_the_step_runs_the_declared_tests_in_the_container_and_saves_what_they_call(case):
    """The owner's example: nothing calls the scripts statically, the tests reach them through sys.path at run
    time, and after the step the script's functions are reached from the test by observed edges."""
    played, manifest, _sites = case
    out = static_store(manifest)
    box = Container(played, prepare=f"DAODAN-DYNAMIC 0 brought pytest {observer.PYTEST}\n")
    result, seen, asked = step(manifest, box)
    assert asked.call_count == 1 and len(box.calls) == 1
    [call] = box.calls
    assert call["out_dir"] == manifest.parent / dynamic.RUNS / observer.ENTRY  # beside the manifest
    assert "run 0 . " in call["command"][2] and call["command"][2].count("-m pytest tests") == 1
    python = result["languages"]["python"]
    assert python["state"] == "observed" and python["edges"] > 0 and python["closed"] >= 6
    kinds = [(event["kind"], event["analyzer"]) for event in seen if event["kind"].startswith("analyzer.")]
    assert kinds == [("analyzer.started", observer.ENTRY), ("analyzer.finished", observer.ENTRY)]
    assert {event["step"] for event in seen} == {"dynamic"}
    assert {event["data"].get("phase") for event in seen if event["kind"] == "progress"} >= {"plan", "tests", "join"}
    assert [event["data"]["gap"]["kind"] for event in seen if event["kind"] == "gap"] == ["runner_brought"]
    with code_graph.Snapshot(manifest) as snap:
        edges, binding, reason = rx.read_edge_store(out, snap.store)
    assert reason is None
    reached = {(edge["file"], edge["target_id"]) for edge in edges if edge["confidence"] == "observed"}
    assert {("tests/test_lib.py", ADD), ("tests/test_lib.py", BUILD), ("tests/test_lib.py", GET)} <= reached
    stored = binding["languages"]["python"]["coverage"]["observed"]
    assert stored["resolver"] == RESOLVER and stored["edges"] == python["edges"]
    assert [(test["root"], test["runner"], test["state"], test["python"]) for test in stored["tests"]] == [
        (".", "pytest", "ran", "3.13.18")]
    # an observation holds for its snapshot: the same store is not observed twice
    again, seen, asked = step(manifest)
    assert asked.call_count == 0 and again["languages"]["python"] == python
    assert [event["data"].get("fresh") for event in seen if event["kind"] == "analyzer.finished"] == [True]


def test_without_a_container_engine_the_step_states_the_gap_and_the_pipeline_goes_on(case):
    _played, manifest, _sites = case
    out = static_store(manifest)
    refused = container.Gap("no container engine answers: neither docker nor podman", "start Docker or Podman")
    result, seen, asked = step(manifest, engine=refused)
    assert asked.call_count == 1
    [event] = [event for event in seen if event["kind"] == "analyzer.unavailable"]
    assert event["level"] == "warning" and refused.cause in event["data"]["cause"]
    assert event["data"]["remedy"] == refused.remedy and event["analyzer"] == observer.ENTRY
    assert result["languages"]["python"]["state"] == "unavailable"
    with code_graph.Snapshot(manifest) as snap:
        edges, _binding, _reason = rx.read_edge_store(out, snap.store)
    assert not [edge for edge in edges if edge["confidence"] == "observed"]
    seen = []
    bus = pipeline.events.Bus()
    bus.subscribe(seen.append)
    context = pipeline.Context(manifest, bus)
    context.results["dynamic"] = result
    pipeline.Union.run(context)
    [gap] = gaps(seen, "not-observed")
    assert refused.cause in gap["detail"]  # the union says the graph is static only, and why


def test_a_project_that_declares_no_test_command_is_a_gap_and_no_container_starts(tmp_path):
    _project, manifest = write_project(tmp_path, {"lib.py": "def f():\n    return len('x')\n",
                                                  "test_lib.py": "import lib\n\n\ndef test_f():\n    lib.f()\n"})
    static_store(manifest)
    result, seen, asked = step(manifest)
    assert asked.call_count == 0
    assert len(gaps(seen, "no_test_command")) == 1 and result["languages"]["python"]["state"] == "not-run"


def test_a_language_with_a_graph_and_no_observer_is_a_gap(case):
    _played, manifest, _sites = case
    static_store(manifest)
    with mock.patch.object(dynamic, "observers", return_value=[]):
        result, seen, asked = step(manifest)
    [gap] = gaps(seen, "no-observer")
    assert gap["language"] == "python" and asked.call_count == 0
    assert result["languages"]["python"]["state"] == "no-observer"


def test_observed_edges_need_the_static_graph_they_answer(tmp_path):
    _project, manifest = write_project(tmp_path)
    result, seen, asked = step(manifest)  # no analyzer has written python's graph
    [gap] = gaps(seen, "no-static-graph")
    assert gap["language"] == "python" and asked.call_count == 0
    assert result["languages"]["python"]["state"] == "no-static-graph"


def test_the_step_is_skipped_when_it_is_switched_off(case, monkeypatch):
    _played, manifest, _sites = case
    static_store(manifest)
    monkeypatch.setenv("DAODAN_DYNAMIC", "off")
    result, seen, asked = step(manifest)
    assert asked.call_count == 0 and [event["kind"] for event in seen] == ["gap"]
    assert "DAODAN_DYNAMIC=off" in seen[0]["message"] and result["languages"] == {}


def test_the_union_says_what_was_observed_and_what_stayed_unobserved(case):
    played, manifest, _sites = case
    static_store(manifest, {("tests/test_lib.py", 10, "build"): APPLY})
    result, _seen, _asked = step(manifest, Container(played))
    seen = []
    bus = pipeline.events.Bus()
    bus.subscribe(seen.append)
    union = pipeline.Union.run(pipeline.Context(manifest, bus))
    assert not gaps(seen, "not-observed")
    [said] = [event for event in seen if event["kind"] == "log"]
    python = result["languages"]["python"]
    assert said["message"] == f"python: {python['sites']} sites observed in a run, {python['closed']} holes closed"
    [files] = gaps(seen, "files-not-executed")
    assert files["files"] == ["scripts/idle.py"] and "scripts/idle.py" in files["detail"]
    [conflict] = gaps(seen, "observed-conflict")
    assert conflict["count"] == 1 and conflict["examples"][0]["site"] == "tests/test_lib.py:10 build"
    assert union["languages"]["python"]["coverage"]["observed"]["edges"] == python["edges"]
    assert seen[-1]["kind"] == "graph.ready"


def test_a_profiler_alone_gives_sampled_edges_and_no_claim_on_what_it_did_not_see(tmp_path):
    """An observer whose run returns sampled pairs and no exact site: its edges are counted apart, and nothing is
    said of the files no sample named."""
    _project, manifest = write_project(tmp_path, {"lib.py": SAMPLED_LIB})
    static_store(manifest)
    ran = [{"root": ".", "runner": "pytest", "declared_in": "conftest.py", "state": "ran"}]
    sampler = SimpleNamespace(ENTRY="dynamic-sample-python", VERSION="1", LANGUAGES=("python",),
                              external=observer.external, plan=lambda record, files, read: {"runs": ran, "gaps": []},
                              observe=lambda project, planned, out_dir, engine: {
                                  "state": "ran", "sites": [], "sampled": PAIRS, "runs": ran, "gaps": []})
    with mock.patch.object(dynamic, "observers", return_value=[sampler]):
        result, seen, asked = step(manifest)
    assert asked.call_count == 1
    assert result["languages"]["python"] == {"state": "observed", "sites": 0, "edges": 0, "closed": 0,
                                             "sampled": {"sites": 2, "edges": 5, "closed": 2}}
    seen = []
    bus = pipeline.events.Bus()
    bus.subscribe(seen.append)
    context = pipeline.Context(manifest, bus)
    context.results["dynamic"] = result
    union = pipeline.Union.run(context)
    assert not gaps(seen, "not-observed") and not gaps(seen, "files-not-executed")
    [said] = [event for event in seen if event["kind"] == "log"]
    assert said["message"] == "python: 2 sites and 5 edges sampled in a run, 2 holes closed"
    assert said["data"]["resolver"] == "dynamic-sample-python@1:sampled"
    assert "files" not in union["languages"]["python"]["coverage"]["observed"]
