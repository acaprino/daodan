"""Each seed of app/ is a real defect and each decoy is correct: these tests pass on the fixture as it is."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "app"))

import view  # noqa: E402
from log import Addition, Record  # noqa: E402
from plan import Dish, Slot  # noqa: E402

PASTA, SALAD = Dish("d1", "pasta", 600), Dish("d2", "salad", 150)
LUNCH = Slot("2026-11-09/lunch", (PASTA, SALAD))


class SeedTest(unittest.TestCase):
    def test_p1_a_free_addition_ticks_every_plan_dish_of_the_slot(self):
        records = {LUNCH.meal_id: Record(LUNCH.meal_id, (Addition("free", None, "apple", 80),))}
        self.assertTrue(view.dish_eaten(LUNCH, PASTA, records))
        self.assertTrue(view.dish_eaten(LUNCH, SALAD, records))

    def test_p2_nothing_logged_is_shown_as_skipped(self):
        self.assertTrue(view.skipped(LUNCH, {}))
        self.assertFalse(view.skipped(LUNCH, {LUNCH.meal_id: Record(LUNCH.meal_id, (Addition("free", None, "apple", 80),), skipped=True)}))

    def test_decoys_slot_badge_and_ring_are_correct(self):
        records = {LUNCH.meal_id: Record(LUNCH.meal_id, (Addition("planned", "d1", "pasta", 600),))}
        self.assertEqual(view.slot_badge(LUNCH, records), "logged")
        self.assertEqual(view.slot_badge(LUNCH, {LUNCH.meal_id: Record(LUNCH.meal_id, deleted=True)}), "empty")
        self.assertEqual(view.ring(records, 2000), 0.3)


if __name__ == "__main__":
    unittest.main()
