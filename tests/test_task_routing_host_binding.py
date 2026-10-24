"""The installed instruction closure binds request routing on every host."""

import unittest

import test_daodan_operational_binding as operational


class RoutingHostTests(unittest.TestCase):
    render_in_memory = operational.OperationalBindingTests.render_in_memory

    def test_every_host_ships_the_routing_method_and_its_fallback(self):
        for host in operational.HOSTS:
            with self.subTest(host=host):
                package = self.render_in_memory("model-routing", host)
                skill = package["skills/model-routing/SKILL.md"]
                self.assertIn("references/task-routing.md", skill)
                method = package["skills/model-routing/references/task-routing.md"]
                for obligation in ("plan --request", "assign --plan", "--no-reply",
                                   "binding_proposal", "assignments[request_sha256]",
                                   "binding artifact", "caller-supplied",
                                   "model_override_supported", "effort_override_supported"):
                    self.assertIn(obligation, method)
                self.assertIn("human confirmation", method)
                self.assertIn("before each dispatch", method)
                self.assertNotIn("run_state.py", method)
                if host != "claude":
                    self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", method)
                self.assertIn("scripts/task_router.py", "\n".join(package))

    def test_preflight_reaches_the_owner_method_on_every_host(self):
        for host in operational.HOSTS:
            with self.subTest(host=host):
                package = self.render_in_memory("project-lifecycle", host)
                preflight = package["skills/lifecycle-method/references/preflight.md"]
                self.assertIn("task-routing.md", preflight)
                self.assertIn("environment.models", preflight)
                self.assertIn("confirmed", preflight)
                self.assertIn("environment.models.assignments", preflight)
                self.assertIn("run_state.py update", preflight)
                self.assertIn("--expected-revision", preflight)


if __name__ == "__main__":
    unittest.main()
