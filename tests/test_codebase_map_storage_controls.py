"""Storage format is orthogonal to delivery, lineage and source freshness."""
from contextlib import redirect_stdout
import hashlib
import inspect
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import mcp_service
import snapshot


class BinaryRunTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-storage-controls-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "src"
        self.source.mkdir()
        (self.source / "one.py").write_text("def answer():\n    return 7\n")
        self.service = mcp_service.MapService(self.root)

    def api(self):
        self.assertIn("format", inspect.signature(self.service.create_run).parameters)

    def run_dir(self, run_id):
        return self.root / ".codebase-map/runs" / run_id

    def write(self, run_id, name, value="# Evidence\n"):
        path = self.run_dir(run_id) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def complete(self, run_id, *, publish=True):
        self.write(run_id, "knowledge/navigation.md")
        self.write(run_id, "knowledge/documentation-leads.md")
        for phase in (1, 2, 5, 7):
            self.write(run_id, snapshot.PHASE_FILES[phase - 1])
        self.assertTrue(snapshot.check_delivery(self.run_dir(run_id))["may_publish"])
        if publish:
            self.assertTrue(self.service.publish(run_id)["published"])

    def test_cli_resolves_declared_format_and_small_metadata(self):
        self.assertTrue(hasattr(snapshot, "cmd_resolve"), "run snapshot resolver must be available to shell workflows")
        for format in ("sqlite", "json"):
            with self.subTest(format=format):
                self.service.create_run("src", format, format=format)
                output = io.StringIO()
                with redirect_stdout(output):
                    code = snapshot.cmd_resolve(SimpleNamespace(run_dir=str(self.run_dir(format))))
                self.assertEqual(code, 0)
                value = json.loads(output.getvalue())
                self.assertEqual(value["format"], format)
                self.assertEqual(value["file_count"], 1)
                self.assertTrue(Path(value["path"]).is_file())
                self.assertNotIn("files", value["metadata"])
                self.assertIn("git", value["metadata"])

    def test_create_run_defaults_to_sqlite_and_format_is_not_analysis_flag(self):
        value = self.service.create_run("src", "example", depth="lite")
        self.assertEqual(value["state"].get("snapshot", {}).get("format"), "sqlite")
        self.assertNotIn("format", value["state"]["flags"])
        self.assertTrue((self.run_dir("example") / "snapshot/manifest.sqlite").is_file())
        self.assertFalse((self.run_dir("example") / "snapshot/manifest.json").exists())

    def test_parent_child_format_matrix_preserves_parent_bytes(self):
        self.api()
        for parent_format in ("json", "sqlite"):
            for child_format in ("json", "sqlite"):
                with self.subTest(parent=parent_format, child=child_format):
                    suffix = parent_format + "-" + child_format
                    parent, child = "parent-" + suffix, "child-" + suffix
                    self.service.create_run("src", parent, depth="lite", format=parent_format)
                    self.complete(parent)
                    parent_file = self.run_dir(parent) / ("snapshot/manifest." + parent_format)
                    before = hashlib.sha256(parent_file.read_bytes()).hexdigest()
                    self.service.create_run("src", child, depth="lite", format=child_format)
                    state_path = self.run_dir(child) / "state.json"
                    state = json.loads(state_path.read_text())
                    state.pop("delivery")
                    state["parent_run"] = parent
                    state_path.write_text(json.dumps(state))
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(snapshot.cmd_diff(SimpleNamespace(parent_run=self.run_dir(parent),
                            target=self.source, out=self.run_dir(child), verify=True, threshold=.4, flags=None)), 0)
                        self.assertEqual(snapshot.cmd_carry(SimpleNamespace(parent_run=self.run_dir(parent),
                            run_dir=self.run_dir(child))), 0)
                    self.service._command("prepare", self.run_dir(child))
                    self.complete(child, publish=False)
                    self.service.resume(child, phase=7)
                    self.assertTrue(self.service.publish(child)["published"])
                    self.assertEqual(hashlib.sha256(parent_file.read_bytes()).hexdigest(), before)

    def test_legacy_json_readable_but_changed_fingerprint_cannot_resume(self):
        self.api()
        self.service.create_run("src", "legacy", depth="lite", format="json")
        path = self.run_dir("legacy") / "state.json"
        state = json.loads(path.read_text())
        state.pop("snapshot")
        path.write_text(json.dumps(state))
        before = (self.run_dir("legacy") / "snapshot/manifest.json").read_bytes()
        self.assertTrue(self.service.status("legacy")["source_available"])
        with mock.patch.object(snapshot, "parser_fingerprint", return_value="changed"):
            with self.assertRaisesRegex(snapshot.RunControlError, "parser"):
                snapshot._bound_manifest(self.run_dir("legacy"), self.root / ".codebase-map", state, fresh=True)
        self.assertEqual((self.run_dir("legacy") / "snapshot/manifest.json").read_bytes(), before)

    def test_ambiguous_or_misdeclared_snapshot_rejected(self):
        self.api()
        self.service.create_run("src", "ambiguous", depth="lite")
        self.write("ambiguous", "snapshot/manifest.json", json.dumps(snapshot.build_manifest(self.source)))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.service.status("ambiguous")
        (self.run_dir("ambiguous") / "snapshot/manifest.json").unlink()
        state_path = self.run_dir("ambiguous") / "state.json"
        state = json.loads(state_path.read_text())
        state["snapshot"]["path"] = "../../outside.sqlite"
        state_path.write_text(json.dumps(state))
        with self.assertRaises(ValueError):
            self.service.status("ambiguous")

    def test_invalid_format_creates_no_run(self):
        self.api()
        with self.assertRaises(ValueError):
            self.service.create_run("src", "invalid", format="pickle")
        self.assertFalse(self.run_dir("invalid").exists())


if __name__ == "__main__":
    unittest.main()
