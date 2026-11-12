"""score.py of benchmarks/system-map on two minimal maps."""

import importlib.util
import unittest
from pathlib import Path

SCORE = Path(__file__).resolve().parents[1] / "benchmarks/system-map/score.py"
spec = importlib.util.spec_from_file_location("system_map_score", SCORE)
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

EXPECTED = {"nodes": [{"name": "Paywall", "type": "schermata", "files": ["app/Paywall.tsx", "app/Plans.tsx"]},
                      {"name": "API acquisti", "type": "servizio o API", "files": ["api/checkout.py", "api/webhook.py"]},
                      {"name": "Stripe", "type": "gateway", "files": ["api/stripe_client.py"]}],
            "flows": [{"name": "Pagamento", "nodes": ["Paywall", "API acquisti", "Stripe"]}]}
PROPOSED = {"nodes": [{"name": "Schermata dei piani", "type": "schermata", "files": ["app/Paywall.tsx"], "evidence": []},
                      {"name": "Pagamenti", "type": "servizio o API", "files": ["api/checkout.py", "api/webhook.py",
                                                                                "api/other.py"], "evidence": []},
                      {"name": "Stripe", "type": "gateway", "files": [], "evidence": ["api/stripe_client.py"]}],
            "flows": [{"name": "Pagare", "nodes": ["Schermata dei piani", "Pagamenti"],
                       "arrows": [{"status": "proved"}, {"status": "declared"}]}],
            "refused_arrows": 1,
            "coverage": {"entries": {"in": 2, "of": 4}, "stores": {"in": 1, "of": 1}, "routes": {"in": 1, "of": 2}}}


class ScoreTests(unittest.TestCase):
    def test_nodes_by_files_flows_by_nodes(self):
        result = score.score_map(PROPOSED, EXPECTED)
        self.assertEqual(result["nodes"], {"found": 3, "of": 3, "missing": []})   # half the files, or more
        self.assertEqual(result["flows"], {"found": 1, "of": 1, "missing": []})   # two thirds of the nodes
        self.assertEqual(result["arrows"], {"proved": 1, "declared": 1, "refused": 1, "refused_share": 0.333})
        self.assertEqual(result["coverage"]["entries"], {"in": 2, "of": 4})

    def test_a_node_with_less_than_half_the_files_is_missing(self):
        thin = {**PROPOSED, "nodes": [{**PROPOSED["nodes"][1], "files": ["api/checkout.py", "api/a.py", "api/b.py"]}]}
        self.assertIn("API acquisti", score.score_map(thin, EXPECTED)["nodes"]["missing"])

    def test_an_entity_is_found_by_its_store_keys(self):
        expected = {"nodes": [{"name": "Abbonamento", "type": "entità", "members": ["store:mongo/subscriptions"]}],
                    "flows": []}
        proposed = {"nodes": [{"name": "Piano", "type": "entità", "members": ["store:mongo/subscriptions"],
                               "files": [], "evidence": []}], "flows": []}
        self.assertEqual(score.score_map(proposed, expected)["nodes"]["found"], 1)

    def test_a_node_without_code_is_found_by_one_cited_file_in_the_same_position(self):
        expected = {"nodes": [{"name": "Stripe", "type": "gateway", "position": "external",
                               "evidence": ["api/stripe_client.py", "api/webhook.py", "requirements.txt"]},
                              {"name": "Landing", "type": "schermata", "position": "unseen", "where": "landing-app"}],
                    "flows": []}
        cited = {"name": "Pagamenti con carta", "type": "servizio o API", "position": "external", "files": [],
                 "evidence": ["requirements.txt#stripe"]}
        unseen = {"name": "Sito", "type": "schermata", "position": "unseen", "files": [], "evidence": []}
        inside = {"name": "Client", "type": "servizio o API", "files": ["api/stripe_client.py"], "evidence": []}
        self.assertEqual(score.score_map({"nodes": [cited, unseen], "flows": []}, expected)["nodes"],
                         {"found": 2, "of": 2, "missing": []})
        self.assertEqual(score.score_map({"nodes": [inside], "flows": []}, expected)["nodes"]["missing"],
                         ["Stripe", "Landing"])

    def test_externals_recall_and_wrong(self):
        result = score.score_externals({"externals": [{"id": "stripe"}, {"id": "react"}, {"id": "redis"}]},
                                       {"externals": ["stripe", "react", "fastapi"]})
        self.assertEqual(result, {"recall": 0.667, "found": ["react", "stripe"], "missed": ["fastapi"], "wrong": ["redis"]})

    def test_externals_by_source_and_used_but_not_named(self):
        brief = {"externals": [{"id": "stripe", "from": ["registry"]}, {"id": "react", "from": ["stack-analyser"]},
                               {"id": "eslint", "from": ["registry", "stack-analyser"]},
                               {"id": "billing", "from": ["modules"]}]}
        expected = {"externals": ["stripe", "react"], "also": ["eslint"]}
        self.assertEqual(score.score_externals(brief, expected, "registry"),
                         {"recall": 0.5, "found": ["stripe"], "missed": ["react"], "wrong": []})
        self.assertEqual(score.score_externals(brief, expected, "stack-analyser")["found"], ["react"])
        self.assertEqual(score.score_externals(brief, expected, "both"),
                         {"recall": 1.0, "found": ["react", "stripe"], "missed": [], "wrong": []})
        self.assertEqual(score.score_externals(brief, expected)["wrong"], ["billing"])


if __name__ == "__main__":
    unittest.main()
