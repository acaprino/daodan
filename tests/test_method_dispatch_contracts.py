"""Real-kernel worker ownership and nested review dispatch regressions.

These checks do not render packages or start a host. They protect the control
plane that every adapter consumes and the method briefs it must bind.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.load import load_plugin
from scripts.daodan.model import INLINE_WORKER_REFERENCE
from scripts.daodan.validate import (
    validate_contract_exports,
    validate_dependencies,
    validate_execution_contracts,
    validate_workflow_graph,
)


class MethodDispatchContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = {
            path.name: load_plugin(path)
            for path in (REPO_ROOT / "plugins").iterdir()
            if (path / "plugin.toml").is_file()
        }

    def workflow(self, plugin, name):
        return next(item for item in self.registry[plugin].workflows if item.name == name)

    def test_standalone_reviewers_deliver_findings_before_the_coordinator_report(self):
        for plugin, name, role in (
            ("react-development", "review-react", "react-performance-optimizer"),
            ("typescript-development", "review-typescript", "type-safety-auditor"),
        ):
            with self.subTest(plugin=plugin):
                workflow = self.workflow(plugin, name)
                phases = {phase.id: phase for phase in workflow.phases}
                worker = phases["review"]
                report = phases["report"]
                self.assertEqual(worker.role, role)
                self.assertEqual(worker.isolation, "required")
                self.assertIn(f"{plugin}/{role}", workflow.dispatch.roles)
                self.assertTrue(workflow.dispatch.isolated)
                self.assertIn(worker.id, report.needs)
                self.assertEqual(report.isolation, "shared")
                self.assertIsNone(report.role)
                self.assertTrue(set(worker.produces) <= set(report.consumes))
                final = f"artifact:{name}-report"
                self.assertEqual(
                    [phase.id for phase in workflow.phases if final in phase.produces],
                    [report.id],
                )
                self.assertNotIn(final, worker.produces)

    def test_nested_review_methods_use_a_declared_isolated_worker_for_inline_tasks(self):
        for name in ("code-review", "team-review", "pr-review"):
            with self.subTest(name=name):
                dispatch = self.workflow("senior-review", name).dispatch
                self.assertTrue(dispatch.inline_workers)
                self.assertTrue(dispatch.isolated)
        self.assertIn("project-protocol", self.registry["senior-review"].required_dependencies)
        self.assertIn(
            "isolated-worker", self.registry["project-protocol"].components.roles
        )
        for relative in (
            "review-quality-gates/SKILL.md",
            "review-quality-gates/references/code-review-agents.md",
            "review-quality-gates/references/code-review-fix-loop.md",
            "review-consolidation/references/code-review.md",
            "review-consolidation/references/team-review.md",
        ):
            with self.subTest(relative=relative):
                body = (REPO_ROOT / "plugins/senior-review/skills" / relative).read_text(encoding="utf-8")
                self.assertIn(INLINE_WORKER_REFERENCE.replace("/", ":"), body)
                self.assertNotRegex(body, r"role:\s*[\"`]?general-purpose")
                self.assertNotIn("run_in_background", body)
                self.assertNotIn("model: sonnet", body)

    def test_worker_briefs_do_not_override_host_dispatch_fields(self):
        for plugin, name in (
            ("react-development", "review-react"),
            ("typescript-development", "review-typescript"),
            ("clean-code", "clean-code"),
        ):
            with self.subTest(plugin=plugin):
                body = (self.registry[plugin].root / self.workflow(plugin, name).entrypoint).read_text(encoding="utf-8")
                self.assertNotRegex(body, r"(?m)^\s*Task:")
                self.assertNotIn("subagent_type", body)
                self.assertNotIn("run_in_background", body)
                self.assertNotIn("model: sonnet", body)

    def test_changed_graphs_keep_their_provider_edges_and_exported_contracts(self):
        for name in ("react-development", "typescript-development", "clean-code", "senior-review",
                     "peer-review", "moe", "project-lifecycle", "project-knowledge"):
            with self.subTest(plugin=name):
                plugin = self.registry[name]
                self.assertEqual(validate_workflow_graph(plugin), [])
                self.assertEqual(validate_execution_contracts(plugin), [])
                self.assertEqual(validate_dependencies(plugin, self.registry), [])
                self.assertEqual(validate_contract_exports(plugin, self.registry), [])


if __name__ == "__main__":
    unittest.main()
