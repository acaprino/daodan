"""Shared read models stay bounded and preserve the engine's evidence."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.errors import DefinitionError
from work_controller.views import Views


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.engine = Engine(root / "home", self.workspace)
        self.views = Views(self.engine)

    def start(self, jobs, *, grants=None):
        path = self.workspace / "process.yaml"
        path.write_text(dump_definition({
            "schema": "work-controller/process/v1", "kind": "graph", "id": "views",
            "objective": "exercise views", "jobs": jobs,
        }), encoding="utf-8")
        return self.engine.start(path, grants=grants or [])["id"]

    def test_overview_and_run_detail_do_not_embed_definition_or_input_payloads(self):
        run_id = self.start([{
            "id": "edit", "type": "agent", "summary": "bounded agent summary",
            "produces": [{"name": "out", "type": "text", "path": "out.txt"}],
            "write_set": ["out.txt"],
        }])
        overview = self.views.overview()
        self.assertEqual(overview["runs"][0]["id"], run_id)
        self.assertNotIn("definition_yaml", overview["runs"][0])
        attempt_id = self.engine.claim(run_id, "host")["attempt_id"]
        self.engine.start_attempt(attempt_id, "host")
        (self.workspace / "out.txt").write_text("done", encoding="utf-8")
        self.engine.complete(attempt_id, "host", "done", "pass")
        detail = self.views.run(run_id)
        self.assertEqual(detail["jobs"][0]["summary"], "bounded agent summary")
        self.assertNotIn("payload_json", detail["jobs"][0])
        self.assertNotIn("inputs", detail["attempts"][0])
        self.assertEqual(detail["artifacts"][0]["name"], "out")
        self.assertEqual(detail["artifacts"][0]["size"], 4)

    def test_event_pages_and_validation_are_shared(self):
        run_id = self.start([{"id": "edit", "type": "agent", "summary": "edit"}])
        self.engine.claim(run_id, "host")
        first = self.views.events(run_id, after=0, limit=1)
        self.assertEqual(len(first["events"]), 1)
        second = self.views.events(run_id, after=first["events"][-1]["seq"], limit=1)
        self.assertNotEqual(first["events"][0]["seq"], second["events"][0]["seq"])
        with self.assertRaises(DefinitionError):
            self.views.events(run_id, after=-1)
        with self.assertRaises(DefinitionError):
            self.views.overview(limit=True)

    def test_map_projection_contains_ticket_dependencies(self):
        self.engine.store.map_open("map", "destination")
        self.engine.store.ticket_add("map", "decide", "decision", "choose")
        self.engine.store.ticket_add("map", "execute", "execution", "execute", blocked_by=["decide"])
        detail = self.views.map("map")
        self.assertEqual(detail["status"]["next"]["id"], "decide")
        self.assertEqual(detail["tickets"][1]["blocked_by"], ["decide"])

    def test_attempt_log_is_bounded_and_stream_checked(self):
        run_id = self.start([{
            "id": "write", "type": "command", "summary": "write output",
            "command": {"argv": [sys.executable, "-c", "print('abcdef')"]},
        }], grants=["shell"])
        self.engine.drive(run_id, "local")
        attempt_id = next(
            event["attempt_id"] for event in self.engine.events(run_id, limit=100)
            if event["kind"] == "attempt.started"
        )
        log = self.views.attempt_log(attempt_id, "stdout", max_bytes=4)
        self.assertTrue(log["available"])
        self.assertTrue(log["truncated"])
        self.assertEqual(len(log["text"]), 4)
        self.assertTrue(log["text"].rstrip("\r\n").endswith("ef"))
        with self.assertRaises(DefinitionError):
            self.views.attempt_log(attempt_id, "other")


if __name__ == "__main__":
    unittest.main()
