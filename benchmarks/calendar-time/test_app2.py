"""Each seed of app2/ is a real defect and each decoy is correct: these tests pass on the fixture as it is."""

import sys
import unittest
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent / "app2"))

import device  # noqa: E402
import planner  # noqa: E402
import server  # noqa: E402
from model import Rule, State, User  # noqa: E402

UTC = timezone.utc
DAILY = frozenset(range(7))
ROME, TOKYO, NEW_YORK = ZoneInfo("Europe/Rome"), ZoneInfo("Asia/Tokyo"), ZoneInfo("America/New_York")


class SeedTest(unittest.TestCase):
    def test_r1_push_and_local_alarm_resolve_the_fold_differently_and_both_ring(self):
        rule, user = Rule("r1", time(1, 30), DAILY), User(NEW_YORK, NEW_YORK)  # New York falls back on 1 November
        push = planner.next_occurrence(rule, datetime(2026, 10, 31, 12, tzinfo=UTC), NEW_YORK)
        alarms = device.local_alarms(rule, user, date(2026, 10, 31))
        self.assertEqual(push, datetime(2026, 11, 1, 5, 30, tzinfo=UTC))
        self.assertIn(datetime(2026, 11, 1, 6, 30, tzinfo=UTC), alarms)
        self.assertTrue(device.should_show_push(push, alarms))
        ordinary = planner.next_occurrence(rule, datetime(2026, 11, 1, 12, tzinfo=UTC), NEW_YORK)
        self.assertFalse(device.should_show_push(ordinary, alarms))

    def test_r2_weekday_is_taken_from_the_utc_instant(self):
        monday = Rule("r2", time(7), frozenset({0}))
        ring = planner.next_occurrence(monday, datetime(2026, 11, 8, 12, tzinfo=UTC), TOKYO)
        self.assertEqual(ring.astimezone(TOKYO).strftime("%a %H:%M"), "Tue 07:00")

    def test_r3_zone_change_rings_the_same_date_twice(self):
        rule, user, state = Rule("r3", time(9), DAILY), User(TOKYO, TOKYO), State()
        state.next_at["r3"] = datetime(2026, 11, 10, 0, tzinfo=UTC)  # 09:00 in Tokyo
        first = server.tick(datetime(2026, 11, 10, 0, tzinfo=UTC), user, [rule], state)
        server.on_zone_change(user, ROME, [rule], state, datetime(2026, 11, 10, 7, tzinfo=UTC))
        second = server.tick(datetime(2026, 11, 10, 8, tzinfo=UTC), user, [rule], state)
        self.assertEqual(first[0][1].astimezone(TOKYO).date(), date(2026, 11, 10))
        self.assertEqual(second[0][1].astimezone(ROME).date(), date(2026, 11, 10))

    def test_r4_today_uses_the_sign_up_zone(self):
        user = User(ROME, TOKYO)
        self.assertEqual(server.today(user, datetime(2026, 11, 9, 20, tzinfo=UTC)), date(2026, 11, 9))  # 05:00, 10 Nov in Tokyo

    def test_decoys_calendar_step_and_utc_instants_are_correct(self):
        rule = Rule("d", time(9), DAILY)
        ring = planner.next_occurrence(rule, datetime(2026, 3, 28, 8, tzinfo=UTC), ROME)  # Rome switches on 29 March
        self.assertEqual(ring.tzinfo, UTC)
        self.assertEqual(ring.astimezone(ROME).strftime("%d %H:%M"), "29 09:00")


if __name__ == "__main__":
    unittest.main()
