"""What `modal_stack.py` takes from `tools/fork_stack.py` for the `stack` step by stack-analyser: the judgement of the
processes started, the cold start, the figures of what the step passed to the tool, and the pins of the driver's image
(the release and the Node the product starts) against `tests/modal_pytest.py` and `daodan/core`. The step itself is
`daodan/core/stack_recognition.py`, tested in `tests/test_codebase_map_stack_recognition.py`.

No test starts Node, reaches the network or runs Modal: `stack_analyser.run` is replaced in every one.

    python -B -m pytest -q -p no:cacheprovider benchmarks/project-model/test_fork_stack.py
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path, PurePosixPath

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE / "tools"), str(HERE), str(ROOT / "daodan/core")]

import container  # noqa: E402
import fork_stack  # noqa: E402
import stack_analyser  # noqa: E402


def component(*items, childs=()):
    return {"name": "main", "path": ["/"], "tech": None, "techs": [], "childs": list(childs), "evidence": list(items)}


# ---------------------------------------------------------------------------------------------- executed

GIT = "/usr/bin/git -c core.fsmonitor=false -c core.hooksPath=/dev/null "
NODE_BIN, CLI = "/opt/node-v24.22.3-linux-x64/bin/node", "/opt/stack-analyser/package/dist/cli.mjs"


def executed(*spawned):
    return fork_stack.executed(list(spawned), NODE_BIN, CLI, GIT)


def test_a_project_is_not_executed_when_each_process_is_the_perimeter_s_git_or_node_on_the_release():
    assert executed(GIT + "ls-files -z", f"{NODE_BIN} {CLI} /work/app --output /tmp/o.json", GIT + "rev-parse HEAD") == "no"
    assert executed(f"{NODE_BIN} {CLI}") == "no"  # no argument after the program
    assert executed() == "no"  # no process started


def test_a_process_that_is_neither_is_unknown():
    for other in ("/usr/bin/python3 setup.py build", "/usr/bin/git status", "/usr/bin/git -c core.fsmonitor=false log",
                  "/usr/bin/git -c core.hooksPath=/dev/null -c core.fsmonitor=false log", "git ls-files",
                  f"{NODE_BIN} /work/app/cli.mjs", f"{NODE_BIN} /work/app/x.js {CLI}", NODE_BIN,
                  f"{NODE_BIN} {CLI}x /work/app", f"/usr/local/bin/node {CLI} /work/app",
                  f"{NODE_BIN}-x {CLI} /work/app", f"sh -c {NODE_BIN} {CLI}"):
        assert executed(GIT + "ls-files", other) == "unknown", other


def test_the_command_of_a_real_run_is_judged_as_modal_stack_records_it():
    """`modal_stack` keeps each process as one string of at most 200 characters: a long command is cut after the cli."""
    argv = stack_analyser.command(PurePosixPath(NODE_BIN), PurePosixPath(CLI), PurePosixPath("/work/" + "d" * 150),
                                  PurePosixPath("/tmp/daodan-stack-x/output.json"), PurePosixPath("/tmp/x/declarations.json"),
                                  PurePosixPath("/tmp/daodan-stack-x/perimeter.json"))
    line = " ".join(map(str, argv))[:200]
    assert len(line) == 200 and line.startswith(f"{NODE_BIN} {CLI} /work/")
    assert executed(line) == "no"


# ---------------------------------------------------------------------------------------------- the figures

def test_the_figures_are_the_declarations_and_the_perimeter_of_the_first_call():
    first = {"declarations": [{"name": "a"}, {"name": "b"}], "skip_dirs": ("tests", "public"), "ignore": ("a/b", "c/.env.example")}
    assert fork_stack.figures([first, {"declarations": []}]) == {"declarations": 2, "perimeter": 4}


def test_a_call_without_declarations_or_perimeter_counts_zero_and_no_call_counts_none():
    assert fork_stack.figures([{}]) == {"declarations": 0, "perimeter": 0}
    assert fork_stack.figures([]) == {"declarations": None, "perimeter": None}


# ---------------------------------------------------------------------------------------------- the cold start

def test_the_tool_starts_once_on_an_empty_folder_before_any_timing(monkeypatch):
    seen = []

    def run(project, **kwargs):
        seen.append((Path(project), sorted(Path(project).iterdir()), kwargs))
        return component()

    monkeypatch.setattr(stack_analyser, "run", run)
    assert fork_stack.start() is None
    [(project, content, kwargs)] = seen
    assert content == [] and kwargs == {} and not project.exists()  # empty, with nothing sent, and gone afterwards


def test_a_tool_that_cannot_start_is_told_with_its_cause_and_remedy(monkeypatch):
    def broken(project, **kwargs):
        raise container.Gap("stack-analyser could not start: no such file", "check Node in Daodan's tool folder")

    monkeypatch.setattr(stack_analyser, "run", broken)
    assert fork_stack.start() == "stack-analyser could not start: no such file (check Node in Daodan's tool folder)"


# ---------------------------------------------------------------------------------------------- the driver's image

def constants(path, names):
    """The values of the module-level `names` of a file, read from its syntax tree: a literal, or a literal `%` a name."""
    out = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in names:
            value = node.value
            out[node.targets[0].id] = (ast.literal_eval(value.left) % out[value.right.id]
                                       if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mod)
                                       else ast.literal_eval(value))
    return out


def image_commands(path):
    """What each `run_commands` call of a file is given, as source text."""
    return {ast.unparse(argument) for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run_commands"
            for argument in node.args}


PINS = ("STACK_ANALYSER", "FETCH_STACK_ANALYSER")  # the launcher's, as they are
RUNTIME = ROOT / "daodan/core/indexers/runtime.py"


def test_the_driver_image_holds_the_release_of_the_test_launcher_and_of_daodan():
    """`tests/modal_pytest.py` cannot be imported here (it imports `modal`, and the launcher is not a module for the
    container): its pins and its commands are read from its syntax tree and must be the driver's."""
    driver, launcher = HERE / "modal_stack.py", ROOT / "tests/modal_pytest.py"
    theirs, ours = constants(launcher, PINS), constants(driver, PINS)
    assert ours == theirs
    assert theirs["STACK_ANALYSER"][:2] == (stack_analyser.URL, stack_analyser.SHA256)
    assert constants(driver, ("CLI",))["CLI"] == f"{theirs['STACK_ANALYSER'][2]}/{stack_analyser.PROGRAM}"
    assert image_commands(driver) <= image_commands(launcher)  # the same unpacking commands, the same fetch commands
    assert {"FETCH_NODE", "FETCH_STACK_ANALYSER"} <= image_commands(driver)


def test_the_driver_measures_on_the_node_the_product_starts_fetched_as_the_launcher_fetches_one():
    """The seconds are the product's on the Node it starts (`indexers.runtime.NODE_VERSION`, not the test image's),
    fetched and checked by the launcher's own command with the driver's pin; the file of `runtime` is read, not imported."""
    driver, launcher = HERE / "modal_stack.py", ROOT / "tests/modal_pytest.py"
    version = constants(RUNTIME, ("NODE_VERSION",))["NODE_VERSION"]
    ours, theirs = constants(driver, ("NODE_VERSION", "NODE", "FETCH_NODE", "NODE_BIN")), constants(launcher, ("NODE", "FETCH_NODE"))
    assert ours["NODE_VERSION"] == version
    assert ours["NODE"][0] == f"https://nodejs.org/dist/{version}/node-{version}-linux-x64.tar.gz"
    assert len(ours["NODE"][1]) == 64 and ours["NODE"] != theirs["NODE"]  # a pin of its own, a sha256
    assert ours["NODE_BIN"] == f"/opt/node-{version}-linux-x64/bin/node"  # where the tarball unpacks
    assert ours["FETCH_NODE"] == theirs["FETCH_NODE"].replace(theirs["NODE"][0], ours["NODE"][0]).replace(
        theirs["NODE"][1], ours["NODE"][1])  # the launcher's command with this pin


# ---------------------------------------------------------------------------------------------- the last round of plan 2

ROUND = HERE / "results/daodan_stack_fork.json"  # kept: the README compares the next round with it


def last_round() -> dict:
    return json.loads(ROUND.read_text(encoding="utf-8"))


def test_no_fixture_of_the_last_round_executed_project_code():
    answered = {name: entry for name, entry in last_round()["fixtures"].items() if "error" not in entry}
    assert answered and [name for name, entry in answered.items() if entry["executed_project_code"] != "no"] == []


