import json
import os
import shutil
import unittest

import compaction_cases as cc


class TranscriptInputs(unittest.TestCase):
    def test_collision_has_equal_metadata_but_different_evidence(self):
        specs = cc.transcript_specs()
        first, second = specs[:2]
        self.assertEqual(first["goal"], second["goal"])
        a = first["messages"][2]["toolResults"][0]["text"]
        b = second["messages"][2]["toolResults"][0]["text"]
        self.assertEqual(len(a), 600)
        self.assertEqual(len(a), len(b))
        self.assertIn("LEASE_EXPIRED", a)
        self.assertNotIn("LEASE_EXPIRED", b)
        self.assertEqual(first["messages"][1], second["messages"][1])

    def test_variants_share_verification_split_and_tail_exceeds_truncation(self):
        specs = {s["id"]: s for s in cc.transcript_specs()}
        self.assertEqual(specs["C05"]["split"], specs["C06"]["split"])
        for case in ["C01", "C05", "C08"]:
            text = specs[case]["messages"][2]["toolResults"][0]["text"]
            self.assertEqual(len(text), 600)
            for token in specs[case]["oracle"]["required_tokens"]:
                self.assertNotIn(token, text[:300])

    def test_structurally_preserved_facts_are_not_decision_bearing(self):
        bearing = {s["id"]: cc.decision_bearing(s["messages"], s["oracle"]["required_tokens"])
                   for s in cc.transcript_specs()}
        self.assertEqual({k for k, v in bearing.items() if v}, {"C01", "C05", "C06", "C07", "C08"})
        self.assertEqual({k for k, v in bearing.items() if not v}, {"C02", "C03", "C04"})

    def test_invalid_answers_never_turn_into_negative_evidence(self):
        case = {"questions": {"call_t1": {"type": "noul"}}}
        for value in [None, True, -0.1, 1.1, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                cc._validate_response(case, {"answers": {"call_t1": {"noul": value}}})


@unittest.skipUnless((os.environ.get("NODE_BINARY") or shutil.which("node")) and os.environ.get("FAST_JEV_MODULE"), "Pinned upstream module not configured")
class UpstreamIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = cc.build_cases()

    def test_actual_upstream_collision_pinning_and_no_oracle_in_input(self):
        cases = {c["id"]: c for c in self.cases}
        self.assertEqual(len(self.cases), 16)
        self.assertEqual(cases["C01-A"]["state"], cases["C02-A"]["state"])
        self.assertNotEqual(cases["C01-B"]["state"], cases["C02-B"]["state"])
        for case in self.cases:
            self.assertEqual(len(case["questions"]), 2)
            transmitted = json.dumps({"state": case["state"], "questions": case["questions"]})
            self.assertNotIn('"oracle"', transmitted)
            self.assertNotIn('"critical"', transmitted)
            self.assertNotIn(case["id"], transmitted)

    def test_drop_loses_tail_and_guardrail_does_not_mask_raw_loss(self):
        case = next(c for c in self.cases if c["id"] == "C08-B")
        answers = {key: {"noul": 0.0} for key in case["questions"]}
        score = cc.score_case(case, {"answers": answers})
        self.assertTrue(score["critical_failures"])
        self.assertFalse(score["evidence_preserved_raw"])
        self.assertEqual(score["protected_missing_facts"], [])

    def test_actual_library_contracts(self):
        result = cc.deterministic_checks()
        self.assertTrue(result["pass"], result)


if __name__ == "__main__":
    unittest.main()
