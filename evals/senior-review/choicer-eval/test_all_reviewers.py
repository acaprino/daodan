"""Independent outcome checks for selection accounting and evidence binding."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import all_reviewers_eval as runner
from all_reviewers_eval import (
    decode_answers, make_requests, model_sessions, score_individual, score_team,
    validate_record, validate_state, verify_frozen_inputs,
)


class SelectionAccountingTests(unittest.TestCase):
    def test_allowed_addition_is_not_false_positive_or_exact_required_match(self):
        result = score_team(
            {"required_roles": ["security"], "allowed_roles": ["premise"]},
            ["security", "premise"], {"security", "premise", "ui"},
        )
        self.assertTrue(result["acceptable_team"])
        self.assertFalse(result["exact_required_team"])
        self.assertEqual(result["false_positives"], [])

    def test_missing_required_and_irrelevant_addition_are_both_retained(self):
        result = score_team(
            {"required_roles": ["security", "data"], "allowed_roles": ["premise"]},
            ["data", "ui"], {"security", "data", "premise", "ui"},
        )
        self.assertEqual(result["required_hits"], 1)
        self.assertEqual(result["missing"], ["security"])
        self.assertEqual(result["false_positives"], ["ui"])
        self.assertFalse(result["acceptable_team"])

    def test_unknown_team_member_is_rejected(self):
        with self.assertRaises(ValueError):
            score_team({"required_roles": ["security"], "allowed_roles": []}, ["invented"], {"security"})

    def test_unavailable_individual_predictions_do_not_become_negatives(self):
        result = score_individual([
            {"id": "positive", "expected": True},
            {"id": "missing_positive", "expected": True},
            {"id": "negative", "expected": False},
        ], {"positive": False, "negative": True})
        self.assertEqual(result, {"available": 2, "expected_cases": 3, "tp": 0, "fn": 1, "fp": 1, "tn": 0})

    def test_model_state_rejects_labels_and_reviewer_ids(self):
        state = {"task": "Inspect this module.", "artifacts": [{"path": "a.py", "content": "x = 1\n"}]}
        validate_state(state, {"p:reviewer"})
        with self.assertRaises(ValueError):
            validate_state(state | {"expected": True}, {"p:reviewer"})
        with self.assertRaises(ValueError):
            validate_state(state | {"task": "Call p:reviewer"}, {"p:reviewer"})


class InferenceIntegrityTests(unittest.TestCase):
    def request(self, kind="noul"):
        return {
            "id": "individual-fixture-grounded",
            "sha256": "request-hash",
            "questions": {"p:reviewer": {
                "type": kind, "instructions": "Does this work need review?",
                "criteria": {"false": "Outside this scope.", "true": "Within this scope."},
            }},
        }

    def answer(self, kind="noul", positive=0.75):
        answer = {"type": kind, "probabilities": {"false": 1 - positive, "true": positive}}
        if kind == "noul":
            answer["noul"] = positive
        else:
            answer["choice"] = "true" if positive > 0.5 else "false"
        return {"answers": {"p:reviewer": answer}}

    def record(self):
        return {
            "id": "individual-fixture-grounded", "request_sha256": "request-hash",
            "status": "ok", "inference_performed": True, "model_session_id": "session",
            "raw_output": self.answer(), "probabilities": {"p:reviewer": 0.75},
            "selected": ["p:reviewer"],
        }

    def test_false_first_mapping_and_variant_tie_behavior(self):
        self.assertEqual(decode_answers(self.request(), self.answer(positive=0.5)),
                         ({"p:reviewer": 0.5}, ["p:reviewer"]))
        self.assertEqual(decode_answers(self.request("choice"), self.answer("choice", 0.5)),
                         ({"p:reviewer": 0.5}, []))
        self.assertEqual(decode_answers(self.request(), self.answer(positive=0.2)),
                         ({"p:reviewer": 0.2}, []))

    def test_missing_and_unexpected_answers_cannot_be_scored(self):
        for raw in ({"answers": {}}, {"answers": {"other": self.answer()["answers"]["p:reviewer"]}}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode_answers(self.request(), raw)

    def test_type_mismatch_cannot_silently_become_a_negative(self):
        with self.assertRaisesRegex(ValueError, "Answer type"):
            decode_answers(self.request("choice"), self.answer("noul"))

    def test_choice_must_match_argmax_and_false_first_order(self):
        raw = self.answer("choice")
        raw["answers"]["p:reviewer"]["choice"] = "false"
        with self.assertRaisesRegex(ValueError, "argmax"):
            decode_answers(self.request("choice"), raw)
        request = self.request("choice")
        request["questions"]["p:reviewer"]["criteria"] = {"true": "Within.", "false": "Outside."}
        with self.assertRaisesRegex(ValueError, "false before true"):
            decode_answers(request, self.answer("choice"))

    def test_noul_scalar_must_agree_when_present(self):
        raw = self.answer()
        raw["answers"]["p:reviewer"]["noul"] = 0.1
        with self.assertRaisesRegex(ValueError, "Noul answer"):
            decode_answers(self.request(), raw)

    def test_nonfinite_boolean_and_unnormalized_probabilities_are_rejected(self):
        for probabilities in (
            {"false": 0.1, "true": float("nan")},
            {"false": 0.1, "true": float("inf")},
            {"false": False, "true": True},
            {"false": 0.6, "true": 0.6},
            {"false": -0.1, "true": 1.1},
        ):
            raw = self.answer()
            raw["answers"]["p:reviewer"]["probabilities"] = probabilities
            with self.subTest(probabilities=probabilities), self.assertRaises(ValueError):
                decode_answers(self.request(), raw)

    def test_saved_output_must_match_raw_decisions_and_model_session(self):
        validate_record(self.request(), self.record(), {"session"})
        for change in (
            {"selected": []}, {"probabilities": {"p:reviewer": 0.2}},
            {"inference_performed": False}, {"model_session_id": "unbound"},
            {"id": "different"}, {"request_sha256": "different"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_record(self.request(), self.record() | change, {"session"})

    def test_failed_output_stays_unavailable_instead_of_scoring_partial_answers(self):
        record = self.record() | {"status": "error", "probabilities": None}
        record.pop("selected")
        record["raw_output"] = {"answers": {}}
        validate_record(self.request(), record, {"session"})
        with self.assertRaisesRegex(ValueError, "scored decisions"):
            validate_record(self.request(), record | {"selected": ["p:reviewer"]}, {"session"})

    def test_scorer_metadata_never_enters_requests(self):
        state = {"task": "Inspect the function.", "artifacts": [{"path": "a.py", "content": "x = 1"}]}
        role = {
            "role_id": "p:reviewer", "question": "Does this work need review?",
            "criteria": {"false": "Outside scope.", "true": "Within scope."},
            "adaptation_rationale": "SCORER_ONLY_ADAPTATION",
            "cases": [{"id": "fixture", "expected": True, "state": state,
                       "rationale": "SCORER_ONLY_REASON", "evidence": "SCORER_ONLY_EVIDENCE"}],
        }
        team = {"id": "team", "state": state, "required_roles": ["p:reviewer"],
                "allowed_roles": [], "rationale": "SCORER_ONLY_TEAM"}
        catalog = {"roles": [{"id": "p:reviewer", "trigger_when": "Applicable work.",
                              "do_not_trigger_when": "Unrelated work."}]}
        requests = make_requests([role], [team], catalog)
        rendered = json.dumps(requests)
        self.assertNotIn("SCORER_ONLY", rendered)
        for forbidden in ('"expected"', '"required_roles"', '"allowed_roles"', '"rationale"', '"evidence"'):
            self.assertNotIn(forbidden, rendered)
        self.assertEqual(len(requests), 5)
        self.assertTrue(all(list(q["criteria"]) == ["false", "true"]
                            for r in requests for q in r["questions"].values()))


class FrozenEvidenceTests(unittest.TestCase):
    def test_changing_scorer_only_label_is_detected(self):
        with tempfile.TemporaryDirectory(dir=runner.BASE, prefix=".test-all-reviewers-") as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(runner.BASE.resolve()))
            source, run = root / "source", root / "run"
            source.mkdir()
            run.mkdir()
            for name in runner.FROZEN_INPUTS:
                (run / name).write_text('{"expected": true}', encoding="utf-8")
            (source / "group.json").write_text("{}", encoding="utf-8")
            plan = {
                "frozen_inputs": {name: runner.digest((run / name).read_bytes()) for name in runner.FROZEN_INPUTS},
                "runtime_sources": {name: runner.digest((runner.BASE / name).read_bytes()) for name in runner.RUNTIME_SOURCES},
                "source_hashes": {"group.json": runner.digest((source / "group.json").read_bytes())},
            }
            (run / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            with patch.object(runner, "RUN", run), patch.object(runner, "SOURCE", source):
                verify_frozen_inputs()
                (run / "suite.json").write_text('{"expected": false}', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Frozen input changed"):
                    verify_frozen_inputs()

    def test_source_and_runtime_drift_are_detected(self):
        with tempfile.TemporaryDirectory(dir=runner.BASE, prefix=".test-all-reviewers-") as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(runner.BASE.resolve()))
            source, run = root / "source", root / "run"
            source.mkdir()
            run.mkdir()
            for name in runner.FROZEN_INPUTS:
                (run / name).write_text("{}", encoding="utf-8")
            (source / "group.json").write_text("{}", encoding="utf-8")
            plan = {
                "frozen_inputs": {name: runner.digest((run / name).read_bytes()) for name in runner.FROZEN_INPUTS},
                "runtime_sources": {name: runner.digest((runner.BASE / name).read_bytes()) for name in runner.RUNTIME_SOURCES},
                "source_hashes": {"group.json": runner.digest((source / "group.json").read_bytes())},
            }
            plan_path = run / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            with patch.object(runner, "RUN", run), patch.object(runner, "SOURCE", source):
                (source / "group.json").write_text('{"changed": true}', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Prepared source changed"):
                    verify_frozen_inputs()
                (source / "group.json").write_text("{}", encoding="utf-8")
                plan["runtime_sources"]["all_reviewers_eval.py"] = "different"
                plan_path.write_text(json.dumps(plan), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Execution source changed"):
                    verify_frozen_inputs()

    def test_resume_rejects_mixed_cached_model_files(self):
        session = {
            "session_id": "first", "revision": runner.JULIA_REVISION,
            "weight_sha256": runner.JULIA_WEIGHT_SHA256, "strict_encoding": True,
            "marker_only_head": False, "max_length": 8192,
            "checkpoint_files": {"model.safetensors": runner.JULIA_WEIGHT_SHA256, "julia/typed.py": "code-hash"},
        }
        metadata = {"models": {"julia/all-reviewers": {"load_sessions": [session]}}}
        self.assertEqual(model_sessions(metadata), {"first"})
        second = copy.deepcopy(session)
        second["session_id"] = "second"
        metadata["models"]["julia/all-reviewers"]["load_sessions"].append(second)
        self.assertEqual(model_sessions(metadata), {"first", "second"})
        second["checkpoint_files"]["julia/typed.py"] = "modified-code"
        with self.assertRaisesRegex(ValueError, "checkpoint files changed"):
            model_sessions(metadata)


if __name__ == "__main__":
    unittest.main()
