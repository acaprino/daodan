"""Integration tests for work-record admission of real process-store evidence."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import work_controller_test_support  # noqa: F401: load the bundled runtime.

import process_binding
from run_state import no_links, report_path
from work_controller.definition import dump_definition
from work_controller.engine import Engine
from work_controller.errors import StateError


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_TEMP_ROOT = REPO_ROOT / ".daodan/runs/20261026-office-binding-repair/tmp"


class ProcessBindingTests(unittest.TestCase):
    def setUp(self):
        TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        environment = patch.dict(os.environ, {"TMP": str(TEST_TEMP_ROOT), "TEMP": str(TEST_TEMP_ROOT)})
        environment.start()
        self.addCleanup(environment.stop)
        temporary = tempfile.TemporaryDirectory(prefix="process-binding-", dir=TEST_TEMP_ROOT)
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        self.project = self.temporary / "workspace"
        self.project.mkdir()
        self.root = self.project / ".daodan"
        self.engine = Engine(self.root / "processes", self.project)
        definition = {
            "schema": "work-controller/process/v1",
            "kind": "graph",
            "id": "office-process",
            "objective": "Bind pending document and review deliveries",
            "jobs": [
                {"id": "check", "type": "command", "summary": "Check the workspace",
                 "command": {"argv": [sys.executable, "-c", "pass"]}},
                {"id": "draft", "type": "agent", "summary": "Draft the document",
                 "produces": [{"name": "document", "type": "text", "path": "document.md"}],
                 "write_set": ["document.md"]},
                {"id": "review", "type": "agent", "summary": "Review the document",
                 "produces": [{"name": "review", "type": "text", "path": "review.md"}],
                 "write_set": ["review.md"]},
            ],
        }
        path = self.project / "process.yaml"
        path.write_text(dump_definition(definition), encoding="utf-8")
        self.started = self.engine.start(path, grants=["shell"], run_id="office-process")
        self.record = {
            "run_id": "office-work",
            "status": "in_progress",
            "deliveries": {"document-worker": {"status": "pending"},
                           "review-worker": {"status": "pending"}},
            "process": {
                "schema": "daodan/process-binding/v1",
                "run_id": "office-process",
                "definition_digest": self.started["definition_digest"],
                "deliveries": {
                    "document-worker": {"job": "draft", "artifact": "document"},
                    "review-worker": {"job": "review", "artifact": "review"},
                },
            },
        }

    def test_every_agent_can_be_bound_while_outputs_are_pending(self):
        result = process_binding.validate(
            self.record, self.project, self.root, no_links, report_path,
        )

        self.assertIsNone(result)
        self.assertEqual(self.engine.store.run("office-process")["revision"], 0)
        self.assertFalse((self.project / "document.md").exists())
        self.assertFalse((self.project / "review.md").exists())

    def test_an_unmapped_agent_is_rejected(self):
        del self.record["process"]["deliveries"]["review-worker"]

        with self.assertRaisesRegex(ValueError, "Every process agent job requires a mapped work delivery"):
            process_binding.validate(
                self.record, self.project, self.root, no_links, report_path,
            )

    def test_the_admitted_definition_digest_must_match(self):
        self.record["process"]["definition_digest"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "Process definition differs from the bound immutable revision"):
            process_binding.validate(
                self.record, self.project, self.root, no_links, report_path,
            )

    def test_validation_does_not_create_a_missing_process_store(self):
        missing_root = self.temporary / "missing-record-home"

        with self.assertRaisesRegex(StateError, "no existing process database"):
            process_binding.validate(
                self.record, self.project, missing_root, no_links, report_path,
            )

        self.assertFalse(missing_root.exists())


if __name__ == "__main__":
    unittest.main()
