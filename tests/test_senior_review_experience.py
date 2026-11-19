"""Experience consumes composition's actual jobs for both recording and briefing."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "daodan/review"  # the catalog, its roles and contracts
if str(REPO / "daodan/core") not in sys.path:
    sys.path.insert(0, str(REPO / "daodan/core"))

import composition  # noqa: E402
import review_experience as experience  # noqa: E402

MEMBER = "senior-review:accessible-navigation-auditor"
TARGET = {"symbol_id": "navigation.py::navigate", "file": "navigation.py", "start": 1, "end": 10,
          "body_hash": "body-1", "interface_hash": "interface-1", "effects_hash": "effects-1",
          "parser_fingerprint": "parser-1"}
PREMISE = "Keyboard focus remains on the removed item"
RECORDED = "2026-11-16T12:00:00+00:00"
MISSING = object()  # a finding without the confidence key; None is an explicit JSON null


def prepared(shape="light", verification="critical-high", **bindings):
    candidate = {"ref": "candidate-1"}
    roster = {"schema": composition.ROSTER_SCHEMA, "id": "review-1", "shape": shape,
              "review_basis": "changeset", "verification": verification,
              "roster": ["senior-review:accessibility-auditor"],
              "support": ["senior-review:isolated-worker"],
              "grounding": {"candidate": candidate, "graph": {"bound_targets": [TARGET]}}}
    return composition.bind(roster, {"candidate": candidate, "knowledge_selection": "",
                                    "selection": "automatic", **bindings}, PLUGIN)


def finding_of(severity="High", confidence=80):
    finding = {"id": "F1", "file": "navigation.py", "line": 3, "severity": severity,
               "premise": PREMISE, "premise_provenance": "independent"}
    if confidence is not MISSING:
        finding["confidence"] = confidence
    return finding


def deliveries_for(review, finding, verdicts):
    job = review["jobs"][0]
    deliveries = {"discovery": {"review": review["id"], "job_id": job["job_id"], "status": "delivered",
                               "specialist_ids": job["specialist_ids"], "findings": [finding],
                               "member_results": [{"specialist_id": member, "status": "delivered", "coverage": "complete",
                                                   "findings": [finding["id"]] if member == MEMBER else [], "gaps": []}
                                                  for member in job["specialist_ids"]]}}
    for lens, verdict in verdicts.items():
        deliveries[f"lens-{lens}"] = {"review": review["id"], "status": "delivered", "coverage": "complete",
                                      "role": "senior-review:premise-auditor" if lens == 0 else "senior-review:isolated-worker",
                                      "gaps": [], "candidate": job["candidate"],
                                      "check": {"kind": "verification", "lens": lens,
                                                "input_mode": "full-context" if lens == 0 else "verification",
                                                "targets": [{"job_id": job["job_id"], "finding_id": finding["id"]}],
                                                "independent": True, "evidence": ["navigation.py:3"], "verdict": verdict}}
    return deliveries


def verdicts_of(review, finding, verdicts):
    rows, skipped = experience.derive_rows(review, deliveries_for(review, finding, verdicts), "run-1", RECORDED)
    assert skipped == 0, skipped
    return [row["verdict"] for row in rows]


class ExperienceTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve()
        (self.project / ".daodan").mkdir()
        (self.project / ".daodan/.daodan-root").touch()
        # The project is its own home even when the temporary directory sits inside a repository.
        ceiling = mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.project.parent)})
        ceiling.start()
        self.addCleanup(ceiling.stop)

    def run_cli(self, *arguments):
        result = subprocess.run([sys.executable, str(Path(experience.__file__)), *map(str, arguments)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def form_fact(self):
        """Three changeset reviews called the member's premise on the target a false positive."""
        experience.append_rows(self.project, [
            {"schema": experience.LEDGER_SCHEMA, "run_id": f"run-{index}", "review_id": "review-1",
             "recorded_at": RECORDED, "review_basis": "changeset", "specialist_id": MEMBER,
             "symbol_id": TARGET["symbol_id"], "digests": {key: TARGET[key] for key in experience.DIGEST_FIELDS},
             "parser_fingerprint": TARGET["parser_fingerprint"], "verdict": "FALSE_POSITIVE", "premise": PREMISE}
            for index in range(3)])

    def test_brief_delivers_learned_facts_to_bound_members(self):
        self.form_fact()
        review = prepared()
        roster_path = self.project / "prepared.json"
        facts_path = self.project / "facts.json"
        roster_path.write_text(json.dumps(review), encoding="utf-8")
        report = self.run_cli("brief", "--project", self.project, "--roster", roster_path, "--out", facts_path)
        self.assertEqual(report, {"facts": 1, "gaps": []})
        jobs = json.loads(facts_path.read_text(encoding="utf-8"))["jobs"]
        self.assertEqual([job["job_id"] for job in jobs], [job["job_id"] for job in review["jobs"]])
        members = {member["specialist_id"]: member["facts"] for job in jobs for member in job["members"]}
        self.assertEqual(set(members), {member for job in review["jobs"] for member in job["specialist_ids"]})
        self.assertEqual(members[MEMBER][0]["symbol_id"], TARGET["symbol_id"])
        self.assertEqual(members[MEMBER][0]["run_review_ids"], [f"run-{index}/review-1" for index in range(3)])
        self.assertEqual(members["senior-review:accessible-perception-auditor"], [])

    def test_facts_of_another_review_basis_are_not_offered(self):
        self.form_fact()
        result = experience.brief(self.project, {**prepared(), "review_basis": "content"})
        self.assertEqual([member["facts"] for job in result["jobs"] for member in job["members"]], [[], []])

    def test_record_persists_verified_outcome_of_bound_job(self):
        review = prepared()
        job = review["jobs"][0]
        deliveries = deliveries_for(review, finding_of(), {0: "HOLDS", 1: "FALSE_POSITIVE"})
        run_dir = self.project / ".daodan/runs/run-1"
        run_dir.mkdir(parents=True)
        (run_dir / "work.json").write_text(json.dumps({"reviews": [review], "deliveries": deliveries}), encoding="utf-8")
        report = self.run_cli("record", "--project", self.project, "--run-id", "run-1", "--review-id", review["id"])
        self.assertEqual(report, {"rows_written": 1, "rows_skipped": 0, "ended_fact_ids": []})
        rows, skipped = experience.parse_rows((self.project / ".daodan/review-experience/ledger.jsonl").read_bytes())
        self.assertEqual(skipped, 0)
        self.assertEqual([(row["job_id"], row["specialist_id"], row["verdict"]) for row in rows],
                         [(job["job_id"], MEMBER, "FALSE_POSITIVE")])

    def test_only_discovery_jobs_receive_facts_and_are_recorded(self):
        for mode in ("full-context", "verification"):
            with self.subTest(mode=mode):
                review = prepared(input_mode=mode)
                result = experience.brief(self.project, review)
                self.assertEqual(result["jobs"], [])
                self.assertEqual(result["gaps"], ["no discovery job in the prepared roster"])
                self.assertEqual(verdicts_of(review, finding_of(), {0: "HOLDS", 1: "FALSE_POSITIVE"}), [])

    def test_record_respects_bound_verification_policy(self):
        lenses = {0: "HOLDS", 1: "FALSE_POSITIVE"}
        cases = [
            ("branch", "critical-high", "High", 80, lenses, 1),
            ("branch", "critical", "Critical", 80, {1: "FALSE_POSITIVE"}, 1),
            ("branch", "critical", "High", 80, {1: "FALSE_POSITIVE", 2: "FALSE_POSITIVE"}, 0),
            ("branch", "critical-high", "High", 80, {1: "FALSE_POSITIVE"}, 0),
            ("branch", "all-above-floor", "Medium", 80, {1: "FALSE_POSITIVE", 2: "FALSE_POSITIVE"}, 1),
            ("branch", "all-above-floor", "Medium", 80, {1: "FALSE_POSITIVE"}, 0),
            # Light follows its roster's level too: quick leaves High unverified.
            ("light", "critical-high", "High", 80, lenses, 1),
            ("light", "critical", "High", 80, lenses, 0),
            # The floor is 50%; no score counts as 60; a fraction is a percentage.
            ("branch", "critical-high", "High", 49, {**lenses, 2: "FALSE_POSITIVE"}, 0),
            ("branch", "critical-high", "High", MISSING, lenses, 1),
            ("branch", "critical-high", "High", None, lenses, 1),
            ("branch", "critical-high", "High", 0.85, lenses, 1),
            ("branch", "critical-high", "High", 0.4, lenses, 0),
        ]
        for shape, mode, severity, confidence, verdicts, expected in cases:
            with self.subTest(shape=shape, mode=mode, severity=severity, confidence=str(confidence),
                              lenses=list(verdicts)):
                review = prepared(shape=shape, verification=mode)
                self.assertEqual(verdicts_of(review, finding_of(severity, confidence), verdicts),
                                 ["FALSE_POSITIVE"] * expected)

    def test_a_full_panel_at_a_lower_level_decides_by_the_panel_rule(self):
        review = prepared(shape="branch", verification="critical-high")  # `--rigorous` adds Lenses 2 and 3
        split = {0: "HOLDS", 1: "FALSE_POSITIVE", 2: "REAL"}
        self.assertEqual(verdicts_of(review, finding_of(), {**split, 3: "REAL"}), ["REAL"])
        self.assertEqual(verdicts_of(review, finding_of(), split), [])  # Lens 3 is missing: no outcome
        self.assertEqual(verdicts_of(review, finding_of(), {**split, 2: "FALSE_POSITIVE"}), ["FALSE_POSITIVE"])

    def test_an_unknown_verification_is_an_error(self):
        for value in (None, "Critical-High"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "unsupported verification"):
                experience.derive_rows({**prepared(), "verification": value}, {}, "run-1", RECORDED)

    def test_unknown_mode_cannot_silently_omit_one_job(self):
        review = prepared()
        review["jobs"].append({**review["jobs"][0], "job_id": "job-custom", "input_mode": "custom"})
        for call in (lambda: experience.brief(self.project, review),
                     lambda: experience.derive_rows(review, {}, "run-1", RECORDED)):
            with self.assertRaisesRegex(ValueError, "input_mode.*custom"):
                call()


if __name__ == "__main__":
    unittest.main()
