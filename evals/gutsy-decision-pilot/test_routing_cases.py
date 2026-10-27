"""Scorer failures, oracle boundaries, and real routing-owner controls."""
import json
import unittest

import routing_cases as routing


def valid_response(case):
    answers = {}
    expected = case["oracle"]["essential"]
    for key, question in case["questions"].items():
        if question["type"] == "noul":
            answers[key] = {"type": "noul", "noul": 0.99 if expected.get(key, False) else 0.01}
        else:
            options = list(question["criteria"])
            choice = routing._mildest(expected.get(key, options[0]))
            answers[key] = {"type": "choice", "choice": choice,
                            "probabilities": {option: float(option == choice) for option in options},
                            "reject": 0.01}
    return {"answers": answers}


class RoutingPilotTests(unittest.TestCase):
    def setUp(self):
        self.cases = routing.build_cases()

    def test_frozen_shape_and_enum_parity(self):
        self.assertEqual([case["id"] for case in self.cases], [f"R{i:02}" for i in range(1, 16)])
        signals = routing._router().SIGNALS
        for case in self.cases:
            self.assertEqual(set(case["questions"]), set(signals))
            self.assertEqual(sum(q["type"] == "choice" for q in case["questions"].values()), 7)
            for key, question in case["questions"].items():
                if question["type"] == "choice":
                    self.assertEqual(list(question["criteria"]), signals[key])

    def test_no_oracle_or_case_identifier_in_inference_payload(self):
        for case in self.cases:
            payload = json.dumps({"state": case["state"], "questions": case["questions"]})
            self.assertNotIn(case["id"], payload)
            for key in ("oracle", "essential", "critical_signals", "minimum_tier"):
                self.assertNotIn(f'"{key}"', payload)

    def test_partial_oracle_does_not_become_vector_accuracy(self):
        case = self.cases[1]
        response = valid_response(case)
        response["answers"]["risk"]["choice"] = "irreversible"
        response["answers"]["risk"]["probabilities"] = {
            key: float(key == "irreversible") for key in case["questions"]["risk"]["criteria"]}
        scored = routing.score_case(case, response)
        self.assertEqual(scored["essential_support"], len(case["oracle"]["essential"]))
        self.assertEqual(scored["essential_hits"], scored["essential_support"])
        self.assertTrue(scored["all_essential_correct"])
        self.assertIn("risk", scored["unlabeled_signals"])
        self.assertNotIn("output_volume", scored["unlabeled_signals"])

    def test_acceptable_set_admits_each_listed_value_and_nothing_else(self):
        case = self.cases[3]
        self.assertEqual(case["oracle"]["essential"]["work_type"], ["coding", "agent_tool_use"])
        for value, hit in (("coding", True), ("agent_tool_use", True), ("analysis", False)):
            response = valid_response(case)
            response["answers"]["work_type"]["choice"] = value
            response["answers"]["work_type"]["probabilities"] = {
                key: float(key == value) for key in case["questions"]["work_type"]["criteria"]}
            self.assertEqual(routing.score_case(case, response)["essential_matches"]["work_type"], hit)

    def test_every_case_labels_long_context_and_perturbations_copy_their_family(self):
        by_id = {case["id"]: case for case in self.cases}
        for case in self.cases:
            self.assertIs(case["oracle"]["essential"]["long_context"], False)
        self.assertEqual(by_id["R13"]["oracle"]["essential"], by_id["R01"]["oracle"]["essential"])
        self.assertEqual(by_id["R15"]["oracle"]["essential"], by_id["R07"]["oracle"]["essential"])
        self.assertNotIn("most severe", by_id["R01"]["questions"]["work_type"]["instructions"])
        self.assertIn("most severe", by_id["R01"]["questions"]["risk"]["instructions"])

    def test_tier_is_attributed_to_labeled_errors_only_when_correcting_them_moves_it(self):
        case = self.cases[0]
        correct = routing.score_case(case, valid_response(case))
        self.assertFalse(correct["tier_changed_by_labeled_errors"])
        self.assertEqual(correct["tier_with_labeled_corrected"], correct["raw_tier"])
        response = valid_response(case)
        response["answers"]["risk"]["choice"] = "irreversible"
        response["answers"]["risk"]["probabilities"] = {
            key: float(key == "irreversible") for key in case["questions"]["risk"]["criteria"]}
        labeled_miss = routing.score_case(case, response)
        self.assertEqual(labeled_miss["raw_tier"], "tier3")
        self.assertTrue(labeled_miss["tier_changed_by_labeled_errors"])
        self.assertEqual(labeled_miss["tier_with_labeled_corrected"], correct["raw_tier"])
        case = self.cases[8]
        response = valid_response(case)
        response["answers"]["risk"]["choice"] = "irreversible"
        response["answers"]["risk"]["probabilities"] = {
            key: float(key == "irreversible") for key in case["questions"]["risk"]["criteria"]}
        unlabeled_driver = routing.score_case(case, response)
        self.assertEqual(unlabeled_driver["raw_tier"], "tier3")
        self.assertTrue(unlabeled_driver["all_essential_correct"])
        self.assertFalse(unlabeled_driver["tier_changed_by_labeled_errors"])

    def test_missing_boolean_is_invalid_not_false(self):
        case = self.cases[0]
        response = valid_response(case)
        del response["answers"]["tool_use_required"]
        scored = routing.score_case(case, response)
        self.assertNotIn("tool_use_required", scored["classification"])
        self.assertFalse(scored["essential_matches"]["tool_use_required"])
        self.assertTrue(scored["fallback_used"])
        self.assertIsNone(scored["raw_tier"])

    def test_nan_boolean_and_incomplete_distribution_are_invalid(self):
        case = self.cases[0]
        response = valid_response(case)
        response["answers"]["evidence_required"]["noul"] = float("nan")
        del response["answers"]["risk"]["probabilities"]["irreversible"]
        scored = routing.score_case(case, response)
        self.assertEqual(len(scored["invalid_answers"]), 2)

    def test_reject_is_separate_from_diagnostic_argmax(self):
        case = self.cases[0]
        response = valid_response(case)
        response["answers"]["work_type"]["reject"] = 0.9
        scored = routing.score_case(case, response)
        self.assertEqual(scored["classification"]["work_type"], "coding")
        self.assertIn("work_type", scored["native_reject_dominant"])
        self.assertEqual(scored["conservative_tier"], "tier3")

    def test_unrelated_high_signal_does_not_hide_critical_misclassification(self):
        case = self.cases[6]
        response = valid_response(case)
        response["answers"]["risk"]["choice"] = "reversible_local"
        response["answers"]["risk"]["probabilities"] = {
            value: float(value == "reversible_local") for value in case["questions"]["risk"]["criteria"]}
        depth = response["answers"]["reasoning_depth"]
        depth["choice"] = "architectural"
        depth["probabilities"] = {value: float(value == "architectural")
                                  for value in case["questions"]["reasoning_depth"]["criteria"]}
        scored = routing.score_case(case, response)
        self.assertEqual(scored["raw_tier"], "tier3")
        self.assertTrue(scored["critical_failures"])

    def test_families_stay_in_one_split(self):
        family_splits = {}
        for case in self.cases:
            family_splits.setdefault(case["oracle"]["family"], set()).add(case["split"])
        self.assertTrue(all(len(value) == 1 for value in family_splits.values()))

    def test_deterministic_owner_floors_and_missing_capability(self):
        result = routing.deterministic_checks()
        self.assertTrue(result["pass"], result)
        self.assertEqual(len(result["floors"]), 5)
        self.assertEqual(len(result["missing_capabilities"]), 3)
        self.assertTrue(all(row["no_binding"] for row in result["missing_capabilities"]))


if __name__ == "__main__":
    unittest.main()
