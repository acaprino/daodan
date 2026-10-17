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

    def test_content_focus_selection_is_bound_to_isolated_workers_and_a_delivery_barrier(self):
        workflow = self.workflow("digital-marketing", "content-strategy")
        phases = {phase.id: phase for phase in workflow.phases}
        audit = phases["audit"]
        self.assertIn(audit.fanout_from, phases["scope"].produces)
        self.assertEqual(audit.role, "content-marketer")
        self.assertIn("digital-marketing/content-marketer", workflow.dispatch.roles)
        self.assertEqual(audit.isolation, "required")
        self.assertEqual(audit.join, "all-delivered")
        self.assertEqual(audit.concurrency, "preferred")
        self.assertIn(audit.id, phases["synthesis"].needs)
        self.assertIn("approval", phases["apply"].needs)
        self.assertIn("apply", phases["report"].needs)
        self.assertEqual(
            [phase.id for phase in workflow.phases
             if "artifact:content-strategy-report" in phase.produces],
            ["report"],
        )
        body = (self.registry["digital-marketing"].root / workflow.entrypoint).read_text(encoding="utf-8")
        self.assertIn("report only", body)
        self.assertIn("zero applied changes", body)
        self.assertIn("delivered or failed", body)

    def test_worker_briefs_do_not_override_host_dispatch_fields(self):
        for plugin, name in (
            ("stripe", "audit-webhooks"),
            ("pwa-expert", "pwa-audit"),
            ("digital-marketing", "content-strategy"),
        ):
            with self.subTest(plugin=plugin):
                body = (self.registry[plugin].root / self.workflow(plugin, name).entrypoint).read_text(encoding="utf-8")
                self.assertNotRegex(body, r"(?m)^\s*Task:")
                self.assertNotIn("subagent_type", body)
                self.assertNotIn("run_in_background", body)
                self.assertNotIn("model: sonnet", body)

    def test_changed_graphs_keep_their_provider_edges_and_exported_contracts(self):
        for name in ("stripe", "pwa-expert", "digital-marketing", "peer-review"):
            with self.subTest(plugin=name):
                plugin = self.registry[name]
                self.assertEqual(validate_workflow_graph(plugin), [])
                self.assertEqual(validate_execution_contracts(plugin), [])
                self.assertEqual(validate_dependencies(plugin, self.registry), [])
                self.assertEqual(validate_contract_exports(plugin, self.registry), [])


if __name__ == "__main__":
    unittest.main()
