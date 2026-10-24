"""Tests for the offline mock Gutsy nomination asset. Stdlib only.

The work-graph bridge tests import the prototype controller by file path.
They prove only that nominated reviewers can materialize as REVIEW_LENS
nodes driven through init/reserve/start/complete/finish with fixture gates
in a temporary directory. They do NOT prove real reviewer dispatch.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gold  # noqa: E402
from mock_gutsy import MockGutsy, MockGutsyFailure  # noqa: E402
from nomination_policy import (  # noqa: E402
    FrozenProfile, decode_answers, nominate, score_team_probs,
)

FAKE_NOW = [1000.0]


def fake_clock():
    return FAKE_NOW[0]


def _questions(*qids):
    return {
        q: {"type": "noul", "instructions": f"Require {q}?",
            "criteria": {"false": "no", "true": "yes"}}
        for q in qids
    }


def _load_controller():
    # HERE.parents: 0 choicer-eval, 1 senior-review, 2 evals
    path = HERE.parents[2] / "project-lifecycle" / "work-graph" / "controller.py"
    spec = importlib.util.spec_from_file_location("work_graph_controller", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContractTests(unittest.TestCase):
    def test_mock_output_passes_decode_answers_and_gold_counts_stable(self):
        counts = gold.guard_counts()
        self.assertEqual(counts, {"gold_c_cases": 11, "gold_c_labeled": 10,
                                  "gold_c_activations": 23, "teams": 12,
                                  "team_required": 39, "team_roles": 22})
        case = gold.load_dataset()["cases"][0]
        roles = gold.reviewer_ids_c()
        state = gold.public_state_c(case)
        self.assertNotIn("expected_roles", json.dumps(state))
        questions = gold.build_questions(roles)
        mock = MockGutsy("oracle", expected_by_case={case["id"]: case["expected_roles"]},
                         clock=fake_clock)
        raw = mock.decide(state, questions)
        probabilities, selected = decode_answers({"questions": questions}, raw)
        self.assertEqual(set(probabilities), set(roles))
        self.assertEqual(sorted(selected), sorted(case["expected_roles"]))
        self.assertEqual(len(raw["decisions"]), len(roles))
        for rec in raw["decisions"]:
            self.assertEqual(rec["runtime_identity"], "mock-gutsy/v1")
            self.assertTrue(rec["decision_id"])
            self.assertEqual(len(rec["state_digest"]), 64)
            self.assertIn(rec["qid"], roles)


class ThresholdTests(unittest.TestCase):
    def test_threshold_inclusive_at_frozen_0_5(self):
        roles = ["r:a", "r:b", "r:c"]
        questions = _questions(*roles)
        # threshold-edge assigns 0.499, 0.5, 0.501 in sorted qid order.
        raw = MockGutsy("threshold-edge", clock=fake_clock).decide({"case_id": "X"}, questions)
        probs, selected = decode_answers({"questions": questions}, raw)
        self.assertEqual(probs, {"r:a": 0.499, "r:b": 0.5, "r:c": 0.501})
        self.assertEqual(selected, ["r:b", "r:c"])
        profile = FrozenProfile(mandatory_lenses=frozenset(),
                                require_evidence_binding=False)
        result = nominate("X", questions, raw, profile)
        self.assertEqual(result["nominated"], ["r:b", "r:c"])
        discarded = {d["qid"]: d for d in result["audit"]["discarded"]}
        self.assertEqual(discarded["r:a"]["reason"], "below_threshold")


class MandatoryLensTests(unittest.TestCase):
    def test_mandatory_lens_not_removable_by_low_probability(self):
        questions = _questions("senior-review:code-auditor",
                               "senior-review:security-auditor", "r:other")
        state = {"case_id": "M1"}
        mock = MockGutsy("oracle", expected_by_case={"M1": []}, clock=fake_clock)
        raw = mock.decide(state, questions)  # all probabilities 0.0
        result = nominate("M1", questions, raw, FrozenProfile())
        self.assertEqual(result["nominated"],
                         ["senior-review:code-auditor", "senior-review:security-auditor"])
        reasons = {a["qid"]: a["reason"] for a in result["audit"]["applied"]}
        self.assertEqual(reasons["senior-review:code-auditor"], "mandatory_lens")


class AbstainTests(unittest.TestCase):
    def test_z_malformed_missing_abstain_never_negative_no_hunk_fallback(self):
        roles = ["r:a", "r:b", "r:c", "r:d"]
        questions = _questions(*roles)
        raw = MockGutsy("abstain", clock=fake_clock).decide({"case_id": "A1"}, questions)
        with self.assertRaises(ValueError):
            decode_answers({"questions": questions}, raw)  # strict gate rejects
        profile = FrozenProfile(mandatory_lenses=frozenset())
        result = nominate("A1", questions, raw, profile)
        self.assertEqual(result["nominated"], [])
        self.assertEqual(len(result["audit"]["abstained"]), 4)
        self.assertEqual(result["audit"]["discarded"], [])
        blob = json.dumps(result)
        self.assertNotIn("negative", blob)
        self.assertNotIn("below_threshold", blob)

    def test_missing_evidence_binding_abstains_without_first_hunk_fallback(self):
        questions = _questions("r:a")
        raw = MockGutsy("oracle", expected_by_case={"E1": ["r:a"]},
                        clock=fake_clock).decide({"case_id": "E1"}, questions)
        hunks = ["hunk-1", "hunk-2"]
        profile = FrozenProfile(mandatory_lenses=frozenset(),
                                require_evidence_binding=True)
        result = nominate("E1", questions, raw, profile,
                          evidence_bindings={})  # nothing explicitly bound
        self.assertEqual(result["nominated"], [])
        self.assertEqual(result["audit"]["abstained"][0]["reason"],
                         "evidence_binding_missing")
        self.assertNotIn(hunks[0], json.dumps(result["audit"]))
        bound = nominate("E1", questions, raw, profile,
                         evidence_bindings={"r:a": ["hunk-2"]})
        self.assertEqual(bound["nominated"], ["r:a"])

    def test_tool_failure_is_abstain_not_negative(self):
        questions = _questions("r:a", "senior-review:code-auditor")
        with self.assertRaises(MockGutsyFailure):
            MockGutsy("failure", clock=fake_clock).decide({"case_id": "F1"}, questions)
        result = nominate("F1", questions, None, FrozenProfile(),
                          failure="tool_failure")
        self.assertTrue(all(a["status"] == "ABSTAIN" for a in result["audit"]["abstained"]))
        self.assertEqual(result["audit"]["discarded"], [])
        # Mandatory lens retained by mandate, explicitly not by a model vote.
        self.assertIn("senior-review:code-auditor", result["nominated"])
        self.assertNotIn("r:a", result["nominated"])


class GoldReplayTests(unittest.TestCase):
    def test_gold_replay_reproduces_recorded_suite2_threshold_numbers(self):
        saved = gold.saved_probs()
        teams = gold.load_teams()
        roles = gold.team_role_ids()
        profile = FrozenProfile.threshold_only_replay()
        raw_probs = {}
        for team in teams:
            state = gold.public_state_team(team)
            self.assertNotIn("required_roles", json.dumps(state))
            questions = gold.build_questions(roles)
            raw = MockGutsy("gold-replay", saved_probs=saved["suite2_raw_probs"],
                            clock=fake_clock).decide(state, questions)
            decode_answers({"questions": questions}, raw)
            result = nominate(team["id"], questions, raw, profile)
            self.assertTrue(result["nominated"] or True)
            raw_probs[team["id"]] = {
                q: raw["answers"][q]["probabilities"]["true"] for q in roles}
        scored = score_team_probs(teams, raw_probs)
        recorded = saved["suite2_grounded_noul"]
        self.assertEqual(scored["0.50"], recorded["0.50"])
        self.assertEqual(scored, recorded)

    def test_gold_replay_missing_saved_probability_abstains_not_negative(self):
        questions = _questions("r:a", "r:b")
        raw = MockGutsy(
            "gold-replay", saved_probs={"X": {"r:a": 0.9}}, clock=fake_clock,
        ).decide({"case_id": "X"}, questions)
        # No invented 0.0 for r:b: the answer is omitted entirely.
        self.assertNotIn("r:b", raw["answers"])
        self.assertEqual(raw["answers"]["r:a"]["probabilities"]["true"], 0.9)
        profile = FrozenProfile(mandatory_lenses=frozenset(),
                                require_evidence_binding=False)
        result = nominate("X", questions, raw, profile)
        self.assertEqual(result["nominated"], ["r:a"])
        abstained = {a["qid"]: a for a in result["audit"]["abstained"]}
        self.assertEqual(abstained["r:b"]["status"], "ABSTAIN")
        self.assertEqual(abstained["r:b"]["reason"], "missing_answer")
        self.assertEqual(result["audit"]["discarded"], [])

    def test_gold_replay_reproduces_recorded_suite3_selection_at_0_5(self):
        saved = gold.saved_probs()
        roles = gold.reviewer_ids_c()
        profile = FrozenProfile.threshold_only_replay()
        recorded = saved["suite3_c01_c11"]["gutsy_exact_catalog_th_0.50"]
        self.assertEqual(recorded["expected_role_recall"], "9/23 (39.1%)")
        for case in gold.load_dataset()["cases"]:
            state = gold.public_state_c(case)
            questions = gold.build_questions(roles)
            raw = MockGutsy("gold-replay", saved_probs=saved["suite3_raw_probs"],
                            clock=fake_clock).decide(state, questions)
            result = nominate(case["id"], questions, raw, profile)
            self.assertEqual(result["nominated"],
                             recorded["per_case_selected"][case["id"]], case["id"])


class ScoreMockCliTests(unittest.TestCase):
    """Full CLI path through score_mock.py in a throwaway runs/ directory."""

    def _run_cli(self, mode):
        run_name = f"test-cli-{mode}-{uuid.uuid4().hex[:12]}"
        target = HERE / "runs" / run_name
        self.addCleanup(shutil.rmtree, target, True)
        proc = subprocess.run(
            [sys.executable, "-B", str(HERE / "score_mock.py"),
             "--mode", mode, "--run-dir", f"runs/{run_name}"],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        decisions = json.loads((target / "decisions.json").read_text(encoding="utf-8"))
        scores = json.loads((target / "scores.json").read_text(encoding="utf-8"))
        return decisions, scores

    def test_cli_abstain_completes_and_records_abstain(self):
        decisions, scores = self._run_cli("abstain")
        self.assertTrue(decisions["decisions"])
        for group in ("team_policy_results", "suite3_policy_results"):
            abstained = [a for r in scores[group] for a in r["audit"]["abstained"]]
            self.assertTrue(abstained, group)
            self.assertTrue(all(a["status"] == "ABSTAIN" for a in abstained), group)
            # Abstentions are never rewritten as below-threshold negatives.
            abstained_qids = {(r["case_id"], a["qid"]) for r in scores[group]
                              for a in r["audit"]["abstained"]}
            discarded = {(r["case_id"], d["qid"]) for r in scores[group]
                         for d in r["audit"]["discarded"]}
            self.assertFalse(abstained_qids & discarded, group)

    def test_cli_aggregated_decision_ids_unique_and_team_source_recorded(self):
        decisions, scores = self._run_cli("gold-replay")
        ids = [d["decision_id"] for d in decisions["decisions"]]
        self.assertTrue(ids)
        # Both fused groups (teams and Gold C) share one artifact.
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("team_source", scores)
        self.assertIn(scores["team_source"]["source"], ("teams.json", "suite.json"))
        self.assertEqual(scores["team_source"]["fallback_used"],
                         scores["team_source"]["source"] == "suite.json")


class WorkGraphBridgeTests(unittest.TestCase):
    """Bridge proof only: nominated reviewers materialize as work-graph nodes.

    This does not prove real reviewer dispatch, real gate verification, or
    any host execution; gates are fixture strings in a temporary directory.
    """

    def _nominated_roles(self):
        questions = _questions("senior-review:code-auditor",
                               "senior-review:security-auditor", "r:other")
        raw = MockGutsy("oracle", expected_by_case={"B1": ["r:other"]},
                        clock=fake_clock).decide({"case_id": "B1"}, questions)
        result = nominate("B1", questions, raw,
                          FrozenProfile(require_evidence_binding=False))
        return result["nominated"]

    @staticmethod
    def _node_id(role: str) -> str:
        return "lens-" + role.replace(":", "-").replace("/", "-")

    def _plan(self, ctrl, nominated, finding_verdict="CONFIRMED"):
        nodes = []
        for role in nominated:
            nid = self._node_id(role)
            nodes.append({
                "id": nid, "op": "REVIEW_LENS",
                "gate": f"finding-verdict:{finding_verdict}",
                "needs": [], "consumes": [], "produces": [f"review:{role}"],
                "writes": [], "reads": [], "locks": [],
            })
        barrier_consumes = [f"review:{r}" for r in nominated]
        nodes.append({
            "id": "wave-barrier", "op": "WAVE_BARRIER", "gate": "finding-verdict:CONFIRMED",
            "needs": [], "consumes": barrier_consumes, "produces": ["wave:promoted"],
            "writes": [], "reads": [], "locks": [],
        })
        return ctrl.compile_plan(nodes, "review_only")

    def _drive_one(self, ctrl, holder="fixture"):
        aid = ctrl.reserve(holder, ctrl.show()["revision"])
        self.assertIsNotNone(aid)
        attempt = ctrl.show()["attempts"][aid]
        self.assertTrue(ctrl.start(aid, holder, attempt["inputs"]))
        node = ctrl.show()["plan"]["nodes"][attempt["node"]]
        outputs = {name: f"fixture-output:{name}" for name in node["produces"]}
        ctrl.complete(f"event-{aid}", aid, f"candidate-{attempt['node']}",
                      "pass", outputs)
        return aid

    def test_nominated_reviewers_materialize_as_review_lens_nodes(self):
        ctrl_mod = _load_controller()
        nominated = self._nominated_roles()
        self.assertGreaterEqual(len(nominated), 2)
        with tempfile.TemporaryDirectory() as tmp:
            now = [1000.0]
            ctrl = ctrl_mod.Controller(tmp, clock=lambda: now[0])
            plan = self._plan(ctrl_mod, nominated)
            lens_nodes = [n for n in plan["nodes"].values() if n["op"] == "REVIEW_LENS"]
            self.assertEqual(len(lens_nodes), len(nominated))
            ctrl.init(plan)
            with self.assertRaises(ctrl_mod.Rejected):
                ctrl.finish()
            for _ in nominated:
                self._drive_one(ctrl)
            self._drive_one(ctrl)  # WAVE_BARRIER
            self.assertTrue(ctrl.finish())
            self.assertEqual(ctrl.show()["outcome"], "VERIFIED_SUCCESS")

    def test_finding_verdict_gate_and_barrier_rejects_stale_delivery(self):
        ctrl_mod = _load_controller()
        nominated = self._nominated_roles()
        with tempfile.TemporaryDirectory() as tmp:
            now = [1000.0]
            ctrl = ctrl_mod.Controller(tmp, clock=lambda: now[0])
            plan = self._plan(ctrl_mod, nominated, finding_verdict="CONFIRMED")
            for node in plan["nodes"].values():
                if node["op"] == "REVIEW_LENS":
                    self.assertEqual(node["gate"], "finding-verdict:CONFIRMED")
            ctrl.init(plan)
            # Drive the first lens, then try to re-deliver it with a changed
            # payload under the same event id: the barrier authority rejects
            # it instead of promoting a stale/changed artifact.
            aid = ctrl.reserve("fixture", ctrl.show()["revision"])
            attempt = ctrl.show()["attempts"][aid]
            self.assertTrue(ctrl.start(aid, "fixture", attempt["inputs"]))
            node = ctrl.show()["plan"]["nodes"][attempt["node"]]
            outputs = {name: f"fixture-output:{name}" for name in node["produces"]}
            ctrl.complete("event-lens-1", aid, "candidate-A", "pass", outputs)
            state = ctrl.show()
            self.assertTrue(any(v == "pass" for v in state["verifications"].values()))
            with self.assertRaisesRegex(ctrl_mod.Rejected, "payload changed"):
                ctrl.complete("event-lens-1", aid, "candidate-CHANGED", "pass", outputs)
            # Barrier (and every later node) cannot start from invented
            # artifact digests: the packet is bound to recorded digests.
            for _ in nominated[1:]:
                self._drive_one(ctrl)
            barrier_aid = ctrl.reserve("fixture", ctrl.show()["revision"])
            self.assertIsNotNone(barrier_aid)
            barrier = ctrl.show()["attempts"][barrier_aid]
            self.assertEqual(ctrl.show()["plan"]["nodes"][barrier["node"]]["op"],
                             "WAVE_BARRIER")
            stale = {k: "invented-digest" for k in barrier["inputs"]}
            with self.assertRaisesRegex(ctrl_mod.Rejected, "stale packet"):
                ctrl.start(barrier_aid, "fixture", stale)
            self.assertFalse(ctrl.show()["artifacts"].get("wave:promoted"))
            self.assertTrue(ctrl.start(barrier_aid, "fixture", barrier["inputs"]))
            ctrl.complete("event-barrier", barrier_aid, "candidate-barrier", "pass",
                          {"wave:promoted": "promoted"})
            self.assertTrue(ctrl.finish())


if __name__ == "__main__":
    unittest.main()
