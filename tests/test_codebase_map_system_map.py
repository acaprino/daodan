"""System map of the fixture in benchmarks/flow-model: format, verification, record."""

import copy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codebase-map/skills/map/scripts"
BENCH = ROOT / "benchmarks/flow-model"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import flows  # noqa: E402
import snapshot  # noqa: E402
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


class Fixture(unittest.TestCase):
    """The flow-model fixture as a git project with a snapshot and its links."""

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="system-map-")).resolve()
        cls.project = cls.work / "app"
        shutil.copytree(BENCH / "app", cls.project)
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            subprocess.run(command, cwd=cls.project, check=True, capture_output=True)
        cls.manifest = cls.work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(cls.project), "--out", str(cls.manifest), "--no-engine", "--no-index"])
        cls.rules = flows.load_rules(BENCH / "rules.json")
        cls.links = flows.link_facts(cls.manifest, cls.rules)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)


class VerifyTests(Fixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.check(TEST_MAP)

    @classmethod
    def check(cls, value):
        return system_map.verify(cls.manifest, cls.links, system_map.validate(copy.deepcopy(value)))

    def arrow(self, source, target, report=None):
        return next(a for flow in (report or self.report)["flows"] for a in flow["arrows"]
                    if (a["from"], a["to"]) == (source, target))

    def node(self, name, report=None):
        return next(n for n in (report or self.report)["nodes"] if n["name"] == name)

    def flow(self, name, report=None):
        return next(f for f in (report or self.report)["flows"] if f["name"] == name)

    def with_cliente_arrow(self, **fields):
        def change(v):
            v["flows"][0]["arrows"][0].update(fields)
            for name in [k for k, value in fields.items() if value is None]:
                v["flows"][0]["arrows"][0].pop(name)
        return self.arrow("Cliente", "Checkout", self.check(changed(change)))

    def test_arrows_are_proved_by_the_links(self):
        proved = {(a["from"], a["to"]) for flow in self.report["flows"] for a in flow["arrows"] if a["status"] == "proved"}
        self.assertLessEqual({("Checkout", "API pagamenti"), ("API pagamenti", "Pagamento"), ("Pagamento", "Badge pagamento"),
                              ("Checkout", "Badge pagamento"), ("Pagamento", "Riprova")}, proved)

    def test_a_proved_arrow_asserts_only_what_its_links_say(self):
        self.assertEqual(self.arrow("Checkout", "API pagamenti")["asserts"], ["chiama"])
        written = self.arrow("API pagamenti", "Pagamento")
        self.assertEqual((written["asserts"], written["via"]), (["scrive"], ["db/payments"]))
        self.assertEqual(self.arrow("Pagamento", "Badge pagamento")["via"], ["web state/payment"])
        passed = self.arrow("Checkout", "Badge pagamento")
        self.assertEqual((passed["asserts"], passed["via"]), (["trasferisce"], ["web state/payment"]))
        self.assertEqual(passed["proof"], [
            {"from": "web/checkout.ts::submitPayment", "to": "store:web state/payment", "type": "scrive",
             "site": "web/checkout.ts:14"},
            {"from": "store:web state/payment", "to": "web/badge.ts::renderBadge", "type": "legge",
             "site": "web/badge.ts:4"}])

    def test_an_arrow_with_an_end_without_code_is_declared(self):
        self.assertEqual(self.arrow("Cliente", "Checkout")["status"], "declared")
        self.assertEqual(self.arrow("Cliente", "Checkout")["asserts"], ["attiva"])
        self.assertEqual(self.arrow("API pagamenti", "card payment provider")["status"], "declared")

    def test_an_arrow_no_link_proves_is_refused(self):
        refused = self.arrow("Badge pagamento", "API pagamenti")
        self.assertEqual(refused["status"], "refused")
        self.assertIn("no link", refused["reason"])

    def test_a_declared_arrow_cites_a_point_of_the_code_end(self):
        self.assertEqual(self.with_cliente_arrow(cite="web/checkout.ts:9999")["status"], "refused")
        self.assertIn("server/http.py", self.with_cliente_arrow(cite="server/http.py:1")["reason"])
        self.assertIn("kind", self.with_cliente_arrow(kind=None)["reason"])
        self.assertIn("cite", self.with_cliente_arrow(cite=None)["reason"])

    def test_a_missing_member_refuses_the_node_and_names_it(self):
        self.assertEqual(self.node("Fantasma")["status"], "refused")
        self.assertIn("web/nope.ts", self.node("Fantasma")["reason"])
        self.assertIn("db/paymnts", self.node("Refuso")["reason"])
        self.assertEqual(self.node("API pagamenti")["files"], ["server/gateway.py", "server/payments.py"])
        self.assertEqual(self.node("Cliente")["status"], "accepted")

    def test_a_flow_needs_accepted_nodes_and_one_standing_arrow(self):
        self.assertEqual([f["status"] for f in self.report["flows"]], ["accepted", "accepted"])
        broken = self.check(changed(lambda v: v["flows"][1]["nodes"].append("Fantasma")))
        self.assertEqual(self.flow("Riprova dei pagamenti", broken)["status"], "refused")
        self.assertIn("Fantasma", self.flow("Riprova dei pagamenti", broken)["reason"])
        lone = self.check(changed(lambda v: v["flows"][1]["arrows"][0].update({"from": "Riprova", "to": "Pagamento"})))
        self.assertEqual(self.flow("Riprova dei pagamenti", lone)["status"], "refused")

    def test_on_names_accepted_nodes_only(self):
        report = self.check(changed(lambda v: node(v, "API pagamenti").update(on=["Fantasma"])))
        self.assertEqual(self.node("API pagamenti", report)["status"], "refused")
        self.assertIn("Fantasma", self.node("API pagamenti", report)["reason"])


if __name__ == "__main__":
    unittest.main()
