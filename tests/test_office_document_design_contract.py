"""Document design has an owned role and an executable host handoff.

These tests inspect real compiler output and capability failures. They do not
establish installed-host execution or saved Word pagination and visual fidelity.
"""

import fnmatch
import json
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
for import_root in (REPO_ROOT, REPO_ROOT / "tests"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support
from scripts.daodan.catalogs import render_catalog
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from host_binding_assertions import canonical_markdown, loaded_instruction_text, without_host_binding


OFFICE = REPO_ROOT / "plugins/office"
ADAPTERS = REPO_ROOT / "adapters"
ROLE = "document-designer"
DESIGN_REFERENCE = Path("skills/docx/references/document-design.md")
ROLE_PATHS = {
    "claude": "agents/document-designer.md",
    "copilot": "agents/document-designer.agent.md",
    "codex": "roles/document-designer.md",
    "pi": "skills/office-document-designer/SKILL.md",
    "opencode": "agents/document-designer.md",
}
ENTRY_PATHS = {
    "claude": "commands/document.md",
    "copilot": "agents/document-coordinator.agent.md",
    "codex": "skills/document-workflow/SKILL.md",
    "pi": "prompts/office-document.md",
    "opencode": "commands/document.md",
}


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _normalized(text):
    return " ".join(text.split())


def _frontmatter(text):
    if not text.startswith("---\n"):
        raise AssertionError("Missing frontmatter")
    return text.split("\n---\n", 1)[0]


class DocumentDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = load_plugin(OFFICE)
        cls.workflow = next(item for item in cls.plugin.workflows if item.name == "document")
        cls.document_plugin = replace(cls.plugin, workflows=(cls.workflow,))
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

    def entry(self, host):
        return loaded_instruction_text(self, self.packages[host] / ENTRY_PATHS[host], host)

    def test_word_and_powerpoint_design_have_distinct_owned_roles(self):
        components = self.plugin.components
        self.assertEqual(
            set(components.roles),
            {ROLE, "presentation-designer", "presentation-reviewer"},
        )
        self.assertNotIn(ROLE, components.skills)
        self.assertNotIn(ROLE, components.workflows)
        self.assertIn("docx", components.skills)
        self.assertIn("presentation-design", components.skills)
        self.assertFalse(self.plugin.mcp_servers)

    def test_word_dispatch_is_isolated_and_only_owns_the_document_designer(self):
        dispatch = self.workflow.dispatch
        self.assertEqual(dispatch.roles, (f"office/{ROLE}",))
        self.assertTrue(dispatch.isolated)
        self.assertFalse(dispatch.inline_workers)
        self.assertTrue(all(phase.invoke is None for phase in self.workflow.phases))
        for host, adapter in self.adapters.items():
            with self.subTest(host=host):
                support = resolve_support(self.document_plugin, adapter)
                self.assertIn(support.state, {"native", "adapted"})
                self.assertEqual(len(support.workflow_strategies), 1)
                workflow_name, strategy_name = support.workflow_strategies[0]
                self.assertEqual(workflow_name, "document")
                strategy = next(item for item in adapter.strategies if item.name == strategy_name)
                self.assertTrue(strategy.isolated)
                entry = self.entry(host)
                self.assertIn(strategy_name, entry)
                self.assertIn("**required**", entry)
                self.assertIn(ROLE, entry)

    def test_word_design_cannot_silently_share_context_when_isolation_is_missing(self):
        for host, adapter in self.adapters.items():
            with self.subTest(host=host):
                shared_only = replace(adapter, strategies=tuple(
                    replace(strategy, isolated=False) for strategy in adapter.strategies
                ))
                unsupported = resolve_support(self.document_plugin, shared_only)
                self.assertEqual(unsupported.state, "unsupported")
                self.assertEqual(unsupported.workflow_strategies, (("document", "none"),))

    def test_word_design_requires_an_actual_dispatch_capability(self):
        for host, adapter in self.adapters.items():
            with self.subTest(host=host):
                bindings = dict(adapter.bindings)
                bindings.pop("roles.dispatch")
                unsupported = resolve_support(self.document_plugin, replace(adapter, bindings=bindings))
                self.assertEqual(unsupported.state, "unsupported")
                self.assertIn("roles.dispatch", unsupported.missing_capabilities)

    def test_pi_checks_worker_availability_only_when_the_document_task_dispatches_one(self):
        harness = _normalized(self.entry("pi").split("## Execution harness", 1)[1].split("## Method", 1)[0])
        self.assertRegex(harness, r"(?i)(?:no (?:dispatched |isolated )?workers?|does not require.*worker).*?(?:continue|proceed|run)")
        self.assertRegex(harness, r"(?i)(?:if|when|only).*?(?:requires|needs|selected|needed|dispatch).*?(?:worker|delivery)")
        self.assertIn("**`required`**: stop", harness)
        self.assertIn("serially in this one context is the loss of isolation", harness)
        self.assertIn("pi install npm:", harness)

    def test_every_host_binds_the_real_role_and_preserves_inherited_model_and_tools(self):
        source_meta = _frontmatter(_read(OFFICE / "roles/document-designer.md"))
        self.assertIn("model: inherit", source_meta)
        self.assertNotRegex(source_meta, r"(?m)^tools:")
        for host, package in self.packages.items():
            with self.subTest(host=host):
                relative = ROLE_PATHS[host]
                body = _read(package / relative)
                for skill in ("docx", "design"):
                    self.assertIn(f"`office:{skill}`", body)
                self.assertIn("document-design.md", body)
                if host in {"codex", "pi"}:
                    self.assertIn(relative, self.entry(host))
                    self.assertIn("complete body verbatim", self.entry(host))
                else:
                    self.assertIn(f"office:{ROLE}", self.entry(host))
                if host == "codex":
                    self.assertIn("not a\nregistered skill", body)
                if host == "pi":
                    self.assertIn("disable-model-invocation: true", _frontmatter(body))
                if host != "claude":
                    self.assertNotRegex(_frontmatter(body), r"(?m)^model:")

    def test_named_host_catalogs_register_the_word_role_as_an_agent(self):
        for host in ("claude", "copilot", "opencode"):
            with self.subTest(host=host):
                catalog = json.loads(render_catalog(
                    host, [self.plugin], "0.0.0", {"office": self.packages[host]},
                    layout=self.adapters[host].layout,
                ))
                if host == "opencode":
                    entry = catalog["daodan"]["plugins"]["office"]
                    self.assertIn(
                        (f"office:{ROLE}", ROLE_PATHS[host]),
                        {(agent["id"], agent["file"]) for agent in entry["agents"]},
                    )
                    self.assertNotIn(f"office:{ROLE}", {skill["id"] for skill in entry["skills"]})
                else:
                    entry = catalog["plugins"][0]
                    self.assertIn("./" + ROLE_PATHS[host], entry["agents"])
                    self.assertFalse(any(ROLE in path for path in entry["skills"]))

    def test_document_layout_reference_is_reachable_and_shipped_to_every_host(self):
        source = _read(OFFICE / DESIGN_REFERENCE)
        for host, package in self.packages.items():
            with self.subTest(host=host):
                exported = without_host_binding(self, _read(package / DESIGN_REFERENCE), host)
                self.assertEqual(canonical_markdown(exported), canonical_markdown(source))
                self.assertIn("references/document-design.md", _read(package / "skills/docx/SKILL.md"))
                self.assertIn("document-designer", self.entry(host))
                self.assertNotIn("plugins/office/", exported)

    def test_document_design_includes_native_page_patterns_and_a_construction_handoff(self):
        text = _normalized(_read(OFFICE / DESIGN_REFERENCE))
        for concept in (
            r"(?i)\bpage\b.*\b(?:size|geometry)\b",
            r"(?i)\bmargins?\b",
            r"(?i)\bsections?\b",
            r"(?i)\bstyles?\b",
            r"(?i)\btables?\b",
            r"(?i)\bcaptions?\b",
            r"(?i)\bheaders?\b",
            r"(?i)\bfooters?\b",
            r"(?i)\b(?:patterns?|templates?)\b",
            r"(?i)\beditable\b",
            r"(?i)\bnative\b",
        ):
            with self.subTest(concept=concept):
                self.assertRegex(text, concept)

    def test_both_format_designers_consume_one_coordinator_supplied_design_record(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                design = _normalized(_read(package / "skills/design/SKILL.md"))
                self.assertIn("share one direction, one palette and one pairing", design)
                for relative in ("skills/docx/SKILL.md", "skills/presentation-design/SKILL.md"):
                    method = _normalized(_read(package / relative))
                    self.assertIn("`office:design`", method)
                    self.assertIn("both format designers consume the same record", method)
                for relative in (
                    ROLE_PATHS[host],
                    ROLE_PATHS[host].replace("document-designer", "presentation-designer"),
                ):
                    role = _normalized(_read(package / relative))
                    self.assertIn("`office:design`", role)
                    self.assertIn("Do not independently replace it", role)

    def test_word_layout_ideas_are_attributed_without_claiming_a_copied_source_port(self):
        text = _normalized(_read(OFFICE / DESIGN_REFERENCE))
        self.assertIn("tivojn/Office", text)
        self.assertRegex(text, r"\b[0-9a-f]{40}\b")
        self.assertRegex(text, r"(?i)original Office guidance")
        self.assertRegex(text, r"(?i)no complete license/copyright text")
        self.assertRegex(text, r"(?i)no upstream wording.*redistributed")
        self.assertRegex(text, r"(?i)not a copied-source sync target")

    def test_worker_delivery_is_bounded_and_missing_reports_cannot_complete_the_design(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                role = _normalized(_read(package / ROLE_PATHS[host]))
                method = _normalized(_read(package / "skills/docx/SKILL.md"))
                self.assertRegex(role, r"(?i)write only.*assigned.*design report")
                self.assertRegex(role, r"(?i)do not.*(?:edit|write|modify).*\b(?:DOCX|document)\b")
                self.assertRegex(role, r"(?i)do not.*generate images")
                self.assertRegex(role, r"(?i)do not.*dispatch")
                self.assertRegex(method, r"(?i)missing.*(?:partial|empty)|(?:partial|empty).*missing")
                self.assertRegex(method, r"(?i)(?:resume|retry|recover|unresolved|incomplete|block|unfulfilled)")
                self.assertRegex(method, r"(?i)design report")

    def test_creative_dispatch_keeps_read_only_and_narrow_document_requests_scoped(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                method = _normalized(_read(package / "skills/docx/SKILL.md"))
                self.assertIn("document-designer", method)
                self.assertRegex(method, r"(?i)(?:new document|new documents|creation|substantial|redesign)")
                self.assertRegex(method, r"(?i)read-only")
                self.assertRegex(method, r"(?i)(?:narrow|targeted|local).*edit|edit.*(?:narrow|targeted|local)")
                self.assertIn("image-tools.md", method)

    def test_saved_document_rendering_is_separate_from_the_design_report(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                method = _normalized(_read(package / "skills/docx/SKILL.md"))
                role = _normalized(_read(package / ROLE_PATHS[host]))
                self.assertRegex(method, r"(?i)render.*(?:actual|saved).*DOCX|(?:actual|saved).*DOCX.*render")
                self.assertRegex(method, r"(?i)(?:page|pagination)")
                self.assertRegex(role, r"(?i)(?:does not|do not|not|unverified).*(?:proof|verif|render|fidelity)")

    def test_document_production_consumes_wordcraft_and_keeps_native_file_verification(self):
        self.assertIn("wordcraft", self.plugin.components.skills)
        self.assertNotIn("wordcraft", self.plugin.components.roles)
        for host, package in self.packages.items():
            with self.subTest(host=host):
                self.assertIn("`office:wordcraft`", self.entry(host))
                self.assertIn("`office:wordcraft`", _read(package / "skills/docx/SKILL.md"))
                production = _normalized(_read(package / "skills/wordcraft/SKILL.md"))
                self.assertIn("references/runtime.md", production)
                self.assertRegex(production, r"(?i)accepted document design report")
                self.assertRegex(production, r"(?i)native.*(?:paragraph|style|table)")
                self.assertRegex(production, r"(?i)save a no-edit round-trip.*separate candidate")
                self.assertRegex(production, r"(?i)reopen.*saved candidate")
                self.assertRegex(production, r"(?i)render actual saved DOCX pages")
                self.assertRegex(production, r"(?i)missing runtime blocks dependent production")
                self.assertRegex(production, r"(?i)does not replace the harness image tool")

    def test_wordcraft_runtime_reference_and_registration_ship_on_all_five_hosts(self):
        relative = Path("skills/wordcraft/references/runtime.md")
        source = _read(OFFICE / relative)
        self.assertIn("storytold/wordcraft", source)
        self.assertIn("--version", source)
        self.assertIn("run --help", source)
        self.assertRegex(_normalized(source), r"(?i)do not automatically upgrade")
        for host, package in self.packages.items():
            with self.subTest(host=host):
                self.assertTrue((package / "skills/wordcraft/SKILL.md").is_file())
                exported = without_host_binding(self, _read(package / relative), host)
                self.assertEqual(canonical_markdown(exported), canonical_markdown(source))
                catalog = json.loads(render_catalog(
                    host, [self.plugin], "0.0.0", {"office": package},
                    layout=self.adapters[host].layout,
                ))
                if host == "opencode":
                    self.assertIn(
                        ("office:wordcraft", "skills/wordcraft/SKILL.md"),
                        {(skill["id"], skill["file"])
                         for skill in catalog["daodan"]["plugins"]["office"]["skills"]},
                    )
                elif host == "pi":
                    directory = "exports/pi/plugins/office/skills/wordcraft"
                    self.assertTrue(any(
                        fnmatch.fnmatchcase(directory, pattern.removeprefix("./") + "/*")
                        for pattern in catalog["pi"]["skills"]
                    ))
                else:
                    self.assertIn("./skills/wordcraft", catalog["plugins"][0]["skills"])


if __name__ == "__main__":
    unittest.main()
