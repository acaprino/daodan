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


class ProtocolCase(unittest.TestCase):
    """Fixture and helpers shared by the record and loop suites."""
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


class ProjectProtocolTests(ProtocolCase):
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


class LoopRecordTests(ProtocolCase):
    """The loop sections: workspace, preflight, adr, waves and rulings."""

    def task(self, identity, *writes, **extra):
        return {"id": identity, "status": "pending", "write_set": list(writes),
                "oracle": {"command": f"pytest tests/test_{identity}.py", "expected_failure": "AssertionError"},
                "verification": {"command": "pytest -q"}, **extra}

    def wave(self, identity, *tasks, **extra):
        return {"id": identity, "status": "pending", "tasks": list(tasks), **extra}

    def plan_check(self, payload, ok=True):
        return self.invoke("plan-check", payload, ok=ok)

    def test_plan_check_accepts_a_disjoint_bounded_wave(self):
        result = self.plan_check({"waves": [self.wave("w1", self.task("a", "src/a.py", "tests/test_a.py"),
                                                       self.task("b", "src/b.py", "tests/test_b.py"))]})
        self.assertEqual((result["valid"], result["waves"], result["tasks"]), (True, 1, 2))

    def test_micro_task_budget_is_mechanical(self):
        five = self.task("a", *(f"src/{index}.py" for index in range(5)))
        refusal = self.plan_check({"waves": [self.wave("w1", five)]}, ok=False)
        self.assertIn("budget is 4", refusal.stderr)
        five["granularity_exception"] = {"reason": "generated client and its four bindings change together"}
        self.assertTrue(self.plan_check({"waves": [self.wave("w1", five)]})["valid"])
        seven = self.task("a", *(f"src/{index}.py" for index in range(7)), granularity_exception={"reason": "x"})
        self.assertIn("budget is 6", self.plan_check({"waves": [self.wave("w1", seven)]}, ok=False).stderr)
        no_oracle = self.task("a", "src/a.py")
        no_oracle["oracle"] = {"command": "pytest"}
        self.assertIn("failure it must produce", self.plan_check({"waves": [self.wave("w1", no_oracle)]}, ok=False).stderr)

    def test_tasks_in_one_wave_share_neither_files_nor_locks_nor_contracts(self):
        shared = self.wave("w1", self.task("a", "src/common.py"), self.task("b", "src/common.py"))
        self.assertIn("share write_set files", self.plan_check({"waves": [shared]}, ok=False).stderr)
        locked = self.wave("w1", self.task("a", "src/a.py", resource_locks=["db:migrations"]),
                           self.task("b", "src/b.py", resource_locks=["db:migrations"]))
        self.assertIn("share resource locks", self.plan_check({"waves": [locked]}, ok=False).stderr)
        chained = self.wave("w1", self.task("a", "src/a.py", produces=["OrderDraft"]),
                            self.task("b", "src/b.py", consumes=["OrderDraft"]))
        self.assertIn("consumes what a produces", self.plan_check({"waves": [chained]}, ok=False).stderr)
        split = [self.wave("w1", self.task("a", "src/a.py", produces=["OrderDraft"])),
                 self.wave("w2", self.task("b", "src/b.py", consumes=["OrderDraft"]))]
        self.assertTrue(self.plan_check({"waves": split})["valid"])

    def test_parallel_waves_need_a_worktree(self):
        waves = [self.wave("w1", self.task("a", "src/a.py"), self.task("b", "src/b.py"), parallel=True)]
        self.assertIn("needs a WORKTREE", self.plan_check({"waves": waves}, ok=False).stderr)
        in_place = {"mode": "IN_PLACE", "branch": "master", "base_sha": "abc"}
        self.assertIn("needs a WORKTREE", self.plan_check({"workspace": in_place, "waves": waves}, ok=False).stderr)
        worktree = {"mode": "WORKTREE", "branch": "task/a", "base_sha": "abc", "worktree_path": ".worktrees/a"}
        self.assertTrue(self.plan_check({"workspace": worktree, "waves": waves})["valid"])
        self.assertIn("worktree_path", self.plan_check({"workspace": {"mode": "WORKTREE", "branch": "t", "base_sha": "a"}}, ok=False).stderr)

    def test_secret_bindings_never_carry_a_value_and_red_baselines_carry_a_fingerprint(self):
        workspace = {"mode": "BRANCH", "branch": "task/a", "base_sha": "abc",
                     "environment_bindings": [{"path": ".env.local", "kind": "env-file", "secret": True, "value": "x"}]}
        self.assertIn("never records its value", self.plan_check({"workspace": workspace}, ok=False).stderr)
        del workspace["environment_bindings"][0]["value"]
        self.assertTrue(self.plan_check({"workspace": workspace})["valid"])
        self.assertIn("fingerprint", self.plan_check({"preflight": {"baseline": "KNOWN_RED"}}, ok=False).stderr)
        self.assertTrue(self.plan_check({"preflight": {"baseline": "KNOWN_RED", "failing_fingerprint": "sha256:0"}})["valid"])
        self.assertIn("ADR identifiers", self.plan_check({"adr": {"active": ["adr-1"]}}, ok=False).stderr)
        self.assertTrue(self.plan_check({"adr": {"active": ["ADR-0014"], "proposed": "ADR-0015"}})["valid"])

    def test_sealed_wave_requires_committed_tasks(self):
        pending = self.wave("w1", self.task("a", "src/a.py"), status="sealed")
        self.assertIn("cannot be sealed", self.plan_check({"waves": [pending]}, ok=False).stderr)
        committed = self.task("a", "src/a.py")
        committed["status"] = "committed"
        self.assertTrue(self.plan_check({"waves": [self.wave("w1", committed, status="sealed")]})["valid"])

    def test_rulings_are_append_only_inside_a_run(self):
        ruling = {"id": "RUL-001", "task": "a", "sha": "abc", "decision": "keep sync API",
                  "reason": "callers are sync", "cost_if_wrong": "one adapter", "evidence": ["src/a.py:12"]}
        self.payload["rulings"] = [ruling]
        record = self.init()
        self.assertEqual(record["rulings"], [ruling])
        second = {**ruling, "id": "RUL-002", "decision": "retry once"}
        updated = self.invoke("update", {"rulings": [ruling, second]}, ["--expected-revision", "0"])
        self.assertEqual([r["id"] for r in updated["rulings"]], ["RUL-001", "RUL-002"])
        altered = {**ruling, "decision": "changed after the fact"}
        refusal = self.invoke("update", {"rulings": [altered, second]}, ["--expected-revision", "1"], ok=False)
        self.assertIn("append-only", refusal.stderr)
        dropped = self.invoke("update", {"rulings": [second]}, ["--expected-revision", "1"], ok=False)
        self.assertIn("append-only", dropped.stderr)
        self.assertIn("cites evidence", self.plan_check({"rulings": [{**ruling, "evidence": []}]}, ok=False).stderr)

    def test_each_review_bounds_only_the_deliveries_bound_to_it(self):
        light = {"id": "R1", "stage": "wave-1", "schema": "daodan/review-roster/v1", "shape": "light",
                 "kind": "changeset", "tier": "light", "roster": ["senior-review:code-auditor"],
                 "support": ["senior-review:premise-auditor", "project-protocol:isolated-worker"],
                 "reasons": ["no raising signal"], "verification": "critical-high"}
        self.payload["reviews"] = [light]
        self.payload["deliveries"] = {
            "R1-code-auditor": {"status": "pending", "role": "senior-review:code-auditor", "review": "R1"},
            "w1-t1": {"status": "pending", "role": "python-development:python-engineer"},
        }
        record = self.init()
        self.assertEqual(record["reviews"][0]["tier"], "light")
        widened = {"deliveries": {"R1-security": {"status": "pending", "role": "senior-review:security-auditor", "review": "R1"}}}
        refusal = self.invoke("update", widened, ["--expected-revision", "0"], ok=False)
        self.assertIn("computed roster of review R1 does not contain", refusal.stderr)
        self.assertIn("senior-review:security-auditor", refusal.stderr)
        lens = {"deliveries": {"R1-lens-0": {"status": "pending", "role": "senior-review:premise-auditor", "review": "R1"}}}
        self.assertIn("R1-lens-0", self.invoke("update", lens, ["--expected-revision", "0"])["deliveries"])
        unknown = {"deliveries": {"R9-x": {"status": "pending", "role": "senior-review:code-auditor", "review": "R9"}}}
        self.assertIn("names review R9", self.invoke("update", unknown, ["--expected-revision", "1"], ok=False).stderr)
        rewritten = {"reviews": [{**light, "roster": light["roster"] + ["senior-review:security-auditor"]}]}
        self.assertIn("append-only", self.invoke("update", rewritten, ["--expected-revision", "1"], ok=False).stderr)
        deeper = {**light, "id": "R2", "shape": "branch", "tier": "small", "stage": "candidate"}
        self.assertEqual(len(self.invoke("update", {"reviews": [light, deeper]}, ["--expected-revision", "1"])["reviews"]), 2)
        self.assertIn("tier must be one of", self.plan_check({"reviews": [{**light, "tier": "enormous"}]}, ok=False).stderr)
        self.assertIn("kind must be one of", self.plan_check({"reviews": [{**light, "kind": "poem"}]}, ok=False).stderr)
        self.assertIn("roster must be a nonempty list",
                      self.plan_check({"reviews": [{**light, "roster": []}]}, ok=False).stderr)

    def git(self, *arguments):
        return subprocess.run(["git", "-C", str(self.project), *arguments], capture_output=True,
                              text=True, encoding="utf-8", check=True).stdout.strip()

    def make_repo(self):
        self.git("init", "-q", "-b", "main")
        self.git("-c", "user.email=t@example.com", "-c", "user.name=t", "add", "app.py")
        self.git("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "base")

    def test_the_agenda_binds_a_task_to_its_branch_and_session(self):
        self.make_repo()
        self.payload["workspace"] = {"mode": "BRANCH", "branch": "task/one", "base_sha": self.git("rev-parse", "HEAD")}
        self.payload["questions"] = [{"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}]
        self.invoke("init", self.payload, ["--session", "s1"])
        agenda = self.invoke("agenda", extra=["--branch", "task/one"])
        row = agenda["tasks"][0]
        self.assertEqual((row["run_id"], row["branch"], row["holder"]["session"], row["questions"], row["loop"]),
                         ("test-run", "task/one", "s1", 1, True))
        self.assertTrue((self.project / ".daodan/agenda.json").is_file())
        held = self.invoke("update", {"phases": {"audit": {"status": "in_progress"}}},
                           ["--expected-revision", "0", "--session", "s2"], ok=False)
        self.assertIn("held by session s1", held.stderr)
        taken = self.invoke("update", {"phases": {"audit": {"status": "in_progress"}}},
                            ["--expected-revision", "0", "--session", "s2", "--take-over"])
        self.assertEqual(taken["revision"], 1)
        row = self.invoke("agenda")["tasks"][0]
        self.assertEqual((row["holder"]["session"], row["phase"]), ("s2", "audit"))
        answered = self.invoke("update", {"questions": [{"id": "Q1", "phase": "interview", "text": "Keep the sync API?", "answer": "yes"}]},
                               ["--expected-revision", "1", "--session", "s2"])
        self.assertEqual(self.invoke("agenda")["tasks"][0]["questions"], 0)
        self.assertEqual(answered["questions"][0]["answer"], "yes")

    def test_a_branch_holds_one_open_loop_task_and_a_completed_run_releases_it(self):
        self.make_repo()
        self.payload["workspace"] = {"mode": "BRANCH", "branch": "task/one", "base_sha": self.git("rev-parse", "HEAD")}
        self.invoke("init", self.payload, ["--session", "s1"])
        second = {**self.payload, "objective": "another"}
        path = self.temp / "second.json"; path.write_text(json.dumps(second), encoding="utf-8")
        args = ["init", "--project", str(self.project), "--run-id", "second-run", "--payload", str(path), "--session", "s1"]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.runtime["main"](args)
        self.assertEqual(code, 1)
        self.assertIn("already holds open task test-run", stderr.getvalue())
        self.assertFalse((self.project / ".daodan/runs/second-run").exists())
        self.invoke("update", {"phases": {"audit": {"status": "complete"}},
                               "deliveries": {"audit": {"status": "delivered", "output": self.report()}},
                               "status": "complete"}, ["--expected-revision", "0", "--session", "s1"])
        row = self.invoke("agenda")["tasks"][0]
        self.assertEqual((row["status"], row["holder"]), ("complete", None))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.runtime["main"](args), 0)

    def test_run_state_of_a_linked_worktree_lives_in_the_main_checkout(self):
        self.make_repo()
        worktree = self.temp / "wt"
        self.git("worktree", "add", "-q", "-b", "task/wt", str(worktree))
        payload = {**self.payload, "workspace": {"mode": "WORKTREE", "branch": "task/wt", "base_sha": self.git("rev-parse", "HEAD"),
                                               "worktree_path": str(worktree)}}
        path = self.temp / "wt.json"; path.write_text(json.dumps(payload), encoding="utf-8")
        args = ["init", "--project", str(worktree), "--run-id", "wt-run", "--payload", str(path), "--session", "s1"]
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.runtime["main"](args), 0)
        record = json.loads(stdout.getvalue())
        self.assertEqual(Path(record["output_root"]), (self.project / ".daodan").resolve())
        self.assertTrue((self.project / ".daodan/runs/wt-run/work.json").is_file())
        self.assertFalse((worktree / ".daodan").exists())
        self.assertEqual(Path(record["project"]["worktree"]), worktree.resolve())
        rows = self.invoke("agenda", extra=["--branch", "task/wt"])["tasks"]
        self.assertEqual([r["run_id"] for r in rows], ["wt-run"])
        self.git("worktree", "remove", "--force", str(worktree))
        self.assertTrue((self.project / ".daodan/runs/wt-run/work.json").is_file())

    def test_environment_and_questions_are_validated(self):
        good = {"interpreter": ".venv/Scripts/python.exe", "commands": {"test": "pytest -q", "lint": "ruff check ."}}
        self.assertTrue(self.plan_check({"environment": good})["valid"])
        self.assertIn("is not one of", self.plan_check({"environment": {**good, "commands": {"deploy": "x"}}}, ok=False).stderr)
        self.assertIn("environment.interpreter is required", self.plan_check({"environment": {"commands": {}}}, ok=False).stderr)
        self.assertIn("repeated", self.plan_check({"questions": [{"id": "Q1", "phase": "p", "text": "a"},
                                                                  {"id": "Q1", "phase": "p", "text": "b"}]}, ok=False).stderr)
        self.assertIn("empty answer", self.plan_check({"questions": [{"id": "Q1", "phase": "p", "text": "a", "answer": " "}]}, ok=False).stderr)

    def test_loop_sections_are_validated_inside_the_record_too(self):
        self.payload["waves"] = [self.wave("w1", self.task("a", "src/common.py"), self.task("b", "src/common.py"))]
        refusal = self.invoke("init", self.payload, ok=False)
        self.assertIn("share write_set files", refusal.stderr)


if __name__ == "__main__":
    unittest.main()
