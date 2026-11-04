"""The generated map is a truthful, bounded-by-area view of canonical evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import semantic_map
import semantic_store
import snapshot
from snapshot_store import artifact_digest, logical_digest, open_snapshot


class SemanticMapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="semantic-map-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "pkg").mkdir()
        self.write("pkg/__init__.py", "")
        self.write("pkg/a.py", "from .b import helper\n\ndef run(x):\n    return helper(x)\n")
        self.write("pkg/b.py", "def helper(value):\n    return value + 1\n\ndef unused():\n    return 0\n")
        self.manifest = self.root / ".codebase-map/manifest.sqlite"
        self.cards = self.manifest.with_name("cards.sqlite")
        self.output = self.manifest.with_name("semantic-map.md")
        self.refresh()

    def write(self, relative, text):
        (self.root / relative).write_text(text, encoding="utf-8", newline="\n")

    def refresh(self):
        if self.manifest.exists():
            with open_snapshot(self.manifest) as previous:
                snapshot.write_snapshot(self.root, self.manifest, previous=previous)
        else:
            snapshot.write_snapshot(self.root, self.manifest)

    def seed(self, *cards):
        with open_snapshot(self.manifest) as store:
            result = semantic_store.upsert_meta_cards(store, self.cards, list(cards))
        self.assertFalse(result.get("rejected"), result)

    def render(self, **options):
        return semantic_map.render_map(self.manifest, cards_path=self.cards, out=self.output, **options)

    def pair(self):
        return self.output.read_bytes(), self.output.with_suffix(".json").read_bytes()

    def test_fresh_card_has_canonical_identity_provenance_contracts_and_graph(self):
        self.seed({"symbol_id": "pkg/b.py::helper", "purpose": "Adds one to a value",
                   "preconditions": ["Input is numeric"], "postconditions": ["Result is input plus one"],
                   "invariants": ["Input is unchanged"], "side_effects": [], "failure_modes": [],
                   "confidence": "high"})
        before = {p: artifact_digest(p) for p in [self.manifest, self.cards, self.root / "pkg/b.py"]}
        report = self.render()
        entity = next(row for row in report["entities"] if row["entity_id"] == "pkg/b.py::helper")
        self.assertEqual(report["schema"], "daodan/semantic-map/v1")
        self.assertEqual(entity["freshness"], "fresh")
        self.assertEqual(entity["freshness_basis"], "lexical")
        self.assertEqual(entity["anchor"]["file"], "pkg/b.py")
        self.assertEqual(entity["anchor"]["start_line"], 1)
        self.assertTrue(entity["card_provenance"]["updated_at"])
        for key in ("body_hash", "interface_hash", "effects_hash"):
            self.assertTrue(entity[key])
        with open_snapshot(self.manifest) as store:
            self.assertEqual(report["snapshot"]["logical_digest"], logical_digest(store))
        text = self.output.read_text(encoding="utf-8")
        for phrase in ("Adds one to a value", "Input is numeric", "Result is input plus one", "Input is unchanged"):
            self.assertIn(phrase, text)
        calls = report["graph"]["calls"]
        self.assertTrue(any(row["caller_entity_id"] == "pkg/a.py::run"
                            and row["target_entity_id"] == "pkg/b.py::helper" for row in calls))
        self.assertEqual(report["artifact_digest"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(json.loads(self.output.with_suffix(".json").read_text()), report)
        self.assertEqual(report["coverage"]["runtime_files"], 0)
        self.assertEqual(report["llm_calls"], 0)
        self.assertIsNone(report["card_llm_tokens"])
        self.assertEqual(before, {p: artifact_digest(p) for p in before})

    def test_absent_and_partial_cards_declare_gaps_without_inventing_purpose(self):
        missing = self.render()
        self.assertFalse(self.cards.exists())
        self.assertTrue(all(row["freshness"] == "unread" for row in missing["entities"]))
        self.seed({"symbol_id": "pkg/b.py::helper", "notes": "Only the signature was inspected"})
        partial = self.render()
        row = next(row for row in partial["entities"] if row["entity_id"] == "pkg/b.py::helper")
        self.assertIn("purpose", row["missing_fields"])
        self.assertIn("side_effects", row["missing_fields"])
        self.assertEqual(partial["coverage"]["cards"]["unread"], partial["coverage"]["symbols"] - 1)

    def test_changed_and_removed_symbols_never_publish_old_card_text_as_current(self):
        self.seed({"symbol_id": "pkg/b.py::helper", "purpose": "OLD HELPER DESCRIPTION"},
                  {"symbol_id": "pkg/b.py::unused", "purpose": "REMOVED SYMBOL DESCRIPTION"})
        self.write("pkg/b.py", "def helper(value):\n    step = 2\n    return value + step\n")
        self.refresh()
        report = self.render()
        helper = next(row for row in report["entities"] if row["entity_id"] == "pkg/b.py::helper")
        self.assertEqual(helper["freshness"], "stale_body")
        self.assertEqual(helper["freshness_basis"], "lexical")
        self.assertNotEqual(helper["body_hash"], helper["card_provenance"]["body_hash"])
        orphan = next(row for row in report["orphans"] if row["entity_id"] == "pkg/b.py::unused")
        self.assertEqual(orphan["freshness"], "orphan")
        self.assertFalse(orphan.get("anchor"))
        self.assertEqual(report["coverage"]["cards"]["orphan"], 1)
        text = self.output.read_text()
        self.assertNotIn("OLD HELPER DESCRIPTION", text)
        self.assertNotIn("REMOVED SYMBOL DESCRIPTION", text)

    def test_area_counts_are_scoped_and_deleted_file_cards_remain_discoverable(self):
        self.write("other.py", "def other():\n    return 1\n")
        self.refresh()
        self.seed({"symbol_id": "other.py::other", "purpose": "OUTSIDE AREA"},
                  {"symbol_id": "pkg/b.py::helper", "purpose": "Local helper"})
        report = self.render(paths=["pkg"])
        self.assertEqual(report["coverage"]["selected_files"], 3)
        self.assertTrue(all(row["entity_id"].startswith("pkg/") for row in report["entities"]))
        self.assertNotIn("OUTSIDE AREA", self.output.read_text())
        self.assertEqual(report["coverage"]["symbols"], len(report["entities"]))
        (self.root / "other.py").unlink()
        self.refresh()
        removed = self.render(paths=["other.py"])
        self.assertEqual(removed["coverage"]["selected_files"], 0)
        self.assertEqual(removed["coverage"]["cards"]["orphan"], 1)
        self.assertEqual(removed["entities"], [])

    def test_deterministic_bytes_and_inert_card_markup(self):
        self.seed({"symbol_id": "pkg/b.py::helper",
                   "purpose": "<script>evil()</script> [click](javascript:evil)\n# forged heading"})
        self.render(paths=["pkg/a.py", "pkg/b.py"])
        first = self.pair()
        self.render(paths=["pkg/b.py", "pkg/a.py", "pkg/b.py"])
        self.assertEqual(first, self.pair())
        text = first[0].decode()
        self.assertNotIn("<script>", text)
        self.assertNotIn("[click](javascript:evil)", text)
        self.assertNotIn("\n# forged heading", text)

    def test_more_than_one_hundred_symbols_and_empty_files_are_not_truncated(self):
        self.write("many.py", "\n".join(f"def item_{i}():\n    return {i}\n" for i in range(130)))
        self.write("empty.py", "")
        self.refresh()
        report = self.render(paths=["many.py", "empty.py"])
        self.assertEqual(report["coverage"]["selected_files"], 2)
        self.assertEqual(report["coverage"]["symbols"], 130)
        self.assertEqual(len(report["entities"]), 130)
        self.assertIn("item_129", self.output.read_text())
        self.assertIn("empty.py", self.output.read_text())

    def test_source_and_inventory_drift_reject_without_replacing_previous_map(self):
        self.render()
        before = self.pair()
        self.write("pkg/a.py", "def changed():\n    return 0\n")
        with self.assertRaises(ValueError):
            self.render()
        self.assertEqual(before, self.pair())
        self.refresh()
        self.render()
        before = self.pair()
        self.write("new.py", "def new():\n    return 0\n")
        with self.assertRaises(ValueError):
            self.render()
        self.assertEqual(before, self.pair())

    def test_invalid_areas_and_output_destinations_preserve_user_files(self):
        self.render()
        before = self.pair()
        for paths in [["../pkg"], [str(self.root)], ["missing"], []]:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                self.render(paths=paths)
        report = self.output.with_name("07-final-report.md")
        report.write_text("Keep the phase report")
        for path in [report, self.root / "semantic-map.md", self.manifest]:
            with self.subTest(output=path), self.assertRaises(ValueError):
                semantic_map.render_map(self.manifest, cards_path=self.cards, out=path)
        self.assertEqual(report.read_text(), "Keep the phase report")
        self.assertEqual(before, self.pair())

    def test_unverifiable_growth_before_or_during_render_preserves_previous_map(self):
        self.seed({"symbol_id": "pkg/b.py::helper", "purpose": "Original logic"})
        self.render()
        before = self.pair()
        source = self.root / "pkg/b.py"
        original = source.read_bytes()
        oversized = "def changed():\n    return 99\n#" + "x" * 1024
        for during_render in (False, True):
            with self.subTest(during_render=during_render):
                source.write_bytes(original)
                render = semantic_map._render

                def change_after_read(report):
                    result = render(report)
                    self.write("pkg/b.py", oversized)
                    return result

                if not during_render:
                    self.write("pkg/b.py", oversized)
                with mock.patch.object(snapshot, "MAX_FILE_BYTES", 512), \
                        mock.patch.object(semantic_map, "_render", side_effect=
                                          change_after_read if during_render else render):
                    with self.assertRaises(ValueError):
                        self.render()
                self.assertEqual(before, self.pair())

    def test_snapshot_excluded_oversized_file_does_not_create_false_inventory_drift(self):
        self.write("too_large.py", "#" + "x" * 1024)
        with mock.patch.object(snapshot, "MAX_FILE_BYTES", 512):
            self.refresh()
            report = self.render()
        self.assertNotIn("too_large.py", report["query"]["selected_files"])
        self.assertEqual(report["coverage"]["selected_files"], 3)

    def test_publication_failure_restores_the_previous_complete_pair(self):
        self.seed({"symbol_id": "pkg/b.py::helper", "purpose": "First card"})
        self.render()
        before = self.pair()
        self.seed({"symbol_id": "pkg/b.py::helper", "purpose": "Second card"})
        replace = os.replace
        failed = False

        def fail_once(source, target):
            nonlocal failed
            if Path(target) == self.output.with_suffix(".json") and not failed:
                failed = True
                raise OSError("injected publication failure")
            return replace(source, target)

        with mock.patch.object(semantic_map.os, "replace", side_effect=fail_once):
            with self.assertRaises(OSError):
                self.render()
        self.assertTrue(failed)
        self.assertEqual(before, self.pair())
        self.render()
        self.assertIn("Second card", self.output.read_text())

    def test_output_aliases_and_foreign_generated_names_are_preserved(self):
        self.render()
        before = self.pair()
        for name in ("cards_path", "engine_store"):
            with self.subTest(input=name), self.assertRaises(ValueError):
                semantic_map.render_map(self.manifest, out=self.output,
                                        **{name: self.output})
        self.assertEqual(before, self.pair())
        alias = self.output.with_name("semantic-map-alias.md")
        os.link(self.output, alias)
        try:
            with self.assertRaises(ValueError):
                semantic_map.render_map(self.manifest, out=alias)
            self.assertEqual(alias.read_bytes(), before[0])
            self.assertEqual(before, self.pair())
        finally:
            alias.unlink()
        foreign = self.output.with_name("semantic-map-notes.md")
        foreign.write_text("User notes must survive", encoding="utf-8")
        with self.assertRaises(ValueError):
            semantic_map.render_map(self.manifest, out=foreign)
        self.assertEqual(foreign.read_text(), "User notes must survive")

    def test_explicit_card_store_does_not_move_output_root(self):
        custom = self.root / ".private-cards/cards.sqlite"
        with open_snapshot(self.manifest) as store:
            semantic_store.upsert_meta_cards(store, custom, [
                {"symbol_id": "pkg/b.py::helper", "purpose": "Shared card"}])
        report = semantic_map.render_map(self.manifest, cards_path=custom)
        self.assertEqual(Path(report["output"]), self.output)
        self.assertFalse(custom.with_name("semantic-map.md").exists())
        self.assertIn("Shared card", self.output.read_text())

    def test_cli_keeps_markdown_on_disk_and_reports_only_summary(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "semantic_map.py"), str(self.manifest),
                                 "--path", "pkg"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(Path(summary["output"]), self.output)
        self.assertNotIn("entities", summary)
        self.assertLess(len(result.stdout), 2500)
        self.assertTrue(self.output.is_file())

    def test_verified_engine_edges_keep_provenance_without_running_inference(self):
        from test_codebase_map_edge_view import Definition, StubEngine
        import resolve_edges
        self.write("leaf.py", "class Worker:\n    def work(self):\n        return 1\n")
        self.write("caller.py", "def call(obj):\n    return obj.work()\n")
        self.refresh()
        self.seed({"symbol_id": "caller.py::call", "purpose": "Delegate work"})
        edges = self.manifest.with_name("engine-edges.sqlite")
        engine = StubEngine({("caller.py", 2): Definition(self.root / "leaf.py", "work", line=2, column=8)})
        resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None, stride=1, out=edges)
        asked = list(engine.asked)
        report = self.render(engine_store=edges)
        calls = [row for row in report["graph"]["calls"] if row["caller_entity_id"] == "caller.py::call"]
        self.assertEqual(calls[0]["target_entity_id"], "leaf.py::Worker.work")
        self.assertEqual(calls[0]["resolver"], "stub@1.0")
        self.assertEqual(engine.asked, asked)
        row = next(row for row in report["entities"] if row["entity_id"] == "caller.py::call")
        self.assertEqual(row["freshness"], "fresh")
        self.assertEqual(row["freshness_basis"], "lexical")


if __name__ == "__main__":
    unittest.main()
