"""Decision-map frontier, ownership and execution-ticket gates."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.errors import StateError
from work_controller.store import Store


class DecisionMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.store = Store(root / "home")
        self.store.map_open("migration", "Migrate the service safely")

    def test_decision_closes_only_with_user_answer_and_unblocks_next(self):
        self.store.ticket_add("migration", "window", "decision", "Choose the cutover window")
        self.store.ticket_add("migration", "execute", "execution", "Run the migration", blocked_by=["window"])
        self.assertEqual(self.store.map_next("migration")["id"], "window")
        self.store.ticket_claim("migration", "window", "session-a")
        with self.assertRaises(StateError):
            self.store.ticket_claim("migration", "window", "session-b")
        with self.assertRaises(StateError):
            self.store.ticket_close("migration", "window", "session-a", source="evidence", resolution="guessed")
        closed = self.store.ticket_close(
            "migration", "window", "session-a", source="user", resolution="Sunday 02:00"
        )
        self.assertEqual(closed["status"], "closed")
        self.assertEqual(self.store.map_next("migration")["id"], "execute")

    def test_ticket_block_cycles_are_rejected_atomically(self):
        self.store.ticket_add("migration", "first", "research", "First", blocked_by=["second"])
        with self.assertRaises(StateError):
            self.store.ticket_add("migration", "second", "research", "Second", blocked_by=["first"])
        with self.assertRaises(StateError):
            self.store.ticket("migration", "second")

    def test_execution_ticket_waits_for_real_run_completion(self):
        workspace = Path(self.temp.name) / "workspace"
        workspace.mkdir()
        engine = Engine(Path(self.temp.name) / "home", workspace)
        definition = workspace / "process.yaml"
        definition.write_text(dump_definition({
            "schema": "work-controller/process/v1", "kind": "graph", "id": "ticket-run",
            "objective": "complete the ticket",
            "jobs": [{
                "id": "edit", "type": "agent", "summary": "edit",
                "produces": [{"name": "out", "type": "text", "path": "out.txt"}],
                "write_set": ["out.txt"],
            }],
        }), encoding="utf-8")
        run_id = engine.start(definition)["id"]
        self.store.ticket_add("migration", "execute", "execution", "Execute", run_id=run_id)
        self.store.ticket_claim("migration", "execute", "session-a")
        with self.assertRaises(StateError):
            self.store.ticket_close("migration", "execute", "session-a", source="run")
        attempt_id = engine.claim(run_id, "host")["attempt_id"]
        engine.start_attempt(attempt_id, "host")
        (workspace / "out.txt").write_text("done", encoding="utf-8")
        engine.complete(attempt_id, "host", "done", "pass")
        engine.drive(run_id, "host")
        closed = self.store.ticket_close("migration", "execute", "session-a", source="run")
        self.assertEqual(closed["resolution"], f"run:{run_id}")
        self.assertEqual(self.store.map_status("migration")["status"], "complete")
        self.assertGreaterEqual(len(self.store.map_events("migration", limit=100)), 4)


if __name__ == "__main__":
    unittest.main()
