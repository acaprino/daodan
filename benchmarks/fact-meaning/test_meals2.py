"""Each seed of app2/ is a real defect and each decoy is correct."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "app2"))

import diary  # noqa: E402
import today  # noqa: E402
import week  # noqa: E402
from diary_store import DiaryStore  # noqa: E402
from plan_store import Dish, PlanSlot, PlanStore  # noqa: E402

PASTA, SALAD = Dish("d1", "pasta", 600), Dish("d2", "salad", 150)
LUNCH = PlanSlot("2026-11-09/lunch", (PASTA, SALAD))


class SeedTest(unittest.TestCase):
    def test_q1_a_free_food_checks_the_plan_dishes(self):
        store = DiaryStore()
        diary.add_food(store, LUNCH.meal_id, "apple", 80)
        self.assertEqual(today.rows(LUNCH, store), [("pasta", True), ("salad", True)])

    def test_q2_adherence_counts_free_food(self):
        plan, store = PlanStore(), DiaryStore()
        plan.put(LUNCH)
        diary.add_food(store, LUNCH.meal_id, "apple", 80)
        self.assertEqual(week.adherence(plan, store, ["2026-11-09"]), 1.0)

    def test_decoys_slot_kcal_and_planned_hook(self):
        store = DiaryStore()
        diary.log_planned(store, LUNCH.meal_id, PASTA)
        diary.add_food(store, LUNCH.meal_id, "apple", 80)
        self.assertEqual(today.slot_kcal(LUNCH, store), 680)
        self.assertEqual(store.entries[LUNCH.meal_id].additions[0].dish_id, "d1")


if __name__ == "__main__":
    unittest.main()
