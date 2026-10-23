"""Local retrieval protects evidence, freshness and atomic publication."""
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


if __name__ == "__main__":
    unittest.main()
