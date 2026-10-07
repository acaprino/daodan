"""CLI behaviour tests for the Daodan compiler."""

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan_build import build_repository, main  # noqa: E402

VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


class CompilerCliTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        shutil.copytree(REPO_ROOT / "adapters", self.root / "adapters")
        shutil.copytree(VALID, self.root / "plugins/example")
        (self.root / "VERSION").write_text("1.0.0\n", encoding="utf-8")

    def run_cli(self, *arguments) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            code = main([*arguments, "--root", str(self.root)])
        return code, out.getvalue()

    def test_publication_then_check_is_clean(self):
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.run_cli("--check")[0], 0)

    def test_check_reports_drift_after_a_kernel_edit(self):
        self.assertEqual(self.run_cli()[0], 0)
        role = self.root / "plugins/example/roles/inspector.md"
        role.write_text(role.read_text(encoding="utf-8") + "\nEdited.\n", encoding="utf-8")
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("generated-drift", output)

    def test_check_reports_drift_when_output_is_missing(self):
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("generated-drift", output)

    def test_partial_publication_is_an_invocation_error(self):
        code, output = self.run_cli("--host", "claude")
        self.assertEqual(code, 2)
        self.assertIn("together", output)

    def test_partial_host_is_allowed_under_check(self):
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.run_cli("--check", "--host", "claude")[0], 0)

    def test_validation_failure_writes_nothing(self):
        manifest = self.root / "plugins/example/plugin.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                '"repository.read"', '"telepathy.read"'
            ),
            encoding="utf-8",
        )
        code, output = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("unknown-capability", output)
        self.assertFalse((self.root / "exports").exists())

    def test_all_three_hosts_are_published_together(self):
        self.assertEqual(self.run_cli()[0], 0)
        for host in ("claude", "copilot", "codex"):
            self.assertTrue((self.root / "exports" / host / "plugins/example").is_dir())
        self.assertTrue((self.root / ".claude-plugin/marketplace.json").is_file())
        self.assertTrue((self.root / ".github/plugin/marketplace.json").is_file())
        self.assertTrue((self.root / ".agents/plugins/marketplace.json").is_file())

    def test_opencode_package_ships_the_loader_and_its_manifest(self):
        self.assertEqual(self.run_cli()[0], 0)
        package = self.root / "exports/opencode"
        self.assertEqual(
            (package / "index.js").read_bytes(),
            (self.root / "adapters/opencode/templates/index.js").read_bytes(),
        )
        self.assertTrue((package / "package.json").is_file())
        self.assertTrue((package / "plugins/example/agents/inspector.md").is_file())

    def test_check_reports_drift_when_the_loader_is_edited(self):
        self.assertEqual(self.run_cli()[0], 0)
        loader = self.root / "exports/opencode/index.js"
        loader.write_text(loader.read_text(encoding="utf-8") + "// edited" + chr(10), encoding="utf-8")
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("index.js", output)

    def test_support_table_names_every_host(self):
        report = build_repository(self.root, ("claude", "copilot", "codex"), check=True)
        self.assertEqual({item.host for item in report.support}, {"claude", "copilot", "codex"})

    def test_retired_generated_plugin_is_drift_then_removed_on_every_host(self):
        self.assertEqual(self.run_cli()[0], 0)
        shutil.rmtree(self.root / "plugins/example")
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("plugins/example", output.replace("\\", "/"))
        code, output = self.run_cli()
        self.assertEqual(code, 0, output)
        for host in ("claude", "copilot", "codex", "pi", "opencode"):
            self.assertFalse((self.root / "exports" / host / "plugins/example").exists())
        self.assertEqual(self.run_cli("--check")[0], 0)

    def test_failed_validation_preserves_retired_and_current_outputs(self):
        self.assertEqual(self.run_cli()[0], 0)
        shutil.copytree(VALID, self.root / "plugins/remaining")
        manifest = self.root / "plugins/remaining/plugin.toml"
        manifest.write_text(manifest.read_text().replace('name = "example"', 'name = "remaining"')
                            .replace('"repository.read"', '"telepathy.read"'))
        shutil.rmtree(self.root / "plugins/example")
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*")
                  if path.is_file() and "plugins" not in path.relative_to(self.root).parts[:1]}
        self.assertEqual(self.run_cli()[0], 1)
        for path, content in before.items():
            self.assertEqual((self.root / path).read_bytes(), content)
        for host in ("claude", "copilot", "codex", "pi", "opencode"):
            self.assertTrue((self.root / "exports" / host / "plugins/example").is_dir())

    def test_unknown_or_mismatched_output_directory_is_never_pruned(self):
        self.assertEqual(self.run_cli()[0], 0)
        unknown = self.root / "exports/claude/plugins/user-files"
        unknown.mkdir()
        (unknown / "important.txt").write_text("preserve")
        self.assertEqual(self.run_cli()[0], 1)
        self.assertEqual((unknown / "important.txt").read_text(), "preserve")

    def test_mismatched_provenance_cannot_authorize_retirement(self):
        self.assertEqual(self.run_cli()[0], 0)
        shutil.rmtree(self.root / "plugins/example")
        provenance = self.root / "exports/claude/plugins/example/.daodan-provenance.json"
        document = json.loads(provenance.read_text())
        document["host"] = "codex"
        provenance.write_text(json.dumps(document))
        code, output = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("unsafe-generated-output", output)
        for host in ("claude", "copilot", "codex", "pi", "opencode"):
            self.assertTrue((self.root / "exports" / host / "plugins/example").is_dir())

    def test_linked_output_root_is_refused_without_touching_target(self):
        self.assertEqual(self.run_cli()[0], 0)
        generated = self.root / "exports/claude/plugins"
        target = self.root / "outside-generated"
        shutil.move(generated, target)
        try:
            generated.symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        before = {path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}
        self.assertEqual(self.run_cli()[0], 1)
        self.assertEqual({path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
