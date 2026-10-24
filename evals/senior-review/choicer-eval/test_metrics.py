"""Hand-computable adversarial scoring regressions, requiring only unittest."""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("metrics.py")
SPEC = importlib.util.spec_from_file_location("choicer_metrics_under_test", MODULE_PATH)
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)

SECURITY = "senior-review:security-auditor"
PREMISE = "senior-review:premise-auditor"
DATA = "senior-review:data-integrity-auditor"
OTHER = "senior-review:other-auditor"
ROLES = [SECURITY, PREMISE, DATA, OTHER]


def prediction(case_id, hunk_id, probabilities, *, impl="julia", variant="noul", selected=None):
    if selected is None:
        selected = [role for role, probability in zip(ROLES, probabilities) if probability >= 0.5]
    return {
        "impl": impl, "variant": variant, "case_id": case_id, "hunk_id": hunk_id,
        "status": "ok", "phase": "warm", "selected": selected,
        "probabilities": dict(zip(ROLES, probabilities)) if probabilities is not None else None,
        "wall_seconds": 2.0, "cpu_seconds": 0.5, "usage": None,
    }


class ScoringEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "roles": [{"id": role, "is_reviewer": True} for role in ROLES],
            "anomalies": [{"kind": "missing_negative", "role": OTHER}],
        }
        self.dataset = {
            "cases": [
                {
                    "id": "C01", "source_case": "positive-two-hunks",
                    "label_status": "labeled", "expected_roles": [SECURITY, DATA],
                    "hunks": [{"id": "H1"}, {"id": "H2"}],
                },
                {
                    "id": "C02", "source_case": "missed-data",
                    "label_status": "labeled", "expected_roles": [DATA],
                    "hunks": [{"id": "H1"}],
                },
                {
                    "id": "C03", "source_case": "unlabeled-precision-only",
                    "label_status": "unlabeled", "expected_roles": [],
                    "hunks": [{"id": "H1"}],
                },
                {
                    "id": "C04", "source_case": "incomplete",
                    "label_status": "labeled", "expected_roles": [SECURITY],
                    "hunks": [{"id": "H1"}, {"id": "H2"}],
                },
            ],
            "dimension_mapping": {"security": SECURITY, "data-integrity": DATA},
            "protocol": {"hunk_rule": "Keep verbatim contiguous changed blocks."},
            "anomalies": [{"kind": "missing_companion_schema"}],
        }
        self.local = [
            prediction("C01", "H1", [0.5, 0.1, 0.2, 0.4]),
            prediction("C01", "H2", [0.3, 0.4, 0.8, 0.2]),
            prediction("C02", "H1", [0.7, 0.2, 0.1, 0.6]),
            prediction("C03", "H1", [0.99, 0.99, 0.99, 0.99]),
            prediction("C04", "H1", [0.0, 0.0, 0.0, 0.0]),
        ]
        self.baseline = [
            prediction("C01", None, None, impl="llm", selected=[SECURITY, PREMISE, DATA]),
            prediction("C02", None, None, impl="llm", selected=[DATA]),
            prediction("C03", None, None, impl="llm", selected=ROLES),
        ]

    def score(self, records=None):
        return metrics.score(self.dataset, self.catalog, self.local if records is None else records)

    def test_missing_and_incomplete_predictions_are_not_negative_labels(self):
        result = self.score()["models"]["julia/noul"]
        self.assertEqual(result["complete_cases"], 3)
        self.assertEqual(result["metrics"]["labeled_cases"], 2)
        self.assertEqual(result["metrics"]["expected_role_activations"], 3)
        self.assertEqual(result["metrics"]["matched_expected_roles"], 2)
        self.assertEqual(result["metrics"]["false_negatives"], 1)
        self.assertAlmostEqual(result["metrics"]["expected_role_recall"], 2 / 3)
        self.assertEqual(result["case_results"][3]["status"], "unavailable")
        self.assertIsNone(result["case_results"][3]["selected"])
        missing = self.score([])["models"]["julia/noul"]["metrics"]
        self.assertIsNone(missing["expected_role_recall"])
        self.assertIsNone(missing["benchmark_excess_per_case"])

    def test_threshold_is_inclusive_and_maximum_is_per_case_role(self):
        first = self.score()["models"]["julia/noul"]["case_results"][0]
        self.assertEqual(first["selected"], sorted([SECURITY, DATA]))
        self.assertEqual(first["probabilities"], dict(zip(ROLES, [0.5, 0.4, 0.8, 0.4])))
        with self.assertRaisesRegex(ValueError, "locked"):
            metrics.score(self.dataset, self.catalog, self.local, threshold=0.6)

    def test_case_role_ece_matches_independent_arithmetic(self):
        calibration = self.score(self.local[:2])["models"]["julia/noul"]["calibration"]
        # Max probabilities (.5, .4, .8, .4) have labels (1, 0, 1, 0).
        # Each occupied bin has only one label value: (.5 + .4 + .2 + .4) / 4.
        self.assertEqual(calibration["observation_count"], 4)
        self.assertAlmostEqual(calibration["ece"], 0.375)
        all_calibration = self.score()["models"]["julia/noul"]["calibration"]
        # The second labeled case adds errors .7, .2, .9, .6.
        self.assertEqual(all_calibration["observation_count"], 8)
        self.assertAlmostEqual(all_calibration["ece"], 3.9 / 8)
        self.assertEqual(sum(row["count"] for row in all_calibration["reliability"]), 8)
        self.assertNotIn("C03", {point["case_id"] for point in all_calibration["observations"]})
        self.assertNotIn("C04", {point["case_id"] for point in all_calibration["observations"]})

    def test_unlabeled_case_does_not_add_false_activation_or_premise_support(self):
        result = self.score()["models"]["julia/noul"]["metrics"]
        self.assertEqual(result["benchmark_excess_activations"], 2)
        self.assertEqual(result["benchmark_excess_per_case"], 1)
        self.assertEqual(result["critical"][PREMISE]["support"], 0)
        self.assertIsNone(result["critical"][PREMISE]["recall"])
        self.assertEqual(result["critical"][DATA]["support"], 2)
        self.assertEqual(result["critical"][DATA]["recall"], 0.5)

    def test_paired_comparison_uses_only_shared_complete_predictions(self):
        result = self.score(self.local + self.baseline)
        pair = next(
            value for value in result["comparisons"].values()
            if {value["left"], value["right"]} == {"llm/noul", "julia/noul"}
        )
        self.assertEqual(pair["paired_cases"], 3)
        self.assertEqual(pair["paired_labeled_cases"], 2)
        self.assertEqual(pair["case_results"][0]["jaccard"], 2 / 3)
        self.assertEqual(pair["case_results"][1]["jaccard"], 0)
        self.assertEqual(pair["case_results"][2]["jaccard"], 1)
        self.assertIsNone(pair["case_results"][3]["jaccard"])
        self.assertEqual(pair["exact_agreement_rate"], 1 / 3)
        self.assertEqual(result["critical_comparison"][DATA]["candidate_not_worse"], False)
        self.assertIsNone(result["critical_comparison"][PREMISE]["candidate_not_worse"])
        self.assertEqual(result["verdict"]["decision"], "critical_regression")

    def test_llm_selections_never_become_invented_confidence(self):
        records = copy.deepcopy(self.baseline)
        records[0]["probabilities"] = {role: 1.0 for role in ROLES}
        result = self.score(records)["models"]["llm/noul"]
        self.assertIsNone(result["calibration"]["ece"])
        self.assertFalse(result["calibration"]["available"])
        self.assertIsNone(result["case_results"][0]["probabilities"])
        self.assertTrue(result["case_results"][0]["anomalies"])

    def test_partial_invalid_duplicate_and_failed_batches_stay_unavailable(self):
        mutations = [
            {"probabilities": {SECURITY: 0.5}},
            {"probabilities": dict(zip(ROLES, [math.nan, 0.1, 0.2, 0.4]))},
            {"probabilities": dict(zip(ROLES, [1.01, 0.1, 0.2, 0.4]))},
            {"selected": ["foreign:unknown-role"]},
            {"status": "error"},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                records = copy.deepcopy(self.local[:2])
                records[0].update(mutation)
                result = self.score(records)["models"]["julia/noul"]
                self.assertEqual(result["complete_cases"], 0)
                self.assertIsNone(result["metrics"]["expected_role_recall"])
        duplicate = self.score([*self.local[:2], self.local[0]])["models"]["julia/noul"]
        self.assertEqual(duplicate["complete_cases"], 0)

    def test_choice_argmax_ties_and_union_are_distinct_from_binary_thresholds(self):
        records = [
            prediction("C01", "H1", [0.4, 0.4, 0.1, 0.1], variant="choice", selected=[SECURITY]),
            prediction("C01", "H2", [0.1, 0.1, 0.4, 0.4], variant="choice", selected=[DATA]),
        ]
        result = self.score(records)["models"]["julia/choice"]
        self.assertEqual(result["case_results"][0]["selected"], sorted([SECURITY, DATA]))
        self.assertIsNone(result["calibration"]["ece"])
        records[0]["probabilities"] = dict(zip(ROLES, [0.9, 0.4, 0.1, 0.1]))
        self.assertEqual(self.score(records)["models"]["julia/choice"]["complete_cases"], 0)

    def test_provider_unknowns_and_cold_warm_case_timings_are_preserved(self):
        records = copy.deepcopy(self.local[:2] + self.baseline[:2])
        records[0]["phase"] = "cold"
        records[2]["usage"] = {"input_tokens": 101, "output_tokens": 7}
        result = self.score(records)
        case = result["models"]["julia/noul"]["case_results"][0]
        self.assertEqual(case["wall_seconds"], 4)
        self.assertEqual(case["cpu_seconds"], 1)
        self.assertEqual(case["latency_by_phase"]["cold"]["wall_seconds"], 2)
        self.assertEqual(case["latency_by_phase"]["warm"]["wall_seconds"], 2)
        usage = result["models"]["llm/noul"]["provider_usage"]
        self.assertIsNone(usage["input_tokens"])
        self.assertEqual(usage["known_input_tokens"], 101)
        self.assertEqual(usage["unknown_input_tokens_calls"], 1)
        records[1]["cpu_seconds"] = None
        self.assertIsNone(self.score(records)["models"]["julia/noul"]["case_results"][0]["cpu_seconds"])

    def test_curve_covers_threshold_boundary_without_tuning(self):
        curve = self.score(self.local[:2])["models"]["julia/noul"]["threshold_curve"]
        at_boundary = next(row for row in curve if row["threshold"] == 0.5)
        after_boundary = next(row for row in curve if row["threshold"] == math.nextafter(0.5, math.inf))
        self.assertEqual(at_boundary["expected_role_recall"], 1)
        self.assertEqual(after_boundary["expected_role_recall"], 0.5)
        self.assertEqual(curve[0]["threshold"], 0)
        self.assertEqual(curve[-1]["threshold"], 1)

    def test_warmup_does_not_add_votes_calibration_or_duplicate_cases(self):
        records = self.local[:2] + [dict(self.local[0], phase="warmup")]
        result = self.score(records)["models"]["julia/noul"]
        self.assertEqual(result["complete_cases"], 1)
        self.assertEqual(result["calibration"]["observation_count"], 4)
        self.assertEqual(result["latency"]["calls"]["wall"]["count"], 2)

    def test_empty_report_carries_protocol_source_anomalies_and_unknowns(self):
        result = self.score([])
        text = metrics.render_report(self.dataset, self.catalog, result, {"gates": ["awaiting approval"]})
        self.assertIn("Keep verbatim contiguous changed blocks.", text)
        self.assertIn("missing_companion_schema", text)
        self.assertIn("missing_negative", text)
        self.assertIn("awaiting approval", text)
        self.assertIn("undefined (no labeled support)", text)
        self.assertIn("No paired labeled predictions were measured", text)
        self.assertIn("## Proposed spec update", text)
        self.assertIsNone(result["verdict"]["net_tokens_saved_per_run"])

    def partial_local_records(self):
        records = copy.deepcopy(self.local)
        for record in records:
            values = record["probabilities"]
            record.update(
                status="error", probabilities=None, selected=[],
                question_errors={PREMISE: "ValueError: Option exceeds 48-token model contract"},
                encoding={
                    role: {"stateTruncated": False, "optionsTruncated": False}
                    for role in ROLES if role != PREMISE
                },
                raw_output={"answers": {
                    role: {
                        "type": "noul",
                        "probabilities": {"false": 1 - values[role], "true": values[role]},
                        "noul": values[role],
                    }
                    for role in ROLES if role != PREMISE
                }},
            )
        return records

    def test_partial_diagnostic_does_not_repair_primary_metrics(self):
        result = self.score(self.partial_local_records())
        primary = result["models"]["julia/noul"]
        self.assertEqual(primary["complete_cases"], 0)
        self.assertIsNone(primary["metrics"]["expected_role_recall"])
        self.assertIsNone(primary["calibration"]["ece"])
        diagnostic = result["partial_capability_diagnostics"]["julia/noul"]
        data = diagnostic["roles"][DATA]
        self.assertEqual(data["scored_positive_support"], 2)
        self.assertEqual(data["true_positives"], 1)
        self.assertEqual(data["false_negatives"], 1)
        self.assertEqual(data["expected_role_recall"], 0.5)
        security = diagnostic["roles"][SECURITY]
        self.assertEqual(security["scored_positive_support"], 1)
        self.assertEqual(security["expected_role_recall"], 1)
        self.assertEqual(security["missing_positive_cases"], ["C04"])
        premise = diagnostic["roles"][PREMISE]
        self.assertEqual(premise["scored_positive_support"], 0)
        self.assertIsNone(premise["expected_role_recall"])
        self.assertEqual(premise["encoding_rejections"], 5)
        self.assertEqual(result["verdict"]["decision"], "incompatible_exact_catalog")
        self.assertEqual(result["verdict"]["incompatible_critical_roles"], [PREMISE])

    def test_partial_diagnostic_requires_valid_accepted_answer_from_every_hunk(self):
        mutations = ("truncate", "missing_encoding", "bad_probability", "question_error")
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                records = self.partial_local_records()
                target = records[1]
                if mutation == "truncate":
                    target["encoding"][DATA]["stateTruncated"] = True
                elif mutation == "missing_encoding":
                    del target["encoding"][DATA]
                elif mutation == "bad_probability":
                    target["raw_output"]["answers"][DATA]["probabilities"]["true"] = math.nan
                else:
                    target["question_errors"][DATA] = "Input unsupported"
                result = self.score(records)["partial_capability_diagnostics"]["julia/noul"]["roles"][DATA]
                self.assertFalse(result["case_results"][0]["complete_for_role"])
                self.assertIsNone(result["case_results"][0]["probability"])
                self.assertEqual(result["scored_positive_support"], 1)
                self.assertEqual(result["expected_role_recall"], 0)

    def test_partial_diagnostic_does_not_infer_successful_encoding_from_predictions(self):
        result = self.score()
        diagnostic = result["partial_capability_diagnostics"]["julia/noul"]
        self.assertEqual(diagnostic["roles"][DATA]["accepted_encodings"], 0)
        self.assertIsNone(diagnostic["roles"][DATA]["expected_role_recall"])
        self.assertEqual(diagnostic["critical_roles_rejected_in_all_observed_encodings"], [])
        self.assertNotEqual(result["verdict"]["decision"], "incompatible_exact_catalog")

    def declared_record(self, case_id, roles):
        return {
            "impl": "llm", "variant": "noul", "case_id": case_id, "hunk_id": None,
            "request_sha256": "request-digest", "status": "error",
            "selected": [], "probabilities": None,
            "error": "Citation snippet is absent at the cited line",
            "raw_output": {
                "request_sha256": "request-digest",
                "response": json.dumps({
                    "mode": "full",
                    "selected": [{"role": role, "trigger_line": "invalid evidence"} for role in roles],
                }),
            },
        }

    def test_unvalidated_declared_roles_do_not_become_primary_predictions(self):
        records = [
            self.declared_record("C01", [SECURITY, DATA]),
            self.declared_record("C02", [DATA]),
            self.declared_record("C03", ROLES),
        ]
        result = self.score(records)
        diagnostic = result["raw_declared_llm_diagnostic"]
        self.assertEqual(diagnostic["available_cases"], 3)
        self.assertEqual(diagnostic["primary_rejected_cases_with_declared_sets"], 3)
        self.assertEqual(diagnostic["metrics"]["labeled_cases"], 2)
        self.assertEqual(diagnostic["metrics"]["expected_role_recall"], 1)
        self.assertEqual(diagnostic["metrics"]["benchmark_excess_activations"], 0)
        self.assertEqual(result["models"]["llm/noul"]["complete_cases"], 0)
        self.assertIsNone(result["models"]["llm/noul"]["metrics"]["expected_role_recall"])
        self.assertEqual(result["verdict"]["decision"], "not_measured")
        self.assertEqual(result["comparisons"]["julia/noul vs llm/noul"]["paired_cases"], 0)

    def test_declared_role_diagnostic_never_drops_unknown_roles_to_salvage_case(self):
        record = self.declared_record("C01", [SECURITY, "foreign:invented"])
        diagnostic = self.score([record])["raw_declared_llm_diagnostic"]
        self.assertEqual(diagnostic["available_cases"], 0)
        self.assertIsNone(diagnostic["metrics"]["expected_role_recall"])
        self.assertIn("unknown", diagnostic["case_results"][0]["reason"])

    def test_declared_role_diagnostic_rejects_ambiguous_or_unbound_raw_records(self):
        record = self.declared_record("C01", [SECURITY])
        self.assertEqual(self.score([record, record])["raw_declared_llm_diagnostic"]["available_cases"], 0)
        record["raw_output"]["request_sha256"] = "different-request"
        diagnostic = self.score([record])["raw_declared_llm_diagnostic"]
        self.assertEqual(diagnostic["available_cases"], 0)
        self.assertIn("digest differs", diagnostic["case_results"][0]["reason"])

    def test_declared_role_diagnostic_unions_duplicate_ids_and_reads_provider_output(self):
        record = self.declared_record("C01", [SECURITY, SECURITY, DATA])
        response = record["raw_output"]["response"]
        record["raw_output"] = {"output": [{"content": [{"type": "output_text", "text": response}]}]}
        diagnostic = self.score([record])["raw_declared_llm_diagnostic"]
        self.assertEqual(diagnostic["case_results"][0]["selected"], sorted([SECURITY, DATA]))
        self.assertEqual(diagnostic["metrics"]["matched_expected_roles"], 2)
        self.assertIsNone(diagnostic["metrics"]["critical"][PREMISE]["recall"])

    def test_adapted_report_describes_authored_criteria_and_excluded_cases(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["cases"] = dataset["cases"][:2]
        dataset["adapted_subset"] = {
            "rule": "Exclude whole cases by tokenizer capacity.",
            "excluded_case_ids": ["C03", "C04"],
            "selection_uses_labels_or_predictions": False,
        }
        catalog = copy.deepcopy(self.catalog)
        catalog["adaptation"] = {
            "kind": "Separately authored criteria", "equivalent_to_original_catalog": False,
        }
        result = metrics.score(dataset, catalog, [])
        report = metrics.render_report(dataset, catalog, result, {})
        self.assertEqual(result["experiment_kind"], "adapted_catalog")
        self.assertEqual(result["verdict"]["decision"], "adapted_unpaired_exploration")
        self.assertIn("tokenizer capacity", report)
        self.assertIn("Separately authored criteria", report)
        self.assertIn("Current trigger criteria, missing negatives", report)
        self.assertIn("Original-catalog A responses are not imported", report)
        self.assertIn("original catalog extraction provenance", report)
        self.assertNotIn("Role criteria are parsed from source frontmatter.", report)
        self.assertNotIn("The same A baseline is compared with both B and C.", report)
        self.assertEqual(result["comparisons"]["julia/noul vs llm/noul"]["paired_cases"], 0)

    def test_adapted_encoding_failures_do_not_claim_original_catalog_failure(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["adaptation"] = {"equivalent_to_original_catalog": False}
        result = metrics.score(self.dataset, catalog, self.partial_local_records())
        self.assertEqual(result["verdict"]["decision"], "incompatible_adapted_catalog")
        self.assertIn("adapted candidate", result["verdict"]["text"])
        self.assertNotIn("exact critical-role", result["verdict"]["text"])

    def test_llm_report_explicitly_limits_evidence_validation_scope(self):
        result = self.score(self.baseline)
        report = metrics.render_report(self.dataset, self.catalog, result, {})
        self.assertIn("side claims are unverified", report)
        self.assertIn("not full schema/evidence conformance", report)
        self.assertIn("A selected (limited checks)", report)
        self.assertIn("llm/noul (limited citation checks)", report)

    def test_fully_attempted_error_case_keeps_operational_wall_cpu_and_phase_totals(self):
        records = copy.deepcopy(self.local[:2])
        for record in records:
            record["status"] = "error"
            record["error"] = "Exact criteria unsupported"
        records[0]["phase"] = "cold"
        result = self.score(records)
        model = result["models"]["julia/noul"]
        case = model["case_results"][0]
        self.assertEqual(case["status"], "unavailable")
        self.assertIsNone(case["selected"])
        self.assertIsNone(model["metrics"]["expected_role_recall"])
        self.assertEqual(case["operational_timing"]["coverage"], "complete")
        self.assertEqual(case["wall_seconds"], 4.0)
        self.assertEqual(case["cpu_seconds"], 1.0)
        self.assertEqual(case["latency_by_phase"]["cold"]["wall_seconds"], 2.0)
        self.assertEqual(case["latency_by_phase"]["warm"]["cpu_seconds"], 0.5)
        self.assertEqual(model["latency"]["fully_attempted_cases"]["case_count"], 1)
        self.assertEqual(model["latency"]["fully_attempted_cases"]["wall"]["total_seconds"], 4.0)
        self.assertEqual(model["latency"]["complete_cases"]["wall"]["count"], 0)
        self.assertEqual(result["comparisons"]["julia/noul vs llm/noul"]["paired_cases"], 0)

    def test_missing_hunk_only_reports_known_recorded_attempt_cost(self):
        record = dict(self.local[0], status="error", phase="cold")
        case = self.score([record])["models"]["julia/noul"]["case_results"][0]
        self.assertEqual(case["operational_timing"]["coverage"], "partial")
        self.assertEqual(case["operational_timing"]["attempted_records"], 1)
        self.assertEqual(case["operational_timing"]["expected_records"], 2)
        self.assertIsNone(case["wall_seconds"])
        self.assertIsNone(case["cpu_seconds"])
        self.assertIsNone(case["latency_by_phase"]["cold"]["wall_seconds"])
        observed = case["operational_timing"]["observed_attempts"]
        self.assertEqual(observed["wall"]["known_total_seconds"], 2.0)
        self.assertEqual(observed["cpu"]["known_total_seconds"], 0.5)
        self.assertEqual(observed["by_phase"]["cold"]["wall"]["known_total_seconds"], 2.0)

    def test_duplicate_or_blocked_hunk_cannot_complete_timing_coverage(self):
        duplicate = self.score([*self.local[:2], self.local[0]])["models"]["julia/noul"]["case_results"][0]
        self.assertEqual(duplicate["operational_timing"]["coverage"], "partial")
        self.assertIsNone(duplicate["wall_seconds"])
        records = copy.deepcopy(self.local[:2])
        records[1].update(status="blocked", wall_seconds=999.0, cpu_seconds=999.0)
        blocked = self.score(records)["models"]["julia/noul"]["case_results"][0]
        self.assertEqual(blocked["operational_timing"]["coverage"], "partial")
        self.assertIsNone(blocked["wall_seconds"])
        self.assertEqual(blocked["operational_timing"]["observed_attempts"]["wall"]["known_total_seconds"], 2.0)

    def test_preflight_error_timings_remain_separate_from_cold_warm_inference(self):
        records = [dict(record, status="error", phase="preflight") for record in self.local[:2]]
        model = self.score(records)["models"]["julia/noul"]
        case = model["case_results"][0]
        self.assertEqual(case["wall_seconds"], 4)
        self.assertEqual(case["latency_by_phase"]["preflight"]["wall_seconds"], 4)
        self.assertIsNone(case["latency_by_phase"]["cold"]["wall_seconds"])
        self.assertIsNone(case["latency_by_phase"]["warm"]["wall_seconds"])
        self.assertEqual(model["latency"]["by_phase"]["preflight"]["wall"]["total_seconds"], 4)


if __name__ == "__main__":
    unittest.main()
