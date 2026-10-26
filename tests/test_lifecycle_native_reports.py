"""Contract with the native workspace output and honest delivery wrappers."""
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("native_reports", ROOT / "plugins/project-lifecycle/skills/lifecycle-method/scripts/native_reports.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeReportContract(unittest.TestCase):
    def test_workspace_converter_tracks_canonical_output_vocabulary(self):
        text = (ROOT / "plugins/repo-hygiene/roles/workspace-auditor.md").read_text(encoding="utf-8")
        line = re.search(r"disposition:\s+([^\n]+)", text).group(1)
        values = {part.strip() for part in line.split("|")}
        self.assertEqual(set(native.WORKSPACE_DISPOSITIONS), values)
        for disposition in values:
            mapped = native.workspace_decision(disposition)
            self.assertEqual(mapped["native_disposition"], disposition)
        self.assertFalse(native.workspace_decision("REPORT-ONLY")["executable"])
        self.assertFalse(native.workspace_decision("REVIEW")["executable"])

    def test_unknown_native_format_is_not_silently_retired(self):
        with self.assertRaises(ValueError):
            native.workspace_decision("DELETE")

    def test_missing_report_cannot_count_as_delivered(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                native.wrap(Path(temp) / "absent", role="testing:test-suite-auditor",
                            role_version="3.0.0", input_sha256="a" * 64,
                            status="delivered", scope={"paths": ["tests"]}, gaps=[])
            wrapped = native.wrap(Path(temp) / "absent", role="testing:test-suite-auditor",
                                  role_version="3.0.0", input_sha256="a" * 64,
                                  status="failed", scope={"paths": ["tests"]},
                                  gaps=["runner absent"])
            self.assertIsNone(wrapped["raw_report"])
            self.assertEqual(wrapped["status"], "failed")

    def test_raw_report_is_preserved_and_fingerprinted(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.md"
            path.write_bytes(b"Native finding with inherited premise")
            wrapped = native.wrap(path, role="senior-review:cleanup-auditor",
                                  role_version="13.0.0", input_sha256="b" * 64,
                                  status="delivered", scope={"paths": ["."]}, gaps=[])
            self.assertEqual(path.read_bytes(), b"Native finding with inherited premise")
            self.assertEqual(len(wrapped["raw_report"]["sha256"]), 64)
            self.assertNotIn("findings", wrapped)

