"""The edit-impact packet: what a worker needs to know before it edits a symbol.

The oracle is the packet's own contract: digests and cards of the target, resolved
one-hop neighbours with their cards, the references static analysis could not
resolve, recent changes and hash-verified source, bounded and read-only.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import mcp_service
import semantic_store
import snapshot
from snapshot_store import artifact_digest, open_snapshot

HELPER = "def helper(value):\n    return value + 1\n\ndef extra():\n    return 10\n"
CALLER = (
    "from .b import helper, extra\n\n"
    "def run(x):\n    return helper(x) + extra()\n\n"
    "def dyn(obj, name):\n    return getattr(obj, name)()\n"
)


def write_project(root: Path) -> None:
    (root / "pkg").mkdir(parents=True, exist_ok=True)
    (root / "pkg/__init__.py").write_text("", encoding="utf-8")
    (root / "pkg/b.py").write_text(HELPER, encoding="utf-8")
    (root / "pkg/a.py").write_text(CALLER, encoding="utf-8")


class EngineImpactTests(unittest.TestCase):
    def setUp(self):
        from test_codebase_map_edge_view import Definition, StubEngine
        import resolve_edges
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name, body in {
            "leaf.py": "class Worker:\n    def run(self):\n        return 1\n",
            "bridge.py": "def middle(obj):\n    return obj.run()\n",
            "entry.py": "def top(obj):\n    return obj.middle()\n",
        }.items():
            (self.root / name).write_text(body, encoding="utf-8")
        self.manifest = self.root / ".codebase-map/manifest.sqlite"
        self.edges = self.manifest.with_name("engine-edges.sqlite")
        snapshot.write_snapshot(self.root, self.manifest)
        self.before = artifact_digest(self.manifest)
        self.engine = StubEngine({
            ("bridge.py", 2): Definition(self.root / "leaf.py", "run", line=2, column=8),
            ("entry.py", 2): Definition(self.root / "bridge.py", "middle", line=1, column=4),
        })
        resolve_edges.resolve_edges(self.manifest, engine=self.engine, limit=None, stride=1, out=self.edges)

    def test_engine_edges_reach_graph_and_both_impact_hops_without_inference(self):
        from store_graph import query_graph
        asked = list(self.engine.asked)
        with open_snapshot(self.manifest) as store:
            graph = query_graph(store, ["leaf.py"], hops=2, engine_store=self.edges)
            packet = semantic_store.build_edit_impact(
                store, ["leaf.py::Worker.run"], hops=2, include_source=False,
                engine_store=self.edges)
        self.assertEqual({call["file"] for call in graph["calls"]}, {"bridge.py", "entry.py"})
        self.assertTrue(all(call["resolver"] == "stub@1.0" for call in graph["calls"]))
        target = packet["targets"][0]
        caller = target["callers"]["listed"][0]
        self.assertEqual(caller["symbol_id"], "bridge.py::middle")
        self.assertEqual(caller["edges"][0]["sites"][0]["resolver"], "stub@1.0")
        self.assertEqual(caller["edges"][0]["sites"][0]["start_line"], 2)
        self.assertIn("entry.py::top", {r["symbol_id"] for r in target["second_hop"]["listed"]})
        self.assertEqual(self.engine.asked, asked)
        self.assertEqual(artifact_digest(self.manifest), self.before)

    def test_file_consumer_counts_engine_calls_and_card_freshness_stays_lexical(self):
        from store_consumers import consumer_reader, file_analysis
        cards = self.manifest.with_name("cards.sqlite")
        with open_snapshot(self.manifest) as store:
            semantic_store.upsert_meta_cards(store, cards, [
                {"symbol_id": "bridge.py::middle", "purpose": "Delegate to the worker"}])
            with consumer_reader(store, engine_store=self.edges) as db:
                semantic, _, _ = file_analysis(store, db, "leaf.py")
            packet = semantic_store.build_edit_impact(
                store, ["bridge.py::middle"], cards_path=cards, include_source=False,
                engine_store=self.edges)
        self.assertEqual(semantic["counts"]["incoming_calls"], 1)
        self.assertEqual(semantic["incoming_calls"][0]["resolver"], "stub@1.0")
        self.assertEqual(semantic["edge_view"]["coverage"]["status"], "complete")
        self.assertEqual(packet["targets"][0]["card"]["freshness"], "fresh")
        self.assertEqual(packet["targets"][0]["card"]["freshness_basis"], "lexical")

    def test_rejected_engine_store_keeps_lexical_fallback_explicit(self):
        from store_graph import query_graph
        self.edges.write_bytes(b"broken")
        with open_snapshot(self.manifest) as store:
            packet = query_graph(store, ["leaf.py"], engine_store=self.edges)
        self.assertEqual(packet["calls"], [])
        self.assertEqual(packet["edge_view"]["coverage"]["status"], "rejected_store")
        self.assertTrue(packet["edge_view"]["gaps"])


class EditImpactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-edit-impact-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        write_project(self.root)
        self.out = self.root / ".codebase-map" / "manifest.sqlite"
        self.cards = self.root / ".codebase-map" / "cards.sqlite"
        snapshot.write_snapshot(self.root, self.out)

    def impact(self, targets, **options):
        with open_snapshot(self.out) as store:
            return semantic_store.build_edit_impact(store, targets, cards_path=self.cards, **options)

    def write_cards(self, cards):
        with open_snapshot(self.out) as store:
            return semantic_store.upsert_meta_cards(store, self.cards, cards)

    def refresh(self):
        with open_snapshot(self.out) as previous:
            snapshot.write_snapshot(self.root, self.out, previous=previous)

    def test_target_reports_digests_card_callers_and_verified_source(self):
        self.write_cards([{
            "file": "pkg/b.py", "symbol": "helper", "purpose": "adds one",
            "preconditions": ["value is numeric"],
        }])

        packet = self.impact(["pkg/b.py::helper"])

        self.assertEqual(packet["schema"], semantic_store.EDIT_IMPACT_SCHEMA)
        target = packet["targets"][0]
        self.assertEqual(target["symbol_id"], "pkg/b.py::helper")
        for digest in ("body_hash", "interface_hash", "effects_hash"):
            self.assertTrue(target[digest])
        self.assertEqual(target["card"]["purpose"], "adds one")
        self.assertEqual(target["card"]["freshness"], "fresh")
        self.assertEqual([c["symbol_id"] for c in target["callers"]["listed"]], ["pkg/a.py::run"])
        self.assertEqual(target["callers"]["listed"][0]["references"], 1)
        self.assertEqual(target["callees"]["total"], 0)
        emitted = "".join(block["source"] for item in packet["source"]["files"]
                          if item["path"] == "pkg/b.py" for block in item["blocks"])
        self.assertIn("return value + 1", emitted)
        self.assertNotIn("return 10", emitted, "an unselected callable body must not be read")

    def test_target_and_neighbours_carry_their_signature_records(self):
        packet = self.impact(["pkg/b.py::helper"], include_source=False)

        target = packet["targets"][0]
        self.assertEqual(target["signatures"][0]["params"], [{"name": "value"}])
        self.assertIn("parameters", target["signatures"][0]["fields"])
        caller = target["callers"]["listed"][0]
        self.assertEqual(caller["symbol_id"], "pkg/a.py::run")
        self.assertEqual(caller["signatures"][0]["params"], [{"name": "x"}])
        with open_snapshot(self.out) as store:
            meta = semantic_store.query_meta_code(store, symbol="pkg/b.py::helper", include_history=False)
        self.assertEqual(meta["symbols"][0]["signatures"], target["signatures"])

    def test_l1_edges_carry_exact_reference_sites(self):
        target = self.impact(["pkg/b.py::helper"], include_source=False)["targets"][0]

        caller_edge = target["callers"]["listed"][0]["edges"][0]
        self.assertEqual(caller_edge["kind"], "call")
        self.assertEqual(caller_edge["count"], 1)
        self.assertEqual(caller_edge["sites"][0]["file"], "pkg/a.py")
        self.assertEqual(caller_edge["sites"][0]["start_line"], 4)
        run = self.impact(["pkg/a.py::run"], include_source=False)["targets"][0]
        callee = next(item for item in run["callees"]["listed"] if item["symbol_id"] == "pkg/b.py::helper")
        self.assertEqual(callee["edges"][0]["sites"][0]["start_line"], 4)

    def test_second_hop_is_signature_only_and_budget_omissions_are_reported(self):
        (self.root / "pkg/c.py").write_text(
            "from .a import run\n\ndef top(x):\n    return run(x)\n", encoding="utf-8")
        self.refresh()

        target = self.impact(["pkg/b.py::helper"], hops=2, include_source=False)["targets"][0]
        second = {item["symbol_id"]: item for item in target["second_hop"]["listed"]}
        self.assertIn("pkg/c.py::top", second)
        self.assertEqual(second["pkg/c.py::top"]["via"][0]["symbol_id"], "pkg/a.py::run")
        self.assertNotIn("card", second["pkg/c.py::top"])
        self.assertTrue(second["pkg/c.py::top"]["signatures"])

        capped = self.impact(["pkg/b.py::helper"], hops=2, include_source=False,
                             budget_chars=1000)["targets"][0]
        self.assertEqual(capped["second_hop"]["listed"], [])
        self.assertGreater(capped["second_hop"]["omitted_by_budget"], 0)

    def test_neighbor_source_is_verified_and_l4_names_related_tests(self):
        (self.root / "pkg/test_b.py").write_text(
            "from .b import helper\n\ndef test_helper():\n    assert helper(1) == 2\n", encoding="utf-8")
        self.refresh()

        packet = self.impact(["pkg/b.py::helper"], include_source=False,
                             include_neighbor_source=True)
        target = packet["targets"][0]
        emitted = "".join(block["source"] for item in packet["neighbor_source"]["files"]
                          for block in item["blocks"])
        self.assertIn("return helper(x) + extra()", emitted)
        self.assertNotIn("getattr", emitted)
        self.assertEqual([item["symbol_id"] for item in target["l4"]["related_tests"]],
                         ["pkg/test_b.py::test_helper"])
        self.assertIn("run-related-tests", {item["kind"] for item in target["l4"]["obligations"]})
        self.assertEqual(target["l4"]["do_not_touch"]["status"], "unavailable")

    def test_lazy_python_slice_excludes_unrelated_statements(self):
        (self.root / "pkg/b.py").write_text(
            "def helper(value):\n"
            "    unused = 999\n"
            "    step = value + 1\n"
            "    if step > 0:\n"
            "        result = step * 2\n"
            "    else:\n"
            "        result = 0\n"
            "    return result\n\n"
            "def extra():\n    return 10\n", encoding="utf-8")
        self.refresh()

        target = self.impact(["pkg/b.py::helper"], include_source=False,
                             include_slices=True)["targets"][0]

        self.assertEqual(target["slice"]["status"], "available")
        starts = {item["start"] for item in target["slice"]["statements"]}
        self.assertNotIn(2, starts, "the unused assignment is outside the backward slice")
        self.assertTrue({3, 4, 5, 7, 8} <= starts)

    def test_callees_are_the_resolved_one_hop_calls_of_the_target(self):
        packet = self.impact(["pkg/a.py::run"], include_source=False)

        callees = {c["symbol_id"] for c in packet["targets"][0]["callees"]["listed"]}
        self.assertEqual(callees, {"pkg/b.py::helper", "pkg/b.py::extra"})
        self.assertNotIn("source", packet)

    def test_unresolved_dynamic_calls_are_listed_as_blind_spots(self):
        packet = self.impact(["pkg/a.py::dyn"], include_source=False)

        blind = packet["targets"][0]["blind_spots"]
        self.assertIn("dynamic-callee", {item["reason"] for item in blind["listed"]})
        self.assertGreaterEqual(blind["unbound_names"], 1, "a builtin is counted, not listed")
        self.assertNotIn("unbound-name", {item["reason"] for item in blind["listed"]})

    def test_recent_changes_follow_an_edit_after_a_refresh(self):
        (self.root / "pkg/b.py").write_text(
            "def helper(value):\n    step = 2\n    return value + step\n\ndef extra():\n    return 10\n",
            encoding="utf-8")
        self.refresh()

        target = self.impact(["pkg/b.py::helper"], include_source=False)["targets"][0]

        self.assertEqual([c["change_kind"] for c in target["recent_changes"]], ["body_only"])

    def test_a_file_path_expands_to_its_symbols_and_the_cap_is_reported(self):
        packet = self.impact(["pkg/b.py"], include_source=False)
        self.assertEqual({t["symbol_id"] for t in packet["targets"]},
                         {"pkg/b.py::helper", "pkg/b.py::extra"})

        with mock.patch.object(semantic_store, "MAX_IMPACT_TARGETS", 1):
            capped = self.impact(["pkg/b.py"], include_source=False)
        self.assertEqual(len(capped["targets"]), 1)
        self.assertEqual(capped["truncated_targets"], 1)

    def test_neighbours_are_capped_and_their_total_is_reported(self):
        (self.root / "pkg/c.py").write_text(
            "from .b import helper\n\ndef one():\n    return helper(1)\n\ndef two():\n    return helper(2)\n",
            encoding="utf-8")
        self.refresh()

        callers = self.impact(["pkg/b.py::helper"], neighbors=1, include_source=False)["targets"][0]["callers"]

        self.assertEqual(callers["total"], 3)
        self.assertEqual(len(callers["listed"]), 1)

    def test_unknown_targets_are_named_not_dropped(self):
        packet = self.impact(["pkg/b.py::helper", "pkg/missing.py::nope"], include_source=False)

        self.assertEqual(packet["unknown_targets"], ["pkg/missing.py::nope"])
        self.assertEqual(len(packet["targets"]), 1)

    def test_stale_source_is_reported_while_the_metadata_stays_usable(self):
        (self.root / "pkg/b.py").write_text("def helper(value):\n    return value + 99\n", encoding="utf-8")

        packet = self.impact(["pkg/b.py::helper"])

        self.assertIn("refresh", packet["source"]["error"])
        self.assertEqual(packet["targets"][0]["symbol_id"], "pkg/b.py::helper")

    def test_the_packet_is_bounded_and_does_not_touch_the_snapshot(self):
        before = artifact_digest(self.out)

        packet = self.impact(["pkg/a.py::run", "pkg/b.py::helper"])

        self.assertLess(packet["bytes"], 8_000)
        self.assertEqual(artifact_digest(self.out), before)

    def test_invalid_requests_and_json_snapshots_are_refused(self):
        for targets in ([], "pkg/b.py", [""], [3]):
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                self.impact(targets)
        for options in ({"neighbors": 0}, {"history": 1000}, {"neighbors": True},
                        {"hops": 0}, {"hops": 3}, {"budget_chars": 999},
                        {"include_neighbor_source": "yes"}, {"include_slices": 1}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.impact(["pkg/b.py::helper"], **options)
        legacy = self.root / ".codebase-map" / "manifest.json"
        snapshot.write_snapshot(self.root, legacy, format="json")
        with open_snapshot(legacy) as store, self.assertRaisesRegex(ValueError, "SQLite"):
            semantic_store.build_edit_impact(store, ["pkg/b.py::helper"])


class EditImpactEntryPointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-edit-impact-entry-")
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        write_project(self.project / "src")
        self.service = mcp_service.MapService(self.project)

    def test_command_line_prints_the_packet_and_fails_on_a_bad_request(self):
        out = self.project / "manifest.sqlite"
        snapshot.write_snapshot(self.project / "src", out)

        done = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "edit-impact", str(out),
             "--target", "pkg/b.py::helper", "--no-source"],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["targets"][0]["symbol_id"], "pkg/b.py::helper")

        failed = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "edit-impact", str(out),
             "--target", "pkg/b.py::helper", "--neighbors", "0"],
            capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertIn("neighbors", failed.stderr)

    def test_service_and_cli_accept_progressive_options(self):
        self.service.create_run("src", "progressive", depth="lite")

        packet = self.service.edit_impact(
            "progressive", ["pkg/b.py::helper"], hops=2,
            include_neighbor_source=True, include_slices=True)

        self.assertIn("second_hop", packet["targets"][0])
        self.assertIn("neighbor_source", packet)
        self.assertEqual(packet["targets"][0]["slice"]["status"], "available")
        out = self.project / "manifest.sqlite"
        snapshot.write_snapshot(self.project / "src", out)
        done = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "edit-impact", str(out),
             "--target", "pkg/b.py::helper", "--hops", "2", "--neighbor-source",
             "--slices", "--budget-chars", "120000"],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["schema"], "daodan/edit-impact/v2")

    def test_service_serves_the_packet_and_meta_query_for_a_run(self):
        self.service.create_run("src", "impact", depth="lite")

        symbols = {item["symbol_id"] for item in self.service.meta_query("impact")["symbols"]}
        self.assertIn("pkg/b.py::helper", symbols)
        packet = self.service.edit_impact("impact", ["pkg/b.py::helper"])

        self.assertEqual(packet["run_id"], "impact")
        self.assertEqual(packet["targets"][0]["callers"]["listed"][0]["symbol_id"], "pkg/a.py::run")
        with self.assertRaises(ValueError):
            self.service.edit_impact("impact", ["pkg/b.py::helper"], include_source="yes")
        with self.assertRaises(ValueError):
            self.service.meta_query("impact", paths=["../outside.py"])


if __name__ == "__main__":
    unittest.main()
