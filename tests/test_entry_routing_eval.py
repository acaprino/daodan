"""Tests for the entry-routing activation eval harness (`evals/entry-routing/run_eval.py`).

Covers only the tool's own logic: `--check` schema validation on `cases.json`
and the `--verify-results` scoring arithmetic on small synthetic fixtures. No
model is invoked and no network request is made; this suite does not run the
measured eval itself (docs/specs/2026-10-28-chat-entry-routing-design.md, S-6).
"""

import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "evals" / "entry-routing" / "run_eval.py"
CASES_PATH = REPO_ROOT / "evals" / "entry-routing" / "cases.json"


def load_module():
    spec = importlib.util.spec_from_file_location("run_eval", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_eval = load_module()


def make_case(case_id, kind="task", expected_entry="/daodan:fix-bug", lang="en"):
    return {
        "id": case_id,
        "lang": lang,
        "prompt": "placeholder prompt text",
        "kind": kind,
        "expected_entry": expected_entry,
    }


class ValidateRealCasesTests(unittest.TestCase):
    """The shipped cases.json itself must pass its own schema validation."""

    def setUp(self):
        with open(CASES_PATH, encoding="utf-8") as fh:
            self.cases = json.load(fh)

    def test_exactly_65_cases_and_no_problems(self):
        problems = run_eval.validate_cases(self.cases)
        self.assertEqual(problems, [])
        self.assertEqual(len(self.cases), 65)

    def test_kind_split_is_40_10_15(self):
        task = [c for c in self.cases if c["kind"] == "task"]
        vertical_or_keyword = [c for c in self.cases if c["kind"] in ("vertical", "keyword")]
        non_task = [c for c in self.cases if c["kind"] == "non-task"]
        self.assertEqual(len(task), 40)
        self.assertEqual(len(vertical_or_keyword), 10)
        self.assertEqual(len(non_task), 15)

    def test_worked_examples_ex1_to_ex6_present(self):
        by_prompt = {c["prompt"]: c for c in self.cases}
        expectations = {
            "c'è un bug nel login, risolviamolo": "/daodan:fix-bug",
            "voglio investigare perché i test falliscono": "/daodan:investigate-problem",
            "rifattorizziamo la classe UserService": "/daodan:refactor-code",
            "come funziona il modulo di login?": None,
            "fai un audit SEO del sito": "/digital-marketing:seo-audit",
            "questo componente React rirenderizza troppo": "react-development:react-best-practices",
        }
        for prompt, expected_entry in expectations.items():
            self.assertIn(prompt, by_prompt, f"missing worked example prompt: {prompt!r}")
            self.assertEqual(by_prompt[prompt]["expected_entry"], expected_entry, prompt)


class ValidateCasesSchemaTests(unittest.TestCase):
    """Synthetic fixtures for each kind of schema defect validate_cases must catch."""

    def _valid_65(self):
        cases = []
        for i in range(40):
            cases.append(make_case(f"task-{i:03d}", kind="task"))
        for i in range(10):
            kind = "vertical" if i % 2 == 0 else "keyword"
            cases.append(make_case(f"vert-{i:03d}", kind=kind, expected_entry="some:target"))
        for i in range(15):
            cases.append(make_case(f"nontask-{i:03d}", kind="non-task", expected_entry=None))
        return cases

    def test_valid_fixture_has_no_problems(self):
        self.assertEqual(run_eval.validate_cases(self._valid_65()), [])

    def test_wrong_count_is_reported(self):
        cases = self._valid_65()[:-1]
        problems = run_eval.validate_cases(cases)
        self.assertTrue(problems)
        self.assertTrue(any("65" in p for p in problems))

    def test_duplicate_id_is_reported(self):
        cases = self._valid_65()
        cases[1] = dict(cases[1])
        cases[1]["id"] = cases[0]["id"]
        problems = run_eval.validate_cases(cases)
        self.assertTrue(any("duplicate" in p.lower() for p in problems))

    def test_missing_expected_entry_on_task_case_is_reported(self):
        cases = self._valid_65()
        cases[0] = dict(cases[0])
        cases[0]["expected_entry"] = None
        problems = run_eval.validate_cases(cases)
        self.assertTrue(
            any("expected_entry" in p and cases[0]["id"] in p for p in problems),
            problems,
        )

    def test_non_null_expected_entry_on_non_task_case_is_reported(self):
        cases = self._valid_65()
        non_task_index = next(i for i, c in enumerate(cases) if c["kind"] == "non-task")
        cases[non_task_index] = dict(cases[non_task_index])
        cases[non_task_index]["expected_entry"] = "/daodan:fix-bug"
        problems = run_eval.validate_cases(cases)
        self.assertTrue(
            any(
                "expected_entry" in p and cases[non_task_index]["id"] in p
                for p in problems
            ),
            problems,
        )


class ScoreResultsTests(unittest.TestCase):
    """Scoring arithmetic for --verify-results on a small synthetic case set."""

    def setUp(self):
        self.cases = [
            make_case("t1", kind="task", expected_entry="/daodan:fix-bug"),
            make_case("t2", kind="task", expected_entry="/daodan:new-feature"),
            make_case("t3", kind="task", expected_entry="/daodan:write-tests"),
            make_case("t4", kind="task", expected_entry="/daodan:tidy-repo"),
            make_case("v1", kind="vertical", expected_entry="/digital-marketing:seo-audit"),
            make_case("v2", kind="keyword", expected_entry="react-development:react-best-practices"),
            make_case("n1", kind="non-task", expected_entry=None),
            make_case("n2", kind="non-task", expected_entry=None),
            make_case("n3", kind="non-task", expected_entry=None),
            make_case("n4", kind="non-task", expected_entry=None),
        ]

    def test_pass_case(self):
        results = {
            "with_hooks": {
                "t1": "/daodan:fix-bug",
                "t2": "/daodan:new-feature",
                "t3": "/daodan:write-tests",
                "t4": "/daodan:tidy-repo",
                "v1": "/digital-marketing:seo-audit",
                "v2": "react-development:react-best-practices",
                "n1": None,
                "n2": None,
                "n3": None,
                "n4": None,
            },
            "without_hooks": {
                "t1": None,
                "t2": None,
                "t3": None,
                "t4": "/daodan:tidy-repo",
                "v1": None,
                "v2": None,
                "n1": "/daodan:fix-bug",
                "n2": None,
                "n3": None,
                "n4": None,
            },
        }
        scores = run_eval.score_results(self.cases, results)
        self.assertEqual(scores["positive_total"], 6)
        self.assertEqual(scores["negative_total"], 4)
        self.assertAlmostEqual(scores["accuracy_with_hooks"], 1.0)
        self.assertAlmostEqual(scores["accuracy_without_hooks"], 1 / 6)
        self.assertAlmostEqual(scores["trigger_rate_with_hooks"], 0.0)
        self.assertAlmostEqual(scores["trigger_rate_without_hooks"], 0.25)
        self.assertTrue(scores["meets_accuracy_target"])
        self.assertTrue(scores["meets_trigger_rate_target"])
        self.assertTrue(scores["better_than_baseline_accuracy"])
        self.assertTrue(scores["better_than_baseline_trigger_rate"])
        self.assertTrue(scores["passed"])

    def test_matches_a_command_invocation_without_its_leading_slash(self):
        # A real Skill tool call never carries the host's leading slash (the
        # probe records "daodan:fix-bug", not "/daodan:fix-bug"), while
        # expected_entry for a command case is written with it.
        results = {
            "with_hooks": {
                "t1": "daodan:fix-bug", "t2": "daodan:new-feature",
                "t3": "daodan:write-tests", "t4": "daodan:tidy-repo",
                "v1": "digital-marketing:seo-audit",
                "v2": "react-development:react-best-practices",
                "n1": None, "n2": None, "n3": None, "n4": None,
            },
            "without_hooks": {k: None for k in ("t1", "t2", "t3", "t4", "v1", "v2", "n1", "n2", "n3", "n4")},
        }
        scores = run_eval.score_results(self.cases, results)
        self.assertAlmostEqual(scores["accuracy_with_hooks"], 1.0)

    def test_fail_case_below_accuracy_target_and_not_better_than_baseline(self):
        # Only 2 of 6 positive cases correct with hooks (33%, below the 85%
        # target); the baseline matches it exactly, so "better" also fails.
        same_with_and_without = {
            "t1": "/daodan:fix-bug",
            "t2": "/daodan:new-feature",
            "t3": None,
            "t4": None,
            "v1": None,
            "v2": None,
            "n1": None,
            "n2": None,
            "n3": None,
            "n4": None,
        }
        results = {
            "with_hooks": dict(same_with_and_without),
            "without_hooks": dict(same_with_and_without),
        }
        scores = run_eval.score_results(self.cases, results)
        self.assertAlmostEqual(scores["accuracy_with_hooks"], 2 / 6)
        self.assertFalse(scores["meets_accuracy_target"])
        self.assertFalse(scores["better_than_baseline_accuracy"])
        self.assertFalse(scores["passed"])

    def test_fail_case_trigger_rate_too_high(self):
        results = {
            "with_hooks": {
                "t1": "/daodan:fix-bug",
                "t2": "/daodan:new-feature",
                "t3": "/daodan:write-tests",
                "t4": "/daodan:tidy-repo",
                "v1": "/digital-marketing:seo-audit",
                "v2": "react-development:react-best-practices",
                # 2 of 4 non-task cases wrongly invoke an entry: 50%, above 10%.
                "n1": "/daodan:fix-bug",
                "n2": "/daodan:new-feature",
                "n3": None,
                "n4": None,
            },
            "without_hooks": {
                "t1": None,
                "t2": None,
                "t3": None,
                "t4": None,
                "v1": None,
                "v2": None,
                "n1": "/daodan:fix-bug",
                "n2": "/daodan:new-feature",
                "n3": None,
                "n4": None,
            },
        }
        scores = run_eval.score_results(self.cases, results)
        self.assertAlmostEqual(scores["trigger_rate_with_hooks"], 0.5)
        self.assertFalse(scores["meets_trigger_rate_target"])
        self.assertFalse(scores["better_than_baseline_trigger_rate"])
        self.assertFalse(scores["passed"])


class CliTests(unittest.TestCase):
    """Wiring tests for main(): --check and --verify-results exit codes and output."""

    def test_check_on_real_cases_json_exits_zero(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = run_eval.main(["--check"])
        self.assertEqual(exit_code, 0)

    def test_check_on_broken_cases_file_exits_nonzero(self, ):
        import tempfile
        broken = [make_case(f"x{i}") for i in range(5)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = run_eval.main(["--check", "--cases", str(path)])
            self.assertNotEqual(exit_code, 0)
            self.assertIn("65", buf.getvalue())

    def test_verify_results_cli_reports_pass(self):
        import tempfile
        cases = ValidateCasesSchemaTests()._valid_65()
        with_hooks = {}
        without_hooks = {}
        non_task_ids = [c["id"] for c in cases if c["kind"] == "non-task"]
        for c in cases:
            if c["kind"] == "non-task":
                with_hooks[c["id"]] = None
                # One false trigger without the hooks, so the baseline
                # false-trigger rate is strictly worse than with the hooks.
                without_hooks[c["id"]] = (
                    "/daodan:fix-bug" if c["id"] == non_task_ids[0] else None
                )
            else:
                with_hooks[c["id"]] = c["expected_entry"]
                without_hooks[c["id"]] = None
        results = {"with_hooks": with_hooks, "without_hooks": without_hooks}
        with tempfile.TemporaryDirectory() as tmp:
            cases_path = Path(tmp) / "cases.json"
            cases_path.write_text(json.dumps(cases), encoding="utf-8")
            results_path = Path(tmp) / "results.json"
            results_path.write_text(json.dumps(results), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = run_eval.main(
                    ["--verify-results", str(results_path), "--cases", str(cases_path)]
                )
            self.assertEqual(exit_code, 0)
            self.assertIn("PASS", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
