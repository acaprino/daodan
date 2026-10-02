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
        document["daodan"]["plugins"]["senior-review"]["agents"][0]["file"] = "agents/gone.md"
        self.manifest.write_text(json.dumps(document), encoding="utf-8")
        result = self.lint()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("agents/gone.md", result.stdout)

    def test_unregistered_component_fails(self):
        extra = self.root / "exports/opencode/plugins/senior-review/commands/stray.md"
        extra.write_text("---\ndescription: x\n---\nx\n", encoding="utf-8")
        result = self.lint()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commands/stray.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
