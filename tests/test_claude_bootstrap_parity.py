"""Parity between the live Claude catalog and the generated Claude export.

Every component the marketplace registers must exist under the export at the
same relative path with the bytes produced from the canonical kernel and adapter.
Owned missing and altered exports prove that the comparison remains active after
the migration from copied bodies to compiled packages.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import load_adapter
from scripts.daodan.load import load_plugin
from scripts.daodan.overrides import load_overrides
from scripts.daodan.render import render_plugin

MARKETPLACE = REPO_ROOT / ".claude-plugin/marketplace.json"
EXPORT_ROOT = REPO_ROOT / "exports/claude/plugins"

COMPONENT_KEYS = ("agents", "skills", "commands", "hooks")


def load_marketplace() -> dict:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


def registered_files(plugin: dict, expected_root: Path) -> list[str]:
    """Expand the catalog's declared files from the freshly compiled package."""
    files: list[str] = []
    for key in COMPONENT_KEYS:
        for entry in plugin.get(key, []):
            reference = entry["source"] if isinstance(entry, dict) else entry
            relative = Path(reference.removeprefix("./"))
            candidate = expected_root / relative
            if candidate.is_dir():
                files.extend(item.relative_to(expected_root).as_posix()
                             for item in sorted(candidate.rglob("*"))
                             if item.is_file() and "__pycache__" not in item.parts)
            else:
                files.append(relative.as_posix())
    return files


def assert_compiled_components(case, plugin, expected_root, exported_root):
    components = registered_files(plugin, expected_root)
    case.assertTrue(components, f"no registered compiled components: {plugin['name']}")
    for component in components:
        expected, exported = expected_root / component, exported_root / component
        case.assertTrue(expected.is_file(), f"catalog names an absent compiled file: {expected}")
        case.assertTrue(exported.is_file(), f"missing export: {exported}")
        case.assertEqual(exported.read_bytes(), expected.read_bytes(), component)


class ClaudeBootstrapParityTests(unittest.TestCase):
    def test_bootstrap_export_matches_registered_components(self):
        registry = {path.name: load_plugin(path) for path in (REPO_ROOT / "plugins").iterdir()
                    if path.is_dir() and (path / "plugin.toml").is_file()}
        adapter = load_adapter(REPO_ROOT / "adapters", "claude")
        with tempfile.TemporaryDirectory(prefix="daodan-claude-parity-") as holder:
            for plugin in load_marketplace()["plugins"]:
                expected = Path(holder) / plugin["name"]
                override_root = REPO_ROOT / "adapters/claude/overrides" / plugin["name"]
                overrides = load_overrides(override_root) if override_root.is_dir() else ()
                render_plugin(registry[plugin["name"]], adapter, expected, overrides,
                              REPO_ROOT / "adapters", registry)

                assert_compiled_components(self, plugin, expected,
                                           EXPORT_ROOT / plugin["name"])


    def test_compiled_component_parity_detects_missing_and_altered_owned_exports(self):
        plugin = load_plugin(REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example")
        entry = {"name": "example", "agents": ["./agents/inspector.md"],
                 "commands": ["./commands/review.md"]}
        with tempfile.TemporaryDirectory(prefix="daodan-claude-parity-discrimination-") as holder:
            expected, exported = Path(holder) / "compiled", Path(holder) / "exported"
            render_plugin(plugin, load_adapter(REPO_ROOT / "adapters", "claude"), expected)
            shutil.copytree(expected, exported)
            component = exported / "agents/inspector.md"
            original = component.read_bytes()

            assert_compiled_components(self, entry, expected, exported)
            for defect in ("missing", "altered"):
                with self.subTest(defect=defect):
                    if defect == "missing":
                        component.unlink()
                    else:
                        component.write_bytes(b"corrupted registered component\n")
                    # A plain TestCase lets the raised mismatch be observed here,
                    # without recording an intentional nested subtest failure.
                    with self.assertRaises(AssertionError):
                        assert_compiled_components(unittest.TestCase(), entry, expected, exported)
                    component.write_bytes(original)

    def test_every_marketplace_source_points_at_the_export(self):
        for plugin in load_marketplace()["plugins"]:
            with self.subTest(plugin=plugin["name"]):
                self.assertEqual(
                    plugin["source"], f"./exports/claude/plugins/{plugin['name']}"
                )

    def test_every_exported_plugin_carries_a_native_manifest(self):
        for plugin in load_marketplace()["plugins"]:
            with self.subTest(plugin=plugin["name"]):
                manifest = EXPORT_ROOT / plugin["name"] / ".claude-plugin/plugin.json"
                self.assertTrue(manifest.is_file(), f"missing manifest: {manifest}")
                declared = json.loads(manifest.read_text(encoding="utf-8"))
                self.assertEqual(declared["name"], plugin["name"])
                self.assertEqual(declared["version"], plugin["version"])

    def test_the_catalog_still_lists_every_plugin_directory(self):
        registered = {plugin["name"] for plugin in load_marketplace()["plugins"]}
        on_disk = {
            path.name
            for path in (REPO_ROOT / "plugins").iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        self.assertEqual(registered, on_disk)

    def test_no_build_artifact_reached_the_export(self):
        for path in EXPORT_ROOT.rglob("*"):
            self.assertNotIn("__pycache__", path.parts)
            self.assertNotIn(path.suffix, {".pyc", ".pyo"})


if __name__ == "__main__":
    unittest.main()
