"""Office workflow rationalization: one intake, one route vocabulary, three format entries.

These tests verify source and generated instructions on every host, not
installed host execution.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "scripts/daodan").is_dir()
)
for import_root in (REPO_ROOT, REPO_ROOT / "tests"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from host_binding_assertions import loaded_instruction_text


OFFICE = REPO_ROOT / "plugins/office"
ADAPTERS = REPO_ROOT / "adapters"
WORKFLOWS = ("presentation", "document", "workbook")
FORMAT_METHODS = ("presentation-design", "docx", "xlsx")
ROUTES = ("Substantial", "Narrow", "Read-only")


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _normalized(text):
    return " ".join(text.split())


def _temp_dir():
    """Keep temporary files on the repository drive so package paths resolve."""
    return str(REPO_ROOT) if os.name == "nt" else None


def _entry_path(package, host, workflow):
    if host == "copilot":
        coordinator = package / f"agents/{workflow}-coordinator.agent.md"
        return coordinator if coordinator.is_file() else package / f"prompts/{workflow}.prompt.md"
    return package / {
        "claude": f"commands/{workflow}.md",
        "codex": f"skills/{workflow}-workflow/SKILL.md",
        "pi": f"prompts/office-{workflow}.md",
        "opencode": f"commands/{workflow}.md",
    }[host]


class OfficeIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = load_plugin(OFFICE)
        cls.temporary = tempfile.TemporaryDirectory(dir=_temp_dir())
        cls.packages = {}
        for host in HOSTS:
            package = Path(cls.temporary.name) / host / "office"
            render_plugin(cls.plugin, load_adapter(ADAPTERS, host), package, adapters_root=ADAPTERS)
            cls.packages[host] = package

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_entries_are_named_by_format(self):
        self.assertEqual(set(self.plugin.components.workflows), set(WORKFLOWS))
        self.assertIn("intake", self.plugin.components.skills)

    def test_every_entry_starts_with_the_shared_intake_on_every_host(self):
        for host, package in self.packages.items():
            for workflow in WORKFLOWS:
                with self.subTest(host=host, workflow=workflow):
                    text = _normalized(loaded_instruction_text(self, _entry_path(package, host, workflow), host))
                    self.assertIn("Load `office:intake` first", text)
                    self.assertIn("read-only route never writes", text)

    def test_intake_defines_one_round_and_three_routes(self):
        text = _normalized(_read(OFFICE / "skills/intake/SKILL.md"))
        for route in ROUTES:
            with self.subTest(route=route):
                self.assertIn(f"| {route} |", text)
        self.assertIn("Never overwrite a supplied file", text)
        self.assertIn("Shortening and restructuring are substantial", text)
        self.assertIn("ask the remaining decisions that change the result in one round", text)
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
        method = _normalized(_read(OFFICE / "skills/presentation-design/SKILL.md"))
        self.assertIn("on the read-only route after rendering the unchanged source", method)


if __name__ == "__main__":
    unittest.main()
