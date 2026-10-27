from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import tools_campaign as tools


def response(case, required_only=True):
    flat = tools._arm(case)
    required = {name for group in case["oracle"]["required_groups"] for name in group}
    selected = {key: tool for key, tool in zip(flat["questions"], flat["state"]["available_tools"])}
    family_names = {tool["family"] for tool in selected.values() if tool["id"] in required}
    return {
        "T1": {"model": tools.MODEL, "answers": {
            key: {"type": "noul", "noul": 1.0 if not required_only or tool["id"] in required else 0.0}
            for key, tool in selected.items()}},
        "T2-families": {"model": tools.MODEL, "answers": {
            "f_" + family: {"type": "noul", "noul": 1.0 if not required_only or family in family_names else 0.0}
            for family in tools.FAMILIES}},
    }


class ToolCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = tools.build_cases()

    def synthetic(self, workflow="verify_candidate", progress="not_started", access="all_available"):
        return next(case for case in self.cases if case.get("factors") == {
            "workflow": workflow, "progress": progress, "access": access})

    def test_provenance_component_splits_and_budget(self):
        self.assertEqual(len(self.cases), 600)
        self.assertEqual(Counter(case["split"] for case in self.cases),
                         {"development": 120, "calibration": 120, "verification": 360})
        groups = defaultdict(set)
        functions = defaultdict(set)
        for case in self.cases:
            groups[case["family_id"]].add(case["split"])
            self.assertTrue(case["provenance"]["public"])
            self.assertLessEqual(len(tools._arm(case)["questions"]), 13)
            self.assertEqual(len(tools._arm(case, "T2-families")["questions"]), 5)
            if case["provenance"]["kind"] != "controlled_synthetic":
                self.assertEqual(case["provenance"]["license"], "Apache-2.0")
                for name in case["catalog"]:
                    functions[name.lower()].add(case["split"])
        self.assertTrue(all(len(splits) == 1 for splits in groups.values()))
        self.assertTrue(all(len(splits) == 1 for splits in functions.values()))
        self.assertEqual(len(groups), 67)
        self.assertEqual(sum(len(arm["questions"]) for case in self.cases for arm in case["arms"]), 6921)

    def test_exact_and_or_capabilities(self):
        case = self.synthetic()
        records = response(case)
        state = tools._arm(case)["state"]
        keys = {tool["id"]: key for key, tool in zip(tools._arm(case)["questions"], state["available_tools"])}
        records["T1"]["answers"][keys["git.diff"]]["noul"] = 0
        score = tools.score_case(case, records)["strategies"]["T1"]
        self.assertTrue(score["success"], "fs.read must satisfy the OR alternative")
        records["T1"]["answers"][keys["test.run"]]["noul"] = 0
        score = tools.score_case(case, records)["strategies"]["T1"]
        self.assertFalse(score["success"])
        self.assertEqual(score["critical_errors"], 1)

    def test_family_false_gate_loses_required_tools(self):
        case = self.synthetic()
        records = response(case)
        for answer in records["T2-families"]["answers"].values():
            answer["noul"] = 0
        score = tools.score_case(case, records)["strategies"]
        self.assertTrue(score["T1"]["success"])
        self.assertFalse(score["T2"]["success"])
        self.assertGreater(score["T2"]["critical_errors"], 0)

    def test_invalid_response_fallback_is_not_raw_credit(self):
        case = self.synthetic()
        missing_model = deepcopy(response(case)["T1"])
        missing_model.pop("model")
        for invalid in (None, {"answers": {}}, {"model": "wrong", "answers": {}},
                        missing_model,
                        {"answers": {key: {"type": "noul", "noul": True} for key in tools._arm(case)["questions"]}}):
            score = tools.score_case(case, {"T1": invalid})["strategies"]
            self.assertFalse(score["T1"]["valid_response"])
            self.assertFalse(score["T1"]["success"])
            self.assertTrue(score["T1-protected"]["fallback"])
            self.assertTrue(score["T1-protected"]["success"])

    def test_public_oracle_never_invents_negative_label(self):
        case = next(case for case in self.cases if case["oracle"]["kind"] == "sufficient_witness")
        records = response(case)
        for answer in records["T1"]["answers"].values():
            answer["noul"] = 0
        score = tools.score_case(case, records)["strategies"]["T1"]
        self.assertIsNone(score["success"])
        self.assertEqual(score["critical_errors"], 0)
        self.assertFalse(score["witness_coverage"])
        self.assertTrue(score["sufficiency_unknown"])

    def test_permissions_and_missing_provider_are_not_model_errors(self):
        case = self.synthetic("apply_patch", access="writes_revoked")
        self.assertNotIn("fs.patch", case["catalog"])
        score = tools.score_case(case, response(case))["strategies"]["T1"]
        self.assertFalse(score["eligible"])
        self.assertIsNone(score["success"])
        self.assertEqual(score["critical_errors"], 0)
        discover = self.synthetic("research_web", access="read_provider_discoverable")
        result = tools.score_case(discover, response(discover))["strategies"]["T4"]
        self.assertTrue(result["discovery_requested"])
        self.assertFalse(result["discovery_completed"])
        self.assertFalse(result["goal_completion_demonstrated"])

    def test_completed_and_stale_candidate_context(self):
        completed = self.synthetic(progress="all_complete")
        stale = self.synthetic(progress="different_target")
        self.assertEqual(completed["oracle"]["required_groups"], [])
        self.assertEqual(len(stale["oracle"]["required_groups"]), 2)
        score = tools.score_case(completed, response(completed))["strategies"]
        self.assertTrue(score["T1"]["success"])
        self.assertEqual(score["T1"]["selected"], [])
        self.assertLess(score["T1"]["utility_cost"], score["T0"]["utility_cost"])

    def test_completed_later_steps_respect_causal_dependencies(self):
        located = self.synthetic("research_web", progress="last_step_complete")
        self.assertEqual(located["oracle"]["required_groups"], [], "Retrieved official document includes its URL")
        pending_edit = self.synthetic("apply_patch", progress="last_step_complete")
        self.assertEqual(pending_edit["oracle"]["required_groups"], [["fs.patch"], ["test.run"]])
        self.assertIn("before the pending correction", tools._arm(pending_edit)["state"]["evidence"]["completed_step_receipts"])

    def test_runtime_plan_uses_input_not_oracle(self):
        case = self.synthetic()
        changed = deepcopy(case)
        changed["oracle"]["required_groups"] = [["email.send"]]
        self.assertEqual(tools.tool_runtime_plan(case), tools.tool_runtime_plan(changed))
        plan = tools.tool_runtime_plan(case)
        self.assertEqual(set(plan["family_for_question"]), set(tools._arm(case)["questions"]))
        self.assertLessEqual(len(plan["retrieval_question_ids"]), 4)
        self.assertTrue(set(plan["family_for_question"].values()) <= set(tools._arm(case, "T2-families")["questions"]))

    def test_robustness_preserves_groups_and_alias_oracles(self):
        auxiliaries = tools.build_auxiliary(self.cases)
        self.assertEqual(len(auxiliaries), 480)
        base = {case["id"]: case for case in self.cases}
        for case in auxiliaries:
            parent = base[case["base_case_id"]]
            self.assertEqual(case["family_id"], parent["family_id"])
            self.assertEqual(case["split"], parent["split"])
            self.assertEqual(len(case["arms"]), 1)
            if case["oracle"]["metric_eligible"]:
                self.assertTrue(tools.score_case(case, response(case))["strategies"]["T1"]["success"])

    def test_calibration_does_not_read_verification_responses(self):
        cases = [self.synthetic()]
        cases[0] = deepcopy(cases[0])
        cases[0]["split"] = "calibration"
        verification = deepcopy(cases[0])
        verification.update(id="verification-secret", split="verification")
        first = tools.select_policy(cases, {cases[0]["id"]: response(cases[0])})
        second = tools.select_policy(cases + [verification], {cases[0]["id"]: response(cases[0]), "verification-secret": None})
        self.assertEqual(first, second)
        self.assertTrue(first["selection_evidence"]["selected_admissible"])
        with self.assertRaises(ValueError):
            tools.select_policy([verification], {})

    def test_source_hash_tamper_rejected(self):
        with tempfile.TemporaryDirectory(dir=tools.SOURCE, prefix="test-hash-") as folder:
            target = Path(folder)
            self.assertTrue(target.resolve().is_relative_to(tools.SOURCE.resolve()))
            manifest = {"revision": tools.REVISION, "license": "Apache-2.0", "files": [
                {"path": "README.md", "sha256": "0" * 64}]}
            (target / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (target / "README.md").write_text("license: apache-2.0\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                tools.build_cases(target)

    def test_scores_and_auxiliary_do_not_mutate_frozen_cases(self):
        before = tools._digest(self.cases)
        case = self.synthetic()
        records = response(case)
        records_before = tools._digest(records)
        tools.score_case(case, records)
        tools.build_auxiliary(self.cases)
        self.assertEqual(tools._digest(self.cases), before)
        self.assertEqual(tools._digest(records), records_before)


if __name__ == "__main__":
    unittest.main()
