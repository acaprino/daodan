"""Regressions for evidence coverage, probability identity and slot restore, without inference."""
import json
import math
from pathlib import Path
import tempfile
import unittest

import gutsy_followup as followup

REFERENCE = followup.HERE / "runs/20261020-gutsy-followup-ctx1536"


class SlotRestoreTests(unittest.TestCase):
    JOB = {"state": "  Case E01\n[Code Under Review]\nx = 1\n", "question": " Does it? ", "options": ["Yes", "No"]}

    def test_prompt_splits_immediately_before_the_question(self):
        prefix, suffix = followup.state_prefix(self.JOB), followup.question_suffix(self.JOB)
        self.assertEqual(prefix + suffix, followup.build_prompt(self.JOB))
        self.assertTrue(prefix.endswith("\n\n"))
        self.assertTrue(suffix.startswith("Question: Does it?"))

    @unittest.skipUnless((REFERENCE / "execution.json").exists(), "reference run not present")
    def test_split_prompt_reproduces_every_frozen_reference_prompt(self):
        jobs = followup.load(REFERENCE / "jobs.json")
        for job in jobs:
            record = followup.load(REFERENCE / "wire" / f"{job['id']}.json")
            self.assertEqual(followup.build_prompt(job), record["request"]["prompt"], job["id"])

    def test_slot_profile_differs_from_full_only_by_its_directory(self):
        plan = {"server_context_tokens": 1536}
        full = followup.server_args(plan, 1111)
        slot = followup.server_args(plan, 2222, Path("slots"))
        self.assertIn("--slot-save-path", slot)
        self.assertNotIn("--slot-save-path", full)
        self.assertEqual(followup.runtime_signature(full), followup.runtime_signature(slot))

    @unittest.skipUnless((REFERENCE / "execution.json").exists(), "reference run not present")
    def test_full_profile_matches_the_recorded_reference_arguments(self):
        recorded = followup.load(REFERENCE / "execution.json")["args"]
        rebuilt = followup.server_args({"server_context_tokens": 1536}, 1)
        self.assertEqual(followup.runtime_signature(rebuilt), followup.runtime_signature(recorded))

    def test_compare_job_reports_flip_margin_and_unknown_probability(self):
        full = {"id": "Q1", "case_id": "E01", "mode": "windowed", "variant": "v2", "role": "r", "window_id": "W001",
                "prompt_sha256": "x", "letter": "B", "probabilities": {"A": 0.21, "B": 0.23, "Z": None}}
        slot = dict(full, letter="A", probabilities={"A": 0.22, "B": 0.21, "Z": 0.001}, prefix_reuse_verified=True)
        row = followup.compare_job(full, slot, 0.05)
        self.assertTrue(row["flip"])
        self.assertTrue(row["near_tie"])
        self.assertTrue(row["same_prompt"])
        self.assertAlmostEqual(row["reference_margin"], 0.02)
        self.assertAlmostEqual(row["max_abs_delta"], 0.02)
        self.assertIsNone(row["deltas"]["Z"])
        self.assertTrue(row["unknown_probability"])
        wide = followup.compare_job(dict(full, probabilities={"A": 0.1, "B": 0.6, "Z": 0.0}), slot, 0.05)
        self.assertFalse(wide["near_tie"])

    def test_new_runs_default_to_the_adopted_slot_restore_mode(self):
        import inspect
        self.assertEqual(inspect.signature(followup.prepare).parameters["prefix_mode"].default, "slot-restore")
        with self.assertRaises(ValueError):
            followup.prepare(followup.HERE / "runs" / "never-created", "unknown")
        self.assertFalse((followup.HERE / "runs" / "never-created").exists())

    def test_compact_memory_samples_export_in_report_format(self):
        monitor = followup.MemoryMonitor(proc=None, limit=1)
        monitor.samples.append((1.0, 10, 11, 12, 20, 21, 22))
        self.assertEqual(monitor.export(), [{"time": 1.0, "server": {"rss": 10, "peak_rss": 11, "private": 12},
                                             "runner": {"rss": 20, "peak_rss": 21, "private": 22}}])

    def test_prepare_slot_copies_reference_inputs_byte_for_byte(self):
        with tempfile.TemporaryDirectory(dir=followup.HERE / "runs") as tmp:
            reference = Path(tmp) / "reference"
            reference.mkdir()
            files = {"cases.json": b"[]\r\n", "jobs.json": b"[1]\r\n", "prompts.json": b"{}\r\n"}
            for name, data in files.items():
                (reference / name).write_bytes(data)
            plan = {"status": "frozen", "jobs": 1, "hashes": {n: followup.digest(d) for n, d in files.items()},
                    "runner_sha256": "old", "server_context_tokens": 1536, "memory_limit_bytes": 1,
                    "legacy_sha256": followup.digest((followup.HERE / "run_gutsy_v2_eval.py").read_bytes())}
            followup.save(reference / "plan.json", plan)
            followup.save(reference / "execution.json", {"status": "complete"})
            followup.prepare_slot(Path(tmp) / "slot", reference)
            for name, data in files.items():
                self.assertEqual((Path(tmp) / "slot" / name).read_bytes(), data)
            frozen = followup.load(Path(tmp) / "slot" / "plan.json")
            self.assertEqual(frozen["prefix_mode"], "slot-restore")
            self.assertEqual(frozen["hashes"], plan["hashes"])
            self.assertEqual(frozen["reference_runner_sha256"], "old")
            self.assertEqual(frozen["comparison_rule"]["near_tie_margin"], 0.05)
            followup.save(reference / "execution.json", {"status": "failed"})
            with self.assertRaises(ValueError):
                followup.prepare_slot(Path(tmp) / "again", reference)


class InputContractTests(unittest.TestCase):
    def test_all_real_hunk_characters_survive_including_late_files(self):
        cases = json.loads(followup.ORIGINAL.read_text(encoding="utf-8"))["cases"]
        for case in cases:
            windows = followup.window_hunks(case["hunks"])
            recovered = {}
            for window in windows:
                self.assertLessEqual(sum(len(p["text"]) for p in window["pieces"]), 2800)
                self.assertEqual({p["path"] for p in window["pieces"]}, {window["path"]})
                for piece in window["pieces"]:
                    key = piece["hunk_id"]
                    self.assertEqual(piece["offset"], len(recovered.get(key, "")))
                    recovered[key] = recovered.get(key, "") + piece["text"]
            self.assertEqual(recovered, {h["id"]: h["text"] for h in case["hunks"]})

    def test_large_line_is_not_dropped_or_looped(self):
        text = "x" * 7000 + "\nnext\n"
        hunk = {"id": "H1", "path": "f.py", "text": text, "start_line": 50}
        windows = followup.window_hunks([hunk])
        self.assertEqual("".join(p["text"] for w in windows for p in w["pieces"]), text)
        self.assertEqual([w["pieces"][0]["line"] for w in windows], [50, 50, 50])

    def test_inference_state_has_no_label_fields(self):
        hunk = {"id": "H1", "path": "f.py", "text": "return 1\n", "start_line": 2,
                "expected_roles": ["secret-label"], "source_case": "answer-title"}
        state = followup.window_state("E01", followup.window_hunks([hunk])[0])
        self.assertNotIn("secret-label", state)
        self.assertNotIn("answer-title", state)
        self.assertNotIn("expected_roles", state)


class ProbabilityTests(unittest.TestCase):
    def test_space_and_lowercase_tokens_cannot_overwrite_bare_letter(self):
        result = {"completion_probabilities": [{"id": 32, "token": "A", "logprob": -0.1,
                    "top_logprobs": [{"id": 32, "token": "A", "logprob": -0.1},
                                     {"id": 800, "token": " A", "logprob": -5},
                                     {"id": 64, "token": "a", "logprob": -6}]}]}
        probabilities = followup.exact_probabilities(result, {"A": 32, "B": 33, "Z": 57})
        self.assertAlmostEqual(probabilities["A"], math.exp(-0.1))
        self.assertIsNone(probabilities["B"])
        self.assertIsNone(probabilities["Z"])

    def test_absent_probabilities_are_unknown(self):
        self.assertEqual(followup.exact_probabilities({}, {"A": 32}), {"A": None})


if __name__ == "__main__":
    unittest.main()
