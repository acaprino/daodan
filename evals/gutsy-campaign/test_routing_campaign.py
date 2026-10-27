"""Outcome-focused checks for the routing corpus and conservative routing policy."""
import collections
import copy
import json
import unittest

import routing_campaign as subject


def response_for(case, arm, changes=None, reject=0.0, margin=None):
    questions = next(row for row in case["arms"] if row["id"] == arm)["questions"]
    expected = dict(case["oracle"]["essential"])
    expected.update(changes or {})
    answers = {}
    for key, question in questions.items():
        allowed = subject._router().SIGNALS[key]
        value = expected.get(key, allowed[0])
        value = value[0] if isinstance(value, list) else value
        if isinstance(allowed[0], bool):
            answers[key] = {"type": "noul", "noul": float(value)}
        else:
            probabilities = {option: float(option == value) for option in allowed}
            if margin is not None:
                runner_up = next(option for option in allowed if option != value)
                probabilities[value] = (1 + margin) / 2
                probabilities[runner_up] = (1 - margin) / 2
            answers[key] = {"type": "choice", "choice": value,
                            "probabilities": probabilities, "reject": reject}
    return {"model": subject.MODEL, "answers": answers}


class RoutingCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = subject.build_cases()

    def test_materialized_counts_and_grouped_splits(self):
        self.assertEqual(600, len(self.cases))
        self.assertEqual({"development": 120, "calibration": 120, "verification": 360},
                         dict(collections.Counter(c["split"] for c in self.cases)))
        self.assertEqual(60, len({c["family_id"] for c in self.cases}))
        self.assertEqual(40, len({c["provenance_id"] for c in self.cases}))
        for field in ("family_id", "provenance_id", "template_id"):
            groups = collections.defaultdict(set)
            for case in self.cases:
                groups[case[field]].add(case["split"])
            self.assertTrue(all(len(splits) == 1 for splits in groups.values()), field)
        self.assertEqual(300, sum(c["provenance"]["kind"] == "public_source_derived" for c in self.cases))
        self.assertEqual(60, sum(not c["metadata_applicable"] for c in self.cases))

    def test_substantive_template_banks_do_not_cross_splits(self):
        tasks = collections.defaultdict(set)
        for case in self.cases:
            tasks[case["split"]].add(case["arms"][0]["state"]["task"])
        for left, right in (("development", "calibration"), ("development", "verification"), ("calibration", "verification")):
            self.assertFalse(tasks[left] & tasks[right])
        self.assertTrue(any("order-dependent" in t for t in tasks["verification"]))
        self.assertFalse(any("order-dependent" in t for t in tasks["development"]))

    def test_metadata_uses_available_contract_not_oracle(self):
        case = copy.deepcopy(self.cases[1])
        state = case["arms"][0]["state"]
        before = subject.derive_metadata(state)
        case["oracle"]["essential"]["risk"] = "production_or_data_loss"
        self.assertEqual(before, subject.derive_metadata(state))
        del state["verified_contract"]["requires_tool_interface"]
        self.assertIsNone(subject.derive_metadata(state))
        free = next(c for c in self.cases if not c["metadata_applicable"])
        self.assertEqual(["R1"], [a["id"] for a in free["arms"]])
        outcome = subject.score_case(free, {})["strategies"]["R3"]
        self.assertTrue(outcome["eligible"])
        self.assertFalse(outcome["model_applicable"])
        self.assertTrue(outcome["fallback"])
        self.assertFalse(outcome["success"])

    def test_perfect_residuals_and_canonical_floor(self):
        for variant in (4, 5, 6, 7):
            case = next(c for c in self.cases if c["variant_index"] == variant)
            scored = subject.score_case(case, {"R3": response_for(case, "R3")})["strategies"]["R3"]
            self.assertTrue(scored["success"])
            self.assertEqual("tier3", scored["raw_tier"])
            self.assertEqual(0, scored["critical_errors"])
            self.assertEqual(2, scored["residual_correct"])
            self.assertEqual(8, scored["metadata_correct"])

    def test_missed_adversarial_floor_is_a_critical_error(self):
        case = next(c for c in self.cases if c["variant_index"] == 4)
        scored = subject.score_case(case, {"R3": response_for(case, "R3", {"reasoning_depth": "lookup"})})["strategies"]["R3"]
        self.assertFalse(scored["success"])
        self.assertTrue(scored["floor_missed"])
        self.assertEqual(1, scored["critical_errors"])

    def test_tool_capability_loss_is_distinct_from_tier(self):
        case = next(c for c in self.cases if c["variant_index"] == 1)
        scored = subject.score_case(case, {"R1": response_for(case, "R1", {"tool_use_required": False})})["strategies"]["R1"]
        self.assertEqual(["tool_call"], scored["capability_misses"])
        self.assertGreater(scored["critical_errors"], 0)

    def test_wrong_model_bad_probability_and_missing_reply_are_not_success(self):
        case = self.cases[1]
        valid = response_for(case, "R3")
        wrong_model = copy.deepcopy(valid)
        wrong_model["model"] = "unregistered-model"
        malformed = copy.deepcopy(valid)
        malformed["answers"]["reasoning_depth"]["probabilities"]["lookup"] = float("nan")
        for value in (None, {}, wrong_model, malformed):
            scored = subject.score_case(case, {"R3": value})["strategies"]["R3"]
            self.assertTrue(scored["fallback"])
            self.assertFalse(scored["success"])
            self.assertEqual("tier3", scored["effective_tier"])
            self.assertTrue(scored["invalid_answers"])

    def test_reject_and_low_margin_trigger_abstention_without_false_credit(self):
        case = self.cases[1]
        policy = {"id": "test", "arm": "R3", "max_reject": .15, "min_margin": .15}
        for response in (response_for(case, "R3", reject=.2), response_for(case, "R3", margin=.1)):
            row = subject.score_case(case, {"R3": response}, policy)["strategies"]["R4"]
            self.assertFalse(row["success"])
            self.assertTrue(row["fallback"])
            self.assertEqual(0, row["residual_correct"])
            self.assertEqual(8, row["metadata_correct"])

    def test_calibration_ignores_verification_responses(self):
        calibration = [c for c in self.cases if c["split"] == "calibration"]
        responses = {c["id"]: {arm: response_for(c, arm) for arm in ("R2", "R3")} for c in calibration if c["metadata_applicable"]}
        first = subject.select_policy(self.cases, responses)
        for case in self.cases:
            if case["split"] == "verification":
                responses[case["id"]] = {"R2": {"invalid": "perturbed holdout"}, "R3": None}
        second = subject.select_policy(self.cases, responses)
        self.assertEqual(first, second)
        self.assertEqual(19, len(first["selection"]["candidates"]))
        self.assertEqual(120, len(first["selection"]["case_ids"]))
        self.assertNotEqual("R0", first["policy"]["arm"])
        self.assertEqual("R0", subject.select_policy(calibration, {})["policy"]["arm"])

    def test_auxiliary_stays_grouped_and_changes_only_declared_conditions(self):
        auxiliary = subject.build_auxiliary(self.cases)
        self.assertEqual(480, len(auxiliary))
        bases = {c["id"]: c for c in self.cases}
        for row in auxiliary:
            original = bases[row["base_case_id"]]
            self.assertEqual("verification", row["split"])
            self.assertEqual(original["family_id"], row["family_id"])
            self.assertEqual(original["provenance_id"], row["provenance_id"])
            self.assertEqual(original["oracle"], row["oracle"])
            self.assertEqual(["R3"], [arm["id"] for arm in row["arms"]])
        self.assertEqual(36, len({c["family_id"] for c in auxiliary}))
        self.assertEqual(set(range(9)), {c["variant_index"] for c in auxiliary})
        self.assertTrue(any(c["oracle"]["minimum_tier"] == "tier3" for c in auxiliary))

    def test_scoring_does_not_mutate_inputs(self):
        case = self.cases[4]
        response = {"R3": response_for(case, "R3")}
        before = json.dumps([case, response], sort_keys=True)
        subject.score_case(case, response)
        self.assertEqual(before, json.dumps([case, response], sort_keys=True))


if __name__ == "__main__":
    unittest.main()
