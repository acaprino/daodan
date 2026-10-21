"""Symbols-at maps diff lines and explicit ranges to snapshot symbols.

The oracle is positional honesty: removed lines are read in the base snapshot,
added lines in the candidate, and anything the snapshots cannot place is a
declared gap rather than an invented symbol.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import mcp_service
import snapshot
from snapshot_store import open_snapshot

SOURCE = (
    "class Box:\n"
    "    def run(self, value):\n"
    "        return value + 1\n"
    "\n"
    "def helper(value):\n"
    "    return value\n"
)


def write_project(root: Path, source: str = SOURCE) -> None:
    (root / "pkg").mkdir(parents=True, exist_ok=True)
    (root / "pkg/__init__.py").write_text("", encoding="utf-8")
    (root / "pkg/a.py").write_text(source, encoding="utf-8")
    (root / "README.md").write_text("# Project\n\nText.\n", encoding="utf-8")


class SymbolsAtTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-symbols-at-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        write_project(self.root)
        self.out = self.root / ".codebase-map" / "manifest.sqlite"
        snapshot.write_snapshot(self.root, self.out)

    def at(self, requests, **kwargs):
        with open_snapshot(self.out) as store:
            return snapshot.symbols_at(store, requests, **kwargs)

    def test_a_range_reports_every_overlapping_symbol_with_its_sourcemap(self):
        result = self.at([{"path": "pkg/a.py", "ranges": [{"start": 2, "end": 3}]}])

        self.assertEqual(result["schema"], snapshot.SYMBOLS_AT_SCHEMA)
        symbols = result["results"][0]["ranges"][0]["symbols"]
        self.assertEqual([item["entity_id"] for item in symbols],
                         ["pkg/a.py::Box.run", "pkg/a.py::Box"])
        entity = symbols[0]
        self.assertEqual(entity["entity_key"]["chain"], ["pkg/a.py", "Box"])
        self.assertEqual(entity["entity_key"]["kind"], "method")
        self.assertEqual(entity["entity_key"]["name"], "run")
        self.assertIsNone(entity["entity_key"]["overload"])
        anchor = entity["anchor"]
        self.assertEqual((anchor["file"], anchor["start_line"], anchor["end_line"]), ("pkg/a.py", 2, 3))
        self.assertEqual(anchor["byte_precision"], "unavailable")
        self.assertEqual(entity["signatures"][0]["params"], [{"name": "self"}, {"name": "value"}])
        self.assertEqual(result["summary"], {"requests": 1, "symbols": 2, "gaps": 0})

    def test_unplaced_ranges_and_files_without_an_ast_are_declared_gaps(self):
        result = self.at([
            {"path": "pkg/a.py", "ranges": [{"start": 4, "end": 4}]},
            {"path": "README.md", "ranges": [{"start": 1, "end": 1}]},
            {"path": "pkg/missing.py", "ranges": [{"start": 1, "end": 1}]},
        ])

        reasons = [gap["reason"] for item in result["results"] for gap in item["gaps"]]
        self.assertEqual(reasons, ["outside-symbols", "no-ast", "not-inventoried"])
        self.assertEqual(result["summary"]["gaps"], 3)

    def test_invalid_requests_are_refused(self):
        for requests in ([], [{"path": "pkg/a.py", "ranges": []}],
                         [{"path": "pkg/a.py", "ranges": [{"start": 3, "end": 2}]}],
                         [{"path": "pkg/a.py", "ranges": [{"start": 1, "end": 99}]}]):
            with self.subTest(requests=requests), self.assertRaises(ValueError):
                self.at(requests)


class SymbolsAtDiffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-symbols-at-diff-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        write_project(self.root, "def helper(value):\n    return value + 1\n")
        self.base = self.root / "base.sqlite"
        snapshot.write_snapshot(self.root, self.base)
        (self.root / "pkg/a.py").write_text(
            "# one\n# two\ndef helper(value):\n    return value + 2\n", encoding="utf-8")
        self.candidate = self.root / "candidate.sqlite"
        snapshot.write_snapshot(self.root, self.candidate)

    def diff_at(self, diff):
        with open_snapshot(self.base) as base, open_snapshot(self.candidate) as candidate:
            return snapshot.symbols_at(candidate, base=base, diff=diff)

    def test_removed_lines_use_the_base_and_added_lines_the_candidate(self):
        result = self.diff_at(
            "diff --git a/pkg/a.py b/pkg/a.py\n"
            "--- a/pkg/a.py\n+++ b/pkg/a.py\n"
            "@@ -1,2 +1,4 @@\n"
            "+# one\n+# two\n"
            " def helper(value):\n"
            "-    return value + 1\n"
            "+    return value + 2\n")

        self.assertEqual(result["mode"], "diff")
        hunk = result["hunks"][0]
        base_symbols = hunk["base"]["ranges"][0]["symbols"]
        candidate_ranges = hunk["candidate"]["ranges"]
        self.assertEqual([item["entity_id"] for item in base_symbols], ["pkg/a.py::helper"])
        self.assertEqual(base_symbols[0]["anchor"]["start_line"], 1)
        self.assertEqual(candidate_ranges[0]["symbols"], [], "comment lines belong to no symbol")
        self.assertEqual([item["entity_id"] for item in candidate_ranges[1]["symbols"]],
                         ["pkg/a.py::helper"])
        self.assertEqual(candidate_ranges[1]["symbols"][0]["anchor"]["start_line"], 3)
        self.assertEqual(hunk["candidate"]["gaps"][0]["reason"], "outside-symbols")

    def test_a_rename_keeps_both_paths(self):
        (self.root / "pkg/a.py").rename(self.root / "pkg/renamed.py")
        candidate = self.root / "renamed.sqlite"
        snapshot.write_snapshot(self.root, candidate)
        diff = (
            "diff --git a/pkg/a.py b/pkg/renamed.py\n"
            "rename from pkg/a.py\nrename to pkg/renamed.py\n"
            "--- a/pkg/a.py\n+++ b/pkg/renamed.py\n"
            "@@ -2 +4 @@\n-    return value + 1\n+    return value + 2\n")
        with open_snapshot(self.base) as base, open_snapshot(candidate) as current:
            result = snapshot.symbols_at(current, base=base, diff=diff)

        hunk = result["hunks"][0]
        self.assertTrue(hunk["renamed"])
        self.assertEqual(hunk["base"]["ranges"][0]["symbols"][0]["entity_id"], "pkg/a.py::helper")
        self.assertEqual(hunk["candidate"]["ranges"][0]["symbols"][0]["entity_id"],
                         "pkg/renamed.py::helper")

    def test_added_and_removed_files_have_one_sided_gaps(self):
        result = self.diff_at(
            "diff --git a/pkg/new.py b/pkg/new.py\n"
            "--- /dev/null\n+++ b/pkg/a.py\n"
            "@@ -0,0 +4 @@\n+    return value + 2\n"
            "diff --git a/pkg/a.py b/pkg/a.py\n"
            "--- a/pkg/a.py\n+++ /dev/null\n"
            "@@ -1 +0,0 @@\n-def helper(value):\n")

        added, removed = result["hunks"]
        self.assertEqual(added["base"]["gaps"], [{"reason": "file-added"}])
        self.assertEqual(added["candidate"]["ranges"][0]["symbols"][0]["entity_id"], "pkg/a.py::helper")
        self.assertEqual(removed["candidate"]["gaps"], [{"reason": "file-removed"}])
        self.assertEqual(removed["base"]["ranges"][0]["symbols"][0]["entity_id"], "pkg/a.py::helper")

    def test_plain_unified_diff_sections_keep_their_own_paths(self):
        sections = snapshot.parse_unified_diff(
            "--- a/one.py\n+++ b/one.py\n@@ -1 +1 @@\n-a\n+b\n"
            "--- a/two.py\n+++ b/two.py\n@@ -3 +4 @@\n-c\n+d\n")

        self.assertEqual([(item["old_path"], item["new_path"]) for item in sections],
                         [("one.py", "one.py"), ("two.py", "two.py")])
        self.assertEqual([item["hunks"][0]["removed_ranges"] for item in sections],
                         [[{"start": 1, "end": 1}], [{"start": 3, "end": 3}]])
        marked = snapshot.parse_unified_diff(
            "--- a/one.py\n+++ b/one.py\n@@ -1,2 +1,2 @@\n--- old\n+++ new\n")
        self.assertEqual(marked[0]["old_path"], "one.py")
        self.assertEqual(marked[0]["hunks"][0]["removed_ranges"], [{"start": 1, "end": 1}])
        self.assertEqual(marked[0]["hunks"][0]["added_ranges"], [{"start": 1, "end": 1}])

    def test_the_command_line_reads_ranges_and_a_diff_file(self):
        def run(*args):
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "snapshot.py"), *map(str, args)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(proc.stdout)

        ranged = run("symbols-at", self.candidate, "--request", "pkg/a.py:4:4")
        self.assertEqual(ranged["results"][0]["ranges"][0]["symbols"][0]["entity_id"],
                         "pkg/a.py::helper")
        diff_path = self.root / "change.diff"
        diff_path.write_text(
            "--- a/pkg/a.py\n+++ b/pkg/a.py\n@@ -2 +4 @@\n"
            "-    return value + 1\n+    return value + 2\n", encoding="utf-8")
        diffed = run("symbols-at", self.candidate, "--base", self.base, "--diff", diff_path)
        self.assertEqual(diffed["summary"]["hunks"], 1)

    def test_the_mcp_service_exposes_the_same_query(self):
        project = self.root / "project"
        write_project(project / "src")
        service = mcp_service.MapService(project)
        service.create_run("src", "symbols", depth="lite")

        result = service.symbols_at(
            "symbols", requests=[{"path": "pkg/a.py", "ranges": [{"start": 2, "end": 2}]}])

        self.assertEqual(result["run_id"], "symbols")
        self.assertEqual(result["results"][0]["ranges"][0]["symbols"][0]["entity_id"],
                         "pkg/a.py::Box.run")


if __name__ == "__main__":
    unittest.main()
