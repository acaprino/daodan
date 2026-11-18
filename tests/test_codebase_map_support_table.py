"""The support document is what `support_table.py` writes now, from the product and the committed results."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import support_table  # noqa: E402


class SupportTableTests(unittest.TestCase):
    def test_the_committed_document_is_the_one_the_script_writes(self):
        self.assertEqual(support_table.check(), [])

    def test_a_document_that_differs_is_a_problem(self):
        with tempfile.TemporaryDirectory() as folder:
            stale = Path(folder) / "supporto.md"
            stale.write_text("# Supporto\n", encoding="utf-8")
            self.assertTrue(support_table.check(stale))

    def test_a_measure_names_its_file_and_a_missing_one_says_so(self):
        text = support_table.render()
        self.assertIn("2026-11-16-finale.report.json", text)
        self.assertIn("daodan_stack.json", text)
        self.assertIn("non misurato", text)


if __name__ == "__main__":
    unittest.main()
