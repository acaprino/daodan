"""Tests for the shared verified lexical + Jedi edge view (P1)."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolve_edges
import snapshot
from snapshot_store import open_snapshot


class Definition:
    def __init__(self, module_path, name, *, kind="function", line=2, column=8):
        self.module_path = module_path
        self.name = name
        self.type = kind
        self.line = line
        self.column = column


class StubEngine:
    name = "stub"

    def __init__(self, answers=None, ready=True, reason=""):
        self.answers = dict(answers or {})
        self.ready = ready
        self.reason = reason
        self.asked = []

    def probe(self):
        return (True, "") if self.ready else (False, self.reason)

    def identity(self):
        return "stub@1.0"

    def definitions(self, path, line, column):
        self.asked.append((Path(path).name, line, column))
        answer = self.answers.get((Path(path).name, line))
        if isinstance(answer, list):
            return answer
        return [] if answer is None else [answer]


class EdgeViewTests(unittest.TestCase):
    SOURCES = {
        "app/contracts.py": (
            "from typing import Protocol\n"
            "from abc import ABC, abstractmethod\n\n"
            "class RunnerProtocol(Protocol):\n"
            "    def run(self) -> int:\n"
            "        ...\n\n"
            "class AbstractRunner(ABC):\n"
            "    @abstractmethod\n"
            "    def execute(self) -> int:\n"
            "        raise NotImplementedError\n"
        ),
        "app/tool.py": (
            "class ConcreteRunner:\n"
            "    def run(self) -> int:\n"
            "        return 1\n\n"
            "def helper_fn() -> int:\n"
            "    return 2\n"
        ),
        "app/use.py": (
            "from app.tool import helper_fn\n\n"
            "def call_all(proto_runner, abs_runner, concrete_runner, mystery):\n"
            "    a = helper_fn()\n"
            "    b = proto_runner.run()\n"
            "    c = abs_runner.execute()\n"
            "    d = concrete_runner.run()\n"
            "    e = mystery.unknown()\n"
            "    return a + b + c + d + e\n"
        ),
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        self.root.mkdir()
        for rel, text in self.SOURCES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.write_snapshot(self.root, self.manifest)
        self.edges = self.root.parent / "engine-edges.sqlite"

    def test_load_edge_view_merges_lexical_and_confirmed_engine_edges_and_distinguishes_target_kinds(self):
        import edge_view

        manifest_digest_before = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        engine = StubEngine(answers={
            ("use.py", 5): Definition(self.root / "app/contracts.py", "run", line=5, column=8),
            ("use.py", 6): Definition(self.root / "app/contracts.py", "execute", line=10, column=8),
            ("use.py", 7): Definition(self.root / "app/tool.py", "run", line=2, column=8),
            ("use.py", 8): [
                Definition(self.root / "app/tool.py", "run", line=2, column=8),
                Definition(self.root / "app/tool.py", "helper_fn", line=5, column=4),
            ],
        })
        report = resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None, stride=1, out=self.edges)
        self.assertTrue(report["available"])
        self.assertEqual((report["confirmed_edges"], report["candidates"]), (3, 1))

        with open_snapshot(self.manifest) as store:
            view = edge_view.load_edge_view(store, engine_store=self.edges)

        self.assertEqual(view["schema"], edge_view.EDGE_VIEW_SCHEMA)
        self.assertEqual(view["version"], edge_view.EDGE_VIEW_VERSION)
        self.assertEqual(view["coverage"]["status"], "complete")
        self.assertEqual(view["profile"]["engine"], "stub@1.0")
        self.assertEqual(view["conflicts"], [])

        by_line = {ref["span"][0]: ref for ref in view["references"] if ref["file"] == "app/use.py"}
        # Line 4: lexical call to helper_fn()
        self.assertEqual(by_line[4]["resolution"], "resolved")
        self.assertEqual(by_line[4]["resolver"], "builtin-lexical")
        self.assertEqual(by_line[4]["target_kind"], "concrete")

        # Line 5: protocol method target
        self.assertEqual(by_line[5]["resolution"], "resolved")
        self.assertEqual(by_line[5]["resolver"], "stub@1.0")
        self.assertEqual(by_line[5]["target_kind"], "protocol")

        # Line 6: abstract / interface method target
        self.assertEqual(by_line[6]["resolution"], "resolved")
        self.assertEqual(by_line[6]["resolver"], "stub@1.0")
        self.assertEqual(by_line[6]["target_kind"], "interface")

        # Line 7: concrete class method target
        self.assertEqual(by_line[7]["resolution"], "resolved")
        self.assertEqual(by_line[7]["resolver"], "stub@1.0")
        self.assertEqual(by_line[7]["target_kind"], "concrete")

        # Line 8: ambiguous engine candidate stays unresolved in effective references
        self.assertEqual(by_line[8]["resolution"], "unresolved")
        self.assertIsNone(by_line[8]["target_id"])
        self.assertEqual(by_line[8]["engine_candidate"]["verdict"], "ambiguous-target")

        self.assertEqual(hashlib.sha256(self.manifest.read_bytes()).hexdigest(), manifest_digest_before)

    def test_load_edge_view_distinguishes_missing_empty_sampled_and_rejected_stores(self):
        import edge_view

        with open_snapshot(self.manifest) as store:
            missing_view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(missing_view["coverage"]["status"], "missing_store")

        resolve_edges.resolve_edges(self.manifest, engine=StubEngine(), limit=1, stride=2, out=self.edges)
        with open_snapshot(self.manifest) as store:
            sampled_view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(sampled_view["coverage"]["status"], "sampled")
        self.assertTrue(sampled_view["coverage"]["sampled"])

        resolve_edges.resolve_edges(self.manifest, engine=StubEngine(), limit=None, stride=1, out=self.edges)
        with open_snapshot(self.manifest) as store:
            empty_view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(empty_view["coverage"]["status"], "completed_empty")
        self.assertFalse(empty_view["coverage"]["sampled"])

        self.edges.write_bytes(b"corrupted")
        with open_snapshot(self.manifest) as store:
            rejected_view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(rejected_view["coverage"]["status"], "rejected_store")
        self.assertTrue(rejected_view["gaps"])

    def test_cli_compact_mode_and_report_out_write_full_report_to_file_and_summary_to_stdout(self):
        report_file = self.root.parent / "full-engine-report.json"
        engine = StubEngine(answers={
            ("use.py", 7): Definition(self.root / "app/tool.py", "run", line=2, column=8),
        })
        stdout = io.StringIO()
        with mock.patch.object(resolve_edges, "JediEngine", return_value=engine):
            with contextlib.redirect_stdout(stdout):
                code = resolve_edges.main([
                    str(self.manifest),
                    "--out", str(self.edges),
                    "--report-out", str(report_file),
                    "--compact",
                ])
        self.assertEqual(code, 0)
        compact = json.loads(stdout.getvalue())
        full = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertTrue(compact["available"])
        self.assertEqual(compact["confirmed_edges"], 1)
        self.assertEqual(compact["report_out"], report_file.as_posix())
        self.assertNotIn("file_environments", compact)
        self.assertIn("verdicts", full)
        self.assertEqual(full["confirmed_edges"], 1)


if __name__ == "__main__":
    unittest.main()
