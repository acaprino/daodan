"""New or missing exported commands are read-only compiler drift, not crashes."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.templates import render_path
from scripts.daodan_build import build_repository


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/daodan/valid/plugins/example"


class WorktreeBuildDriftTests(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory(prefix="daodan-command-drift-",
                                             dir=os.environ.get("DAODAN_TEST_TMPDIR"))
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        shutil.copytree(ROOT / "adapters", self.root / "adapters")
        shutil.copytree(FIXTURE, self.root / "plugins/example")
        self.assertFalse(build_repository(self.root, HOSTS, check=False).has_failures)

    def output_bytes(self):
        outputs = {path.relative_to(self.root): path.read_bytes()
                   for name in ("exports", ".claude-plugin", ".github", ".agents")
                   for path in (self.root / name).rglob("*") if path.is_file()}
        outputs[Path("package.json")] = (self.root / "package.json").read_bytes()
        return outputs

    def test_added_workflow_checks_without_reading_stale_live_components(self):
        kernel = self.root / "plugins/example"
        manifest = kernel / "plugin.toml"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace(
            'workflows = ["review"]', 'workflows = ["review", "worktrees"]'), encoding="utf-8")
        (kernel / "workflows/worktrees.md").write_bytes((kernel / "workflows/review.md").read_bytes())
        sidecar = (kernel / "workflows/review.toml").read_text(encoding="utf-8")
        (kernel / "workflows/worktrees.toml").write_text(
            sidecar.replace('name = "review"', 'name = "worktrees"').replace(
                'entrypoint = "review.md"', 'entrypoint = "worktrees.md"'), encoding="utf-8")
        before = self.output_bytes()

        checked = build_repository(self.root, HOSTS, check=True)

        self.assertFalse(checked.issues)
        for host in HOSTS:
            self.assertIn(self.root / f"exports/{host}/plugins/example", checked.drift)
        self.assertEqual(self.output_bytes(), before, "Checking must not publish partial outputs")
        self.assertFalse(build_repository(self.root, HOSTS, check=False).has_failures)
        for host in HOSTS:
            adapter = load_adapter(self.root / "adapters", host)
            relative = render_path(adapter.layout["workflows"], {"plugin": "example", "workflow": "worktrees"})
            self.assertTrue((self.root / f"exports/{host}/plugins/example" / relative).is_file())
        catalog = json.loads((self.root / "exports/opencode/package.json").read_text(encoding="utf-8"))
        commands = catalog["daodan"]["plugins"]["example"]["commands"]
        self.assertIn("example:worktrees", {command["name"] for command in commands})
        self.assertFalse(build_repository(self.root, HOSTS, check=True).has_failures)

    def test_missing_live_component_is_drift_and_check_preserves_its_absence(self):
        missing = self.root / "exports/opencode/plugins/example/commands/review.md"
        missing.unlink()
        before = self.output_bytes()

        checked = build_repository(self.root, HOSTS, check=True)

        self.assertFalse(checked.issues)
        self.assertIn(missing.parent.parent, checked.drift)
        self.assertFalse(missing.exists())
        self.assertEqual(self.output_bytes(), before)
        self.assertFalse(build_repository(self.root, HOSTS, check=False).has_failures)
        self.assertTrue(missing.is_file())
        self.assertFalse(build_repository(self.root, HOSTS, check=True).has_failures)


if __name__ == "__main__":
    unittest.main()
