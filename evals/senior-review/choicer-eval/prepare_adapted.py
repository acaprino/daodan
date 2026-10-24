"""Freeze the separately authorized, outcome-blind adapted Julia experiment."""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from run_eval import (
    BASE, REPO, confined, digest, initialize, prepare, read_json, reviewer_roles,
    write_json,
)


def adapted_catalog(catalog: dict, adaptation: dict) -> dict:
    """Bind edits to their exact original strings, never to labels or predictions."""
    original = {role["id"]: role for role in reviewer_roles(catalog)}
    edits = adaptation["reviewers"]
    if len(edits) != len(original) or {edit["id"] for edit in edits} != set(original):
        raise ValueError("Adaptation must cover each original reviewer exactly once")
    result = copy.deepcopy(catalog)
    by_id = {role["id"]: role for role in result["roles"]}
    for edit in edits:
        role = original[edit["id"]]
        if edit["original"] != {
            "true": role["trigger_when"], "false": role["do_not_trigger_when"],
        }:
            raise ValueError(f"Adaptation is not bound to the original criteria: {edit['id']}")
        values = edit["adapted"]
        if any(not isinstance(values.get(side), str) or not values[side].strip() for side in ("true", "false")):
            raise ValueError(f"Incomplete binary criteria: {edit['id']}")
        if not isinstance(edit.get("choice_description"), str) or not edit["choice_description"].strip():
            raise ValueError(f"Missing compact choice description: {edit['id']}")
        target = by_id[edit["id"]]
        target["trigger_when"] = values["true"]
        target["do_not_trigger_when"] = values["false"]
        target["choice_description"] = edit["choice_description"]
        target["adaptation"] = copy.deepcopy(edit)
    result["adaptation"] = {
        "kind": "Separately authored criteria and compact choice descriptions",
        "equivalent_to_original_catalog": False,
        "source": "adapted_reviewers.json",
        "original_extraction_provenance_retained": True,
    }
    return result


def context_subset(dataset: dict, capacity: dict) -> tuple[dict, list[dict]]:
    """Exclude whole cases with state-only overflow, before adapted inference."""
    hunks = {(case["id"], hunk["id"]) for case in dataset["cases"] for hunk in case["hunks"]}
    rows = capacity["hunks"]
    if len(rows) != len(hunks) or {(row["case_id"], row["hunk_id"]) for row in rows} != hunks:
        raise ValueError("Capacity evidence does not cover every original hunk exactly once")
    excluded = [row for row in rows if row["state_alone_exceeds_sequence_limit"]]
    excluded_ids = {row["case_id"] for row in excluded}
    result = copy.deepcopy(dataset)
    result["cases"] = [case for case in result["cases"] if case["id"] not in excluded_ids]
    result["adapted_subset"] = {
        "rule": "Exclude an entire case if any original state alone exceeds Julia's sequence limit.",
        "selection_uses_labels_or_predictions": False,
        "original_case_count": len(dataset["cases"]),
        "excluded_case_ids": sorted(excluded_ids),
        "overflow_evidence": excluded,
        "remaining_hunks_rewritten": False,
        "full_question_encoding_still_required": True,
    }
    return result, excluded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--adaptation", default="adapted_reviewers.json")
    args = parser.parse_args()
    source, target = confined(args.source_run), confined(args.run_dir)
    if target == source or not target.is_relative_to(BASE / "runs") or target == BASE / "runs":
        parser.error("Use a distinct child of the benchmark runs directory")
    if any((target / "results").rglob("*.json")):
        parser.error("This adapted run already has results; use a new run directory")
    adaptation_path = confined(args.adaptation)
    capacity_path = source / "execution/julia-state-capacity.json"
    adaptation = read_json(adaptation_path)
    catalog = adapted_catalog(read_json(source / "catalog.json"), adaptation)
    dataset, excluded = context_subset(read_json(source / "dataset.json"), read_json(capacity_path))
    for name, value in (
        ("catalog.json", catalog), ("dataset.json", dataset),
        ("prompts.json", read_json(source / "prompts.json")),
        ("adapted_reviewers.json", adaptation),
    ):
        write_json(target / name, value, freeze=True)
    metadata = initialize(target)
    metadata.update(
        experiment="Adapted Julia criteria on fully context-compatible cases",
        parent_run=source.relative_to(REPO).as_posix(),
        original_catalog_comparison="Exploratory reference only; no same-catalog A baseline was executed.",
        adaptation={
            "artifact_sha256": digest(adaptation_path.read_bytes()),
            "capacity_evidence_sha256": digest(capacity_path.read_bytes()),
            "capacity_evidence": capacity_path.relative_to(REPO).as_posix(),
            "excluded_case_ids": sorted({row["case_id"] for row in excluded}),
            "catalog_equivalence_claimed": False,
            "additional_paid_baseline_calls": 0,
            "input_windowing_or_truncation": False,
        },
        gates=[
            {"gate": "uv environment", "status": "Previously authorized environment reused"},
            {"gate": "Julia weights", "status": "Previously authorized pinned weights reused offline"},
            {"gate": "reviewer adaptation", "status": "Explicit user instruction; separate benchmark artifact"},
            {"gate": "paid adapted LLM baseline", "status": "Not requested or executed; original A is reference only"},
        ],
        execution_status="Prepared; no adapted inference yet",
    )
    metadata["anomalies"] = [
        "Criteria and compact choices were authored by a separate agent without cases, labels or outputs.",
        "This is a changed-catalog experiment, not a drop-in measurement of the exact kernel criteria.",
        "Cases with state-only context overflow are excluded as whole cases using pre-inference token counts.",
        "No premise-positive label exists; the full critical-role condition remains untested.",
        "No additional paid LLM baseline was executed for these adapted criteria.",
    ]
    write_json(target / "metadata.json", metadata)
    for variant in ("noul", "choice"):
        prepare(target, "julia", variant)
    print(f"Prepared {len(dataset['cases'])} cases; excluded {metadata['adaptation']['excluded_case_ids']}")


if __name__ == "__main__":
    main()
