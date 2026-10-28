#!/usr/bin/env python3
"""Activation-eval tooling for chat entry routing (S-6).

This script builds and validates the eval harness only. It never calls a
model and never makes a network request:

- ``--check`` loads ``cases.json`` and validates its schema: exactly 65
  objects, each matching the case schema, split 40 "task" / 10
  "vertical"+"keyword" / 15 "non-task", every id unique, every non-"non-task"
  case carrying a non-null ``expected_entry`` and every "non-task" case
  carrying a null one.
- ``--verify-results PATH`` loads a results file produced by a later,
  separately authorized step (headless runs against a disposable
  configuration, with and without the routing hooks) and computes the S-6
  targets: at least 85% of task/vertical/keyword cases invoke the expected
  entry first with the hooks, at most 10% of non-task cases invoke any entry
  with the hooks, and both figures improve on the run without the hooks.

Launching headless sessions is out of scope here; see README.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_CASES_PATH = HERE / "cases.json"

EXPECTED_TOTAL = 65
EXPECTED_TASK_COUNT = 40
EXPECTED_VERTICAL_OR_KEYWORD_COUNT = 10
EXPECTED_NON_TASK_COUNT = 15

VALID_KINDS = ("task", "vertical", "keyword", "non-task")
VALID_LANGS = ("it", "en")
REQUIRED_KEYS = frozenset({"id", "lang", "prompt", "kind", "expected_entry"})

ACCURACY_TARGET = 0.85
TRIGGER_RATE_TARGET = 0.10


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_cases(cases: Any) -> list[str]:
    """Return a list of problem descriptions; empty means the schema holds."""
    problems: list[str] = []

    if not isinstance(cases, list):
        return [f"cases.json must contain a JSON array, found {type(cases).__name__}"]

    if len(cases) != EXPECTED_TOTAL:
        problems.append(f"expected exactly {EXPECTED_TOTAL} cases, found {len(cases)}")

    seen_ids: dict[str, int] = {}
    counts = {"task": 0, "vertical": 0, "keyword": 0, "non-task": 0}

    for index, case in enumerate(cases):
        where = f"case[{index}]"
        if not isinstance(case, dict):
            problems.append(f"{where}: expected an object, found {type(case).__name__}")
            continue

        where = f"case[{index}] (id={case.get('id')!r})"

        extra_keys = set(case.keys()) - REQUIRED_KEYS
        missing_keys = REQUIRED_KEYS - set(case.keys())
        if missing_keys:
            problems.append(f"{where}: missing keys {sorted(missing_keys)}")
        if extra_keys:
            problems.append(f"{where}: unexpected keys {sorted(extra_keys)}")

        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            problems.append(f"{where}: 'id' must be a non-empty string")
        else:
            if case_id in seen_ids:
                problems.append(
                    f"{where}: duplicate id {case_id!r} (first seen at case[{seen_ids[case_id]}])"
                )
            else:
                seen_ids[case_id] = index

        lang = case.get("lang")
        if lang not in VALID_LANGS:
            problems.append(f"{where}: 'lang' must be one of {VALID_LANGS}, found {lang!r}")

        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            problems.append(f"{where}: 'prompt' must be a non-empty string")

        kind = case.get("kind")
        if kind not in VALID_KINDS:
            problems.append(f"{where}: 'kind' must be one of {VALID_KINDS}, found {kind!r}")
        elif kind in counts:
            counts[kind] += 1

        expected_entry = case.get("expected_entry")
        if kind == "non-task":
            if expected_entry is not None:
                problems.append(
                    f"{where}: 'expected_entry' must be null for a non-task case, "
                    f"found {expected_entry!r}"
                )
        elif kind in ("task", "vertical", "keyword"):
            if not isinstance(expected_entry, str) or not expected_entry:
                problems.append(
                    f"{where}: 'expected_entry' must be a non-empty string for a "
                    f"{kind!r} case, found {expected_entry!r}"
                )

    task_count = counts["task"]
    vertical_or_keyword_count = counts["vertical"] + counts["keyword"]
    non_task_count = counts["non-task"]

    if task_count != EXPECTED_TASK_COUNT:
        problems.append(
            f"expected exactly {EXPECTED_TASK_COUNT} 'task' cases, found {task_count}"
        )
    if vertical_or_keyword_count != EXPECTED_VERTICAL_OR_KEYWORD_COUNT:
        problems.append(
            f"expected exactly {EXPECTED_VERTICAL_OR_KEYWORD_COUNT} 'vertical'/'keyword' "
            f"cases, found {vertical_or_keyword_count}"
        )
    if non_task_count != EXPECTED_NON_TASK_COUNT:
        problems.append(
            f"expected exactly {EXPECTED_NON_TASK_COUNT} 'non-task' cases, found {non_task_count}"
        )

    return problems


def score_results(cases: list[dict[str, Any]], results: dict[str, Any]) -> dict[str, Any]:
    """Compute the S-6 targets from a results file against the case set.

    ``results`` has the shape ``{"with_hooks": {case_id: entry_or_null},
    "without_hooks": {...}}``. A case id absent from either mapping counts as
    no entry invoked (``None``).
    """
    with_hooks = results.get("with_hooks", {})
    without_hooks = results.get("without_hooks", {})

    positive_cases = [c for c in cases if c["kind"] != "non-task"]
    negative_cases = [c for c in cases if c["kind"] == "non-task"]

    def normalized(entry: Any) -> Any:
        # A command's expected_entry carries its host slash ("/daodan:fix-bug");
        # a Skill tool invocation never does ("daodan:fix-bug"). Compare by identity.
        return entry.lstrip("/") if isinstance(entry, str) else entry

    def accuracy(invocations: dict[str, Any]) -> float:
        if not positive_cases:
            return 0.0
        correct = sum(
            1 for c in positive_cases
            if normalized(invocations.get(c["id"])) == normalized(c["expected_entry"])
        )
        return correct / len(positive_cases)

    def trigger_rate(invocations: dict[str, Any]) -> float:
        if not negative_cases:
            return 0.0
        triggered = sum(1 for c in negative_cases if invocations.get(c["id"]) is not None)
        return triggered / len(negative_cases)

    accuracy_with = accuracy(with_hooks)
    accuracy_without = accuracy(without_hooks)
    trigger_rate_with = trigger_rate(with_hooks)
    trigger_rate_without = trigger_rate(without_hooks)

    meets_accuracy_target = accuracy_with >= ACCURACY_TARGET
    meets_trigger_rate_target = trigger_rate_with <= TRIGGER_RATE_TARGET
    better_than_baseline_accuracy = accuracy_with > accuracy_without
    better_than_baseline_trigger_rate = trigger_rate_with < trigger_rate_without

    passed = (
        meets_accuracy_target
        and meets_trigger_rate_target
        and better_than_baseline_accuracy
        and better_than_baseline_trigger_rate
    )

    return {
        "positive_total": len(positive_cases),
        "negative_total": len(negative_cases),
        "accuracy_with_hooks": accuracy_with,
        "accuracy_without_hooks": accuracy_without,
        "trigger_rate_with_hooks": trigger_rate_with,
        "trigger_rate_without_hooks": trigger_rate_without,
        "meets_accuracy_target": meets_accuracy_target,
        "meets_trigger_rate_target": meets_trigger_rate_target,
        "better_than_baseline_accuracy": better_than_baseline_accuracy,
        "better_than_baseline_trigger_rate": better_than_baseline_trigger_rate,
        "passed": passed,
    }


def format_score_report(scores: dict[str, Any]) -> str:
    def mark(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    lines = [
        f"positive cases (task+vertical+keyword): {scores['positive_total']}",
        f"negative cases (non-task): {scores['negative_total']}",
        "",
        f"accuracy with hooks:    {scores['accuracy_with_hooks']:.1%} "
        f"(target >= {ACCURACY_TARGET:.0%}) "
        f"[{mark(scores['meets_accuracy_target'])}]",
        f"accuracy without hooks: {scores['accuracy_without_hooks']:.1%}",
        f"  better than baseline: [{mark(scores['better_than_baseline_accuracy'])}]",
        "",
        f"false-trigger rate with hooks:    {scores['trigger_rate_with_hooks']:.1%} "
        f"(target <= {TRIGGER_RATE_TARGET:.0%}) "
        f"[{mark(scores['meets_trigger_rate_target'])}]",
        f"false-trigger rate without hooks: {scores['trigger_rate_without_hooks']:.1%}",
        f"  better than baseline:           [{mark(scores['better_than_baseline_trigger_rate'])}]",
        "",
        f"overall: [{mark(scores['passed'])}]",
    ]
    return "\n".join(lines)


def run_check(cases_path: Path) -> int:
    try:
        cases = load_json(cases_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not load {cases_path}: {exc}")
        return 1

    problems = validate_cases(cases)
    if problems:
        print(f"ERROR: {cases_path} failed validation:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"OK: {cases_path} has {len(cases)} valid cases")
    return 0


def run_verify_results(results_path: Path, cases_path: Path) -> int:
    try:
        cases = load_json(cases_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not load {cases_path}: {exc}")
        return 1

    problems = validate_cases(cases)
    if problems:
        print(f"ERROR: {cases_path} failed validation, cannot score results:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    try:
        results = load_json(results_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not load {results_path}: {exc}")
        return 1

    if not isinstance(results, dict) or "with_hooks" not in results or "without_hooks" not in results:
        print(
            f"ERROR: {results_path} must be a JSON object with 'with_hooks' and "
            "'without_hooks' keys"
        )
        return 1

    scores = score_results(cases, results)
    print(format_score_report(scores))
    return 0 if scores["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate cases.json's schema; calls no model, makes no network request",
    )
    parser.add_argument(
        "--verify-results",
        metavar="PATH",
        help="score a results file against the S-6 targets (read-only, no model call)",
    )
    parser.add_argument(
        "--cases",
        metavar="PATH",
        default=str(DEFAULT_CASES_PATH),
        help="path to cases.json (default: the file beside this script)",
    )
    args = parser.parse_args(argv)

    if not args.check and not args.verify_results:
        parser.error("one of --check or --verify-results is required")

    cases_path = Path(args.cases)

    if args.check:
        return run_check(cases_path)

    return run_verify_results(Path(args.verify_results), cases_path)


if __name__ == "__main__":
    sys.exit(main())
