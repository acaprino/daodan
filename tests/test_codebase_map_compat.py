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
# Since 38.0.0 both entry units are loaded by one daodan command, which replaced
# the two codebase-map wrappers and runs the method in its orchestrating context.
ENTRY = "map-code"
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
                           cls.registry["senior-review"], cls.registry["repo-hygiene"],
                           cls.registry["daodan"]):
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
        entry = self.registry["daodan"]
        wrapper = read(entry.root / "workflows" / f"{ENTRY}.md")
        spec = next(item for item in entry.workflows if item.name == ENTRY)
        # The command loads the method in the coordinator's own context: every
        # phase of its graph is shared, and only the dispatched workers isolate.
        self.assertTrue(spec.phases)
        self.assertTrue(all(phase.isolation == "shared" for phase in spec.phases))
        self.assertTrue(spec.dispatch.isolated)
        self.assertIn("Load the skill `codebase-map:map-method`", wrapper)
        self.assertNotIn("## Pre-flight", wrapper)
        self.assertNotIn("## Method loads", wrapper)
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                source = read(references / f"entry-{workflow}.md")
                self.assertFalse(source.startswith("---\n"))
                self.assertIn("## Method loads", source)
                self.assertIn(f"references/entry-{workflow}.md", wrapper)
                if workflow == "analyze":
                    for section in ("## Coordinator boundary", "## Isolated analysis", "## Publish and completion"):
                        self.assertIn(section, source)
                        self.assertNotIn(section, wrapper)
                    self.assertIn("codebase-map:map-analyst", source)
                    self.assertIn("nested loads in the coordinator context", " ".join(source.split()))
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
        source = read(self.registry["daodan"].root / "workflows" / f"{ENTRY}.md")
        entry_method = source.split("\n---\n", 1)[1].lstrip("\n")
        for host in HOSTS:
            with self.subTest(host=host, workflow=ENTRY):
                wrapper = read(self.component(host, "daodan", "workflows", ENTRY))
                if host == "copilot":
                    self.assertIn(f"daodan:{ENTRY}-coordinator", wrapper)
                    wrapper = read(self.package(host, "daodan") /
                                   f"agents/{ENTRY}-coordinator.agent.md")
                self.assertIn("## Execution harness", wrapper)
                self.assertIn("`execute`: runs in the orchestrating context", wrapper)
                self.assertIn("Every dispatched worker runs in its own", wrapper)
                self.assertIn("`codebase-map:map-analyst`", wrapper)
                self.assertEqual(canonical_markdown(wrapper.split("\n## Method\n\n", 1)[1]),
                                 canonical_markdown(self.adapt_placeholders(host, entry_method)))
            for workflow in WORKFLOWS:
                with self.subTest(host=host, workflow=workflow):
                    resource = f"entry-{workflow}.md"
                    shared = self.assert_shared_resource(host, resource)
                    self.assertIn("## Coordinator boundary" if workflow == "analyze"
                                  else "## CRITICAL RULES", shared)
                    self.assertIn(f"references/{resource}", wrapper)
                    if workflow == "analyze":
                        # Since 38.0.0 no phase graph renders the old command's
                        # analysis and publish phases: the shipped unit orders one
                        # isolated analyst before publication by the coordinator.
                        prose = " ".join(shared.split())
                        self.assertIn("dispatch one isolated `codebase-map:map-analyst`", prose)
                        self.assertIn("publish only when the gate permits it", prose)
                        self.assertLess(shared.index("## Isolated analysis"),
                                        shared.index("## Publish and completion"))
            for role in ROLES:
                with self.subTest(host=host, role=role):
                    resource = f"role-{role}.md"
                    self.assert_shared_resource(host, resource)
                    wrapper = read(self.component(host, "codebase-map", "roles", role))
                    self.assertIn(resource, wrapper)
                    self.assertIn("same worker context", wrapper)
            policy = tomllib.loads(read(self.package(host, "codebase-map") / "policies/write-confinement.toml"))
            self.assertNotIn("migration", policy)
            method = self.component(host, "codebase-map", "skills", "map-method").parent
            self.assertTrue((method / "scripts/confinement.py").is_file())
            self.assertFalse((method / "scripts/migrate_root.py").exists())

    def test_standalone_map_consumption_ships_on_all_hosts(self):
        description = read(self.canonical.root / "skills/map-method/SKILL.md").split("---", 2)[1]
        self.assertIn("standalone navigation of existing map evidence", description)
        self.assertIn("project questions, unfamiliar code, debugging, feature work", description)
        self.assertIn("Loading the skill starts no analysis or refresh", description)
        for host in HOSTS:
            with self.subTest(host=host):
                method = read(self.component(host, "codebase-map", "skills", "map-method"))
                self.assertIn("Every map consumer, including analyze and composed workflows", method)
                self.assertIn("`references/reading.md` section `Task views`", method)
                self.assertIn("sections `CRITICAL PRINCIPLE: EVIDENCE-ANCHORED OUTPUT` and `Forbidden Files`", method)
                standalone = self.assert_shared_resource(host, "standalone.md")
                reading = self.assert_shared_resource(host, "reading.md")
                evidence = self.assert_shared_resource(host, "evidence.md")
                self.assertIn("| `references/standalone.md` | all | always |", reading)
                analyst = read(self.component(host, "codebase-map", "roles", "map-analyst"))
                self.assertIn("references/standalone.md", analyst)
                self.assertIn("references/reading.md` | section: Task views", analyst)
                for role in ROLES[:3]:
                    role_unit = self.assert_shared_resource(host, f"role-{role}.md")
                    self.assertIn("references/standalone.md", role_unit)
                    self.assertIn("references/reading.md` | section: Task views", role_unit)
                synthesizer = self.assert_shared_resource(host, "role-partition-synthesizer.md")
                self.assertNotIn("references/standalone.md", synthesizer)
                self.assertNotIn("references/reading.md` | section: Task views", synthesizer)
                task_views = reading.split("## Task views", 1)[1].split("## Method loads", 1)[0]
                standalone_evidence = evidence.split("## Script Commands", 1)[0]
                self.assertNotIn("deepen.md", task_views)
                self.assertNotIn("semantic_map.py", task_views)
                self.assertNotIn("snapshot.py write", standalone_evidence)
                self.assertNotIn("--reuse", standalone_evidence)
                prose = " ".join(standalone.split())
                self.assertIn("inside analyze or other composed workflows", prose)
                self.assertIn("This unit grants no run creation, snapshot refresh", prose)
                self.assertIn("codebase_map_outline", prose)
                self.assertIn("codebase_map_edit_impact", prose)
                self.assertIn("verify material behavior and business rules against current source", prose)
                self.assertIn("continues with ordinary repository exploration", prose)
                self.assertIn("never starting analysis, update or deepening implicitly", prose)
                self.assertIn("composed producer instead follows its authorized refresh", prose)
                self.assertIn("artifact-only consumers stay within their declared inputs", prose)
                self.assertNotIn("codebase_map_create_run", standalone)
                self.assertNotIn("entry-analyze.md", standalone)
                self.assertNotIn("migrate_root.py", standalone)

    def test_abstraction_worker_never_launches_a_map_on_all_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = " ".join(read(self.component(
                    host, "abstraction-architect", "roles", "abstraction-architect-agent",
                )).split())
                self.assertIn("never launches a Map and never writes the map", text)
                self.assertNotIn("migrate_root", text)
                self.assertIn("Edit nothing except `report_path`", text)
                self.assertNotIn("references/migration.md", text)
                census = read(self.package(host, "abstraction-architect") /
                              "skills/abstraction-architect/references/concept-census.md")
                self.assertIn("Read the supplied bound run's phase files", census)
                self.assertIn("the root mirror is not this input", census)
                self.assertNotIn("## Existing analysis compatibility", census)
                self.assertNotIn("references/migration.md", census)

    def test_handover_writes_only_its_run_and_dossier_on_all_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                text = " ".join(read(self.component(
                    host, "project-lifecycle", "skills", "handover-method",
                )).split())
                self.assertIn("Only run-owned records, worker reports and the dossier may be written.", text)
                self.assertNotIn("preflight exception", text)
                self.assertIn("Application files, tests, durable instructions, README and project guides", text)

    def test_no_shipped_unit_names_a_root_migration_on_all_hosts(self):
        plugins = ("abstraction-architect", "codebase-map", "project-knowledge",
                   "project-lifecycle", "repo-hygiene", "senior-review")
        retired = ("migrate_root", "references/migration.md", ".codebase-xray")
        for host in HOSTS:
            for plugin in plugins:
                with self.subTest(host=host, plugin=plugin):
                    for path in self.package(host, plugin).rglob("*.md"):
                        text = read(path)
                        for name in retired:
                            self.assertNotIn(name, text, f"{path} still names {name}")


if __name__ == "__main__":
    unittest.main()
