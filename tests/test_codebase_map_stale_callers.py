"""Stale-callers separates edit obligations from validation obligations.

The oracle is the fingerprint delta between two snapshots: a signature change
makes direct callers RED, a body-only change makes downstream callers GREEN
for editing, and an unchanged intermediate contract stops the edit cascade.
"""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import mcp_service
import semantic_store
import snapshot
from snapshot_store import open_snapshot

BASE_FILES = {
    "pkg/__init__.py": "",
    "pkg/b.py": "def helper(value):\n    return value + 1\n\ndef extra():\n    return 10\n",
    "pkg/a.py": "from .b import helper, extra\n\ndef run(x):\n    return helper(x) + extra()\n",
    "pkg/c.py": "from .a import run\n\ndef top(x):\n    return run(x)\n",
    "pkg/test_chain.py": "from .c import top\n\ndef test_top():\n    assert top(1)\n",
}


def write_files(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def ids(packet, key):
    return {item["symbol_id"] for item in packet[key]["listed"]}


class StaleCallersTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-stale-callers-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        write_files(self.root, BASE_FILES)
        self.base = self.root / "base.sqlite"
        snapshot.write_snapshot(self.root, self.base)

    def compare(self, changed_text: str):
        (self.root / "pkg/b.py").write_text(changed_text, encoding="utf-8")
        candidate = self.root / "candidate.sqlite"
        snapshot.write_snapshot(self.root, candidate)
        with open_snapshot(self.base) as base, open_snapshot(candidate) as current:
            return semantic_store.build_stale_callers(base, current)

    def test_a_body_only_change_validates_callers_without_editing_them(self):
        result = self.compare("def helper(value):\n    step = 2\n    return value + step\n\ndef extra():\n    return 10\n")

        self.assertEqual(result["schema"], semantic_store.STALE_CALLERS_SCHEMA)
        self.assertEqual({item["symbol_id"]: item["change_kind"] for item in result["changed"]},
                         {"pkg/b.py::helper": "body_only"})
        self.assertEqual(ids(result, "edit_impact"), set())
        self.assertEqual(ids(result, "validation_impact"),
                         {"pkg/a.py::run", "pkg/c.py::top", "pkg/test_chain.py::test_top"})
        self.assertEqual(ids(result, "do_not_touch"), ids(result, "validation_impact"))
        self.assertTrue(all(item["status"] == "GREEN" for item in result["validation_impact"]["listed"]))

    def test_an_interface_change_stops_at_an_unchanged_intermediate_contract(self):
        result = self.compare("def helper(value, offset=1):\n    return value + offset\n\ndef extra():\n    return 10\n")

        self.assertEqual(ids(result, "edit_impact"), {"pkg/a.py::run"})
        self.assertEqual(result["edit_impact"]["listed"][0]["status"], "RED")
        self.assertEqual(ids(result, "validation_impact"), set())
        self.assertEqual(ids(result, "do_not_touch"), {"pkg/c.py::top"})
        order = [component["symbols"] for component in result["components"]]
        self.assertLess(order.index(["pkg/b.py::helper"]), order.index(["pkg/a.py::run"]))
        self.assertLess(order.index(["pkg/a.py::run"]), order.index(["pkg/c.py::top"]))

    def test_an_effects_change_is_an_edit_impact(self):
        result = self.compare("def helper(value):\n    return value + extra()\n\ndef extra():\n    return 10\n")

        self.assertEqual({item["change_kind"] for item in result["changed"]}, {"effects_changed"})
        self.assertEqual(ids(result, "edit_impact"), {"pkg/a.py::run"})

    def test_removed_target_retains_its_base_callers(self):
        result = self.compare("def extra():\n    return 10\n")
        self.assertIn("pkg/a.py::run", ids(result, "edit_impact"))
        removed = result["lexical_callee_drift"]["items"]
        self.assertTrue(any(item["kind"] == "removed_target" and
                            item["caller"] == "pkg/a.py::run" for item in removed))

    def test_rebinding_an_import_reports_rewired_call_with_unchanged_caller_body(self):
        (self.root / "pkg/a.py").write_text(
            "from .b import extra as helper, extra\n\ndef run(x):\n    return helper(x) + extra()\n",
            encoding="utf-8")
        candidate = self.root / "candidate.sqlite"
        snapshot.write_snapshot(self.root, candidate)
        with open_snapshot(self.base) as base, open_snapshot(candidate) as current:
            result = semantic_store.build_stale_callers(base, current)
        drift = result["lexical_callee_drift"]["items"]
        self.assertTrue(any(item["kind"] == "rewired_call" and
                            item["before_target"] == "pkg/b.py::helper" and
                            item["after_target"] == "pkg/b.py::extra" for item in drift))

    def test_engine_availability_versions_and_sampling_do_not_assert_rewiring(self):
        from test_codebase_map_edge_view import Definition, StubEngine
        import resolve_edges
        (self.root / "pkg/a.py").write_text("def run(obj):\n    return obj.helper()\n", encoding="utf-8")
        snapshot.write_snapshot(self.root, self.base)
        base_edges = self.root / "base-edges.sqlite"
        candidate_edges = self.root / "candidate-edges.sqlite"
        candidate = self.root / "candidate.sqlite"
        engine = StubEngine({("a.py", 2): Definition(self.root / "pkg/b.py", "helper", line=1, column=4)})
        resolve_edges.resolve_edges(self.base, engine=engine, limit=None, stride=1, out=base_edges)
        snapshot.write_snapshot(self.root, candidate)
        resolve_edges.resolve_edges(candidate, engine=engine, limit=None, stride=1, out=candidate_edges)
        def compare(before, after):
            with open_snapshot(self.base) as base, open_snapshot(candidate) as current:
                return semantic_store.build_stale_callers(
                    base, current, base_engine_store=before, candidate_engine_store=after)
        missing = self.root / "absent.sqlite"
        for before, after in ((base_edges, missing), (missing, candidate_edges)):
            result = compare(before, after)
            self.assertEqual(result["engine_callee_drift"]["status"], "incomparable")
            self.assertEqual(result["engine_callee_drift"]["items"], [])
            self.assertIn("lexical_callee_drift", result)
        engine.identity = lambda: "stub@2.0"
        resolve_edges.resolve_edges(candidate, engine=engine, limit=None, stride=1, out=candidate_edges)
        self.assertEqual(compare(base_edges, candidate_edges)["engine_callee_drift"]["status"], "incomparable")
        engine.identity = lambda: "stub@1.0"
        resolve_edges.resolve_edges(candidate, engine=engine, limit=0, stride=2, out=candidate_edges)
        self.assertEqual(compare(base_edges, candidate_edges)["engine_callee_drift"]["status"], "incomparable")
        engine.answers[("a.py", 2)] = Definition(self.root / "pkg/b.py", "extra", line=4, column=4)
        resolve_edges.resolve_edges(candidate, engine=engine, limit=None, stride=1, out=candidate_edges)
        drift = compare(base_edges, candidate_edges)["engine_callee_drift"]
        self.assertEqual(drift["status"], "complete")
        self.assertEqual(drift["items"][0]["kind"], "rewired_call")
        self.assertEqual(drift["items"][0]["after_target"], "pkg/b.py::extra")

    def test_protocol_to_implementation_is_dispatch_evidence_not_confirmed_rewiring(self):
        from test_codebase_map_edge_view import Definition, StubEngine
        import resolve_edges
        write_files(self.root, {
            "pkg/b.py": "from typing import Protocol\nclass P(Protocol):\n    def run(self): ...\nclass Impl:\n    def run(self): return 1\n",
            "pkg/a.py": "def run(obj):\n    return obj.run()\n",
        })
        snapshot.write_snapshot(self.root, self.base)
        before_edges = self.root / "before.sqlite"
        after_edges = self.root / "after.sqlite"
        candidate = self.root / "candidate.sqlite"
        engine = StubEngine({("a.py", 2): Definition(self.root / "pkg/b.py", "run", line=3, column=8)})
        resolve_edges.resolve_edges(self.base, engine=engine, limit=None, stride=1, out=before_edges)
        snapshot.write_snapshot(self.root, candidate)
        engine.answers[("a.py", 2)] = Definition(self.root / "pkg/b.py", "run", line=5, column=8)
        resolve_edges.resolve_edges(candidate, engine=engine, limit=None, stride=1, out=after_edges)
        with open_snapshot(self.base) as base, open_snapshot(candidate) as current:
            result = semantic_store.build_stale_callers(base, current,
                base_engine_store=before_edges, candidate_engine_store=after_edges)
        drift = result["engine_callee_drift"]["items"]
        self.assertEqual(len(drift), 1)
        self.assertEqual((drift[0]["kind"], drift[0]["certainty"]), ("dispatch_set_changed", "potential"))

    def test_a_digest_version_mismatch_is_incompatible_not_an_edit(self):
        legacy = self.root / "legacy.sqlite"
        legacy.write_bytes(self.base.read_bytes())
        with closing(sqlite3.connect(legacy)) as database, database:
            database.execute("UPDATE meta_symbols SET interface_hash='0123456789abcdef' WHERE id='pkg/b.py::helper'")
        candidate = self.root / "candidate.sqlite"
        snapshot.write_snapshot(self.root, candidate)

        with open_snapshot(legacy) as base, open_snapshot(candidate) as current:
            result = semantic_store.build_stale_callers(base, current)

        self.assertEqual([item["symbol_id"] for item in result["incompatible"]], ["pkg/b.py::helper"])
        self.assertEqual(result["changed"], [])

    def test_union_of_acyclic_revisions_terminates(self):
        source = self.root / "acyclic.py"
        source.write_text("def a(x):\n    return b(x)\n\ndef b(x):\n    return x\n")
        snapshot.write_snapshot(self.root, self.base)
        source.write_text("def a(x, y=0):\n    return x\n\ndef b(x, y=0):\n    return a(x)\n")
        candidate = self.root / "candidate.sqlite"
        snapshot.write_snapshot(self.root, candidate)
        program = (
            "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
            "from snapshot_store import open_snapshot; import semantic_store; "
            "base=open_snapshot(Path(sys.argv[2])); candidate=open_snapshot(Path(sys.argv[3])); "
            "packet=semantic_store.build_stale_callers(base,candidate); "
            "assert any(c['cyclic'] for c in packet['components'])"
        )
        result = subprocess.run([sys.executable, "-B", "-c", program, str(SCRIPTS),
                                 str(self.base), str(candidate)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_one_sided_engine_witness_survives_removed_target(self):
        from test_codebase_map_edge_view import Definition, StubEngine
        import resolve_edges
        (self.root / "pkg/a.py").write_text("def run(obj):\n    return obj.helper()\n")
        snapshot.write_snapshot(self.root, self.base)
        edges = self.root / "base-edges.sqlite"
        engine = StubEngine({("a.py", 2): Definition(self.root / "pkg/b.py", "helper", line=1, column=4)})
        resolve_edges.resolve_edges(self.base, engine=engine, limit=None, stride=1, out=edges)
        (self.root / "pkg/b.py").write_text("def extra():\n    return 10\n")
        candidate = self.root / "candidate.sqlite"
        snapshot.write_snapshot(self.root, candidate)
        with open_snapshot(self.base) as base, open_snapshot(candidate) as current:
            result = semantic_store.build_stale_callers(
                base, current, base_engine_store=edges,
                candidate_engine_store=self.root / "missing.sqlite")
        self.assertEqual(result["engine_callee_drift"]["status"], "incomparable")
        self.assertEqual(result["engine_callee_drift"]["items"], [])
        caller = next(item for item in result["edit_impact"]["listed"] if item["symbol_id"] == "pkg/a.py::run")
        sites = caller["reasons"][0]["edges"][0]["sites"]
        self.assertEqual(sites[0]["snapshot"], "base")
        self.assertEqual(sites[0]["resolver"], "stub@1.0")

    def test_cycles_are_one_atomic_component(self):
        root = self.root / "cycle"
        write_files(root, {
            "pkg/__init__.py": "",
            "pkg/a.py": "from .b import y\n\ndef x():\n    return y()\n",
            "pkg/b.py": "from .a import x\n\ndef y():\n    return x()\n",
        })
        base = root / "base.sqlite"
        snapshot.write_snapshot(root, base)
        (root / "pkg/b.py").write_text(
            "from .a import x\n\ndef y(scale=1):\n    return x() * scale\n", encoding="utf-8")
        candidate = root / "candidate.sqlite"
        snapshot.write_snapshot(root, candidate)

        with open_snapshot(base) as before, open_snapshot(candidate) as current:
            result = semantic_store.build_stale_callers(before, current)

        cyclic = [item for item in result["components"] if item["cyclic"]]
        self.assertEqual(len(cyclic), 1)
        self.assertEqual(set(cyclic[0]["symbols"]), {"pkg/a.py::x", "pkg/b.py::y"})
        self.assertTrue(cyclic[0]["atomic"])
        self.assertEqual(ids(result, "edit_impact"), {"pkg/a.py::x"})

    def test_cli_and_mcp_service_expose_the_projection(self):
        project = self.root / "project"
        write_files(project / "src", BASE_FILES)
        service = mcp_service.MapService(project)
        service.create_run("src", "base-run", depth="lite")
        write_files(project / "src", {
            "pkg/b.py": "def helper(value, offset=1):\n    return value + offset\n\ndef extra():\n    return 10\n",
        })
        service.create_run("src", "candidate-run", depth="lite")

        result = service.stale_callers("candidate-run", "base-run")

        self.assertEqual(result["base_run_id"], "base-run")
        self.assertEqual(ids(result, "edit_impact"), {"pkg/a.py::run"})
        candidate = project / "candidate.sqlite"
        base = project / "base.sqlite"
        snapshot.write_snapshot(project / "src", candidate)
        write_files(project / "src", BASE_FILES)
        snapshot.write_snapshot(project / "src", base)
        done = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "stale-callers", str(candidate),
             "--base", str(base)],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["schema"], semantic_store.STALE_CALLERS_SCHEMA)


if __name__ == "__main__":
    unittest.main()
