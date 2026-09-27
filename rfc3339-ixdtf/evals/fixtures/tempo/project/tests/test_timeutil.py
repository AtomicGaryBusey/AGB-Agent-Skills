import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import timeutil  # noqa: E402

NY = ZoneInfo("America/New_York")


class FormatTests(unittest.TestCase):
    def test_instant_is_millisecond_utc(self):
        dt = datetime(2026, 3, 14, 9, 30, 5, 987654, tzinfo=NY)
        self.assertEqual(timeutil.format_instant(dt), "2026-03-14T13:30:05.987Z")

    def test_instant_rejects_naive(self):
        with self.assertRaises(ValueError):
            timeutil.format_instant(datetime(2026, 3, 14, 9, 30))

    def test_ixdtf_includes_zone_and_calendar(self):
        dt = datetime(2026, 3, 14, 9, 30, tzinfo=NY)
        self.assertEqual(
            timeutil.format_ixdtf(dt, calendar="hebrew"),
            "2026-03-14T09:30:00-04:00[America/New_York][u-ca=hebrew]",
        )

    def test_reminder_is_minute_precision(self):
        dt = datetime(2026, 3, 14, 9, 15, 42, tzinfo=NY)
        self.assertEqual(timeutil.format_reminder(dt), "2026-03-14T09:15-04:00")


class ParseTests(unittest.TestCase):
    def test_offset_roundtrip(self):
        dt = timeutil.parse_timestamp("1996-12-19T16:39:57-08:00")
        self.assertEqual(dt.astimezone(timezone.utc),
                         datetime(1996, 12, 20, 0, 39, 57, tzinfo=timezone.utc))

    def test_fraction_and_lowercase(self):
        dt = timeutil.parse_timestamp("1985-04-12t23:20:50.52z")
        self.assertEqual(dt.microsecond, 520000)
        self.assertEqual(dt.utcoffset(), timedelta(0))

    def test_rejects_impossible_date(self):
        with self.assertRaises(ValueError):
            timeutil.parse_timestamp("2023-02-30T10:00:00Z")

    def test_ixdtf_first_calendar_wins(self):
        stamp = timeutil.parse_ixdtf(
            "2022-07-08T00:14:07Z[Europe/Paris][u-ca=chinese][u-ca=japanese]")
        self.assertEqual(stamp.zone, "Europe/Paris")
        self.assertEqual(stamp.calendar, "chinese")

    def test_ixdtf_critical_zone_inconsistency(self):
        with self.assertRaises(ValueError):
            timeutil.parse_ixdtf("2022-07-08T00:14:07+00:00[!Europe/London]")

    def test_ixdtf_z_with_critical_zone_is_consistent(self):
        stamp = timeutil.parse_ixdtf("2022-07-08T00:14:07Z[!Europe/London]")
        self.assertEqual(stamp.zone, "Europe/London")


if __name__ == "__main__":
    unittest.main()
