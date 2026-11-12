"""System map of the fixture in benchmarks/flow-model: format, verification, record."""

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import system_map  # noqa: E402

PRESENT = {"pagamenti e abbonamenti", "esercizio"}
TEST_MAP = {
    "nodes": [
        {"name": "Cliente", "type": "attore", "position": "external", "evidence": ["web/checkout.ts"]},
        {"name": "Checkout", "type": "schermata", "members": ["web/checkout.ts"]},
        {"name": "Badge pagamento", "type": "schermata", "members": ["web/badge.ts"]},
        {"name": "API pagamenti", "type": "servizio o API", "members": ["server/payments.py", "server/gateway.py"],
         "on": ["Server shop"]},
        {"name": "Pagamento", "type": "entità", "members": ["store:db/payments", "store:web state/payment"]},
        {"name": "card payment provider", "type": "gateway", "position": "external", "evidence": ["server/gateway.py"]},
        {"name": "Riprova", "type": "funzionalità", "members": ["server/jobs.py"]},
        {"name": "Server shop", "type": "dispositivo", "position": "external", "evidence": ["server/http.py"]},
        {"name": "Fantasma", "type": "schermata", "members": ["web/nope.ts"]},
        {"name": "Refuso", "type": "entità", "members": ["store:db/paymnts"]},
    ],
    "flows": [
        {"name": "Pagare un ordine", "area": "pagamenti e abbonamenti", "types": ["funzionale"],
         "nodes": ["Cliente", "Checkout", "Badge pagamento", "API pagamenti", "Pagamento", "card payment provider"],
         "arrows": [
             {"from": "Cliente", "to": "Checkout", "data": "clic su Paga", "kind": "attiva", "cite": "web/checkout.ts:22"},
             {"from": "Checkout", "to": "API pagamenti", "data": "ordine da pagare"},
             {"from": "API pagamenti", "to": "Pagamento", "data": "esito dell'addebito"},
             {"from": "Pagamento", "to": "Badge pagamento", "data": "stato del pagamento"},
             {"from": "Checkout", "to": "Badge pagamento", "data": "stato del pagamento"},
             {"from": "API pagamenti", "to": "card payment provider", "data": "importo", "kind": "usa",
              "cite": "server/gateway.py:1"},
             {"from": "Badge pagamento", "to": "API pagamenti", "data": "richiesta di stato"},
         ]},
        {"name": "Riprova dei pagamenti", "area": "esercizio", "types": ["operativo"], "nodes": ["Pagamento", "Riprova"],
         "arrows": [{"from": "Pagamento", "to": "Riprova", "data": "pagamenti rifiutati"}]},
    ],
    "areas": [{"name": area, "present": area in PRESENT} for area in system_map.AREAS],
}


def changed(change) -> dict:
    value = copy.deepcopy(TEST_MAP)
    change(value)
    return value


def node(value, name) -> dict:
    return next(n for n in value["nodes"] if n["name"] == name)


class ValidateTests(unittest.TestCase):
    def refused(self, change, field):
        with self.assertRaisesRegex(ValueError, field):
            system_map.validate(changed(change))

    def test_the_test_map_is_valid(self):
        value = system_map.validate(copy.deepcopy(TEST_MAP))
        self.assertEqual(sorted(value), ["areas", "flows", "nodes", "schema"])
        self.assertEqual(value["schema"], system_map.SCHEMA)
        self.assertEqual((node(value, "Checkout")["position"], node(value, "Cliente")["members"]), ("internal", []))
        self.assertIn("entità", system_map.NODE_TYPES)

    def test_a_node_type_out_of_the_list(self):
        self.refused(lambda v: node(v, "Checkout").update(type="pagina"), "type")

    def test_two_names_equal_but_for_case_and_accents(self):
        self.refused(lambda v: node(v, "Riprova").update(name="pagaménto"), "name")

    def test_members_belong_to_internal_nodes_only(self):
        self.refused(lambda v: node(v, "Checkout").update(members=[]), "members")
        self.refused(lambda v: node(v, "Cliente").update(members=["web/checkout.ts"]), "members")

    def test_a_node_without_code_cites_its_evidence(self):
        self.refused(lambda v: node(v, "Server shop").update(evidence=[]), "evidence")

    def test_an_unseen_node_says_where_it_is(self):
        self.refused(lambda v: node(v, "Server shop").update(position="unseen", evidence=[]), "where")
        system_map.validate(changed(lambda v: node(v, "Server shop").update(position="unseen", evidence=[], where="infra repo")))

    def test_references_name_nodes_of_the_map(self):
        self.refused(lambda v: v["flows"][1]["nodes"].append("Magazzino"), "nodes")
        self.refused(lambda v: v["flows"][1]["arrows"][0].update(to="Checkout"), "to")
        self.refused(lambda v: node(v, "API pagamenti").update(on=["Magazzino"]), "on")

    def test_an_arrow_says_what_passes_and_what_it_asserts(self):
        self.refused(lambda v: v["flows"][1]["arrows"][0].pop("data"), "data")
        self.refused(lambda v: v["flows"][1]["arrows"][0].update(kind="spedisce"), "kind")

    def test_a_flow_has_known_types(self):
        self.refused(lambda v: v["flows"][1].update(types=["notturno"]), "types")

    def test_every_area_is_declared_without_scope(self):
        self.refused(lambda v: v["areas"].pop(0), "areas")

    def test_with_scope_a_flow_stays_inside_it(self):
        def scoped(v):
            v["scope"] = ["pagamenti e abbonamenti"]
            v["areas"] = [{"name": "pagamenti e abbonamenti", "present": True}]
        system_map.validate(changed(lambda v: (scoped(v), v["flows"].pop())))
        self.refused(scoped, "area")

    def test_a_flow_sits_in_a_present_area(self):
        self.refused(lambda v: v["flows"][1].update(area="comunicazioni"), "area")

    def test_an_unknown_field(self):
        self.refused(lambda v: node(v, "Checkout").update(owner="team"), "owner")
        self.refused(lambda v: v["flows"][0]["arrows"][0].update(weight=1), "weight")
        self.refused(lambda v: v.update(version=2), "version")


if __name__ == "__main__":
    unittest.main()
