"""Source identity and consumer integration for portable semantic evidence."""

import copy
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))

import snapshot
from languages import python
from analyze_file import analyze_single_file, format_as_markdown
from semantic_index import build_semantic_index


class SemanticSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="map-semantic-integration-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def observation(self, notes=None):
        data = b"def save():\n    return 1\n"
        source = self.root / "core.py"
        source.write_bytes(data)
        result = python.adapter.parse(data.decode(), str(source))
        result.semantic = {
            "version": 1, "backend": "stdlib-ast", "status": "ast", "notes": [],
            "scopes": [{"id": "module", "parent": None, "kind": "module"}],
            "declarations": [{"id": "function@1:0", "name": "save", "kind": "function",
                              "scope": "module", "span": [1, 0, 2, 12]}],
            "imports": [], "exports": [{"exported": "save", "local": "save"}], "references": [],
        }
        if notes is not None:
            result.notes = notes
        return source, data, result

    def test_semantic_evidence_is_bound_to_observed_bytes_and_copied(self):
        source, data, result = self.observation()
        expected = copy.deepcopy(result.semantic)
        entry = snapshot.file_entry(source, data, 1.0, parse_result=result)
        self.assertEqual(entry["raw_hash"], hashlib.sha256(data).hexdigest())
        self.assertEqual(entry.get("semantic"), expected)
        result.semantic["declarations"].clear()
        self.assertEqual(entry["semantic"], expected)

    def test_partial_syntax_cannot_certify_complete_reference_coverage(self):
        source, data, result = self.observation(["parser=stdlib-ast", "syntax error: incomplete source"])
        entry = snapshot.file_entry(source, data, 1.0, parse_result=result)
        self.assertEqual(entry["status"], "parse-error")
        self.assertNotIn("semantic", entry)

    def test_changed_bytes_do_not_reuse_old_semantic_payload(self):
        source, data, result = self.observation()
        first = snapshot.build_manifest(self.root, parse_results={source: (data.decode(), result)})
        source.write_text("def renamed():\n    return 2\n", encoding="utf-8")
        second = snapshot.build_manifest(self.root, previous=first)
        self.assertEqual(second["metrics"]["cache_hits"], 0)
        self.assertNotEqual(first["files"]["core.py"]["raw_hash"], second["files"]["core.py"]["raw_hash"])
        self.assertNotEqual(first["files"]["core.py"].get("semantic"), second["files"]["core.py"].get("semantic"))

    def test_observations_reuse_prefetched_target_without_another_source_read(self):
        source, data, result = self.observation()
        observations = {"removed.py": b"stale input"}
        original = Path.read_bytes

        def read_bytes(path):
            if path == source:
                self.fail("prefetched target was read again")
            return original(path)

        with mock.patch.object(Path, "read_bytes", read_bytes):
            manifest = snapshot.build_manifest(
                self.root, parse_results={source: (data.decode(), result)},
                source_observations=observations,
            )
        self.assertEqual(observations, {"core.py": data})
        self.assertEqual(manifest["metrics"]["files_read"], 0)

    def test_cycle_diagnostics_can_retain_self_import_without_changing_default_graph(self):
        (self.root / "loop.py").write_text("import loop\n", encoding="utf-8")
        manifest = snapshot.build_manifest(self.root)
        self.assertEqual(snapshot.module_targets(manifest)["loop.py"], [])
        self.assertEqual(snapshot.module_targets(manifest, include_self=True)["loop.py"], ["loop.py"])


class SemanticConsumerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="map-semantic-consumer-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "project"
        self.root.mkdir()

    def write(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_analysis_exposes_alias_callsites_and_reads_target_once(self):
        source = self.write("core.py", "def save():\n    return 1\n")
        self.write("consumer.py", "from core import save as persist\ndef run():\n    persist(); persist()\n")
        self.write("decoys.py", "# save()\ntext = 'save()'\ndef run(save):\n    save()\n")
        original = Path.read_bytes
        reads = []

        def read_bytes(path):
            if path == source:
                reads.append(path)
            return original(path)

        with mock.patch.object(Path, "read_bytes", read_bytes):
            result = analyze_single_file(source, True, self.root, "save")
        self.assertEqual(len(reads), 1)
        semantic = result["semantic_analysis"]
        incoming = semantic["incoming_calls"]
        self.assertEqual([(ref["file"], ref["parts"]) for ref in incoming],
                         [("consumer.py", ["persist"]), ("consumer.py", ["persist"])])
        self.assertTrue(all(ref["resolution"] == "resolved" for ref in incoming))
        self.assertTrue(all(ref["caller"].startswith("consumer.py::") for ref in incoming))
        self.assertEqual(result["usages"]["save"]["resolved_count"], 2)
        self.assertIn("resolved", format_as_markdown(result).lower())
        json.dumps(result)
        self.assertNotIn("_source_text", result)

    def test_file_graph_distinguishes_direct_importers_and_transitive_reachability(self):
        source = self.write("core.py", "import core\ndef save():\n    return 1\n")
        self.write("middle.py", "import core\n")
        self.write("front.py", "import middle\n")
        result = analyze_single_file(source, project_root=self.root)
        self.assertEqual(result["imported_by_count"], 1)
        graph = result["dependency_graph"]
        self.assertEqual(graph["import_cycles"], [["core.py"]])
        self.assertEqual({item["file"]: item["depth"] for item in graph["transitive_importers"]},
                         {"middle.py": 1, "front.py": 2})
        self.assertGreater(graph["pagerank"], 0)

    def test_diff_records_transitive_diagnostics_without_expanding_recommendation(self):
        source = self.write("core.py", "def save():\n    return 1\n")
        self.write("middle.py", "import core\n")
        self.write("front.py", "import middle\n")
        parent = self.home / "parent"
        (parent / "snapshot").mkdir(parents=True)
        out = self.home / "update"
        # This test isolates update policy from concurrent helper development.
        with mock.patch.object(snapshot, "parser_fingerprint", return_value="integration-fixture"):
            manifest = snapshot.build_manifest(self.root)
            (parent / "snapshot/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (parent / "state.json").write_text('{"status":"complete"}', encoding="utf-8")
            source.write_text("def save():\n    return 2\n", encoding="utf-8")
            snapshot.cmd_diff(argparse.Namespace(parent_run=str(parent), target=str(self.root),
                                                out=str(out), flags=None, verify=True, threshold=0.8))
        changes = json.loads((out / "changes.json").read_text())
        self.assertEqual(changes["recommendation"], "incremental")
        self.assertEqual(changes["affected_files"], ["core.py", "middle.py"])
        self.assertEqual({item["file"]: item["depth"] for item in changes["transitive_importers"]},
                         {"middle.py": 1, "front.py": 2})
        self.assertIn("Transitive", (out / "changes.md").read_text())

    @unittest.skipIf(sys.version_info < (3, 12), "generic Python syntax requires Python 3.12")
    def test_unsupported_scope_generic_headers_and_methods_cannot_link_to_outer_name(self):
        fixtures = ["def run[save](x: save()): pass\n",
                    "def run[save]() -> save(): pass\n",
                    "class C[save](save()): pass\n",
                    "class C[save]:\n    def run(self): save()\n"]
        for body in fixtures:
            with self.subTest(body=body):
                self.write("main.py", "def save(): pass\n" + body)
                observations = {}
                manifest = snapshot.build_manifest(self.root, source_observations=observations)
                index = build_semantic_index(manifest, source_observations=observations)
                calls = [ref for ref in index["references"] if ref["kind"] == "call"]
                self.assertTrue(calls)
                self.assertTrue(all(ref["resolution"] != "resolved" for ref in calls))

    def test_unsupported_scope_direct_eval_mutation_blocks_ancestor_binding(self):
        from languages._treesitter import get_parser
        if get_parser("javascript") is None:
            self.skipTest("JavaScript grammar unavailable")
        self.write("main.js", 'function save(){}; function mutate(){eval("save=()=>2")} mutate(); save();')
        observations = {}
        manifest = snapshot.build_manifest(self.root, source_observations=observations)
        index = build_semantic_index(manifest, source_observations=observations)
        calls = [ref for ref in index["references"] if ref["kind"] == "call" and ref["parts"] == ["save"]]
        self.assertEqual(len(calls), 1)
        self.assertNotEqual(calls[0]["resolution"], "resolved")


if __name__ == "__main__":
    unittest.main()
