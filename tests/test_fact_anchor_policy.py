"""Exercise policy drift detection with independent copies and mutations."""
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from scripts import lint_fact_anchors as linter


ROOT = Path(__file__).resolve().parents[1]
POLICY_ANCHORS = (
    "test-layer-ownership",
    "test-assertion-protection",
    "test-retirement-protection",
)


class TestPolicyAnchorTests(unittest.TestCase):
    def check_fixture(self, anchor_id, owner_text, echo_text):
        anchor = linter.ANCHORS[anchor_id]
        owner = Path(anchor[0])
        echo = Path("instructions/nested/AGENTS.md")
        texts = {owner: owner_text, echo: echo_text}
        with patch.object(linter, "ANCHORS", {anchor_id: anchor}), \
                patch.object(linter, "scan_files", return_value=iter(texts)), \
                patch.object(Path, "read_text", autospec=True,
                             side_effect=lambda path, **kwargs: texts[path]):
            return linter.check(), owner, echo

    def test_changed_independent_policy_copy_reports_both_sources(self):
        for anchor_id in POLICY_ANCHORS:
            with self.subTest(anchor=anchor_id):
                owner_path, pattern, _ = linter.ANCHORS[anchor_id]
                source = (ROOT / owner_path).read_text(encoding="utf-8")
                # Derive the fixture from the canonical source without pinning prose.
                match = re.search(pattern, source)
                self.assertIsNotNone(match, "anchored owner must still state its policy")
                statement = match.group(0)
                mutated = statement[:match.start(1) - match.start()] + "Unapproved policy"
                result, owner, echo = self.check_fixture(anchor_id, statement, mutated)
                conflicts, orphans, _, checked, scanned = result
                self.assertEqual((len(conflicts), len(orphans), checked, scanned), (1, 0, 1, 2))
                reported = {path for paths in conflicts[0][3].values() for path in paths}
                self.assertEqual(reported, {owner.as_posix(), echo.as_posix()})

    def test_silent_owner_cannot_be_replaced_by_an_instruction_echo(self):
        anchor_id = "test-retirement-protection"
        owner_path, pattern, _ = linter.ANCHORS[anchor_id]
        source = (ROOT / owner_path).read_text(encoding="utf-8")
        statement = re.search(pattern, source).group(0)
        result, _, echo = self.check_fixture(anchor_id, "No canonical statement", statement)
        conflicts, orphans, _, checked, _ = result
        self.assertEqual((len(conflicts), len(orphans), checked), (0, 1, 0))
        self.assertIn(echo.as_posix(), orphans[0][3])

    def test_cosmetic_whitespace_does_not_change_a_policy(self):
        anchor_id = "test-assertion-protection"
        owner_path, pattern, _ = linter.ANCHORS[anchor_id]
        source = (ROOT / owner_path).read_text(encoding="utf-8")
        statement = re.search(pattern, source).group(0)
        prefix, value = statement.split(": ", 1)
        echo = prefix + ": " + value.upper().replace(" ", "  ")
        result, _, _ = self.check_fixture(anchor_id, statement, echo)
        conflicts, orphans, _, checked, _ = result
        self.assertEqual((conflicts, orphans, checked), ([], [], 1))


if __name__ == "__main__":
    unittest.main()
