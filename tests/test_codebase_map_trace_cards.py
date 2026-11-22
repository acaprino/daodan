"""Machine-constructed event paths, including where the evidence ends."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

CORE = Path(__file__).resolve().parents[1] / "daodan" / "core"
sys.path.insert(0, str(CORE))
import flow_paths as traces


def edge(a, b, kind="chiama", line=1, **extra):
    return {"from": a, "to": b, "type": kind, "site": f"a.py:{line}", "origin": "diretto", **extra}


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.entry = {"kind": "azione", "shape": "clicked", "label": "Paga", "site": "w.ui:7", "symbol": "a.py::pay"}
        self.links = {"entries": [self.entry], "gaps": [{"symbol": "a.py::pay", "site": "a.py:3", "reason": "computed"}],
                      "edges": [edge("a.py::pay", "a.py::submit"), edge("a.py::submit", "store:db/pay", "scrive", 2),
                                edge("a.py::other", "store:db/pay", "scrive", 3)]}
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.manifest = Path(temporary.name) / "manifest.sqlite"
        self.cached = mock.patch.object(traces.flows, "cached_links", return_value=(None, self.links))
        self.cached.start()
        self.addCleanup(self.cached.stop)

    def test_nearest_first_direction_effect_and_file_gap(self):
        card = traces.page(self.manifest, [])["cards"][0]
        self.assertEqual((card["handler"], card["event"], card["label"]), ("a.py::pay", "clicked", "Paga"))
        result = traces.page(self.manifest, [], card_id=card["card_id"])
        steps = result["steps"]
        effect = next(s for s in steps if s["end"] == "effetto")
        parent = steps[effect["parent"] - 1]
        self.assertEqual((parent["from"], parent["to"], effect["from"], effect["to"]),
                         ("a.py::pay", "a.py::submit", "a.py::submit", "store:db/pay"))
        self.assertEqual([s["reason"] for s in steps if s["end"] == "lacuna"], ["computed"])
        self.assertNotIn("a.py::other", str(steps))
        self.assertEqual(traces.page(self.manifest, [], offset=1, limit=1, card_id=card["card_id"])["steps"], steps[1:2])

    def test_true_site_wrong_destination_never_becomes_a_flow(self):
        card = traces.page(self.manifest, [])["cards"][0]
        steps = traces.page(self.manifest, [], card_id=card["card_id"])["steps"]
        gap = next(s["n"] for s in steps if s["end"] == "lacuna")
        decision = {"card_id": card["card_id"], "steps": [gap], "data": ["denaro"], "name": "Pagamento del conto",
                    "area": "pagamenti e abbonamenti", "types": ["funzionale"], "corrections": [
                        {"step": gap, "site": "a.py:3", "text": "store.write(", "to": "store:db/pay"}]}
        with mock.patch.object(traces.system_map, "record", side_effect=AssertionError("invalid flow recorded")):
            result = traces.record(self.manifest, [], decision)
        self.assertEqual(result["status"], "refused")
        self.assertIn("destination", result["reason"])

    def test_shared_handler_keeps_distinct_events_and_a_cited_review_is_resumable(self):
        self.links["entries"].append({**self.entry, "column": 17, "label": "Paga dopo"})
        first, second = traces.page(self.manifest, [])["cards"]
        self.assertNotEqual(first["card_id"], second["card_id"])
        pending = traces.next_question(self.manifest, [])
        self.assertEqual(pending["remaining"], 2)
        decision = {"card_id": first["card_id"], "disposition": "unresolved", "reason": "Missing device recording"}
        self.assertEqual(traces.record(self.manifest, [], decision)["status"], "unresolved")
        resumed = traces.next_question(self.manifest, [])
        self.assertEqual((resumed["question"]["card_id"], resumed["remaining"], resumed["reviewed"]["unresolved"]),
                         (second["card_id"], 1, 1))
        steps = traces.page(self.manifest, [], card_id=second["card_id"])["steps"]
        self.assertEqual(next(s["shared_by"] for s in steps if s["end"] == "effetto"), 2)
        traces.record(self.manifest, [], {**decision, "card_id": second["card_id"], "disposition": "excluded"})
        self.assertEqual(traces.next_question(self.manifest, [])["status"], "complete")
        self.links["edges"][0]["site"] = "a.py:99"
        self.assertEqual(traces.next_question(self.manifest, [])["remaining"], 2)

    def test_the_new_stores_and_their_sqlite_sidecars_honor_confinement(self):
        for suffix in ("", "-journal", "-wal", "-shm"):
            with self.subTest(suffix=suffix):
                path = self.manifest.with_name("trace-cards.sqlite" + suffix)
                try:
                    path.symlink_to(self.manifest.with_name("other"))
                except OSError:
                    self.skipTest("this host cannot create symbolic links")
                with self.assertRaisesRegex(ValueError, "link"):
                    traces._saved(self.manifest, "id", lambda: [])
                path.unlink()
        linked = self.manifest.with_name("entry-reviews.sqlite")
        linked.symlink_to(self.manifest.with_name("other"))
        with self.assertRaisesRegex(ValueError, "link"):
            traces.next_question(self.manifest, [])
        self.assertFalse(linked.exists())

    def test_new_evidence_invalidates_an_old_step_number_and_sampled_is_visible(self):
        old = traces.page(self.manifest, [])["cards"][0]
        self.links["edges"][0].update(confidence="sampled", origin="osservato")
        with self.assertRaisesRegex(ValueError, "card"):
            traces.page(self.manifest, [], card_id=old["card_id"])
        card = traces.page(self.manifest, [])["cards"][0]
        steps = traces.page(self.manifest, [], card_id=card["card_id"])["steps"]
        sample = next(s for s in steps if s.get("confidence") == "sampled")
        self.assertEqual((sample["from"], sample["to"], sample["end"]), ("a.py::pay", "a.py::submit", "lacuna"))

    def test_the_whole_unicode_answer_fits_even_with_a_long_card_and_nested_edge_data(self):
        text = "😀" * 5000
        self.entry.update(label=text, event=text, reader=text, declared_in=text, handler_source=text)
        self.links["edges"][0].update(route=["service", "POST", text], recorded={"some": [text]})
        listed = traces.page(self.manifest, [], limit=100)
        ident = listed["cards"][0]["card_id"]
        self.assertTrue(listed["cards"][0]["truncated"])
        self.assertLess(len(json.dumps(listed)), traces.system_brief.LIMIT)
        detail = traces.page(self.manifest, [], card_id=ident, limit=100)
        self.assertLess(len(json.dumps(detail)), traces.system_brief.LIMIT)
        self.assertEqual(detail["card"]["card_id"], ident)
        self.assertTrue(detail["steps"][0]["truncated"])
        self.assertEqual(detail["steps"][0]["n"], 1)
        self.assertEqual(list(detail)[-1], "question")
        if detail["next_offset"] is not None:
            later = traces.page(self.manifest, [], card_id=ident, offset=detail["next_offset"])
            self.assertGreater(later["steps"][0]["n"], detail["steps"][-1]["n"])


class RecordedPathTests(unittest.TestCase):
    def test_actual_source_text_can_correct_only_the_cited_store_write(self):
        import shutil
        from test_codebase_map_system_map import fixture
        fixture(self)
        self.addCleanup(shutil.rmtree, self.work)
        links = self.links
        write = next(e for e in links["edges"] if e["from"] == "web/checkout.ts::submitPayment"
                     and e["to"] == "store:web state/payment")
        links["gaps"].append({"symbol": write["from"], "site": write["site"], "reason": "unresolved destination"})
        with mock.patch.object(traces.flows, "cached_links",
                               side_effect=lambda *args, with_key=False: (None, links) if with_key else links):
            card = next(c for c in traces.page(self.manifest, self.rules)["cards"] if c["handler"].endswith("::onPayClick"))
            detail = traces.page(self.manifest, self.rules, card_id=card["card_id"], limit=100)
            gap = next(s for s in detail["steps"] if s.get("reason") == "unresolved destination")
            numbers = [gap["n"]]
            while (parent := detail["steps"][numbers[-1] - 1]["parent"]) is not None:
                numbers.append(parent)
            numbers.reverse()
            file, _, line = write["site"].rpartition(":")
            source = (self.project / file).read_text().splitlines()[int(line) - 1]
            correction = {"step": gap["n"], "site": write["site"], "text": source, "to": "store:web state/theme"}
            decision = {"card_id": card["card_id"], "steps": numbers, "data": ["stato"] * len(numbers),
                        "name": "Pagamento della spesa", "area": "pagamenti e abbonamenti", "types": ["funzionale"],
                        "corrections": [correction]}
            self.assertEqual(traces.record(self.manifest, self.rules, decision)["status"], "refused")
            self.assertIsNone(traces.system_map.load(self.manifest, self.rules))
            correction["to"] = write["to"]
            self.assertEqual(traces.record(self.manifest, self.rules, decision)["status"], "accepted")
            saved = traces.system_map.load(self.manifest, self.rules)["flows"][0]
            self.assertEqual(saved["trace"]["steps"][-1], write)

    def test_record_retry_and_reopen_keep_the_exact_control_and_link(self):
        import shutil
        from test_codebase_map_system_map import fixture
        fixture(self)
        self.addCleanup(shutil.rmtree, self.work)
        cards = traces.page(self.manifest, self.rules, limit=100)["cards"]
        card = next(c for c in cards if c["handler"] == "web/checkout.ts::onPayClick")
        first = traces.page(self.manifest, self.rules, card_id=card["card_id"], limit=100)
        effect = next(s for s in first["steps"] if s["to"] == "store:web state/payment")
        numbers = [effect["n"]]
        while (parent := first["steps"][numbers[-1] - 1]["parent"]) is not None:
            numbers.append(parent)
        numbers.reverse()
        decision = {"card_id": card["card_id"], "steps": numbers, "data": ["stato"] * len(numbers),
                    "name": "Pagamento della spesa", "area": "pagamenti e abbonamenti", "types": ["funzionale"]}
        with mock.patch.object(traces, "_inventory", side_effect=AssertionError("repeat inventory")), \
             mock.patch.object(traces, "_steps", side_effect=AssertionError("repeat walk")):
            self.assertEqual(traces.record(self.manifest, self.rules, decision)["status"], "accepted")
            self.assertEqual(traces.record(self.manifest, self.rules, decision)["status"], "accepted")
            self.assertEqual(traces.next_question(self.manifest, self.rules)["reviewed"]["accepted"], 1)
            after = traces.page(self.manifest, self.rules, card_id=card["card_id"], limit=100)
        self.assertEqual(first["steps"], after["steps"])
        saved = traces.system_map.load(self.manifest, self.rules)["flows"][0]
        self.assertEqual((saved["trace"]["card_id"], saved["reachability"]), (card["card_id"], "verified"))
        # An older map client can resave an unchanged decision. Editing its
        # meaning reopens the question until those precise steps are named again.
        ordinary = {"scope": [saved["area"]], "flows": [
            {**{k: saved[k] for k in ("name", "area", "nodes", "types", "entries", "effects")},
             "arrows": [{k: a[k] for k in ("from", "to", "data")} for a in saved["arrows"]]}]}
        traces.system_map.record(self.manifest, self.rules, ordinary)
        again = traces.system_map.load(self.manifest, self.rules)["flows"][0]
        self.assertEqual(again["trace"], saved["trace"])
        ordinary["flows"][0]["arrows"][0]["data"] = "un altro dato"
        traces.system_map.record(self.manifest, self.rules, ordinary)
        revised = traces.system_map.load(self.manifest, self.rules)["flows"][0]
        self.assertEqual((revised["status"], revised["trace_review"]["card_id"]), ("incomplete", card["card_id"]))
        self.assertEqual(traces.next_question(self.manifest, self.rules)["reviewed"]["accepted"], 0)
        self.assertEqual(traces.record(self.manifest, self.rules, decision)["status"], "accepted")
        # Same members, direction and file, a different call site. The nearby link is insufficient.
        links = traces.flows.cached_links(self.manifest, self.rules)
        first_edge = saved["trace"]["steps"][0]
        next(e for e in links["edges"] if e == first_edge)["site"] = "web/checkout.ts:1"
        with mock.patch.object(traces.flows, "cached_links", side_effect=lambda *a, with_key=False: (None, links) if with_key else links):
            changed = traces.system_map.load(self.manifest, self.rules)["flows"][0]
        self.assertFalse(changed["fresh"])
        self.assertNotEqual(changed["reachability"], "verified")
        self.assertEqual(changed["arrows"][0]["status"], "refused")
