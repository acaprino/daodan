"""External optional providers stay outside required installation and dispatch."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.daodan.catalogs import merge_into_legacy, render_catalog
from scripts.daodan.load import load_plugin
from scripts.daodan.model import ModelError
from scripts.daodan.validate import validate_dependencies
from scripts.sync_plugin_docs import closure, reference


def _temp_dir():
    """Keep temporary files on the repository drive so relative links resolve."""
    return str(ROOT) if os.name == "nt" else None


class OptionalDependencyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=_temp_dir())
        self.addCleanup(self.temporary.cleanup)
        self.kernel = Path(self.temporary.name) / "example"
        shutil.copytree(ROOT / "tests/fixtures/daodan/valid/plugins/example", self.kernel)
        self.base = load_plugin(self.kernel)
        self.provider = "visual-guidance@external-marketplace"

    def load_optional(self, value):
        manifest = self.kernel / "plugin.toml"
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(text.replace("[dependencies]", f"[dependencies]\noptional = {value}"), encoding="utf-8")
        return load_plugin(self.kernel)

    def test_loader_accepts_optional_external_providers_without_requiring_them(self):
        plugin = self.load_optional(json.dumps([self.provider]))
        self.assertEqual(plugin.optional_dependencies, (self.provider,))
        self.assertEqual(plugin.required_dependencies, self.base.required_dependencies)
        self.assertEqual(validate_dependencies(plugin, {plugin.name: plugin}), [])
        self.assertEqual(closure(plugin.name, {plugin.name: plugin}), ([plugin.name], []))

    def test_loader_defaults_to_no_optional_dependencies(self):
        self.assertEqual(self.base.optional_dependencies, ())

    def test_loader_rejects_scalar_optional_dependency(self):
        with self.assertRaises(ModelError):
            self.load_optional(json.dumps(self.provider))

    def test_validation_rejects_local_malformed_duplicate_and_conflicting_providers(self):
        cases = [
            (("local-provider",), (), "invalid-optional-dependency"),
            (("local-provider@elsewhere",), (), "optional-local-dependency"),
            (("example@elsewhere",), (), "optional-local-dependency"),
            (("visual-guidance@",), (), "invalid-optional-dependency"),
            (("visual-guidance@one@two",), (), "invalid-optional-dependency"),
            ((self.provider, self.provider), (), "duplicate-optional-dependency"),
            ((self.provider,), (self.provider,), "conflicting-dependency"),
        ]
        for optional, required, expected in cases:
            with self.subTest(optional=optional, required=required):
                plugin = replace(self.base, optional_dependencies=optional, required_dependencies=required)
                registry = {plugin.name: plugin, "local-provider": replace(self.base, name="local-provider")}
                self.assertIn(expected, {issue.code for issue in validate_dependencies(plugin, registry)})

    def test_optional_provider_cannot_satisfy_a_required_worker_binding(self):
        workflow = replace(self.base.workflows[0], dispatch=replace(
            self.base.workflows[0].dispatch, roles=("visual-guidance/designer",), isolated=True,
        ))
        plugin = replace(self.base, optional_dependencies=(self.provider,), workflows=(workflow,))
        self.assertIn("undeclared-dependency", {issue.code for issue in validate_dependencies(plugin)})

    def test_catalogs_keep_optional_and_required_edges_separate(self):
        plugin = replace(self.base, required_dependencies=("required-tool@required-marketplace",),
                         optional_dependencies=(self.provider,))
        for host in ("claude", "codex", "copilot"):
            with self.subTest(host=host):
                catalog = json.loads(render_catalog(host, [plugin], "1.0.0"))
                entry = catalog["plugins"][0]
                self.assertEqual(entry["dependencies"], ["required-tool@required-marketplace"])
                self.assertEqual(entry["optionalDependencies"], [self.provider])
                self.assertEqual(catalog["allowCrossMarketplaceDependenciesOn"],
                                 ["external-marketplace", "required-marketplace"])
        for host in ("pi", "opencode"):
            with self.subTest(host=host):
                catalog = json.loads(render_catalog(host, [plugin], "1.0.0"))
                self.assertNotIn("optionalDependencies", catalog, "Foreign plugin IDs are not npm dependencies")
                if host == "opencode":
                    self.assertNotIn("dependencies", catalog["daodan"]["plugins"][plugin.name])

    def test_legacy_merge_removes_stale_required_and_optional_edges(self):
        optional = replace(self.base, optional_dependencies=(self.provider,))
        existing = {"plugins": [{"name": self.base.name, "dependencies": [self.provider],
                                  "optionalDependencies": ["old@marketplace"]}]}
        packages = {self.base.name: self.kernel}
        for host in ("claude", "codex", "copilot"):
            with self.subTest(host=host):
                merged = merge_into_legacy(existing, [optional], host, packages)
                self.assertEqual(merged["plugins"][0]["dependencies"], [])
                self.assertEqual(merged["plugins"][0]["optionalDependencies"], [self.provider])
                cleared = merge_into_legacy(merged, [self.base], host, packages)
                self.assertNotIn("optionalDependencies", cleared["plugins"][0])

    def test_documentation_separates_optional_providers_from_required_closure(self):
        plugin = replace(self.base, optional_dependencies=(self.provider,), workflows=(),
                         components=replace(self.base.components, roles=(), workflows=()))
        document = reference(plugin, {plugin.name: plugin}, {}, ROOT / "docs/plugins/example.md", ROOT)
        required, optional = document.split("### Optional external providers", 1)
        self.assertNotIn(self.provider, required)
        self.assertIn(self.provider, optional)
        self.assertIn("External closure (0)", required)


if __name__ == "__main__":
    unittest.main()
