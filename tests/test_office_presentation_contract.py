"""Office presentation ownership and dispatch contracts on actual host renders.

These tests verify generated instructions and capability gates, not installed
host execution or PowerPoint fidelity. Runtime tests belong to each engine.
"""

import json
import os
import re
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "scripts/daodan").is_dir()
)
for import_root in (REPO_ROOT, REPO_ROOT / "tests"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support
from scripts.daodan.catalogs import render_catalog
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from scripts.daodan.validate import validate_dependencies
from host_binding_assertions import canonical_markdown, loaded_instruction_text, without_host_binding


OFFICE = REPO_ROOT / "plugins/office"
ADAPTERS = REPO_ROOT / "adapters"
ROLES = ("presentation-designer", "presentation-reviewer")
ALL_ROLES = (*ROLES, "document-designer", "document-reviewer")
COMPATIBILITY_REFERENCE = Path("skills/pptx/references/pptx-compatibility.md")
DESIGN_LIBRARY_REFERENCE = Path("skills/pptx/references/design-library.md")
HARNESS_PATHS = {
    "claude": "commands/presentation.md",
    "copilot": "agents/presentation-coordinator.agent.md",
    "codex": "skills/presentation-workflow/SKILL.md",
    "pi": "prompts/office-presentation.md",
    "opencode": "commands/presentation.md",
}
ROLE_PATHS = {
    "claude": "agents/{role}.md",
    "copilot": "agents/{role}.agent.md",
    "codex": "roles/{role}.md",
    "pi": "skills/office-{role}/SKILL.md",
    "opencode": "agents/{role}.md",
}


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _temp_dir():
    """Keep temporary files on the repository drive so package paths resolve."""
    return str(REPO_ROOT) if os.name == "nt" else None


def _normalized(text):
    return " ".join(text.split())


def _frontmatter(text):
    if not text.startswith("---\n"):
        raise AssertionError("Missing frontmatter")
    return text.split("\n---\n", 1)[0]


class PresentationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = load_plugin(OFFICE)
        cls.workflow = next(item for item in cls.plugin.workflows if item.name == "presentation")
        cls.presentation_plugin = replace(cls.plugin, workflows=(cls.workflow,))
        cls.temporary = tempfile.TemporaryDirectory(dir=_temp_dir())
        cls.packages = {}
        cls.adapters = {}
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            package = Path(cls.temporary.name) / host / "office"
            render_plugin(cls.plugin, adapter, package, adapters_root=ADAPTERS)
            cls.adapters[host] = adapter
            cls.packages[host] = package

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def harness(self, host):
        return loaded_instruction_text(self, self.packages[host] / HARNESS_PATHS[host], host)

    def test_creative_roles_are_distinct_from_methods_and_both_engines_remain(self):
        components = self.plugin.components
        self.assertEqual(set(components.roles), set(ALL_ROLES))
        self.assertTrue({"pptx", "slidepoise", "deckcraft"} <= set(components.skills))
        self.assertFalse(set(components.skills) & set(components.roles))
        self.assertFalse(set(components.workflows) & set(components.roles))
        self.assertFalse(set(components.workflows) & set(components.skills))
        self.assertFalse(self.plugin.mcp_servers, "External DeckCraft is not a bundled server")

    def test_office_consults_no_external_design_provider(self):
        self.assertEqual(self.plugin.optional_dependencies, ())
        self.assertFalse(any(name.split("@", 1)[0] in {"impeccable", "taste-skill"}
                             for name in self.plugin.required_dependencies))
        for host, package in self.packages.items():
            with self.subTest(host=host):
                self.assertFalse((package / "skills/pptx/references/creative-providers.md").exists())
                method = _normalized(_read(package / "skills/pptx/SKILL.md"))
                self.assertIn("consult no external design provider", method)
                for role in ROLES:
                    body = _normalized(_read(package / ROLE_PATHS[host].format(role=role)))
                    self.assertIn("consult no external design provider", body)
                    self.assertNotRegex(body, r"`(?:impeccable|taste-skill):")

    def test_isolated_method_dispatch_is_serial_and_has_only_owned_roles(self):
        self.assertTrue(self.workflow.dispatch.isolated)
        self.assertFalse(self.workflow.dispatch.inline_workers)
        self.assertEqual(set(self.workflow.dispatch.roles), {f"office/{role}" for role in ROLES})
        self.assertTrue({"contexts.isolate", "roles.dispatch"} <= set(self.plugin.capabilities.required))
        self.assertTrue(all(phase.invoke is None for phase in self.workflow.phases))
        for host, adapter in self.adapters.items():
            with self.subTest(host=host):
                support = resolve_support(self.presentation_plugin, adapter)
                self.assertIn(support.state, {"native", "adapted"})
                self.assertEqual(support.workflow_strategies, (("presentation", "serial-isolated"),))
                harness = self.harness(host)
                self.assertIn("serial-isolated", harness)
                self.assertIn("**required**", harness)
                for role in ROLES:
                    self.assertIn(role, harness)

    def test_no_host_can_replace_required_isolation_with_shared_context(self):
        for host, adapter in self.adapters.items():
            with self.subTest(host=host):
                shared_only = replace(adapter, strategies=tuple(
                    replace(strategy, isolated=False) for strategy in adapter.strategies
                ))
                unavailable = resolve_support(self.presentation_plugin, shared_only)
                self.assertEqual(unavailable.state, "unsupported")
                self.assertEqual(unavailable.workflow_strategies, (("presentation", "none"),))

    def test_required_dispatch_tool_failure_is_not_hidden_by_an_available_strategy(self):
        for host, adapter in self.adapters.items():
            with self.subTest(host=host):
                bindings = dict(adapter.bindings)
                bindings.pop("roles.dispatch")
                unavailable = resolve_support(self.presentation_plugin, replace(adapter, bindings=bindings))
                self.assertEqual(unavailable.state, "unsupported")
                self.assertIn("roles.dispatch", unavailable.missing_capabilities)

    def test_method_dispatch_cannot_ship_without_its_declared_capability(self):
        weakened = replace(self.plugin, capabilities=replace(
            self.plugin.capabilities,
            required=tuple(item for item in self.plugin.capabilities.required if item != "roles.dispatch"),
        ))
        issues = validate_dependencies(weakened, {"office": weakened})
        self.assertIn("dispatch-without-capability", {issue.code for issue in issues})

    def test_host_role_bindings_resolve_real_owned_files_and_keep_model_inheritance(self):
        for host, package in self.packages.items():
            harness = self.harness(host)
            for role in ROLES:
                with self.subTest(host=host, role=role):
                    path = package / ROLE_PATHS[host].format(role=role)
                    self.assertTrue(path.is_file())
                    body = _read(path)
                    self.assertIn("office:pptx", body)
                    source_meta = _frontmatter(_read(OFFICE / "roles" / f"{role}.md"))
                    self.assertIn("model: inherit", source_meta)
                    self.assertNotRegex(source_meta, r"(?m)^tools:")
                    if host in {"codex", "pi"}:
                        self.assertIn(path.relative_to(package).as_posix(), harness)
                        self.assertIn("complete body verbatim", harness)
                    else:
                        self.assertIn(f"office:{role}", harness)
                    if host == "codex":
                        self.assertIn("not a\nregistered skill", body)
                    if host == "pi":
                        self.assertIn("disable-model-invocation: true", _frontmatter(body))
                    if host != "claude":
                        self.assertNotRegex(_frontmatter(body), r"(?m)^model:")

    def test_named_host_catalogs_register_roles_separately_from_skills(self):
        for host in ("claude", "copilot", "opencode"):
            with self.subTest(host=host):
                catalog = json.loads(render_catalog(
                    host, [self.plugin], "0.0.0", {"office": self.packages[host]},
                    layout=self.adapters[host].layout,
                ))
                if host == "opencode":
                    entry = catalog["daodan"]["plugins"]["office"]
                    agents = {item["id"] for item in entry["agents"]}
                    skills = {item["id"] for item in entry["skills"]}
                    self.assertEqual(agents, {f"office:{role}" for role in ALL_ROLES})
                    self.assertFalse(agents & skills)
                    for agent in entry["agents"]:
                        self.assertFalse(any(rule.get("effect") == "deny" for rule in agent["permissions"]))
                else:
                    entry = catalog["plugins"][0]
                    for role in ROLES:
                        self.assertIn("./" + ROLE_PATHS[host].format(role=role), entry["agents"])
                    self.assertIn("./skills/pptx", entry["skills"])
                    self.assertFalse(any("presentation-designer" in path or "presentation-reviewer" in path
                                         for path in entry["skills"]))

    def test_nested_presentation_contracts_survive_every_host_verbatim(self):
        for host, package in self.packages.items():
            for reference in (
                "design-library.md",
                "design-preview.md",
                "image-tools.md",
                "layout-patterns.md",
                "pptx-compatibility.md",
            ):
                with self.subTest(host=host, reference=reference):
                    relative = Path("skills/pptx/references") / reference
                    source = _read(OFFICE / relative)
                    rendered = without_host_binding(self, _read(package / relative), host)
                    self.assertEqual(canonical_markdown(rendered), canonical_markdown(source))
                    method = _read(package / "skills/pptx/SKILL.md")
                    self.assertIn(f"references/{reference}", method)

    def test_ppt_visual_sketches_live_in_the_patterns_with_one_slide_schema(self):
        relative = Path("skills/pptx/references/layout-patterns.md")
        license_relative = relative.with_name("LICENSE-ppt-visual-MIT.txt")
        source = _read(OFFICE / relative)
        license_text = _read(OFFICE / license_relative)
        self.assertFalse((relative.parent / "ppt-visual.md").exists())
        self.assertIn("claude-office-skills/skills", source)
        self.assertRegex(source, r"\b[0-9a-f]{40}\b")
        self.assertIn(license_relative.name, source)
        self.assertEqual(source.count("Sketch: `["), 9)
        self.assertIn("this catalog adds no second schema", source)
        self.assertIn("Copyright (c) 2026 Claude Office Skills Contributors", license_text)
        self.assertIn("Permission is hereby granted, free of charge", license_text)
        library = _read(OFFICE / "skills/pptx/references/design-library.md")
        self.assertNotIn("| Slide ID |", library)
        self.assertIn("single slide-object specification", library)
        compatibility = _read(OFFICE / "skills/pptx/references/pptx-compatibility.md")
        self.assertIn("do not introduce\na second construction schema", compatibility)
        self.assertIn("Stable slide ID from the deck plan", compatibility)
        for host, package in self.packages.items():
            with self.subTest(host=host):
                designer = _normalized(_read(package / ROLE_PATHS[host].format(role="presentation-designer")))
                self.assertIn("references/layout-patterns.md", designer)
                self.assertNotIn("ppt-visual.md", designer)
                self.assertIn("wireframe", designer)
                self.assertIn("native object placement", designer)
                reviewer = _normalized(_read(package / ROLE_PATHS[host].format(role="presentation-reviewer")))
                self.assertIn("references/layout-patterns.md", reviewer)
                self.assertIn("references/directions.md", reviewer)
                self.assertEqual((package / license_relative).read_bytes(), (OFFICE / license_relative).read_bytes())

    def test_pptx_constraints_reach_the_workflow_workers_and_both_engines(self):
        """Shipping a reference is insufficient unless each independent entry reads it."""
        consumers = (
            "skills/pptx/SKILL.md",
            "skills/slidepoise/SKILL.md",
            "skills/deckcraft/SKILL.md",
        )
        for host, package in self.packages.items():
            with self.subTest(host=host, consumer="workflow"):
                self.assertIn("pptx-compatibility.md", self.harness(host))
            for consumer in (*consumers, *(ROLE_PATHS[host].format(role=role) for role in ROLES)):
                with self.subTest(host=host, consumer=consumer):
                    text = _normalized(_read(package / consumer))
                    self.assertIn("pptx-compatibility.md", text)
            with self.subTest(host=host, consumer="contract"):
                self.assertTrue((package / COMPATIBILITY_REFERENCE).is_file())

    def test_pptx_feasibility_is_established_before_creative_direction(self):
        text = _normalized(_read(OFFICE / COMPATIBILITY_REFERENCE))
        for obligation in (
            "Apply this contract before design work, generating reference images",
            "fixed 16:9 canvas as the default",
            "Record the construction engine and version, intended viewing application",
            "Check the commands or reconstruction types needed for the proposed composition before accepting it",
            "Resolve font families and weights available to construction and target rendering",
            "Record any substitution and recheck line breaks",
            "Unsupported elements must be redesigned within the brief or reported before construction",
        ):
            with self.subTest(obligation=obligation):
                self.assertIn(obligation, text)

    def test_pptx_object_plan_preserves_editability_and_source_data(self):
        text = _normalized(_read(OFFICE / COMPATIBILITY_REFERENCE))
        for obligation in (
            "Use slide IDs and one declared coordinate unit and origin",
            "x/y position, width/height, margins or padding, alignment and stacking order",
            "Native text, shape, connector, table or chart; or a separate image asset with crop, dimensions, placement and provenance",
            "What must remain editable, including chart series/data, table cells and diagram labels",
            "Build native charts from the authoritative source data, preserving labels, units and series",
            "Do not flatten a complete slide, convert required text to outlines, or silently rasterize editable objects",
            "An image or SVG inside a PPTX is not proof of native object editability",
            "A change to requested editability needs the user's decision",
        ):
            with self.subTest(obligation=obligation):
                self.assertIn(obligation, text)

    def test_web_guidance_becomes_supported_static_slide_objects_before_generation(self):
        text = _normalized(_read(OFFICE / COMPATIBILITY_REFERENCE))
        for obligation in (
            "Translate web-inspired layout into this fixed slide specification before generation",
            "hover states, scroll effects and responsive breakpoints are not PowerPoint construction instructions",
            "Express their useful visual intent through fixed geometry and static compositions",
            "Treat animation as a separate, explicitly requested feature with verified support",
            "Use gradients, shadows, transparency and clipping only where the chosen engine and target renderer preserve them",
            "Inspect generated references for reconstructability",
            "There is no general HTML/CSS-to-PPTX converter in this integration",
            "Generated or edited images must use the exposed harness image tool",
            "An external image script, image-search utility or web workflow does not replace that obligation",
        ):
            with self.subTest(obligation=obligation):
                self.assertIn(obligation, text)

    def test_fidelity_claims_require_target_application_evidence(self):
        text = _normalized(_read(OFFICE / COMPATIBILITY_REFERENCE))
        for obligation in (
            "Render the actual saved candidate and compare every page",
            "Same-engine round-trip renders and object counts cannot prove cross-application fidelity or editability",
            "Report design-reference comparison, selected-engine preview and target-application verification as separate evidence",
            "To claim fidelity in Microsoft PowerPoint, open/render the actual candidate there and record the version and font environment",
            "report PowerPoint fidelity as unverified",
            "Do not promise pixel-perfect equivalence from a generated image, a browser preview, valid OOXML, unit tests or a DeckCraft render",
            "Never improve that score by sacrificing required native content",
        ):
            with self.subTest(obligation=obligation):
                self.assertIn(obligation, text)

    def test_image_contract_requires_real_tool_schema_artifacts_and_no_automatic_external_fallback(self):
        text = _normalized(_read(OFFICE / "skills/pptx/references/image-tools.md"))
        for obligation in (
            "Discover the actual tool name, input schema",
            "Only a context with the exposed tool may invoke it",
            "when that handoff is available",
            "block the dependent image step",
            "Do not use an API-key script, external image CLI, browser service or different model as an automatic fallback",
            "Verify the engine can consume the artifact",
            "do not substitute a whole-slide image",
        ):
            self.assertIn(obligation, text)
        self.assertNotRegex(text, r"\b(?:image_gen__imagegen|mcp__\w+|spawn_agent)\b")

    def test_design_library_routes_to_directions_and_patterns_with_density_caps(self):
        index = _normalized(_read(OFFICE / "skills/pptx/references/design-library.md"))
        directions = _normalized(_read(OFFICE / "skills/design/references/directions.md"))
        patterns = _normalized(_read(OFFICE / "skills/pptx/references/layout-patterns.md"))
        for obligation in (
            "at most 4 cards or text columns per slide",
            "at most 7 nodes in a process or architecture",
            "never below `13 pt`",
            "one visual direction",
            "one pattern per slide",
        ):
            with self.subTest(obligation=obligation):
                self.assertIn(obligation, index)
        self.assertIn("references/directions.md", index)
        self.assertIn("layout-patterns.md", index)
        for direction in ("A Executive Boardroom", "H Brand-Led Custom", "P Compliance Formal"):
            with self.subTest(direction=direction):
                self.assertIn(direction, directions)
        self.assertIn("Direction pitfalls to avoid", directions)
        for pattern in (
            "**Cover**",
            "**Executive summary**",
            "**Chart and insight**",
            "**Comparison matrix**",
            "**Timeline and roadmap**",
            "**Architecture and system map**",
            "**Next steps and decision request**",
        ):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, patterns)
        self.assertIn("A pattern is a construction plan, not a picture", patterns)

    def test_review_severity_and_bounded_repair_loop_survive_every_host(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                reviewer = _normalized(_read(package / ROLE_PATHS[host].format(role="presentation-reviewer")))
                for obligation in (
                    "**Blocking**",
                    "**Advisory**",
                    "source text is lost outside the approved cuts",
                    "report it once as a deck-level defect",
                    "advisory defects are listed, never blocking on their own",
                ):
                    self.assertIn(obligation, reviewer)
                method = _normalized(_read(package / "skills/pptx/SKILL.md"))
                self.assertIn("resolve every blocking finding", method)
                self.assertIn("Fix a deck-level defect at its source", method)
                self.assertIn("Run at most three review rounds", method)

    def test_text_coverage_guards_derived_and_shortened_decks_on_every_host(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                method = _normalized(_read(package / "skills/pptx/SKILL.md"))
                self.assertIn("run `pptx_inspect.py coverage`", method)
                self.assertIn("never cut content the user did not approve", method)
                deckcraft = _normalized(_read(package / "skills/deckcraft/SKILL.md"))
                self.assertIn("pptx_inspect.py\" coverage SOURCE.pptx CANDIDATE.pptx --cuts cuts.json", deckcraft)
                reviewer = _normalized(_read(package / ROLE_PATHS[host].format(role="presentation-reviewer")))
                self.assertIn("every `missing` item is lost source text", reviewer)
        intake = _normalized(_read(OFFICE / "skills/intake/SKILL.md"))
        self.assertIn("record the approved cuts", intake)

    def test_argument_mode_is_chosen_recorded_and_reviewed(self):
        library = _normalized(_read(OFFICE / "skills/pptx/references/design-library.md"))
        for mode in ("Pyramid", "Narrative", "Instructional", "Showcase", "Briefing"):
            with self.subTest(mode=mode):
                self.assertIn(f"| {mode} |", library)
        self.assertIn("Headline set by the argument mode", library)
        self.assertIn("one argument mode", library)
        for host, package in self.packages.items():
            with self.subTest(host=host):
                method = _normalized(_read(package / "skills/pptx/SKILL.md"))
                self.assertIn("argument mode", method)
                for role in ROLES:
                    body = _normalized(_read(package / ROLE_PATHS[host].format(role=role)))
                    self.assertIn("argument mode", body)

    def test_single_writer_and_independent_candidate_review_survive_all_host_bodies(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                method = _normalized(_read(package / "skills/pptx/SKILL.md"))
                self.assertIn("coordinator is the sole deck writer and image-tool caller", method)
                self.assertIn("They do not launch further workers", method)
                self.assertIn("exact candidate path and SHA-256", method)
                self.assertIn("obtain an updated review tied to the new candidate", method)
                reviewer = _normalized(_read(package / ROLE_PATHS[host].format(role="presentation-reviewer")))
                self.assertIn("Review every page", reviewer)
                self.assertIn("Missing render or visual access blocks visual approval", reviewer)
                self.assertIn("Do not edit the deck, generate images or dispatch workers", reviewer)
                designer = _normalized(_read(package / ROLE_PATHS[host].format(role="presentation-designer")))
                self.assertIn("Do not generate images, edit the deck, dispatch agents", designer)
                self.assertIn("not the coordinator's dispatch procedure", designer)

    def test_both_engine_skills_keep_their_helpers_and_never_start_a_second_coordinator(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                slidepoise = _normalized(_read(package / "skills/slidepoise/SKILL.md"))
                deckcraft = _normalized(_read(package / "skills/deckcraft/SKILL.md"))
                self.assertIn("do not start a second coordinator", slidepoise)
                self.assertIn("without starting another coordinator", deckcraft)
                self.assertIn("not replace that creative reconstruction workflow", deckcraft)
                self.assertIn("do not round-trip every SlidePoise result", _normalized(self.harness(host)))
                for relative in (
                    "skills/slidepoise/scripts/slidepoise_bridge.py",
                    "skills/deckcraft/scripts/deckcraft_bridge.py",
                    "skills/deckcraft/scripts/pptx_inspect.py",
                    "skills/xlsx/scripts/xlsx_inspect.py",
                ):
                    self.assertTrue((package / relative).is_file(), relative)

    def test_copilot_image_access_is_not_invented_by_the_coordinator_allowlist(self):
        header = _frontmatter(self.harness("copilot"))
        tool_line = next(line for line in header.splitlines() if line.startswith("tools:"))
        actual = set(re.findall(r"'([^']+)'", tool_line))
        self.assertEqual(actual, {"agent", "edit", "fetch", "runCommands", "search"})
        contract = _normalized(_read(self.packages["copilot"] / "skills/pptx/references/image-tools.md"))
        self.assertIn("If the coordinator lacks the tool", contract)
        self.assertIn("otherwise record the missing capability", contract)
        self.assertIn("Do not assume another agent inherits an unavailable tool", contract)


if __name__ == "__main__":
    unittest.main()
