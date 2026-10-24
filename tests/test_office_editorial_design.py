"""Office's adapted editorial knowledge is local, reachable and shipped.

These contracts exercise real compiler outputs. They do not claim an installed
host has consulted a skill or that a document has been visually verified.
"""

import fnmatch
import json
import os
import re
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


OFFICE = REPO_ROOT / "plugins/office"
ADAPTERS = REPO_ROOT / "adapters"
DESIGN_SKILLS = ("design",)
LOCAL_SKILLS = DESIGN_SKILLS
DESIGN_REFERENCES = ("references/editorial-design.md", "references/typography.md")
LICENSE = Path("skills/design/references/LICENSE-APACHE-2.0.txt")
NOTICE = Path("skills/design/references/agentit-upstream.md")
THEME_NOTICE = Path("skills/design/references/theme-factory-upstream.md")
THEME_LICENSE = Path("skills/design/references/LICENSE-theme-factory-APACHE-2.0.txt")
MIT_NOTICES = {
    Path("skills/design/references/LICENSE-rampstackco-MIT.txt"): "RampStack",
    Path("skills/design/references/LICENSE-peterbamuhigire-MIT.txt"): "Peter Bamuhigire",
}
ROLE_PATHS = {
    "claude": "agents/{role}.md",
    "copilot": "agents/{role}.agent.md",
    "codex": "roles/{role}.md",
    "pi": "skills/office-{role}/SKILL.md",
    "opencode": "agents/{role}.md",
}
DOCUMENT_PATHS = {
    "claude": "commands/document.md",
    "copilot": "agents/document-coordinator.agent.md",
    "codex": "skills/document-workflow/SKILL.md",
    "pi": "prompts/office-document.md",
    "opencode": "commands/document.md",
}


def _read(path):
    return Path(path).read_text(encoding="utf-8")


class EditorialDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = load_plugin(OFFICE)
        cls.temporary = tempfile.TemporaryDirectory(dir=str(REPO_ROOT) if os.name == "nt" else None)
        cls.packages = {}
        cls.adapters = {}
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            package = Path(cls.temporary.name) / host / "office"
            render_plugin(cls.plugin, adapter, package, adapters_root=ADAPTERS)
            cls.packages[host] = package
            cls.adapters[host] = adapter

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def assert_skill_loads(self, text, skills=DESIGN_SKILLS):
        for skill in skills:
            self.assertIn(f"`office:{skill}`", text)

    def test_adapted_guides_are_owned_skills_without_an_external_agentit_provider(self):
        self.assertTrue(set(LOCAL_SKILLS) <= set(self.plugin.components.skills))
        self.assertFalse(set(LOCAL_SKILLS) & set(self.plugin.components.roles))
        self.assertFalse(set(LOCAL_SKILLS) & set(self.plugin.components.workflows))
        dependencies = (*self.plugin.required_dependencies, *self.plugin.optional_dependencies)
        self.assertFalse(any("agentit" in dependency.casefold() for dependency in dependencies))
        self.assertEqual(self.plugin.license, "MIT")
        self.assertFalse(self.plugin.mcp_servers)

    def test_both_guides_are_registered_by_every_host_catalog(self):
        for host, package in self.packages.items():
            catalog = json.loads(render_catalog(
                host, [self.plugin], "0.0.0", {"office": package}, layout=self.adapters[host].layout,
            ))
            for skill in LOCAL_SKILLS:
                with self.subTest(host=host, skill=skill):
                    relative = f"skills/{skill}/SKILL.md"
                    self.assertTrue((package / relative).is_file())
                    if host == "opencode":
                        registered = catalog["daodan"]["plugins"]["office"]["skills"]
                        self.assertIn(
                            (f"office:{skill}", relative),
                            {(item["id"], item["file"]) for item in registered},
                        )
                    elif host == "pi":
                        directory = f"exports/pi/plugins/office/skills/{skill}"
                        self.assertTrue(any(
                            fnmatch.fnmatchcase(directory, pattern.removeprefix("./") + "/*")
                            for pattern in catalog["pi"]["skills"]
                        ))
                    else:
                        self.assertIn(f"./skills/{skill}", catalog["plugins"][0]["skills"])

    def test_the_adapted_knowledge_survives_all_host_exports(self):
        for host, package in self.packages.items():
            for reference in DESIGN_REFERENCES:
                with self.subTest(host=host, reference=reference):
                    relative = Path("skills/design") / reference
                    source = _read(OFFICE / relative)
                    rendered = without_host_binding(self, _read(package / relative), host)
                    root_note = self.adapters[host].layout.get("plugin_root_note")
                    if root_note and "${CLAUDE_PLUGIN_ROOT}" in source:
                        block = f"> {root_note}\n\n"
                        self.assertEqual(rendered.count(block), 1)
                        rendered = rendered.replace(block, "", 1)
                    expected = source.replace(
                        "${CLAUDE_PLUGIN_ROOT}",
                        self.adapters[host].layout.get("plugin_root_reference", "${CLAUDE_PLUGIN_ROOT}"),
                    )
                    self.assertEqual(canonical_markdown(rendered), canonical_markdown(expected))
                    self.assertNotRegex(rendered, r"(?i)`agentit:[^`]+`")

    def test_presentation_and_word_methods_load_the_local_pair(self):
        for host, package in self.packages.items():
            for relative in ("skills/pptx/SKILL.md", "skills/docx/SKILL.md"):
                with self.subTest(host=host, method=relative):
                    self.assert_skill_loads(_read(package / relative))
            with self.subTest(host=host, method="document entry"):
                entry = loaded_instruction_text(self, package / DOCUMENT_PATHS[host], host)
                self.assertIn("`office:docx`", entry)
                self.assertIn("`office:design`", entry)

    def test_isolated_designer_and_reviewer_can_read_the_local_pair(self):
        for host, package in self.packages.items():
            for role in ("presentation-designer", "presentation-reviewer"):
                with self.subTest(host=host, role=role):
                    body = _read(package / ROLE_PATHS[host].format(role=role))
                    self.assert_skill_loads(body)
                    self.assertIn("office:pptx", body)

    def test_pair_references_resolve_without_an_upstream_checkout(self):
        editorial = _read(OFFICE / "skills/design/references/editorial-design.md")
        typography = _read(OFFICE / "skills/design/references/typography.md")
        self.assertIn("`typography.md`", editorial)
        self.assertIn("`editorial-design.md`", typography)
        for host, package in self.packages.items():
            for relative in (LICENSE, NOTICE, THEME_NOTICE, THEME_LICENSE, *MIT_NOTICES):
                with self.subTest(host=host, reference=relative):
                    self.assertTrue((package / relative).is_file())
            for reference in ("SKILL.md", *DESIGN_REFERENCES):
                with self.subTest(host=host, reference=reference):
                    text = _read(package / "skills/design" / reference)
                    self.assertNotIn("plugins/office/", text)
                    if host != "claude":
                        self.assertNotIn("CLAUDE_PLUGIN_ROOT", text)

    def test_apache_license_and_modified_source_notice_travel_with_the_guides(self):
        license_text = _read(OFFICE / LICENSE)
        self.assertIn("Apache License", license_text)
        self.assertIn("Version 2.0, January 2004", license_text)
        self.assertIn("END OF TERMS AND CONDITIONS", license_text)
        notice = _read(OFFICE / NOTICE)
        self.assertIn("marcmarti9/agentit", notice)
        self.assertRegex(notice, r"\b[0-9a-f]{40}\b")
        self.assertRegex(notice, r"(?i)adapt|modif")
        skill = _read(OFFICE / "skills/design/SKILL.md")
        self.assertRegex(skill.split("\n---\n", 1)[0], r"(?m)^license: Apache-2\.0$")
        for reference in DESIGN_REFERENCES:
            self.assertIn(reference.removeprefix("references/"), notice)
            self.assertIn("marcmarti9/agentit", _read(OFFICE / "skills/design" / reference))
        for relative, owner in MIT_NOTICES.items():
            text = _read(OFFICE / relative)
            with self.subTest(notice=relative):
                self.assertIn(owner, text)
                self.assertIn("Permission is hereby granted, free of charge", text)
                self.assertIn("THE SOFTWARE IS PROVIDED", text)
        for host, package in self.packages.items():
            with self.subTest(host=host):
                self.assertEqual((package / LICENSE).read_bytes(), (OFFICE / LICENSE).read_bytes())
                exported_notice = without_host_binding(self, _read(package / NOTICE), host)
                self.assertEqual(canonical_markdown(exported_notice), canonical_markdown(notice))
                for relative in MIT_NOTICES:
                    self.assertEqual((package / relative).read_bytes(), (OFFICE / relative).read_bytes())

    def test_design_guidance_retains_native_format_and_harness_image_boundaries(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                guides = "\n".join(_read(package / "skills/design" / reference) for reference in DESIGN_REFERENCES)
                for concept in (r"\bDOCX\b", r"\bPPTX\b", r"(?i)editab", r"(?i)render", r"(?i)harness"):
                    self.assertRegex(guides, concept)
                docx = _read(package / "skills/docx/SKILL.md")
                self.assertIn("image-tools.md", docx)
                self.assertRegex(docx, r"(?i)native.*(?:style|paragraph)")
                self.assertRegex(docx, r"(?i)render.*saved DOCX")
                presentation = _read(package / "skills/pptx/SKILL.md")
                self.assertIn("pptx-compatibility.md", presentation)
                self.assertIn("references/image-tools.md", presentation)
                self.assertTrue((package / "skills/pptx/references/image-tools.md").is_file())

    def test_one_direction_and_an_ad_hoc_palette_replace_theme_presets(self):
        self.assertFalse((OFFICE / "skills/theme-factory").exists())
        directions = _read(OFFICE / "skills/design/references/directions.md")
        rows = re.findall(r"^\| \*\*([A-T]) ", directions, re.M)
        self.assertEqual(rows, [chr(code) for code in range(ord("A"), ord("T") + 1)])
        self.assertNotIn("Q Pop", directions)
        self.assertRegex(directions, r"(?i)default seeds")
        for host, package in self.packages.items():
            with self.subTest(host=host):
                skill = _read(package / "skills/design/SKILL.md")
                for phrase in ("palette.py\" candidates", "palette_preview.py\"", "ask which number to use",
                               "from-image", "from-url", "from-css", "from-file", "default seeds",
                               "font_fetch.py\" install", "font_embed.py\" embed", "brand or template always wins"):
                    self.assertIn(phrase, skill)
                self.assertNotIn("office:theme-factory", skill)
                for relative in ("skills/docx/SKILL.md", "skills/pptx/SKILL.md",
                                 "skills/slidepoise/SKILL.md", "skills/deckcraft/SKILL.md", "skills/wordcraft/SKILL.md"):
                    text = _read(package / relative)
                    self.assertIn("`office:design`", text)
                    for stale in ("office:theme-factory", "office:editorial-design", "office:typography-and-layout"):
                        self.assertNotIn(stale, text)
                attribution = without_host_binding(self, _read(package / THEME_NOTICE), host)
                self.assertIn("anthropics/skills", attribution)
                self.assertRegex(attribution, r"\b[0-9a-f]{40}\b")
                self.assertIn("Apache", _read(package / THEME_LICENSE))

if __name__ == "__main__":
    unittest.main()
