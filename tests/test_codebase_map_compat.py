"""Codebase Map exports and historical report compatibility after X-ray retirement."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402
from scripts.daodan.templates import render_path  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY, validate_plugins  # noqa: E402
from host_binding_assertions import canonical_markdown, without_host_binding  # noqa: E402


ROLES = (
    "partition-behavior-worker",
    "partition-quality-worker",
    "partition-structure-worker",
    "partition-synthesizer",
    "semantic-interconnect-mapper",
)
WORKFLOWS = ("analyze", "team-analyze")
ADAPTERS = REPO_ROOT / "adapters"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class CodebaseMapExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = {
            path.parent.name: load_plugin(path.parent)
            for path in sorted((REPO_ROOT / "plugins").glob("*/plugin.toml"))
        }
        cls.canonical = cls.registry["codebase-map"]
        cls.temp = tempfile.TemporaryDirectory(prefix="daodan-map-compat-")
        cls.packages = {}
        cls.adapters = {host: load_adapter(ADAPTERS, host) for host in HOSTS}
        for host, adapter in cls.adapters.items():
            for plugin in (cls.canonical, cls.registry["abstraction-architect"],
                           cls.registry["project-lifecycle"], cls.registry["project-knowledge"],
                           cls.registry["senior-review"]):
                package = Path(cls.temp.name) / host / plugin.name
                render_plugin(
                    plugin, adapter, package, adapters_root=ADAPTERS,
                    plugin_registry=cls.registry,
                )
                cls.packages[(host, plugin.name)] = package

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def package(self, host: str, plugin: str) -> Path:
        return self.packages[(host, plugin)]

    def component(self, host: str, plugin: str, kind: str, name: str) -> Path:
        variables = {"plugin": plugin, "skill": name, "workflow": name, "role": name}
        return self.package(host, plugin) / render_path(self.adapters[host].layout[kind], variables)

    def adapt_placeholders(self, host: str, text: str) -> str:
        layout = self.adapters[host].layout
        text = text.replace("${CLAUDE_PLUGIN_ROOT}", layout["plugin_root_reference"])
        return re.sub(r"\$ARGUMENTS\b", lambda _: layout["arguments_reference"], text)

    def assert_shared_resource(self, host: str, resource: str) -> str:
        relative = Path("skills/map-method/references") / resource
        source = read(self.canonical.root / relative)
        rendered = read(self.package(host, "codebase-map") / relative)
        expected = self.adapt_placeholders(host, source)
        layout = self.adapters[host].layout
        notes = []
        for reference, note in (("plugin_root_reference", "plugin_root_note"),
                                ("arguments_reference", "arguments_note")):
            if layout.get(note) and layout[reference] in expected:
                notes.append(f"> {layout[note]}\n")
        if notes:
            expected = "".join(notes) + "\n" + expected
        self.assertEqual(canonical_markdown(without_host_binding(self, rendered, host)),
                         canonical_markdown(expected), f"{host}: incomplete shared resource {resource}")
        return rendered

    def test_retired_plugin_has_no_kernel_or_host_registration(self):
        self.assertFalse("codebase-xray" in self.registry)
        self.assertFalse((REPO_ROOT / "plugins/codebase-xray").exists())
        catalogs = {
            "claude": ".claude-plugin/marketplace.json",
            "copilot": ".github/plugin/marketplace.json",
            "codex": ".agents/plugins/marketplace.json",
            "pi": "package.json",
            "opencode": "exports/opencode/package.json",
        }
        for host, relative in catalogs.items():
            with self.subTest(host=host):
                self.assertFalse((REPO_ROOT / "exports" / host / "plugins/codebase-xray").exists())
                catalog = read(REPO_ROOT / relative)
                self.assertNotIn("codebase-xray", catalog)
                if host == "pi":
                    document = json.loads(catalog)
                    self.assertIn("./exports/pi/plugins/*/skills", document["pi"]["skills"])
                    self.assertIn("./exports/pi/plugins/*/prompts", document["pi"]["prompts"])
                    self.assertTrue((REPO_ROOT / "exports/pi/plugins/codebase-map").is_dir())
                else:
                    self.assertIn("codebase-map", catalog)
        issues = validate_plugins(tuple(self.registry.values()), CAPABILITY_REGISTRY)
        self.assertEqual(issues, [], "\n".join(str(issue) for issue in issues))

    def test_no_operational_body_loads_or_dispatches_retired_identities(self):
        retired = re.compile(r"(?:(?<![.\w-])/?codebase-xray[:/]|xray-method)")
        for root in (REPO_ROOT / "plugins", REPO_ROOT / "exports"):
            for path in root.rglob("*.md"):
                with self.subTest(path=path):
                    self.assertIsNone(retired.search(read(path)), "Retired plugin identity is executable")
        for plugin in self.registry.values():
            self.assertNotIn("codebase-xray", plugin.required_dependencies)

    def test_shared_sources_keep_the_complete_canonical_execution(self):
        references = self.canonical.root / "skills/map-method/references"
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                source = read(references / f"entry-{workflow}.md")
                wrapper = read(self.canonical.root / "workflows" / f"{workflow}.md")
                self.assertFalse(source.startswith("---\n"))
                self.assertIn("## Method loads", source)
                self.assertIn("in this same coordinator context", wrapper)
                self.assertNotIn("## Pre-flight", wrapper)
                if workflow == "analyze":
                    for section in ("## Coordinator boundary", "## Isolated analysis", "## Publish and completion"):
                        self.assertIn(section, source)
                        self.assertNotIn(section, wrapper)
                    self.assertIn("codebase-map:map-analyst", source)
                else:
                    self.assertIn("## CRITICAL RULES", source)
        for role in ROLES:
            with self.subTest(role=role):
                source = read(references / f"role-{role}.md")
                wrapper = read(self.canonical.root / "roles" / f"{role}.md")
                self.assertFalse(source.startswith("---\n"))
                self.assertIn("## OWNERSHIP CONTRACT" if role != "semantic-interconnect-mapper"
                              else "## PRIME DIRECTIVES", source)
                self.assertIn("in this same worker context", wrapper)

    def test_all_five_hosts_ship_complete_canonical_entries_and_loaded_resources(self):
        for host in HOSTS:
            for workflow in WORKFLOWS:
                with self.subTest(host=host, workflow=workflow):
                    resource = f"entry-{workflow}.md"
                    shared = self.assert_shared_resource(host, resource)
                    self.assertIn("## Coordinator boundary" if workflow == "analyze"
                                  else "## CRITICAL RULES", shared)
                    wrapper = read(self.component(host, "codebase-map", "workflows", workflow))
                    if host == "copilot":
                        self.assertIn(f"codebase-map:{workflow}-coordinator", wrapper)
                        wrapper = read(self.package(host, "codebase-map") /
                                       f"agents/{workflow}-coordinator.agent.md")
                    self.assertIn("## Execution harness", wrapper)
                    self.assertIn(resource, wrapper)
                    self.assertIn("## Method loads", wrapper)
                    self.assertIn("same coordinator context", wrapper)
                    source = read(self.canonical.root / "workflows" / f"{workflow}.md")
                    method = source.split("\n---\n", 1)[1].lstrip("\n")
                    self.assertEqual(canonical_markdown(wrapper.split("\n## Method\n\n", 1)[1]),
                                     canonical_markdown(self.adapt_placeholders(host, method)))
                    if workflow == "analyze":
                        self.assertIn("`analysis`: one `map-analyst` in an isolated context", wrapper)
                        self.assertIn("`publish`: runs in the orchestrating context; needs `analysis`", wrapper)
            for role in ROLES:
                with self.subTest(host=host, role=role):
                    resource = f"role-{role}.md"
                    self.assert_shared_resource(host, resource)
                    wrapper = read(self.component(host, "codebase-map", "roles", role))
                    self.assertIn(resource, wrapper)
                    self.assertIn("same worker context", wrapper)
            policy = tomllib.loads(read(self.package(host, "codebase-map") / "policies/write-confinement.toml"))
            self.assertEqual(policy["migration"]["legacy_root"], ".codebase-xray")
            self.assertTrue(policy["migration"]["preserve_evidence_bytes"])
            self.assertTrue(policy["migration"]["require_idle_legacy_runs"])
            method = self.component(host, "codebase-map", "skills", "map-method").parent
            self.assertTrue((method / "scripts/migrate_root.py").is_file())

    def test_abstraction_worker_only_resolves_after_coordinator_migration_on_all_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = " ".join(read(self.component(
                    host, "abstraction-architect", "roles", "abstraction-architect-agent",
                )).split())
                self.assertIn("coordinator must complete root migration before dispatching", text)
                self.assertIn("use only the provider's `migrate_root.py resolve`", text)
                self.assertIn("performs no root migration", text)
                self.assertIn("never writes the legacy store", text)
                self.assertIn("still selects `.codebase-xray`, stop", text)
                self.assertIn("Edit nothing except `report_path`", text)
                self.assertNotIn("and apply its `references/migration.md`", text)
                census = read(self.package(host, "abstraction-architect") /
                              "skills/abstraction-architect/references/concept-census.md")
                self.assertIn("Read the supplied bound run's phase files", census)
                self.assertIn("the root mirror is not this input", census)
                self.assertNotIn("## Existing analysis compatibility", census)
                self.assertNotIn("references/migration.md", census)

    def test_handover_preflight_exception_keeps_worker_and_content_limits_on_all_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = " ".join(read(self.component(
                    host, "project-lifecycle", "skills", "handover-method",
                )).split())
                self.assertIn("bounded coordinator preflight exception", text)
                self.assertIn("move an idle legacy archive intact", text)
                self.assertIn("write only the helper's bound relocation metadata", text)
                self.assertIn("Workers do not perform this migration", text)
                self.assertIn("grants no analysis run, content edits or generic filesystem move", text)
                self.assertIn("Application files, tests, durable instructions, README and project guides", text)


    def test_shared_worker_units_and_readonly_coordinators_keep_migration_ownership_on_all_hosts(self):
        worker_units = {
            "project-knowledge": "skills/project-knowledge/references/preparation.md",
            "senior-review": "skills/review-quality-gates/SKILL.md",
        }
        readonly_units = {
            "project-knowledge": ["skills/project-knowledge/SKILL.md"],
            "senior-review": ["skills/review-method/SKILL.md", "skills/review-preparation/SKILL.md"],
        }
        for host in HOSTS:
            with self.subTest(host=host):
                for plugin, resource in worker_units.items():
                    prose = " ".join(read(self.package(host, plugin) / resource).split())
                    self.assertIn("Coordinators load `codebase-map:map-method`", prose)
                    self.assertIn("Workers never migrate roots", prose)
                    self.assertIn("use only its `migrate_root.py resolve`", prose)
                    self.assertIn("still-legacy `.codebase-xray` path blocks", prose)
                for plugin, resources in readonly_units.items():
                    for resource in resources:
                        prose = " ".join(read(self.package(host, plugin) / resource).split())
                        self.assertIn("coordinator alone may perform the project-bound Codebase Map preflight", prose)
                        self.assertIn("write only bound relocation metadata", prose)
                        self.assertIn("authorizes no application changes, analysis run, worker migration or generic filesystem move", prose)
                references = self.package(host, "codebase-map") / "skills/map-method/references"
                for name in ("reading.md", "run.md"):
                    preflight = read(references / name).split("\n## ", 1)[0]
                    self.assertIn("Coordinators: before", preflight)
                    self.assertIn("Workers only resolve bindings", preflight)
                migration = " ".join(read(references / "migration.md").split())
                self.assertIn("Coordinators run preflight", migration)
                self.assertIn("Workers only resolve supplied bindings afterward", migration)


if __name__ == "__main__":
    unittest.main()
