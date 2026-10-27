"""`snapshot.py write` builds the lexical index; `index` repairs it; `search` ranks it and never raises on a gap."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO_ROOT / "plugins/codebase-map/skills/map-method/scripts/snapshot.py"


class IndexCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "billing.py").write_text(
            "def invoiceTotal(items):\n    tax_adjustment = 7\n    return sum(items) + tax_adjustment\n", encoding="utf-8")
        (self.root / "other.py").write_text("def invoiceTotal(items):\n    return 0\n", encoding="utf-8")
        self.manifest = self.root / ".codebase-map/manifest.sqlite"
        self.index = self.manifest.with_name("retrieval.sqlite")

    def run_cli(self, *arguments):
        completed = subprocess.run([sys.executable, "-B", str(SNAPSHOT), *arguments],
                                   capture_output=True, text=True, encoding="utf-8", cwd=self.root)
        return completed.returncode, completed.stdout, completed.stderr

    def write(self, *extra):
        return self.run_cli("write", str(self.root), "--out", str(self.manifest), *extra)

    def test_write_builds_the_index_and_no_index_skips_it(self):
        code, out, err = self.write("--no-index")
        self.assertEqual((code, err), (0, ""))
        self.assertFalse(self.index.exists())
        code, out, err = self.write()
        self.assertEqual((code, err), (0, ""))
        self.assertIn("index: rebuilt -> ", out)
        self.assertIn("(4 documents)", out)
        self.assertTrue(self.index.exists())
        self.assertFalse(self.index.with_name("retrieval.sqlite.lock").exists())

    def test_index_reports_and_repairs_with_exit_codes(self):
        self.write("--no-index")
        code, out, _ = self.run_cli("index", str(self.manifest), "--check")
        report = json.loads(out)
        self.assertEqual((code, report["state"], report["action"]), (1, "missing", "reported"))
        self.assertFalse(self.index.exists())
        code, out, _ = self.run_cli("index", str(self.manifest))
        report = json.loads(out)
        self.assertEqual((code, report["state"], report["action"], report["previous"]), (0, "fresh", "rebuilt", "missing"))
        code, out, _ = self.run_cli("index", str(self.manifest), "--check")
        self.assertEqual((code, json.loads(out)["state"]), (0, "fresh"))
        self.index.write_bytes(b"not a database")
        code, out, _ = self.run_cli("index", str(self.manifest))
        report = json.loads(out)
        self.assertEqual((code, report["state"], report["previous"]), (0, "fresh", "corrupt"))
        code, _, err = self.run_cli("index", str(self.root / "elsewhere.sqlite"))
        self.assertEqual(code, 2)
        self.assertIn("error", err)
        lock = self.index.with_name("retrieval.sqlite.lock")
        lock.write_bytes(b"")
        self.index.unlink()
        code, out, _ = self.run_cli("index", str(self.manifest))
        self.assertEqual((code, json.loads(out)["state"]), (1, "failed"))
        code, out, _ = self.run_cli("index", str(self.manifest), "--break-lock")
        report = json.loads(out)
        self.assertEqual((code, report["state"], report["lock_broken"]), (0, "fresh", str(lock)))
        self.assertFalse(lock.exists())

    def test_search_ranks_trimmed_records_and_accepts_anchors(self):
        self.write()
        code, out, err = self.run_cli("search", str(self.manifest), "--query", "tax adjustment", "--limit", "2")
        self.assertEqual((code, err), (0, ""))
        result = json.loads(out)
        self.assertEqual(result["index_state"], "fresh")
        self.assertEqual(result["results"][0]["entity_id"], "billing.py::invoiceTotal")
        self.assertEqual(set(result["results"][0]),
                         {"entity_id", "kind", "path", "start_line", "end_line", "signatures", "provenance", "score"})
        self.assertNotIn("binding", result)
        self.assertEqual(result["limit"], 2)
        code, out, _ = self.run_cli("search", str(self.manifest), "--query", "invoice total",
                                    "--anchor", "other.py::invoiceTotal")
        result = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(result["results"][0]["entity_id"], "other.py::invoiceTotal")
        self.assertIn("exact", result["results"][0]["provenance"])
        code, out, _ = self.run_cli("search", str(self.manifest), "--query", "nothing here",
                                    "--anchor", '{"path": "billing.py", "line": 2}')
        result = json.loads(out)
        self.assertEqual((code, result["results"][0]["entity_id"]), (0, "billing.py::invoiceTotal"))
        self.assertEqual(result["results"][0]["provenance"], ["exact"])
        code, out, _ = self.run_cli("search", str(self.manifest), "--query", "invoice", "--limit", "200")
        self.assertEqual((code, json.loads(out)["limit"]), (0, 200))
        code, _, err = self.run_cli("search", str(self.manifest), "--query", "invoice", "--limit", "0")
        self.assertEqual(code, 2)
        self.assertIn("limit", err)

    def test_search_on_a_missing_or_stale_index_is_a_gap_not_an_error(self):
        self.write("--no-index")
        code, out, err = self.run_cli("search", str(self.manifest), "--query", "tax adjustment")
        self.assertEqual((code, err), (0, ""))
        result = json.loads(out)
        self.assertEqual((result["index_state"], result["results"]), ("missing", []))
        self.assertEqual(len(result["gaps"]), 1)
        self.assertTrue(result["gaps"][0].startswith("retrieval_missing: "))
        self.assertIn(f"snapshot.py index {self.manifest}", result["gaps"][0])
        self.assertEqual(result["capabilities"]["fts5"], False)
        self.assertIsNone(result["ranking_policy"])
        code, _, err = self.run_cli("search", str(self.manifest), "--query", "x", "--limit", "0")
        self.assertEqual(code, 2)
        self.assertIn("limit", err)
        code, _, err = self.run_cli("search", str(self.manifest), "--query", "x", "--anchor", '{"bogus": 1}')
        self.assertEqual(code, 2)
        self.assertIn("anchor keys", err)
        self.run_cli("index", str(self.manifest))
        (self.root / "billing.py").write_text("def invoiceTotal(items):\n    return sum(items)\n", encoding="utf-8")
        self.write("--no-index")
        code, out, _ = self.run_cli("search", str(self.manifest), "--query", "tax adjustment")
        result = json.loads(out)
        self.assertEqual((code, result["index_state"]), (0, "stale"))
        self.assertTrue(result["gaps"][0].startswith("retrieval_stale: "))
        self.assertTrue(self.index.exists())

    def test_verify_tree_rereads_sources_and_the_default_does_not(self):
        self.write()
        (self.root / "billing.py").write_text("def invoiceTotal(items):\n    return sum(items)\n", encoding="utf-8")
        code, out, _ = self.run_cli("search", str(self.manifest), "--query", "tax adjustment")
        self.assertEqual((code, json.loads(out)["results"][0]["entity_id"]), (0, "billing.py::invoiceTotal"))
        code, _, err = self.run_cli("search", str(self.manifest), "--query", "tax adjustment", "--verify-tree")
        self.assertEqual(code, 2)
        self.assertIn("refresh the manifest", err)


if __name__ == "__main__":
    unittest.main()
