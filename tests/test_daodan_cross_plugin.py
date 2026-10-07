"""Installed-resource contracts for schema exports and external workers."""

import dataclasses
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.load import load_plugin
from scripts.daodan.model import DispatchSpec, ModelError
from scripts.daodan.render import render_plugin
from scripts.daodan.validate import CAPABILITY_REGISTRY, validate_plugins

FIXTURE = REPO_ROOT / "tests/fixtures/daodan/cross-plugin/plugins"
ADAPTERS = REPO_ROOT / "adapters"


class CrossPluginContractsTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp)
        shutil.copytree(FIXTURE, self.temp / "plugins")
        self.provider = load_plugin(self.temp / "plugins/provider")
        self.consumer = load_plugin(self.temp / "plugins/consumer")
        self.registry = {p.name: p for p in (self.provider, self.consumer)}

    def codes(self, consumer=None, provider=None):
        return {
            issue.code for issue in validate_plugins(
                [provider or self.provider, consumer or self.consumer], CAPABILITY_REGISTRY
            )
        }

    def test_exported_contract_and_shared_reference_load_and_validate(self):
        self.assertEqual(self.provider.contract_exports, (Path("contracts/result.toml"),))
        self.assertEqual(
            self.consumer.workflows[0].contract.shared_schemas,
            ("provider/contracts/result.toml",),
        )
        self.assertEqual(self.codes(), set())

    def test_external_role_must_exist_in_declared_provider(self):
        workflow = self.consumer.workflows[0]
        phase = dataclasses.replace(workflow.phases[1], role="provider/missing")
        consumer = dataclasses.replace(
            self.consumer, workflows=(dataclasses.replace(workflow, phases=(workflow.phases[0], phase)),)
        )
        self.assertIn("unknown-role", self.codes(consumer))

    def test_provider_must_be_a_hard_dependency(self):
        consumer = dataclasses.replace(self.consumer, required_dependencies=())
        self.assertIn("undeclared-dependency", self.codes(consumer))
        self.assertIn("undeclared-schema-provider", self.codes(consumer))

    def test_nonexported_schema_cannot_be_consumed(self):
        provider = dataclasses.replace(self.provider, contract_exports=())
        self.assertIn("unexported-shared-schema", self.codes(provider=provider))

    def test_exports_must_live_under_contracts(self):
        provider = dataclasses.replace(self.provider, contract_exports=(Path("roles/inspector.md"),))
        self.assertIn("invalid-contract-export", self.codes(provider=provider))

    def test_invocation_is_rejected_instead_of_ignored(self):
        workflow = self.consumer.workflows[0]
        phase = dataclasses.replace(workflow.phases[0], invoke="provider:inspect")
        consumer = dataclasses.replace(
            self.consumer, workflows=(dataclasses.replace(workflow, phases=(phase, workflow.phases[1])),)
        )
        self.assertIn("unsupported-workflow-invoke", self.codes(consumer))

    def test_exports_ship_only_in_provider_and_external_dispatch_is_bound(self):
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ADAPTERS, host)
                provider_out = self.temp / host / "provider"
                consumer_out = self.temp / host / "consumer"
                render_plugin(self.provider, adapter, provider_out, adapters_root=ADAPTERS,
                              plugin_registry=self.registry)
                render_plugin(self.consumer, adapter, consumer_out, adapters_root=ADAPTERS,
                              plugin_registry=self.registry)
                self.assertTrue((provider_out / "contracts/result.toml").is_file())
                self.assertFalse((consumer_out / "contracts/result.toml").exists())
                text = "\n".join(p.read_text(encoding="utf-8") for p in consumer_out.rglob("*.md"))
                self.assertIn("provider:inspector", text)
                self.assertNotIn("`provider/inspector`", text)
                if host in {"codex", "pi"}:
                    self.assertIn("contracts/dispatch/provider/inspector.md", text)
                    body = consumer_out / "contracts/dispatch/provider/inspector.md"
                    self.assertIn("PROVIDER_ROLE_BODY", body.read_text(encoding="utf-8"))
                    self.assertIn("provider:tools", body.read_text(encoding="utf-8"))
                    self.assertIn("<provider-plugin-root>/skills/tools/scripts/inspect.py", body.read_text(encoding="utf-8"))
                    self.assertNotIn("<plugin-root>/skills/tools/scripts/inspect.py", body.read_text(encoding="utf-8"))
                    self.assertTrue((provider_out / "skills/tools/scripts/inspect.py").is_file())
                if host == "copilot":
                    self.assertIn("agents: ['provider:inspector']", text)

    def test_inline_resource_changes_when_canonical_owner_changes(self):
        adapter = load_adapter(ADAPTERS, "codex")
        first = self.temp / "first"
        second = self.temp / "second"
        render_plugin(self.consumer, adapter, first, adapters_root=ADAPTERS, plugin_registry=self.registry)
        source = self.provider.root / "roles/inspector.md"
        source.write_text(source.read_text().replace("PROVIDER_ROLE_BODY", "CHANGED_ROLE_BODY"))
        render_plugin(self.consumer, adapter, second, adapters_root=ADAPTERS, plugin_registry=self.registry)
        resource = Path("contracts/dispatch/provider/inspector.md")
        self.assertNotEqual((first / resource).read_text(), (second / resource).read_text())
        self.assertIn("Owner: provider:inspector", (second / resource).read_text())

    def test_same_role_name_from_two_owners_has_distinct_bindings(self):
        other = dataclasses.replace(self.provider, name="second")
        workflow = self.consumer.workflows[0]
        phase = dataclasses.replace(workflow.phases[1], id="other", role="second/inspector")
        consumer = dataclasses.replace(
            self.consumer, required_dependencies=("provider", "second"),
            workflows=(dataclasses.replace(workflow, phases=(*workflow.phases, phase)),),
        )
        registry = {**self.registry, "second": other, "consumer": consumer}
        target = self.temp / "distinct"
        render_plugin(consumer, load_adapter(ADAPTERS, "codex"), target,
                      adapters_root=ADAPTERS, plugin_registry=registry)
        self.assertTrue((target / "contracts/dispatch/provider/inspector.md").is_file())
        self.assertTrue((target / "contracts/dispatch/second/inspector.md").is_file())
        text = (target / "skills/review-workflow/SKILL.md").read_text()
        self.assertIn("provider:inspector", text)
        self.assertIn("second:inspector", text)

    def test_shared_reference_rejects_traversal(self):
        workflow = self.consumer.workflows[0]
        changed = dataclasses.replace(workflow.contract, shared_schemas=("provider/contracts/../../roles/inspector.toml",))
        consumer = dataclasses.replace(self.consumer, workflows=(dataclasses.replace(workflow, contract=changed),))
        self.assertIn("invalid-shared-schema", self.codes(consumer))

    def test_composed_method_dispatch_loads_without_phase_role(self):
        sidecar = self.consumer.root / "workflows/review.toml"
        sidecar.write_text(sidecar.read_text() + '\n[dispatch]\nroles = ["provider/inspector"]\nisolated = true\ninline_workers = false\n')
        loaded = load_plugin(self.consumer.root)
        self.assertEqual(loaded.workflows[0].dispatch, DispatchSpec(("provider/inspector",), True, False))

    def test_composed_method_dispatch_has_closed_metadata_and_real_role_resolution(self):
        workflow = dataclasses.replace(self.consumer.workflows[0], dispatch=DispatchSpec(("provider/missing",), True))
        self.assertIn("unknown-role", self.codes(dataclasses.replace(self.consumer, workflows=(workflow,))))
        sidecar = self.consumer.root / "workflows/review.toml"
        sidecar.write_text(sidecar.read_text() + '\n[dispatch]\nroles = []\ninline_workers = ["verifier"]\n')
        with self.assertRaises(ModelError):
            load_plugin(self.consumer.root)

    def test_composed_method_only_dispatch_renders_complete_bindings(self):
        workflow = self.consumer.workflows[0]
        phases = tuple(dataclasses.replace(phase, role=None, fanout=(), fanout_from=None, isolation="shared")
                       for phase in workflow.phases)
        workflow = dataclasses.replace(workflow, phases=phases, dispatch=DispatchSpec(("provider/inspector",), True))
        consumer = dataclasses.replace(self.consumer, workflows=(workflow,))
        for host in HOSTS:
            target = self.temp / "composed" / host
            render_plugin(consumer, load_adapter(ADAPTERS, host), target, adapters_root=ADAPTERS,
                          plugin_registry={**self.registry, "consumer": consumer})
            text = "\n".join(path.read_text() for path in target.rglob("*.md"))
            self.assertIn("provider:inspector", text)
            self.assertIn("required", text)
            if host in {"codex", "pi"}:
                self.assertTrue((target / "contracts/dispatch/provider/inspector.md").is_file())
            if host == "copilot":
                self.assertIn("agents: ['provider:inspector']", text)

    def test_inline_workers_need_canonical_provider_and_only_its_one_role(self):
        workflow = dataclasses.replace(self.consumer.workflows[0], dispatch=DispatchSpec(inline_workers=True))
        consumer = dataclasses.replace(self.consumer, workflows=(workflow,))
        self.assertIn("undeclared-dependency", self.codes(consumer))
        protocol = load_plugin(REPO_ROOT / "plugins/project-protocol")
        consumer = dataclasses.replace(consumer, required_dependencies=("provider", "project-protocol"))
        registry = {**self.registry, "consumer": consumer, "project-protocol": protocol}
        self.assertEqual(validate_plugins(list(registry.values()), CAPABILITY_REGISTRY), [])
        for host in HOSTS:
            target = self.temp / "inline" / host
            render_plugin(consumer, load_adapter(ADAPTERS, host), target, adapters_root=ADAPTERS, plugin_registry=registry)
            text = "\n".join(path.read_text() for path in target.rglob("*.md"))
            self.assertIn("project-protocol:isolated-worker", text)
            self.assertIn("full task", text)


if __name__ == "__main__":
    unittest.main()
