"""Evidence-locator regressions independent of any measured model responses."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_eval


ROLE = "example:auditor"
CATALOG = {"roles": [{
    "id": ROLE, "is_reviewer": True, "trigger_when": "external access",
    "do_not_trigger_when": "no external access",
}]}
CASE = {"hunks": [
    {"id": "H1", "path": "path with spaces/source.py", "start_line": 7, "text": "return value\n"},
    {"id": "H2", "path": "other.py", "start_line": 30, "text": "await send(value)\n"},
]}


def entry(citation="[H1] candidate path with spaces/source.py:7 return value"):
    return {
        "trigger_line": citation, "reason": "Verify external access.",
        "role": ROLE, "tier": "tier2", "effort": "high",
    }


class LlmEvidenceValidationTests(unittest.TestCase):
    def validate(self, entries, case=CASE):
        warnings = []
        selected = run_eval.validate_llm({"mode": "full", "selected": entries}, case, CATALOG, warnings)
        return selected, warnings

    def test_prompt_side_token_is_parsed_separately_from_the_exact_path(self):
        for side in ("base", "candidate"):
            with self.subTest(side=side):
                selected, warnings = self.validate([entry(f"[H1] {side} path with spaces/source.py:7 return value")])
                self.assertEqual(selected, [ROLE])
                self.assertIn("omitted a side binding", warnings[0])

    def test_duplicate_role_activations_are_unioned_after_every_citation_is_validated(self):
        selected, warnings = self.validate([
            entry(),
            entry("[H2] candidate other.py:30 await send(value)"),
        ])
        self.assertEqual(selected, [ROLE])
        self.assertTrue(any("counted once" in warning for warning in warnings))
        with self.assertRaisesRegex(ValueError, "absent"):
            self.validate([entry(), entry("[H2] candidate other.py:30 await invented()")])

    def test_unknown_qualifiers_paths_hunks_lines_and_snippets_remain_invalid(self):
        invalid = [
            "[H1] arbitrary path with spaces/source.py:7 return value",
            "[H1] candidate wrong/path with spaces/source.py:7 return value",
            "[H99] candidate path with spaces/source.py:7 return value",
            "[H1] candidate path with spaces/source.py:8 return value",
            "[H1] candidate path with spaces/source.py:7 invented()",
            "[H1] candidate path with spaces/source.py:7   ",
        ]
        for citation in invalid:
            with self.subTest(citation=citation), self.assertRaises(ValueError):
                self.validate([entry(citation)])
        invalid_role = entry()
        invalid_role["role"] = "foreign:auditor"
        with self.assertRaisesRegex(ValueError, "Unknown reviewer"):
            self.validate([entry(), invalid_role])

    def test_explicit_evidence_side_must_match_when_bound(self):
        case = copy.deepcopy(CASE)
        case["hunks"][0]["side"] = "base"
        selected, warnings = self.validate([entry("[H1] base path with spaces/source.py:7 return value")], case)
        self.assertEqual(selected, [ROLE])
        self.assertEqual(warnings, [])
        for citation in [
            "[H1] candidate path with spaces/source.py:7 return value",
            "[H1] path with spaces/source.py:7 return value",
        ]:
            with self.subTest(citation=citation), self.assertRaisesRegex(ValueError, "side"):
                self.validate([entry(citation)], case)

    def test_path_that_itself_begins_candidate_is_not_renamed(self):
        case = copy.deepcopy(CASE)
        case["hunks"][0]["path"] = "candidate source.py"
        self.assertEqual(
            self.validate([entry("[H1] candidate candidate source.py:7 return value")], case)[0],
            [ROLE],
        )
        self.assertEqual(
            self.validate([entry("[H1] candidate source.py:7 return value")], case)[0],
            [ROLE],
        )

    def test_invalid_json_shapes_fail_with_validation_errors(self):
        for raw in ([], None, {"mode": "full", "selected": [None]}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                run_eval.validate_llm(raw, CASE, CATALOG)


if __name__ == "__main__":
    unittest.main()
