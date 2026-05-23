import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestParseStatus(unittest.TestCase):
    def test_ac_power_charging(self):
        from ww.macos.charge_watcher import _parse_status

        output = "Now drawing from 'AC Power'\n-InternalBattery-0 (id=1234)\t100%; charging; 1:00 remaining\n"
        result = _parse_status(output)
        self.assertEqual(result["power_source"], "AC Power")
        self.assertEqual(result["charging_state"], "charging")
        self.assertEqual(result["percent"], 100)

    def test_battery_power_discharging(self):
        from ww.macos.charge_watcher import _parse_status

        output = "Now drawing from 'Battery Power'\n-InternalBattery-0 (id=1234)\t75%; discharging; 3:00 remaining\n"
        result = _parse_status(output)
        self.assertEqual(result["power_source"], "Battery Power")
        self.assertEqual(result["charging_state"], "discharging")
        self.assertEqual(result["percent"], 75)

    def test_ac_not_charging(self):
        from ww.macos.charge_watcher import _parse_status

        output = "Now drawing from 'AC Power'\n-InternalBattery-0 (id=1234)\t80%; not charging; 0:00 remaining\n"
        result = _parse_status(output)
        self.assertEqual(result["power_source"], "AC Power")
        self.assertEqual(result["charging_state"], "not charging")
        self.assertEqual(result["percent"], 80)

    def test_finishing_charge(self):
        from ww.macos.charge_watcher import _parse_status

        output = "Now drawing from 'AC Power'\n-InternalBattery-0 (id=1234)\t99%; finishing charge;\n"
        result = _parse_status(output)
        self.assertEqual(result["charging_state"], "charging")

    def test_unknown_format(self):
        from ww.macos.charge_watcher import _parse_status

        output = "some random output\n"
        result = _parse_status(output)
        self.assertEqual(result["power_source"], "Unknown")
        self.assertEqual(result["charging_state"], "unknown")
        self.assertEqual(result["percent"], -1)


class TestAlertState(unittest.TestCase):
    def test_not_charging_on_ac(self):
        from ww.macos.charge_watcher import _alert_state

        status = {
            "power_source": "AC Power",
            "charging_state": "not charging",
            "percent": 80,
        }
        self.assertEqual(_alert_state(status), "not_charging")

    def test_charging_on_ac(self):
        from ww.macos.charge_watcher import _alert_state

        status = {
            "power_source": "AC Power",
            "charging_state": "charging",
            "percent": 50,
        }
        self.assertEqual(_alert_state(status), "charging")

    def test_on_battery(self):
        from ww.macos.charge_watcher import _alert_state

        status = {
            "power_source": "Battery Power",
            "charging_state": "discharging",
            "percent": 60,
        }
        self.assertEqual(_alert_state(status), "battery")


class TestPmsetOutput(unittest.TestCase):
    @patch("ww.macos.charge_watcher.subprocess.run")
    def test_returns_stdout(self, mock_run):
        from ww.macos.charge_watcher import _pmset_output

        mock_run.return_value = MagicMock(stdout="battery info\n")
        result = _pmset_output()
        self.assertEqual(result, "battery info\n")
        mock_run.assert_called_once_with(
            ["pmset", "-g", "batt"], capture_output=True, text=True
        )


class TestNotify(unittest.TestCase):
    @patch("ww.macos.charge_watcher.subprocess.run")
    def test_calls_osascript(self, mock_run):
        from ww.macos.charge_watcher import _notify

        _notify("Title", "Message")
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "osascript")
        self.assertIn("Title", call_args[2])
        self.assertIn("Message", call_args[2])


class TestMain(unittest.TestCase):
    @patch("ww.macos.charge_watcher.time.sleep", side_effect=KeyboardInterrupt)
    @patch("ww.macos.charge_watcher._parse_status")
    @patch("ww.macos.charge_watcher._pmset_output")
    def test_main_stops_on_ctrl_c(self, mock_pmset, mock_parse, mock_sleep):
        from ww.macos.charge_watcher import main

        mock_pmset.return_value = "AC Power\n80%; charging\n"
        mock_parse.return_value = {
            "power_source": "AC Power",
            "charging_state": "charging",
            "percent": 80,
        }
        main()  # should not raise

    @patch("ww.macos.charge_watcher.time.sleep")
    @patch("ww.macos.charge_watcher._notify")
    @patch("ww.macos.charge_watcher._parse_status")
    @patch("ww.macos.charge_watcher._pmset_output")
    def test_not_charging_alert_after_ticks(
        self, mock_pmset, mock_parse, mock_notify, mock_sleep
    ):
        from ww.macos.charge_watcher import main, NOT_CHARGING_CONFIRM_TICKS

        not_charging_status = {
            "power_source": "AC Power",
            "charging_state": "not charging",
            "percent": 80,
        }
        mock_parse.return_value = not_charging_status
        mock_pmset.return_value = "output"

        call_count = [0]

        def sleep_side_effect(interval):
            call_count[0] += 1
            if call_count[0] >= NOT_CHARGING_CONFIRM_TICKS + 1:
                raise KeyboardInterrupt()

        mock_sleep.side_effect = sleep_side_effect

        main()
        mock_notify.assert_called()


if __name__ == "__main__":
    unittest.main()
