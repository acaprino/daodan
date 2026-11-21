"""Durable event evidence and per-entry traversal of one indexed snapshot."""

import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import flow_paths as paths
import system_map
from test_codebase_map_system_map import fixture


def edge(src, dst, effect=False):
    return {"from": src, "to": dst, "type": "scrive" if effect else "chiama", "site": "a.py:1", "origin": "diretto"}


def entry(symbol):
    return {"site": "a.py:1", "kind": "azione", "symbol": symbol}


class PathIndexTests(unittest.TestCase):
    def test_manual_event_types_disambiguate_legacy_bindings_at_same_site(self):
        action = entry("hook")
        self.assertNotEqual(paths.entry_id(action), paths.entry_id({**action, "kind": "comando"}))
        click = {**action, "shape": "clicked", "reader": "AST"}
        self.assertEqual(paths.entry_id(click), paths.entry_id({**click, "kind": "comando"}))

    def test_first_exploration_indexes_isolated_entries_once(self):
        class CountVisits(list):
            visited = 0
            def __iter__(self):
                for item in super().__iter__():
                    self.visited += 1
                    yield item

        for count in (256, 512):
            with self.subTest(count=count):
                edges = CountVisits(edge(str(n), f"store:{n}", effect=True) for n in range(count))
                links = {"edges": edges, "entries": [entry(str(n)) for n in range(count)], "gaps": []}
                graph = paths._PathGraph(links)
                cards = paths._inventory(links, graph)
                steps = [paths._steps(graph, card) for card in cards.values()]
                self.assertTrue(all(len(rows) == 1 and rows[0]["end"] == "effetto" for rows in steps))
                self.assertEqual(edges.visited, count)

    def test_cycle_and_effect_on_other_branch_have_separate_conclusions(self):
        links = {"entries": [entry("A")], "gaps": [], "edges": [edge("A", "store:E", True), edge("A", "B"),
                                                                edge("B", "C"), edge("C", "B")]}
        graph = paths._PathGraph(links)
        card, = paths._inventory(links, graph).values()
        steps = paths._steps(graph, card)
        self.assertEqual([(s["from"], s["to"], s["end"]) for s in steps if s["end"]],
                         [("A", "store:E", "effetto"), ("C", "B", "lacuna")])
        self.assertEqual(steps[-1]["reason"], "cycle without a proven effect")

    def test_legacy_dispositions_require_matching_saved_details(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "manifest.sqlite"
            bindings = [entry("A"), entry("B")]
            links = {"entries": bindings, "edges": [edge("A", "store:E", True)], "gaps": []}
            graph = paths._PathGraph(links)
            cards = list(paths._inventory(links, graph).values())
            old_key = "a" * 64 + ":" + "b" * 64
            old_ids = [paths._digest([old_key, e]) for e in bindings]
            paths._saved(manifest, old_key, lambda: {old: {**card, "card_id": old} for old, card in zip(old_ids, cards)})
            paths._saved(manifest, old_ids[0], lambda: paths._steps(graph, cards[0]))
            with sqlite3.connect(manifest.with_name("entry-reviews.sqlite")) as db:
                db.execute("CREATE TABLE reviews (id TEXT PRIMARY KEY, disposition TEXT, reason TEXT)")
                db.executemany("INSERT INTO reviews VALUES (?, 'excluded','outside')", [(i,) for i in old_ids])
            with patch.object(paths.flows, "cached_links", return_value=(None, links)):
                self.assertEqual(paths.next_question(manifest, [])["reviewed"]["excluded"], 1)
                links["edges"][0]["to"] = "store:different"
                self.assertEqual(paths.next_question(manifest, [])["reviewed"]["excluded"], 0)


class SavedIdentityTests(unittest.TestCase):
    def setUp(self):
        fixture(self)
        self.addCleanup(shutil.rmtree, self.work)
        self.name = "Pagamento della spesa"
        self.input = {"name": self.name, "area": "pagamenti e abbonamenti", "types": ["funzionale"]}

    def accept(self, card, **choices):
        steps = paths.page(self.manifest, self.rules, card_id=card["card_id"], limit=100)["steps"]
        effect = next(s for s in steps if s["to"] == "store:web state/payment")
        numbers = [effect["n"]]
        while (parent := steps[numbers[-1] - 1]["parent"]) is not None:
            numbers.append(parent)
        return paths.record(self.manifest, self.rules, {**self.input, **choices, "card_id": card["card_id"],
                            "steps": numbers[::-1], "data": ["stato"] * len(numbers)})

    def pay_cards(self):
        return [c for c in paths.page(self.manifest, self.rules, limit=100)["cards"]
                if c["handler"] == "web/checkout.ts::onPayClick"]

    def test_decisions_survive_rule_reorder_unrelated_write_and_manifest_touch(self):
        card = self.pay_cards()[0]
        self.assertEqual(self.accept(card)["status"], "accepted")
        other = next(c for c in paths.page(self.manifest, self.rules)["cards"] if c["handler"] != card["handler"])
        self.assertEqual(paths.record(self.manifest, self.rules, {"card_id": other["card_id"], "disposition": "excluded",
                                                                 "reason": "Not an operator control"})["status"], "excluded")
        self.rules = self.rules[::-1]
        self.manifest.touch()
        self.assertEqual(card["card_id"], self.pay_cards()[0]["card_id"])
        counts = paths.next_question(self.manifest, self.rules)["reviewed"]
        self.assertEqual((counts["accepted"], counts["excluded"]), (1, 1))
        self.assertEqual(system_map.about(system_map.load(self.manifest, self.rules), self.name)["flows"][0]["trace_id"], card["card_id"])
        self.links["edges"].append(edge("unused", "store:new", True))
        with patch.object(paths.flows, "cached_links", side_effect=lambda *a, with_key=False: (None, self.links) if with_key else self.links):
            self.assertEqual(self.pay_cards()[0]["card_id"], card["card_id"])
            self.assertEqual(paths.next_question(self.manifest, self.rules)["reviewed"], counts)
            self.links["edges"] = [e for e in self.links["edges"] if e["to"] != "store:web state/payment"]
            self.assertEqual(paths.next_question(self.manifest, self.rules)["reviewed"]["accepted"], 0)

    def test_legacy_map_rebinds_and_two_controls_can_cite_same_path(self):
        first = next(e for e in self.links["entries"] if e["symbol"].endswith("::onPayClick"))
        self.links["entries"].append({**first, "column": 234, "label": "Second control"})
        with patch.object(paths.flows, "cached_links", side_effect=lambda *a, with_key=False: (None, self.links) if with_key else self.links):
            first, second = self.pay_cards()
            self.assertEqual(self.accept(first)["status"], "accepted")
            saved = self.manifest.with_name(system_map.FILE)
            old = json.loads(saved.read_text())
            old["flows"][0]["trace"]["card_id"] = "legacy id"
            saved.write_text(json.dumps(old))
            self.assertEqual(paths.next_question(self.manifest, self.rules)["reviewed"]["accepted"], 1)
            self.assertEqual(system_map.about(system_map.load(self.manifest, self.rules), self.name)["flows"][0]["trace_id"], first["card_id"])
            self.assertEqual(self.accept(second)["status"], "accepted")
            self.assertEqual(paths.next_question(self.manifest, self.rules)["reviewed"]["accepted"], 2)
            loaded = system_map.load(self.manifest, self.rules)["flows"]
            self.assertEqual(len(loaded), 1)
            bindings = system_map.trace_bindings(loaded[0]["trace"])
            self.assertEqual({b["card_id"] for b in bindings}, {first["card_id"], second["card_id"]})
            self.links["entries"].remove(bindings[0]["entry"])
            flow, = system_map.load(self.manifest, self.rules)["flows"]
            self.assertTrue(flow["fresh"])
            self.assertEqual(flow["trace"]["card_id"], bindings[1]["card_id"])

    def test_independent_names_allowed_and_a_refusal_does_not_touch_saved_map(self):
        e = next(e for e in self.links["entries"] if e["symbol"].endswith("::onPayClick"))
        self.links["entries"].append({**e, "column": 44, "label": "Again"})
        with patch.object(paths.flows, "cached_links", side_effect=lambda *a, with_key=False: (None, self.links) if with_key else self.links):
            first, second = self.pay_cards()
            self.assertEqual(self.accept(first)["status"], "accepted")
            saved = self.manifest.with_name(system_map.FILE)
            baseline = saved.read_bytes()
            self.assertEqual(self.accept(first, name="Un pagamento duplicato")["status"], "refused")
            self.assertEqual(saved.read_bytes(), baseline)
            self.assertEqual(self.accept(second, name="Conferma del pagamento")["status"], "accepted")
            self.assertEqual(paths.next_question(self.manifest, self.rules)["reviewed"]["accepted"], 2)
