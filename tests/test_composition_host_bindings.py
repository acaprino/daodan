"""Host body fingerprints describe the bytes actually delivered to a worker."""
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from scripts.daodan.adapter import load_adapter
from scripts.daodan.overrides import OverrideSpec, source_digest, validate_override
from scripts.daodan.render import render_plugin, publish_plugin, RenderError
from scripts.daodan_build import discover_plugins, _override_outcomes

ROOT = Path(__file__).resolve().parents[1]


class EffectiveReviewerBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = {p.name: p for p in discover_plugins(ROOT)}

    def setUp(self):
        self.holder = tempfile.TemporaryDirectory()
        self.addCleanup(self.holder.cleanup)
        self.root = Path(self.holder.name)
        self.adapter = load_adapter(ROOT / "adapters", "claude")

    def override(self, provider, role):
        source = ROOT / "plugins" / provider / "roles" / f"{role}.md"
        directory = self.root / provider
        directory.mkdir()
        original = source.read_text(encoding="utf-8")
        (directory / "replacement.md").write_text(original + "\nHost-specific reviewed clarification.\n", encoding="utf-8")
        target = f"role:{role}"
        spec = OverrideSpec(directory, target, (source.relative_to(ROOT),), "Binding regression", "native-agents",
            source_digest([source], ROOT), tuple(_override_outcomes(self.registry[provider], target, self.registry)), (), Path("replacement.md"))
        declared = frozenset(self.registry[provider].capabilities.required + self.registry[provider].capabilities.optional)
        self.assertEqual(validate_override(spec, declared, declared_contracts=frozenset(spec.contracts_preserved), repository_root=ROOT), [])
        return spec

    def test_local_role_override_fingerprint_matches_the_published_file(self):
        override = self.override("senior-review", "security-auditor")
        output = self.root / "senior"
        render_plugin(self.registry["senior-review"], self.adapter, output, [override], ROOT / "adapters", self.registry)
        entries = json.loads((output / "skills/review-preparation/references/reviewer-catalog.json").read_text(encoding="utf-8"))["entries"]
        entry = next(e for e in entries if e["id"] == "senior-review:security-auditor")
        actual = "sha256:" + hashlib.sha256((output / entry["host_binding"]["file"]).read_bytes()).hexdigest()
        self.assertEqual(actual, entry["host_binding"]["sha256"])

    def test_foreign_role_override_fingerprint_follows_the_provider(self):
        override = self.override("react-development", "react-effects-auditor")
        provider_output = self.root / "react"
        render_plugin(self.registry["react-development"], self.adapter, provider_output, [override], ROOT / "adapters", self.registry)
        output = self.root / "senior"
        render_plugin(self.registry["senior-review"], self.adapter, output, adapters_root=ROOT / "adapters",
                      plugin_registry=self.registry, role_overrides={"react-development": [override]})
        entries = json.loads((output / "skills/review-preparation/references/reviewer-catalog.json").read_text(encoding="utf-8"))["entries"]
        entry = next(e for e in entries if e["id"] == "react-development:react-effects-auditor")
        actual = "sha256:" + hashlib.sha256((provider_output / entry["host_binding"]["file"]).read_bytes()).hexdigest()
        self.assertEqual(actual, entry["host_binding"]["sha256"])

    def test_unbound_host_specific_member_override_cannot_silently_enter_a_composition(self):
        override = self.override("react-development", "react-effects-auditor")
        plugin = self.registry["react-development"]
        plugin = replace(plugin, components=replace(plugin.components, roles=(*plugin.components.roles, "combined")),
                         reviewer_compositions=(("combined", ("react-development:react-effects-auditor",)),))
        registry = {**self.registry, plugin.name: plugin}
        live = self.root / "live"
        live.mkdir()
        (live / "sentinel").write_text("preserved", encoding="utf-8")
        with self.assertRaises(RenderError):
            publish_plugin(plugin, self.adapter, live, [override], ROOT / "adapters", registry)
        self.assertEqual([p.name for p in live.iterdir()], ["sentinel"])

    def test_opencode_catalog_registers_a_virtual_composition_with_member_permissions(self):
        from scripts.daodan.catalogs import render_catalog
        plugin = self.registry["react-development"]
        plugin = replace(plugin, components=replace(plugin.components, roles=(*plugin.components.roles, "combined")),
                         reviewer_compositions=(("combined", ("react-development:react-effects-auditor", "react-development:react-render-cost-auditor")),))
        registry = {**self.registry, plugin.name: plugin}
        adapter = load_adapter(ROOT / "adapters", "opencode")
        output = self.root / "opencode"
        render_plugin(plugin, adapter, output, adapters_root=ROOT / "adapters", plugin_registry=registry)
        document = json.loads(render_catalog("opencode", list(registry.values()), "1.0.0", {plugin.name: output}, layout=adapter.layout))
        entry = document["daodan"]["plugins"][plugin.name]
        role = next(a for a in entry["agents"] if a["id"] == "react-development:combined")
        self.assertIn("react-effects-auditor", role["description"])
        from scripts.daodan.render import opencode_permissions
        self.assertEqual(role["permissions"], opencode_permissions("Read, Write, Glob, Grep, Bash"))
        self.assertFalse(any(r["action"] == "subagent" and r["effect"] == "allow" for r in role["permissions"]))
