"""Operational compatibility of the former Codebase X-ray entry identities."""

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
from scripts.daodan.catalogs import catalog_document, render_catalog  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import opencode_permissions, render_plugin  # noqa: E402
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


def frontmatter(text: str) -> str:
    return text[: text.index("\n---\n", 4) + 5]


class CodebaseMapCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = {
            path.parent.name: load_plugin(path.parent)
            for path in sorted((REPO_ROOT / "plugins").glob("*/plugin.toml"))
        }
        cls.canonical = cls.registry["codebase-map"]
        cls.legacy = cls.registry["codebase-xray"]
        cls.temp = tempfile.TemporaryDirectory(prefix="daodan-map-compat-")
        cls.packages = {}
        cls.adapters = {host: load_adapter(ADAPTERS, host) for host in HOSTS}
        for host, adapter in cls.adapters.items():
            for plugin in (cls.canonical, cls.legacy, cls.registry["abstraction-architect"],
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

    def test_old_installation_requires_the_canonical_provider(self):
        self.assertEqual(self.legacy.required_dependencies, ("codebase-map",))
        self.assertEqual(self.legacy.components.skills, ("xray-method",))
        self.assertEqual(set(self.legacy.components.roles), set(ROLES))
        self.assertEqual(self.legacy.components.workflows, WORKFLOWS)
        for plugin in (self.legacy, self.canonical):
            self.assertGreaterEqual(tuple(map(int, plugin.version.split("."))), (6, 0, 0))
        issues = validate_plugins(tuple(self.registry.values()), CAPABILITY_REGISTRY)
        self.assertEqual(issues, [], "\n".join(str(issue) for issue in issues))

    def test_shared_sources_retain_metadata_and_full_execution_in_one_location(self):
        references = self.canonical.root / "skills/map-method/references"
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                source = read(references / f"entry-{workflow}.md")
                wrapper = read(self.canonical.root / "workflows" / f"{workflow}.md")
                legacy = read(self.legacy.root / "workflows" / f"{workflow}.md")
                self.assertFalse(source.startswith("---\n"), "Shared behavior does not duplicate registration metadata")
                self.assertEqual(frontmatter(wrapper), frontmatter(legacy))
                if workflow == "analyze":
                    self.assertIn("## Coordinator boundary", source)
                    self.assertIn("## Isolated analysis", source)
                    self.assertIn("## Publish and completion", source)
                    self.assertIn("codebase-map:map-analyst", source)
                    for entry in (wrapper, legacy):
                        self.assertNotIn("## Preflight", entry)
                        self.assertNotIn("## Isolated analysis", entry)
                        self.assertNotIn("## Publish and completion", entry)
                else:
                    self.assertIn("## CRITICAL RULES", source)
                self.assertIn("## Method loads", source)
                self.assertNotIn("## Pre-flight", wrapper)
                self.assertNotIn("## Pre-flight", legacy)
                self.assertIn("in this same coordinator context", wrapper)
                self.assertIn("in this same coordinator context", legacy)
        for role in ROLES:
            with self.subTest(role=role):
                source = read(references / f"role-{role}.md")
                wrapper = read(self.canonical.root / "roles" / f"{role}.md")
                legacy = read(self.legacy.root / "roles" / f"{role}.md")
                self.assertFalse(source.startswith("---\n"), "Shared behavior does not duplicate registration metadata")
                self.assertEqual(frontmatter(wrapper), frontmatter(legacy))
                self.assertIn("## OWNERSHIP CONTRACT" if role != "semantic-interconnect-mapper"
                              else "## PRIME DIRECTIVES", source)
                self.assertIn("in this same worker context", wrapper)
                self.assertIn("in this same worker context", legacy)
                self.assertNotIn("Agent", frontmatter(legacy))
                self.assertNotIn("Task", frontmatter(legacy))

    def test_all_five_hosts_ship_shared_resources_and_old_registered_entries(self):
        for host in HOSTS:
            for workflow in WORKFLOWS:
                with self.subTest(host=host, workflow=workflow):
                    resource = f"entry-{workflow}.md"
                    shared = self.assert_shared_resource(host, resource)
                    self.assertIn("## Coordinator boundary" if workflow == "analyze"
                                  else "## CRITICAL RULES", shared)
                    for plugin in ("codebase-map", "codebase-xray"):
                        path = self.component(host, plugin, "workflows", workflow)
                        wrapper = read(path)
                        if host == "copilot":
                            self.assertIn(f"{plugin}:{workflow}-coordinator", wrapper)
                            wrapper = read(self.package(host, plugin) /
                                           f"agents/{workflow}-coordinator.agent.md")
                        self.assertIn("## Execution harness", wrapper)
                        self.assertIn(resource, wrapper)
                        self.assertIn("## Method loads", wrapper)
                        self.assertIn("same coordinator context", wrapper)
                        source = read(self.registry[plugin].root / "workflows" / f"{workflow}.md")
                        method = source.split("\n---\n", 1)[1].lstrip("\n")
                        self.assertEqual(canonical_markdown(wrapper.split("\n## Method\n\n", 1)[1]),
                                         canonical_markdown(self.adapt_placeholders(host, method)))
                        if workflow == "analyze":
                            analyst = "map-analyst" if plugin == "codebase-map" else "codebase-map:map-analyst"
                            self.assertIn(f"`analysis`: one `{analyst}` in an isolated context", wrapper)
                            self.assertIn("`publish`: runs in the orchestrating context; needs `analysis`", wrapper)
            for role in ROLES:
                with self.subTest(host=host, role=role):
                    resource = f"role-{role}.md"
                    self.assert_shared_resource(host, resource)
                    for plugin in ("codebase-map", "codebase-xray"):
                        wrapper = read(self.component(host, plugin, "roles", role))
                        self.assertIn(resource, wrapper)
                        self.assertIn("same worker context", wrapper)
            method = read(self.component(host, "codebase-xray", "skills", "xray-method"))
            self.assertIn("codebase-map:map-method", method)
            self.assertIn("Literal helper paths", method)
            self.assertIn("not redirected", method)

    def test_legacy_harness_uses_canonical_workers_and_keeps_isolation(self):
        workflow = next(item for item in self.legacy.workflows if item.name == "team-analyze")
        expected = {f"codebase-map/{role}" for role in ROLES}
        self.assertEqual(set(workflow.worker_references(self.legacy.components.roles)), expected)
        self.assertTrue(all(phase.isolation == "required" for phase in workflow.phases if phase.role))
        for host in HOSTS:
            with self.subTest(host=host):
                package = self.package(host, "codebase-xray")
                path = self.component(host, "codebase-xray", "workflows", "team-analyze")
                if host == "copilot":
                    path = package / "agents/team-analyze-coordinator.agent.md"
                harness = read(path)
                for role in ROLES:
                    self.assertIn(f"codebase-map:{role}", harness)
                    if host in {"codex", "pi"}:
                        dispatch = read(package / f"contracts/dispatch/codebase-map/{role}.md")
                        self.assertIn(f"role-{role}.md", dispatch)
                        self.assertIn("same worker context", dispatch)
                        self.assertIn("Owner: codebase-map:", dispatch)
                self.assertIn("all-delivered", harness)

    def test_old_named_roles_keep_the_canonical_tool_permissions(self):
        for role in ROLES:
            source = read(self.canonical.root / "roles" / f"{role}.md")
            tools = re.search(r"(?m)^tools: (.+)$", frontmatter(source)).group(1)
            expected = opencode_permissions(tools)
            catalog = json.loads(render_catalog(
                "opencode", [self.canonical, self.legacy], "99.0.0",
                packages={plugin: self.package("opencode", plugin)
                          for plugin in ("codebase-map", "codebase-xray")},
            ))
            aliases = catalog["daodan"]["plugins"]["codebase-xray"]["agents"]
            actual = next(item for item in aliases if item["id"] == f"codebase-xray:{role}")
            self.assertEqual(actual["permissions"], expected)
            self.assertFalse(any(rule["action"] == "subagent" and rule["effect"] == "allow"
                                 for rule in actual["permissions"]))

    def test_catalogs_and_pi_names_preserve_old_installation_closure(self):
        plugins = [self.canonical, self.legacy]
        for host in ("claude", "copilot", "codex"):
            packages = {plugin: self.package(host, plugin) for plugin in ("codebase-map", "codebase-xray")}
            catalog = catalog_document(host, plugins, "99.0.0", packages)
            entry = next(item for item in catalog["plugins"] if item["name"] == "codebase-xray")
            self.assertEqual(entry["dependencies"], ["codebase-map"])
            self.assertEqual(entry["source"], f"./exports/{host}/plugins/codebase-xray")
        catalog = json.loads(render_catalog(
            "opencode", plugins, "99.0.0",
            packages={plugin: self.package("opencode", plugin) for plugin in ("codebase-map", "codebase-xray")},
        ))
        listing = catalog["daodan"]["plugins"]
        self.assertEqual(listing["codebase-xray"]["dependencies"], ["codebase-map"])
        self.assertEqual({item["name"] for item in listing["codebase-xray"]["commands"]},
                         {f"codebase-xray:{workflow}" for workflow in WORKFLOWS})
        self.assertEqual({item["id"] for item in listing["codebase-xray"]["skills"]},
                         {"codebase-xray:xray-method"})
        names = []
        for plugin in ("codebase-map", "codebase-xray"):
            for path in self.package("pi", plugin).glob("skills/*/SKILL.md"):
                names.append(re.search(r"(?m)^name: (.+)$", read(path)).group(1))
            for workflow in WORKFLOWS:
                self.assertTrue((self.package("pi", plugin) / f"prompts/{plugin}-{workflow}.md").is_file())
        self.assertEqual(len(names), len(set(names)), "Pi has a flat skill registry")

    def test_legacy_worker_translates_bound_paths_without_migrating_or_dispatching(self):
        for role in ROLES:
            with self.subTest(role=role):
                text = " ".join(read(self.legacy.root / "roles" / f"{role}.md").split())
                self.assertIn("migrate_root.py resolve", text)
                self.assertIn("coordinator", text)
                self.assertIn("never writes the legacy store", text)
                self.assertIn("performs no root migration", text)
                self.assertIn("Do not dispatch another worker", text)

    def test_compatibility_never_guesses_another_plugin_filesystem_root(self):
        for path in self.legacy.root.rglob("*.md"):
            text = read(path)
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}/skills/map-method", text, str(path))
            self.assertNotIn("../codebase-map", text, str(path))
            self.assertIn("codebase-map:map-method", text, str(path))
            self.assertIn("never\nto this compatibility package", text, str(path))


    def test_legacy_policy_binds_only_the_canonical_provider_preflight_on_all_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                package = self.package(host, "codebase-xray")
                policy = tomllib.loads(read(package / "policies/write-confinement.toml"))
                migration = policy["migration"]
                self.assertEqual(migration["legacy_root"], ".codebase-xray")
                self.assertEqual(migration["helper_provider"], "codebase-map:map-method")
                self.assertEqual(migration["helper"], "scripts/migrate_root.py")
                self.assertTrue(migration["preserve_evidence_bytes"])
                self.assertTrue(migration["require_idle_legacy_runs"])
                method = self.component(host, "codebase-map", "skills", "map-method").parent
                self.assertTrue((method / migration["helper"]).is_file())
                self.assertEqual(policy["roots"], {"xray": ".codebase-map"})
                self.assertTrue(policy["confinement"]["forbid_writes_outside_roots"])

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
