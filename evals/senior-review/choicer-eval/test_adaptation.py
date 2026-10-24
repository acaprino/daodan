"""Protect source binding and the outcome-independent subset rule."""
import copy
import tempfile
import unittest
from pathlib import Path

from prepare_adapted import adapted_catalog, context_subset
from test_inputs import fixture
import run_eval
from run_eval import build_requests


class AdaptationTests(unittest.TestCase):
    def test_original_criteria_mismatch_rejected(self):
        _, catalog, _ = fixture()
        edits = [{
            "id": role["id"],
            "original": {"true": role["trigger_when"], "false": role["do_not_trigger_when"]},
            "adapted": {"true": "Positive", "false": "Negative"},
            "choice_description": "Choice",
        } for role in catalog["roles"] if role["is_reviewer"]]
        changed = adapted_catalog(catalog, {"reviewers": edits})
        self.assertEqual(changed["roles"][0]["trigger_when"], "Positive")
        self.assertNotEqual(catalog["roles"][0]["trigger_when"], "Positive")
        edits[0]["original"]["true"] = "Different source"
        with self.assertRaisesRegex(ValueError, "not bound"):
            adapted_catalog(catalog, {"reviewers": edits})

    def test_whole_case_exclusion_uses_only_capacity(self):
        dataset, _, _ = fixture()
        second = copy.deepcopy(dataset["cases"][0])
        second["id"] = "C02"
        dataset["cases"].append(second)
        capacity = {"hunks": [{
            "case_id": case["id"], "hunk_id": hunk["id"],
            "state_alone_exceeds_sequence_limit": case["id"] == "C02" and hunk["id"] == "H2",
        } for case in dataset["cases"] for hunk in case["hunks"]]}
        subset, excluded = context_subset(dataset, capacity)
        self.assertEqual([case["id"] for case in subset["cases"]], ["C01"])
        self.assertEqual(subset["cases"][0], dataset["cases"][0])
        self.assertEqual(len(excluded), 1)
        capacity["hunks"].pop()
        with self.assertRaisesRegex(ValueError, "every original hunk"):
            context_subset(dataset, capacity)

    def test_compact_choice_is_explicit_and_does_not_change_binary(self):
        dataset, catalog, prompts = fixture()
        before = build_requests(dataset, catalog, prompts, "julia", "noul")
        catalog["roles"][0]["choice_description"] = "Compact choice"
        after = build_requests(dataset, catalog, prompts, "julia", "noul")
        self.assertEqual(before, after)
        choice = build_requests(dataset, catalog, prompts, "julia", "choice")
        self.assertEqual(choice[0]["questions"]["reviewer"]["criteria"]["example:first"], "Compact choice")

    def test_scoring_rejects_records_from_a_different_catalog(self):
        dataset, catalog, prompts = fixture()
        with tempfile.TemporaryDirectory(dir=run_eval.BASE) as directory:
            root = Path(directory)
            request = build_requests(dataset, catalog, prompts, "llm", "noul")[0]
            request["request_sha256"] = run_eval.digest(run_eval.encoded(request))
            run_eval.write_json(root / "requests/llm/noul/C01-batch.json", request)
            record = run_eval.base_record(request)
            run_eval.write_json(root / "results/llm/noul/C01-batch.json", record)
            self.assertEqual(len(run_eval.verified_results(root, dataset, catalog, prompts)), 1)
            catalog["roles"][0]["trigger_when"] = "Changed criterion"
            with self.assertRaisesRegex(ValueError, "binding failed"):
                run_eval.verified_results(root, dataset, catalog, prompts)


if __name__ == "__main__":
    unittest.main()
