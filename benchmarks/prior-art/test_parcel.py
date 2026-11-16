"""Ogni seme di parcel/ esiste e ogni esca è corretta: i test passano sulla fixture così com'è."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parcel import billing, dispatch, labels, legacy, parcels, tracking, webhook  # noqa: E402

OLD = {"id": "v1", "dest": "Ada Rossi, 20 121", "grams": 900}


class Base(unittest.TestCase):
    def setUp(self):
        parcels.PARCELS.clear()
        billing.BALANCE["acme"] = 100.0
        parcels.create("p1", "Bo Neri", "10 100", 1500)
        legacy.load([OLD])


def refusal(call):
    try:
        call()
    except ValueError as exc:
        return str(exc)
    return None


class SeedTest(Base):
    def test_t1_the_webhook_guard_refuses_what_add_event_refuses_with_the_same_message(self):
        self.assertEqual(
            refusal(lambda: webhook.on_event({"parcel": "nessuna", "status": "in_transit"})),
            refusal(lambda: tracking.add_event("nessuna", "in_transit")),
        )

    def test_t2_every_status_the_webhook_refuses_is_refused_by_add_event_with_the_same_message(self):
        for status in ("perso", "created", ""):
            self.assertEqual(
                refusal(lambda: webhook.on_event({"parcel": "p1", "status": status})),
                refusal(lambda: tracking.add_event("p1", status)),
            )
        self.assertIsNotNone(refusal(lambda: tracking.add_event("p1", "delivered")))

    def test_t2_is_not_contained_a_missing_status_on_a_delivered_parcel_passes_add_event(self):
        tracking.add_event("p1", "in_transit")
        tracking.add_event("p1", "delivered")
        self.assertEqual(refusal(lambda: webhook.on_event({"parcel": "p1", "status": None})), "passaggio non ammesso")
        self.assertIsNone(refusal(lambda: tracking.add_event("p1", None)))
        self.assertIsNone(parcels.PARCELS["p1"]["status"])

    def test_t3_every_producer_writes_a_list_of_events(self):
        tracking.add_event("p1", "in_transit")
        for parcel in parcels.PARCELS.values():
            self.assertIs(labels._history(parcel), parcel["events"])

    def test_t4_the_label_statuses_copy_the_states_tracking_can_reach(self):
        self.assertEqual(set(labels.STATUSES), {"created", *tracking.NEXT.values()})
        tracking.add_event("p1", "in_transit")
        tracking.add_event("p1", "delivered")
        for parcel in parcels.PARCELS.values():
            self.assertIn(parcel["status"], labels.STATUSES)


class DecoyTest(Base):
    def test_d1_the_old_system_writes_the_recipient_as_text_and_the_label_reads_both(self):
        self.assertIsInstance(parcels.PARCELS["v1"]["recipient"], str)
        self.assertEqual(labels.text("v1"), "Ada Rossi | 20121 | 0.9 kg | created")
        self.assertEqual(labels.text("p1"), "Bo Neri | 10100 | 1.5 kg | created")

    def test_d2_the_check_before_the_charge_keeps_the_money_when_the_step_is_refused(self):
        dispatch.ship("p1", "acme")
        self.assertEqual(billing.BALANCE["acme"], 92.5)
        self.assertEqual(refusal(lambda: dispatch.ship("p1", "acme")), "passaggio non ammesso")
        self.assertEqual(billing.BALANCE["acme"], 92.5)
        billing.charge("acme")
        self.assertEqual(refusal(lambda: tracking.add_event("p1", "in_transit")), "passaggio non ammesso")
        self.assertEqual(billing.BALANCE["acme"], 85.0)


if __name__ == "__main__":
    unittest.main()
