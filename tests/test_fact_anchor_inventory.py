"""The anchor gate scans repository sources, including new and tracked ignored files."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts import lint_fact_anchors as linter


class AnchorInventoryTests(unittest.TestCase):
    def test_local_ignored_history_is_not_source_but_tracked_ignored_files_are(self):
        with tempfile.TemporaryDirectory(prefix="anchor-inventory-") as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            (root / ".gitignore").write_text("ignored/\n")
            (root / "owner.md").write_text("Current source")
            (root / "new.py").write_text("# New source")
            (root / "ignored").mkdir()
            (root / "ignored/kept.md").write_text("Shipped source")
            (root / "ignored/history.json").write_text('{"past":"not a current source"}')
            subprocess.run(["git", "-C", str(root), "add", "-f", "ignored/kept.md"], check=True, capture_output=True)
            before = Path.cwd()
            try:
                os.chdir(root)
                self.assertEqual({path.as_posix() for path in linter.scan_files()},
                                 {"owner.md", "new.py", "ignored/kept.md"})
            finally:
                os.chdir(before)


if __name__ == "__main__":
    unittest.main()
