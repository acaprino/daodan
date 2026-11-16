"""Ogni seme di booking/ esiste e ogni esca è corretta: i test passano sulla fixture così com'è."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from booking import bookings, imports, mail, recurring, slots, view  # noqa: E402

ROW = {"room": "aula-1", "day": "lun", "start": 9, "end": 11, "owner": "ada", "people": 4}


class Base(unittest.TestCase):
    def setUp(self):
        bookings.BOOKINGS.clear()


class SeedTest(Base):
    def test_r1_the_button_offers_an_extension_the_rule_refuses(self):
        booking = bookings.create("aula-1", "lun", 9, 12, "ada")
        self.assertTrue(view.can_extend(booking))
        with self.assertRaises(ValueError):
            bookings.extend(booking["id"])

    def test_r2_the_mail_title_equals_the_calendar_label(self):
        for room, start, end in (("aula-1", 9, 11), ("sala-blu", 0, 24), ("x", 7, 8)):
            booking = {"room": room, "start": start, "end": end}
            self.assertEqual(mail._title(booking), view.label(booking))

    def test_r3_import_and_create_store_the_same_record_and_refuse_the_same_clash(self):
        imported = imports.load([dict(ROW)])[0]
        with self.assertRaises(ValueError):
            imports.load([dict(ROW)])
        self.setUp()
        created = bookings.create(ROW["room"], ROW["day"], ROW["start"], ROW["end"], ROW["owner"], ROW["people"])
        with self.assertRaises(ValueError):
            bookings.create(ROW["room"], ROW["day"], ROW["start"], ROW["end"], ROW["owner"], ROW["people"])
        self.assertEqual(imported, created)

    def test_r4_the_series_refuses_what_create_refuses_with_the_same_message(self):
        for room, end in (("aula-1", 13), ("nessuna", 10)):
            messages = []
            for call in (
                lambda: recurring.book_weekly(room, ["lun"], 9, end, "ada"),
                lambda: bookings.create(room, "lun", 9, end, "ada"),
            ):
                with self.assertRaises(ValueError) as raised:
                    call()
                messages.append(str(raised.exception))
            self.assertEqual(messages[0], messages[1])

    def test_r5_every_producer_writes_the_owner(self):
        records = [bookings.create("aula-1", "lun", 9, 11, "ada"), imports.load([{**ROW, "day": "mar"}])[0]]
        for record in records:
            self.assertEqual(mail._owner(record), record["owner"])


class DecoyTest(Base):
    def test_f1_touching_slots_do_not_overlap_but_leave_no_cleaning_hour(self):
        first, second = {"start": 9, "end": 11}, {"start": 11, "end": 12}
        self.assertFalse(slots.overlap(first, second))
        self.assertTrue(slots.needs_gap(first, second))

    def test_f2_the_sender_default_is_the_documented_one(self):
        self.assertEqual(mail.SENDER, os.environ.get("ROOMS_SENDER", "sale@example.org"))


if __name__ == "__main__":
    unittest.main()
