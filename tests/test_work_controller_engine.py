"""Behavioral tests for the durable engine and its bounded public views."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.errors import AuthorizationError, StateError


def job(job_id, kind="agent", **extra):
    data = {
        "id": job_id,
        "type": kind,
        "summary": job_id,
        "max_attempts": 2,
        "timeout_seconds": 30,
    }
    data.update(extra)
    return data


def process(jobs, **extra):
    data = {
        "schema": "work-controller/process/v1",
        "kind": "graph",
        "id": "test-process",
        "objective": "exercise durable execution",
        "jobs": jobs,
        "budget": {"max_attempts": 20, "max_seconds": 300},
    }
    data.update(extra)
    return data


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.home = root / "home"
        self.engine = Engine(self.home, self.workspace)

    def definition(self, data, name="process.yaml"):
        path = self.workspace / name
        path.write_text(dump_definition(data), encoding="utf-8")
        return path

    def test_command_graph_exchanges_a_real_artifact_and_completes(self):
        producer = job(
            "produce",
            "command",
            command={"argv": [
                # Python is resolved explicitly; no shell command line is involved.
                __import__("sys").executable,
                "-c",
                "from pathlib import Path; Path('out.txt').write_text('hello', encoding='utf-8')",
            ]},
            produces=[{"name": "document", "type": "text", "path": "out.txt"}],
            write_set=["out.txt"],
            max_attempts=1,
        )
        verifier = job(
            "verify",
            "command",
            command={"argv": [
                __import__("sys").executable,
                "-c",
                "from pathlib import Path; assert Path('out.txt').read_text(encoding='utf-8') == 'hello'",
            ]},
            needs=["produce"],
            consumes=["document"],
            max_attempts=1,
        )
        started = self.engine.start(self.definition(process([producer, verifier])), grants=["shell"])
        result = self.engine.drive(started["id"], "local")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(self.engine.status(started["id"])["outcome"], "VERIFIED_SUCCESS")
        artifact = self.engine.store.latest_artifact(started["id"], "document")
        self.assertEqual(self.engine.artifacts.read(artifact["digest"]), b"hello")
        events = self.engine.events(started["id"], limit=100)
        self.assertEqual(len([e for e in events if e["kind"] == "attempt.reserved"]), 2)
        self.assertEqual(events[-1]["kind"], "run.completed")

    def test_shell_and_commit_require_distinct_grants(self):
        command = job("check", "command", command={"argv": ["anything"]}, max_attempts=1)
        with self.assertRaises(AuthorizationError):
            self.engine.start(self.definition(process([command])))
        committed = job(
            "edit",
            produces=[{"name": "out", "type": "text", "path": "out.txt"}],
            write_set=["out.txt"],
            commit={"message": "partial"},
        )
        with self.assertRaises(AuthorizationError):
            self.engine.start(self.definition(process([committed])))

    def test_agent_handoff_and_duplicate_completion_are_durable(self):
        agent = job(
            "edit",
            produces=[{"name": "out", "type": "text", "path": "out.txt"}],
            write_set=["out.txt"],
        )
        run_id = self.engine.start(self.definition(process([agent])))["id"]
        waiting = self.engine.drive(run_id, "host")
        self.assertEqual(waiting["status"], "waiting_for_agent")
        packet = waiting["packet"]
        self.assertNotIn("definition_yaml", packet)
        self.engine.start_attempt(packet["attempt_id"], "host")
        (self.workspace / "out.txt").write_text("delivered", encoding="utf-8")
        delivered = self.engine.complete(packet["attempt_id"], "host", "delivery-1", "pass")
        self.assertFalse(delivered["duplicate"])
        repeated = self.engine.complete(packet["attempt_id"], "host", "delivery-1", "pass")
        self.assertTrue(repeated["duplicate"])
        events = self.engine.events(run_id, limit=100)
        self.assertEqual(len([e for e in events if e["kind"] == "delivery.completed"]), 1)
        self.assertEqual(len([e for e in events if e["kind"] == "attempt.reserved"]), 1)
        self.assertEqual(self.engine.store.latest_artifact(run_id, "out")["version"], 1)
        self.assertEqual(self.engine.drive(run_id, "host")["status"], "complete")

    def test_resume_never_blindly_restarts_an_unknown_worker(self):
        agent = job(
            "edit",
            produces=[{"name": "out", "type": "text", "path": "out.txt"}],
            write_set=["out.txt"],
        )
        run_id = self.engine.start(self.definition(process([agent])))["id"]
        packet = self.engine.claim(run_id, "host")
        self.engine.start_attempt(packet["attempt_id"], "host")
        resumed = self.engine.resume(run_id)
        self.assertEqual(resumed["status"], "blocked")
        self.assertIsNone(self.engine.claim(run_id, "host"))
        with self.assertRaises(StateError):
            self.engine.resolve_unknown(packet["attempt_id"], confirm_stopped=False)
        reconciled = self.engine.resolve_unknown(packet["attempt_id"], confirm_stopped=True)
        self.assertEqual(reconciled["status"], "failed")
        next_packet = self.engine.claim(run_id, "host")
        self.assertEqual(next_packet["attempt"], 2)
        self.assertNotEqual(next_packet["attempt_id"], packet["attempt_id"])

    def test_reserved_attempt_can_resume_without_a_duplicate(self):
        agent = job("edit")
        run_id = self.engine.start(self.definition(process([agent])))["id"]
        first = self.engine.claim(run_id, "host")
        self.assertEqual(self.engine.resume(run_id)["status"], "in_progress")
        second = self.engine.claim(run_id, "host")
        self.assertEqual(second["attempt"], 2)
        self.assertNotEqual(first["attempt_id"], second["attempt_id"])

    def test_two_processes_cannot_claim_the_same_job(self):
        agent = job("edit")
        run_id = self.engine.start(self.definition(process([agent])))["id"]
        peer = Engine(self.home, self.workspace)
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def claim(engine):
            barrier.wait()
            try:
                results.append(engine.claim(run_id, "host"))
            except Exception as exc:  # noqa: BLE001 - every thread error must reach the assertions.
                errors.append(exc)

        threads = [threading.Thread(target=claim, args=(instance,)) for instance in (self.engine, peer)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(self.engine.status(run_id)["jobs"]["reserved"], 1)

    def test_failed_command_preserves_attempt_history(self):
        failing = job(
            "fail",
            "command",
            command={"argv": [__import__("sys").executable, "-c", "raise SystemExit(7)"]},
            max_attempts=2,
        )
        run_id = self.engine.start(self.definition(process([failing])), grants=["shell"])["id"]
        result = self.engine.drive(run_id, "local")
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["run"]["outcome"], "JOB_FAILED")
        attempts = self.engine.store.events(run_id, limit=100)
        self.assertEqual(len([e for e in attempts if e["kind"] == "delivery.completed"]), 2)

    def test_external_input_is_bound_to_immutable_bytes(self):
        source = self.workspace / "source.txt"
        source.write_text("original", encoding="utf-8")
        agent = job("review", consumes=["source"])
        run_id = self.engine.start(self.definition(process(
            [agent], inputs=[{"name": "source", "type": "text", "path": "source.txt"}]
        )))["id"]
        source.write_text("changed later", encoding="utf-8")
        packet = self.engine.claim(run_id, "host")
        self.assertEqual(packet["objective"], "exercise durable execution")
        self.assertEqual(Path(packet["inputs"][0]["content_path"]).read_bytes(), b"original")

    def test_status_and_events_are_bounded(self):
        agent = job("edit")
        run_id = self.engine.start(self.definition(process([agent])))["id"]
        status = self.engine.status(run_id)
        self.assertNotIn("definition_yaml", status)
        self.assertNotIn("grants", status)
        with self.assertRaises(StateError):
            self.engine.finish(run_id)
        self.assertEqual(self.engine.events(run_id, limit=1).__len__(), 1)


if __name__ == "__main__":
    unittest.main()
