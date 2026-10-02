"""Structural tests for the disposable native-host protocol probes."""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.probe_host_marketplaces import (  # noqa: E402
    MARKETPLACE_PATH,
    PROBE_ROOT,
    validate_fixture,
)


class HostProbeFixtureTests(unittest.TestCase):
    def test_each_host_has_marketplace_and_plugin_manifest(self):
        expected = {
            "claude": (".claude-plugin/marketplace.json", ".claude-plugin/plugin.json"),
            "copilot": (".github/plugin/marketplace.json", "plugin.json"),
            "codex": (".agents/plugins/marketplace.json", ".codex-plugin/plugin.json"),
        }
        for host, (marketplace, manifest) in expected.items():
            root = REPO_ROOT / "tests/host-probes" / host
            self.assertTrue((root / marketplace).is_file(), f"{host}: {marketplace}")
            self.assertTrue((root / "plugins/probe" / manifest).is_file(), f"{host}: {manifest}")

    def test_every_fixture_validates(self):
        for host in ("claude", "copilot", "codex"):
            with self.subTest(host=host):
                self.assertEqual(validate_fixture(PROBE_ROOT / host, host), [])

    def test_every_fixture_declares_the_same_probe_identity(self):
        for host in ("claude", "copilot", "codex"):
            with self.subTest(host=host):
                catalog = json.loads(
                    (PROBE_ROOT / host / MARKETPLACE_PATH[host]).read_text(
                        encoding="utf-8"
                    )
                )
                entry = catalog["plugins"][0]
                self.assertEqual(entry["name"], "daodan-probe")
                self.assertEqual(entry["version"], "0.0.1")
                self.assertEqual(entry["source"], "./plugins/probe")

    def test_opencode_fixture_validates(self):
        self.assertEqual(validate_fixture(PROBE_ROOT / "opencode", "opencode"), [])

    def test_opencode_fixture_ships_the_real_loader(self):
        self.assertEqual(
            (PROBE_ROOT / "opencode/index.js").read_bytes(),
            (REPO_ROOT / "adapters/opencode/templates/index.js").read_bytes(),
        )

    def test_opencode_fixture_manifest_names_the_probe(self):
        document = json.loads((PROBE_ROOT / "opencode/package.json").read_text(encoding="utf-8"))
        self.assertEqual(document["name"], "daodan-probe")
        self.assertEqual(document["version"], "0.0.1")
        self.assertEqual(document["main"], "index.js")
        entry = document["daodan"]["plugins"]["probe"]
        self.assertEqual([a["id"] for a in entry["agents"]], ["probe:probe-worker"])
        self.assertEqual([c["name"] for c in entry["commands"]], ["probe:probe-team"])

    def test_readme_carries_the_evidence_table_header(self):
        readme = (PROBE_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "host | isolated workers | parallel fan-out | shared tasks | "
            "peer messaging | worker allowlist | packaged roles",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
