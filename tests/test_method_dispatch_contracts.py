"""Real-kernel worker ownership and nested review dispatch regressions.

These checks do not render packages or start a host. They protect the control
plane that every adapter consumes and the method briefs it must bind. Since
marketplace 38.0.0 every command is a `daodan` workflow: the control plane is
the entry's sidecar, and the briefs are the owner units the entry loads.
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
        # Until 38.0.0 review-react and review-typescript declared an isolated
        # `review` phase and a shared `report` phase that alone wrote the report.
        # Those audits are now owner units that check-health's assessment loads:
        # the entry declares each reviewer for isolated dispatch, and the unit
        # states that the reviewer delivers to an intermediate path before the
        # coordinator writes the one final report.
        entry = self.workflow("daodan", "check-health")
        self.assertTrue(entry.dispatch.isolated)
        assess = (self.registry["project-lifecycle"].root
                  / "skills/lifecycle-method/references/assess.md").read_text(encoding="utf-8")
        for plugin, skill, role, output in (
            ("react-development", "react-best-practices", "react-performance-optimizer", "react-review"),
            ("typescript-development", "type-safety-rules", "type-safety-auditor", "ts-review"),
        ):
            with self.subTest(plugin=plugin):
                provider = self.registry[plugin]
                self.assertEqual(provider.workflows, ())
                self.assertIn(role, provider.components.roles)
                self.assertIn(f"{plugin}/{role}", entry.dispatch.roles)
                self.assertIn(plugin, self.registry["daodan"].required_dependencies)
                self.assertIn(plugin, self.registry["project-lifecycle"].required_dependencies)
                self.assertIn(f"`{plugin}:{skill}`", assess)
                body = (provider.root / "skills" / skill / "references/audit.md").read_text(encoding="utf-8")
                prose = " ".join(body.split())
                self.assertIn(f"Dispatch `{plugin}:{role}` in its required isolated context "
                              "through the host harness", prose)
                worker = prose.index(f"intermediate report path `<run>/{output}/worker-findings.md`")
                self.assertIn("The reviewer returns its findings and a delivered or failed outcome; "
                              "it does not write the final report. Record that outcome before the "
                              "report phase. A failed or missing delivery leaves the review incomplete "
                              "and must be reported.", prose)
                report = prose.index(f"After the agent completes, create the `<run>/{output}/` "
                                     "directory and write `report.md`.")
                self.assertLess(worker, report)
                self.assertIn(f"**Output file:** `<run>/{output}/report.md`", prose)

    def test_nested_review_methods_use_a_declared_isolated_worker_for_inline_tasks(self):
        # code-review became review-changes; team-review and pr-review became
        # the two variants of review-branch (38.0.0).
        for name in ("review-changes", "review-branch"):
            with self.subTest(name=name):
                dispatch = self.workflow("daodan", name).dispatch
                self.assertTrue(dispatch.inline_workers)
                self.assertTrue(dispatch.isolated)
        for owner in ("daodan", "senior-review"):
            self.assertIn("project-protocol", self.registry[owner].required_dependencies)
        self.assertIn(
            "isolated-worker", self.registry["project-protocol"].components.roles
        )
        for relative in (
            "review-method/SKILL.md",
            "review-method/references/light.md",
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
        # The old review-react, review-typescript and clean-code entries are the
        # owner units their replacements load since 38.0.0; every daodan entry
        # body is held to the same rule.
        bodies = {
            "react-development": "skills/react-best-practices/references/audit.md",
            "typescript-development": "skills/type-safety-rules/references/audit.md",
            "clean-code": "skills/readability-method/SKILL.md",
            "project-lifecycle": "skills/lifecycle-method/references/refactor.md",
        }
        entry = self.registry["daodan"]
        for workflow in entry.workflows:
            bodies[f"daodan:{workflow.name}"] = workflow.entrypoint
        for label, relative in bodies.items():
            with self.subTest(body=label):
                owner = self.registry[label.split(":", 1)[0]]
                body = (owner.root / relative).read_text(encoding="utf-8")
                self.assertNotRegex(body, r"(?m)^\s*Task:")
                self.assertNotIn("subagent_type", body)
                self.assertNotIn("run_in_background", body)
                self.assertNotIn("model: sonnet", body)

    def test_changed_graphs_keep_their_provider_edges_and_exported_contracts(self):
        for name in ("daodan", "react-development", "typescript-development", "clean-code", "senior-review",
                     "peer-review", "moe", "project-lifecycle", "project-knowledge"):
            with self.subTest(plugin=name):
                plugin = self.registry[name]
                self.assertEqual(validate_workflow_graph(plugin), [])
                self.assertEqual(validate_execution_contracts(plugin), [])
                self.assertEqual(validate_dependencies(plugin, self.registry), [])
                self.assertEqual(validate_contract_exports(plugin, self.registry), [])


if __name__ == "__main__":
    unittest.main()
