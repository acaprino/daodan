"""Atomic Map acquisition stays bound and isolated in composing consumers.

These are source and compiler contracts, not installed-host execution evidence.
"""

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from scripts.daodan.validate import validate_dependencies
from host_binding_assertions import loaded_instruction_text

ANALYST = "codebase-map/map-analyst"
CONSUMERS = {
    "abstraction-architect": ("audit",),
    "senior-review": ("team-review",),
    "project-lifecycle": ("assess", "repair", "change", "verify", "consolidate", "maintain"),
}
HARNESS_PATHS = {
    "claude": "commands/{workflow}.md",
    "copilot": "agents/{workflow}-coordinator.agent.md",
    "codex": "skills/{workflow}-workflow/SKILL.md",
    "pi": "prompts/{plugin}-{workflow}.md",
    "opencode": "commands/{workflow}.md",
}


class CodebaseMapCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = {
            path.parent.name: load_plugin(path.parent)
            for path in (REPO_ROOT / "plugins").glob("*/plugin.toml")
        }

    def body(self, relative):
        return (REPO_ROOT / "plugins" / relative).read_text(encoding="utf-8")

    def test_every_map_composing_workflow_declares_the_required_isolated_analyst(self):
        for name, workflows in CONSUMERS.items():
            plugin = self.registry[name]
            self.assertIn("codebase-map", plugin.required_dependencies)
            for workflow in plugin.workflows:
                if workflow.name in workflows:
                    with self.subTest(plugin=name, workflow=workflow.name):
                        self.assertIn(ANALYST, workflow.dispatch.roles)
                        self.assertTrue(workflow.dispatch.isolated)
                        self.assertNotIn("map-analyst", plugin.components.skills)

    def test_nested_method_paragraphs_preserve_analysis_isolation(self):
        for relative in (
            "senior-review/skills/review-method/SKILL.md",
            "senior-review/skills/review-preparation/SKILL.md",
            "senior-review/skills/review-preparation/references/team-review.md",
            "project-lifecycle/skills/lifecycle-method/SKILL.md",
            "project-lifecycle/skills/lifecycle-method/references/assess.md",
        ):
            with self.subTest(relative=relative):
                text = self.body(relative)
                self.assertIn("codebase-map:map-analyst", text)
                self.assertIn("isolated", text)
                self.assertNotIn("canonical phases in order in this same context", text)
                self.assertNotIn("map-method` phase-by-phase in this same context", text)
                self.assertNotIn("canonical method phase-by-phase", text)

    def test_audit_binds_runs_and_bounds_both_acquisition_branches(self):
        text = self.body("abstraction-architect/workflows/audit.md")
        self.assertIn("newest", text)
        self.assertIn("snapshot/manifest.json", text)
        self.assertIn("run_id", text)
        self.assertIn("never the mirror", text)
        self.assertIn("snapshot.py", text)
        self.assertIn("--verify", text)
        self.assertIn("parent_run", text)
        self.assertIn("original flags", text)
        launches = [line for line in text.splitlines()
                    if line.strip().startswith("/codebase-map:analyze ")]
        self.assertEqual(len(launches), 2)
        self.assertTrue(all("--stop-after 4" in line for line in launches))
        diff = text.split("### Diff acquisition", 1)[1].split("### Auditor delivery", 1)[0]
        self.assertIn("never launches", diff)
        self.assertNotIn("/codebase-map:analyze", diff)
        self.assertIn("files.added", diff)
        self.assertIn("files.modified", diff)
        self.assertIn("files.removed", diff)
        self.assertIn("changed_files", diff)
        self.assertIn("Gaps", diff)

    def test_auditor_uses_bound_context_and_reports_every_out_of_diff_change(self):
        text = self.body("abstraction-architect/roles/abstraction-architect-agent.md")
        self.assertIn(".codebase-map/runs/<run-id>/", text)
        self.assertIn("snapshot/manifest.json", text)
        self.assertIn("map_outside_diff_changed_files", text)
        self.assertIn("every path", text)
        self.assertIn("never launches", text)
        self.assertIn("never read the mirror's phase files", text)
        self.assertIn("only its `state.json -> run_id`", text)
        self.assertIn("only from the same bound run", text)
        census = self.body("abstraction-architect/skills/abstraction-architect/references/concept-census.md")
        self.assertNotIn("Read `.codebase-map/`", census)
        self.assertIn("bound run", census)

    def test_dependency_validation_rejects_missing_map_provider(self):
        for name in CONSUMERS:
            with self.subTest(plugin=name):
                plugin = self.registry[name]
                candidate = replace(plugin, required_dependencies=tuple(
                    dep for dep in plugin.required_dependencies if dep != "codebase-map"
                ))
                self.assertTrue(validate_dependencies(candidate, self.registry))

    def test_all_hosts_bind_composed_analyst_as_a_worker_and_require_isolation(self):
        with tempfile.TemporaryDirectory(prefix="daodan-map-composition-") as temp:
            for host in HOSTS:
                adapter = load_adapter(REPO_ROOT / "adapters", host)
                for name, workflows in CONSUMERS.items():
                    with self.subTest(host=host, plugin=name):
                        plugin = self.registry[name]
                        package = Path(temp) / host / name
                        render_plugin(plugin, adapter, package,
                                      adapters_root=REPO_ROOT / "adapters",
                                      plugin_registry=self.registry)
                        for workflow in workflows:
                            harness = package / HARNESS_PATHS[host].format(
                                plugin=name, workflow=workflow
                            )
                            text = loaded_instruction_text(self, harness, host)
                            self.assertIn("map-analyst", text)
                            self.assertIn("isolated", text)
                            if host in {"codex", "pi"}:
                                analyst_body = package / "contracts/dispatch/codebase-map/map-analyst.md"
                                self.assertTrue(analyst_body.is_file())
                                role_text = analyst_body.read_text(encoding="utf-8")
                                self.assertIn("codebase-map:map-method", role_text)
                                self.assertIn("Never publish", role_text)
                            else:
                                self.assertIn("codebase-map", text)
                        bindings = dict(adapter.bindings)
                        bindings["contexts.isolate"] = replace(
                            bindings["contexts.isolate"], state="unsupported"
                        )
                        unsupported = resolve_support(plugin, replace(adapter, bindings=bindings))
                        self.assertEqual(unsupported.state, "unsupported")
                        self.assertIn("contexts.isolate", unsupported.missing_capabilities)


if __name__ == "__main__":
    unittest.main()
