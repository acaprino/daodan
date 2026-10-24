"""Offline scoring and Markdown reporting; no model calls or filesystem writes."""

from __future__ import annotations

import itertools
import json
import math
import statistics
from collections import defaultdict
from typing import Any


CRITICAL_ROLES = (
    "senior-review:security-auditor",
    "senior-review:premise-auditor",
    "senior-review:data-integrity-auditor",
)
DEFAULT_MODELS = ("llm/noul", "julia/noul", "julia/choice")
TIMING_PHASES = ("cold", "warm", "preflight", "unknown")


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _duration(values: list[Any]) -> dict[str, Any]:
    known = [float(value) for value in values if _number(value)]
    return {
        "count": len(values),
        "known_count": len(known),
        "unknown_count": len(values) - len(known),
        "total_seconds": sum(known) if known and len(known) == len(values) else None,
        "known_total_seconds": sum(known) if known else None,
        "mean_seconds": statistics.mean(known) if known else None,
        "min_seconds": min(known) if known else None,
        "max_seconds": max(known) if known else None,
    }


def _token_usage(records: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"calls": len(records)}
    for name in ("input_tokens", "output_tokens"):
        values = [
            (record.get("usage") or {}).get(name)
            for record in records
        ]
        known = [
            value for value in values
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0
        ]
        result[name] = sum(known) if known and len(known) == len(values) else None
        result[f"known_{name}"] = sum(known) if known else None
        result[f"unknown_{name}_calls"] = len(values) - len(known)
    return result


def _role_metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    labeled = [case for case in cases if case["label_status"] == "labeled"]
    expected_count = sum(len(case["expected_roles"]) for case in labeled)
    matched_count = sum(
        len(set(case["selected"]) & set(case["expected_roles"])) for case in labeled
    )
    excess = sum(
        len(set(case["selected"]) - set(case["expected_roles"])) for case in labeled
    )
    critical: dict[str, Any] = {}
    for role in CRITICAL_ROLES:
        supporting = [case for case in labeled if role in case["expected_roles"]]
        found = sum(role in case["selected"] for case in supporting)
        critical[role] = {
            "support": len(supporting),
            "true_positives": found,
            "false_negatives": len(supporting) - found,
            "recall": _ratio(found, len(supporting)),
        }
    critical_support = sum(item["support"] for item in critical.values())
    critical_found = sum(item["true_positives"] for item in critical.values())
    return {
        "labeled_cases": len(labeled),
        "expected_role_activations": expected_count,
        "matched_expected_roles": matched_count,
        "false_negatives": expected_count - matched_count,
        "expected_role_recall": _ratio(matched_count, expected_count),
        "benchmark_excess_activations": excess,
        "benchmark_excess_per_case": _ratio(excess, len(labeled)),
        "critical": critical,
        "critical_overall": {
            "support": critical_support,
            "true_positives": critical_found,
            "false_negatives": critical_support - critical_found,
            "recall": _ratio(critical_found, critical_support),
        },
    }


def _calibration(cases: list[dict[str, Any]], role_ids: list[str]) -> dict[str, Any]:
    observations = [
        {
            "case_id": case["case_id"],
            "role": role,
            "probability": case["probabilities"][role],
            "benchmark_label": int(role in case["expected_roles"]),
        }
        for case in cases
        if case["label_status"] == "labeled"
        for role in role_ids
    ]
    bins: list[dict[str, Any]] = []
    ece = 0.0
    for index in range(10):
        members = [
            point for point in observations
            if min(int(point["probability"] * 10), 9) == index
        ]
        confidence = (
            statistics.mean(point["probability"] for point in members) if members else None
        )
        frequency = (
            statistics.mean(point["benchmark_label"] for point in members) if members else None
        )
        gap = abs(confidence - frequency) if members else None
        if members:
            ece += len(members) / len(observations) * gap
        bins.append({
            "lower": index / 10,
            "upper": (index + 1) / 10,
            "upper_inclusive": index == 9,
            "count": len(members),
            "mean_probability": confidence,
            "benchmark_positive_frequency": frequency,
            "absolute_gap": gap,
        })
    return {
        "available": bool(observations),
        "reason": None if observations else "No complete labeled case probabilities.",
        "interpretation": (
            "Descriptive case-role ECE against partial benchmark labels. An absent "
            "expected role is a proxy negative, not proof that its review is irrelevant. "
            "P(case, role) is the maximum P(true) across that case's hunks."
        ),
        "observation_count": len(observations),
        "ece": ece if observations else None,
        "reliability": bins,
        "observations": observations,
    }


def _curve(cases: list[dict[str, Any]], role_ids: list[str]) -> list[dict[str, Any]]:
    labeled = [case for case in cases if case["label_status"] == "labeled"]
    if not labeled:
        return []
    # Every achievable selection set in [0, 1], including >= boundary behavior.
    thresholds = {0.0, 0.5, 1.0}
    thresholds.update(index / 20 for index in range(21))
    thresholds.update(
        math.nextafter(case["probabilities"][role], math.inf)
        for case in labeled for role in role_ids
        if case["probabilities"][role] < 1
    )
    rows = []
    for threshold in sorted(thresholds):
        classified = [
            {
                **case,
                "selected": [
                    role for role in role_ids
                    if case["probabilities"][role] >= threshold
                ],
            }
            for case in labeled
        ]
        metrics = _role_metrics(classified)
        rows.append({
            "threshold": threshold,
            "expected_role_recall": metrics["expected_role_recall"],
            "benchmark_excess_per_case": metrics["benchmark_excess_per_case"],
            "false_negatives": metrics["false_negatives"],
            "critical": metrics["critical"],
        })
    return rows


def _hunk_id(hunk: dict[str, Any]) -> str | None:
    return hunk.get("id", hunk.get("hunk_id"))


def _case_timing(
    hunk_ids: list[str], records: list[dict[str, Any]], impl: str,
) -> dict[str, Any]:
    """Measure recorded operational attempts independently of prediction validity."""
    expected_ids = [None] if impl == "llm" and hunk_ids else hunk_ids
    observed_ids = [record.get("hunk_id") for record in records]
    attempted = [record for record in records if record.get("status") in {"ok", "error"}]
    complete = (
        bool(expected_ids)
        and len(observed_ids) == len(expected_ids)
        and set(observed_ids) == set(expected_ids)
        and len(attempted) == len(records)
    )
    wall = _duration([record.get("wall_seconds") for record in attempted])
    cpu = _duration([record.get("cpu_seconds") for record in attempted])
    by_phase = {
        phase: {
            "wall": _duration([
                record.get("wall_seconds") for record in attempted if record.get("phase", "unknown") == phase
            ]),
            "cpu": _duration([
                record.get("cpu_seconds") for record in attempted if record.get("phase", "unknown") == phase
            ]),
        }
        for phase in TIMING_PHASES
    }
    return {
        "wall_seconds": wall["total_seconds"] if complete else None,
        "cpu_seconds": cpu["total_seconds"] if complete else None,
        "latency_by_phase": {
            phase: {
                "wall_seconds": values["wall"]["total_seconds"] if complete else None,
                "cpu_seconds": values["cpu"]["total_seconds"] if complete else None,
            }
            for phase, values in by_phase.items()
        },
        "operational_timing": {
            "coverage": "complete" if complete else "partial" if attempted else "unavailable",
            "expected_records": len(expected_ids),
            "attempted_records": len(attempted),
            "observed_attempts": {"wall": wall, "cpu": cpu, "by_phase": by_phase},
            "interpretation": (
                "Full-case totals require one attempted record per expected hunk/batch, "
                "including failed attempts. Known recorded-attempt sums may cover only "
                "part of a case and never establish full-case latency or valid predictions."
            ),
        },
    }


def _case_result(
    case: dict[str, Any],
    records: list[dict[str, Any]],
    impl: str,
    variant: str,
    role_ids: list[str],
    threshold: float,
) -> dict[str, Any]:
    result = {
        "case_id": case["id"],
        "source_case": case.get("source_case", case["id"]),
        "label_status": case["label_status"],
        "expected_roles": sorted(set(case.get("expected_roles", []))),
        "status": "unavailable",
        "reason": None,
        "selected": None,
        "probabilities": None,
        "hunk_count": len(case.get("hunks", [])),
        "record_count": len(records),
        "anomalies": [
            warning for record in records for warning in record.get("validation_warnings", [])
        ],
    }
    hunk_ids = [_hunk_id(hunk) for hunk in case.get("hunks", [])]
    result.update(_case_timing(hunk_ids, records, impl))
    if not hunk_ids:
        result["reason"] = "No materialized hunks."
        return result
    if not records:
        result["reason"] = "No prediction records."
        return result
    failed = [record for record in records if record.get("status") != "ok"]
    if failed:
        result["reason"] = "Non-success records: " + ", ".join(
            sorted({str(record.get("status", "missing status")) for record in failed})
        )
        return result
    expected_ids = [None] if impl == "llm" else hunk_ids
    observed_ids = [record.get("hunk_id") for record in records]
    if len(observed_ids) != len(expected_ids) or set(observed_ids) != set(expected_ids):
        result["reason"] = "Missing, duplicate, or unexpected hunk/batch records."
        return result
    allowed = set(role_ids)
    probabilities: dict[str, float] = {}
    selected: set[str] = set()
    for record in records:
        stored_selected = record.get("selected")
        if (
            not isinstance(stored_selected, list)
            or not all(isinstance(role, str) for role in stored_selected)
            or not set(stored_selected).issubset(allowed)
            or len(stored_selected) != len(set(stored_selected))
        ):
            result["reason"] = "Selected roles are missing, duplicated, or outside the catalog."
            return result
        if impl == "llm":
            selected.update(stored_selected)
            if record.get("probabilities") is not None:
                result["anomalies"].append(
                    "Ignored LLM probabilities: the verbatim prompt has no probability field."
                )
            continue
        values = record.get("probabilities")
        if (
            not isinstance(values, dict)
            or set(values) != allowed
            or not all(_number(value) and value <= 1 for value in values.values())
        ):
            result["reason"] = "Probabilities must cover every catalog role with finite values in [0, 1]."
            return result
        for role, value in values.items():
            probabilities[role] = max(probabilities.get(role, 0.0), float(value))
        if variant == "noul":
            hunk_selected = {role for role in role_ids if values[role] >= threshold}
        else:
            if not math.isclose(sum(values.values()), 1.0, rel_tol=0.0, abs_tol=0.001):
                result["reason"] = "Choice probabilities do not sum to one within 0.001."
                return result
            # Stable catalog order resolves exact ties without thresholding choice scores.
            hunk_selected = {max(role_ids, key=lambda role: values[role])}
        selected.update(hunk_selected)
        if set(stored_selected) != hunk_selected:
            result["anomalies"].append(
                f"{record.get('hunk_id')}: stored selection differs from the probability-derived selection."
            )
    result.update({
        "status": "complete",
        "selected": sorted(selected),
        "probabilities": probabilities if impl != "llm" else None,
    })
    return result


def _partial_capability_diagnostics(
    cases: list[dict[str, Any]],
    role_ids: list[str],
    records: list[dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    """Inspect successful individual questions without repairing incomplete runs."""
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_case[record["case_id"]].append(record)
    roles: dict[str, Any] = {}
    for role in role_ids:
        rejected = defaultdict(int)
        accepted_encodings = 0
        observed_questions = 0
        valid_answers = 0

        def probability(record: dict[str, Any]) -> float | None:
            nonlocal accepted_encodings, observed_questions, valid_answers
            encoding = (record.get("encoding") or {}).get(role)
            question_error = (record.get("question_errors") or {}).get(role)
            raw = record.get("raw_output")
            answers = raw.get("answers", {}) if isinstance(raw, dict) else {}
            answer = answers.get(role) if isinstance(answers, dict) else None
            if encoding is not None or question_error is not None or answer is not None:
                observed_questions += 1
            if question_error is not None:
                rejected[str(question_error)] += 1
                return None
            if not isinstance(encoding, dict):
                return None
            if encoding.get("stateTruncated") is not False or encoding.get("optionsTruncated") is not False:
                return None
            accepted_encodings += 1
            if not isinstance(answer, dict) or answer.get("type") != "noul":
                return None
            values = answer.get("probabilities")
            if not isinstance(values, dict) or set(values) != {"false", "true"}:
                return None
            if not all(_number(value) and value <= 1 for value in values.values()):
                return None
            if not math.isclose(sum(values.values()), 1.0, rel_tol=0.0, abs_tol=0.00001):
                return None
            if "noul" in answer and (
                not _number(answer["noul"])
                or not math.isclose(answer["noul"], values["true"], rel_tol=0.0, abs_tol=0.00001)
            ):
                return None
            valid_answers += 1
            return float(values["true"])

        case_results = []
        for case in cases:
            case_records = by_case[case["id"]]
            hunk_ids = [_hunk_id(hunk) for hunk in case.get("hunks", [])]
            observed_hunks = [record.get("hunk_id") for record in case_records]
            probabilities = [probability(record) for record in case_records]
            complete = (
                bool(hunk_ids)
                and len(hunk_ids) == len(observed_hunks)
                and set(hunk_ids) == set(observed_hunks)
                and all(value is not None for value in probabilities)
            )
            value = max(probabilities) if complete else None
            case_results.append({
                "case_id": case["id"],
                "label_status": case["label_status"],
                "expected": role in case.get("expected_roles", []),
                "complete_for_role": complete,
                "probability": value,
                "selected": value >= threshold if value is not None else None,
                "required_hunks": len(hunk_ids),
                "recorded_hunks": len(case_records),
                "valid_hunk_answers": sum(value is not None for value in probabilities),
            })
        supporting = [
            case for case in case_results
            if case["label_status"] == "labeled" and case["expected"] and case["complete_for_role"]
        ]
        expected_cases = [
            case for case in case_results
            if case["label_status"] == "labeled" and case["expected"]
        ]
        true_positives = sum(case["selected"] for case in supporting)
        roles[role] = {
            "observed_questions": observed_questions,
            "accepted_encodings": accepted_encodings,
            "valid_hunk_answers": valid_answers,
            "encoding_rejections": sum(rejected.values()),
            "rejection_reasons": dict(rejected),
            "complete_cases_for_role": sum(case["complete_for_role"] for case in case_results),
            "expected_positive_cases": len(expected_cases),
            "scored_positive_support": len(supporting),
            "true_positives": true_positives,
            "false_negatives": len(supporting) - true_positives,
            "expected_role_recall": _ratio(true_positives, len(supporting)),
            "missing_positive_cases": [
                case["case_id"] for case in expected_cases if not case["complete_for_role"]
            ],
            "case_results": case_results,
        }
    critical_encoding_failures = [
        role for role in CRITICAL_ROLES
        if role in roles and roles[role]["observed_questions"]
        and roles[role]["encoding_rejections"] == roles[role]["observed_questions"]
        and roles[role]["accepted_encodings"] == 0
    ]
    return {
        "purpose": (
            "Separate diagnostic of representable individual questions. Never "
            "substitutes for complete-catalog primary metrics or set agreement."
        ),
        "acceptance_rule": (
            "For a role/case require exactly one record for every hunk, explicit "
            "untruncated encoding with no per-question error, and finite normalized "
            "binary raw probabilities. Aggregate max P(true); missing roles are unknown."
        ),
        "roles": roles,
        "critical_roles_rejected_in_all_observed_encodings": critical_encoding_failures,
        "compatibility": "rejected_supplied_critical_catalog" if critical_encoding_failures else "not_established",
    }


def _declared_llm_diagnostic(
    cases: list[dict[str, Any]],
    role_ids: list[str],
    records: list[dict[str, Any]],
    primary_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    """Expose raw known-role sets without granting citation/schema validity."""
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_case[record["case_id"]].append(record)
    primary = {case["case_id"]: case for case in primary_cases}
    case_results = []
    allowed = set(role_ids)
    for case in cases:
        row = {
            "case_id": case["id"],
            "source_case": case.get("source_case", case["id"]),
            "label_status": case["label_status"],
            "expected_roles": case.get("expected_roles", []),
            "available": False,
            "selected": None,
            "reason": None,
            "primary_status": primary[case["id"]]["status"],
            "primary_validation_error": None,
        }
        matches = by_case[case["id"]]
        if len(matches) != 1 or matches[0].get("hunk_id") is not None:
            row["reason"] = "Missing, duplicate, or non-batch raw LLM record."
            case_results.append(row)
            continue
        record = matches[0]
        row["primary_validation_error"] = record.get("error")
        raw = record.get("raw_output")
        if isinstance(raw, dict) and "response" in raw:
            captured_digest = raw.get("request_sha256")
            if captured_digest is not None and captured_digest != record.get("request_sha256"):
                row["reason"] = "Raw capture request digest differs from normalized record."
                case_results.append(row)
                continue
            raw = raw["response"]
        elif isinstance(raw, dict) and isinstance(raw.get("output"), list):
            raw = "".join(
                part.get("text", "")
                for item in raw["output"] if isinstance(item, dict)
                for part in item.get("content", []) if isinstance(part, dict)
                and part.get("type") == "output_text" and isinstance(part.get("text"), str)
            )
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                raw = None
        if not isinstance(raw, dict) or raw.get("mode") != "full" or not isinstance(raw.get("selected"), list):
            row["reason"] = "Raw response does not contain a full-mode selection array."
            case_results.append(row)
            continue
        entries = raw["selected"]
        if any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("role"), str)
            or entry["role"] not in allowed
            for entry in entries
        ):
            row["reason"] = "Raw declared role set contains missing or unknown role IDs."
            case_results.append(row)
            continue
        row.update(available=True, selected=sorted({entry["role"] for entry in entries}))
        case_results.append(row)
    available = [case for case in case_results if case["available"]]
    return {
        "purpose": (
            "Unvalidated raw-declared LLM role sets, including responses rejected "
            "for citations or other output metadata. Reveals selection/validation "
            "attrition only; never substitutes for the validated baseline."
        ),
        "available_cases": len(available),
        "primary_rejected_cases_with_declared_sets": sum(
            case["primary_status"] != "complete" for case in available
        ),
        "case_results": case_results,
        "metrics": _role_metrics(available),
        "calibration": "Unavailable; declared selections are not probabilities.",
        "comparability": (
            "Excluded from primary metrics, paired comparisons and the verdict. "
            "Do not compare as a controlled baseline to a differently adapted catalog."
        ),
    }


def score(
    dataset: dict[str, Any],
    catalog: dict[str, Any],
    results: list[dict[str, Any]],
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Score complete case predictions without treating missing outputs as negatives."""
    if threshold != 0.5:
        raise ValueError("The pilot threshold is locked a priori at 0.5; curves are descriptive only.")
    cases = dataset["cases"]
    adapted = bool(catalog.get("adaptation") or dataset.get("adapted_subset"))
    case_ids = [case["id"] for case in cases]
    role_ids = [role["id"] for role in catalog["roles"] if role.get("is_reviewer", True)]
    if not role_ids or len(set(role_ids)) != len(role_ids):
        raise ValueError("Reviewer catalog must be nonempty and have unique IDs.")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("Case IDs must be unique.")
    for case in cases:
        if case.get("label_status") not in {"labeled", "unlabeled"}:
            raise ValueError(f"{case['id']}: explicit labeled/unlabeled status is required.")
        expected = case.get("expected_roles", [])
        if not isinstance(expected, list) or not all(isinstance(role, str) for role in expected):
            raise ValueError(f"{case['id']}: expected_roles must be a list of role IDs.")
        if not set(expected).issubset(role_ids):
            raise ValueError(f"{case['id']}: an expected role is absent from the reviewer catalog.")
        if case["label_status"] == "unlabeled" and expected:
            raise ValueError(f"{case['id']}: an unlabeled case cannot contain expected roles.")
        hunks = [_hunk_id(hunk) for hunk in case.get("hunks", [])]
        if any(not isinstance(hunk, str) or not hunk for hunk in hunks) or len(set(hunks)) != len(hunks):
            raise ValueError(f"{case['id']}: hunk IDs must be nonempty and unique.")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    anomalies: list[str] = []
    for record in results:
        if record.get("impl") not in {"llm", "julia", "laya"}:
            raise ValueError("Unknown implementation in result record.")
        if record.get("variant") not in {"noul", "choice"}:
            raise ValueError("Unknown variant in result record.")
        if record.get("case_id") not in case_ids:
            raise ValueError("Unknown case ID in result record.")
        if record.get("phase") == "warmup":
            anomalies.append("Explicit warmup record excluded from predictive scoring and measured calls.")
            continue
        grouped[f"{record['impl']}/{record['variant']}"].append(record)
    models: dict[str, Any] = {}
    for key in sorted(set(DEFAULT_MODELS) | set(grouped)):
        impl, variant = key.split("/")
        records = grouped[key]
        by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_case[record["case_id"]].append(record)
        case_results = [
            _case_result(case, by_case[case["id"]], impl, variant, role_ids, threshold)
            for case in cases
        ]
        complete = [case for case in case_results if case["status"] == "complete"]
        fully_attempted = [
            case for case in case_results if case["operational_timing"]["coverage"] == "complete"
        ]
        attempted = [record for record in records if record.get("status") != "blocked"]
        if impl == "llm":
            calibration = {
                "available": False,
                "reason": "The verbatim REVIEWER_CHOICER emits selections, not P(true); no synthetic confidence.",
                "ece": None,
                "reliability": [],
                "observations": [],
            }
        elif variant == "choice":
            calibration = {
                "available": False,
                "reason": "Categorical choice probabilities are not independent binary P(true) values.",
                "ece": None,
                "reliability": [],
                "observations": [],
            }
        else:
            calibration = _calibration(complete, role_ids)
        models[key] = {
            "impl": impl,
            "variant": variant,
            "status": (
                "complete" if len(complete) == len(cases) and cases
                else "partial" if complete else "unavailable"
            ),
            "complete_cases": len(complete),
            "unavailable_cases": len(cases) - len(complete),
            "case_results": case_results,
            "metrics": _role_metrics(complete),
            "calibration": calibration,
            "threshold_curve": _curve(complete, role_ids) if impl != "llm" and variant == "noul" else [],
            "latency": {
                "calls": {
                    "wall": _duration([record.get("wall_seconds") for record in attempted]),
                    "cpu": _duration([record.get("cpu_seconds") for record in attempted]),
                },
                "by_phase": {
                    phase: {
                        "wall": _duration([
                            record.get("wall_seconds") for record in attempted if record.get("phase") == phase
                        ]),
                        "cpu": _duration([
                            record.get("cpu_seconds") for record in attempted if record.get("phase") == phase
                        ]),
                    }
                    for phase in TIMING_PHASES
                },
                "complete_cases": {
                    "wall": _duration([case["wall_seconds"] for case in complete]),
                    "cpu": _duration([case["cpu_seconds"] for case in complete]),
                },
                "fully_attempted_cases": {
                    "case_count": len(fully_attempted),
                    "wall": _duration([case["wall_seconds"] for case in fully_attempted]),
                    "cpu": _duration([case["cpu_seconds"] for case in fully_attempted]),
                },
            },
            "provider_usage": _token_usage(attempted),
        }
    diagnostics = {
        key: {
            **_partial_capability_diagnostics(cases, role_ids, grouped[key], threshold),
            "catalog_kind": "adapted" if adapted else "exact",
        }
        for key in models if key.split("/")[0] != "llm" and key.endswith("/noul")
    }
    comparisons: dict[str, Any] = {}
    for left, right in itertools.combinations(models, 2):
        left_cases = {case["case_id"]: case for case in models[left]["case_results"]}
        right_cases = {case["case_id"]: case for case in models[right]["case_results"]}
        comparison_rows = []
        paired_left, paired_right = [], []
        for case_id in case_ids:
            a, b = left_cases[case_id], right_cases[case_id]
            available = a["status"] == b["status"] == "complete"
            union = set(a["selected"] or []) | set(b["selected"] or [])
            intersection = set(a["selected"] or []) & set(b["selected"] or [])
            comparison_rows.append({
                "case_id": case_id,
                "available": available,
                "exact_agreement": a["selected"] == b["selected"] if available else None,
                "jaccard": ((len(intersection) / len(union)) if union else 1.0) if available else None,
            })
            if available and a["label_status"] == "labeled":
                paired_left.append(a)
                paired_right.append(b)
        left_metrics, right_metrics = _role_metrics(paired_left), _role_metrics(paired_right)
        available_rows = [row for row in comparison_rows if row["available"]]
        comparisons[f"{left} vs {right}"] = {
            "left": left,
            "right": right,
            "paired_cases": len(available_rows),
            "paired_labeled_cases": len(paired_left),
            "exact_agreement_rate": (
                statistics.mean(row["exact_agreement"] for row in available_rows) if available_rows else None
            ),
            "mean_jaccard": (
                statistics.mean(row["jaccard"] for row in available_rows) if available_rows else None
            ),
            "case_results": comparison_rows,
            "left_metrics": left_metrics,
            "right_metrics": right_metrics,
        }
    baseline = models["llm/noul"]
    candidate = models["julia/noul"]
    paired = next(
        item for item in comparisons.values()
        if {item["left"], item["right"]} == {"llm/noul", "julia/noul"}
    )
    baseline_paired = paired["left_metrics"] if paired["left"] == "llm/noul" else paired["right_metrics"]
    candidate_paired = paired["left_metrics"] if paired["left"] == "julia/noul" else paired["right_metrics"]
    critical_comparison = {
        role: {
            "paired_support": baseline_paired["critical"][role]["support"],
            "baseline_false_negatives": baseline_paired["critical"][role]["false_negatives"],
            "candidate_false_negatives": candidate_paired["critical"][role]["false_negatives"],
            "candidate_not_worse": (
                candidate_paired["critical"][role]["false_negatives"]
                <= baseline_paired["critical"][role]["false_negatives"]
            ) if baseline_paired["critical"][role]["support"] else None,
        }
        for role in CRITICAL_ROLES
    }
    measured_pairs = paired["paired_labeled_cases"]
    worse = any(item["candidate_not_worse"] is False for item in critical_comparison.values())
    unsupported = [role for role, item in critical_comparison.items() if not item["paired_support"]]
    incompatible_critical_roles = diagnostics["julia/noul"][
        "critical_roles_rejected_in_all_observed_encodings"
    ]
    if incompatible_critical_roles:
        decision = "incompatible_adapted_catalog" if adapted else "incompatible_exact_catalog"
        verdict = (
            ("The adapted candidate rejected supplied critical-role criteria in every observed encoding "
             if adapted else "The candidate rejected exact critical-role criteria in every observed encoding ")
            + "for " + ", ".join(incompatible_critical_roles) + ". This pilot rejects "
            "compatibility with this run's catalog; partial answers do not establish full routing quality."
        )
    elif adapted and not measured_pairs:
        decision = "adapted_unpaired_exploration"
        verdict = (
            "This adapted-catalog experiment has no matched LLM baseline. Local results "
            "are exploratory and cannot establish replacement quality or critical-role non-inferiority."
        )
    elif not measured_pairs:
        decision = "not_measured"
        verdict = "No paired labeled predictions were measured; opening shadow mode is not yet evidence-supported."
    elif worse:
        decision = "critical_regression"
        verdict = "The candidate missed more expected critical activations on paired cases; this pilot does not support opening shadow mode."
    elif unsupported or baseline["status"] != "complete" or candidate["status"] != "complete":
        decision = "inconclusive"
        verdict = "The pilot is inconclusive for the full critical-role condition because coverage is incomplete."
    else:
        decision = "shadow_observation_only"
        verdict = "The pilot supports considering shadow observation on the Decision Log only; it does not support promotion."
    return {
        "schema": "choicer-eval-score/v1",
        "experiment_kind": "adapted_catalog" if adapted else "exact_catalog",
        "protocol": {
            "threshold": threshold,
            "threshold_policy": "0.5 fixed a priori; the full empirical curve is descriptive and must not select the reported threshold.",
            "label_policy": "Expected dimensions provide partial positives; other roles are proxy negatives only.",
            "unlabeled_policy": "Unlabeled cases enter agreement and latency only, never recall, excess, calibration, or threshold curves.",
            "case_probability": "Maximum P(true) over all hunks of a complete case.",
            "choice_selection": "Argmax per hunk, with catalog-order tie break; union across the case.",
            "missing_policy": "Incomplete, failed, duplicate, or blocked cases never become negative predictions.",
            "llm_validation_scope": (
                "Accepted under limited citation checks: registered role, hunk ID, "
                "exact supplied path and line, snippet occurrence, tier/effort and "
                "reason constraints. Frozen hunk inputs omit base/candidate bindings, "
                "so side claims are unverified. This is not full schema/evidence "
                "conformance or proof of semantic reviewer relevance."
            ),
        },
        "dataset": {
            "case_count": len(cases),
            "labeled_case_count": sum(case["label_status"] == "labeled" for case in cases),
            "unlabeled_case_count": sum(case["label_status"] == "unlabeled" for case in cases),
            "reviewer_count": len(role_ids),
            "hunk_count": sum(len(case.get("hunks", [])) for case in cases),
            "dimension_mapping": dataset.get("dimension_mapping", {}),
            "adapted_subset": dataset.get("adapted_subset"),
            "catalog_adaptation": catalog.get("adaptation"),
        },
        "models": models,
        "partial_capability_diagnostics": diagnostics,
        "raw_declared_llm_diagnostic": _declared_llm_diagnostic(
            cases, role_ids, grouped["llm/noul"], models["llm/noul"]["case_results"],
        ),
        "comparisons": comparisons,
        "critical_comparison": critical_comparison,
        "anomalies": anomalies,
        "verdict": {
            "decision": decision,
            "text": verdict,
            "unsupported_critical_roles": unsupported,
            "incompatible_critical_roles": incompatible_critical_roles,
            "net_tokens_saved_per_run": None,
            "net_savings_reason": "Downstream tier2/tier3 spend avoided and routing-error/retry token costs are not measured by this pilot.",
            "promotion": "Not established. Only an expanded Decision Log shadow evaluation can establish promotion.",
        },
    }


def _cell(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _decimal(value: Any, digits: int = 3) -> str:
    return f"{value:.{digits}f}" if _number(value) else "unknown"


def _recall(item: dict[str, Any]) -> str:
    if not item["support"]:
        return "undefined (no labeled support)"
    return f"{item['true_positives']}/{item['support']} ({item['recall']:.3f})"


def _roles(value: list[str] | None) -> str:
    if value is None:
        return "unavailable"
    return ", ".join(f"`{role}`" for role in value) or "(none)"


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(_cell(value) for value in row) + " |" for row in rows],
        "",
    ]


def render_report(
    dataset: dict[str, Any],
    catalog: dict[str, Any],
    scored: dict[str, Any],
    metadata: dict[str, Any],
) -> str:
    """Render only recorded metadata and values derived by :func:`score`."""
    summary = scored["dataset"]
    models = scored["models"]
    adapted = scored["experiment_kind"] == "adapted_catalog"
    def model_label(key: str) -> str:
        return key + (" (limited citation checks)" if key.startswith("llm/") else "")

    lines = [
        "# Choicer adapted-catalog exploration" if adapted else "# Choicer offline pilot",
        "",
        scored["verdict"]["text"],
        "",
        f"Recorded date: {_cell(metadata.get('generated_at', metadata.get('date')))}. "
        f"Evidence directory: {_cell(metadata.get('run_path'))}.",
        "",
        "## Protocol and scope",
        "",
        f"The dataset contains {summary['case_count']} cases, "
        f"{summary['labeled_case_count']} with expected reviewer dimensions and "
        f"{summary['unlabeled_case_count']} without activation labels. "
        f"The catalog contains {summary['reviewer_count']} reviewer roles; "
        f"{summary['hunk_count']} hunks were materialized.",
        "",
        (
            "This run uses separately authored criteria and a tokenizer-selected "
            "subset. It is not equivalent to the original exact-catalog experiment. "
            "Original A outputs are reference material only unless a new baseline "
            "was measured on these same adapted criteria."
            if adapted else
            "The credential-refill case is unlabeled for reviewer activation. Its "
            "must-not-report claim concerns findings and cannot establish that any "
            "reviewer should or should not activate. It contributes only to measured "
            "agreement and latency when predictions exist."
        ),
        "",
        "Expected dimensions are known positive review lenses, not an exhaustive "
        "annotation of every legitimate trigger. Consequently, 'false activations' "
        "below mean benchmark-excess selections only. They do not establish wasted "
        "reviewer tokens or irrelevant reviews. ECE likewise uses proxy negatives "
        "and is descriptive, not validated calibration of reviewer relevance.",
        "",
        scored["protocol"]["threshold_policy"],
        "The scoring JSON retains every achievable selection set on the empirical "
        "threshold curve, including the inclusive >= boundary, plus a fixed display "
        "grid. No best threshold is selected.",
        "",
        scored["protocol"]["missing_policy"],
        "Comparative metrics use the same complete cases on both sides. Model-level "
        "summaries also state their own coverage, which can differ.",
        "Neither partial-capability answers nor raw-declared LLM selections enter "
        "any paired comparison or replace a primary prediction.",
        "",
        "LLM baseline validation: " + scored["protocol"]["llm_validation_scope"],
        "For A, 'complete' means accepted under those limited checks. The original "
        "request inputs remain frozen; side warnings are retained with each response.",
        "",
        "### Materialization and leakage boundary",
        "",
    ]
    if adapted:
        lines.extend([
            "Catalog adaptation: " + _cell(catalog.get("adaptation")),
            "",
            "Recorded subset rule and exclusions: " + _cell(dataset.get("adapted_subset")),
            "",
            "The following source-materialization rules describe the original "
            "corpus; the recorded subset above determines which cases remain here.",
            "",
        ])
    source_protocol = dataset.get("protocol", {})
    if isinstance(source_protocol, dict) and source_protocol:
        lines.extend(_table(["Recorded rule", "Exact dataset protocol"], list(source_protocol.items())))
    else:
        lines.extend(["Materialization protocol: unknown; see the dataset source evidence.", ""])
    lines.extend([
        "Reviewer-catalog selection: " + _cell(catalog.get("reviewer_selection")),
        "",
        (
            "Current trigger criteria, missing negatives and compact choice "
            "descriptions were authored for this separate adaptation. Original "
            "extracted text, field status and rationale remain in the catalog "
            "as provenance; they do not make the adapted wording verbatim or equivalent."
            if adapted else
            "Role criteria are parsed from source frontmatter. Missing trigger fields "
            "remain missing and are reported as anomalies; this report does not "
            "synthesize replacement criteria."
        ),
        "",
        "## Dimension mapping",
        "",
    ])
    mapping = dataset.get("dimension_mapping", {})
    if isinstance(mapping, dict):
        mapping_rows = [[name, _roles(value if isinstance(value, list) else [value])] for name, value in sorted(mapping.items())]
    else:
        mapping_rows = [[_cell(item), "See dataset evidence"] for item in mapping]
    lines.extend(_table(["Expected dimension", "Role ID"], mapping_rows))
    lines.extend([
        "Mapping provenance: " + _cell(dataset.get("dimension_mapping_provenance")),
        "",
    ])
    lines.extend(["## Model identity and environment", ""])
    identity = metadata.get("models", {})
    lines.extend(_table(
        ["Implementation / variant", "Recorded identity and runtime"],
        [[key, identity.get(key, identity.get(key.split("/")[0], "unknown"))] for key in models],
    ))
    lines.extend([
        "Hardware: " + _cell(metadata.get("hardware")),
        "",
        "Provenance: " + _cell(metadata.get("provenance")),
        "",
        "Model-card accuracy, context size, format and speed claims are not "
        "measurements of this pilot. Unknown identity, revision, weight hash, "
        "precision and runtime fields remain unknown until recorded by execution.",
        "",
        "## Reviewer activation metrics",
        "",
    ])
    lines.extend(_table(
        ["Implementation", "Complete cases", "Labeled cases scored", "Expected-role recall",
         "Critical recall", "Benchmark excess / labeled case", "Descriptive ECE"],
        [
            [
                model_label(key),
                f"{model['complete_cases']}/{summary['case_count']}",
                model["metrics"]["labeled_cases"],
                _decimal(model["metrics"]["expected_role_recall"]),
                _recall(model["metrics"]["critical_overall"]),
                _decimal(model["metrics"]["benchmark_excess_per_case"]),
                _decimal(model["calibration"]["ece"]),
            ]
            for key, model in models.items()
        ],
    ))
    lines.extend(_table(
        ["Implementation", "Critical role", "Recall", "False negatives"],
        [
            [model_label(key), role, _recall(value), value["false_negatives"] if value["support"] else "undefined"]
            for key, model in models.items()
            for role, value in model["metrics"]["critical"].items()
        ],
    ))
    declared = scored["raw_declared_llm_diagnostic"]
    if declared["available_cases"]:
        lines.extend([
            "## Unvalidated LLM declared-role diagnostic",
            "",
            declared["purpose"],
            declared["comparability"],
            "",
            f"{declared['available_cases']} raw role sets are readable; "
            f"{declared['primary_rejected_cases_with_declared_sets']} of those "
            "failed primary validation. A known role ID with a bad citation "
            "remains unvalidated even when the role happens to be expected.",
            "",
        ])
        lines.extend(_table(
            ["Case", "Primary limited checks", "Raw declared roles", "Validation error"],
            [
                [case["case_id"], case["primary_status"], _roles(case["selected"]),
                 case["primary_validation_error"] or case["reason"] or "(none)"]
                for case in declared["case_results"]
            ],
        ))
        lines.extend(_table(
            ["Diagnostic only", "Labeled cases", "Expected-role recall", "Benchmark excess / case"],
            [[
                "Raw declared known-role sets", declared["metrics"]["labeled_cases"],
                _decimal(declared["metrics"]["expected_role_recall"]),
                _decimal(declared["metrics"]["benchmark_excess_per_case"]),
            ]],
        ))
        lines.extend(_table(
            ["Critical role", "Unvalidated declared-role recall"],
            [[role, _recall(item)] for role, item in declared["metrics"]["critical"].items()],
        ))
    lines.extend([
        "## Partial-capability diagnostic",
        "",
        "This separate view inspects successful questions retained inside failed "
        "full-catalog calls. It never fills missing primary predictions, changes "
        "the primary recall denominator, or supplies a B set for agreement. "
        "A role/case is usable here only when every one of its hunks has an "
        "explicitly accepted, untruncated encoding and a finite normalized binary "
        "answer. Probabilities are aggregated by maximum at the fixed threshold. "
        "Recall is conditional on this stated role-specific coverage.",
        "",
    ])
    for key, diagnostic in scored["partial_capability_diagnostics"].items():
        lines.extend([f"### {key}", ""])
        lines.extend(_table(
            ["Role", "Complete cases for role", "Scored / expected positive cases",
             "Scored positive case IDs", "Positive hits", "Conditional recall",
             "Accepted encodings", "Rejected encodings"],
            [
                [
                    role, item["complete_cases_for_role"],
                    f"{item['scored_positive_support']}/{item['expected_positive_cases']}",
                    ", ".join(
                        case["case_id"] for case in item["case_results"]
                        if case["complete_for_role"] and case["expected"] and case["label_status"] == "labeled"
                    ) or "(none)",
                    item["true_positives"] if item["scored_positive_support"] else "undefined",
                    _decimal(item["expected_role_recall"]),
                    item["accepted_encodings"], item["encoding_rejections"],
                ]
                for role, item in diagnostic["roles"].items()
            ],
        ))
        rejected = [
            [role, item["rejection_reasons"]]
            for role, item in diagnostic["roles"].items() if item["rejection_reasons"]
        ]
        if rejected:
            lines.extend(_table(["Role with encoding failure", "Recorded errors and counts"], rejected))
        lines.extend([
            "Critical roles rejected in every observed encoding: "
            + _roles(diagnostic["critical_roles_rejected_in_all_observed_encodings"])
            + (
                ". This is a compatibility failure for this run's supplied criteria, "
                "not a measured false negative."
                if diagnostic["critical_roles_rejected_in_all_observed_encodings"]
                else ". No such rejection is established by the recorded encodings."
            ),
            "",
        ])
    lines.extend([
        "## Per-case agreement",
        "",
        (
            "B is Julia noul and C is Julia choice on the adapted catalog. A is "
            "available only if measured on this same adapted catalog. Original-catalog "
            "A responses are not imported into this comparison. Agreement is exact "
            "set equality followed by Jaccard overlap."
            if adapted else
            "A is the verbatim LLM full-mode reviewer selection. B is Julia noul "
            "at the fixed threshold. C is Julia categorical choice, whose per-hunk "
            "argmax selections are unioned. Agreement is exact set equality followed "
            "by Jaccard overlap; two measured empty sets have Jaccard 1."
        ),
        "",
        (
            "The unchanged hunk text is shared across the retained cases. Criteria "
            "changed, so any comparison to original A belongs in a separately "
            "labeled exploratory reference analysis, never a controlled paired result."
            if adapted else
            "The same A baseline is compared with both B and C. A separate LLM "
            "single-choice control would change the verbatim full-mode prompt and "
            "is therefore not claimed by this benchmark."
        ),
        "",
    ])
    indexed = {
        key: {case["case_id"]: case for case in model["case_results"]}
        for key, model in models.items()
    }
    ab = next(
        item for item in scored["comparisons"].values()
        if {item["left"], item["right"]} == {"llm/noul", "julia/noul"}
    )
    agreement = {row["case_id"]: row for row in ab["case_results"]}
    case_rows = []
    for case in dataset["cases"]:
        pair = agreement[case["id"]]
        case_rows.append([
            f"{case['id']} ({case.get('source_case', case['id'])})",
            _roles(case.get("expected_roles", [])) if case["label_status"] == "labeled" else "unlabeled",
            _roles(indexed["llm/noul"][case["id"]]["selected"]),
            _roles(indexed["julia/noul"][case["id"]]["selected"]),
            _roles(indexed["julia/choice"][case["id"]]["selected"]),
            (
                f"{'equal' if pair['exact_agreement'] else 'different'}; {pair['jaccard']:.3f}"
                if pair["available"] else "unavailable"
            ),
        ])
    lines.extend(_table(
        ["Case", "Expected", "A selected (limited checks)", "B selected", "C selected", "A/B agreement"],
        case_rows,
    ))
    lines.extend(_table(
        ["Pair", "Paired cases", "Paired labeled cases", "Exact agreement", "Mean Jaccard",
         "Left recall", "Right recall", "Left excess / case", "Right excess / case"],
        [
            [
                name, pair["paired_cases"], pair["paired_labeled_cases"],
                _decimal(pair["exact_agreement_rate"]), _decimal(pair["mean_jaccard"]),
                _decimal(pair["left_metrics"]["expected_role_recall"]),
                _decimal(pair["right_metrics"]["expected_role_recall"]),
                _decimal(pair["left_metrics"]["benchmark_excess_per_case"]),
                _decimal(pair["right_metrics"]["benchmark_excess_per_case"]),
            ]
            for name, pair in scored["comparisons"].items()
        ],
    ))
    lines.extend(["## Calibration", ""])
    for key, model in models.items():
        calibration = model["calibration"]
        lines.extend([f"### {key}", ""])
        if not calibration["available"]:
            lines.extend([calibration["reason"], ""])
            continue
        lines.extend([calibration["interpretation"], ""])
        lines.extend(_table(
            ["Probability bin", "Case-role observations", "Mean P(true)", "Expected-role frequency", "Absolute gap"],
            [
                [
                    f"[{item['lower']:.1f}, {item['upper']:.1f}{']' if item['upper_inclusive'] else ')'}",
                    item["count"], _decimal(item["mean_probability"]),
                    _decimal(item["benchmark_positive_frequency"]), _decimal(item["absolute_gap"]),
                ]
                for item in calibration["reliability"]
            ],
        ))
    lines.extend(["## Latency and provider tokens", ""])
    lines.extend([
        "All values are seconds. Full-case totals require one uniquely identified "
        "attempt for every expected hunk or case batch, whether that attempt "
        "succeeded or failed. They are unknown if a required attempt or component "
        "timing is absent. Prediction validity is independent of timing coverage. "
        "Known recorded-attempt sums are shown separately for partial cases and "
        "never imply a measured full-case duration. Recorded call duration includes "
        "question-encoding preflight. Cold/warm rows describe the "
        "recorded call phases, not invented repeated trials. CPU is the runner's "
        "recorded process CPU time; remote service CPU is unknown. Failed attempted "
        "calls remain in operational call and token totals. Model provisioning and "
        "load costs are reported separately when supplied in run metadata. Cold "
        "means the first inference in a fresh process; the operating-system page "
        "cache is not flushed. Repeated warm timing samples, when recorded, "
        "do not add prediction votes or calibration observations.",
        "",
    ])
    lines.extend(_table(
        ["Implementation", "Phase", "Timed calls / calls", "Wall total", "Wall mean", "CPU total"],
        [
            [
                key, phase,
                f"{item['wall']['known_count']}/{item['wall']['count']}",
                _decimal(item["wall"]["total_seconds"]),
                _decimal(item["wall"]["mean_seconds"]),
                _decimal(item["cpu"]["total_seconds"]),
            ]
            for key, model in models.items()
            for phase, item in model["latency"]["by_phase"].items()
        ],
    ))
    lines.extend(_table(
        ["Implementation", "Case", "Prediction status", "Timing coverage",
         "Full wall", "Full CPU", "Cold wall", "Cold CPU", "Warm wall", "Warm CPU",
         "Known recorded-attempt wall", "Known recorded-attempt CPU"],
        [
            [
                key, case["case_id"], case["status"],
                (
                    f"{case['operational_timing']['coverage']} "
                    f"({case['operational_timing']['attempted_records']}/"
                    f"{case['operational_timing']['expected_records']} records)"
                ),
                _decimal(case["wall_seconds"]), _decimal(case["cpu_seconds"]),
                _decimal(case["latency_by_phase"]["cold"]["wall_seconds"]),
                _decimal(case["latency_by_phase"]["cold"]["cpu_seconds"]),
                _decimal(case["latency_by_phase"]["warm"]["wall_seconds"]),
                _decimal(case["latency_by_phase"]["warm"]["cpu_seconds"]),
                _decimal(case["operational_timing"]["observed_attempts"]["wall"]["known_total_seconds"]),
                _decimal(case["operational_timing"]["observed_attempts"]["cpu"]["known_total_seconds"]),
            ]
            for key, model in models.items() for case in model["case_results"]
        ],
    ))
    lines.extend(_table(
        ["Implementation", "Attempted calls", "Provider input tokens", "Provider output tokens"],
        [
            [key, model["provider_usage"]["calls"],
             model["provider_usage"]["input_tokens"], model["provider_usage"]["output_tokens"]]
            for key, model in models.items() if model["impl"] == "llm"
        ],
    ))
    lines.extend(["Provisioning/load evidence: " + _cell(metadata.get("provisioning")), ""])
    if metadata.get("timing_repeats"):
        lines.extend(["Repeated warm timing evidence: " + _cell(metadata["timing_repeats"]), ""])
    lines.extend(["## Coverage, anomalies and authorization gates", ""])
    unavailable = [
        [key, case["case_id"], case["reason"]]
        for key, model in models.items() for case in model["case_results"]
        if case["status"] != "complete"
    ]
    if unavailable:
        lines.extend(_table(["Implementation", "Unavailable case", "Reason"], unavailable))
    all_anomalies = [("scoring", item) for item in scored["anomalies"]]
    supplied_anomalies = metadata.get("anomalies", [])
    all_anomalies.extend(
        ("execution", item)
        for item in (supplied_anomalies if isinstance(supplied_anomalies, list) else [supplied_anomalies])
    )
    all_anomalies.extend(
        ("original dataset provenance" if adapted else "dataset", item)
        for item in dataset.get("anomalies", [])
    )
    all_anomalies.extend(
        ("original catalog extraction provenance" if adapted else "catalog", item)
        for item in catalog.get("anomalies", [])
    )
    all_anomalies.extend(
        (f"{key} / {case['case_id']}", message)
        for key, model in models.items()
        for case in model["case_results"] for message in case["anomalies"]
    )
    if all_anomalies:
        lines.extend(_table(["Anomaly source", "Recorded evidence"], [list(item) for item in all_anomalies]))
    else:
        lines.extend(["Recorded anomalies: none recorded.", ""])
    lines.extend(["Authorization gates: " + _cell(metadata.get("gates", "unknown")), ""])
    lines.extend(["## Verdict and token economics", "", scored["verdict"]["text"], ""])
    lines.extend(_table(
        ["Critical role", "Paired labeled support", "A false negatives", "B false negatives", "B no worse than A"],
        [
            [
                role, value["paired_support"],
                value["baseline_false_negatives"] if value["paired_support"] else None,
                value["candidate_false_negatives"] if value["paired_support"] else None,
                value["candidate_not_worse"],
            ]
            for role, value in scored["critical_comparison"].items()
        ],
    ))
    lines.extend([
        "Net tokens saved per run = tier1 Choicer tokens avoided + tier2/tier3 "
        "tokens avoided by finer routing - routing-error and retry token costs. "
        "Net savings: unknown. " + scored["verdict"]["net_savings_reason"],
        "",
        "This small, fixed case set is a pilot. It can inform whether to open "
        "shadow observation on the Decision Log. It cannot establish statistical "
        "non-inferiority, downstream token savings or promotion to default. "
        "The model-card benchmark scores are excluded from that decision.",
        "",
        "## Proposed spec update",
        "",
        "Revise sections 7.5/8 to distinguish the reviewer-activation pilot's "
        "partial positive dimension labels from exhaustive trigger labels: the "
        "credential-refill precision case has no activation labels and must be "
        "excluded from accuracy and calibration, while excess activations and "
        "ECE remain descriptive proxies until all legitimate triggers are "
        "adjudicated. Keep the noul threshold fixed before evaluation, aggregate "
        "probabilities once per case and role, compare only paired complete cases, "
        "and report absent critical-role support explicitly. The verbatim LLM "
        "prompt supplies selections rather than probabilities, so its ECE is "
        "unavailable; categorical choice scores do not substitute for binary "
        "probabilities. Preserve the offline pilot as a gate to considering "
        "Decision Log shadow observation only, and require measured downstream "
        "review/retry costs, positive net token savings and adequate critical-role "
        "coverage before any promotion."
        + (
            " Keep separately authored criteria and capacity-selected subsets in "
            "distinct experiments with preserved originals, and require a matched "
            "baseline on the adapted catalog before drawing controlled comparisons."
            if adapted else ""
        ),
        "",
    ])
    return "\n".join(lines)
