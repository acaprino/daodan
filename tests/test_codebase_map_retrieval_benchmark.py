"""Mechanical guards for the retrieval benchmark's scoring, not model quality."""
import importlib.util
import json
import unittest
from pathlib import Path

HARNESS = (Path(__file__).resolve().parents[1]
           / "evals/codebase-map/retrieval-benchmark/run_benchmark.py")
SPEC = importlib.util.spec_from_file_location("retrieval_benchmark", HARNESS)
BENCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCH)


class RetrievalBenchmarkTests(unittest.TestCase):
    def test_subtokens_split_code_identifiers_and_paths(self):
        self.assertEqual(
            BENCH.subtokens("semantic_store.buildEditImpact pkg/a.py"),
            ["semantic", "store", "build", "edit", "impact", "pkg", "py"])

    def test_metrics_reward_expected_symbols_and_dependencies(self):
        query = {"expected": ["a::f"], "dependencies": ["b::g"]}
        values = BENCH.metrics_for(["x::z", "a::f"], ["x::z", "b::g"], query)

        self.assertEqual(values["symbol_recall_at_20"], 1.0)
        self.assertEqual(values["mrr_at_10"], 0.5)
        self.assertGreater(values["ndcg_at_10"], 0.0)
        self.assertEqual(values["dependency_recall_at_15"], 1.0)

    def test_anchors_ignore_one_letter_css_symbols(self):
        docs = [{"id": "x.css::a", "file": "x.css", "name": "a", "short": "a"},
                {"id": "x.py::build_edit_impact", "file": "x.py",
                 "name": "build_edit_impact", "short": "build_edit_impact"}]

        self.assertEqual(BENCH.anchors(docs, "find a build_edit_impact"), ["x.py::build_edit_impact"])

    def test_gold_set_shape_and_categories(self):
        payload = json.loads((HARNESS.parent / "queries.json").read_text(encoding="utf-8"))
        queries = payload["queries"]

        self.assertGreaterEqual(len(queries), 30)
        self.assertEqual({item["kind"] for item in queries},
                         {"exact", "traceback", "nl-en", "nl-it", "code"})
        self.assertTrue(all(item["expected"] for item in queries))
        self.assertEqual(len({item["id"] for item in queries}), len(queries))


if __name__ == "__main__":
    unittest.main()
