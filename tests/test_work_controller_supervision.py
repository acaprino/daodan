"""The supervisor advises from bounded evidence but owns no transitions."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.supervision import recommend


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.workspace = root / "workspace"
        self.workspace.mkdir()
        self.engine = Engine(root / "home", self.workspace)

    def test_running_observation_is_bounded_and_not_authoritative(self):
        definition = self.workspace / "process.yaml"
        definition.write_text(dump_definition({
            "schema": "work-controller/process/v1",
            "kind": "graph",
            "id": "supervision",
            "objective": "observe a job",
            "jobs": [{
                "id": "edit", "type": "agent", "summary": "edit",
                "produces": [{"name": "out", "type": "text", "path": "out.txt"}],
                "write_set": ["out.txt"],
            }],
        }), encoding="utf-8")
        run_id = self.engine.start(definition)["id"]
        attempt_id = self.engine.claim(run_id, "host")["attempt_id"]
        self.engine.start_attempt(attempt_id, "host")
        result = self.engine.supervise(attempt_id)
        self.assertEqual(result["action"], "CONTINUE")
        self.assertFalse(result["authoritative"])
        self.assertNotIn("command", result["observation"])
        self.assertLessEqual(len(result["observation"]["events"]), 8)

    def test_policy_retries_available_failure_and_escalates_unknown(self):
        base = {
            "attempt_status": "failed", "job_status": "failed", "expired": False,
            "attempts_used": 1, "max_attempts": 2,
        }
        self.assertEqual(recommend(base), "RETRY_WORKER")
        self.assertEqual(recommend({**base, "attempts_used": 2}), "ESCALATE")
        self.assertEqual(recommend({**base, "attempt_status": "unknown"}), "ESCALATE")


if __name__ == "__main__":
    unittest.main()
