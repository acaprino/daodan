"""Worktree entry, delegated runtime and failure boundaries across host exports."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from scripts.daodan.templates import render_path


ROOT = Path(__file__).resolve().parents[1]


class WorktreeExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = {path.parent.name: load_plugin(path.parent)
                        for path in (ROOT / "plugins").glob("*/plugin.toml")}

    def test_every_host_ships_runtime_contract_and_resolvable_entry(self):
        with tempfile.TemporaryDirectory(prefix="daodan-worktree-exports-") as temporary:
            for host in HOSTS:
                with self.subTest(host=host):
                    adapter = load_adapter(ROOT / "adapters", host)
                    packages = {}
                    for name in ("worktree-manager", "daodan", "project-delivery"):
                        package = Path(temporary) / host / name
                        render_plugin(self.registry[name], adapter, package,
                                      adapters_root=ROOT / "adapters", plugin_registry=self.registry)
                        packages[name] = package
                    package = packages["worktree-manager"]
                    skill = package / render_path(adapter.layout["skills"],
                                                  {"plugin": "worktree-manager", "skill": "worktree-method"})
                    text = skill.read_text(encoding="utf-8")
                    self.assertIn("workspaces.py", text)
                    self.assertIn("work-controller:work-record", text)
                    for relative in ("scripts/workspaces.py", "scripts/worktrunk_runtime.py",
                                     "references/upstream.json", "references/upstream.md", "references/lifecycle.md",
                                     "references/runtime.toml", "references/no-hooks/README.md"):
                        self.assertTrue((skill.parent / relative).is_file(), (host, relative))
                    for source in (skill, skill.parent / "references/upstream.md"):
                        body = source.read_text(encoding="utf-8")
                        self.assertIn(adapter.layout["plugin_root_reference"], body)
                        if host != "claude":
                            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", body)
                    workflow = packages["daodan"] / render_path(adapter.layout["workflows"],
                                                               {"plugin": "daodan", "workflow": "worktrees"})
                    coordinator = workflow
                    if "coordinators" in adapter.layout:
                        coordinator = packages["daodan"] / render_path(
                            adapter.layout["coordinators"], {"plugin": "daodan", "workflow": "worktrees"})
                        self.assertIn("worktrees-coordinator", workflow.read_text(encoding="utf-8"))
                    harness = coordinator.read_text(encoding="utf-8")
                    self.assertIn("worktree-manager:worktree-method", harness)
                    self.assertIn("Execution harness", harness)
                    self.assertIn("senior-review", harness)
                    self.assertIn("isolated-worker", harness)
                    self.assertIn("delivery", harness)
                    self.assertFalse(list(package.rglob("*.exe")), "Provider binaries are not shipped")

    def test_worktrees_finish_composition_has_the_owners_full_worker_contract(self):
        workflows = {flow.name: flow for flow in self.registry["daodan"].workflows}
        worktrees, finish = workflows["worktrees"], workflows["finish-task"]
        self.assertEqual(worktrees.dispatch, finish.dispatch)
        self.assertTrue(worktrees.dispatch.isolated)
        self.assertTrue(worktrees.dispatch.inline_workers)
        self.assertEqual(worktrees.contract.shared_schemas, finish.contract.shared_schemas)

    def test_finish_route_requires_isolation_on_every_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ROOT / "adapters", host)
                bindings = dict(adapter.bindings)
                bindings["contexts.isolate"] = replace(bindings["contexts.isolate"], state="unsupported")
                support = resolve_support(self.registry["daodan"], replace(adapter, bindings=bindings))
                self.assertEqual(support.state, "unsupported")
                self.assertIn("contexts.isolate", support.missing_capabilities)

    def test_missing_shell_capability_blocks_all_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ROOT / "adapters", host)
                bindings = dict(adapter.bindings)
                bindings["shell.execute"] = replace(bindings["shell.execute"], state="unsupported")
                support = resolve_support(self.registry["worktree-manager"], replace(adapter, bindings=bindings))
                self.assertEqual(support.state, "unsupported")
                self.assertIn("shell.execute", support.missing_capabilities)

    def test_entry_and_delivery_require_the_workspace_owner(self):
        for name in ("daodan", "project-delivery"):
            with self.subTest(plugin=name):
                self.assertIn("worktree-manager", self.registry[name].required_dependencies)
        self.assertEqual(self.registry["worktree-manager"].required_dependencies, ("work-controller",))


if __name__ == "__main__":
    unittest.main()
