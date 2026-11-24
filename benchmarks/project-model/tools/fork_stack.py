"""What `modal_stack.py` judges of the `stack` step by stack-analyser, as functions the container only calls: `executed`
judges the processes started, `start` pays Node's cold start outside every timing, `figures` reads what the step
passed to the tool. `benchmarks/project-model/test_fork_stack.py` tests them on this PC.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(os.environ.get("PM_PLUGIN_SCRIPTS") or
               (next((p / "daodan/core" for p in Path(__file__).resolve().parents
                      if (p / "daodan/core").is_dir()), "/daodan/map/core")))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import stack_analyser  # noqa: E402


def executed(spawned: list[str], node: str, cli: str, git: str) -> str:
    """`"no"` when each process started is the perimeter's `git` (the start of its command line) or `node` with `cli` as
    its first argument, else `"unknown"`. A process comes as one string, cut at 200 characters: the program and its
    first argument are at the start."""
    program = f"{node} {cli}"
    return "no" if all(line.startswith(git) or line == program or line.startswith(program + " ") for line in spawned) \
        else "unknown"


def figures(passed: list[dict]) -> dict:
    """`{"declarations": n, "perimeter": m}` of the first call of `stack_analyser.run` among `passed` (the keyword
    arguments of each call): the declarations sent, and the entries of the perimeter, `skip_dirs` and `ignore` together.
    Without a call, both are `None`: the step did not reach the tool."""
    if not passed:
        return {"declarations": None, "perimeter": None}
    first = passed[0]
    return {"declarations": len(first.get("declarations") or ()),
            "perimeter": len(first.get("skip_dirs") or ()) + len(first.get("ignore") or ())}


def start() -> str | None:
    """One run of the tool on an empty folder, for the cold start (Node's compile cache) to be paid outside every timing:
    None when it ran, else why it could not (cause and remedy)."""
    with tempfile.TemporaryDirectory(prefix="daodan-fork-start-") as empty:
        try:
            stack_analyser.run(Path(empty))
        except container.Gap as gap:
            return f"{gap.cause} ({gap.remedy})"
    return None
