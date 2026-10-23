"""Persisted semantic queries match the conservative in-memory reference."""
from pathlib import Path
import copy
import importlib.util
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import snapshot
import source_reader
from resolution import LEXICAL_RESOLVER
from snapshot_store import open_snapshot


class StorageQueryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-storage-query-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / "a.py").write_text("def target():\n    return 7\n", encoding="utf-8")
        (self.root / "b.py").write_text("from a import target\n\ndef caller():\n    return target()\n", encoding="utf-8")
        (self.root / "unused.py").write_text("VALUE = 1\n", encoding="utf-8")

    def api(self):
        self.assertIsNotNone(importlib.util.find_spec("semantic_store"), "persistent semantic query owner is required")

    def write(self, format="sqlite"):
        out = self.root / ".codebase-map" / ("manifest." + format)
        snapshot.write_snapshot(self.root, out, format=format)
        return out

    def assert_graph_parity(self, actual, reference, *, format="sqlite", enriched=True):
        """Preserve every lexical field and verify the additive engine-view contract."""
        expected = copy.deepcopy(reference)
        sqlite = format == "sqlite"
        expected["edge_view"] = {
            "schema": "daodan/edge-view/v1", "version": 1,
            "profile": {"lexical_resolver": LEXICAL_RESOLVER, "engine": None,
                        "engine_available": False, **({"engine_store": None} if sqlite else {})},
            "coverage": {
                "status": "missing_store" if sqlite else "unsupported_format",
                "sampled": False, "population": 0, "selected": 0, "asked": 0,
                "stride": 1, "confirmed": 0, "candidates": 0,
                "no_edges_reason": None if sqlite else "json-manifest",
            },
            "gaps": [] if sqlite else ["JSON snapshot holds no semantic reference table"],
            "candidates": {"items": [], "total": 0, "truncated": 0},
            "conflicts": {"items": [], "total": 0, "truncated": 0},
        }
        if sqlite and enriched:
            for call in expected["calls"]:
                resolved = call["resolution"] == "resolved"
                call.update(confidence="confirmed" if resolved else None,
                            provenance=[LEXICAL_RESOLVER] if resolved else [],
                            lexical_resolution=call["resolution"],
                            lexical_target_id=call["target_id"], lexical_reason=call["reason"],
                            target_kind="concrete" if resolved else None)
        self.assertEqual(actual, expected)

    def test_graph_parity_across_formats(self):
        self.api()
        for format in ("sqlite", "json"):
            with self.subTest(format=format), open_snapshot(self.write(format)) as store:
                reference = {**store.metadata, "files": dict(store.iter_files())}
                expected = source_reader.graph_packet(reference, ["b.py"], hops=2, limit=2)
                actual = source_reader.graph_packet(store, ["b.py"], hops=2, limit=2)
                self.assert_graph_parity(actual, expected, format=format)

    def test_queries_do_not_call_global_semantic_builder(self):
        self.api()
        import semantic_index
        out = self.write()
        with open_snapshot(out) as store:
            with mock.patch.object(semantic_index, "build_semantic_index",
                                   side_effect=AssertionError("global semantic heap rebuilt")):
                packet = source_reader.graph_packet(store, ["b.py"], hops=1, limit=1)
            self.assertGreater(packet["totals"]["calls"], 0)

    def test_stale_non_seed_source_is_refused(self):
        self.api()
        out = self.write()
        (self.root / "unused.py").write_text("VALUE = 2\n", encoding="utf-8")
        with open_snapshot(out) as store:
            with self.assertRaisesRegex(ValueError, "source|refresh|identity"):
                source_reader.graph_packet(store, ["b.py"])

    def test_outline_and_read_use_the_same_store(self):
        self.api()
        out = self.write()
        with open_snapshot(out) as store:
            reference = {**store.metadata, "files": dict(store.iter_files())}
            self.assertEqual(source_reader.outline_manifest(store, pattern="target", limit=2),
                             source_reader.outline_manifest(reference, pattern="target", limit=2))
            requests = [{"path":"b.py", "symbols":["caller"]}]
            self.assertEqual(source_reader.read_packet(store, requests),
                             source_reader.read_packet(reference, requests))

    def test_unresolved_shadowing_is_preserved(self):
        self.api()
        (self.root / "b.py").write_text("from a import target\n\ndef caller(target):\n    return target()\n")
        with open_snapshot(self.write()) as store:
            reference = {**store.metadata, "files": dict(store.iter_files())}
            self.assert_graph_parity(source_reader.graph_packet(store, ["b.py"]),
                                     source_reader.graph_packet(reference, ["b.py"]))

    def test_conservative_bindings_and_unicode_match_reference(self):
        original = snapshot.file_entry
        fixtures = [
            ("def target(): pass\ndef target(): pass\n", "from a import target\ntarget()\n", False, "unresolved"),
            ("def target(): pass\n", "from a import target\ntarget()\n", True, "unresolved"),
            ("def café(): pass\n", "from a import café\ncafé()\n", False, "resolved"),
        ]
        for source, caller, type_only, resolution in fixtures:
            with self.subTest(source=source, type_only=type_only):
                (self.root / "a.py").write_text(source, encoding="utf-8")
                (self.root / "b.py").write_text(caller, encoding="utf-8")
                def entry(path, *args, **kwargs):
                    value = original(path, *args, **kwargs)
                    if path.name == "b.py" and type_only:
                        value["semantic"]["imports"][0]["type_only"] = True
                    return value
                with mock.patch.object(snapshot, "file_entry", side_effect=entry):
                    out = self.write()
                with open_snapshot(out) as store:
                    reference = {**store.metadata, "files": dict(store.iter_files())}
                    actual = source_reader.graph_packet(store, ["b.py"])
                    self.assert_graph_parity(actual, source_reader.graph_packet(reference, ["b.py"]))
                    self.assertEqual(len(actual["calls"]), 1)
                    self.assertEqual(actual["calls"][0]["resolution"], resolution)
                    self.assertEqual(actual["coverage"]["counts"], {"ast": 3})

    def test_reused_ast_does_not_reuse_resolved_edges(self):
        self.api()
        first = self.write()
        (self.root / "a.py").write_text("def replacement():\n    return 8\n")
        second = self.root / ".codebase-map/second.sqlite"
        with open_snapshot(first) as previous:
            result = snapshot.write_snapshot(self.root, second, previous=previous)
        self.assertEqual(result["metrics"]["cache_hits"], 2)
        with open_snapshot(second) as store:
            reference = {**store.metadata, "files": dict(store.iter_files())}
            actual = source_reader.graph_packet(store, ["b.py"])
            self.assert_graph_parity(actual, source_reader.graph_packet(reference, ["b.py"]))
            self.assertEqual(actual["calls"][0]["resolution"], "unresolved")

    def test_new_git_exclusion_rebuilds_only_derived_bindings(self):
        self.api()
        import subprocess
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        out = self.write()
        before = out.read_bytes()
        (self.root / ".gitignore").write_text("a.py\n")
        with open_snapshot(out) as store:
            reference = {**store.metadata, "files": dict(store.iter_files())}
            actual = source_reader.graph_packet(store, ["b.py"])
            # Excluding the target rebuilds lexical bindings; an old view cannot
            # attach metadata from its now-disallowed target to the new call.
            self.assert_graph_parity(actual, source_reader.graph_packet(reference, ["b.py"]),
                                     enriched=False)
            self.assertEqual(actual["calls"][0]["resolution"], "unresolved")
        self.assertEqual(out.read_bytes(), before)

    def test_persistent_fact_tampering_is_not_hidden_by_cache(self):
        self.api()
        from contextlib import closing
        import sqlite3
        from snapshot_store import _pack, _unpack
        out = self.write()
        with closing(sqlite3.connect(out)) as database:
            row = database.execute("SELECT ordinal,payload FROM facts WHERE file='b.py' AND kind='references' LIMIT 1").fetchone()
            item = _unpack(row[1])
            item["reason"] = "tampered"
            database.execute("UPDATE facts SET payload=? WHERE file='b.py' AND kind='references' AND ordinal=?", (_pack(item), row[0]))
            database.commit()
        with open_snapshot(out) as store:
            with self.assertRaisesRegex(ValueError, "facts changed|refresh"):
                source_reader.graph_packet(store, ["b.py"])

    def test_analysis_reuses_snapshot_without_rebuilding_inventory(self):
        self.api()
        import analyze_file
        import inspect
        self.assertIn("snapshot_path", inspect.signature(analyze_file.analyze_single_file).parameters)
        out = self.write()
        with mock.patch.object(snapshot, "build_manifest", side_effect=AssertionError("global manifest rebuilt")):
            with mock.patch.object(snapshot, "write_snapshot", side_effect=AssertionError("snapshot rebuilt")):
                result = analyze_file.analyze_single_file(self.root / "a.py", project_root=self.root, snapshot_path=out)
        self.assertEqual(result["imported_by_count"], 1)
        self.assertEqual(result["semantic_analysis"]["counts"]["incoming_calls"], 1)

    def test_bound_analysis_checks_perimeter_before_opening_source(self):
        import analyze_file
        import subprocess
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        out = self.write()
        (self.root / ".gitignore").write_text("a.py\n")
        original = Path.read_bytes
        def read(path):
            if path.resolve() == (self.root / "a.py").resolve():
                raise AssertionError("excluded source opened before perimeter check")
            return original(path)
        with mock.patch.object(Path, "read_bytes", read):
            with self.assertRaisesRegex(ValueError, "perimeter|excluded|ignored"):
                analyze_file.analyze_single_file(self.root / "a.py", project_root=self.root, snapshot_path=out)

    def test_usage_store_matches_legacy_reference_and_limits_are_explicit(self):
        self.api()
        import dataclasses
        import inspect
        import usage_finder
        self.assertIn("limit", inspect.signature(usage_finder.find_all_usages_batch).parameters)
        for number in range(12):
            (self.root / f"use{number}.py").write_text("from a import target\n\ndef invoke():\n    return target()\n")
        with open_snapshot(self.write()) as store:
            reference = {**store.metadata, "files": dict(store.iter_files())}
            expected = usage_finder.find_all_usages_batch(["target"], self.root / "a.py", self.root, manifest=reference)["target"]
            actual = usage_finder.find_all_usages_batch(["target"], self.root / "a.py", self.root, manifest=store, limit=2)["target"]
            self.assertEqual(actual.total_count, len(expected.usages))
            self.assertTrue(actual.truncated)
            self.assertEqual([dataclasses.asdict(row) for row in actual.usages],
                             [dataclasses.asdict(row) for row in expected.usages[:2]])
            self.assertEqual(actual.resolved_count, expected.resolved_count)
            self.assertEqual(actual.ast_candidate_count, expected.ast_candidate_count)
            self.assertEqual(actual.lexical_candidate_count, expected.lexical_candidate_count)
            self.assertEqual(actual.importing_modules, expected.importing_modules)

    def test_disk_graph_metrics_match_cycles_and_pagerank(self):
        self.api()
        import sqlite3
        from contextlib import closing
        from dependency_graph import dependency_graph_metrics
        from store_graph_metrics import build_metrics, metric_metadata
        graph = {"a":["b","a"],"b":["c"],"c":["a"],"d":[],"\u00e9":["d"]}
        expected = dependency_graph_metrics(graph)
        with closing(sqlite3.connect(self.root / "diagnostics.sqlite")) as db:
            db.execute("CREATE TABLE nodes(file TEXT PRIMARY KEY)")
            db.execute("CREATE TABLE links(source TEXT,target TEXT)")
            db.executemany("INSERT INTO nodes VALUES(?)", ((node,) for node in graph))
            db.executemany("INSERT INTO links VALUES(?,?)", ((source,target) for source, targets in graph.items() for target in targets))
            build_metrics(db, prefix="sem", temporary=False, nodes="SELECT file FROM nodes", edges="SELECT source,target FROM links")
            self.assertEqual(dict(db.execute("SELECT node,score FROM sem_rank")), expected["pagerank"])
            cycles = [[row[0] for row in db.execute("SELECT node FROM sem_cycles WHERE component=? ORDER BY ordinal",(component,))]
                      for (component,) in db.execute("SELECT DISTINCT component FROM sem_cycles ORDER BY component")]
            self.assertEqual(cycles, expected["import_cycles"])
            self.assertEqual(metric_metadata(db), {key:value for key,value in expected.items() if key.startswith("pagerank_")})

    def test_large_fan_in_reports_exact_totals(self):
        self.api()
        for number in range(90):
            (self.root / f"caller{number}.py").write_text(
                f"from a import target\n\ndef caller{number}():\n    return target()\n")
        with open_snapshot(self.write()) as store:
            packet = source_reader.graph_packet(store, ["a.py"], hops=1, limit=1)
            self.assertEqual(len(packet["calls"]), 1)
            self.assertEqual(packet["totals"]["calls"], 91)
            self.assertIn("calls", packet["truncated"])


if __name__ == "__main__":
    unittest.main()
