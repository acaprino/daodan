"""Generated catalogs cannot become inputs to their own next generation."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.daodan.adapter import HOSTS
from scripts.daodan_build import build_repository


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/daodan/valid/plugins/example"
CATALOGS = {
    "claude": ".claude-plugin/marketplace.json",
    "copilot": ".github/plugin/marketplace.json",
    "codex": ".agents/plugins/marketplace.json",
    "pi": "package.json",
    "opencode": "exports/opencode/package.json",
}


class CatalogGenerationAuthorityTests(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory(prefix="catalog-authority-",
                                             dir=os.environ.get("DAODAN_TEST_TMPDIR"))
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        shutil.copytree(ROOT / "adapters", self.root / "adapters")
        shutil.copytree(FIXTURE, self.root / "plugins/example")
        self.authority = {
            "name": "daodan",
            "metadata": {"version": "9.4.0", "description": "Authoritative fixture"},
            "plugins": [{"name": "example", "version": "0.0.1", "source": "./old/example"}],
        }
        self.write_catalog("claude", self.authority)

    def write_catalog(self, host, document):
        path = self.root / CATALOGS[host]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    def build(self, *, check=False):
        return build_repository(self.root, HOSTS, check=check)

    def catalog(self, host):
        return json.loads((self.root / CATALOGS[host]).read_text(encoding="utf-8"))

    def catalog_bytes(self):
        return {host: (self.root / relative).read_bytes() for host, relative in CATALOGS.items()}

    def assert_compiled_catalog(self, host):
        document = self.catalog(host)
        self.assertEqual(document["name"], "daodan")
        if host in {"claude", "copilot", "codex"}:
            self.assertEqual(document["metadata"]["version"], "9.4.0")
            entries = document["plugins"]
            names = [entry["name"] for entry in entries]
            self.assertEqual(len(names), len(set(names)), "Generated identities must be unique")
            self.assertEqual(names, ["example"])
            self.assertEqual(entries[0]["version"], "1.2.3")
            self.assertEqual(entries[0]["source"], f"./exports/{host}/plugins/example")
        elif host == "pi":
            self.assertEqual(document["version"], "9.4.0")
            self.assertNotIn("plugins", document)
            self.assertEqual(document["pi"]["skills"], ["./exports/pi/plugins/*/skills"])
        else:
            self.assertEqual(document["version"], "9.4.0")
            self.assertNotIn("plugins", document)
            self.assertEqual(set(document["daodan"]["plugins"]), {"example"})
            self.assertEqual(document["daodan"]["plugins"]["example"]["root"], "plugins/example")
            provenance = json.loads((self.root / "exports/opencode/plugins/example/.daodan-provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["version"], "1.2.3")

    def test_generated_residue_is_readonly_drift_then_repaired_and_idempotent(self):
        self.assertFalse(self.build().has_failures)
        for host in HOSTS:
            if host == "claude":
                continue
            stale = self.catalog(host)
            stale["name"] = "stale-host-identity"
            if "metadata" in stale:
                stale["metadata"]["version"] = "0.0.0"
            else:
                stale["version"] = "0.0.0"
            # Keep compiled fields in legacy-merge order, so check mode cannot
            # satisfy its drift assertion through formatting differences alone.
            for entry in stale.get("plugins", []):
                components = {key: entry.pop(key) for key in ("agents", "commands", "skills", "mcpServers") if key in entry}
                entry.update(components)
            stale.setdefault("plugins", []).extend([
                {"name": "duplicate-residue", "version": "3.0.0"},
                {"name": "duplicate-residue", "version": "16.7.0"},
            ])
            self.write_catalog(host, stale)
        before = self.catalog_bytes()

        checked = self.build(check=True)

        self.assertFalse(checked.issues)
        for host in HOSTS:
            if host != "claude":
                with self.subTest(host=host, phase="check"):
                    self.assertIn(self.root / CATALOGS[host], checked.drift)
        self.assertEqual(self.catalog_bytes(), before, "Check mode must preserve every catalog byte")
        self.assertFalse(self.build().has_failures)
        for host in HOSTS:
            with self.subTest(host=host, phase="publication"):
                self.assert_compiled_catalog(host)
        repaired = self.catalog_bytes()
        self.assertFalse(self.build(check=True).has_failures)
        self.assertFalse(self.build().has_failures)
        self.assertEqual(self.catalog_bytes(), repaired)

    def test_malformed_generated_catalogs_are_replaced_without_becoming_inputs(self):
        self.assertFalse(self.build().has_failures)
        for host in HOSTS:
            if host != "claude":
                (self.root / CATALOGS[host]).write_text("{not generated JSON", encoding="utf-8")

        self.assertFalse(self.build().has_failures)

        for host in HOSTS:
            with self.subTest(host=host):
                self.assert_compiled_catalog(host)

    def test_authoritative_claude_legacy_registration_survives_partial_migration(self):
        legacy = {"name": "foreign", "version": "7.0.0",
                  "source": {"source": "github", "repo": "someone/foreign"},
                  "agents": ["./old/worker.md"], "custom": {"keep": True}}
        self.authority["plugins"].insert(0, legacy)
        self.authority["custom"] = {"preserved": "Claude migration input"}
        self.write_catalog("claude", self.authority)

        self.assertFalse(self.build().has_failures)

        actual = self.catalog("claude")
        self.assertEqual(actual["metadata"], self.authority["metadata"])
        self.assertEqual(actual["custom"], self.authority["custom"])
        self.assertEqual(actual["plugins"][0], legacy)
        self.assertEqual([entry["name"] for entry in actual["plugins"]], ["foreign", "example"])
        self.assertEqual(actual["plugins"][1]["version"], "1.2.3")
        self.assertEqual(actual["plugins"][1]["source"], "./exports/claude/plugins/example")
        for host in HOSTS:
            if host != "claude":
                with self.subTest(host=host):
                    self.assert_compiled_catalog(host)


if __name__ == "__main__":
    unittest.main()
