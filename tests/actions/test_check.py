import unittest
from datetime import datetime, timezone, timedelta

from ww.actions.check import _parse_time, _time_ago, _status_icon, STATUS_ICONS


class TestParseTime(unittest.TestCase):
    def test_valid_iso(self):
        result = _parse_time("2024-06-15T10:30:00Z")
        assert result is not None
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 6)
        self.assertEqual(result.hour, 10)

    def test_none(self):
        self.assertIsNone(_parse_time(None))

    def test_empty_string(self):
        self.assertIsNone(_parse_time(""))

    def test_with_offset(self):
        result = _parse_time("2024-01-01T00:00:00+05:30")
        assert result is not None
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)


class TestTimeAgo(unittest.TestCase):
    def test_none(self):
        self.assertEqual(_time_ago(None), "?")

    def test_seconds_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(seconds=30)
        result = _time_ago(dt)
        self.assertRegex(result, r"\d+s ago")

    def test_minutes_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(minutes=5)
        result = _time_ago(dt)
        self.assertRegex(result, r"\d+m ago")

    def test_hours_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(hours=3)
        result = _time_ago(dt)
        self.assertRegex(result, r"\d+h ago")

    def test_days_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(days=2)
        result = _time_ago(dt)
        self.assertRegex(result, r"\d+d ago")


class TestStatusIcon(unittest.TestCase):
    def test_success(self):
        icon = _status_icon("success")
        self.assertIn("✓", icon)

    def test_failure(self):
        icon = _status_icon("failure")
        self.assertIn("✗", icon)

    def test_cancelled(self):
        icon = _status_icon("cancelled")
        self.assertIn("○", icon)

    def test_none_conclusion(self):
        icon = _status_icon(None)
        self.assertIn("⟳", icon)

    def test_unknown_conclusion(self):
        icon = _status_icon("timed_out")
        self.assertIn("?", icon)

    def test_all_status_icons_present(self):
        for status in [
            "success",
            "failure",
            "cancelled",
            "in_progress",
            "queued",
            "skipped",
        ]:
            self.assertIn(status, STATUS_ICONS)


if __name__ == "__main__":
    unittest.main()
