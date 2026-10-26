"""CLI composition and integrity-only behavior."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.cli import main
from work_controller.definition import load_definition
from work_controller.store import Store


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.home = root / "home"

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(["--workspace", str(self.workspace), "--home", str(self.home), *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_validate_does_not_create_runtime_state(self):
        definition = self.workspace / "analysis.yaml"
        code, _, errors = self.invoke(
            "compose", "--objective", "Analyze the contract", "--output", str(definition)
        )
        self.assertEqual((code, errors), (0, ""))
        other_home = self.home.parent / "validation-home"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main([
                "--workspace", str(self.workspace), "--home", str(other_home),
                "validate", str(definition),
            ])
        self.assertEqual(code, 0)
        self.assertFalse(other_home.exists())

    def test_interview_is_resumable_and_does_not_ask_twice(self):
        definition = self.workspace / "interview.yaml"
        args = (
            "interview", "--id", "contract-review", "--objective", "Review the API",
            "--archetype", "analysis", "--output", str(definition),
        )
        code, output, errors = self.invoke(*args)
        self.assertEqual((code, errors), (0, ""))
        self.assertIn('"status": "complete"', output)
        first = load_definition(definition)
        code, output, errors = self.invoke(*args)
        self.assertEqual((code, errors), (0, ""))
        self.assertIn('"status": "complete"', output)
        self.assertEqual(load_definition(definition).digest, first.digest)
        self.assertEqual(Store(self.home).interview("contract-review")["status"], "complete")

    def test_change_composer_preserves_argv(self):
        definition = self.workspace / "change.yaml"
        code, _, errors = self.invoke(
            "compose", "--objective", "Fix the parser", "--archetype", "change",
            "--target", "parser.py", "--verify", "python -m unittest discover -s tests",
            "--output", str(definition),
        )
        self.assertEqual((code, errors), (0, ""))
        data = load_definition(definition).data
        self.assertEqual(data["jobs"][1]["command"], {"argv": ["python", "-m", "unittest", "discover", "-s", "tests"]})

    def test_store_uses_legacy_database_only_when_new_one_is_absent(self):
        legacy_home = self.home.parent / "legacy-store"
        legacy_home.mkdir()
        legacy_path = legacy_home / "brain.db"
        legacy_path.touch()

        self.assertEqual(Store(legacy_home).path, legacy_path)
        self.assertTrue(legacy_path.exists())

        new_path = legacy_home / "process.db"
        new_path.touch()
        self.assertEqual(Store(legacy_home).path, new_path)
        self.assertTrue(legacy_path.exists())

    def test_default_home_requires_explicit_selection_of_legacy_directory(self):
        legacy_home = self.workspace / ".deadly-brain"
        legacy_home.mkdir()
        legacy_path = legacy_home / "brain.db"
        legacy_path.touch()
        stdout, stderr = io.StringIO(), io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main([
                "--workspace", str(self.workspace),
                "map-open", "--id", "legacy-home", "--destination", "Check selection",
            ])

        self.assertEqual(code, 1)
        self.assertIn("--home", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertTrue(legacy_path.exists())
        self.assertEqual(legacy_path.read_bytes(), b"")
        self.assertFalse((self.workspace / ".process-controller").exists())
        self.assertFalse((self.workspace / ".daodan").exists())

    def test_default_home_creates_the_shared_daodan_process_store(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main([
                "--workspace", str(self.workspace),
                "map-open", "--id", "shared-home", "--destination", "Use the shared home",
            ])

        self.assertEqual(code, 0)
        canonical_home = self.workspace / ".daodan" / "processes"
        self.assertTrue((canonical_home.parent / ".daodan-root").is_file())
        self.assertTrue((canonical_home / "process.db").is_file())
        self.assertEqual(Store(canonical_home).map_status("shared-home")["id"], "shared-home")
        self.assertFalse((self.workspace / ".process-controller").exists())
        self.assertFalse((self.workspace / ".deadly-brain").exists())

    def test_explicit_legacy_home_preserves_its_database_and_records(self):
        for directory, database in ((".deadly-brain", "brain.db"), (".process-controller", "process.db")):
            with self.subTest(home=directory):
                legacy_home = self.workspace / directory
                legacy_home.mkdir()
                legacy_path = legacy_home / database
                legacy_path.touch()
                Store(legacy_home).map_open("existing", "Preserve the old map")
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    code = main([
                        "--workspace", str(self.workspace), "--home", str(legacy_home),
                        "map-open", "--id", "resumed", "--destination", "Use explicit legacy home",
                    ])

                self.assertEqual(code, 0)
                self.assertEqual(Store(legacy_home).path, legacy_path)
                self.assertEqual(Store(legacy_home).map_status("existing")["id"], "existing")
                self.assertEqual(Store(legacy_home).map_status("resumed")["id"], "resumed")
                self.assertTrue(legacy_path.exists())
                if database == "brain.db":
                    self.assertFalse((legacy_home / "process.db").exists())
        self.assertFalse((self.workspace / ".daodan").exists())

    def test_competing_legacy_homes_are_not_chosen_or_merged(self):
        databases = []
        for directory, database in ((".deadly-brain", "brain.db"), (".process-controller", "process.db")):
            legacy_home = self.workspace / directory
            legacy_home.mkdir()
            path = legacy_home / database
            path.write_bytes(directory.encode("utf-8"))
            databases.append((path, path.read_bytes()))
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main([
                "--workspace", str(self.workspace),
                "map-open", "--id", "competing", "--destination", "Require an explicit selection",
            ])

        self.assertEqual(code, 1)
        self.assertIn("--home", stderr.getvalue())
        self.assertIn(".deadly-brain", stderr.getvalue())
        self.assertIn(".process-controller", stderr.getvalue())
        for path, before in databases:
            self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.workspace / ".daodan").exists())


if __name__ == "__main__":
    unittest.main()
