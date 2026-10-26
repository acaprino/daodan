"""Exercise the published engine helper through every host package."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOSTS = ("claude", "codex", "copilot", "pi", "opencode")


class ExportedEngineTests(unittest.TestCase):
    def test_all_host_helpers_report_real_importers_and_callable_calls(self):
        with tempfile.TemporaryDirectory(prefix="map-export-") as directory:
            project = Path(directory)
            target = project / "core.py"
            target.write_text("def run():\n    return helper()\n", encoding="utf-8")
            (project / "app.py").write_text("from core import run\nrun()\n", encoding="utf-8")
            for host in HOSTS:
                with self.subTest(host=host):
                    helper = ROOT / "exports" / host / "plugins/codebase-map/skills/map-method/scripts/analyze_file.py"
                    result = subprocess.run(
                        [sys.executable, str(helper), "--file", str(target),
                         "--project-root", str(project), "--output-format", "json"],
                        capture_output=True, text=True,
                        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    analysis = json.loads(result.stdout)
                    self.assertEqual(analysis["imported_by_count"], 1)
                    self.assertEqual(analysis["classification"]["imported_by_count"], 1)
                    self.assertEqual(analysis["structure"]["functions"][0]["calls_made"], ["helper"])


if __name__ == "__main__":
    unittest.main()
