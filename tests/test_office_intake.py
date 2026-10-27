"""Office workflow rationalization: one intake, one route vocabulary, three format entries.

These tests verify source and generated instructions on every host, not
installed host execution.
"""

import sys
import unittest
from pathlib import Path


REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "scripts/daodan").is_dir()
)
for import_root in (REPO_ROOT, REPO_ROOT / "tests"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.daodan.load import load_plugin
from host_binding_assertions import loaded_instruction_text
import office_entries
from test_office_unified_contract import use_published_office


OFFICE = REPO_ROOT / "plugins/office"
ADAPTERS = REPO_ROOT / "adapters"
WORKFLOWS = ("presentation", "document", "workbook")
FORMAT_METHODS = ("pptx", "docx", "xlsx")
ROUTES = ("Substantial", "Narrow", "Read-only")


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _normalized(text):
    return " ".join(text.split())


class OfficeIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        use_published_office(cls)

    @classmethod
    def tearDownClass(cls):
        """The shared publisher cleans its immutable packages at process exit."""

    def test_entries_are_named_by_format(self):
        # verify and fix act on an existing file; theme creates a template, not a file from a brief;
        # start routes a request to the others. The seven entries are `daodan`
        # workflows: office keeps the methods, the roles and the contracts.
        daodan = load_plugin(office_entries.DAODAN)
        self.assertEqual(
            sorted(set(office_entries.ENTRY_NAMES) - set(daodan.components.workflows)), []
        )
        self.assertEqual(set(self.plugin.components.workflows), set())
        self.assertIn("intake", self.plugin.components.skills)

    def test_every_entry_starts_with_the_shared_intake_on_every_host(self):
        for host, entries in self.entries.items():
            for workflow in WORKFLOWS:
                with self.subTest(host=host, workflow=workflow):
                    path = office_entries.entry_path(entries, host, workflow)
                    text = _normalized(loaded_instruction_text(self, path, host))
                    self.assertIn("Load `office:intake` first", text)
                    self.assertRegex(text, r"read-only (?:route|work) never writes")

    def test_intake_defines_one_round_and_three_routes(self):
        text = _normalized(_read(OFFICE / "skills/intake/SKILL.md"))
        for route in ROUTES:
            with self.subTest(route=route):
                self.assertIn(f"| {route} |", text)
        self.assertIn("Never overwrite a supplied file", text)
        self.assertIn("Shortening/restructuring is substantial", text)
        self.assertIn("remaining material decisions in one round", text)
        self.assertIn("A read-only request authorizes no edit", text)

    def test_intake_ships_on_every_host(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                shipped = [path for path in package.rglob("SKILL.md") if "name: intake" in _read(path)]
                self.assertTrue(shipped, f"office:intake missing from the {host} package")

    def test_format_methods_add_questions_to_the_intake_round_instead_of_asking_separately(self):
        for method in FORMAT_METHODS:
            with self.subTest(method=method):
                text = _normalized(_read(OFFICE / f"skills/{method}/SKILL.md"))
                self.assertIn("`office:intake`", text)
                self.assertNotIn("in one round of questions", text)

    def test_presentation_reviewer_accepts_an_unchanged_source_deck(self):
        text = _normalized(_read(OFFICE / "roles/presentation-reviewer.md"))
        self.assertIn("On a read-only review the deck under review is the unchanged source", text)
        method = _normalized(_read(OFFICE / "skills/pptx/SKILL.md"))
        self.assertIn("on the read-only route after rendering the unchanged source", method)

    def test_taste_reuses_the_settled_brief_without_another_intake_or_inherited_creative_phase(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                intake = _normalized(_read(package / "skills/intake/SKILL.md"))
                self.assertIn("An aesthetic reference is optional", intake)
                self.assertIn("required Taste provider", intake)
                self.assertIn("references/art-direction.md", intake)
                self.assertIn("without an upstream-admission interview", intake)
                self.assertIn("Inherited/narrow/read-only operations do not open a creative dependency phase", intake)
                self.assertRegex(intake, r"Missing required capability, after activation, blocks only dependent deliveries "
                                        r"while independent work continues")


if __name__ == "__main__":
    unittest.main()
