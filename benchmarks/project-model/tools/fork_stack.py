"""The measures of the `stack` step by stack-analyser, as functions the container only calls: the step itself is
`stack_recognition.run`, which the benchmark puts where `service_registry.run` stood. `measure` takes one project's
two records and its fast scan, `compare` sets the two records side by side against `expected.json`, `executed` judges the processes
started, `summary` gives the totals. `benchmarks/project-model/test_fork_stack.py` tests them on this PC.
"""
from __future__ import annotations

import os
import statistics
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

SCRIPTS = Path(os.environ.get("PM_PLUGIN_SCRIPTS") or
               (next((p / "daodan/core" for p in Path(__file__).resolve().parents
                      if (p / "daodan/core").is_dir()), "/daodan/map/core")))
PROJECT_MODEL = Path(__file__).resolve().parents[1]  # `score.py`
for _path in (SCRIPTS, PROJECT_MODEL):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import container  # noqa: E402
import score  # noqa: E402
import service_registry  # noqa: E402
import stack_analyser  # noqa: E402
import stack_recognition  # noqa: E402
import technologies  # noqa: E402


# ---------------------------------------------------------------------------------------------- the measures

def _found_names(expected: dict, record: dict) -> dict[str, dict[str, str]]:
    """Per facet, the names `expected` lists that `score.score_technologies` finds in `record`, by the score's own
    spelling (`score._framework`: its aliases) with the first spelling `expected` gives: the frameworks by name alone, as
    its `frameworks_by_name` counts them (a framework in two units is one name)."""
    scored = score.score_technologies(expected, record)
    found = {}
    for facet, key in (("frameworks", "frameworks_by_name"), ("services", "services")):
        if key in scored:  # the expected file's `unknown` takes a facet out
            missed = set(scored[key]["missed"])  # spelt as the score spells them
            found[facet] = {}
            for item in expected.get(facet) or ():
                label = score._framework(item["name"])
                if label not in missed:
                    found[facet].setdefault(label, item["name"])
    return found


def _only(here: dict, there: dict) -> list[str]:
    """The names found in `here` and not in `there`: each once per facet, sorted, the frameworks first."""
    return [name for facet in ("frameworks", "services")
            for name in sorted(n for label, n in here.get(facet, {}).items() if label not in there.get(facet, {}))]


def compare(expected: dict, before: dict, after: dict) -> dict:
    """The record `before` (the registry's) and `after` (the fork's, with its `gaps`), in the form
    `score.score_technologies` takes, against each other: the expected names found only before (`lost`) or only after
    (`gained`), the ids of `technologies` only after (`new`) or only before (`gone`), and the ids the fork named that
    the registry lacks (`not_in_registry`)."""
    names_before, names_after = _found_names(expected, before), _found_names(expected, after)
    ids_before, ids_after = ({t["id"] for t in record["technologies"]} for record in (before, after))
    gaps = after.get("gaps") or ()
    return {"lost": _only(names_before, names_after), "gained": _only(names_after, names_before),
            "new": sorted(ids_after - ids_before), "gone": sorted(ids_before - ids_after),
            "not_in_registry": sorted({gap["entry"] for gap in gaps if gap.get("kind") == "not_in_registry"})}


def executed(spawned: list[str], node: str, cli: str, git: str) -> str:
    """`"no"` when each process started is the perimeter's `git` (the start of its command line) or `node` with `cli` as
    its first argument, else `"unknown"`. A process comes as one string, cut at 200 characters: the program and its
    first argument are at the start."""
    program = f"{node} {cli}"
    return "no" if all(line.startswith(git) or line == program or line.startswith(program + " ") for line in spawned) \
        else "unknown"


def _timed(function, *args) -> tuple[dict, float]:
    started = time.monotonic()
    answer = function(*args)
    return answer, round(time.monotonic() - started, 3)


def _declared(answer: dict) -> set[str]:
    """The ids of the entries with a declared sign: the ones `technologies.derive` keeps, the others it leaves mentioned."""
    return {entry["id"] for entry in answer["found"] if any(s["strength"] == "declared" for s in entry["signs"])}


def measure(manifest: Path, registry: dict, full: dict, fast: dict) -> dict:
    """One project, two ways. `technologies.derive` on the pre-map's facts `full` with the registry's recogniser and with
    the fork's (`service_registry.run` replaced by `stack_recognition.run`), and each recogniser alone on the facts `fast` (the
    pre-map without its model commands), compared by the ids each declares; the seconds are each call's. `derive` makes
    the module graph the first time and finds it the second, so one derive, not timed, comes first: the graph is
    already there under both. `fast_gaps` are the fork's gaps of the fast scan, as `after["gaps"]` are of the full one."""
    manifest = Path(manifest)
    technologies.derive(manifest, registry, full)
    before, registry_full = _timed(technologies.derive, manifest, registry, full)
    with mock.patch.object(service_registry, "run", stack_recognition.run):
        after, fork_full = _timed(technologies.derive, manifest, registry, full)
    by_registry, registry_fast = _timed(service_registry.run, manifest, registry, fast)
    by_fork, fork_fast = _timed(stack_recognition.run, manifest, registry, fast)
    ours, theirs = _declared(by_registry), _declared(by_fork)
    return {"before": before, "after": after,
            "fast": {"registry": sorted(ours), "fork": sorted(theirs), "lost": sorted(ours - theirs)},
            "fast_gaps": by_fork["gaps"],
            "seconds": {"registry_full": registry_full, "fork_full": fork_full, "registry_fast": registry_fast,
                        "fork_fast": fork_fast}}


def fork_gaps(gaps: list[dict]) -> dict:
    """The fork's gaps of one scan: their count by kind, and the cause of each run of the tool that failed (`stack_recognition.run`'s
    `checker_failed` of `stack-analyser`; the host checker's failure is the registry's too, and is not one)."""
    kinds = {}
    for gap in gaps:
        kinds[gap["kind"]] = kinds.get(gap["kind"], 0) + 1
    return {"kinds": dict(sorted(kinds.items())),
            "failed": [gap["detail"] for gap in gaps if gap["kind"] == "checker_failed" and gap.get("checker") == "stack-analyser"]}


def fixture_result(expected: dict, stored: dict, node: str, cli: str, git: str) -> dict:
    """One fixture's entry of the results file from what the container stored (`before`, `after` with its gaps, `fast`,
    `fast_gaps`, `seconds`, `spawned`, `model`). A fixture whose run of the tool failed, in either scan, is flagged
    `fork_failed`: its comparison is that of a fork that found nothing, not a loss, and its seconds are not a speed."""
    before, after = stored["before"], stored["after"]
    gaps = {"full": fork_gaps(after["gaps"]), "fast": fork_gaps(stored["fast_gaps"])}
    return {"compare": compare(expected, before, after), "fast": stored["fast"], "seconds": stored["seconds"],
            "executed_project_code": executed(stored["spawned"], node, cli, git),
            "score": {"before": score.score_technologies(expected, before), "after": score.score_technologies(expected, after)},
            "fork_gaps": gaps, "fork_failed": bool(gaps["full"]["failed"] or gaps["fast"]["failed"]),
            "model": stored["model"], "model_missing": stored["model_missing"], "spawned": sorted(set(stored["spawned"]))}


def start() -> str | None:
    """One run of the tool on an empty folder, for the cold start (Node's compile cache) to be paid outside every timing:
    None when it ran, else why it could not (cause and remedy)."""
    with tempfile.TemporaryDirectory(prefix="daodan-fork-start-") as empty:
        try:
            stack_analyser.run(Path(empty))
        except container.Gap as gap:
            return f"{gap.cause} ({gap.remedy})"
    return None


def _spread(fixtures: dict, key: str) -> dict:
    times = {name: entry["seconds"][key] for name, entry in fixtures.items() if "seconds" in entry}
    slowest = max(times, key=times.get, default=None)
    return {"median": round(statistics.median(times.values()), 3) if times else None,
            "max": times.get(slowest), "slowest": slowest}


def summary(fixtures: dict) -> dict:
    """The totals over the fixtures `fetch` writes (name -> `{"error": ...}`, or the result with its `compare`, its
    `seconds` and the `score` of each record): the expected names found before and after, the fixtures that lose some,
    the spread of the fast scans. A fixture whose run of the tool failed (`fork_failed`) is named apart and is left out of
    what measures the fork: the names found, the losses and the fork's seconds; the registry's seconds on it stay."""
    failed = sorted(name for name, entry in fixtures.items() if entry.get("fork_failed"))
    run = {name: entry for name, entry in fixtures.items() if name not in failed}
    found = {}
    for facet, key in (("frameworks", "frameworks_by_name"), ("services", "services")):
        row = {"expected": 0, "before": 0, "after": 0}
        for entry in run.values():
            scores = entry.get("score")
            if scores and key in scores["before"]:
                row["expected"] += scores["before"][key]["expected"]
                row["before"] += scores["before"][key].get("found", 0)
                row["after"] += scores["after"][key].get("found", 0)
        found[facet] = row
    return {"fixtures": len(fixtures), "errors": sum("error" in entry for entry in fixtures.values()),
            "fixtures_with_lost": sum(bool(entry.get("compare", {}).get("lost")) for entry in run.values()),
            "fork_failed": {"count": len(failed), "fixtures": failed},
            "found": found, "fork_fast": _spread(run, "fork_fast"), "registry_fast": _spread(fixtures, "registry_fast")}
