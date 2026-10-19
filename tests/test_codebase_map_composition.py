"""Atomic Map acquisition stays bound and isolated in composing consumers.

These are source and compiler contracts, not installed-host execution evidence.
"""

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import lint_dependency_graph as graph
from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from scripts.daodan.validate import validate_dependencies
from host_binding_assertions import loaded_instruction_text

ANALYST = "codebase-map/map-analyst"
# Since 38.0.0 every command is a `daodan` workflow. The entries that replaced
# the old composing commands (audit and assess: check-health; assess --init:
# init-project; team-review and verify: review-branch; repair: fix-bug; change:
# new-feature; verify and consolidate: finish-task; maintain: run-maintenance)
# bind the analyst, and the methods they load stay with their owners.
ENTRY = "daodan"
CONSUMERS = ("check-health", "init-project", "review-branch", "fix-bug", "new-feature",
             "finish-task", "run-maintenance")
METHOD_OWNERS = ("abstraction-architect", "senior-review", "project-lifecycle")
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
        entry = self.registry[ENTRY]
        workflows = {workflow.name: workflow for workflow in entry.workflows}
        for name in CONSUMERS:
            with self.subTest(plugin=ENTRY, workflow=name):
                self.assertIn(name, workflows)
                self.assertIn(ANALYST, workflows[name].dispatch.roles)
                self.assertTrue(workflows[name].dispatch.isolated)
        for name in (ENTRY, *METHOD_OWNERS):
            with self.subTest(plugin=name):
                plugin = self.registry[name]
                self.assertIn("codebase-map", plugin.required_dependencies)
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
        # Since 38.0.0 the audit procedure is the abstraction-architect method that
        # check-health runs. Its two acquisitions run the canonical analyze entry
        # with named controls rather than a command line.
        text = self.body("abstraction-architect/skills/abstraction-architect/references/audit.md")
        self.assertIn("newest", text)
        self.assertIn("snapshot.py resolve", text)
        self.assertIn("run_id", text)
        self.assertIn("never the mirror", text)
        self.assertIn("snapshot.py", text)
        self.assertIn("--verify", text)
        self.assertIn("parent_run", text)
        self.assertIn("original controls", text)
        acquisition = text.split("### Global acquisition", 1)[1].split("### Diff acquisition", 1)[0]
        self.assertIn("references/entry-analyze.md", acquisition)
        launches = [line for line in acquisition.splitlines() if line.strip().startswith("stop after:")]
        self.assertEqual(len(launches), 2)
        self.assertTrue(all(line.split(":", 1)[1].strip() == "phase 4" for line in launches))
        updates = [line.split(":", 1)[1].strip() for line in acquisition.splitlines()
                   if line.strip().startswith("update:")]
        self.assertEqual(updates, ["yes, from parent_run", "no"])
        diff = text.split("### Diff acquisition", 1)[1].split("### Auditor delivery", 1)[0]
        self.assertIn("never launches", diff)
        for launch in ("entry-analyze.md", "stop after:", "/daodan:map-code", "/codebase-map:analyze"):
            self.assertNotIn(launch, diff)
        self.assertIn("files.added", diff)
        self.assertIn("files.modified", diff)
        self.assertIn("files.removed", diff)
        self.assertIn("changed_files", diff)
        self.assertIn("Gaps", diff)

    def test_auditor_uses_bound_context_and_reports_every_out_of_diff_change(self):
        text = self.body("abstraction-architect/roles/abstraction-architect-agent.md")
        self.assertIn(".codebase-map/runs/<run-id>/", text)
        self.assertIn("snapshot.py resolve", text)
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
        # The compiler checks the entry's dispatch roles. Since 38.0.0 the method
        # owners register no workflow, so the dependency linter that CI runs checks
        # the runtime map loads and dispatches of their bodies.
        with self.subTest(plugin=ENTRY):
            plugin = self.registry[ENTRY]
            candidate = replace(plugin, required_dependencies=tuple(
                dep for dep in plugin.required_dependencies if dep != "codebase-map"
            ))
            self.assertTrue(validate_dependencies(candidate, self.registry))
        with patch.object(graph, "PLUGINS", REPO_ROOT / "plugins"):
            declared = graph.load_plugins()
            references = graph.extract_references(declared)
            baseline = set(graph.check_runtime_refs(declared, references))
            for name in METHOD_OWNERS:
                with self.subTest(plugin=name):
                    candidate = copy.deepcopy(declared)
                    candidate[name]["dependencies"] = [
                        dep for dep in candidate[name]["dependencies"] if dep != "codebase-map"
                    ]
                    problems = [problem for problem in graph.check_runtime_refs(candidate, references)
                                if problem not in baseline]
                    self.assertTrue(problems)
                    self.assertTrue(all("'codebase-map'" in problem and name in problem
                                        for problem in problems), problems)

    def test_all_hosts_bind_composed_analyst_as_a_worker_and_require_isolation(self):
        with tempfile.TemporaryDirectory(prefix="daodan-map-composition-") as temp:
            for host in HOSTS:
                adapter = load_adapter(REPO_ROOT / "adapters", host)
                with self.subTest(host=host, plugin=ENTRY):
                    package = Path(temp) / host / ENTRY
                    render_plugin(self.registry[ENTRY], adapter, package,
                                  adapters_root=REPO_ROOT / "adapters",
                                  plugin_registry=self.registry)
                    for workflow in CONSUMERS:
                        harness = package / HARNESS_PATHS[host].format(
                            plugin=ENTRY, workflow=workflow
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
                for name in (ENTRY, *METHOD_OWNERS):
                    with self.subTest(host=host, plugin=name):
                        bindings = dict(adapter.bindings)
                        bindings["contexts.isolate"] = replace(
                            bindings["contexts.isolate"], state="unsupported"
                        )
                        unsupported = resolve_support(self.registry[name],
                                                      replace(adapter, bindings=bindings))
                        self.assertEqual(unsupported.state, "unsupported")
                        self.assertIn("contexts.isolate", unsupported.missing_capabilities)


if __name__ == "__main__":
    unittest.main()
