"""Unit contract for version-bump validation at the CLI entry seam.

Git is the controlled external boundary; version classification, manifest parsing,
changed-path ownership and diagnostics execute through the real main().
"""

import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import check_version_bumps as checker  # noqa: E402

MISSING = object()


def manifest(plugin_version="1.0.0", marketplace_version="1.0.0", *, registered=True):
    metadata = {}
    if marketplace_version is not MISSING:
        metadata["version"] = marketplace_version
    plugins = []
    if registered:
        plugin = {"name": "example", "source": "./exports/claude/plugins/example"}
        if plugin_version is not MISSING:
            plugin["version"] = plugin_version
        plugins.append(plugin)
    return {"metadata": metadata, "plugins": plugins}


class VersionBumpTests(unittest.TestCase):
    def run_check(self, before, after, *, changed=("plugins/example/roles/review.md",),
                  directory_present=True):
        """Supply revision facts at Git's subprocess boundary, without real Git."""
        snapshots = {"BASE": before, "HEAD": after}

        def git_boundary(command, **kwargs):
            if command[0] != "git":
                self.fail(f"unexpected executable: {command}")
            if command[1] == "diff":
                return subprocess.CompletedProcess(command, 0, "\n".join(changed), "")
            if command[1] == "show":
                revision, path = command[2].split(":", 1)
                self.assertEqual(path, ".claude-plugin/marketplace.json")
                return subprocess.CompletedProcess(command, 0, json.dumps(snapshots[revision]), "")
            if command[1] == "ls-tree":
                output = "040000 tree fixture\tplugins/example\n" if directory_present else ""
                return subprocess.CompletedProcess(command, 0, output, "")
            self.fail(f"unexpected Git operation: {command}")

        stdout = io.StringIO()
        with patch.object(checker.subprocess, "run", side_effect=git_boundary), \
                patch.object(sys, "argv", ["check_version_bumps.py", "BASE", "HEAD"]), \
                contextlib.redirect_stdout(stdout):
            try:
                checker.main()
            except SystemExit as exit_signal:
                code = exit_signal.code
            else:
                code = 0
        return code, stdout.getvalue()

    def test_existing_plugin_accepts_numeric_patch_minor_and_major_increases(self):
        # Explicit accepted pairs, independently specified by the C11 contract.
        pairs = (("1.0.0", "1.0.1"), ("1.9.9", "1.10.0"), ("1.99.99", "2.0.0"))
        for old, new in pairs:
            with self.subTest(before=old, after=new):
                before = manifest(old, "3.0.0")
                after = manifest(new, "3.0.1")

                code, output = self.run_check(before, after)

                self.assertEqual(code, 0, output)
                self.assertIn("ok    version bumps", output)

    def test_marketplace_accepts_numeric_patch_minor_and_major_increases(self):
        pairs = (("1.0.0", "1.0.1"), ("1.9.9", "1.10.0"), ("1.99.99", "2.0.0"))
        for old, new in pairs:
            with self.subTest(before=old, after=new):
                before = manifest("4.0.0", old)
                after = manifest("4.0.1", new)

                code, output = self.run_check(before, after)

                self.assertEqual(code, 0, output)
                self.assertIn("ok    version bumps", output)

    def test_existing_plugin_rejects_equality_and_numeric_downgrades(self):
        pairs = (("1.0.0", "1.0.0"), ("1.0.1", "1.0.0"),
                 ("1.10.0", "1.9.9"), ("2.0.0", "1.99.99"))
        for old, new in pairs:
            with self.subTest(before=old, after=new):
                before = manifest(old, "3.0.0")
                after = manifest(new, "3.0.1")

                code, output = self.run_check(before, after)

                self.assertEqual(code, 1, output)
                self.assertIn("plugins/example", output)

    def test_marketplace_rejects_equality_and_numeric_downgrades(self):
        pairs = (("1.0.0", "1.0.0"), ("1.0.1", "1.0.0"),
                 ("1.10.0", "1.9.9"), ("2.0.0", "1.99.99"))
        for old, new in pairs:
            with self.subTest(before=old, after=new):
                before = manifest("4.0.0", old)
                after = manifest("4.0.1", new)

                code, output = self.run_check(before, after)

                self.assertEqual(code, 1, output)
                self.assertIn("metadata.version", output)

    def test_existing_plugin_rejects_malformed_or_missing_head_version(self):
        bad_versions = ("v1.0.1", "1.0", "1.0.1-rc", "1.0.1.0", "-1.0.1", 2, None, MISSING)
        for bad in bad_versions:
            with self.subTest(version="<missing>" if bad is MISSING else repr(bad)):
                before = manifest("1.0.0", "3.0.0")
                after = manifest(bad, "3.0.1")

                code, output = self.run_check(before, after)

                self.assertEqual(code, 1, output)
                self.assertIn("plugins/example", output)

    def test_existing_plugin_rejects_malformed_or_missing_base_version(self):
        for bad in ("broken", None, MISSING):
            with self.subTest(version="<missing>" if bad is MISSING else repr(bad)):
                before = manifest(bad, "3.0.0")
                after = manifest("1.0.1", "3.0.1")

                code, output = self.run_check(before, after)

                self.assertEqual(code, 1, output)
                self.assertIn("plugins/example", output)

    def test_marketplace_rejects_malformed_or_missing_head_version(self):
        bad_versions = ("v1.0.1", "1.0", "1.0.1-rc", "1.0.1.0", "-1.0.1", 2, None, MISSING)
        for bad in bad_versions:
            with self.subTest(version="<missing>" if bad is MISSING else repr(bad)):
                before = manifest("4.0.0", "1.0.0")
                after = manifest("4.0.1", bad)

                code, output = self.run_check(before, after)

                self.assertEqual(code, 1, output)
                self.assertIn("metadata.version", output)

    def test_marketplace_rejects_malformed_or_missing_base_version(self):
        for bad in ("broken", None, MISSING):
            with self.subTest(version="<missing>" if bad is MISSING else repr(bad)):
                before = manifest("4.0.0", bad)
                after = manifest("4.0.1", "1.0.1")

                code, output = self.run_check(before, after)

                self.assertEqual(code, 1, output)
                self.assertIn("metadata.version", output)

    def test_new_registered_plugin_needs_no_preexisting_plugin_version(self):
        before = manifest(marketplace_version="3.0.0", registered=False)
        after = manifest("1.0.0", "3.0.1")

        code, output = self.run_check(before, after)

        self.assertEqual(code, 0, output)

    def test_removed_plugin_with_no_remaining_directory_is_allowed(self):
        before = manifest("1.0.0", "3.0.0")
        after = manifest(marketplace_version="3.0.1", registered=False)

        code, output = self.run_check(before, after, directory_present=False)

        self.assertEqual(code, 0, output)

    def test_unregistered_plugin_with_remaining_directory_is_rejected(self):
        before = manifest("1.0.0", "3.0.0")
        after = manifest(marketplace_version="3.0.1", registered=False)

        code, output = self.run_check(before, after, directory_present=True)

        self.assertEqual(code, 1, output)
        self.assertIn("not registered", output)

    def test_no_plugin_changes_need_no_version_increment(self):
        before = manifest("1.0.0", "3.0.0")
        after = manifest("1.0.0", "3.0.0")

        code, output = self.run_check(before, after, changed=())

        self.assertEqual(code, 0, output)
        self.assertIn("no plugin changes", output)


if __name__ == "__main__":
    unittest.main()
