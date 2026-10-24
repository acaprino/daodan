"""Offline CLI scorer for the mock Gutsy nomination eval.

Writes ONLY into mock-nomination/runs/<new-timestamp>/ (decisions.json,
scores.json, REPORT.md). Existing run directories are never overwritten:
an existing target aborts the run. No inference is performed; gold-replay
serves the probabilities already saved in gutsy-comparison.json.

Usage:
    python -B .../score_mock.py --mode gold-replay --run-dir runs/<timestamp>
``--run-dir`` is resolved inside mock-nomination/runs/; omit it to generate a
fresh UTC timestamp directory.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))  # choicer-eval, for the metrics import

import gold  # noqa: E402
from mock_gutsy import MODES, MockGutsy, MockGutsyFailure  # noqa: E402
from nomination_policy import (  # noqa: E402
    FrozenProfile, nominate, score_team_probs, validate_answer,
)

# metrics.py is importable with the stdlib alone (verified); reuse it when
# available and fall back to a faithful local replica of the two functions
# this scorer needs, documented here so the fallback is never silent.
try:
    import metrics as _metrics

    _role_metrics = _metrics._role_metrics
    _calibration = _metrics._calibration
    METRICS_SOURCE = "imported ../metrics.py (_role_metrics, _calibration)"
except Exception as _exc:  # pragma: no cover - exercised only if import breaks
    METRICS_SOURCE = f"local replica (../metrics.py import failed: {_exc})"
    import statistics as _statistics

    def _ratio(n, d):
        return n / d if d else None

    def _role_metrics(cases):  # replica of metrics._role_metrics:66-102
        labeled = [c for c in cases if c["label_status"] == "labeled"]
        expected = sum(len(c["expected_roles"]) for c in labeled)
        matched = sum(len(set(c["selected"]) & set(c["expected_roles"])) for c in labeled)
        excess = sum(len(set(c["selected"]) - set(c["expected_roles"])) for c in labeled)
        critical_roles = (
            "senior-review:security-auditor", "senior-review:premise-auditor",
            "senior-review:data-integrity-auditor",
        )
        critical = {}
        for role in critical_roles:
            supporting = [c for c in labeled if role in c["expected_roles"]]
            found = sum(role in c["selected"] for c in supporting)
            critical[role] = {"support": len(supporting), "true_positives": found,
                              "false_negatives": len(supporting) - found,
                              "recall": _ratio(found, len(supporting))}
        cs = sum(i["support"] for i in critical.values())
        cf = sum(i["true_positives"] for i in critical.values())
        return {"labeled_cases": len(labeled), "expected_role_activations": expected,
                "matched_expected_roles": matched, "false_negatives": expected - matched,
                "expected_role_recall": _ratio(matched, expected),
                "benchmark_excess_activations": excess,
                "benchmark_excess_per_case": _ratio(excess, len(labeled)),
                "critical": critical,
                "critical_overall": {"support": cs, "true_positives": cf,
                                     "false_negatives": cs - cf,
                                     "recall": _ratio(cf, cs)}}

    def _calibration(cases, role_ids):  # replica of metrics._calibration:105-154
        observations = [
            {"case_id": c["case_id"], "role": r, "probability": c["probabilities"][r],
             "benchmark_label": int(r in c["expected_roles"])}
            for c in cases if c["label_status"] == "labeled" for r in role_ids
        ]
        bins, ece = [], 0.0
        for index in range(10):
            members = [p for p in observations if min(int(p["probability"] * 10), 9) == index]
            conf = _statistics.mean(p["probability"] for p in members) if members else None
            freq = _statistics.mean(p["benchmark_label"] for p in members) if members else None
            gap = abs(conf - freq) if members else None
            if members:
                ece += len(members) / len(observations) * gap
            bins.append({"lower": index / 10, "upper": (index + 1) / 10,
                         "upper_inclusive": index == 9, "count": len(members),
                         "mean_probability": conf, "benchmark_positive_frequency": freq,
                         "absolute_gap": gap})
        return {"available": bool(observations),
                "reason": None if observations else "No complete labeled case probabilities.",
                "observation_count": len(observations),
                "ece": ece if observations else None, "reliability": bins,
                "observations": observations}


def _resolve_run_dir(raw: str | None) -> Path:
    runs_root = (HERE / "runs").resolve()
    if raw:
        candidate = Path(raw)
        if not candidate.is_absolute():
            # Accept "runs/<ts>" (relative to this folder) or bare "<ts>".
            candidate = (HERE / candidate) if candidate.parts and candidate.parts[0] == "runs" else (runs_root / candidate)
        target = candidate.resolve()
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = runs_root / stamp
    if runs_root not in target.parents:
        raise ValueError(f"run dir must live under {runs_root}: {target}")
    if target.exists():
        raise ValueError(f"refusing to overwrite existing run dir: {target}")
    return target


def _valid_probs(questions: dict, raw: dict, qids) -> dict:
    """P(true) only for answers the policy accepts as a real vote.

    Missing, malformed, Z-marked or otherwise invalid answers are omitted
    here and recorded as ABSTAIN by ``nominate``; they never become a 0.0
    (negative) probability in calibration or threshold scoring.
    """
    answers = raw.get("answers") if isinstance(raw, dict) else None
    if not isinstance(answers, dict):
        return {}
    probs = {}
    for qid in qids:
        verdict = validate_answer(questions.get(qid, {}), answers.get(qid))
        if verdict["status"] == "ok":
            probs[qid] = verdict["p_true"]
    return probs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, default="gold-replay")
    parser.add_argument("--run-dir", default=None,
                        help="runs/<timestamp> inside mock-nomination/ (must not exist)")
    args = parser.parse_args(argv)

    counts = gold.guard_counts()
    saved = gold.saved_probs()
    teams = gold.load_teams()
    team_roles = gold.team_role_ids()
    dataset = gold.load_dataset()
    c_roles = gold.reviewer_ids_c()

    # Both instances feed one aggregated decisions.json, so they share one
    # counter: decision_id stays unique across the team and Gold C groups.
    decision_counter = itertools.count(1)
    if args.mode == "gold-replay":
        mock_teams = MockGutsy("gold-replay", saved_probs=saved["suite2_raw_probs"],
                               counter=decision_counter)
        mock_c = MockGutsy("gold-replay", saved_probs=saved["suite3_raw_probs"],
                           counter=decision_counter)
    elif args.mode == "oracle":
        mock_teams = MockGutsy("oracle", expected_by_case={
            t["id"]: t["required_roles"] for t in teams}, counter=decision_counter)
        mock_c = MockGutsy("oracle", expected_by_case={
            c["id"]: c.get("expected_roles", []) for c in dataset["cases"]},
            counter=decision_counter)
    else:
        mock_teams = MockGutsy(args.mode, counter=decision_counter)
        mock_c = MockGutsy(args.mode, counter=decision_counter)

    replay_profile = FrozenProfile.threshold_only_replay()
    decisions, failures = [], []
    team_raw_probs: dict = {}
    team_results = []
    for team in teams:
        questions = gold.build_questions(team_roles)
        state = gold.public_state_team(team)
        bindings = {rid: [a["path"] for a in state["artifacts"]] for rid in team_roles}
        try:
            raw = mock_teams.decide(state, questions)
        except MockGutsyFailure as exc:
            failures.append({"case_id": team["id"], "error": str(exc)})
            team_results.append(nominate(team["id"], questions, None,
                                         failure="tool_failure"))
            continue
        decisions.extend(raw.get("decisions", []))
        result = nominate(team["id"], questions, raw, replay_profile)
        team_results.append(result)
        team_raw_probs[team["id"]] = _valid_probs(questions, raw, team_roles)

    c_rows, c_calibration_rows, c_results = [], [], []
    for case in dataset["cases"]:
        questions = gold.build_questions(c_roles)
        state = gold.public_state_c(case)
        try:
            raw = mock_c.decide(state, questions)
        except MockGutsyFailure as exc:
            failures.append({"case_id": case["id"], "error": str(exc)})
            c_results.append(nominate(case["id"], questions, None,
                                      replay_profile, failure="tool_failure"))
            continue
        decisions.extend(raw.get("decisions", []))
        result = nominate(case["id"], questions, raw, replay_profile)
        c_results.append(result)
        # Absent/invalid answers ABSTAIN in ``result`` and contribute no
        # probability; only complete cases enter calibration, whose metrics
        # require one probability per role.
        probs = _valid_probs(questions, raw, c_roles)
        c_rows.append({"case_id": case["id"], "label_status": case["label_status"],
                       "expected_roles": case.get("expected_roles", []),
                       "selected": result["nominated"]})
        if len(probs) == len(c_roles):
            c_calibration_rows.append({**c_rows[-1], "probabilities": probs})

    suite2_scored = score_team_probs(teams, team_raw_probs) if len(team_raw_probs) == len(teams) else {}
    recorded = saved["suite2_grounded_noul"]
    suite2_match = {
        th: (suite2_scored.get(th) == recorded.get(th)) for th in recorded
    } if suite2_scored and recorded else {}
    suite3_recorded = saved["suite3_c01_c11"].get("gutsy_exact_catalog_th_0.50", {})
    suite3_match = None
    if suite3_recorded:
        suite3_match = all(
            sorted(r["selected"]) == sorted(suite3_recorded["per_case_selected"].get(r["case_id"], []))
            for r in c_rows
        )

    scores = {
        "mode": args.mode,
        "runtime_identity": "mock-gutsy/v1",
        "metrics_source": METRICS_SOURCE,
        "gold_counts": counts,
        "team_source": gold.team_source(),
        "failures": failures,
        "team_policy_results": team_results,
        "suite3_policy_results": c_results,
        "suite2_threshold_only_replay": suite2_scored,
        "suite2_matches_recorded": suite2_match,
        "suite3_role_metrics_at_0.50": _role_metrics(c_rows) if c_rows else None,
        "suite3_calibration": _calibration(c_calibration_rows, c_roles) if c_calibration_rows else None,
        "suite3_per_case_selected_matches_recorded_gutsy_exact_catalog_th_0.50": suite3_match,
    }

    target = _resolve_run_dir(args.run_dir)
    target.mkdir(parents=True)
    (target / "decisions.json").write_text(
        json.dumps({"decisions": decisions, "failures": failures}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (target / "scores.json").write_text(
        json.dumps(scores, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Mock Gutsy nomination run",
        "",
        f"Mode: `{args.mode}` (runtime_identity `mock-gutsy/v1`). Offline only; no inference performed.",
        f"Metrics source: {METRICS_SOURCE}.",
        "",
        f"Gold guards: {counts}.",
        f"Answer decisions recorded: {len(decisions)}; tool failures: {len(failures)}.",
        f"Suite2 threshold-only replay matches recorded gutsy-comparison numbers: {suite2_match}.",
        f"Suite3 per-case selection at 0.50 matches recorded gutsy_exact_catalog_th_0.50: {suite3_match}.",
        "",
        "The threshold-only replay profile (no mandatory lenses, no evidence gate) exists solely to",
        "reproduce the recorded threshold numbers. Default nomination adds the mandatory senior-review",
        "lenses and the evidence-binding gate; those numbers differ by design and are not claimed here.",
        "",
    ]
    (target / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {target} (mode={args.mode}, decisions={len(decisions)}, "
          f"suite2_match={suite2_match}, suite3_match={suite3_match})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
