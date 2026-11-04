"""Local retrieval protects evidence, freshness and atomic publication."""
import json
import sys
import sqlite3
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import snapshot
import retrieval
import source_reader


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write("billing.py", "def invoiceTotal(items):\n    tax_adjustment = 7\n    return sum(items) + tax_adjustment\n")
        self.write("other.py", "def invoiceTotal(items):\n    return 0\n")
        self.manifest = self.root / ".codebase-map/manifest.sqlite"
        self.index = self.manifest.with_name("retrieval.sqlite")
        snapshot.write_snapshot(self.root, self.manifest)

    def write(self, name, body):
        (self.root / name).write_text(body, encoding="utf-8")

    def refresh(self):
        return retrieval.refresh_index(self.manifest, self.index)

    def search(self, query="", anchors=None, limit=10):
        return retrieval.search(self.index, query, anchors=anchors or [], limit=limit)

    def test_exact_body_subtokens_and_traceback_keep_provenance(self):
        before = self.manifest.read_bytes()
        self.refresh()
        self.assertEqual(self.search("tax adjustment")["results"][0]["entity_id"], "billing.py::invoiceTotal")
        exact = self.search("invoice total", [{"entity_id": "other.py::invoiceTotal"}])
        self.assertEqual(exact["results"][0]["entity_id"], "other.py::invoiceTotal")
        self.assertIn("exact", exact["results"][0]["provenance"])
        trace = self.search('File "billing.py", line 2, in invoiceTotal')
        self.assertEqual(trace["results"][0]["entity_id"], "billing.py::invoiceTotal")
        self.assertIn("traceback", trace["results"][0]["provenance"])
        self.assertEqual(self.manifest.read_bytes(), before)

    def test_refresh_batches_source_reads(self):
        original = source_reader.read_packet
        calls = []

        def counted(store, requests):
            calls.append(requests)
            return original(store, requests)

        with mock.patch.object(source_reader, "read_packet", side_effect=counted):
            self.refresh()
        self.assertEqual(len(calls), 3)
        for requests in calls:
            self.assertEqual({request["path"] for request in requests}, {"billing.py", "other.py"})
            self.assertTrue(all(request["full_file"] for request in requests))

    def test_search_batches_source_freshness_verification(self):
        self.refresh()
        original = source_reader.read_packet
        calls = []

        def counted(store, requests):
            calls.append(requests)
            return original(store, requests)

        with mock.patch.object(source_reader, "read_packet", side_effect=counted):
            self.assertTrue(self.search("tax")["results"])
        self.assertEqual(len(calls), 1)
        self.assertEqual({request["path"] for request in calls[0]}, {"billing.py", "other.py"})
        self.assertTrue(all(request["full_file"] for request in calls[0]))

    def test_module_context_remains_searchable_and_line_addressable(self):
        self.write("billing.py", 'API_ENDPOINT = "payments.example"\n\ndef send(data):\n    return data\n')
        snapshot.write_snapshot(self.root, self.manifest)
        self.refresh()
        result = self.search("payments")
        self.assertEqual(result["results"][0]["entity_id"], "billing.py::@file")
        anchored = self.search(anchors=[{"path": "billing.py", "line": 1}])
        self.assertEqual(anchored["exact"], ["billing.py::@file"])
        inside = self.search(anchors=[{"path": "billing.py", "line": 4}])
        self.assertEqual(inside["exact"], ["billing.py::send"])

    def test_form_feed_preserves_physical_lines(self):
        self.write("billing.py", 'def execute():\n    text = "first\fsecond"\n    return text\n')
        snapshot.write_snapshot(self.root, self.manifest)
        self.refresh()
        self.assertEqual(self.search("second")["results"][0]["entity_id"], "billing.py::execute")

    def test_external_traceback_frames_are_gaps_without_losing_project_frames(self):
        self.refresh()
        result = self.search('File "<stdin>", line 1\nFile "billing.py", line 2')
        self.assertIn("billing.py::invoiceTotal", result["exact"])
        self.assertTrue(result["gaps"])
        with self.assertRaisesRegex(ValueError, "inventoried"):
            self.search(anchors=[{"path": "<stdin>", "line": 1}])

    def test_ambiguous_names_stay_candidates_and_limits_are_visible(self):
        self.refresh()
        result = self.search("", [{"symbol": "invoiceTotal"}], limit=1)
        self.assertEqual(result["exact"], [])
        self.assertEqual(result["ambiguous"][0]["total"], 2)
        self.assertEqual((result["matched"], result["returned"], result["truncated"]), (2, 1, 1))
        self.assertEqual(result, self.search("", [{"symbol": "invoiceTotal"}], limit=1))
        self.assertEqual(self.search("", [{"symbol": "invoicetotal"}])["matched"], 0)

    def test_incremental_rename_remove_and_full_rebuild_agree(self):
        first = self.refresh()
        second = self.refresh()
        self.assertEqual(second["reused"], first["documents"])
        self.assertEqual(second["updated"], 0)
        (self.root / "other.py").unlink()
        self.write("billing.py", "def receiptTotal(items):\n    return sum(items)\n")
        self.write("exports.py", "def exported():\n    return 4\n")
        snapshot.write_snapshot(self.root, self.manifest)
        self.assertEqual(self.refresh()["removed"], 3)
        incremental = self.search("total exported")
        separate = self.manifest.with_name("fresh-retrieval.sqlite")
        retrieval.refresh_index(self.manifest, separate)
        fresh = retrieval.search(separate, "total exported", anchors=[], limit=10)
        self.assertEqual(incremental["results"], fresh["results"])
        self.assertEqual(incremental["document_digest"], fresh["document_digest"])

    def test_changed_sources_manifest_or_new_file_require_refresh(self):
        self.refresh()
        original = (self.root / "billing.py").read_text()
        self.write("billing.py", original.replace("7", "9"))
        with self.assertRaisesRegex(ValueError, "source|stale"):
            self.search("tax")
        snapshot.write_snapshot(self.root, self.manifest)
        with self.assertRaisesRegex(ValueError, "snapshot|stale"):
            self.search("tax")
        self.refresh()
        self.write("new_export.py", "def new_export(): return 1\n")
        with self.assertRaisesRegex(ValueError, "inventory|refresh"):
            self.search("new export")

    def test_publication_failure_preserves_previous_index(self):
        self.refresh()
        before = self.index.read_bytes()
        with mock.patch.object(retrieval.os, "replace", side_effect=OSError("disk unavailable")):
            with self.assertRaises(OSError):
                self.refresh()
        self.assertEqual(self.index.read_bytes(), before)
        self.assertTrue(self.search("tax")["results"])

    def test_concurrent_source_change_preserves_previous_index(self):
        self.refresh()
        before = self.index.read_bytes()
        original = retrieval._documents
        def documents_then_change(store):
            yield from original(store)
            self.write("billing.py", "def invoiceTotal(items): return 99\n")
        with mock.patch.object(retrieval, "_documents", documents_then_change):
            with self.assertRaisesRegex(ValueError, "source changed"):
                self.refresh()
        self.assertEqual(self.index.read_bytes(), before)

    def test_empty_registry_and_absent_export_are_reindexed(self):
        self.write("registry.py", "")
        snapshot.write_snapshot(self.root, self.manifest)
        self.refresh()
        self.assertEqual(self.search("registeredHandler")["matched"], 0)
        self.write("registry.py", "registeredHandler = 'invoiceTotal'\n")
        snapshot.write_snapshot(self.root, self.manifest)
        self.refresh()
        result = self.search("registeredHandler")
        self.assertTrue(any(r["anchor"]["file"] == "registry.py" for r in result["results"]))

    def test_index_errors_do_not_turn_into_empty_results(self):
        self.refresh()
        db = sqlite3.connect(self.index)
        try:
            db.execute("DROP TABLE search_text")
            db.commit()
        finally:
            db.close()
        with self.assertRaises(sqlite3.DatabaseError):
            self.search("tax")

    def test_hidden_sources_and_linked_destinations_are_not_indexed(self):
        hidden = self.root / ".hidden"
        hidden.mkdir()
        (hidden / "secret.py").write_text("def confidential(): return 1\n")
        self.refresh()
        self.assertEqual(self.search("confidential")["matched"], 0)
        link = self.manifest.with_name("linked.sqlite")
        try:
            link.symlink_to(self.index)
        except OSError:
            self.skipTest("host does not allow symlinks")
        with self.assertRaises(ValueError):
            retrieval.refresh_index(self.manifest, link)
        with self.assertRaises(ValueError):
            retrieval.search(link, "tax", anchors=[], limit=10)

    def test_missing_fts5_is_an_error_not_empty_retrieval(self):
        with mock.patch.object(retrieval, "_require_fts5", side_effect=ValueError("SQLite FTS5 unavailable")):
            with self.assertRaisesRegex(ValueError, "FTS5"):
                self.refresh()
        self.assertFalse(self.index.exists())

    def test_index_destination_cannot_replace_manifest_or_source(self):
        for dest in (self.manifest, self.root / "billing.py", self.root.parent / "escape.sqlite"):
            with self.subTest(dest=dest), self.assertRaises(ValueError):
                retrieval.refresh_index(self.manifest, dest)

    def test_anchor_validation_and_optional_embeddings_are_explicit(self):
        self.refresh()
        for anchor in ({"path": "../billing.py"}, {"path": "missing.py"}, {"path": "billing.py", "line": 999}):
            with self.subTest(anchor=anchor), self.assertRaises(ValueError):
                self.search(anchors=[anchor])
        with self.assertRaises(ValueError):
            self.search(limit=True)
        self.assertEqual(self.search("calcolo imposte")["capabilities"]["embedding"], "unavailable")
        with self.assertRaisesRegex(ValueError, "embedding"):
            retrieval.search(self.index, "tax", anchors=[], limit=2, embedding_result={"results": []})

    def test_context_contract_exports_four_schemas_and_i1_fields(self):
        plugin = SCRIPTS.parents[2]
        metadata = tomllib.loads((plugin / "plugin.toml").read_text())
        self.assertIn("contracts/context.toml", metadata["contracts"]["exports"])
        contract = tomllib.loads((plugin / "contracts/context.toml").read_text())
        schemas = {item["record_schema"]: item for item in contract["records"]}
        self.assertEqual(set(schemas), {f"daodan/{name}/v1" for name in
                        ("context-request", "scope-plan", "context-packet", "map-slice")})
        self.assertTrue({"snapshot", "components", "edges", "gaps"} <= set(schemas["daodan/map-slice/v1"]["required"]))


class IndexStateTests(unittest.TestCase):
    """The index lifecycle reports one state and repairs only what is not fresh."""

    setUp = RetrievalTests.setUp
    write = RetrievalTests.write
    refresh = RetrievalTests.refresh
    search = RetrievalTests.search

    def state(self):
        return retrieval.index_state(self.manifest, self.index)

    def test_missing_fresh_and_default_index_name(self):
        self.assertEqual(self.state()["state"], "missing")
        self.assertEqual(retrieval.index_name(self.manifest), self.index)
        self.refresh()
        fresh = self.state()
        self.assertEqual((fresh["state"], fresh["documents"]), ("fresh", 4))
        self.assertEqual(retrieval.index_state(self.manifest)["state"], "fresh")
        with snapshot.open_snapshot(self.manifest) as store:
            self.assertEqual(fresh["binding"]["manifest_digest"], retrieval._binding(store)["manifest_digest"])

    def test_stale_names_the_differing_binding_keys(self):
        self.refresh()
        self.write("billing.py", "def invoiceTotal(items):\n    return sum(items)\n")
        snapshot.write_snapshot(self.root, self.manifest)
        stale = self.state()
        self.assertEqual(stale["state"], "stale")
        self.assertIn("manifest_digest", stale["reason"])
        with self.assertRaisesRegex(ValueError, "stale retrieval index"):
            self.search("invoice")

    def test_other_schema_is_stale_and_an_unreadable_index_is_failed(self):
        self.refresh()
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(self.index)) as db:
            metadata = json.loads(db.execute("SELECT value FROM metadata").fetchone()[0])
            metadata["binding"]["schema"] = "daodan/retrieval-index/v2"
            db.execute("DELETE FROM metadata")
            db.execute("INSERT INTO metadata VALUES(?)", (json.dumps(metadata),))
            db.commit()
        stale = self.state()
        self.assertEqual(stale["state"], "stale")
        self.assertIn("schema", stale["reason"])
        self.assertEqual(retrieval.ensure_index(self.manifest, self.index)["action"], "rebuilt")
        with mock.patch.object(retrieval, "_read", side_effect=sqlite3.OperationalError("database is locked")):
            failed = retrieval.index_state(self.manifest, self.index)
            self.assertEqual(failed["state"], "failed")
            self.assertEqual(retrieval.ensure_index(self.manifest, self.index)["action"], "none")
        self.assertTrue(self.index.exists())
        self.assertEqual(self.state()["state"], "fresh")

    def test_gap_result_carries_the_whole_envelope(self):
        gap = retrieval.gap_result(self.state(), 7, "snapshot.py index M")
        self.assertEqual(set(gap), set(retrieval.public_result(self.refresh_and_search())) | {"index_state"})
        self.assertEqual((gap["index_state"], gap["results"], gap["limit"], gap["capabilities"]["fts5"]),
                         ("missing", [], 7, False))
        self.assertTrue(gap["gaps"][0].startswith("retrieval_missing: "))
        self.assertTrue(gap["gaps"][0].endswith("run snapshot.py index M"))

    def refresh_and_search(self):
        self.refresh()
        return self.search("tax adjustment", limit=2)

    def test_corrupt_index_is_reported_and_rebuilt(self):
        self.index.write_bytes(b"not a database")
        corrupt = self.state()
        self.assertEqual(corrupt["state"], "corrupt")
        self.assertIn("not a readable retrieval index", corrupt["reason"])
        checked = retrieval.ensure_index(self.manifest, self.index, check=True)
        self.assertEqual((checked["state"], checked["action"]), ("corrupt", "reported"))
        self.assertEqual(self.index.read_bytes(), b"not a database")
        repaired = retrieval.ensure_index(self.manifest, self.index)
        self.assertEqual((repaired["state"], repaired["action"], repaired["previous"]), ("fresh", "rebuilt", "corrupt"))
        self.assertEqual(repaired["refresh"]["mode"], "rebuild")
        self.assertEqual(self.search("tax adjustment")["results"][0]["entity_id"], "billing.py::invoiceTotal")

    def test_ensure_index_refreshes_stale_and_leaves_fresh_alone(self):
        built = retrieval.ensure_index(self.manifest, self.index)
        self.assertEqual((built["state"], built["action"], built["previous"]), ("fresh", "rebuilt", "missing"))
        untouched = retrieval.ensure_index(self.manifest, self.index)
        self.assertEqual((untouched["state"], untouched["action"]), ("fresh", "none"))
        self.assertNotIn("refresh", untouched)
        self.write("billing.py", "def invoiceTotal(items):\n    return sum(items)\n")
        snapshot.write_snapshot(self.root, self.manifest)
        refreshed = retrieval.ensure_index(self.manifest, self.index)
        self.assertEqual((refreshed["state"], refreshed["action"], refreshed["previous"]), ("fresh", "refreshed", "stale"))
        self.assertEqual(refreshed["refresh"]["mode"], "incremental")

    def test_held_lock_and_missing_fts5_are_failed_not_raised(self):
        lock = self.index.with_name(self.index.name + ".lock")
        lock.write_bytes(b"")
        held = retrieval.ensure_index(self.manifest, self.index)
        self.assertEqual((held["state"], held["action"], held["lock"]), ("failed", "none", str(lock)))
        self.assertIn("lock held", held["reason"])
        missing = self.state()
        self.assertEqual((missing["state"], missing["lock"]), ("missing", str(lock)))
        self.assertGreaterEqual(missing["lock_age_s"], 0)
        leftover = self.index.with_name(".retrieval-crashed.sqlite")
        leftover.write_bytes(b"half written")
        broken = retrieval.ensure_index(self.manifest, self.index, break_lock=True)
        self.assertEqual((broken["state"], broken["action"], broken["lock_broken"]), ("fresh", "rebuilt", str(lock)))
        self.assertFalse(lock.exists())
        self.assertFalse(leftover.exists())
        lock.write_bytes(b"")
        checked = retrieval.ensure_index(self.manifest, self.index, check=True)
        self.assertEqual((checked["state"], checked["action"], checked["lock"]), ("fresh", "none", str(lock)))
        self.assertTrue(lock.exists())
        swept = retrieval.ensure_index(self.manifest, self.index, break_lock=True)
        self.assertEqual((swept["state"], swept["action"]), ("fresh", "none"))
        self.assertFalse(lock.exists())
        self.index.unlink()
        with mock.patch.object(retrieval, "_require_fts5", side_effect=ValueError("SQLite FTS5 unavailable; use a Python runtime with FTS5")):
            failed = retrieval.ensure_index(self.manifest, self.index)
        self.assertEqual(failed["state"], "failed")
        self.assertIn("FTS5 unavailable", failed["reason"])
        self.assertFalse(self.index.exists())
        with self.assertRaises(ValueError):
            retrieval.index_state(self.manifest, self.root / "elsewhere.sqlite")

    def test_search_verify_false_skips_only_the_tree_read(self):
        self.refresh()
        with mock.patch.object(retrieval, "_verify_tree", side_effect=AssertionError("tree read")) as read:
            result = retrieval.search(self.index, "tax adjustment", anchors=[], limit=5, verify=False)
            self.assertEqual(result["results"][0]["entity_id"], "billing.py::invoiceTotal")
            read.assert_not_called()
            with self.assertRaisesRegex(AssertionError, "tree read"):
                retrieval.search(self.index, "tax adjustment", anchors=[], limit=5)
        self.write("billing.py", "def invoiceTotal(items):\n    return sum(items)\n")
        snapshot.write_snapshot(self.root, self.manifest)
        with self.assertRaisesRegex(ValueError, "stale retrieval index"):
            retrieval.search(self.index, "tax adjustment", anchors=[], limit=5, verify=False)

    def test_public_result_trims_records_and_keeps_the_envelope(self):
        self.refresh()
        public = retrieval.public_result(self.search("tax adjustment", limit=2))
        self.assertEqual(set(public), {"schema", "document_digest", "exact", "exact_total", "exact_truncated", "ambiguous",
                                       "matched", "returned", "truncated", "limit", "gaps", "ranking_policy",
                                       "capabilities", "results"})
        first = public["results"][0]
        self.assertEqual(set(first), {"entity_id", "kind", "path", "start_line", "end_line", "signatures", "provenance", "score"})
        self.assertEqual((first["entity_id"], first["kind"], first["path"], first["start_line"]),
                         ("billing.py::invoiceTotal", "function", "billing.py", 1))
        self.assertIn("fts5", first["provenance"])
        self.assertNotIn("binding", public)
        self.assertNotIn("anchor", first)


if __name__ == "__main__":
    unittest.main()
