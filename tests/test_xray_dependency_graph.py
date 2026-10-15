"""Graph diagnostics on hand-checked import relationships, without source I/O."""

import math
from pathlib import Path
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))

import dependency_graph


class DependencyGraphTests(unittest.TestCase):
    def setUp(self):
        self.engine = dependency_graph

    def test_cycles_keep_self_edges_and_deduplicate_mutual_edges(self):
        result = self.engine.dependency_graph_metrics({
            "isolated": [], "b": ["a", "a"], "self": ["self"], "a": ["b"],
        })
        self.assertEqual(result["nodes"], ["a", "b", "isolated", "self"])
        self.assertEqual(result["edges"], [["a", "b"], ["b", "a"], ["self", "self"]])
        self.assertEqual(result["import_cycles"], [["a", "b"], ["self"]])

    def test_targets_without_outgoing_records_remain_nodes(self):
        result = self.engine.dependency_graph_metrics({"app": ["removed"], "unused": []})
        self.assertEqual(result["nodes"], ["app", "removed", "unused"])
        self.assertEqual(result["edges"], [["app", "removed"]])
        self.assertEqual(result["import_cycles"], [])

    def test_dag_cross_edge_is_not_mistaken_for_a_cycle(self):
        result = self.engine.dependency_graph_metrics({
            "a": ["b", "c"], "b": ["c"], "c": [],
        })
        self.assertEqual(result["import_cycles"], [])

    def test_deep_chain_and_cycle_do_not_use_python_recursion(self):
        graph = {str(index): [str(index + 1)] for index in range(3500)}
        graph["3500"] = ["3499"]
        result = self.engine.dependency_graph_metrics(graph)
        self.assertEqual(len(result["nodes"]), 3501)
        self.assertEqual(len(result["edges"]), 3501)
        self.assertEqual(result["import_cycles"], [["3499", "3500"]])

    def test_pagerank_follows_imports_and_corrects_dangling_mass(self):
        result = self.engine.dependency_graph_metrics({"app": ["core"], "core": []})
        self.assertTrue(result["pagerank_converged"])
        self.assertGreater(result["pagerank_iterations"], 0)
        self.assertAlmostEqual(result["pagerank_damping"], 0.85)
        self.assertAlmostEqual(sum(result["pagerank"].values()), 1.0, places=11)
        # Solving p(app) = .075 + .425*p(core), with unit total mass.
        self.assertAlmostEqual(result["pagerank"]["app"], 20 / 57, places=8)
        self.assertAlmostEqual(result["pagerank"]["core"], 37 / 57, places=8)

    def test_isolated_nodes_receive_equal_finite_rank(self):
        result = self.engine.dependency_graph_metrics({"c": [], "b": [], "a": []})
        self.assertTrue(result["pagerank_converged"])
        for value in result["pagerank"].values():
            self.assertTrue(math.isfinite(value))
            self.assertAlmostEqual(value, 1 / 3)

    def test_empty_graph_is_an_explicit_converged_empty_result(self):
        result = self.engine.dependency_graph_metrics({})
        self.assertEqual(result["nodes"], [])
        self.assertEqual(result["edges"], [])
        self.assertEqual(result["import_cycles"], [])
        self.assertEqual(result["pagerank"], {})
        self.assertTrue(result["pagerank_converged"])
        self.assertEqual(result["pagerank_iterations"], 0)

    def test_results_are_deterministic_across_input_order_and_duplicates(self):
        left = {"b": ["c", "a", "a"], "a": ["c"], "c": ["a"], "free": []}
        right = {"free": [], "c": ["a"], "a": ["c"], "b": ["a", "c"]}
        self.assertEqual(self.engine.dependency_graph_metrics(left), self.engine.dependency_graph_metrics(right))

    def test_iteration_limit_reports_nonconvergence(self):
        result = self.engine.dependency_graph_metrics({"app": ["core"], "core": []}, max_iterations=1)
        self.assertFalse(result["pagerank_converged"])
        self.assertEqual(result["pagerank_iterations"], 1)
        self.assertEqual(result["pagerank_max_iterations"], 1)
        self.assertAlmostEqual(sum(result["pagerank"].values()), 1.0)

    def test_invalid_pagerank_controls_are_rejected(self):
        for name, values in {
            "damping": [-0.1, 0, 1, float("nan"), float("inf"), True, "0.85"],
            "tolerance": [0, -1, float("nan"), float("inf"), True, "0.1"],
            "max_iterations": [0, -1, 1.5, True, "2"],
        }.items():
            for value in values:
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    self.engine.dependency_graph_metrics({"app": ["core"]}, **{name: value})

    def test_invalid_graph_shapes_do_not_become_character_edges(self):
        for graph in [None, [], {"app": "core"}, {"app": None}, {1: ["core"]}, {"app": [1]}]:
            with self.subTest(graph=graph), self.assertRaises(ValueError):
                self.engine.dependency_graph_metrics(graph)

    def test_transitive_diamond_has_shortest_paths_and_deterministic_witnesses(self):
        result = self.engine.transitive_importers({
            "core": ["right", "left", "left"], "right": ["app"], "left": ["app"],
            "unrelated": ["other"],
        }, ["core"])
        self.assertEqual(result, [
            {"file": "left", "depth": 1, "via": "core", "seed": "core"},
            {"file": "right", "depth": 1, "via": "core", "seed": "core"},
            {"file": "app", "depth": 2, "via": "left", "seed": "core"},
        ])

    def test_multiple_seeds_are_excluded_and_nearest_seed_wins(self):
        result = self.engine.transitive_importers({
            "a": ["b", "long"], "b": ["end"], "long": ["end"], "end": ["tail"],
        }, (value for value in ["b", "a", "b"]))
        self.assertEqual(result, [
            {"file": "end", "depth": 1, "via": "b", "seed": "b"},
            {"file": "long", "depth": 1, "via": "a", "seed": "a"},
            {"file": "tail", "depth": 2, "via": "end", "seed": "b"},
        ])

    def test_transitive_cycles_terminate_and_exclude_seed(self):
        self.assertEqual(self.engine.transitive_importers({
            "core": ["core", "service"], "service": ["core", "route"], "route": ["service"],
        }, ["core"]), [
            {"file": "service", "depth": 1, "via": "core", "seed": "core"},
            {"file": "route", "depth": 2, "via": "service", "seed": "core"},
        ])

    def test_removed_seed_has_incoming_importers_without_invented_outgoing_edges(self):
        index = {"removed": ["survivor"], "survivor": ["app"], "other": ["elsewhere"]}
        self.assertEqual(self.engine.transitive_importers(index, ["removed"]), [
            {"file": "survivor", "depth": 1, "via": "removed", "seed": "removed"},
            {"file": "app", "depth": 2, "via": "survivor", "seed": "removed"},
        ])
        self.assertEqual(self.engine.transitive_importers(index, ["missing"]), [])
        self.assertEqual(self.engine.transitive_importers(index, []), [])

    def test_deep_reverse_chain_returns_depth_without_recursion(self):
        index = {str(number): [str(number + 1)] for number in range(3500)}
        result = self.engine.transitive_importers(index, ["0"])
        self.assertEqual(len(result), 3500)
        self.assertEqual(result[-1]["depth"], 3500)
        self.assertEqual(result[-1], {"file": "3500", "depth": 3500, "via": "3499", "seed": "0"})
        self.assertTrue(all(set(row) == {"file", "depth", "via", "seed"} for row in result))

    def test_reverse_index_and_seed_shapes_are_validated(self):
        for index, seeds in [({"core": "app"}, ["core"]), ({"core": [1]}, ["core"]),
                             ({}, "core"), ({}, [1]), ({}, None)]:
            with self.subTest(index=index, seeds=seeds), self.assertRaises(ValueError):
                self.engine.transitive_importers(index, seeds)


if __name__ == "__main__":
    unittest.main()
