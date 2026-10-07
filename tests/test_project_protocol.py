"""Behavioral tests of persisted work, rather than prompt wording."""

import json
import contextlib
import io
import os
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/project-protocol/skills/project-protocol/scripts/run_state.py"


class ProjectProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(self.remove_temp)
        self.project = self.temp / "project"
        self.project.mkdir()
        (self.project / "app.py").write_text("print('original')\n", encoding="utf-8")
        self.payload = {
            "operation": "assess", "objective": "Find existing debt",
            "scope": {"paths": ["app.py"], "focus": "all"},
            "authorizations": {"mode": "read-only"},
            "budget": {"max_workers": 2},
            "phases": {"audit": {"status": "pending"}},
            "plan": [], "deliveries": {"audit": {"status": "pending"}},
            "required_gates": [],
        }
        self.payload_counter = 0
        self.runtime = runpy.run_path(str(SCRIPT)) if SCRIPT.is_file() else None

    def remove_temp(self):
        def writable_remove(function, path, _error):
            os.chmod(path, stat.S_IWRITE)
            function(path)
        self.assertTrue(self.temp.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()))
        shutil.rmtree(self.temp, onerror=writable_remove)

    def invoke(self, command, payload=None, extra=(), ok=True):
        self.assertTrue(SCRIPT.is_file(), "The protocol CLI must ship with its skill")
        args = [sys.executable, str(SCRIPT), command, "--project", str(self.project),
                "--run-id", "test-run", *extra]
        if payload is not None:
            self.payload_counter += 1
            path = self.temp / f"payload-{self.payload_counter}.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            args += ["--payload", str(path)]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.runtime["main"](args[2:])
        result = subprocess.CompletedProcess(args, code, stdout.getvalue(), stderr.getvalue())
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def init(self, extra=()):
        return self.invoke("init", self.payload, extra)

    def report(self, name="audit.md"):
        path = self.project / ".daodan/runs/test-run" / name
        path.write_text("Audit delivered, including an explicit no-findings result.\n")
        return name

    def git(self, *arguments):
        result = subprocess.run(["git", "-C", str(self.project), *arguments],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def committed_project(self):
        self.git("init")
        self.git("config", "user.name", "Protocol Test")
        self.git("config", "user.email", "protocol@example.invalid")
        self.git("config", "core.autocrlf", "false")
        self.git("add", "app.py")
        self.git("commit", "-m", "Initial candidate")

    def remote_completion(self, record):
        candidate = record["candidate"]
        return {"status": "complete", "phases": {"audit": {"status": "complete"}},
                "deliveries": {"audit": {"status": "delivered", "output": self.report()}},
                "gates": {"remote": {"status": "passed", "snapshot": candidate["snapshot"]["digest"],
                                      "head": candidate["head"], "evidence": {"job": "ci-job", "attempt": "1",
                                      "source_revision": candidate["head"]}}}}

    def test_init_materializes_snapshot_and_sentinel_without_touching_source(self):
        record = self.init()
        self.assertEqual(record["revision"], 0)
        self.assertEqual(record["schema"], "daodan/work/v1")
        self.assertEqual(record["status"], "in_progress")
        self.assertIn("app.py", record["project"]["snapshot"]["files"])
        self.assertTrue((self.project / ".daodan/.daodan-root").is_file())
        self.assertEqual((self.project / "app.py").read_text(), "print('original')\n")

    def test_old_revision_cannot_overwrite_new_work(self):
        self.init()
        updated = self.invoke("update", {"interruption": {"reason": "worker stopped"}},
                              ("--expected-revision", "0"))
        self.assertEqual(updated["revision"], 1)
        failure = self.invoke("update", {"interruption": None},
                              ("--expected-revision", "0"), ok=False)
        self.assertIn("revision", failure.stderr)
        self.assertEqual(self.invoke("show")["interruption"]["reason"], "worker stopped")

    def test_same_snapshot_and_authorization_can_resume(self):
        original = self.init()
        resumed = self.invoke("resume", {"authorizations": self.payload["authorizations"]})
        self.assertEqual(resumed["run_id"], original["run_id"])
        self.assertIn("audit", resumed["pending_deliveries"])

    def test_changed_dirty_input_rejects_resume_even_without_head_change(self):
        self.init()
        (self.project / "app.py").write_text("print('changed')\n")
        failure = self.invoke("resume", {"authorizations": self.payload["authorizations"]}, ok=False)
        self.assertIn("snapshot", failure.stderr)

    def test_resume_does_not_invent_missing_authorization(self):
        self.init()
        self.invoke("resume", {"authorizations": {}}, ok=False)

    def test_completion_rejects_missing_worker_and_does_not_corrupt_work(self):
        self.init()
        self.invoke("update", {"status": "complete"}, ("--expected-revision", "0"), ok=False)
        self.assertEqual(self.invoke("show")["revision"], 0)

    def test_completion_rejects_failed_worker_as_success(self):
        self.init()
        self.invoke("update", {"status": "complete", "phases": {"audit": {"status": "complete"}},
                              "deliveries": {"audit": {"status": "failed", "reason": "timeout"}}},
                    ("--expected-revision", "0"), ok=False)

    def test_completion_requires_correlated_gates(self):
        self.payload["required_gates"] = ["tests"]
        record = self.init()
        patch = {"status": "complete", "phases": {"audit": {"status": "complete"}},
                 "deliveries": {"audit": {"status": "delivered", "output": "audit.md"}},
                 "gates": {"tests": {"status": "passed", "snapshot": "old-success"}}}
        self.invoke("update", patch, ("--expected-revision", "0"), ok=False)
        (self.project / ".daodan/runs/test-run/audit.md").write_text("Audit evidence\n")
        patch["gates"]["tests"]["snapshot"] = record["project"]["snapshot"]["digest"]
        patch["gates"]["tests"]["head"] = record["project"]["head"]
        patch["gates"]["tests"]["evidence"] = {"command": "pytest", "job": "run-1"}
        result = self.invoke("update", patch, ("--expected-revision", "0"))
        self.assertEqual(result["status"], "complete")

    def test_identity_cannot_be_rebound_by_patch(self):
        self.init()
        self.invoke("update", {"run_id": "different"}, ("--expected-revision", "0"), ok=False)
        self.invoke("update", {"scope": {"paths": []}}, ("--expected-revision", "0"), ok=False)

    def test_exact_run_id_and_root_confinement_are_checked_before_writes(self):
        self.invoke("init", self.payload, ("--out", str(self.temp / "outside")), ok=False)
        self.assertFalse((self.temp / "outside").exists())
        self.invoke("init", self.payload, ("--run-id", "../escape"), ok=False)
        self.assertFalse((self.project / "escape").exists())

    def test_custom_root_must_be_dedicated_and_inside_project(self):
        self.invoke("init", self.payload, ("--out", str(self.project)), ok=False)
        self.init(("--out", "reports/lifecycle"))
        self.assertTrue((self.project / "reports/lifecycle/.daodan-root").is_file())

    def test_duplicate_run_cannot_replace_existing_record(self):
        first = self.init()
        self.invoke("init", self.payload, ok=False)
        self.assertEqual(self.invoke("show"), first)

    def test_output_root_symlink_is_rejected(self):
        outside = self.temp / "outside"
        outside.mkdir()
        try:
            (self.project / "linked").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        self.invoke("init", self.payload, ("--out", "linked"), ok=False)
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipUnless(os.name == "nt", "Windows junctions are unavailable on this platform")
    def test_owned_report_junction_is_rejected_without_the_new_pathlib_api(self):
        self.init()
        outside = self.temp / "foreign-evidence"
        outside.mkdir()
        report = outside / "report.md"
        report.write_text("Keep this evidence unchanged\n")
        junction = self.project / ".daodan/runs/test-run/reports"
        environment = {**os.environ, "DAODAN_JUNCTION_LINK": str(junction), "DAODAN_JUNCTION_TARGET": str(outside)}
        created = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "New-Item -ItemType Junction -Path $env:DAODAN_JUNCTION_LINK -Target $env:DAODAN_JUNCTION_TARGET | Out-Null"],
            env=environment, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if created.returncode:
            self.skipTest(f"junction unavailable: {created.stderr}")

        def absent_junction_api(_self):
            raise AttributeError("Path.is_junction is unavailable before Python 3.12")

        # The target is a real junction. Only the newer convenience API is absent.
        with patch.object(Path, "is_junction", property(absent_junction_api), create=True):
            delivery = {"deliveries": {"audit": {"status": "delivered", "output": "reports/report.md"}}}
            failure = self.invoke("update", delivery, ("--expected-revision", "0"), ok=False)
            self.assertIn("Link is not an owned", failure.stderr)
            self.assertEqual(report.read_text(), "Keep this evidence unchanged\n")
            report.unlink()
            outside.rmdir()
            failure = self.invoke("update", delivery, ("--expected-revision", "0"), ok=False)
            self.assertIn("Link is not an owned", failure.stderr)
        self.assertEqual(self.invoke("show")["revision"], 0)

    def test_interruption_is_persisted_and_resume_reports_unfinished_delivery(self):
        self.init()
        self.invoke("update", {"interruption": {"phase": "audit", "reason": "session ended"},
                               "deliveries": {"audit": {"status": "running"}}},
                    ("--expected-revision", "0"))
        resumed = self.invoke("resume", {"authorizations": self.payload["authorizations"]})
        self.assertEqual(resumed["interruption"]["reason"], "session ended")
        self.assertEqual(resumed["pending_deliveries"], ["audit"])

    def test_closed_phase_cannot_regress(self):
        self.init()
        self.invoke("update", {"phases": {"audit": {"status": "complete"}}},
                    ("--expected-revision", "0"))
        self.invoke("update", {"phases": {"audit": {"status": "pending"}}},
                    ("--expected-revision", "1"), ok=False)

    def test_retry_keeps_the_failed_attempt(self):
        self.init()
        failed = {"status": "failed", "reason": "lost worker"}
        self.invoke("update", {"deliveries": {"audit": failed}}, ("--expected-revision", "0"))
        self.invoke("update", {"deliveries": {"audit": {"status": "running"}}},
                    ("--expected-revision", "1"), ok=False)
        self.invoke("update", {"deliveries": {"audit": {"status": "running", "attempts": [failed]}}},
                    ("--expected-revision", "1"))

    def test_historical_complete_record_can_be_read_after_source_changes(self):
        self.init()
        self.invoke("update", {"status": "complete", "phases": {"audit": {"status": "complete"}},
                               "deliveries": {"audit": {"status": "delivered", "output": self.report()}}},
                    ("--expected-revision", "0"))
        (self.project / "app.py").write_text("different input\n")
        self.assertEqual(self.invoke("show")["status"], "complete")
        self.invoke("resume", {"authorizations": self.payload["authorizations"]}, ok=False)

    def test_concurrent_writers_do_not_lose_an_update(self):
        self.init()
        paths = []
        for index in range(2):
            path = self.temp / f"concurrent-{index}.json"
            path.write_text(json.dumps({"interruption": {"reason": f"writer-{index}"}}))
            paths.append(path)
        commands = [
            [sys.executable, str(SCRIPT), "update", "--project", str(self.project), "--run-id", "test-run",
             "--expected-revision", "0", "--payload", str(path)] for path in paths
        ]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for command in commands]
        results = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            results.append((process.returncode, stdout, stderr))
        self.assertEqual(sorted(result[0] for result in results), [0, 1], results)
        self.assertEqual(self.invoke("show")["revision"], 1)

    def test_missing_report_cannot_be_claimed_delivered(self):
        self.init()
        self.invoke("update", {"status": "complete", "phases": {"audit": {"status": "complete"}},
                               "deliveries": {"audit": {"status": "delivered", "output": "missing.md"}}},
                    ("--expected-revision", "0"), ok=False)

    def test_referenced_report_cannot_escape_the_run(self):
        self.init()
        self.invoke("update", {"deliveries": {"audit": {"status": "delivered", "output": "../other/report.md"}}},
                    ("--expected-revision", "0"), ok=False)

    def test_newly_discovered_gate_can_be_added_but_never_removed(self):
        self.init()
        added = self.invoke("update", {"required_gates": ["behavior"]}, ("--expected-revision", "0"))
        self.assertEqual(added["required_gates"], ["behavior"])
        self.invoke("update", {"required_gates": []}, ("--expected-revision", "1"), ok=False)
        self.invoke("update", {"required_gates": ["behavior", "protection"]}, ("--expected-revision", "1"))

    def test_completed_run_cannot_rebind_an_old_success_to_new_input(self):
        self.init()
        self.invoke("update", {"status": "complete", "phases": {"audit": {"status": "complete"}},
                               "deliveries": {"audit": {"status": "delivered", "output": self.report()}}},
                    ("--expected-revision", "0"))
        (self.project / "app.py").write_text("new candidate\n")
        self.invoke("update", {"plan": ["pretend this was checked"]},
                    ("--expected-revision", "1"), ok=False)

    def test_result_is_bound_to_exact_work_revision_and_snapshot(self):
        record = self.init()
        result = {
            "schema": "daodan/project-result/v1", "run_id": "test-run", "work_revision": 0,
            "scope": record["scope"], "snapshot": record["candidate"]["snapshot"]["digest"],
            "deliveries": {"audit": {"status": "pending"}}, "checks": {},
            "outputs": [], "limitations": ["Audit still pending"], "complete": False,
        }
        path = self.project / ".daodan/runs/test-run/result.json"
        path.write_text(json.dumps(result))
        self.assertTrue(self.invoke("validate", extra=("--result", str(path)))["valid"])
        result["work_revision"] = 7
        path.write_text(json.dumps(result))
        self.invoke("validate", extra=("--result", str(path)), ok=False)
        result["work_revision"] = 0
        result["complete"] = True
        path.write_text(json.dumps(result))
        self.invoke("validate", extra=("--result", str(path)), ok=False)

    def test_current_validation_rejects_old_success_after_input_changes(self):
        self.init()
        (self.project / "app.py").write_text("new input\n")
        self.assertTrue(self.invoke("validate")["valid"])
        self.invoke("validate", extra=("--current",), ok=False)

    def test_delivered_worker_must_have_a_real_report_before_completion(self):
        record = self.init()
        patch = {"status": "complete", "phases": {"audit": {"status": "complete"}},
                 "deliveries": {"audit": {"status": "delivered"}}}
        failure = self.invoke("update", patch, ("--expected-revision", "0"), ok=False)
        self.assertIn("report", failure.stderr)
        self.assertEqual(self.invoke("show")["revision"], 0)
        # A hand-written false completion is rejected on read, including result validation.
        record.update(patch)
        directory = self.project / ".daodan/runs/test-run"
        (directory / "work.json").write_text(json.dumps(record))
        result = {"schema": "daodan/project-result/v1", "run_id": "test-run", "work_revision": 0,
                  "scope": record["scope"], "snapshot": record["candidate"]["snapshot"]["digest"],
                  "deliveries": patch["deliveries"], "checks": {}, "outputs": [],
                  "limitations": [], "complete": True}
        (directory / "result.json").write_text(json.dumps(result))
        self.invoke("validate", extra=("--current", "--result", str(directory / "result.json")), ok=False)

    def test_remote_gate_needs_a_real_source_revision(self):
        self.runtime["main"].__globals__["git_value"] = lambda *_: None
        self.payload["required_gates"] = ["remote"]
        record = self.init()
        patch = self.remote_completion(record)
        del patch["gates"]["remote"]["evidence"]["source_revision"]
        self.invoke("update", patch, ("--expected-revision", "0"), ok=False)

    def test_remote_gate_cannot_verify_dirty_inputs_at_the_old_head(self):
        self.committed_project()
        (self.project / "app.py").write_text("modified but not committed\n")
        self.payload["required_gates"] = ["remote"]
        record = self.init()
        self.invoke("update", self.remote_completion(record), ("--expected-revision", "0"), ok=False)

    def test_remote_gate_cannot_verify_untracked_ignored_inputs(self):
        self.committed_project()
        self.git("config", "core.excludesfile", str(self.project / "ignore-file"))
        (self.project / "ignore-file").write_text("scratch.py\n")
        (self.project / "scratch.py").write_text("new input\n")
        self.payload["scope"]["paths"].append("scratch.py")
        self.payload["required_gates"] = ["remote"]
        record = self.init()
        self.invoke("update", self.remote_completion(record), ("--expected-revision", "0"), ok=False)

    def test_remote_gate_can_verify_a_committed_clean_candidate(self):
        self.committed_project()
        self.payload["required_gates"] = ["remote"]
        record = self.init()
        result = self.invoke("update", self.remote_completion(record), ("--expected-revision", "0"))
        self.assertEqual(result["status"], "complete")

    def test_remote_gate_cannot_hide_dirty_content_with_assume_unchanged(self):
        self.committed_project()
        self.git("update-index", "--assume-unchanged", "app.py")
        (self.project / "app.py").write_text("hidden dirty content\n")
        self.payload["required_gates"] = ["remote"]
        record = self.init()
        self.invoke("update", self.remote_completion(record), ("--expected-revision", "0"), ok=False)

    def test_coordinator_records_are_not_worker_reports_under_aliases(self):
        self.init()
        for output in ("work.json", "WORK.JSON", "work.json.", "result.json", ".write-lock"):
            self.invoke("update", {"deliveries": {"audit": {"status": "delivered", "output": output}}},
                        ("--expected-revision", "0"), ok=False)

    def test_remote_gate_cannot_attest_replaced_head_symlink_as_regular_file(self):
        self.committed_project()
        self.git("config", "core.symlinks", "true")
        source = self.project / "app.py"
        source.unlink()
        try:
            source.symlink_to("target.txt")
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        self.git("add", "app.py")
        self.git("commit", "-m", "Symlink candidate")
        source.unlink()
        source.write_bytes(b"target.txt")
        self.payload["required_gates"] = ["remote"]
        record = self.init()
        self.invoke("update", self.remote_completion(record), ("--expected-revision", "0"), ok=False)

    @unittest.skipIf(os.name == "nt", "POSIX executable state is unavailable on Windows")
    def test_executable_change_invalidates_resume_and_remote_head_gate(self):
        self.committed_project()
        self.init()
        source = self.project / "app.py"
        source.chmod(source.stat().st_mode | stat.S_IXUSR)
        self.invoke("resume", {"authorizations": self.payload["authorizations"]}, ok=False)
        record = self.invoke("show")
        patch = self.remote_completion(record)
        patch["required_gates"] = ["remote"]
        candidate = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        patch["gates"]["remote"]["snapshot"] = candidate["snapshot"]["digest"]
        self.invoke("update", patch, ("--expected-revision", "0"), ok=False)

    def test_linked_lock_file_cannot_mutate_an_unowned_file(self):
        self.init()
        foreign = self.temp / "foreign.txt"
        foreign.write_text("must survive")
        lock = self.project / ".daodan/runs/test-run/.write-lock"
        try:
            os.link(foreign, lock)
        except OSError as error:
            self.skipTest(f"hardlink unavailable: {error}")
        self.invoke("update", {"interruption": {"reason": "test"}},
                    ("--expected-revision", "0"), ok=False)
        self.assertEqual(foreign.read_text(), "must survive")


if __name__ == "__main__":
    unittest.main()
