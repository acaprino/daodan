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
        for options in ({"neighbors": 0}, {"history": 1000}, {"neighbors": True}):
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
