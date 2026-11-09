"""Each seed of app/reminders.py is a real defect: these tests pass while it is present."""

import sys
import unittest
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent / "app"))

import reminders as r  # noqa: E402

UTC = timezone.utc


def local_hhmm(instant, zone):
    return instant.astimezone(ZoneInfo(zone)).strftime("%H:%M")


class SeedTest(unittest.TestCase):
    def test_s1_card_and_ring_resolve_the_dst_gap_differently(self):
        user = r.User(ZoneInfo("Australia/Sydney"))
        day = date(2026, 10, 4)  # 02:00 -> 03:00
        rem = r.create("s1", time(2, 30), day, user)
        self.assertEqual(r.card(rem, day), "02:30 to do")
        self.assertEqual(local_hhmm(rem.next_at, "Australia/Sydney"), "03:30")

    def test_s2_recurrence_adds_24_hours_and_moves_the_wall_clock_time(self):
        user = r.User(ZoneInfo("Europe/Rome"))
        rem = r.create("s2", time(9), date(2026, 3, 28), user)  # Rome switches on 29 March
        r.tick(datetime(2026, 3, 28, 8, tzinfo=UTC), [rem])
        self.assertEqual(local_hhmm(rem.next_at, "Europe/Rome"), "10:00")

    def test_s3_zone_change_keeps_the_ring_planned_in_the_old_zone(self):
        user = r.User(ZoneInfo("Europe/Rome"))
        rem = r.create("s3", time(9), date(2026, 11, 10), user)
        r.set_zone(user, "Asia/Tokyo")
        self.assertEqual(local_hhmm(rem.next_at, "Asia/Tokyo"), "17:00")

    def test_s4_done_compares_the_utc_date_with_the_local_day(self):
        user = r.User(ZoneInfo("Asia/Tokyo"))
        day = date(2026, 11, 10)
        rem = r.create("s4", time(8), day, user)
        self.assertEqual(len(r.tick(datetime(2026, 11, 9, 23, tzinfo=UTC), [rem])), 1)  # 08:00 in Tokyo
        self.assertEqual(r.card(rem, day), "08:00 to do")

    def test_decoy_utc_instants_round_trip(self):
        user = r.User(ZoneInfo("Europe/Rome"))
        rem = r.create("d", time(9), date(2026, 11, 10), user)
        self.assertEqual(rem.next_at.tzinfo, UTC)
        self.assertEqual(local_hhmm(rem.next_at, "Europe/Rome"), "09:00")


if __name__ == "__main__":
    unittest.main()
