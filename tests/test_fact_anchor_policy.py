"""Exercise policy drift detection with independent copies and mutations."""
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import lint_fact_anchors as linter
POLICY_ANCHORS = (
    "constraint-saturation-threshold",
    "web-api-global-rate",
    "broker-archetype-count",
)
WORKING_ANCHORS = (
    "working-principle-material-assumptions",
    "working-principle-sufficient-simplicity",
    "working-principle-authorized-scope",
    "working-principle-observable-verification",
)
WORKING_OWNER = "CLAUDE.md"
WORKING_COPIES = (
    WORKING_OWNER,
    "AGENTS.md",
)


class TestPolicyAnchorTests(unittest.TestCase):
    def working_fixture(self, anchor_id):
        self.assertIn(anchor_id, linter.ANCHORS, "The shared working rule needs a drift anchor")
        anchor = linter.ANCHORS[anchor_id]
        self.assertEqual(anchor[0], WORKING_OWNER)
        source = (ROOT / WORKING_OWNER).read_text(encoding="utf-8")
        matches = list(re.finditer(anchor[1], source))
        self.assertEqual(len(matches), 1, "The actual protocol must state its own anchored rule once")
        return anchor, matches[0].group(0)

    def check_working_fixture(self, anchor_id, texts):
        """Control only the filesystem boundary; retain the actual linter algorithm."""
        with patch.object(linter, "ANCHORS", {anchor_id: linter.ANCHORS[anchor_id]}), \
                patch.object(linter, "scan_files", return_value=iter(texts)), \
                patch.object(Path, "read_text", autospec=True,
                             side_effect=lambda path, **kwargs: texts[path]):
            return linter.check()

    def test_matching_working_rules_in_all_required_copies_are_accepted(self):
        for anchor_id in WORKING_ANCHORS:
            with self.subTest(anchor=anchor_id):
                _, statement = self.working_fixture(anchor_id)
                texts = {Path(copy): statement for copy in WORKING_COPIES}

                conflicts, orphans, _, checked, scanned = self.check_working_fixture(anchor_id, texts)

                self.assertEqual((conflicts, orphans, checked, scanned), ([], [], 1, len(WORKING_COPIES)))

    def test_changed_working_copy_reports_the_protocol_and_mutated_source(self):
        for anchor_id in WORKING_ANCHORS:
            for copy in WORKING_COPIES[1:]:
                with self.subTest(anchor=anchor_id, copy=copy):
                    _, statement = self.working_fixture(anchor_id)
                    texts = {Path(required): statement for required in WORKING_COPIES}
                    prefix = statement.split(":", 1)[0]
                    texts[Path(copy)] = prefix + ": Omit this approved execution obligation."

                    conflicts, orphans, _, checked, scanned = self.check_working_fixture(anchor_id, texts)

                    self.assertEqual((len(conflicts), orphans, checked, scanned), (1, [], 1, len(WORKING_COPIES)))
                    self.assertEqual(conflicts[0][0], anchor_id)
                    reported = {path for paths in conflicts[0][3].values() for path in paths}
                    self.assertIn(WORKING_OWNER, reported)
                    self.assertIn(copy, reported)

    def test_every_working_rule_requires_each_independently_loaded_source_copy(self):
        for anchor_id in WORKING_ANCHORS:
            for copy in WORKING_COPIES:
                for absent_file in (False, True):
                    with self.subTest(anchor=anchor_id, copy=copy, absent_file=absent_file):
                        _, statement = self.working_fixture(anchor_id)
                        texts = {Path(required): statement for required in WORKING_COPIES}
                        if absent_file:
                            texts.pop(Path(copy))
                        else:
                            texts[Path(copy)] = "The file exists but its required execution rule was removed."

                        conflicts, orphans, _, _, scanned = self.check_working_fixture(anchor_id, texts)

                        self.assertEqual(conflicts, [])
                        missing = [row for row in orphans if row[0] == anchor_id]
                        self.assertTrue(missing, "Deleting an independently loaded rule must fail the linter")
                        self.assertTrue(any(copy in row[3] or (copy == WORKING_OWNER and row[1] == copy)
                                            for row in missing), "The failure must identify the missing source copy")
                        self.assertEqual(scanned, len(WORKING_COPIES) - 1 if absent_file else len(WORKING_COPIES))

    def test_working_rule_cosmetic_case_and_whitespace_remain_equivalent(self):
        for anchor_id in WORKING_ANCHORS:
            with self.subTest(anchor=anchor_id):
                _, statement = self.working_fixture(anchor_id)
                prefix, value = statement.split(": ", 1)
                texts = {Path(copy): statement for copy in WORKING_COPIES}
                texts[Path("AGENTS.md")] = prefix + ": " + value.upper().replace(" ", "  ")

                conflicts, orphans, _, checked, _ = self.check_working_fixture(anchor_id, texts)

                self.assertEqual((conflicts, orphans, checked), ([], [], 1))

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
                mutated = (
                    statement[: match.start(1) - match.start()]
                    + "999"
                    + statement[match.end(1) - match.start() :]
                )
                result, owner, echo = self.check_fixture(anchor_id, statement, mutated)
                conflicts, orphans, _, checked, scanned = result
                self.assertEqual((len(conflicts), len(orphans), checked, scanned), (1, 0, 1, 2))
                reported = {path for paths in conflicts[0][3].values() for path in paths}
                self.assertEqual(reported, {owner.as_posix(), echo.as_posix()})

    def test_cosmetic_whitespace_does_not_change_a_policy(self):
        anchor_id = "working-principle-material-assumptions"
        owner_path, pattern, _ = linter.ANCHORS[anchor_id]
        source = (ROOT / owner_path).read_text(encoding="utf-8")
        statement = re.search(pattern, source).group(0)
        prefix, value = statement.split(": ", 1)
        echo = prefix + ": " + value.upper().replace(" ", "  ")
        texts = {Path(copy): statement for copy in WORKING_COPIES}
        texts[Path("instructions/nested/AGENTS.md")] = echo
        conflicts, orphans, _, checked, _ = self.check_working_fixture(anchor_id, texts)
        self.assertEqual((conflicts, orphans, checked), ([], [], 1))

    def test_silent_owner_cannot_be_replaced_by_an_instruction_echo(self):
        anchor_id = "constraint-saturation-threshold"
        owner_path, pattern, _ = linter.ANCHORS[anchor_id]
        source = (ROOT / owner_path).read_text(encoding="utf-8")
        statement = re.search(pattern, source).group(0)
        result, _, echo = self.check_fixture(anchor_id, "No canonical statement", statement)
        conflicts, orphans, _, checked, _ = result
        self.assertEqual((len(conflicts), len(orphans), checked), (0, 1, 0))
        self.assertIn(echo.as_posix(), orphans[0][3])


if __name__ == "__main__":
    unittest.main()
