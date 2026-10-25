"""Regressions for state, completion and integration findings from source review."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.errors import OutcomeUnknownError, StateError


def agent(commit=False, attempts=2):
    job = {
        "id": "edit",
        "type": "agent",
        "summary": "edit",
        "produces": [{"name": "out", "type": "text", "path": "out.txt"}],
        "write_set": ["out.txt"],
        "max_attempts": attempts,
        "timeout_seconds": 30,
    }
    if commit:
        job["commit"] = {"message": "work-controller: partial"}
    return job


def process(jobs, attempts=20):
    return {
        "schema": "work-controller/process/v1",
        "kind": "graph",
        "id": "regression",
        "objective": "exercise regression",
        "jobs": jobs,
        "budget": {"max_attempts": attempts, "max_seconds": 300},
    }


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.home = root / "home"
        self.engine = Engine(self.home, self.workspace)

    def start_run(self, jobs, *, attempts=20, grants=None, run_id=None):
        path = self.workspace / f"process-{len(list(self.workspace.glob('process-*.yaml')))}.yaml"
        path.write_text(dump_definition(process(jobs, attempts)), encoding="utf-8")
        return self.engine.start(path, grants=grants or [], run_id=run_id)["id"]

    def running_attempt(self, run_id):
        attempt_id = self.engine.claim(run_id, "host")["attempt_id"]
        self.engine.start_attempt(attempt_id, "host")
        return attempt_id

    def test_expired_reservation_revocation_is_committed(self):
        run_id = self.start_run([agent()])
        packet = self.engine.claim(run_id, "host")
        expires = self.engine.store.attempt(packet["attempt_id"])["expires_at"]
        with patch("work_controller.store.time.time", return_value=expires), self.assertRaisesRegex(StateError, "expired"):
            self.engine.start_attempt(packet["attempt_id"], "host")
        self.assertEqual(self.engine.store.attempt(packet["attempt_id"])["status"], "revoked")
        self.assertEqual(self.engine.store.job(run_id, "edit")["status"], "pending")
        replacement = self.engine.claim(run_id, "host")
        self.assertEqual(replacement["attempt"], 2)

    def test_exact_global_budget_still_allows_success_finish(self):
        run_id = self.start_run([agent(attempts=1)], attempts=1)
        attempt_id = self.running_attempt(run_id)
        (self.workspace / "out.txt").write_text("done", encoding="utf-8")
        self.engine.complete(attempt_id, "host", "done", "pass")
        self.assertEqual(self.engine.drive(run_id, "host")["status"], "complete")
        self.assertEqual(self.engine.status(run_id)["outcome"], "VERIFIED_SUCCESS")

    def test_client_event_cannot_block_internal_finish_event(self):
        run_id = self.start_run([agent(attempts=1)], attempts=1)
        attempt_id = self.running_attempt(run_id)
        (self.workspace / "out.txt").write_text("done", encoding="utf-8")
        self.engine.complete(attempt_id, "host", "run-finished", "pass")
        self.engine.finish(run_id)
        kinds = [event["kind"] for event in self.engine.events(run_id, limit=100)]
        self.assertIn("run.completed", kinds)
        self.assertEqual(self.engine.status(run_id)["status"], "complete")

    def test_wrong_holder_has_no_artifact_or_commit_side_effect(self):
        with patch("work_controller.engine.GitSupport") as git_class:
            git = git_class.return_value
            run_id = self.start_run([agent(commit=True)], grants=["commit"])
            attempt_id = self.running_attempt(run_id)
            (self.workspace / "out.txt").write_text("done", encoding="utf-8")
            with self.assertRaises(StateError):
                self.engine.complete(attempt_id, "foreign", "foreign-delivery", "pass")
            git.commit_paths.assert_not_called()
            self.assertIsNone(self.engine.store.latest_artifact(run_id, "out"))
            self.assertEqual(self.engine.store.attempt(attempt_id)["status"], "running")

    def test_new_event_for_delivered_attempt_does_not_reingest_or_recommit(self):
        sha = "a" * 40
        with patch("work_controller.engine.GitSupport") as git_class:
            git = git_class.return_value
            git.commit_paths.return_value = sha
            run_id = self.start_run([agent(commit=True)], grants=["commit"])
            attempt_id = self.running_attempt(run_id)
            (self.workspace / "out.txt").write_text("first", encoding="utf-8")
            self.engine.complete(attempt_id, "host", "first-delivery", "pass")
            (self.workspace / "out.txt").write_text("changed", encoding="utf-8")
            with self.assertRaises(StateError):
                self.engine.complete(attempt_id, "host", "second-delivery", "pass")
            self.assertEqual(git.commit_paths.call_count, 1)
            self.assertEqual(self.engine.store.latest_artifact(run_id, "out")["version"], 1)

    def test_concurrent_completion_admits_effects_once(self):
        started = threading.Event()
        release = threading.Event()
        sha = "b" * 40

        def commit(*args):
            started.set()
            if not release.wait(timeout=10):
                raise TimeoutError("test did not release the commit")
            return sha

        with patch("work_controller.engine.GitSupport") as git_class:
            git = git_class.return_value
            git.commit_paths.side_effect = commit
            run_id = self.start_run([agent(commit=True)], grants=["commit"])
            attempt_id = self.running_attempt(run_id)
            (self.workspace / "out.txt").write_text("done", encoding="utf-8")
            peer = Engine(self.home, self.workspace)
            results, errors = [], []

            def complete(engine):
                try:
                    results.append(engine.complete(attempt_id, "host", "shared-delivery", "pass"))
                except Exception as exc:  # noqa: BLE001 - every thread error must reach the assertions.
                    errors.append(exc)

            first = threading.Thread(target=complete, args=(self.engine,))
            second = threading.Thread(target=complete, args=(peer,))
            first.start()
            self.assertTrue(started.wait(timeout=5))
            second.start()
            second.join(timeout=10)
            self.assertFalse(second.is_alive())
            release.set()
            first.join(timeout=10)
            self.assertFalse(first.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)
            self.assertEqual(sum(bool(result.get("in_progress")) for result in results), 1)
            self.assertEqual(sum(result.get("verdict") == "pass" for result in results), 2)
            self.assertEqual(git.commit_paths.call_count, 1)
            deliveries = [e for e in self.engine.events(run_id, limit=100) if e["kind"] == "delivery.completed"]
            self.assertEqual(len(deliveries), 1)
            self.assertEqual(self.engine.store.latest_artifact(run_id, "out")["version"], 1)

    def test_commit_sha_survives_a_delivery_database_failure(self):
        sha = "c" * 40
        with patch("work_controller.engine.GitSupport") as git_class:
            git = git_class.return_value
            git.commit_paths.return_value = sha
            run_id = self.start_run([agent(commit=True)], grants=["commit"])
            attempt_id = self.running_attempt(run_id)
            (self.workspace / "out.txt").write_text("done", encoding="utf-8")
            with patch.object(self.engine.store, "complete", side_effect=StateError("injected database failure")), self.assertRaisesRegex(StateError, "injected"):
                self.engine.complete(attempt_id, "host", "delivery-retry", "pass")
            self.assertEqual(self.engine.store.attempt(attempt_id)["commit_sha"], sha)
            self.assertEqual(self.engine.store.attempt(attempt_id)["status"], "running")
            result = self.engine.complete(attempt_id, "host", "delivery-retry", "pass")
            self.assertEqual(result["commit_sha"], sha)
            self.assertEqual(git.commit_paths.call_count, 1)

    def test_execution_ticket_cannot_be_rebound_to_another_completed_run(self):
        store = self.engine.store
        store.map_open("map", "Finish the declared run")
        run_a = self.start_run([agent()], run_id="run-a")
        run_b = self.start_run([agent()], run_id="run-b")
        attempt_b = self.running_attempt(run_b)
        (self.workspace / "out.txt").write_text("done", encoding="utf-8")
        self.engine.complete(attempt_b, "host", "done-b", "pass")
        self.engine.drive(run_b, "host")
        store.ticket_add("map", "execute", "execution", "Execute A", run_id=run_a)
        store.ticket_claim("map", "execute", "session")
        with self.assertRaises(StateError):
            store.ticket_close("map", "execute", "session", source="run", run_id=run_b)
        self.assertEqual(store.ticket("map", "execute")["status"], "in_progress")

    def test_identical_failure_without_error_is_idempotent(self):
        run_id = self.start_run([agent()])
        attempt_id = self.running_attempt(run_id)
        first = self.engine.complete(attempt_id, "host", "failure", "fail")
        second = self.engine.complete(attempt_id, "host", "failure", "fail")
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        failures = [e for e in self.engine.events(run_id, limit=100) if e["kind"] == "delivery.completed"]
        self.assertEqual(len(failures), 1)

    def test_git_unknown_recovers_with_sha_without_a_second_commit(self):
        with patch("work_controller.engine.GitSupport") as git_class:
            git = git_class.return_value
            git.commit_paths.side_effect = OutcomeUnknownError("rev-parse failed after commit")
            run_id = self.start_run([agent(commit=True)], grants=["commit"])
            attempt_id = self.running_attempt(run_id)
            (self.workspace / "out.txt").write_text("done", encoding="utf-8")
            with self.assertRaises(OutcomeUnknownError):
                self.engine.complete(attempt_id, "host", "git-unknown", "pass")
            self.assertEqual(self.engine.store.attempt(attempt_id)["status"], "unknown")
            self.assertEqual(self.engine.status(run_id)["status"], "blocked")
            with self.assertRaises(StateError):
                self.engine.resolve_unknown(attempt_id, confirm_stopped=True)
            sha = "d" * 40
            recovered = self.engine.resolve_unknown(
                attempt_id, confirm_stopped=True, commit_sha=sha
            )
            self.assertEqual(recovered["status"], "running")
            result = self.engine.complete(attempt_id, "host", "git-unknown", "pass")
            self.assertEqual(result["commit_sha"], sha)
            self.assertEqual(git.commit_paths.call_count, 1)

    def test_git_unknown_requires_explicit_discard_before_a_new_attempt(self):
        with patch("work_controller.engine.GitSupport") as git_class:
            git = git_class.return_value
            git.commit_paths.side_effect = OutcomeUnknownError("commit outcome unknown")
            run_id = self.start_run([agent(commit=True)], grants=["commit"])
            attempt_id = self.running_attempt(run_id)
            (self.workspace / "out.txt").write_text("done", encoding="utf-8")
            with self.assertRaises(OutcomeUnknownError):
                self.engine.complete(attempt_id, "host", "discard-unknown", "pass")
            with self.assertRaises(StateError):
                self.engine.resolve_unknown(attempt_id, confirm_stopped=True)
            discarded = self.engine.resolve_unknown(
                attempt_id, confirm_stopped=True, discard_commit_outcome=True
            )
            self.assertEqual(discarded["status"], "failed")
            with self.assertRaises(StateError):
                self.engine.complete(attempt_id, "host", "discard-unknown", "pass")
            next_packet = self.engine.claim(run_id, "host")
            self.assertEqual(next_packet["attempt"], 2)

    def test_note_commit_failure_blocks_and_recovers_the_known_sha(self):
        sha = "e" * 40
        with patch("work_controller.engine.GitSupport") as git_class:
            git = git_class.return_value
            git.commit_paths.return_value = sha
            run_id = self.start_run([agent(commit=True)], grants=["commit"])
            attempt_id = self.running_attempt(run_id)
            (self.workspace / "out.txt").write_text("done", encoding="utf-8")
            with patch.object(self.engine.store, "note_commit", side_effect=StateError("temporary database failure")), self.assertRaises(OutcomeUnknownError):
                self.engine.complete(attempt_id, "host", "note-unknown", "pass")
            self.assertEqual(self.engine.store.attempt(attempt_id)["status"], "unknown")
            self.assertEqual(self.engine.store.attempt(attempt_id)["commit_sha"], sha)
            self.engine.resolve_unknown(attempt_id, confirm_stopped=True, commit_sha=sha)
            result = self.engine.complete(attempt_id, "host", "note-unknown", "pass")
            self.assertEqual(result["commit_sha"], sha)
            self.assertEqual(git.commit_paths.call_count, 1)

    def test_reconciled_completion_is_rejected_not_left_in_progress(self):
        run_id = self.start_run([agent()])
        attempt_id = self.running_attempt(run_id)
        self.assertEqual(
            self.engine.store.begin_completion(attempt_id, "host", "old-completion", "pass", None, None),
            "proceed",
        )
        self.engine.resume(run_id)
        self.engine.resolve_unknown(attempt_id, confirm_stopped=True)
        with self.assertRaises(StateError):
            self.engine.complete(attempt_id, "host", "old-completion", "pass")
        self.assertEqual(self.engine.store.attempt(attempt_id)["status"], "failed")

    def test_workspace_mismatch_is_rejected_before_handoff(self):
        run_id = self.start_run([agent()])
        packet = self.engine.claim(run_id, "host")
        other_workspace = Path(self.temp.name) / "other-workspace"
        other_workspace.mkdir()
        peer = Engine(self.home, other_workspace)
        with self.assertRaisesRegex(StateError, "workspace mismatch"):
            peer.packet(packet["attempt_id"], "host")
        with self.assertRaisesRegex(StateError, "workspace mismatch"):
            peer.drive(run_id, "host")

    def test_supervision_escalates_when_global_budget_is_exhausted(self):
        import sys

        failing = {
            "id": "check", "type": "command", "summary": "fails",
            "command": {"argv": [sys.executable, "-c", "raise SystemExit(3)"]},
            "max_attempts": 2, "timeout_seconds": 30,
        }
        run_id = self.start_run([failing], attempts=1, grants=["shell"])
        result = self.engine.drive(run_id, "local")
        self.assertEqual(result["run"]["outcome"], "BUDGET_EXHAUSTED")
        attempt_id = next(e["attempt_id"] for e in self.engine.events(run_id, limit=100) if e["kind"] == "delivery.completed")
        supervised = self.engine.supervise(attempt_id)
        self.assertEqual(supervised["action"], "ESCALATE")
        self.assertEqual(supervised["observation"]["global_attempts_used"], 1)
        self.assertEqual(supervised["observation"]["run_status"], "stopped")

    def test_observation_queries_the_current_attempt_after_many_old_events(self):
        run_id = self.start_run([agent()])
        attempt_id = self.running_attempt(run_id)
        with self.engine.store.transaction() as conn:
            for index in range(105):
                self.engine.store._event(conn, run_id, f"noise-{index}", "test.noise", {})
            self.engine.store._event(
                conn, run_id, "current-marker", "test.marker", {}, attempt_id=attempt_id
            )
        observation = self.engine.supervise(attempt_id)["observation"]
        self.assertEqual(observation["events"][-1]["kind"], "test.marker")
        self.assertLessEqual(len(observation["events"]), 8)


if __name__ == "__main__":
    unittest.main()
