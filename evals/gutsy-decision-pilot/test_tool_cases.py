"""Behavioral checks for selection coverage, fixtures and missing-answer handling."""
import json
import unittest

import tool_cases as tc


def response_for(case, canonical_selected=()):
    selected = set(canonical_selected)
    return {"answers": {name: {"type": "noul", "noul": 0.9 if case["oracle"]["mapping"][name] in selected else 0.1}
                        for name in case["questions"]}}


class ToolCasesTest(unittest.TestCase):
    def setUp(self):
        self.cases = {c["id"]: c for c in tc.build_cases()}

    def test_case_count_and_model_budget(self):
        self.assertEqual(len(self.cases), 16)
        self.assertEqual(len(tc.CATALOG), 14)
        self.assertLessEqual(sum(len(c["questions"]) for c in self.cases.values()), 208)
        for case in self.cases.values():
            self.assertNotIn("tools.discover", case["questions"])
            self.assertNotIn("oracle", case["state"])
            self.assertNotIn("id", case["state"])
            self.assertNotIn("required_groups", json.dumps(case["state"]))

    def test_context_pair_preserves_goal_and_changes_requirement(self):
        first, second = self.cases["T01"], self.cases["T02"]
        self.assertEqual(first["state"]["objective"], second["state"]["objective"])
        self.assertNotEqual(first["state"], second["state"])
        self.assertNotIn("fs.patch", first["questions"])
        self.assertIn("fs.patch", second["questions"])
        self.assertTrue(tc.score_case(first, response_for(first, {"fs.search", "fs.read"}))["sufficiency_raw"])
        self.assertFalse(tc.score_case(second, response_for(second, {"fs.search", "fs.read"}))["sufficiency_raw"])

    def test_or_group_accepts_both_independent_alternatives(self):
        case = self.cases["T03"]
        for alternative in ("git.diff", "fs.read"):
            self.assertTrue(tc.score_case(case, response_for(case, {"test.run", alternative}))["sufficiency_raw"])
        self.assertFalse(tc.score_case(case, response_for(case, {"test.run"}))["sufficiency_raw"])

    def test_permissions_filter_removes_side_effects(self):
        case = self.cases["T09"]
        self.assertNotIn("email.send", case["questions"])
        self.assertIn("email.send", case["oracle"]["prohibited"])
        result = tc.score_case(case, response_for(case, {"email.search"}))
        self.assertEqual(result["prohibited_included"], [])
        self.assertTrue(result["sufficiency_raw"])

    def test_aliases_change_exported_ids_but_not_capability_grading(self):
        case = self.cases["T13"]
        self.assertNotIn("fs.patch", case["questions"])
        result = tc.score_case(case, response_for(case, {"fs.patch", "test.run"}))
        self.assertTrue(result["sufficiency_raw"])
        self.assertEqual(set(result["selected_canonical"]), {"fs.patch", "test.run"})
        self.assertLess(result["schema_bytes_after"], result["schema_bytes_before"])

    def test_missing_answer_is_not_a_negative(self):
        case = self.cases["T02"]
        response = response_for(case, {"fs.patch", "test.run"})
        del response["answers"]["fs.patch"]
        result = tc.score_case(case, response)
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["sufficiency_raw"])
        self.assertTrue(result["sufficiency_policy"])
        self.assertEqual(result["fallback"], "all_eligible_on_invalid")
        self.assertNotIn("fs.patch", result["probabilities"])

    def test_valid_wrong_answer_does_not_trigger_oracle_based_fallback(self):
        case = self.cases["T02"]
        result = tc.score_case(case, response_for(case, set()))
        self.assertFalse(result["sufficiency_raw"])
        self.assertFalse(result["sufficiency_policy"])
        self.assertEqual(result["fallback"], "none")

    def test_bad_probability_and_extra_answer_are_incomplete(self):
        case = self.cases["T05"]
        for bad in (True, -0.01, 1.1, float("nan"), "0.9"):
            response = response_for(case, {"web.fetch"})
            response["answers"]["web.fetch"]["noul"] = bad
            self.assertFalse(tc.score_case(case, response)["complete"])
        response = response_for(case, {"web.fetch"})
        response["answers"]["imaginary.tool"] = {"type": "noul", "noul": 1.0}
        self.assertFalse(tc.score_case(case, response)["complete"])

    def test_discovery_is_next_step_not_completion(self):
        case = self.cases["T15"]
        result = tc.score_case(case, response_for(case))
        self.assertTrue(result["sufficiency_raw"])
        self.assertFalse(result["goal_completion_sufficient"])
        self.assertEqual(result["next_step"], "discovery_required")
        self.assertEqual(result["mandatory_ids"], ["tools.discover"])

    def test_absent_discovery_cannot_claim_sufficient_inventory(self):
        case = self.cases["T16"]
        result = tc.score_case(case, response_for(case))
        self.assertFalse(result["sufficiency_raw"])
        self.assertFalse(result["baseline_sufficient"])
        self.assertEqual(result["next_step"], "blocked")

    def test_no_tool_case_scores_empty_set_as_sufficient(self):
        case = self.cases["T04"]
        result = tc.score_case(case, response_for(case))
        self.assertTrue(result["sufficiency_raw"])
        self.assertTrue(result["exact_sufficient"])
        self.assertEqual(result["selected_ids"], [])
        self.assertEqual(result["schema_bytes_minimal"], 0)

    def test_selecting_everything_is_sufficient_but_not_exact(self):
        case = self.cases["T04"]
        everything = set(case["oracle"]["mapping"].values())
        result = tc.score_case(case, response_for(case, everything))
        self.assertTrue(result["sufficiency_raw"])
        self.assertFalse(result["exact_sufficient"])
        self.assertEqual(result["selected_count"], len(case["questions"]))
        self.assertEqual(set(result["superfluous_canonical"]), everything - {"tools.discover"})

    def test_or_alternatives_are_never_superfluous_and_minimal_bytes_take_the_cheapest(self):
        case = self.cases["T03"]
        result = tc.score_case(case, response_for(case, {"test.run", "git.diff", "fs.read", "fs.search"}))
        self.assertEqual(result["superfluous_canonical"], ["fs.search"])
        self.assertFalse(result["exact_sufficient"])
        schemas = case["oracle"]["schemas"]
        cheapest = min(tc._bytes([schemas["git.diff"]]), tc._bytes([schemas["fs.read"]]))
        self.assertEqual(result["schema_bytes_minimal"], tc._bytes([schemas["test.run"]]) + cheapest)
        self.assertLessEqual(result["schema_bytes_minimal"], result["schema_bytes_after"])


if __name__ == "__main__":
    unittest.main()
