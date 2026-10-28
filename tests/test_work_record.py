"""Behavioral tests of persisted work, rather than prompt wording."""

import copy
import json
import contextlib
import hashlib
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
SCRIPT = REPO_ROOT / "plugins/work-controller/skills/work-record/scripts/run_state.py"


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

    def test_a_consumer_names_its_own_operation(self):
        self.payload["operation"] = "restyle"
        self.assertEqual(self.init()["operation"], "restyle")
        self.assertEqual(self.invoke("agenda")["tasks"][0]["operation"], "restyle")

    def test_identity_cannot_be_rebound_by_patch(self):
        self.init()
        self.invoke("update", {"run_id": "different"}, ("--expected-revision", "0"), ok=False)
        self.invoke("update", {"scope": {"paths": []}}, ("--expected-revision", "0"), ok=False)

    def test_exact_run_id_is_checked_before_writes(self):
        self.invoke("init", self.payload, ("--run-id", "../escape"), ok=False)
        self.assertFalse((self.project / "escape").exists())

    def test_the_record_home_must_be_dedicated(self):
        home = self.project / ".daodan"
        home.mkdir()
        (home / "notes.txt").write_text("someone else's\n", encoding="utf-8")
        self.assertIn("dedicated", self.invoke("init", self.payload, ok=False).stderr)
        (home / "notes.txt").unlink()
        self.init()
        self.assertTrue((home / ".daodan-root").is_file())

    def test_duplicate_run_cannot_replace_existing_record(self):
        first = self.init()
        self.invoke("init", self.payload, ok=False)
        self.assertEqual(self.invoke("show"), first)

    def test_a_linked_record_home_is_rejected(self):
        outside = self.temp / "outside"
        outside.mkdir()
        try:
            (self.project / ".daodan").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        self.invoke("init", self.payload, ok=False)
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
        lock = self.project / ".daodan/.write-lock"
        lock.unlink()
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
        wave = {"id": identity, "status": "pending", "tasks": list(tasks), **extra}
        if any(task.get("status") in {"running", "green", "committed"} for task in tasks) and tasks[0].get("candidate"):
            candidate = tasks[0]["candidate"]
            if "plan_candidate" not in extra:
                wave["plan_candidate"] = candidate
            if "plan_review" not in extra:
                wave["plan_review"] = {"id": "R0", "verdict": "PASS",
                                       "snapshot": candidate["digest"], "head": candidate["head"]}
        if isinstance(wave.get("plan_review"), dict) and wave.get("plan_candidate"):
            wave["plan_review"].setdefault("plan_sha256", self.runtime["plan_fingerprint"](wave))
        return wave

    def check_draft(self, draft, ok=True):
        """Record a draft in a run of its own: the write validates it, and a refusal writes nothing."""
        self.drafts = getattr(self, "drafts", 0) + 1
        return self.invoke("init", {**self.payload, **draft}, ["--run-id", f"draft-{self.drafts}"], ok=ok)

    def test_a_disjoint_bounded_wave_is_accepted(self):
        record = self.check_draft({"waves": [self.wave("w1", self.task("a", "src/a.py", "tests/test_a.py"),
                                                       self.task("b", "src/b.py", "tests/test_b.py"))]})
        self.assertEqual([len(wave["tasks"]) for wave in record["waves"]], [2])

    def test_micro_task_budget_is_mechanical(self):
        five = self.task("a", *(f"src/{index}.py" for index in range(5)))
        refusal = self.check_draft({"waves": [self.wave("w1", five)]}, ok=False)
        self.assertIn("budget is 4", refusal.stderr)
        five["granularity_exception"] = {"reason": "generated client and its four bindings change together"}
        self.check_draft({"waves": [self.wave("w1", five)]})
        seven = self.task("a", *(f"src/{index}.py" for index in range(7)), granularity_exception={"reason": "x"})
        self.assertIn("budget is 6", self.check_draft({"waves": [self.wave("w1", seven)]}, ok=False).stderr)
        no_oracle = self.task("a", "src/a.py")
        no_oracle["oracle"] = {"command": "pytest"}
        self.assertIn("failure it must produce", self.check_draft({"waves": [self.wave("w1", no_oracle)]}, ok=False).stderr)

    def test_tasks_in_one_wave_share_neither_files_nor_locks_nor_contracts(self):
        shared = self.wave("w1", self.task("a", "src/common.py"), self.task("b", "src/common.py"))
        self.assertIn("share write_set files", self.check_draft({"waves": [shared]}, ok=False).stderr)
        locked = self.wave("w1", self.task("a", "src/a.py", resource_locks=["db:migrations"]),
                           self.task("b", "src/b.py", resource_locks=["db:migrations"]))
        self.assertIn("share resource locks", self.check_draft({"waves": [locked]}, ok=False).stderr)
        chained = self.wave("w1", self.task("a", "src/a.py", produces=["OrderDraft"]),
                            self.task("b", "src/b.py", consumes=["OrderDraft"]))
        self.assertIn("consumes what a produces", self.check_draft({"waves": [chained]}, ok=False).stderr)
        split = [self.wave("w1", self.task("a", "src/a.py", produces=["OrderDraft"])),
                 self.wave("w2", self.task("b", "src/b.py", consumes=["OrderDraft"]))]
        self.check_draft({"waves": split})

    def test_parallel_waves_need_a_worktree(self):
        waves = [self.wave("w1", self.task("a", "src/a.py"), self.task("b", "src/b.py"), parallel=True)]
        self.assertIn("needs a WORKTREE", self.check_draft({"waves": waves}, ok=False).stderr)
        in_place = {"mode": "IN_PLACE", "branch": "master", "base_sha": "abc"}
        self.assertIn("needs a WORKTREE", self.check_draft({"workspace": in_place, "waves": waves}, ok=False).stderr)
        worktree = {"mode": "WORKTREE", "branch": "task/a", "base_sha": "abc", "worktree_path": ".worktrees/a"}
        self.check_draft({"workspace": worktree, "waves": waves})
        self.assertIn("worktree_path", self.check_draft({"workspace": {"mode": "WORKTREE", "branch": "t", "base_sha": "a"}}, ok=False).stderr)

    def test_secret_bindings_never_carry_a_value_and_red_baselines_carry_a_fingerprint(self):
        workspace = {"mode": "BRANCH", "branch": "task/a", "base_sha": "abc",
                     "environment_bindings": [{"path": ".env.local", "kind": "env-file", "secret": True, "value": "x"}]}
        self.assertIn("never records its value", self.check_draft({"workspace": workspace}, ok=False).stderr)
        del workspace["environment_bindings"][0]["value"]
        self.check_draft({"workspace": workspace})
        self.assertIn("fingerprint", self.check_draft({"preflight": {"baseline": "KNOWN_RED"}}, ok=False).stderr)
        self.check_draft({"preflight": {"baseline": "KNOWN_RED", "failing_fingerprint": "sha256:0"}})
        self.assertIn("ADR identifiers", self.check_draft({"adr": {"active": ["adr-1"]}}, ok=False).stderr)
        self.check_draft({"adr": {"active": ["ADR-0014"], "proposed": "ADR-0015"}})

    def test_an_adr_citation_may_pin_a_version(self):
        self.check_draft({"adr": {"active": ["ADR-0006 v2"], "proposed": "ADR-0007"}})
        self.assertIn("ADR identifiers", self.check_draft({"adr": {"active": ["ADR-0006 v0"]}}, ok=False).stderr)

    def review(self, candidate, identity="R1", stage="pre-commit-a"):
        job = {"id": f"{identity}-job", "role": "senior-review:code-auditor",
               "specialist_ids": ["general"], "scope_id": "candidate", "input_mode": "discovery",
               "body_sha256": "b" * 64, "candidate": candidate, "output_path": f"{identity}-report.md"}
        return {"id": identity, "stage": stage, "schema": "daodan/review-roster/v1",
                "shape": "light", "kind": "changeset", "tier": "light",
                "roster": ["senior-review:code-auditor"], "reasons": ["step gate"],
                "verification": "critical-high", "grounding": {"candidate": candidate},
                "required_specialists": [{"specialist_id": "general", "scope_id": "candidate",
                                          "evidence": ["app.py"]}], "jobs": [job]}

    def review_delivery(self, review, run_id, write=True):
        directory = self.project / ".daodan/runs" / run_id
        job = review["jobs"][0]
        if write:
            (directory / job["output_path"]).write_text("PASS: no blocking findings.\n", encoding="utf-8")
        return {f"{review['id']}-delivery": {
            "status": "delivered", "role": job["role"], "review": review["id"], "job_id": job["id"],
            "output": job["output_path"], "scope_id": job["scope_id"], "body_sha256": job["body_sha256"],
            "candidate": job["candidate"], "specialist_ids": job["specialist_ids"],
            "member_results": [{"specialist_id": "general", "status": "delivered", "coverage": "complete",
                                "findings": [], "gaps": []}], "findings": []}}

    def use_review(self, candidate):
        plan = self.review(candidate, "R0", "plan")
        plan["kind"] = "plan"
        review = self.review(candidate)
        self.payload["reviews"] = [plan, review]
        for item in (plan, review):
            delivery = self.review_delivery(item, "test-run", write=False)
            for entry in delivery.values():
                entry["status"] = "pending"
            self.payload.setdefault("deliveries", {}).update(delivery)
        self._deliver_on_init = [plan, review]
        self._plan = plan

    def init(self, extra=()):
        if hasattr(self, "_plan"):
            for wave in self.payload.get("waves", []):
                wave["plan_candidate"] = self._plan["grounding"]["candidate"]
                wave["plan_review"] = {"id": "R0", "verdict": "PASS",
                                       "snapshot": self._plan["grounding"]["candidate"]["digest"],
                                       "head": self._plan["grounding"]["candidate"]["head"]}
                fingerprint = self.runtime["plan_fingerprint"](wave)
                wave["plan_review"]["plan_sha256"] = fingerprint
                self._plan["grounding"]["plan_sha256"] = fingerprint
            del self._plan
        record = super().init(extra)
        for review in getattr(self, "_deliver_on_init", []):
            delivery = self.review_delivery(review, "test-run")
            record = self.invoke("update", {"deliveries": delivery},
                                 ["--expected-revision", str(record["revision"])])
        self._deliver_on_init = []
        return record

    def committed_task(self, candidate, commit_sha="c" * 40):
        task = self.task("a", "app.py")
        task.update({"status": "committed", "candidate": candidate, "commit_sha": commit_sha,
                     "verification_receipt": {"status": "passed", "snapshot": candidate["digest"],
                                              "head": candidate["head"], "command": "pytest -q"},
                     "pre_commit_review": {"id": "R1", "verdict": "PASS",
                                           "snapshot": candidate["digest"], "head": candidate["head"]}})
        return task

    def sealed_wave(self, candidate):
        task = self.committed_task(candidate)
        wave = self.wave("w1", task, status="sealed", candidate=candidate,
                         plan_candidate=candidate,
                         plan_review={"id": "R0", "verdict": "PASS",
                                      "snapshot": candidate["digest"], "head": candidate["head"]},
                         wave_review={"id": "R2", "verdict": "PASS",
                                      "snapshot": candidate["digest"], "head": candidate["head"]})
        plan = self.review(candidate, "R0", "plan")
        plan["kind"] = "plan"
        plan["grounding"]["plan_sha256"] = self.runtime["plan_fingerprint"](wave)
        reviews = [plan, self.review(candidate), self.review(candidate, "R2", "wave-w1")]
        return wave, reviews

    def test_sealed_wave_requires_committed_tasks_and_their_precommit_evidence(self):
        pending = self.wave("w1", self.task("a", "src/a.py"), status="sealed")
        self.assertIn("cannot be sealed", self.check_draft({"waves": [pending]}, ok=False).stderr)
        bare = self.task("a", "app.py", status="committed")
        self.assertIn("candidate", self.check_draft({"waves": [self.wave("w1", bare, status="sealed")]}, ok=False).stderr)
        candidate = {"digest": "0" * 64, "head": "base"}
        wave, reviews = self.sealed_wave(candidate)
        record = self.check_draft({"reviews": reviews,
                                   "waves": [self.wave("w1", self.task("a", "app.py"))]})
        deliveries = {}
        for review in reviews:
            deliveries.update(self.review_delivery(review, record["run_id"]))
        updated = self.runtime["merge"](record, {"deliveries": deliveries, "waves": [wave]})
        self.runtime["validate_record"](updated, self.project, Path(record["output_root"]))
        refusal = self.invoke("init", {**self.payload, "reviews": reviews, "deliveries": deliveries,
                                       "waves": [wave]}, ["--run-id", "presealed"], ok=False)
        self.assertIn("only pending work", refusal.stderr)
        unreviewed, _ = self.sealed_wave(candidate)
        del unreviewed["wave_review"]
        invalid = self.runtime["merge"](updated, {"waves": [unreviewed]})
        with self.assertRaisesRegex(self.runtime["ProtocolError"], "wave review"):
            self.runtime["validate_record"](invalid, self.project, Path(record["output_root"]))

    def test_commit_requires_verification_and_pass_review_on_the_same_candidate(self):
        candidate = {"digest": "0" * 64, "head": "base"}
        task = self.committed_task(candidate)
        task["verification_receipt"]["status"] = "failed"
        self.assertIn("passing verification", self.check_draft(
            {"reviews": [self.review(candidate)], "waves": [self.wave("w1", task)]}, ok=False).stderr)
        task = self.committed_task(candidate)
        task["pre_commit_review"]["verdict"] = "BLOCK"
        self.assertIn("pre-commit review", self.check_draft(
            {"reviews": [self.review(candidate)], "waves": [self.wave("w1", task)]}, ok=False).stderr)
        task = self.committed_task(candidate)
        task["pre_commit_review"]["snapshot"] = "1" * 64
        self.assertIn("pre-commit review", self.check_draft(
            {"reviews": [self.review(candidate)], "waves": [self.wave("w1", task)]}, ok=False).stderr)
        task = self.committed_task(candidate)
        task["verification_receipt"]["command"] = "echo ok"
        self.assertIn("passing verification", self.check_draft(
            {"reviews": [self.review(candidate)], "waves": [self.wave("w1", task)]}, ok=False).stderr)

    def test_declared_pass_without_a_delivered_review_cannot_commit(self):
        candidate = {"digest": "0" * 64, "head": "base"}
        refusal = self.check_draft({"reviews": [self.review(candidate)],
                                    "waves": [self.wave("w1", self.committed_task(candidate))]}, ok=False)
        self.assertIn("not delivered", refusal.stderr)

    def test_commit_transition_binds_current_head_and_reviewed_bytes(self):
        self.make_repo()
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        current = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": current["snapshot"]["digest"], "head": current["head"]}
        pending = self.task("a", "app.py")
        self.use_review(candidate)
        self.payload["waves"] = [self.wave("w1", pending)]
        self.init()
        self.git("add", "app.py")
        self.git("commit", "-m", "Reviewed step", "-m", "Daodan-Task: test-run wave 1/1")
        committed = self.committed_task(candidate, self.git("rev-parse", "HEAD"))
        updated = self.invoke("update", {"waves": [self.wave("w1", committed)]}, ["--expected-revision", "2"])
        self.assertEqual(updated["waves"][0]["tasks"][0]["status"], "committed")
        blocked = {"id": "R0", "verdict": "BLOCK", "snapshot": candidate["digest"], "head": candidate["head"]}
        unreviewed = self.wave("w1", committed, plan_review=blocked)
        refusal = self.invoke("update", {"waves": [unreviewed]},
                              ["--expected-revision", "3"], ok=False)
        self.assertIn("adversarial PASS plan review", refusal.stderr)
        head = self.git("rev-parse", "HEAD")
        wave_candidate = {"digest": candidate["digest"], "head": head}
        wave_review = self.review(wave_candidate, "R2", "wave-w1")
        reviews = [*updated["reviews"], wave_review]
        deliveries = self.review_delivery(wave_review, "test-run")
        sealed = self.wave("w1", committed, status="sealed", candidate=wave_candidate,
                           wave_review={"id": "R2", "verdict": "PASS",
                                        "snapshot": wave_candidate["digest"], "head": head})
        sealed_record = self.invoke("update", {"reviews": reviews, "deliveries": deliveries,
                                               "waves": [sealed]}, ["--expected-revision", "3"])
        self.assertEqual(sealed_record["waves"][0]["status"], "sealed")
        broken = dict(sealed)
        added = self.committed_task(wave_candidate, head)
        added["id"] = "b"
        added["write_set"] = ["other.py"]
        added_review = self.review(wave_candidate, "R4", "pre-commit-b")
        added["pre_commit_review"]["id"] = "R4"
        broken["tasks"] = [committed, added]
        fingerprint = self.runtime["plan_fingerprint"](broken)
        new_plan = self.review(broken["plan_candidate"], "R5", "plan")
        new_plan["kind"] = "plan"
        new_plan["grounding"]["plan_sha256"] = fingerprint
        broken["plan_review"].update(id="R5", plan_sha256=fingerprint)
        deliveries = {**self.review_delivery(added_review, "test-run"),
                      **self.review_delivery(new_plan, "test-run")}
        refusal = self.invoke("update", {"waves": [broken], "reviews": [*reviews, added_review, new_plan],
                                         "deliveries": deliveries},
                              ["--expected-revision", "4"], ok=False)
        self.assertIn("sealed membership", refusal.stderr)
        candidate_review = self.review(wave_candidate, "R3", "candidate")
        candidate_review["shape"] = "branch"
        integration = {"merged_sha": head, "realigned": True,
                       "candidate_review": {"id": "R3", "verdict": "PASS",
                                            "snapshot": wave_candidate["digest"], "head": head}}
        completion = {"status": "complete", "integration": integration,
                      "phases": {"audit": {"status": "complete"}},
                      "reviews": [*reviews, candidate_review],
                      "deliveries": {**self.review_delivery(candidate_review, "test-run"),
                                     "audit": {"status": "delivered", "output": self.report()}}}
        self.assertIn("merged_sha", self.invoke("update", {"status": "complete"},
                                                ["--expected-revision", "4"], ok=False).stderr)
        reviewed_head = head
        self.git("checkout", "--orphan", "independent")
        (self.project / "app.py").unlink(missing_ok=True)
        (self.project / "unrelated.py").write_text("print('independent')\n", encoding="utf-8")
        self.git("add", "unrelated.py")
        self.git("commit", "-m", "Independent root")
        completion["integration"]["merged_sha"] = self.git("rev-parse", "HEAD")
        refusal = self.invoke("update", completion, ["--expected-revision", "4"], ok=False)
        self.assertIn("does not descend", refusal.stderr)
        self.git("merge", "--allow-unrelated-histories", "--no-ff", reviewed_head, "-m", "Merge reviewed candidate")
        completion["integration"]["merged_sha"] = self.git("rev-parse", "HEAD")
        completed = self.invoke("update", completion, ["--expected-revision", "4"])
        self.assertEqual(completed["status"], "complete")

    def test_delivery_completion_rejects_an_unsealed_wave(self):
        record = self.check_draft({"waves": [self.wave("w1", self.task("a", "app.py"))]})
        record["status"] = "complete"
        with self.assertRaisesRegex(self.runtime["ProtocolError"], "unsealed wave"):
            self.runtime["validate_delivery_completion"](record, self.runtime["contract"]()["loop"]["reviews"])

    def test_plan_edit_or_source_change_blocks_dispatch(self):
        self.make_repo()
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        reviewed = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": reviewed["snapshot"]["digest"], "head": reviewed["head"]}
        self.use_review(candidate)
        self.payload["waves"] = [self.wave("w1", self.task("a", "app.py"))]
        record = self.init()
        planned = record["waves"][0]
        changed = copy.deepcopy(planned)
        changed["tasks"][0]["write_set"] = ["other.py"]
        changed["tasks"][0]["status"] = "running"
        refusal = self.invoke("update", {"waves": [changed]}, ["--expected-revision", "2"], ok=False)
        self.assertIn("plan changed", refusal.stderr)
        running = copy.deepcopy(planned)
        running["tasks"][0]["status"] = "running"
        (self.project / "app.py").write_text("print('after plan')\n", encoding="utf-8")
        refusal = self.invoke("update", {"waves": [running]}, ["--expected-revision", "2"], ok=False)
        self.assertIn("bytes changed", refusal.stderr)

    def test_committed_evidence_cannot_be_rewritten_without_reopening(self):
        self.make_repo()
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        reviewed = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": reviewed["snapshot"]["digest"], "head": reviewed["head"]}
        self.use_review(candidate)
        self.payload["waves"] = [self.wave("w1", self.task("a", "app.py"))]
        self.init()
        self.git("add", "app.py")
        self.git("commit", "-m", "Reviewed step", "-m", "Daodan-Task: test-run wave 1/1")
        committed = self.committed_task(candidate, self.git("rev-parse", "HEAD"))
        record = self.invoke("update", {"waves": [self.wave("w1", committed)]}, ["--expected-revision", "2"])
        altered = {**committed, "commit_sha": "0" * 40, "write_set": ["other.py"]}
        altered_wave = self.wave("w1", altered)
        new_plan = self.review(altered_wave["plan_candidate"], "R5", "plan")
        new_plan["kind"] = "plan"
        new_plan["grounding"]["plan_sha256"] = altered_wave["plan_review"]["plan_sha256"]
        altered_wave["plan_review"]["id"] = "R5"
        refusal = self.invoke("update", {"waves": [altered_wave], "reviews": [*record["reviews"], new_plan],
                                         "deliveries": self.review_delivery(new_plan, "test-run")},
                              ["--expected-revision", "3"], ok=False)
        self.assertIn("immutable", refusal.stderr)
        self.assertEqual(self.invoke("show")["waves"][0]["tasks"][0], committed)

    def test_edit_after_review_blocks_the_commit_transition(self):
        self.make_repo()
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        reviewed = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": reviewed["snapshot"]["digest"], "head": reviewed["head"]}
        self.use_review(candidate)
        self.payload["waves"] = [self.wave("w1", self.task("a", "app.py"))]
        self.init()
        (self.project / "app.py").write_text("print('changed after review')\n", encoding="utf-8")
        self.git("add", "app.py")
        self.git("commit", "-m", "Different step", "-m", "Daodan-Task: test-run wave 1/1")
        committed = self.committed_task(candidate, self.git("rev-parse", "HEAD"))
        refusal = self.invoke("update", {"waves": [self.wave("w1", committed)]},
                              ["--expected-revision", "2"], ok=False)
        self.assertIn("stale", refusal.stderr)
        self.assertEqual(self.invoke("show")["waves"][0]["tasks"][0]["status"], "pending")

    def test_commit_parent_must_be_the_reviewed_head(self):
        self.make_repo()
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        reviewed = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": reviewed["snapshot"]["digest"], "head": reviewed["head"]}
        self.use_review(candidate)
        self.payload["waves"] = [self.wave("w1", self.task("a", "app.py"))]
        self.init()
        (self.project / "app.py").write_text("print('intermediate')\n", encoding="utf-8")
        self.git("add", "app.py")
        self.git("commit", "-m", "Intermediate")
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        self.git("add", "app.py")
        self.git("commit", "-m", "Wrong parent", "-m", "Daodan-Task: test-run wave 1/1")
        committed = self.committed_task(candidate, self.git("rev-parse", "HEAD"))
        refusal = self.invoke("update", {"waves": [self.wave("w1", committed)]},
                              ["--expected-revision", "2"], ok=False)
        self.assertIn("parent differs", refusal.stderr)

    def test_commit_cannot_include_paths_outside_the_task_write_set(self):
        self.make_repo()
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        reviewed = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": reviewed["snapshot"]["digest"], "head": reviewed["head"]}
        self.use_review(candidate)
        self.payload["waves"] = [self.wave("w1", self.task("a", "app.py"))]
        self.init()
        (self.project / "other.py").write_text("print('foreign')\n", encoding="utf-8")
        self.git("add", "app.py", "other.py")
        self.git("commit", "-m", "Too broad", "-m", "Daodan-Task: test-run wave 1/1")
        committed = self.committed_task(candidate, self.git("rev-parse", "HEAD"))
        refusal = self.invoke("update", {"waves": [self.wave("w1", committed)]},
                              ["--expected-revision", "2"], ok=False)
        self.assertIn("outside its write_set", refusal.stderr)

    def test_commit_trailer_must_name_the_actual_wave(self):
        self.make_repo()
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        reviewed = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": reviewed["snapshot"]["digest"], "head": reviewed["head"]}
        self.use_review(candidate)
        self.payload["waves"] = [self.wave("w1", self.task("a", "app.py"))]
        self.init()
        self.git("add", "app.py")
        self.git("commit", "-m", "Wrong wave", "-m", "Daodan-Task: test-run wave 999/999")
        committed = self.committed_task(candidate, self.git("rev-parse", "HEAD"))
        refusal = self.invoke("update", {"waves": [self.wave("w1", committed)]},
                              ["--expected-revision", "2"], ok=False)
        self.assertIn("correct run and wave trailer", refusal.stderr)

    def test_resume_reconciles_a_commit_created_before_the_crash(self):
        self.make_repo()
        (self.project / "app.py").write_text("print('reviewed')\n", encoding="utf-8")
        reviewed = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": reviewed["snapshot"]["digest"], "head": reviewed["head"]}
        self.use_review(candidate)
        green = self.committed_task(candidate)
        green["status"] = "pending"
        del green["commit_sha"]
        self.payload["waves"] = [self.wave("w1", green)]
        self.init()
        self.git("add", "app.py")
        self.git("commit", "-m", "Crash after commit", "-m", "Daodan-Task: test-run wave 1/1")
        resumed = self.invoke("resume", {"authorizations": self.payload["authorizations"]})
        task = resumed["waves"][0]["tasks"][0]
        self.assertEqual(task["status"], "committed")
        self.assertEqual(task["commit_sha"], self.git("rev-parse", "HEAD"))
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "2")

    def test_legacy_records_are_readable_but_not_resumable_without_current_gates(self):
        record = self.init()
        legacy = {**record, "status": "complete", "phases": {"audit": {"status": "complete"}},
                  "deliveries": {"audit": {"status": "delivered", "output": self.report()}},
                  "waves": [{"id": "w1", "status": "sealed",
                             "tasks": [{"id": "a", "status": "committed", "write_set": ["app.py"],
                                        "oracle": {"command": "pytest", "expected_failure": "x"},
                                        "verification": {"command": "pytest"}}]}]}
        (self.project / ".daodan/runs/test-run/work.json").write_text(json.dumps(legacy), encoding="utf-8")
        self.invoke("show", ok=False)
        historical = self.invoke("show", extra=["--historical"])
        self.assertTrue(historical["historical"])
        self.assertEqual(historical["waves"][0]["status"], "sealed")
        self.invoke("resume", {"authorizations": self.payload["authorizations"]}, ok=False)

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
        self.assertIn("cites evidence", self.check_draft({"rulings": [{**ruling, "evidence": []}]}, ok=False).stderr)

    def test_an_authorization_asked_later_is_an_append_only_grant(self):
        record = self.init()
        grant = {"id": "G1", "kind": "commit", "scope": ["src"], "granted_at": "wave-1",
                 "source": {"kind": "user", "reference": "answer to: commit the wave?"}}
        granted = self.invoke("update", {"grants": [grant]}, ["--expected-revision", "0"])
        self.assertEqual(granted["grants"], [grant])
        self.assertEqual(granted["authorizations"], record["authorizations"])
        withdrawn = self.invoke("update", {"grants": []}, ["--expected-revision", "1"], ok=False)
        self.assertIn("append-only", withdrawn.stderr)
        assumed = {**grant, "id": "G2", "source": {"kind": "coordinator", "reference": "seemed fine"}}
        self.assertIn("user's answer", self.invoke("update", {"grants": [grant, assumed]},
                                                    ["--expected-revision", "1"], ok=False).stderr)
        unknown = {**grant, "id": "G2", "kind": "everything"}
        self.assertIn("kind must be one of", self.invoke("update", {"grants": [grant, unknown]},
                                                         ["--expected-revision", "1"], ok=False).stderr)
        widened = self.invoke("update", {"authorizations": {"commit": True}}, ["--expected-revision", "1"], ok=False)
        self.assertIn("cannot replace identity, scope, authorization", widened.stderr)

    def test_each_review_bounds_only_the_deliveries_bound_to_it(self):
        light = {"id": "R1", "stage": "wave-1", "schema": "daodan/review-roster/v1", "shape": "light",
                 "kind": "changeset", "tier": "light", "roster": ["senior-review:code-auditor"],
                 "support": ["senior-review:premise-auditor", "work-controller:isolated-worker"],
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
        self.assertIn("tier must be one of", self.check_draft({"reviews": [{**light, "tier": "enormous"}]}, ok=False).stderr)
        self.assertIn("kind must be one of", self.check_draft({"reviews": [{**light, "kind": "poem"}]}, ok=False).stderr)
        self.assertIn("roster must be a nonempty list",
                      self.check_draft({"reviews": [{**light, "roster": []}]}, ok=False).stderr)

    def git(self, *arguments):
        return subprocess.run(["git", "-C", str(self.project), *arguments], capture_output=True,
                              text=True, encoding="utf-8", check=True).stdout.strip()

    def make_repo(self):
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.git("add", "app.py")
        self.git("commit", "-q", "-m", "base")

    def test_the_agenda_binds_a_task_to_its_branch_and_session(self):
        self.make_repo()
        self.payload["workspace"] = {"mode": "BRANCH", "branch": "task/one", "base_sha": self.git("rev-parse", "HEAD")}
        self.invoke("init", self.payload, ["--session", "s1"])
        self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}, extra=["--session", "s1"])
        agenda = self.invoke("agenda", extra=["--branch", "task/one"])
        row = agenda["tasks"][0]
        self.assertEqual((row["run_id"], row["branch"], row["holder"]["session"], row["questions"], row["loop"]),
                         ("test-run", "task/one", "s1", 1, True))
        self.assertTrue((self.project / ".daodan/agenda.json").is_file())
        patch = {"phases": {"audit": {"status": "in_progress"}}}
        held = self.invoke("update", patch, ["--expected-revision", "1", "--session", "s2"], ok=False)
        self.assertIn("held by session s1", held.stderr)
        unnamed = self.invoke("update", patch, ["--expected-revision", "1"], ok=False)
        self.assertIn("held by session s1", unnamed.stderr)
        taken = self.invoke("update", patch, ["--expected-revision", "1", "--session", "s2", "--take-over"])
        self.assertEqual(taken["revision"], 2)
        row = self.invoke("agenda")["tasks"][0]
        self.assertEqual((row["holder"]["session"], row["phase"]), ("s2", "audit"))
        nameless = self.invoke("update", patch, ["--expected-revision", "2", "--take-over"], ok=False)
        self.assertIn("--take-over needs --session", nameless.stderr)
        self.invoke("answer", {"question": "Q1", "text": "yes", "source": "chat"}, ["--session", "s2"])
        self.assertEqual(self.invoke("agenda")["tasks"][0]["questions"], 0)
        self.assertEqual(self.invoke("show")["questions"][0]["answer"], "yes")
        done = {"status": "complete", "phases": {"audit": {"status": "complete"}},
                "deliveries": {"audit": {"status": "delivered", "output": self.report()}}}
        self.assertIn("held by session s2",
                      self.invoke("update", done, ["--expected-revision", "3", "--session", "s1"], ok=False).stderr)
        self.assertEqual(self.invoke("update", done, ["--expected-revision", "3", "--session", "s2"])["status"], "complete")

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
        rows = self.invoke("agenda", extra=["--branch", "task/wt", "--run-id", "wt-run"])["tasks"]
        self.assertEqual([r["run_id"] for r in rows], ["wt-run"])
        self.git("worktree", "remove", "--force", str(worktree))
        self.assertTrue((self.project / ".daodan/runs/wt-run/work.json").is_file())

    def test_environment_is_validated(self):
        good = {"interpreter": ".venv/Scripts/python.exe", "commands": {"test": "pytest -q", "lint": "ruff check ."}}
        self.check_draft({"environment": good})
        self.assertIn("is not one of", self.check_draft({"environment": {**good, "commands": {"deploy": "x"}}}, ok=False).stderr)
        self.assertIn("environment.interpreter is required", self.check_draft({"environment": {"commands": {}}}, ok=False).stderr)

    def test_loop_sections_are_validated_inside_the_record_too(self):
        self.payload["waves"] = [self.wave("w1", self.task("a", "src/common.py"), self.task("b", "src/common.py"))]
        refusal = self.invoke("init", self.payload, ok=False)
        self.assertIn("share write_set files", refusal.stderr)


    def test_questions_change_only_through_ask_and_answer(self):
        question = {"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}
        refused = self.invoke("init", {**self.payload, "questions": [question]}, ok=False)
        self.assertIn("only through ask and answer", refused.stderr)
        self.init()
        patched = self.invoke("update", {"questions": [question]}, ["--expected-revision", "0"], ok=False)
        self.assertIn("only through ask and answer", patched.stderr)
        self.ask(question)
        self.assertIn("is not one of", self.answer("Q1", "yes", source="email", ok=False).stderr)
        self.assertIn("empty answer", self.answer("Q1", " ", ok=False).stderr)
        self.assertEqual(self.answer("Q1", "yes", source="chat")["open"], 0)

    def test_a_task_waits_for_the_questions_it_consumes(self):
        self.init()
        self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
        waiting = self.task("a", "src/a.py", consumes=["question:Q1"])
        self.invoke("update", {"waves": [self.wave("w1", waiting)]}, ["--expected-revision", "1"])
        unknown = self.task("a", "src/a.py", consumes=["question:Q9"])
        self.assertIn("does not ask Q9", self.invoke("update", {"waves": [self.wave("w1", unknown)]},
                                                     ["--expected-revision", "2"], ok=False).stderr)
        running = {**waiting, "status": "running"}
        current = self.runtime["project_binding"](self.project, self.payload["scope"], self.project / ".daodan")
        candidate = {"digest": current["snapshot"]["digest"], "head": None}
        plan = self.review(candidate, "R0", "plan")
        plan["kind"] = "plan"
        planned = self.wave("w1", waiting, plan_candidate=candidate,
                            plan_review={"id": "R0", "verdict": "PASS",
                                         "snapshot": candidate["digest"], "head": None})
        fingerprint = self.runtime["plan_fingerprint"](planned)
        planned["plan_review"]["plan_sha256"] = fingerprint
        plan["grounding"]["plan_sha256"] = fingerprint
        self.invoke("update", {"waves": [planned], "reviews": [plan],
                               "deliveries": self.review_delivery(plan, "test-run")}, ["--expected-revision", "2"])
        running_planned = {**planned, "tasks": [running]}
        self.assertIn("consumes question:Q1, which is not answered",
                      self.invoke("update", {"waves": [running_planned]},
                                  ["--expected-revision", "3"], ok=False).stderr)
        self.answer("Q1", "yes")
        self.invoke("update", {"waves": [running_planned]}, ["--expected-revision", "4"])

    def test_completion_requires_every_question_closed(self):
        self.init()
        self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
        done = {"status": "complete", "phases": {"audit": {"status": "complete"}},
                "deliveries": {"audit": {"status": "delivered", "output": self.report()}}}
        refused = self.invoke("update", done, ["--expected-revision", "1"], ok=False)
        self.assertIn("every question answered or withdrawn: Q1", refused.stderr)
        self.answer("Q1", "yes")
        self.assertEqual(self.invoke("update", done, ["--expected-revision", "2"])["status"], "complete")

    def test_stored_questions_load_as_written(self):
        self.init()
        path = self.project / ".daodan/runs/test-run/work.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["questions"] = [
            {"id": "Q1", "phase": "audit", "text": "undecided: keep the sync API", "answer": "yes", "source": "email"},
            {"id": "Q2", "phase": "audit", "text": "undecided: drop the export"}]
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(self.invoke("show")["questions"][0]["source"], "email")
        self.invoke("update", {"phases": {"audit": {"status": "complete"}}}, ["--expected-revision", "0"])
        resumed = self.invoke("resume", {"authorizations": self.payload["authorizations"]})
        self.assertEqual([q["id"] for q in resumed["pending_questions"]], ["Q2"])

    def ask(self, question, ok=True, extra=()):
        return self.invoke("ask", question, extra, ok=ok)

    def answer(self, qid, text, source="question-tool", ok=True, **extra):
        return self.invoke("answer", {"question": qid, "text": text, "source": source, **extra}, ok=ok)

    def test_ask_records_a_shaped_question_once(self):
        self.init()
        q1 = {"id": "Q1", "phase": "interview", "text": "Keep the sync API?\nToday `api.py:12` serves it to two clients."}
        self.assertEqual(self.ask(q1), {"question": "Q1", "revision": 1, "open": 1})
        self.assertEqual(self.ask(q1), {"question": "Q1", "revision": 1, "open": 1, "existing": True})
        self.assertIn("already asks", self.ask({**q1, "text": "Drop the sync API?"}, ok=False).stderr)
        self.assertIn("first line must be the question", self.ask({**q1, "id": "Q2", "text": "Sync API"}, ok=False).stderr)
        self.assertIn("ask records a question only", self.ask({**q1, "id": "Q3", "answer": "yes"}, ok=False).stderr)

    def test_ask_returns_the_open_question_already_asking_it(self):
        self.init()
        self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
        same = self.ask({"id": "Q7", "phase": "interview", "text": "keep the  SYNC api?\nother context"})
        self.assertEqual((same["question"], same["revision"], same["existing"]), ("Q1", 1, True))
        self.assertEqual(self.ask({"id": "Q8", "phase": "waves", "text": "Keep the sync API?"})["question"], "Q8")
        self.answer("Q1", "no, split wave 2")
        again = self.ask({"id": "Q9", "phase": "interview", "text": "Keep the sync API?\nRevision 2 drops a client."})
        self.assertEqual((again["question"], again["revision"], again["open"]), ("Q9", 4, 2))

    def test_answer_unblocks_only_tasks_whose_questions_are_all_answered(self):
        self.init()
        self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
        self.ask({"id": "Q2", "phase": "interview", "text": "Which clients migrate first?"})
        wave = self.wave("w1", self.task("a", "src/a.py", consumes=["question:Q1"]),
                         self.task("b", "src/b.py", consumes=["question:Q1", "question:Q2"]),
                         self.task("c", "src/c.py"))
        self.invoke("update", {"waves": [wave]}, ["--expected-revision", "2"])
        self.assertEqual(self.answer("Q1", "yes")["unblocked"], ["a"])
        resumed = self.invoke("resume", {"authorizations": self.payload["authorizations"]})
        self.assertEqual(resumed["waiting"], {"b": ["Q2"]})
        self.assertEqual(self.answer("Q2", "web first", source="chat"),
                         {"question": "Q2", "revision": 5, "open": 0, "unblocked": ["b"]})

    def test_a_repeated_answer_changes_nothing_and_a_different_one_is_refused(self):
        self.init()
        self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
        self.answer("Q1", "yes")
        again = self.answer("Q1", "yes")
        self.assertEqual((again["revision"], again["unchanged"]), (2, True))
        self.assertTrue(self.answer("Q1", "yes", source="continue")["unchanged"])
        self.assertIn("a changed answer is a new question", self.answer("Q1", "no", ok=False).stderr)
        self.assertIn("does not ask Q9", self.answer("Q9", "yes", ok=False).stderr)

    def test_a_withdrawn_question_closes_without_unblocking(self):
        self.init()
        self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
        self.invoke("update", {"waves": [self.wave("w1", self.task("a", "src/a.py", consumes=["question:Q1"]))]},
                    ["--expected-revision", "1"])
        withdrawn = self.answer("Q1", "drop the export goal", source="chat", withdraw=True)
        self.assertEqual((withdrawn["unblocked"], withdrawn["replan"], withdrawn["open"]), ([], ["a"], 0))
        self.assertEqual(self.invoke("resume", {"authorizations": self.payload["authorizations"]})["replan"], ["a"])
        self.assertEqual(self.invoke("agenda")["tasks"][0]["questions"], 0)
        retried = self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
        self.assertEqual((retried["existing"], retried["withdrawn"]), (True, True))

    def test_answer_keeps_the_users_words_exactly(self):
        self.init()
        self.ask({"id": "Q1", "phase": "interview", "text": "Quale finestra di fermo?"})
        words = 'Sì, ma "solo" lunedì\nseconda riga, perché sì'
        self.answer("Q1", words)
        stored = self.invoke("show")["questions"][0]
        self.assertEqual((stored["answer"], stored["source"]), (words, "question-tool"))
        self.assertIn("answered_at", stored)
        self.assertEqual(self.invoke("show").get("grants", []), [])

    def test_the_question_rule_ships_with_the_skill(self):
        skill = SCRIPT.parents[1]
        self.assertIn("`ask`", (skill / "references/questions.md").read_text(encoding="utf-8"))
        self.assertIn("references/questions.md", (skill / "SKILL.md").read_text(encoding="utf-8"))

    def test_ask_respects_the_task_holder(self):
        self.invoke("init", self.payload, ["--session", "s1"])
        held = self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}, ok=False, extra=["--session", "s2"])
        self.assertIn("held by session s1", held.stderr)


class FirstUseTests(ProtocolCase):
    """The read-only first-use probe: a map or a run ends first use, a bare .daodan/ does not."""

    def probe(self, project=None):
        stdout = io.StringIO()
        args = ["first-use", "--project", str(project or self.project)]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.runtime["main"](args), 0)
        return json.loads(stdout.getvalue())

    def test_probe_of_a_fresh_project_reports_first_use_and_writes_nothing(self):
        self.git("init", "-q")
        before = sorted(p.name for p in self.project.iterdir())
        self.assertEqual(self.probe(), {"first_use": True})
        self.assertEqual(sorted(p.name for p in self.project.iterdir()), before)
        self.assertFalse((self.project / ".daodan").exists())

    def test_a_map_directory_ends_first_use(self):
        self.git("init", "-q")
        (self.project / ".codebase-map").mkdir()
        self.assertEqual(self.probe(), {"first_use": False})

    def test_a_bare_daodan_directory_keeps_first_use_and_a_run_directory_ends_it(self):
        """The process store and a declined decision-record answer create .daodan/ before any run."""
        self.git("init", "-q")
        (self.project / ".daodan/processes").mkdir(parents=True)
        (self.project / ".daodan/adr-declined").write_text("declined\n", encoding="utf-8")
        (self.project / ".daodan/.daodan-root").touch()
        self.assertEqual(self.probe(), {"first_use": True})
        (self.project / ".daodan/runs").mkdir()
        self.assertEqual(self.probe(), {"first_use": False})

    def test_an_adr_index_alone_is_not_daodan_state(self):
        self.git("init", "-q")
        (self.project / "docs/adr").mkdir(parents=True)
        (self.project / "docs/adr/README.md").write_text("# Decision records\n", encoding="utf-8")
        self.assertEqual(self.probe(), {"first_use": True})

    def test_probe_from_a_linked_worktree_reports_the_main_checkout(self):
        self.committed_project()
        worktree = self.temp / "wt"
        self.git("worktree", "add", "-q", "-b", "task/wt", str(worktree))
        self.assertTrue(self.probe(worktree)["first_use"])
        (self.project / ".daodan/runs").mkdir(parents=True)
        self.assertFalse(self.probe(worktree)["first_use"])


if __name__ == "__main__":
    unittest.main()
