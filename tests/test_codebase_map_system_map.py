"""System map of the fixture in benchmarks/flow-model: format, verification, record."""

import copy
import json
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
        system_map.validate(changed(lambda v: (scoped(v), v.pop("areas"), v["flows"].pop())))  # the scope is present

    def test_a_flow_sits_in_a_present_area(self):
        self.refused(lambda v: v["flows"][1].update(area="comunicazioni"), "area")

    def test_an_unknown_field(self):
        self.refused(lambda v: node(v, "Checkout").update(owner="team"), "owner")
        self.refused(lambda v: v["flows"][0]["arrows"][0].update(weight=1), "weight")
        self.refused(lambda v: v.update(version=2), "version")


def fixture(holder) -> None:
    """The flow-model fixture as a git project with a snapshot, its rules and links."""
    holder.work = Path(tempfile.mkdtemp(prefix="system-map-")).resolve()
    holder.project = holder.work / "app"
    shutil.copytree(BENCH / "app", holder.project)
    for command in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=holder.project, check=True, capture_output=True)
    holder.manifest = holder.work / "snapshot/manifest.sqlite"
    refresh(holder)
    holder.rules = flows.load_rules(BENCH / "rules.json")
    holder.links = flows.link_facts(holder.manifest, holder.rules)


def refresh(holder) -> None:
    snapshot.main(["write", str(holder.project), "--out", str(holder.manifest), "--no-engine", "--no-index"])


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture(cls)

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

    def test_a_function_member_is_proved_through_its_file_and_says_so(self):
        # The route enters at create_payment; the node names charge_order, the function beside it that does the work.
        work = self.check(changed(lambda v: node(v, "API pagamenti").update(
            members=["server/payments.py::charge_order", "server/gateway.py"])))
        entering = self.arrow("Checkout", "API pagamenti", work)
        self.assertEqual((entering["status"], entering["precise"]), ("proved", False))
        self.assertEqual(entering["proof"][0]["to"], "server/payments.py::create_payment")
        self.assertNotIn("precise", self.arrow("API pagamenti", "Pagamento", work))  # charge_order itself writes
        self.assertNotIn("precise", self.arrow("Checkout", "API pagamenti"))         # a file member holds the function
        route = self.check(changed(lambda v: node(v, "API pagamenti").update(
            members=["server/payments.py::create_payment", "server/gateway.py"])))
        self.assertIs(self.arrow("API pagamenti", "Pagamento", route)["precise"], False)  # the write is beside it
        self.assertEqual(self.arrow("Badge pagamento", "API pagamenti", work)["status"], "refused")

    def test_a_function_another_node_holds_is_not_beside(self):
        def cut(v):
            node(v, "API pagamenti").update(members=["server/payments.py::charge_order", "server/gateway.py"])
            v["nodes"].append({"name": "Rotta pagamenti", "type": "servizio o API",
                               "members": ["server/payments.py::create_payment"]})
            v["flows"][0]["nodes"].append("Rotta pagamenti")
        self.assertEqual(self.arrow("Checkout", "API pagamenti", self.check(changed(cut)))["status"], "refused")

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

    def test_a_shared_file_proves_no_arrow_by_itself(self):
        def share(v):
            node(v, "Badge pagamento")["members"].append("web/checkout.ts")
            v["flows"][0]["arrows"].append({"from": "Badge pagamento", "to": "Checkout", "data": "nulla"})
        self.assertEqual(self.arrow("Badge pagamento", "Checkout", self.check(changed(share)))["status"], "refused")

    def test_module_and_directory_members(self):
        report = self.check(changed(lambda v: (node(v, "Riprova").update(members=["module:payment"]),
                                               node(v, "API pagamenti").update(members=["server"]))))
        self.assertIn("server/jobs.py", self.node("Riprova", report)["files"])
        self.assertIn("server/http.py", self.node("API pagamenti", report)["files"])
        self.assertEqual(self.arrow("Pagamento", "Riprova", report)["status"], "proved")
        missing = self.check(changed(lambda v: node(v, "Riprova").update(members=["module:nessuno"])))
        self.assertIn("module:nessuno", self.node("Riprova", missing)["reason"])


def with_node(**fields) -> dict:
    """The test map with one more node, or with the node of that id changed."""
    value = copy.deepcopy(TEST_MAP)
    if "id" in fields:
        value["nodes"] = [n for n in value["nodes"] if system_map.modules.slug(n["name"]) != fields["id"]]
    value["nodes"].append({"type": "schermata", **fields})
    return value


def names(system) -> list[str]:
    return [n["name"] for n in system["nodes"]]


def by_id(system, kind, ident) -> dict:
    return next(r for r in system[kind] if r["id"] == ident)


class RecordTests(unittest.TestCase):
    def setUp(self):
        fixture(self)
        self.addCleanup(shutil.rmtree, self.work, True)

    def record(self, value):
        return system_map.record(self.manifest, self.rules, copy.deepcopy(value))

    def load(self):
        return system_map.load(self.manifest, self.rules)

    def declare(self, **fields):
        """The project confirms a node of the map, with the fields given changed."""
        system = self.load()
        ids = {n["name"]: n["id"] for n in system["nodes"]}
        found = dict(by_id(system, "nodes", fields["id"]))
        declared = {k: found[k] for k in ("id", "name", "type", "position", "members", "evidence") if k in found}
        declared.update(on=[ids[n] for n in found["on"]], **fields)
        path = self.project / system_map.DECLARED_FILE
        value = (json.loads(path.read_text(encoding="utf-8")) if path.exists()
                 else {"schema": system_map.DECLARED_SCHEMA, "nodes": [], "flows": []})
        value["nodes"] = [n for n in value["nodes"] if n["id"] != fields["id"]] + [declared]
        path.write_text(json.dumps(value), encoding="utf-8")
        refresh(self)

    def node_report(self, report, name):
        return next(n for n in report["nodes"] if n["name"] == name)

    def test_a_long_remainder_is_reported_by_directory_and_kept_by_name_in_the_map(self):
        from unittest import mock
        with mock.patch.object(system_map, "LEFT_LISTED", 2):
            report = self.record(TEST_MAP)
        entries = report["coverage"]["entries"]
        self.assertNotIn("left", entries)
        self.assertEqual(entries["left_by_directory"], {"admin": 1, "server": 1, "web": 1})
        self.assertEqual(report["coverage"]["routes"]["left"], ["admin/orders.py::list_all_orders", "server/orders.py::list_orders"])
        self.assertEqual(len(self.load()["coverage"]["entries"]["left"]), 3)

    def test_coverage_counts_what_the_accepted_flows_hold(self):
        report = self.record(TEST_MAP)
        coverage = report["coverage"]
        self.assertEqual((coverage["entries"]["in"], coverage["entries"]["of"]), (3, 6))
        self.assertEqual(coverage["entries"]["left"],
                         ["admin/orders.py::list_all_orders", "server/orders.py::list_orders", "web/cart.ts::toggleTheme"])
        self.assertEqual([(coverage[k]["in"], coverage[k]["of"]) for k in ("stores", "routes")], [(2, 4), (1, 3)])
        self.assertEqual(self.load()["coverage"], coverage)
        recorded = (self.manifest.parent / system_map.FILE).read_text(encoding="utf-8")
        self.assertNotIn("Fantasma", recorded)
        self.assertNotIn("Refuso", recorded)
        flow = by_id(self.load(), "flows", "pagare-un-ordine")
        self.assertNotIn(("Badge pagamento", "API pagamenti"), {(a["from"], a["to"]) for a in flow["arrows"]})

    def test_about_answers_for_a_node_and_an_area(self):
        self.record(TEST_MAP)
        system = self.load()
        self.assertEqual([f["name"] for f in system_map.about(system, "Pagamento")["flows"]],
                         ["Pagare un ordine", "Riprova dei pagamenti"])
        self.assertEqual(system_map.about(system, "pagamento"), system_map.about(system, "Pagamento"))
        area = system_map.about(system, "pagamenti e abbonamenti")
        self.assertEqual([f["name"] for f in area["flows"]], ["Pagare un ordine"])
        self.assertEqual(area["flows"][0]["files"], ["server/gateway.py", "server/payments.py", "web/badge.ts",
                                                     "web/checkout.ts"])
        self.assertEqual((area["externals"], area["unseen"]), (["card payment provider", "Cliente"], []))
        self.assertEqual(system_map.about(system, "riprova-dei-pagamenti")["kind"], "flow")
        self.record(changed(lambda v: node(v, "Server shop").update(position="unseen", evidence=[], where="infra")))
        self.assertEqual(system_map.about(self.load(), "Server shop")["unseen"], [{"name": "Server shop", "where": "infra"}])

    def test_identity_does_not_follow_the_name(self):
        first = self.record(TEST_MAP)
        self.assertEqual(self.node_report(first, "Checkout")["id"], "checkout")
        again = self.record(with_node(name="Schermata di pagamento", members=["web/checkout.ts"]))
        self.assertEqual(self.node_report(again, "Schermata di pagamento")["status"], "refused")
        self.assertIn("checkout", self.node_report(again, "Schermata di pagamento")["reason"])
        twins = self.record(changed(lambda v: v["nodes"].extend([
            {"name": "Carrello", "type": "schermata", "members": ["web/cart.ts"]},
            {"name": "Cestino", "type": "schermata", "members": ["web/cart.ts"]}])))
        self.assertIn("carrello", self.node_report(twins, "Cestino")["reason"])
        wider = self.record(with_node(name="Gestione cassa", members=["web/checkout.ts", "web/cart.ts"]))
        self.assertEqual(self.node_report(wider, "Gestione cassa")["status"], "refused")
        self.assertIn("checkout", self.node_report(wider, "Gestione cassa")["reason"])
        self.assertEqual(self.record(TEST_MAP)["created"], [])
        self.record(with_node(id="checkout", name="Schermata di pagamento", members=["web/checkout.ts"]))
        self.assertEqual(names(self.load()).count("Schermata di pagamento"), 1)
        self.assertNotIn("Checkout", names(self.load()))
        self.declare(id="checkout", name="Checkout")
        report = self.record(with_node(id="checkout", name="Cassa", members=["web/checkout.ts"]))
        self.assertEqual(self.node_report(report, "Cassa")["status"], "confirmed")
        confirmed = by_id(self.load(), "nodes", "checkout")
        self.assertEqual((confirmed["name"], confirmed["status"]), ("Checkout", "confirmed"))

    def test_a_rename_does_not_take_the_name_of_another_node(self):
        self.record(TEST_MAP)
        report = self.record({"scope": ["comunicazioni"], "areas": [{"name": "comunicazioni", "present": False}],
                              "nodes": [{"id": "checkout", "name": "Riprova", "type": "schermata",
                                         "members": ["web/checkout.ts"]}]})
        self.assertIn("riprova", self.node_report(report, "Riprova")["reason"])
        self.assertEqual(by_id(self.load(), "nodes", "checkout")["name"], "Checkout")

    def test_a_refused_flow_leaves_the_recorded_one(self):
        self.record(TEST_MAP)
        before = by_id(self.load(), "flows", "riprova-dei-pagamenti")
        report = self.record(changed(lambda v: v["flows"][1]["arrows"][0].update({"from": "Riprova", "to": "Pagamento"})))
        self.assertEqual(report["flows"][1]["status"], "refused")
        self.assertNotIn("riprova-dei-pagamenti", report["removed"])
        self.assertEqual(by_id(self.load(), "flows", "riprova-dei-pagamenti"), before)

    def test_a_declared_file_that_does_not_read_is_a_gap(self):
        self.record(TEST_MAP)
        (self.project / system_map.DECLARED_FILE).write_text(json.dumps(
            {"schema": system_map.DECLARED_SCHEMA, "nodes": [{"id": "x", "name": "X", "type": "schermata",
                                                              "members": ["web/cart.ts"], "on": ["nowhere"]}]}))
        refresh(self)
        system = self.load()
        self.assertIn("nowhere", system["gaps"][0]["reason"])
        self.assertNotIn("X", names(system))

    def test_a_proposal_removes_nothing_it_does_not_name(self):
        self.record(TEST_MAP)
        before = self.load()
        scoped = self.record({"scope": ["pagamenti e abbonamenti"], "nodes": [], "flows": []})
        whole = self.record(changed(lambda v: v["flows"].pop(0)))  # the correction of one flow, the other not restated
        self.assertEqual((scoped["removed"], whole["removed"]), ([], []))
        self.assertEqual([f["id"] for f in self.load()["flows"]], [f["id"] for f in before["flows"]])
        self.assertEqual(names(self.load()), names(before))

    def test_a_flow_leaves_the_map_when_the_proposal_removes_it_by_id_or_name(self):
        self.record(TEST_MAP)
        report = self.record({"scope": ["esercizio"], "remove": ["Pagare un ordine", "nessuno", "Riprova"]})
        self.assertIn("pagare-un-ordine", report["removed"])
        self.assertIn("checkout", report["removed"])        # a node no flow uses any more
        self.assertNotIn("pagamento", report["removed"])    # still used by the other flow
        self.assertEqual({r["name"]: r["reason"] for r in report["not_removed"]},
                         {"nessuno": "no flow has this id or name",
                          "Riprova": "a node leaves the map when no flow uses it"})
        self.assertEqual([f["id"] for f in self.load()["flows"]], ["riprova-dei-pagamenti"])
        with self.assertRaisesRegex(ValueError, "both proposed and removed"):
            self.record(changed(lambda v: v.update(remove=["Pagare un ordine"])))

    def test_a_proposal_for_one_area_leaves_the_others(self):
        self.record(TEST_MAP)
        before = self.load()
        flow = copy.deepcopy(TEST_MAP["flows"][0])
        flow["nodes"].remove("Badge pagamento")
        flow["arrows"] = [a for a in flow["arrows"] if "Badge pagamento" not in (a["from"], a["to"])]
        proposal = {"scope": ["pagamenti e abbonamenti"], "areas": [{"name": "pagamenti e abbonamenti", "present": True}],
                    "nodes": [], "flows": [flow]}
        report = self.record(proposal)
        after = self.load()
        self.assertEqual(by_id(after, "flows", "riprova-dei-pagamenti"), by_id(before, "flows", "riprova-dei-pagamenti"))
        self.assertEqual([n["id"] for n in after["nodes"]].count("pagamento"), 1)
        self.assertIn("badge-pagamento", report["removed"])
        self.assertNotIn("pagamento", report["removed"])
        self.record(TEST_MAP)
        self.declare(id="badge-pagamento", name="Badge pagamento")
        self.assertNotIn("badge-pagamento", self.record(proposal)["removed"])
        self.assertIn("Badge pagamento", names(self.load()))

    def test_a_changed_file_is_proved_again_or_sent_back(self):
        self.record(TEST_MAP)
        for path, line in (("web/badge.ts", "// edited\n"), ("server/http.py", "# edited\n")):
            with (self.project / path).open("a", encoding="utf-8") as stream:
                stream.write(line)
        refresh(self)
        system = self.load()
        badge = by_id(system, "nodes", "badge-pagamento")
        self.assertEqual((badge["status"], badge["fresh"]), ("accepted", True))
        shop = by_id(system, "nodes", "server-shop")
        self.assertEqual((shop["fresh"], shop["changed_files"]), (False, ["server/http.py"]))
        runs_on = next(c for c in system["correspondences"] if (c["from"], c["to"]) == ("API pagamenti", "Server shop"))
        self.assertEqual((runs_on["fresh"], runs_on["changed_files"]), (False, ["server/http.py"]))
        self.assertTrue(by_id(system, "nodes", "checkout")["fresh"])
        with (self.project / "web/checkout.ts").open("a", encoding="utf-8") as stream:
            stream.write("// edited\n")
        refresh(self)
        flow = by_id(self.load(), "flows", "pagare-un-ordine")
        declared = next(a for a in flow["arrows"] if (a["from"], a["to"]) == ("Cliente", "Checkout"))
        self.assertEqual((declared["status"], declared["fresh"], declared["changed_files"]),
                         ("declared", False, ["web/checkout.ts"]))
        self.assertFalse(flow["fresh"])


if __name__ == "__main__":
    unittest.main()
