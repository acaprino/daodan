"""Operational invariants for lifecycle artifact retention."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/project-lifecycle/skills/lifecycle-method/scripts/artifacts.py"
spec = importlib.util.spec_from_file_location("lifecycle_artifacts", SCRIPT)
artifacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifacts)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ArtifactRetention(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.output = self.project / ".daodan"
        self.run = self.output / "runs" / "sample"
        self.run.mkdir(parents=True)
        (self.output / ".daodan-root").touch()
        (self.run / "work.json").write_text(json.dumps({
            "schema": "daodan/work/v1", "run_id": "sample",
            "project": {"root": str(self.project.resolve())},
            "output_root": str(self.output.resolve())
        }))
        self.data = self.run / "outputs" / "large.bin"
        self.data.parent.mkdir()
        self.data.write_bytes(b"reproducible-output" * 512)
        self.evidence = self.run / "evidence.txt"
        self.evidence.write_text("command, conditions, failure and result")
        self.manifest = self.run / "artifacts.json"
        self.manifest.write_text(json.dumps({
            "schema": "daodan/artifacts/v1", "run_id": "sample",
            "artifacts": [{
                "path": "outputs/large.bin", "owned_by": "sample",
                "sha256": digest(self.data), "classification": "reproducible-output",
                "status": "concluded", "reproduce": "repeat the recorded command"
            }]
        }))
        self.report = self.run / "summary.json"
        self.report.write_text(json.dumps({
            "schema": "daodan/evidence-summary/v1", "run_id": "sample",
            "summary": "Result checked against retained evidence.",
            "verification": {"status": "verified", "by": "coordinator"},
            "retained_evidence": [{"path": "evidence.txt", "sha256": digest(self.evidence)}],
            "required_artifacts": [], "unresolved": []
        }))

    def plan(self):
        return artifacts.make_plan(self.run, self.manifest, self.report)

    def grant(self):
        return {"run_id": "sample", "operation": "purge",
                "paths": ["outputs/large.bin"],
                "source": {"kind": "user", "reference": "explicit purge request"}}

    def test_quarantine_moves_without_claiming_freed_space_and_can_resume(self):
        plan = self.plan()
        result = artifacts.apply_plan(self.run, plan)
        self.assertEqual(result["bytes_deleted"], 0)
        self.assertEqual(result["bytes_moved"], len(b"reproducible-output" * 512))
        self.assertFalse(self.data.exists())
        self.assertTrue((self.run / "quarantine" / plan["plan_id"] / "outputs/large.bin").exists())
        self.assertEqual(artifacts.apply_plan(self.run, plan)["bytes_moved"], result["bytes_moved"])
        self.assertTrue(self.evidence.exists())

    def test_purge_requires_explicit_scoped_authorization(self):
        plan = self.plan()
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan, purge=True)
        wrong = self.grant()
        wrong["paths"] = ["different.bin"]
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan, purge=True, authorization=wrong)
        self.assertTrue(self.data.exists())
        result = artifacts.apply_plan(self.run, plan, purge=True, authorization=self.grant())
        self.assertEqual(result["bytes_deleted"], len(b"reproducible-output" * 512))
        self.assertEqual(result["bytes_moved"], 0)
        self.assertEqual(artifacts.apply_plan(self.run, plan, purge=True, authorization=self.grant()), result)

    def test_changed_output_rejected_before_any_mutation(self):
        plan = self.plan()
        self.data.write_bytes(b"new evidence from another execution")
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan, purge=True, authorization=self.grant())
        self.assertTrue(self.data.exists())

    def test_recorded_project_output_binding_is_required(self):
        record_path = self.run / "work.json"
        record = json.loads(record_path.read_text())
        record["output_root"] = str(self.project / "different")
        record_path.write_text(json.dumps(record))
        with self.assertRaises(artifacts.RetentionError):
            self.plan()
        self.assertTrue(self.data.exists())

    def test_missing_sentinel_blocks_retention(self):
        (self.output / ".daodan-root").unlink()
        with self.assertRaises(artifacts.RetentionError):
            self.plan()

    def test_ancestor_symlink_cannot_escape_recorded_project(self):
        import os
        import shutil
        external = Path(self.temp.name) / "outside-runs"
        original = self.output / "runs"
        shutil.move(str(original), str(external))
        try:
            os.symlink(external, original, target_is_directory=True)
        except OSError:
            self.skipTest("directory symlinks unavailable")
        with self.assertRaises(artifacts.RetentionError):
            self.plan()
        self.assertTrue((external / "sample/outputs/large.bin").exists())

    def test_changed_report_or_retained_evidence_blocks_apply(self):
        plan = self.plan()
        self.evidence.write_text("changed evidence")
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan)
        self.assertTrue(self.data.exists())

    def test_unresolved_problem_blocks_retention(self):
        report = json.loads(self.report.read_text())
        report["unresolved"] = ["the failing attempt still needs its raw output"]
        self.report.write_text(json.dumps(report))
        with self.assertRaises(artifacts.RetentionError):
            self.plan()

    def test_required_artifact_is_kept(self):
        report = json.loads(self.report.read_text())
        report["required_artifacts"] = ["outputs/large.bin"]
        self.report.write_text(json.dumps(report))
        plan = self.plan()
        self.assertEqual(plan["items"], [])
        self.assertEqual(plan["kept"][0]["path"], "outputs/large.bin")

    def test_uncertain_ownership_or_classification_is_kept(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["artifacts"][0]["classification"] = "unresolved-evidence"
        self.manifest.write_text(json.dumps(manifest))
        self.assertEqual(self.plan()["items"], [])
        manifest["artifacts"][0]["classification"] = "reproducible-output"
        manifest["artifacts"][0]["owned_by"] = "another-session"
        self.manifest.write_text(json.dumps(manifest))
        self.assertEqual(self.plan()["items"], [])

    def test_traversal_and_absolute_paths_rejected(self):
        for path in ("../outside.bin", str(self.data), "C:/elsewhere/file", "outputs/../evidence.txt",
                     "outputs//large.bin", "outputs/large.bin/", "outputs/large.bin."):
            manifest = json.loads(self.manifest.read_text())
            manifest["artifacts"][0]["path"] = path
            self.manifest.write_text(json.dumps(manifest))
            with self.assertRaises(artifacts.RetentionError, msg=path):
                self.plan()

    @unittest.skipUnless(__import__("os").name == "nt", "Windows path aliases")
    def test_case_alias_cannot_delete_required_evidence(self):
        report = json.loads(self.report.read_text())
        report["required_artifacts"] = ["outputs/LARGE.bin"]
        self.report.write_text(json.dumps(report))
        plan = self.plan()
        self.assertEqual(plan["items"], [])
        self.assertTrue(self.data.exists())

    def test_symlink_and_hardlink_rejected(self):
        import os
        link = self.run / "linked.bin"
        try:
            os.link(self.data, link)
        except OSError:
            self.skipTest("hardlinks unavailable")
        with self.assertRaises(artifacts.RetentionError):
            self.plan()

    def test_tampered_plan_rejected(self):
        plan = self.plan()
        plan["items"][0]["sha256"] = "0" * 64
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan)
        self.assertTrue(self.data.exists())

    def test_self_hashed_plan_cannot_add_unowned_or_control_files(self):
        plan = self.plan()
        plan["items"].append({"path": "work.json", "sha256": digest(self.run / "work.json"),
                              "size": (self.run / "work.json").stat().st_size,
                              "classification": "completed-output"})
        plan["plan_id"] = artifacts._json_hash({k: v for k, v in plan.items() if k != "plan_id"})
        grant = self.grant()
        grant["paths"].append("work.json")
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan, purge=True, authorization=grant)
        self.assertTrue(self.data.exists())
        self.assertTrue((self.run / "work.json").exists())

    def test_changed_summary_blocks_apply(self):
        plan = self.plan()
        self.report.write_text("{}")
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan)
        self.assertTrue(self.data.exists())

    def test_plan_output_preserves_required_evidence_and_existing_files(self):
        for name in ("retention-plan-proof.json", "retention-plan-other.json"):
            target = self.run / name
            target.write_bytes(b"original evidence")
            report = json.loads(self.report.read_text())
            report["required_artifacts"] = [name] if "proof" in name else []
            self.report.write_text(json.dumps(report))
            with self.assertRaises(artifacts.RetentionError):
                artifacts.save_plan(self.run, name, self.plan())
            self.assertEqual(target.read_bytes(), b"original evidence")

    def test_plan_output_is_created_once(self):
        plan = self.plan()
        artifacts.save_plan(self.run, "retention-plan.json", plan)
        self.assertEqual(json.loads((self.run / "retention-plan.json").read_text()), plan)
        with self.assertRaises(artifacts.RetentionError):
            artifacts.save_plan(self.run, "retention-plan.json", plan)

    def test_quarantine_never_overwrites_an_existing_file(self):
        plan = self.plan()
        target = self.run / "quarantine" / plan["plan_id"] / "outputs/large.bin"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"someone else's file")
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan)
        self.assertEqual(target.read_bytes(), b"someone else's file")
        self.assertTrue(self.data.exists())

    def test_interrupt_after_move_resumes_from_prepared_receipt(self):
        from unittest.mock import patch
        plan = self.plan()
        original = artifacts._write
        writes = 0
        def interrupt(root, path, record):
            nonlocal writes
            writes += 1
            if writes == 2:
                raise OSError("simulated interruption")
            return original(root, path, record)
        with patch.object(artifacts, "_write", side_effect=interrupt):
            with self.assertRaises(OSError):
                artifacts.apply_plan(self.run, plan)
        self.assertFalse(self.data.exists())
        result = artifacts.apply_plan(self.run, plan)
        self.assertEqual(result["bytes_moved"], len(b"reproducible-output" * 512))
        self.assertEqual(result["bytes_deleted"], 0)

    def test_new_output_after_retention_is_not_treated_as_an_old_target(self):
        plan = self.plan()
        artifacts.apply_plan(self.run, plan)
        self.data.write_bytes(b"new session output")
        with self.assertRaises(artifacts.RetentionError):
            artifacts.apply_plan(self.run, plan)
        self.assertEqual(self.data.read_bytes(), b"new session output")

if __name__ == "__main__":
    unittest.main()

