"""The OpenCode pass of the registration linter, run against a broken copy."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LINTER = REPO_ROOT / "scripts/lint_plugin_registration.py"


class OpenCodeRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        for relative in (".claude-plugin", "plugins", "exports/claude", "exports/opencode", "exports/pi"):
            shutil.copytree(REPO_ROOT / relative, self.root / relative)
        shutil.copy(REPO_ROOT / "package.json", self.root / "package.json")
        self.manifest = self.root / "exports/opencode/package.json"

    def lint(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(LINTER)], cwd=self.root, capture_output=True, text=True
        )

    def test_live_tree_passes(self):
        result = self.lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ok    opencode manifest", result.stdout)

    def test_dangling_manifest_entry_fails(self):
        document = json.loads(self.manifest.read_text(encoding="utf-8"))
        target = next(
            name for name, entry in document["daodan"]["plugins"].items() if entry.get("agents")
        )
        document["daodan"]["plugins"][target]["agents"][0]["file"] = "agents/gone.md"
        self.manifest.write_text(json.dumps(document), encoding="utf-8")
        result = self.lint()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("agents/gone.md", result.stdout)

    def test_unregistered_component_fails(self):
        document = json.loads(self.manifest.read_text(encoding="utf-8"))
        target = next(
            name for name, entry in document["daodan"]["plugins"].items() if entry.get("commands")
        )
        extra = self.root / f"exports/opencode/plugins/{target}/commands/stray.md"
        extra.write_text("---\ndescription: x\n---\nx\n", encoding="utf-8")
        result = self.lint()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commands/stray.md", result.stdout)

    def test_dangling_routing_entry_fails(self):
        document = json.loads(self.manifest.read_text(encoding="utf-8"))
        target = next(iter(document["daodan"]["plugins"]))
        document["daodan"]["plugins"][target]["routing"] = "hooks/entry-routing.md"
        self.manifest.write_text(json.dumps(document), encoding="utf-8")
        result = self.lint()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dangling hooks/entry-routing.md", result.stdout)

    def test_unregistered_routing_file_fails(self):
        document = json.loads(self.manifest.read_text(encoding="utf-8"))
        target = next(iter(document["daodan"]["plugins"]))
        extra = self.root / f"exports/opencode/plugins/{target}/hooks/entry-routing.md"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("x\n", encoding="utf-8")
        result = self.lint()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unregistered hooks/entry-routing.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
