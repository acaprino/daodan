"""Levels of a flow of the system map, on the flow-model fixture."""

import copy
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_codebase_map_system_map import TEST_MAP, fixture  # noqa: E402
import flows  # noqa: E402
import system_levels  # noqa: E402
import system_map  # noqa: E402

PAY = "Pagare un ordine"


def names(view) -> set[str]:
    return {n["name"] for n in view["nodes"]}


def arrow_states(view) -> set[tuple]:
    return {(a["from"], a["to"], a["status"]) for a in view["arrows"]}


class LevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture(cls)
        system_map.record(cls.manifest, cls.rules, TEST_MAP)
        cls.m = system_map.load(cls.manifest, cls.rules)
        cls.links = flows.cached_links(cls.manifest, cls.rules)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def view(self, levels, flow=PAY, links=None):
        return system_levels.view(self.m, flow, levels, links)

    def test_each_level_shows_its_node_types(self):
        self.assertEqual(names(self.view(["persone"])), {"Cliente", "Checkout", "Badge pagamento"})
        self.assertEqual(names(self.view(["dati"])), {"Pagamento"})
        self.assertEqual(self.view(["persone"], "pagare-un-ordine"), self.view(["persone"]))

    def test_an_arrow_keeps_its_state_and_proof(self):
        people = self.view(["persone"])
        self.assertIn(("Checkout", "Badge pagamento", "proved"), arrow_states(people))
        self.assertIn(("Cliente", "Checkout", "declared"), arrow_states(people))
        kept = next(a for a in people["arrows"] if (a["from"], a["to"]) == ("Checkout", "Badge pagamento"))
        self.assertEqual(kept["via"], ["web state/payment"])
        self.assertTrue(kept["proof"])

    def test_infrastructure_puts_a_node_on_what_it_runs_on(self):
        infra = self.view(["infrastruttura"])
        self.assertIn(("Server shop", "card payment provider", "declared"), arrow_states(infra))
        self.assertIn("API pagamenti", next(a for a in infra["arrows"] if a["from"] == "Server shop")["through"])

    def test_a_refused_step_is_a_gap_never_an_arrow(self):
        broken = copy.deepcopy(self.m)
        flow = next(f for f in broken["flows"] if f["name"] == PAY)
        for arrow in flow["arrows"]:
            if (arrow["from"], arrow["to"]) in {("API pagamenti", "card payment provider"), ("Cliente", "Checkout")}:
                arrow["status"] = "refused"
        infra = system_levels.view(broken, PAY, ["infrastruttura"])
        self.assertEqual(infra["arrows"], [])
        self.assertIn("refused", infra["gaps"][0]["reason"])
        people = system_levels.view(broken, PAY, ["persone"])
        self.assertNotIn(("Cliente", "Checkout"), {(a["from"], a["to"]) for a in people["arrows"]})
        self.assertIn(("Cliente", "Checkout"), {(g["from"], g["to"]) for g in people["gaps"]})

    def test_a_path_budget_that_runs_out_is_a_gap(self):
        budget = system_levels.MAX_PATHS
        system_levels.MAX_PATHS = 1
        self.addCleanup(setattr, system_levels, "MAX_PATHS", budget)
        people = self.view(["persone"])
        self.assertTrue(any("budget" in g["reason"] for g in people["gaps"]))

    def test_code_shows_files_from_the_links(self):
        code = self.view(["codice"], links=self.links)
        self.assertIn("server/payments.py", names(code))
        self.assertIn(("server/payments.py", "server/gateway.py", "proved"), arrow_states(code))
        self.assertFalse(any("::" in name for name in names(code)))
        with self.assertRaisesRegex(ValueError, "links"):
            self.view(["codice"])

    def test_two_copies_of_an_entity_are_a_gap_not_an_arrow(self):
        mixed = self.view(["persone", "funzioni"])
        self.assertNotIn(("API pagamenti", "Badge pagamento"), {(a["from"], a["to"]) for a in mixed["arrows"]})
        gap = next(g for g in mixed["gaps"] if (g["from"], g["to"]) == ("API pagamenti", "Badge pagamento"))
        self.assertIn("db/payments", gap["reason"])
        self.assertIn("web state/payment", gap["reason"])
        self.assertEqual(gap["through"], ["Pagamento"])

    def test_a_flow_exists_at_the_levels_where_it_has_nodes(self):
        self.assertEqual(self.view(["persone"], "Riprova dei pagamenti")["absent"], ["persone"])
        everything = self.view(list(system_levels.LEVELS), links=self.links)
        self.assertTrue(everything["nodes"][0]["also"])
        badge = next(n for n in everything["nodes"] if n["name"] == "Badge pagamento")
        self.assertEqual(badge["also"], {"codice": ["web/badge.ts"]})
        with self.assertRaisesRegex(ValueError, "level"):
            self.view(["fisico"])

    def test_inside_a_node(self):
        opened = system_levels.inside(self.m, "Pagamento", self.links)
        self.assertEqual({r["id"] for r in opened["members"]}, {"store:db/payments", "store:web state/payment"})
        self.assertEqual(opened["relations"], [])
        self.assertIn("db/payments", opened["gaps"][0]["reason"])
        written = next(r for r in opened["members"] if r["id"] == "store:db/payments")
        self.assertEqual(written["writes"], ["server/payments.py::charge_order"])
        self.assertEqual(system_levels.inside(self.m, "card payment provider")["detail"], "none")
        checkout = system_levels.inside(self.m, "checkout", self.links)
        self.assertEqual((checkout["detail"], [r["id"] for r in checkout["members"]]), ("available", ["web/checkout.ts"]))
        self.assertTrue(checkout["relations"])


if __name__ == "__main__":
    unittest.main()
