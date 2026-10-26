"""Workbook production delegates to GridCraft, and every engine states its template limits.

These tests inspect real compiler output. They do not establish installed-host
execution, GridCraft calculation or Microsoft Excel fidelity.
"""

import fnmatch
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
for import_root in (REPO_ROOT, REPO_ROOT / "tests"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.catalogs import render_catalog
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from host_binding_assertions import canonical_markdown, loaded_instruction_text, without_host_binding
import office_entries


OFFICE = REPO_ROOT / "plugins/office"
ADAPTERS = REPO_ROOT / "adapters"
RUNTIME = Path("skills/gridcraft/references/runtime.md")
ENTRY_PATHS = {
    "claude": "commands/workbook.md",
    "copilot": "prompts/workbook.prompt.md",
    "codex": "skills/workbook-workflow/SKILL.md",
    "pi": "prompts/daodan-workbook.md",
    "opencode": "commands/workbook.md",
}


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _normalized(text):
    return " ".join(text.split())


class GridCraftContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = load_plugin(OFFICE)
        cls.temporary = tempfile.TemporaryDirectory(dir=str(REPO_ROOT) if os.name == "nt" else None)
        cls.packages = {}
        cls.adapters = {}
        cls.entries = office_entries.render_entries(cls.temporary.name, ("workbook",))
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            package = Path(cls.temporary.name) / host / "office"
            render_plugin(cls.plugin, adapter, package, adapters_root=ADAPTERS)
            cls.packages[host] = package
            cls.adapters[host] = adapter

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_workbook_production_routes_to_gridcraft_without_a_silent_fallback(self):
        self.assertIn("gridcraft", self.plugin.components.skills)
        self.assertNotIn("gridcraft", self.plugin.components.roles)
        for host, package in self.packages.items():
            with self.subTest(host=host):
                entry = loaded_instruction_text(
                    self, self.entries[host] / ENTRY_PATHS[host], host
                )
                self.assertIn("`office:gridcraft`", entry)
                method = _normalized(_read(package / "skills/xlsx/SKILL.md"))
                self.assertIn("load `office:gridcraft`", method)
                self.assertIn("do not silently substitute it", method)
                self.assertNotIn("openpyxl", method)
                self.assertNotIn("bundled spreadsheet", method)
                production = _normalized(_read(package / "skills/gridcraft/SKILL.md"))
                self.assertIn("references/runtime.md", production)
                self.assertRegex(production, r"(?i)save a no-edit round-trip to a separate candidate")
                self.assertRegex(production, r"(?i)not its only oracle")
                self.assertRegex(production, r"(?i)missing runtime blocks dependent production")
                self.assertRegex(production, r"(?i)never overwrite the template")

    def test_runtime_reference_is_pinned_and_states_its_unproven_limits(self):
        source = _normalized(_read(OFFICE / RUNTIME))
        self.assertIn("ac8da7d49cbeb4be6aa1ad5869f3d29fe2da8cd9", source)
        self.assertIn("v0.11.1", source)
        self.assertIn("MIT OR Apache-2.0", source)
        self.assertRegex(source, r"(?i)alpha")
        self.assertRegex(source, r"(?i)not yet proven in Microsoft Excel")
        self.assertRegex(source, r"(?i)slicers.*timelines.*data model.*dropped on save")
        self.assertRegex(source, r"(?i)documents no folder-confinement flags")
        self.assertRegex(source, r"(?i)do not claim confinement")

    def test_runtime_reference_and_registration_ship_on_all_five_hosts(self):
        source = _read(OFFICE / RUNTIME)
        for host, package in self.packages.items():
            with self.subTest(host=host):
                self.assertTrue((package / "skills/gridcraft/SKILL.md").is_file())
                exported = without_host_binding(self, _read(package / RUNTIME), host)
                self.assertEqual(canonical_markdown(exported), canonical_markdown(source))
                catalog = json.loads(render_catalog(
                    host, [self.plugin], "0.0.0", {"office": package},
                    layout=self.adapters[host].layout,
                ))
                if host == "opencode":
                    self.assertIn(
                        ("office:gridcraft", "skills/gridcraft/SKILL.md"),
                        {(skill["id"], skill["file"])
                         for skill in catalog["daodan"]["plugins"]["office"]["skills"]},
                    )
                elif host == "pi":
                    directory = "exports/pi/plugins/office/skills/gridcraft"
                    self.assertTrue(any(
                        fnmatch.fnmatchcase(directory, pattern.removeprefix("./") + "/*")
                        for pattern in catalog["pi"]["skills"]
                    ))
                else:
                    self.assertIn("./skills/gridcraft", catalog["plugins"][0]["skills"])

    def test_every_engine_states_how_it_handles_templates(self):
        expectations = {
            "skills/deckcraft/references/runtime.md": (r"\.potx", r"presentation content type",
                                                       r"#1111", r"#300"),
            "skills/wordcraft/references/runtime.md": (r"\.dotx", r"file\.newFromTemplate",
                                                       r"file\.saveTemplate"),
            "skills/gridcraft/references/runtime.md": (r"\.xltx", r"New from template.*missing"),
        }
        for relative, patterns in expectations.items():
            text = _normalized(_read(OFFICE / relative))
            for pattern in (*patterns, r"(?i)never overwrit"):
                with self.subTest(reference=relative, pattern=pattern):
                    self.assertRegex(text, pattern)


if __name__ == "__main__":
    unittest.main()
