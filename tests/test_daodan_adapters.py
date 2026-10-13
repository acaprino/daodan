"""Capability-parity tests for the three peer harnesses."""

import sys
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import (  # noqa: E402
    HOSTS,
    AdapterError,
    CoordinationStrategy,
    load_adapter,
    resolve_support,
    select_coordination,
)
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"
VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"

STRATEGY_TABLE = {
    "parallel-subagents": CoordinationStrategy(
        "parallel-subagents", "baseline", True, True, False, False, "inline-prompt"
    ),
    "serial-isolated": CoordinationStrategy(
        "serial-isolated", "baseline", True, False, False, False, "inline-prompt"
    ),
    "single-context": CoordinationStrategy(
        "single-context", "baseline", False, False, False, False, "inline-prompt"
    ),
}


def load_example_plugin():
    return load_plugin(VALID)


def load_review_workflow():
    return load_example_plugin().workflows[0]


def adapter_with_strategies(*names: str):
    adapter = load_adapter(ADAPTERS, "codex")
    return replace(adapter, strategies=tuple(STRATEGY_TABLE[name] for name in names))


class AdapterParityTests(unittest.TestCase):
    def test_every_host_binds_every_registry_capability(self):
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ADAPTERS, host)
                self.assertEqual(set(adapter.bindings), set(CAPABILITY_REGISTRY))

    def test_example_plugin_is_supported_on_every_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                report = resolve_support(load_example_plugin(), load_adapter(ADAPTERS, host))
                self.assertIn(report.state, {"native", "adapted"})
                self.assertEqual(report.missing_capabilities, ())

    def test_required_capability_without_binding_is_unsupported(self):
        adapter = replace(load_adapter(ADAPTERS, "codex"), bindings={})
        report = resolve_support(load_example_plugin(), adapter)
        self.assertEqual(report.state, "unsupported")
        self.assertIn("repository.read", report.missing_capabilities)

    def test_optional_capability_never_hides_a_required_failure(self):
        adapter = load_adapter(ADAPTERS, "codex")
        bindings = dict(adapter.bindings)
        bindings["contexts.isolate"] = replace(bindings["contexts.isolate"], state="unsupported")
        report = resolve_support(load_example_plugin(), replace(adapter, bindings=bindings))
        self.assertEqual(report.state, "unsupported")

    def test_preferred_parallelism_can_fall_back_to_serial_isolation(self):
        adapter = adapter_with_strategies("serial-isolated")
        strategy = select_coordination(load_review_workflow(), adapter)
        self.assertEqual(strategy.name, "serial-isolated")
        self.assertTrue(strategy.isolated)
        self.assertFalse(strategy.parallel)

    def test_shared_context_cannot_satisfy_independent_review(self):
        adapter = adapter_with_strategies("single-context")
        self.assertIsNone(select_coordination(load_review_workflow(), adapter))

    def test_host_order_selects_the_first_viable_strategy(self):
        adapter = adapter_with_strategies("parallel-subagents", "serial-isolated")
        self.assertEqual(select_coordination(load_review_workflow(), adapter).name, "parallel-subagents")

    def test_required_concurrency_cannot_select_serial(self):
        workflow = load_review_workflow()
        phases = (replace(workflow.phases[0], concurrency="required"),)
        workflow = replace(workflow, phases=phases)
        self.assertIsNone(select_coordination(workflow, adapter_with_strategies("serial-isolated")))
        self.assertEqual(
            select_coordination(workflow, adapter_with_strategies("parallel-subagents")).name,
            "parallel-subagents",
        )

    def test_no_host_offers_a_single_context_fallback(self):
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ADAPTERS, host)
                self.assertTrue(all(strategy.isolated for strategy in adapter.strategies))


    def test_coordination_flags_reject_nonboolean_toml_values(self):
        """C09 requires typed capabilities rather than truthiness."""
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, True)
        adapters = temporary / "adapters"
        shutil.copytree(ADAPTERS / "codex", adapters / "codex")
        coordination = adapters / "codex/coordination.toml"
        original = coordination.read_text(encoding="utf-8")
        flags = {"isolated": "true", "parallel": "true",
                 "shared_tasks": "false", "peer_messaging": "false"}
        invalid_values = ('"false"', '"true"', '""', "0", "1", "0.5",
                          "[]", "[false]", "{ enabled = false }", "2026-10-12")
        for flag, old_value in flags.items():
            for invalid in invalid_values:
                with self.subTest(flag=flag, value=invalid):
                    coordination.write_text(original.replace(
                        f"{flag} = {old_value}", f"{flag} = {invalid}", 1),
                        encoding="utf-8")

                    with self.assertRaises(AdapterError) as caught:
                        load_adapter(adapters, "codex")

                    self.assertEqual(caught.exception.path, coordination)
                    self.assertIn(flag, caught.exception.message)
                    self.assertIn("boolean", caught.exception.message.lower())

    def test_coordination_flags_preserve_genuine_true_and_false(self):
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, True)
        adapters = temporary / "adapters"
        shutil.copytree(ADAPTERS / "codex", adapters / "codex")
        coordination = adapters / "codex/coordination.toml"
        original = coordination.read_text(encoding="utf-8")
        flags = {"isolated": "true", "parallel": "true",
                 "shared_tasks": "false", "peer_messaging": "false"}
        for flag, old_value in flags.items():
            for literal, expected in (("true", True), ("false", False)):
                with self.subTest(flag=flag, value=literal):
                    coordination.write_text(original.replace(
                        f"{flag} = {old_value}", f"{flag} = {literal}", 1),
                        encoding="utf-8")

                    adapter = load_adapter(adapters, "codex")

                    self.assertIs(getattr(adapter.strategies[0], flag), expected)
                    self.assertEqual(tuple(row.name for row in adapter.strategies),
                                     ("parallel-subagents", "serial-isolated"))


if __name__ == "__main__":
    unittest.main()
