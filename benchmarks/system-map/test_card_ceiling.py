"""The ceiling of the product path cards on the flow-model fixture, with a webhook the card provider calls."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import card_ceiling  # noqa: E402
import flow_paths  # noqa: E402
from test_possible import WEBHOOK, run  # noqa: E402

PAYMENT = {"node": "Pagamento", "kind": "stato salvato"}
RETRY = {"name": "Riprovare i pagamenti rifiutati", "nodes": ["Lavori", "Pagamento"],
         "entries": [{"node": "Lavori", "kind": "lavoro pianificato"}], "effects": [PAYMENT], "arrows": []}
REFERENCE = {
    "nodes": [
        {"name": "Cliente", "type": "attore", "position": "external", "evidence": ["web/checkout.ts"]},
        {"name": "Checkout", "type": "schermata", "members": ["web/checkout.ts"]},
        {"name": "Badge pagamento", "type": "schermata", "members": ["web/badge.ts"]},
        {"name": "Eventi della carta", "type": "servizio o API", "members": ["server/events.py"]},
        {"name": "Ordini", "type": "servizio o API", "members": ["server/orders.py"]},
        {"name": "Lavori", "type": "lavoro a orario", "members": ["server/jobs.py"]},
        {"name": "Pagamento", "type": "entità", "members": ["store:db/payments"]},
        {"name": "Fornitore delle carte", "type": "gateway", "position": "external", "evidence": ["server/gateway.py"]},
        {"name": "Landing", "type": "schermata", "position": "unseen", "where": "un altro repository"},
    ],
    "flows": [
        {"name": "Pagare un ordine", "nodes": ["Cliente", "Checkout", "Pagamento", "Badge pagamento"],
         "entries": [{"node": "Cliente", "kind": "controllo dell'interfaccia"}],
         "effects": [PAYMENT, {"node": "Badge pagamento"}],
         "arrows": [{"from": "Cliente", "to": "Checkout", "data": "clic su Paga"},
                    {"from": "Checkout", "to": "Pagamento", "data": "ordine da pagare"}]},
        {"name": "Registrare l'esito della carta", "nodes": ["Fornitore delle carte", "Eventi della carta", "Pagamento"],
         "entries": [{"node": "Fornitore delle carte", "kind": "rotta"}], "effects": [PAYMENT],
         "arrows": [{"from": "Fornitore delle carte", "to": "Eventi della carta", "data": "esito"},
                    {"from": "Eventi della carta", "to": "Pagamento", "data": "esito registrato"}]},
        RETRY,
        {"name": "Mostrare lo stato nel badge", "nodes": ["Checkout", "Badge pagamento"],
         "entries": [{"node": "Checkout", "kind": "controllo dell'interfaccia"}],
         "effects": [{"node": "Badge pagamento", "kind": "valore mostrato"}], "arrows": []},
        {"name": "Aprire il badge", "nodes": ["Badge pagamento", "Pagamento"],
         "entries": [{"node": "Badge pagamento", "kind": "controllo dell'interfaccia"}], "effects": [PAYMENT], "arrows": []},
        {"name": "Abbonarsi dalla landing", "nodes": ["Landing", "Pagamento"],
         "entries": [{"node": "Landing", "kind": "controllo dell'interfaccia"}], "effects": [PAYMENT], "arrows": []},
        {"name": "Consultare gli ordini", "nodes": ["Ordini", "Pagamento"],
         "entries": [{"node": "Ordini", "kind": "rotta"}], "effects": [PAYMENT], "arrows": []},
    ],
}
EXTRA = [  # nodes a test adds to the reference
    {"name": "Stato pagamento", "type": "entità", "members": ["store:web state/payment"]},
    {"name": "Pagamento e stato", "type": "entità", "members": ["store:web state/payment", "store:db/payments"]},
    {"name": "Carrello", "type": "entità", "members": ["store:web state/cart"]},
    {"name": "Segnale del badge", "type": "entità", "members": ["store:web state/badge"]},  # a store only a test's links have
    {"name": "Carrello a schermo", "type": "schermata", "members": ["web/cart.ts"]},
    {"name": "Ingresso con file mancante", "type": "schermata", "members": ["web/checkout.ts", "web/missing.ts"]},
    {"name": "Ingresso senza file", "type": "schermata", "members": ["web/missing.ts"]},  # verify refuses both
]


def flow(name, entries, effects, arrows=(), also=()):
    ends = [end for pair in arrows for end in pair]
    return {"name": name, "nodes": list(dict.fromkeys([*entries, *effects, *ends, *also])),
            "entries": [{"node": n} for n in entries], "effects": [{"node": n} for n in effects],
            "arrows": [{"from": a, "to": b, "data": "dato"} for a, b in arrows]}


class CardCeiling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="ceiling-")).resolve()
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        project = cls.work / "app"
        shutil.copytree(ROOT / "benchmarks/flow-model/app", project)
        (project / "server/events.py").write_text(WEBHOOK, encoding="utf-8")
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            run(command, cwd=project)
        cls.manifest = cls.work / "snapshot/manifest.sqlite"
        core = ROOT / "daodan" / "core"
        run([sys.executable, str(core / "snapshot.py"), "write", str(project), "--out", str(cls.manifest),
             "--no-engine", "--no-index"])
        cls.links = json.loads(run([sys.executable, str(core / "flows.py"), "links", str(cls.manifest), "--rules",
                                    str(ROOT / "benchmarks/flow-model/rules.json")]))
        cls.result = card_ceiling.measure(cls.manifest, cls.links, REFERENCE)
        cls.rows = {row["name"]: row for row in cls.result["per_flow"]}

    def row(self, one_flow, links=None):
        reference = {"nodes": REFERENCE["nodes"] + EXTRA, "flows": [one_flow]}
        return card_ceiling.measure(self.manifest, links or self.links, reference)["per_flow"][0]

    def reading(self, row, links=None):
        """The handler of the row's card and the bytes of its steps up to the effect, from flow_paths alone."""
        links = links or self.links
        graph = flow_paths._build_graph(links)
        card = flow_paths._inventory(links, graph)[row["card_id"]]
        return card["handler"], sum(len(json.dumps(step)) + 2 for step in flow_paths._steps(graph, card)[:row["effect_n"]])

    def sampled_write(self):
        """The links with the write of charge_order into the payments table made uncertain: no engine ran on the
        fixture, so none is by itself."""
        sampled = copy.deepcopy(self.links)
        for edge in sampled["edges"]:
            if edge["type"] == "scrive" and edge["from"] == "server/payments.py::charge_order":
                edge["confidence"] = "sampled"
        return sampled

    def test_a_flow_entered_by_a_person_is_proved_by_the_card_of_the_screen_they_act_on(self):
        row = self.rows["Pagare un ordine"]
        self.assertEqual((row["bucket"], row["cards_at_entry"]), ("provata", 1))
        self.assertEqual((row["steps"], row["effect_n"], row["depth"]), (19, 11, 4))  # click -> submit -> route -> charge -> db
        self.assertEqual(self.reading(row), ("web/checkout.ts::onPayClick", row["bytes_to_effect"]))
        self.assertEqual((row["effects_proved"], row["cards_needed"], row["cards_by_site_only"]), ([1, 1], 1, 0))
        self.assertNotIn("detail", row)
        self.assertEqual(row["effects"], [{"node": "Pagamento", "kind": "stato salvato", "expressible": True},
                                          {"node": "Badge pagamento", "kind": None, "expressible": False}])

    def test_a_handler_that_writes_the_store_itself_is_proved_at_depth_one(self):
        row = self.rows["Registrare l'esito della carta"]  # entered by a service of others, through its arrow
        self.assertEqual((row["bucket"], row["steps"], row["effect_n"], row["depth"]), ("provata", 3, 1, 1))

    def test_a_flow_whose_only_effect_is_a_screen_is_not_expressible_by_a_card(self):
        row = self.rows["Mostrare lo stato nel badge"]
        self.assertEqual((row["bucket"], row["cards_at_entry"]), ("effetto non esprimibile", 1))
        self.assertNotIn("card_id", row)

    def test_a_flow_with_no_card_at_its_entry_says_whether_no_node_has_code_or_no_node_has_a_card(self):
        self.assertEqual((self.rows["Aprire il badge"]["bucket"], self.rows["Aprire il badge"]["detail"]),
                         ("nessuna scheda all'ingresso", "no card at the entry"))
        row = self.rows["Abbonarsi dalla landing"]
        self.assertEqual((row["bucket"], row["detail"], row["cards_at_entry"]),
                         ("nessuna scheda all'ingresso", "no entry node with code", 0))

    def test_a_write_no_path_reaches_is_a_hole_of_the_graph(self):
        row = self.rows["Consultare gli ordini"]  # list_orders only reads the table
        self.assertEqual((row["bucket"], row["cards_at_entry"]), ("buco del grafo", 1))

    def test_a_write_the_card_drops_is_cut_by_the_card_and_not_missing_from_the_graph(self):
        self.assertEqual(self.rows[RETRY["name"]]["bucket"], "provata")
        self.assertEqual(self.row(RETRY, self.sampled_write())["bucket"], "tagliata dalla scheda")

    def test_a_card_is_at_the_entry_by_the_file_of_its_binding_site_when_its_handler_is_elsewhere(self):
        moved = json.loads(json.dumps(self.links).replace("web/checkout.ts::onPayClick", "web/handlers.ts::onPayClick"))
        row = self.row(REFERENCE["flows"][0], moved)
        self.assertEqual((row["bucket"], row["cards_at_entry"], row["cards_by_site_only"]), ("provata", 1, 1))
        self.assertEqual(self.reading(row, moved)[0], "web/handlers.ts::onPayClick")

    def test_a_flow_is_proved_only_when_every_store_effect_is_and_it_reports_the_last_one_proved(self):
        row = self.row(flow("Pagare e salvare lo stato", ["Checkout"], ["Stato pagamento", "Pagamento"]))
        self.assertEqual((row["bucket"], row["effects_proved"], row["cards_needed"]), ("provata", [2, 2], 1))
        self.assertEqual((row["effect_n"], row["depth"]), (11, 4))  # the table, not the earlier state write at step 3
        self.assertEqual(self.reading(row)[1], row["bytes_to_effect"])

    def test_effects_proved_by_different_cards_report_the_proof_a_model_reads_last(self):
        row = self.row(flow("Pagare e registrare", ["Checkout", "Eventi della carta"], ["Stato pagamento", "Pagamento"]))
        self.assertEqual((row["bucket"], row["effects_proved"], row["cards_needed"]), ("provata", [2, 2], 2))
        # the table is written at step 1 of the webhook, the state at step 3 of the click: the click is the longer read
        self.assertEqual((row["effect_n"], self.reading(row)), (3, ("web/checkout.ts::onPayClick", row["bytes_to_effect"])))

    def test_an_effect_proved_by_two_of_its_stores_is_proved_at_the_earlier_step(self):
        row = self.row(flow("Pagare con un solo nodo", ["Checkout"], ["Pagamento e stato"]))
        self.assertEqual((row["bucket"], row["effects_proved"], row["effect_n"], row["depth"]), ("provata", [1, 1], 3, 2))

    def test_the_effects_not_proved_decide_between_the_card_and_the_graph(self):
        hole = self.row(flow("Pagare e riempire il carrello", ["Checkout"], ["Stato pagamento", "Carrello"]))
        self.assertEqual((hole["bucket"], hole["effects_proved"], hole["cards_at_entry"]), ("buco del grafo", [1, 2], 1))
        self.assertNotIn("card_id", hole)
        sampled = self.sampled_write()  # the table is reached, the card does not prove it
        cut = self.row(flow("Pagare e salvare lo stato", ["Checkout"], ["Stato pagamento", "Pagamento"]), sampled)
        self.assertEqual((cut["bucket"], cut["effects_proved"]), ("tagliata dalla scheda", [1, 2]))
        both = self.row(flow("Pagare, salvare e riempire", ["Checkout"], ["Stato pagamento", "Pagamento", "Carrello"]), sampled)
        self.assertEqual((both["bucket"], both["effects_proved"]), ("buco del grafo", [1, 3]))  # one of them is not reached

    def test_the_readers_of_a_store_are_followed_only_when_a_node_of_the_flow_holds_it(self):
        links = copy.deepcopy(self.links)  # the badge reads the payment state and writes a store of its own
        links["stores"]["web state/badge"] = {"writes": ["web/badge.ts::renderBadge"], "reads": []}
        links["edges"].append({"from": "web/badge.ts::renderBadge", "to": "store:web state/badge", "type": "scrive",
                               "site": "web/badge.ts:5", "origin": "dedotto"})
        shared = self.row(flow("Segnalare il pagamento", ["Checkout"], ["Segnale del badge"], also=["Stato pagamento"]), links)
        self.assertEqual((shared["bucket"], shared["effects_proved"]), ("tagliata dalla scheda", [0, 1]))
        alone = self.row(flow("Segnalare senza lo stato", ["Checkout"], ["Segnale del badge"]), links)
        self.assertEqual(alone["bucket"], "buco del grafo")

    def test_an_activation_is_not_a_path(self):
        links = copy.deepcopy(self.links)
        links["edges"].append({"from": "web/cart.ts::toggleTheme", "to": "web/cart.ts::addToCart", "type": "attiva",
                               "site": "web/cart.ts:12", "origin": "dedotto"})
        row = self.row(flow("Aggiungere dal tema", ["Carrello a schermo"], ["Carrello"]), links)
        self.assertEqual((row["bucket"], row["cards_at_entry"]), ("buco del grafo", 1))

    def test_a_node_verify_refused_is_no_entry_and_leads_to_none(self):
        for refused, arrows in (("Ingresso con file mancante", ()),  # it holds the screen, and is refused
                                ("Ingresso senza file", (("Ingresso senza file", "Checkout"),))):  # its arrow leads to one
            row = self.row(flow("Entrare da un nodo rifiutato", [refused], ["Pagamento"], arrows))
            self.assertEqual((row["bucket"], row["detail"], row["cards_at_entry"]),
                             ("nessuna scheda all'ingresso", "no entry node with code", 0), refused)

    def test_a_card_with_an_uncertain_handler_proves_nothing_yet_is_at_the_entry_and_walked(self):
        uncertain = copy.deepcopy(self.links)
        for entry in uncertain["entries"]:
            if entry["symbol"] == "server/jobs.py::retry_declined":
                entry["handler_confidence"] = "sampled"
        row = self.row(RETRY, uncertain)
        self.assertEqual((row["bucket"], row["cards_at_entry"], row["effects_proved"]), ("tagliata dalla scheda", 1, [0, 1]))

    def test_a_row_with_no_card_at_its_entry_says_why_whatever_its_bucket(self):
        row = self.row(flow("Mostrare da fuori", ["Landing"], ["Badge pagamento"]))
        self.assertEqual((row["bucket"], row["detail"], row["effects_proved"]),
                         ("effetto non esprimibile", "no entry node with code", [0, 0]))
        row = self.row(flow("Mostrare dal badge", ["Badge pagamento"], ["Badge pagamento"]))
        self.assertEqual((row["bucket"], row["detail"]), ("effetto non esprimibile", "no card at the entry"))

    def test_the_totals_add_up_to_the_flows_the_effects_and_the_cards(self):
        self.assertEqual(self.result["flows"], {"provata": 3, "effetto non esprimibile": 1, "nessuna scheda all'ingresso": 2,
                                                "tagliata dalla scheda": 0, "buco del grafo": 1})
        self.assertEqual(sum(self.result["flows"].values()), len(REFERENCE["flows"]))
        self.assertEqual(self.result["effects"], {"expressible": 6, "not_expressible": {"-": 1, "valore mostrato": 1}})
        self.assertEqual(self.result["deck"], {"cards": 7, "with_effect": 5, "steps_median": 5, "steps_max": 19})

    def test_links_of_another_schema_are_refused(self):
        with self.assertRaisesRegex(ValueError, "links schema"):
            card_ceiling.measure(self.manifest, {**self.links, "schema": "daodan/flow-links/v2"}, REFERENCE)


if __name__ == "__main__":
    unittest.main()
