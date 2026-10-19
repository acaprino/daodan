"""Cards live outside every snapshot and are judged against the snapshot being read.

A run's snapshot is immutable evidence, so a model's reading of a symbol is kept in
one project-level file together with the digests it was written against. The oracle
is behavioural: a card is fresh exactly when the symbol still has those digests,
wherever the snapshot came from.
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
import card_store
import mcp_service
import semantic_store
import snapshot
from snapshot_store import artifact_digest, open_snapshot

HELPER = "def helper(value):\n    return value + 1\n\ndef extra():\n    return 10\n"
CALLER = "from .b import helper, extra\n\ndef run(x):\n    return helper(x) + extra()\n"


def write_project(root: Path, helper: str = HELPER) -> None:
    (root / "pkg").mkdir(parents=True, exist_ok=True)
    (root / "pkg/__init__.py").write_text("", encoding="utf-8")
    (root / "pkg/b.py").write_text(helper, encoding="utf-8")
    (root / "pkg/a.py").write_text(CALLER, encoding="utf-8")


class CardStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-card-store-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def test_a_valid_card_keeps_only_its_declared_fields(self):
        payload = card_store.validate_card({
            "file": "a.py", "symbol": "f", "purpose": "adds", "invariants": ["pure"],
        })

        self.assertEqual(payload, {"purpose": "adds", "invariants": ["pure"]})

    def test_invalid_cards_are_refused_instead_of_trimmed(self):
        cases = {
            "unknown field": {"purpose": "x", "side_effect": ["writes"]},
            "empty card": {"file": "a.py", "symbol": "f"},
            "text field not text": {"purpose": ["x"]},
            "list field not a list": {"invariants": "pure"},
            "list item not text": {"invariants": [3]},
            "too many items": {"invariants": ["x"] * (card_store.MAX_FIELD_ITEMS + 1)},
            "text too long": {"purpose": "x" * (card_store.MAX_TEXT + 1)},
            "not an object": ["purpose"],
        }
        for label, card in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                card_store.validate_card(card)

    def test_a_run_snapshot_uses_the_analysis_root_and_any_other_keeps_its_own_directory(self):
        run = self.root / ".codebase-map" / "runs" / "example"
        (run / "snapshot").mkdir(parents=True)
        (run / "state.json").write_text("{}", encoding="utf-8")

        self.assertEqual(card_store.default_cards_path(run / "snapshot/manifest.sqlite"),
                         self.root / ".codebase-map" / "cards.sqlite")
        self.assertEqual(card_store.default_cards_path(self.root / "loose/manifest.sqlite"),
                         self.root / "loose" / "cards.sqlite")
        # a directory named `snapshot` without a run beside it is not a run
        (self.root / "other/snapshot").mkdir(parents=True)
        self.assertEqual(card_store.default_cards_path(self.root / "other/snapshot/m.sqlite"),
                         self.root / "other/snapshot" / "cards.sqlite")

    def test_a_missing_store_holds_no_cards(self):
        missing = self.root / "none.sqlite"

        self.assertEqual(card_store.digests(missing, "root"), [])
        self.assertEqual(card_store.read_cards(missing, "root", ["a::f"]), {})
        self.assertFalse(missing.exists(), "reading must not create the store")

    def test_a_file_that_is_not_a_card_store_is_refused_and_left_alone(self):
        project = self.root / "p"
        write_project(project)
        manifest = self.root / "manifest.sqlite"
        snapshot.write_snapshot(project, manifest)
        garbage = self.root / "garbage.sqlite"
        garbage.write_bytes(b"this is not a database at all" * 20)
        before = (artifact_digest(manifest), artifact_digest(garbage))

        for path in (manifest, garbage):
            with self.subTest(path.name), self.assertRaisesRegex(ValueError, "card store"):
                card_store.digests(path, "root")
            with self.subTest(path.name), self.assertRaises(ValueError):
                card_store.write_cards(path, "root", [self.row()])

        self.assertEqual((artifact_digest(manifest), artifact_digest(garbage)), before)

    def row(self, **changes):
        base = {"symbol_id": "a.py::f", "file": "a.py", "symbol": "f", "kind": "function",
                "body_hash": "b", "interface_hash": "i", "effects_hash": "e",
                "callee_digest": "", "payload": {"purpose": "x"}}
        return {**base, **changes}

    def test_a_failed_batch_leaves_the_earlier_cards_unchanged(self):
        path = self.root / "cards.sqlite"
        card_store.write_cards(path, "root", [self.row(payload={"purpose": "first"})])

        with self.assertRaises(KeyError):
            card_store.write_cards(path, "root", [
                self.row(payload={"purpose": "second"}),
                {"symbol_id": "a.py::g"},  # incomplete row
            ])

        self.assertEqual(card_store.read_cards(path, "root", ["a.py::f"])["a.py::f"]["purpose"], "first")

    def test_roots_do_not_see_each_others_cards(self):
        path = self.root / "cards.sqlite"
        card_store.write_cards(path, "/project/one", [self.row(payload={"purpose": "one"})])
        card_store.write_cards(path, "/project/two", [self.row(payload={"purpose": "two"})])

        self.assertEqual(card_store.read_cards(path, "/project/one", ["a.py::f"])["a.py::f"]["purpose"], "one")
        self.assertEqual(card_store.read_cards(path, "/project/two", ["a.py::f"])["a.py::f"]["purpose"], "two")
        self.assertEqual(card_store.read_cards(path, "/project/three", ["a.py::f"]), {})


class CardLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-card-lifecycle-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        write_project(self.root)
        self.out = self.root / ".codebase-map" / "manifest.sqlite"
        self.cards = self.root / ".codebase-map" / "cards.sqlite"
        snapshot.write_snapshot(self.root, self.out)

    def refresh(self):
        with open_snapshot(self.out) as previous:
            snapshot.write_snapshot(self.root, self.out, previous=previous)

    def write(self, cards):
        with open_snapshot(self.out) as store:
            return semantic_store.upsert_meta_cards(store, self.cards, cards)

    def query(self, **options):
        with open_snapshot(self.out) as store:
            return semantic_store.query_meta_code(store, cards_path=self.cards, include_history=False, **options)

    def states(self):
        return {item["symbol_id"]: item["freshness"] for item in self.query()["symbols"]}

    def edit_helper(self, text):
        (self.root / "pkg/b.py").write_text(text, encoding="utf-8")
        self.refresh()

    def seed(self):
        self.write([
            {"file": "pkg/b.py", "symbol": "helper", "purpose": "adds one"},
            {"file": "pkg/a.py", "symbol": "run", "purpose": "combines helper and extra"},
        ])

    def test_symbols_without_a_card_are_uncovered_and_counted(self):
        self.seed()

        result = self.query()
        counts = result["summary"]["cards"]

        self.assertEqual(self.states()["pkg/b.py::extra"], "uncovered")
        self.assertEqual(counts["fresh"], 2)
        self.assertEqual(counts["uncovered"], result["summary"]["total_symbols"] - 2)
        self.assertEqual([s["symbol_id"] for s in self.query(freshness="uncovered")["symbols"]
                          if s["symbol_id"] in ("pkg/b.py::helper", "pkg/a.py::run")], [])

    def test_a_card_stays_fresh_across_a_rebuilt_snapshot_of_unchanged_code(self):
        self.seed()
        self.refresh()
        self.refresh()

        self.assertEqual(self.states()["pkg/b.py::helper"], "fresh")
        self.assertEqual(self.query(symbol="pkg/b.py::helper")["symbols"][0]["card"]["purpose"], "adds one")

    def test_a_body_edit_stales_only_the_edited_symbols_card(self):
        self.seed()
        self.edit_helper("def helper(value):\n    step = 2\n    return value + step\n\ndef extra():\n    return 10\n")

        states = self.states()

        self.assertEqual(states["pkg/b.py::helper"], "stale_body")
        self.assertEqual(states["pkg/a.py::run"], "fresh")

    def test_a_callee_that_only_moves_down_the_file_leaves_its_callers_digests_alone(self):
        def digests():
            with open_snapshot(self.out) as store:
                return dict(store.connection.execute(
                    "SELECT id, body_hash || interface_hash || effects_hash FROM meta_symbols"))

        before = digests()
        # a longer helper body shifts `extra` down; `run` calls both and did not change
        self.edit_helper("def helper(value):\n    step = 2\n    return value + step\n\ndef extra():\n    return 10\n")
        after = digests()

        self.assertNotEqual(before["pkg/b.py::helper"], after["pkg/b.py::helper"])
        self.assertEqual(before["pkg/b.py::extra"], after["pkg/b.py::extra"], "same text, only moved")
        self.assertEqual(before["pkg/a.py::run"], after["pkg/a.py::run"])
        with open_snapshot(self.out) as store:
            changed = {d["symbol_id"] for c in semantic_store.query_meta_code(store)["changesets"] for d in c["deltas"]}
        self.assertNotIn("pkg/a.py::run", changed)

    def test_an_interface_edit_stales_the_symbol_and_its_callers_card(self):
        self.seed()
        self.edit_helper("def helper(value, offset=1):\n    return value + offset\n\ndef extra():\n    return 10\n")

        states = self.states()

        self.assertEqual(states["pkg/b.py::helper"], "stale_interface")
        self.assertEqual(states["pkg/a.py::run"], "stale_callee")

    def test_a_card_is_fresh_again_when_the_code_returns_to_what_it_described(self):
        self.seed()
        self.edit_helper("def helper(value, offset=1):\n    return value + offset\n\ndef extra():\n    return 10\n")
        self.assertEqual(self.states()["pkg/a.py::run"], "stale_callee")

        self.edit_helper(HELPER)

        self.assertEqual(self.states()["pkg/b.py::helper"], "fresh")
        self.assertEqual(self.states()["pkg/a.py::run"], "fresh")

    def test_rewriting_a_stale_card_binds_it_to_the_current_code(self):
        self.seed()
        self.edit_helper("def helper(value):\n    return value + 2\n\ndef extra():\n    return 10\n")
        self.assertEqual(self.states()["pkg/b.py::helper"], "stale_body")

        self.write([{"file": "pkg/b.py", "symbol": "helper", "purpose": "adds two"}])

        self.assertEqual(self.states()["pkg/b.py::helper"], "fresh")
        self.assertEqual(self.query(symbol="pkg/b.py::helper")["symbols"][0]["card"]["purpose"], "adds two")

    def test_a_removed_symbol_leaves_an_orphan_that_is_listed_only_when_asked(self):
        self.seed()
        self.edit_helper("def extra():\n    return 10\n")

        self.assertNotIn("pkg/b.py::helper", self.states())
        orphans = self.query(freshness="orphan")

        self.assertEqual([o["symbol_id"] for o in orphans["orphans"]], ["pkg/b.py::helper"])
        self.assertEqual(orphans["symbols"], [])
        self.assertEqual(self.query()["orphans"], [])

    def test_cards_follow_the_root_across_a_different_snapshot_file(self):
        self.seed()
        other = self.root / ".codebase-map" / "runs" / "other" / "snapshot" / "manifest.sqlite"
        other.parent.mkdir(parents=True)
        (other.parent.parent / "state.json").write_text("{}", encoding="utf-8")
        snapshot.write_snapshot(self.root, other)

        with open_snapshot(other) as store:
            states = {s["symbol_id"]: s["freshness"]
                      for s in semantic_store.query_meta_code(store, cards_path=self.cards)["symbols"]}

        self.assertEqual(states["pkg/b.py::helper"], "fresh")

    def test_a_card_written_for_one_project_is_invisible_in_another(self):
        self.seed()
        second = self.root / "second"
        write_project(second)
        manifest = second / "manifest.sqlite"
        snapshot.write_snapshot(second, manifest)

        with open_snapshot(manifest) as store:
            result = semantic_store.query_meta_code(store, cards_path=self.cards)

        self.assertEqual(result["summary"]["cards"].get("fresh", 0), 0)
        self.assertTrue(all(s["freshness"] == "uncovered" for s in result["symbols"]))

    def test_unknown_symbols_are_reported_and_a_bad_card_writes_nothing(self):
        result = self.write([{"file": "pkg/b.py", "symbol": "helper", "purpose": "adds one"},
                             {"symbol_id": "pkg/missing.py::nope", "purpose": "x"}])
        self.assertEqual((result["upserted"], result["missing_symbols"]), (1, ["pkg/missing.py::nope"]))

        before = card_store.digests(self.cards, self.query()["summary"] and self.root.as_posix())
        for bad in ([{"file": "pkg/a.py", "symbol": "run", "purpose": "ok"}, {"file": "pkg/a.py", "symbol": "run"}],
                    [{"file": "pkg/a.py", "purpose": "no symbol"}],
                    [{"symbol_id": "", "purpose": "x"}],
                    [],
                    "not a list"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.write(bad)
        self.assertEqual(card_store.digests(self.cards, self.root.as_posix()), before)

    def test_an_unknown_freshness_filter_is_refused(self):
        with self.assertRaisesRegex(ValueError, "freshness"):
            self.query(freshness="mostly-fresh")


class CardEntryPointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-card-entry-")
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        write_project(self.project / "src")

    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPTS / "snapshot.py"), *map(str, args)],
                              capture_output=True, text=True)

    def test_the_command_line_writes_then_reads_cards_beside_the_snapshot(self):
        manifest = self.project / "loose" / "manifest.sqlite"
        snapshot.write_snapshot(self.project / "src", manifest)
        payload = self.project / "cards.json"
        payload.write_text(json.dumps({"cards": [
            {"file": "pkg/b.py", "symbol": "helper", "purpose": "adds one", "invariants": ["pure"]}]}),
            encoding="utf-8")

        wrote = self.cli("meta-upsert", manifest, "--input", payload)
        self.assertEqual(wrote.returncode, 0, wrote.stderr)
        self.assertTrue((manifest.parent / "cards.sqlite").is_file())

        read = self.cli("meta-query", manifest, "--symbol", "pkg/b.py::helper", "--no-history")
        self.assertEqual(read.returncode, 0, read.stderr)
        symbol = json.loads(read.stdout)["symbols"][0]
        self.assertEqual((symbol["freshness"], symbol["card"]["invariants"]), ("fresh", ["pure"]))

        refused = self.cli("meta-upsert", manifest, "--input", payload, "--cards", self.project)
        self.assertEqual(refused.returncode, 2)

        piped = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "meta-upsert", str(manifest), "--input", "-"],
            input=json.dumps([{"file": "pkg/b.py", "symbol": "helper", "purpose": "adds one, piped"}]),
            capture_output=True, text=True)
        self.assertEqual(piped.returncode, 0, piped.stderr)
        read = self.cli("meta-query", manifest, "--symbol", "pkg/b.py::helper", "--no-history")
        self.assertEqual(json.loads(read.stdout)["symbols"][0]["card"]["purpose"], "adds one, piped")

        invalid = self.cli("meta-query", manifest, "--freshness", "mostly-fresh")
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("freshness", invalid.stderr)

    def test_a_run_reads_the_analysis_root_cards_and_its_snapshot_never_changes(self):
        service = mcp_service.MapService(self.project)
        service.create_run("src", "carded", depth="lite")
        run_snapshot = service.root / "runs" / "carded" / "snapshot" / "manifest.sqlite"
        before = artifact_digest(run_snapshot)

        with open_snapshot(run_snapshot) as store:
            semantic_store.upsert_meta_cards(
                store, card_store.default_cards_path(run_snapshot),
                [{"file": "pkg/b.py", "symbol": "helper", "purpose": "adds one"}])

        self.assertEqual(artifact_digest(run_snapshot), before)
        self.assertEqual(card_store.default_cards_path(run_snapshot), (service.root / "cards.sqlite").resolve())
        symbol = service.meta_query("carded", symbol="pkg/b.py::helper")["symbols"][0]
        self.assertEqual((symbol["freshness"], symbol["card"]["purpose"]), ("fresh", "adds one"))
        impact = service.edit_impact("carded", ["pkg/b.py::helper"], include_source=False)
        self.assertEqual(impact["targets"][0]["card"]["purpose"], "adds one")
        self.assertEqual(impact["targets"][0]["card"]["freshness"], "fresh")
        self.assertEqual(artifact_digest(run_snapshot), before)

    def test_the_store_is_a_plain_sqlite_file_with_its_own_identity(self):
        path = self.project / "cards.sqlite"
        card_store.write_cards(path, "root", [{
            "symbol_id": "a.py::f", "file": "a.py", "symbol": "f", "kind": "function",
            "body_hash": "b", "interface_hash": "i", "effects_hash": "e", "callee_digest": "",
            "payload": {"purpose": "x"}}])

        with closing(sqlite3.connect(path)) as database:
            self.assertEqual(database.execute("PRAGMA application_id").fetchone()[0], card_store.APPLICATION_ID)
            self.assertEqual(database.execute("SELECT count(*) FROM cards").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
