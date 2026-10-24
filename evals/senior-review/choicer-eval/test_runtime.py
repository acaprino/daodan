"""Offline adapter tests with deterministic fake inference and saved captures."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import metrics
import run_eval


BASE = Path(__file__).resolve().parent
ROLES = ["example:first", "example:second", "example:third"]
CATALOG = {
    "roles": [
        {"id": role, "is_reviewer": True, "trigger_when": "trigger", "do_not_trigger_when": "negative"}
        for role in ROLES
    ],
}


def request(hunk: str = "H1", variant: str = "noul") -> dict:
    if variant == "noul":
        questions = {
            role: {
                "type": "noul", "instructions": "Apply the exact trigger.",
                "criteria": {"false": "negative", "true": "trigger"},
            }
            for role in ROLES
        }
    else:
        questions = {
            "reviewer": {
                "type": "choice", "instructions": "Select the closest reviewer.",
                "criteria": dict.fromkeys(ROLES, "trigger"),
            },
        }
    return {
        "impl": "julia", "variant": variant, "case_id": "C01",
        "hunk_id": hunk, "request_sha256": "offline-fixture",
        "state": "[H1]\nsource.py:7 return value", "questions": questions,
    }


def case_data(hunks: list[str]) -> dict:
    return {
        "cases": [{
            "id": "C01", "source_case": "private-source-name",
            "label_status": "labeled", "expected_roles": [ROLES[0], ROLES[2]],
            "hunks": [
                {"id": hunk, "path": "source.py", "start_line": 7, "text": "return value\n"}
                for hunk in hunks
            ],
        }],
    }


class FakeEngine:
    """Named responses exercise the adapter without importing a model package."""

    def __init__(self, probabilities: tuple[float, ...] = (0.5, 0.499, 0.8)):
        self.probabilities = dict(zip(ROLES, probabilities))
        self.calls = []
        self.batch_size = 1
        self.benchmark_session_id = "fake-session"

    def encoding_info(self, rows):
        row = rows[0]
        if any(not option for option in row["options"]):
            raise ValueError("Option descriptions must be nonempty")
        return [{
            "stateTruncated": row["state"] == "state-overflow",
            "optionsTruncated": "option-overflow" in row["options"],
        }]

    def predict(self, *, state, questions):
        self.calls.append({"state": state, "questions": copy.deepcopy(questions)})
        if "reviewer" in questions:
            return {"answers": {"reviewer": {"probabilities": self.probabilities}}}
        return {
            "answers": {
                role: {"probabilities": {"true": self.probabilities[role], "false": 1 - self.probabilities[role]}}
                for role in questions
            },
        }


class LocalAdapterTests(unittest.TestCase):
    def run_fake(self, requests, engine):
        for entry in requests:
            entry["request_sha256"] = run_eval.digest(run_eval.encoded({
                key: value for key, value in entry.items() if key != "request_sha256"
            }))
        with tempfile.TemporaryDirectory(prefix="test-runtime-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            args = argparse.Namespace(
                impl="julia", variant=requests[0]["variant"], resume=False,
                threads=4, require_complete_catalog=False,
            )
            with patch.object(run_eval, "load_julia", return_value=engine) as loader:
                run_eval.run_local(root, args, requests, CATALOG)
            loader.assert_called_once_with(root, args)
            return [
                run_eval.read_json(root / "results/julia" / args.variant / f"C01-{entry['hunk_id']}.json")
                for entry in requests
            ]

    def test_unsupported_questions_are_preserved_and_never_scored_as_missing_negatives(self):
        entry = request()
        entry["questions"][ROLES[0]]["criteria"]["false"] = ""
        entry["questions"][ROLES[1]]["criteria"]["true"] = "option-overflow"
        engine = FakeEngine()
        records = self.run_fake([entry], engine)
        record = records[0]
        self.assertEqual(record["status"], "error")
        self.assertEqual(set(record["question_errors"]), set(ROLES[:2]))
        self.assertIn("nonempty", record["question_errors"][ROLES[0]])
        self.assertIn("truncate", record["question_errors"][ROLES[1]])
        self.assertEqual(set(record["raw_output"]["answers"]), {ROLES[2]})
        self.assertEqual(set(engine.calls[0]["questions"]), {ROLES[2]})
        self.assertIsNone(record["probabilities"])
        scored = metrics.score(case_data(["H1"]), CATALOG, records)["models"]["julia/noul"]
        self.assertEqual(scored["complete_cases"], 0)
        self.assertIsNone(scored["metrics"]["expected_role_recall"])
        self.assertIsNone(scored["case_results"][0]["selected"])

    def test_first_actual_inference_is_cold_after_rejected_preflight(self):
        entries = [request("H1"), request("H2"), request("H3")]
        entries[0]["state"] = "state-overflow"
        engine = FakeEngine()
        records = self.run_fake(entries, engine)
        self.assertEqual([entry["phase"] for entry in records], ["preflight", "cold", "warm"])
        self.assertEqual([entry["status"] for entry in records], ["error", "ok", "ok"])
        self.assertEqual(len(engine.calls), 2)
        self.assertEqual(set(records[0]["question_errors"]), set(ROLES))
        self.assertEqual(records[0]["raw_output"], {"answers": {}})

    def test_full_noul_catalog_uses_inclusive_half_probability(self):
        engine = FakeEngine()
        records = self.run_fake([request()], engine)
        record = records[0]
        self.assertEqual(record["status"], "ok")
        self.assertEqual(record["selected"], [ROLES[0], ROLES[2]])
        self.assertEqual(record["probabilities"], engine.probabilities)
        scored = metrics.score(case_data(["H1"]), CATALOG, records)["models"]["julia/noul"]
        self.assertEqual(scored["complete_cases"], 1)
        self.assertEqual(scored["metrics"]["expected_role_recall"], 1)

    def test_choice_uses_argmax_even_when_all_scores_are_below_half(self):
        engine = FakeEngine((0.35, 0.4, 0.25))
        record = self.run_fake([request(variant="choice")], engine)[0]
        self.assertEqual(record["status"], "ok")
        self.assertEqual(record["selected"], [ROLES[1]])
        self.assertEqual(record["probabilities"], engine.probabilities)

    def test_invalid_model_probability_is_saved_as_error(self):
        for values, variant in (
            ((0.2, 0.3, 0.4), "choice"),
            ((1.01, 0.1, 0.2), "noul"),
        ):
            with self.subTest(variant=variant, values=values):
                record = self.run_fake([request(variant=variant)], FakeEngine(values))[0]
                self.assertEqual(record["status"], "error")
                self.assertIsNotNone(record["raw_output"])
                self.assertIsNone(record["probabilities"])


class ResumeTests(unittest.TestCase):
    def entries(self):
        entries = [request("H1"), request("H2")]
        for entry in entries:
            entry["request_sha256"] = run_eval.digest(run_eval.encoded({
                key: value for key, value in entry.items() if key != "request_sha256"
            }))
        return entries

    def test_identical_evidence_and_derived_reports_are_not_rewritten(self):
        with tempfile.TemporaryDirectory(prefix="test-resume-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            path = root / "frozen.json"
            run_eval.write_json(path, {"evidence": "unchanged"}, freeze=True)
            modified = path.stat().st_mtime_ns
            original_open = Path.open

            def read_only_open(target, mode="r", *args, **kwargs):
                if any(flag in mode for flag in "wa+"):
                    self.fail("Identical content was opened for writing")
                return original_open(target, mode, *args, **kwargs)

            with patch.object(Path, "open", read_only_open):
                run_eval.write_json(path, {"evidence": "unchanged"}, freeze=True)
                run_eval.write_json(path, {"evidence": "unchanged"}, freeze=False)
            self.assertEqual(path.stat().st_mtime_ns, modified)

    def test_resume_preserves_saved_bytes_and_executes_only_missing_requests(self):
        with tempfile.TemporaryDirectory(prefix="test-resume-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            entries = self.entries()
            args = argparse.Namespace(
                impl="julia", variant="noul", resume=False, threads=4,
                require_complete_catalog=False,
            )
            with patch.object(run_eval, "load_julia", return_value=FakeEngine()):
                run_eval.run_local(root, args, entries[:1], CATALOG)
            saved = root / "results/julia/noul/C01-H1.json"
            original = saved.read_bytes()
            args.resume = True
            engine = FakeEngine()
            with patch.object(run_eval, "load_julia", return_value=engine):
                run_eval.run_local(root, args, entries, CATALOG)
            self.assertEqual(saved.read_bytes(), original)
            self.assertEqual(len(engine.calls), 1)
            fresh = run_eval.read_json(root / "results/julia/noul/C01-H2.json")
            self.assertEqual(fresh["runtime_config"], {"batch_size": 1, "threads": 4})
            self.assertEqual(fresh["model_session_id"], "fake-session")
            with patch.object(run_eval, "load_julia") as loader:
                run_eval.run_local(root, args, entries, CATALOG)
            loader.assert_not_called()

    def test_resume_rejects_result_hash_mismatch_before_loading_model(self):
        with tempfile.TemporaryDirectory(prefix="test-resume-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            entries = self.entries()
            saved = run_eval.base_record(entries[0])
            saved.update(status="error", request_sha256="tampered")
            run_eval.write_json(root / "results/julia/noul/C01-H1.json", saved)
            args = argparse.Namespace(
                impl="julia", variant="noul", resume=True, threads=4,
                require_complete_catalog=False,
            )
            with patch.object(run_eval, "load_julia") as loader:
                with self.assertRaisesRegex(ValueError, "output/request mismatch"):
                    run_eval.run_local(root, args, entries, CATALOG)
            loader.assert_not_called()

    def test_resume_rejects_changed_request_and_unmatched_saved_output(self):
        with tempfile.TemporaryDirectory(prefix="test-resume-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            entries = self.entries()
            args = argparse.Namespace(
                impl="julia", variant="noul", resume=True, threads=4,
                require_complete_catalog=False,
            )
            entries[0]["state"] = "modified after freezing"
            with self.assertRaisesRegex(ValueError, "Request hash is invalid"):
                run_eval.pending_local_requests(root, args, entries)
            run_eval.write_json(root / "results/julia/noul/C99-H99.json", {"status": "ok"})
            with self.assertRaisesRegex(ValueError, "no matching request"):
                run_eval.pending_local_requests(root, args, self.entries())


class CompleteCatalogTests(unittest.TestCase):
    def test_atomic_validation_prevents_partial_inference_and_keeps_predictions_unknown(self):
        with tempfile.TemporaryDirectory(prefix="test-catalog-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            entry = request()
            entry["questions"][ROLES[0]]["criteria"]["false"] = ""
            entry["request_sha256"] = run_eval.digest(run_eval.encoded({
                key: value for key, value in entry.items() if key != "request_sha256"
            }))
            args = argparse.Namespace(
                impl="julia", variant="noul", resume=False, threads=4,
                require_complete_catalog=True,
            )
            engine = FakeEngine()
            with patch.object(run_eval, "load_julia", return_value=engine):
                run_eval.run_local(root, args, [entry], CATALOG)
            record = run_eval.read_json(root / "results/julia/noul/C01-H1.json")
            self.assertEqual(engine.calls, [])
            self.assertFalse(record["inference_attempted"])
            self.assertFalse(record["inference_performed"])
            self.assertEqual(record["submitted_question_ids"], [])
            self.assertEqual(record["phase"], "preflight")
            self.assertEqual(record["status"], "error")
            self.assertEqual(set(record["question_errors"]), {ROLES[0]})
            self.assertEqual(set(record["encoding"]), set(ROLES[1:]))
            self.assertIsNone(record["probabilities"])
            self.assertEqual(record["raw_output"], {"answers": {}})
            self.assertIn("Complete catalog", record["rejection_reason"])
            self.assertFalse((root / "wire/julia/noul/C01-H1.json").exists())

    def test_complete_catalog_runs_all_questions_and_saves_exact_effective_input(self):
        with tempfile.TemporaryDirectory(prefix="test-catalog-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            entry = request()
            entry["request_sha256"] = run_eval.digest(run_eval.encoded({
                key: value for key, value in entry.items() if key != "request_sha256"
            }))
            args = argparse.Namespace(
                impl="julia", variant="noul", resume=False, threads=4,
                require_complete_catalog=True,
            )
            engine = FakeEngine()
            with patch.object(run_eval, "load_julia", return_value=engine):
                run_eval.run_local(root, args, [entry], CATALOG)
            record = run_eval.read_json(root / "results/julia/noul/C01-H1.json")
            wire = run_eval.read_json(root / "wire/julia/noul/C01-H1.json")
            self.assertTrue(record["inference_performed"])
            self.assertEqual(record["submitted_question_ids"], ROLES)
            self.assertEqual(wire["source_request_sha256"], entry["request_sha256"])
            self.assertEqual(wire["state"], entry["state"])
            self.assertEqual(wire["questions"], entry["questions"])
            self.assertEqual(engine.calls, [{"state": wire["state"], "questions": wire["questions"]}])


class LlmCaptureTests(unittest.TestCase):
    def response(self):
        return {
            "mode": "full",
            "selected": [{
                "trigger_line": "[H1] source.py:7 return value",
                "reason": "Verify the boundary.",
                "role": ROLES[0], "tier": "tier2", "effort": "high",
            }],
            "recommend_full_review": False,
            "recommend_full_reason": None,
        }

    def test_fabricated_citations_and_unknown_roles_are_rejected(self):
        case = case_data(["H1"])["cases"][0]
        self.assertEqual(run_eval.validate_llm(self.response(), case, CATALOG), [ROLES[0]])
        mutations = [
            {"trigger_line": "[H99] source.py:7 return value"},
            {"trigger_line": "[H1] other.py:7 return value"},
            {"trigger_line": "[H1] source.py:8 return value"},
            {"trigger_line": "[H1] source.py:7 invented()"},
            {"role": "foreign:unknown"},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                response = self.response()
                response["selected"][0].update(mutation)
                with self.assertRaises(ValueError):
                    run_eval.validate_llm(response, case, CATALOG)

    def import_capture(self, root, capture):
        requests = [{
            "impl": "llm", "variant": "noul", "case_id": "C01",
            "hunk_id": None, "request_sha256": "correct-request-digest",
        }]
        source = root / "captures"
        run_eval.write_json(source / "C01-batch.json", capture)
        args = argparse.Namespace(responses=str(source), variant="noul")
        run_eval.imported_llm(root, args, requests, case_data(["H1"]), CATALOG)
        return root / "results/llm/noul/C01-batch.json"

    def test_import_rejects_a_capture_bound_to_another_request(self):
        with tempfile.TemporaryDirectory(prefix="test-runtime-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            capture = {"request_sha256": "another-request-digest", "response": self.response()}
            with self.assertRaisesRegex(ValueError, "another input"):
                self.import_capture(root, capture)
            self.assertFalse((root / "results").exists())

    def test_valid_capture_keeps_unreported_telemetry_unknown(self):
        with tempfile.TemporaryDirectory(prefix="test-runtime-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            capture = {"request_sha256": "correct-request-digest", "response": self.response()}
            record = run_eval.read_json(self.import_capture(root, capture))
            self.assertEqual(record["status"], "ok")
            self.assertEqual(record["selected"], [ROLES[0]])
            self.assertEqual(record["raw_output"], capture)
            self.assertIsNone(record["usage"])
            self.assertIsNone(record["wall_seconds"])
            self.assertIsNone(record["cpu_seconds"])
            self.assertIsNone(record["probabilities"])
            self.assertEqual(record["phase"], "unknown")

    def test_invalid_citation_capture_is_preserved_as_an_error(self):
        with tempfile.TemporaryDirectory(prefix="test-runtime-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            response = self.response()
            response["selected"][0]["trigger_line"] = "[H1] source.py:7 invented()"
            capture = {"request_sha256": "correct-request-digest", "response": response}
            record = run_eval.read_json(self.import_capture(root, capture))
            self.assertEqual(record["status"], "error")
            self.assertEqual(record["raw_output"], capture)
            self.assertIn("absent", record["error"])


if __name__ == "__main__":
    unittest.main()
