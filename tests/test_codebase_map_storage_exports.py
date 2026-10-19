"""Storage choices and bounded reading remain executable on every rendered host."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.load import load_plugin
from scripts.daodan.render import render_plugin
from host_binding_assertions import loaded_instruction_text

# Since 38.0.0 the map is started by the daodan entry `map-code`, which loads the
# method and names both entry units; the storage control is parsed by those units.
ENTRIES = {
    "claude": "commands/{name}.md",
    "copilot": "agents/{name}-coordinator.agent.md",
    "codex": "skills/{name}-workflow/SKILL.md",
    "pi": "prompts/daodan-{name}.md",
    "opencode": "commands/{name}.md",
}
UNITS = ("entry-analyze.md", "entry-team-analyze.md")


class StorageExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = {path.parent.name: load_plugin(path.parent) for path in (ROOT / "plugins").glob("*/plugin.toml")}

    def test_every_host_preserves_format_resolution_and_targeted_consumers(self):
        with tempfile.TemporaryDirectory(prefix="map-storage-exports-") as temporary:
            for host in HOSTS:
                with self.subTest(host=host):
                    adapter = load_adapter(ROOT / "adapters", host)
                    package = Path(temporary) / host / "codebase-map"
                    render_plugin(self.registry["codebase-map"], adapter, package,
                                  adapters_root=ROOT / "adapters", plugin_registry=self.registry)
                    entry = Path(temporary) / host / "daodan"
                    render_plugin(self.registry["daodan"], adapter, entry,
                                  adapters_root=ROOT / "adapters", plugin_registry=self.registry)
                    text = loaded_instruction_text(self, entry / ENTRIES[host].format(name="map-code"), host)
                    self.assertIn("codebase-map:map-method", text)
                    references = package / "skills/map-method/references"
                    for unit in UNITS:
                        self.assertIn(f"references/{unit}", text)
                        self.assertIn("--format sqlite|json", (references / unit).read_text(encoding="utf-8"))
                    snapshot = (references / "snapshot.md").read_text(encoding="utf-8")
                    self.assertIn("snapshot/manifest.sqlite", snapshot)
                    self.assertIn("--format json", snapshot)
                    self.assertIn("snapshot.py resolve", snapshot)
                    self.assertIn("state.json -> snapshot", snapshot)
                    evidence = (references / "evidence.md").read_text(encoding="utf-8")
                    self.assertIn('--snapshot "$source_manifest"', evidence)
                    self.assertIn("totals", evidence)
                    self.assertIn("truncated", evidence)
                    self.assertNotIn("Derive " + chr(96) + "source_manifest = $RUN_DIR/snapshot/manifest.json", evidence)


if __name__ == "__main__":
    unittest.main()
