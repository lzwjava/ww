import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestRunCommand(unittest.TestCase):
    def test_successful_command_returns_output(self):
        from ww.network.wifi_util import run_command

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout.strip.return_value = "eth0"
            mock_run.return_value = mock_result

            result = run_command("echo hello")
            self.assertEqual(result, "eth0")

    def test_failed_command_returns_fallback(self):
        from ww.network.wifi_util import run_command

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            result = run_command("invalid_command", fallback="default")
            self.assertEqual(result, "default")

    def test_exception_returns_fallback(self):
        from ww.network.wifi_util import run_command
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.SubprocessError("error")):
            result = run_command("bad_cmd", fallback="fallback_value")
            self.assertEqual(result, "fallback_value")


class TestGetWifiInterfaces(unittest.TestCase):
    def test_returns_interfaces_from_iw(self):
        from ww.network.wifi_util import get_wifi_interfaces

        with patch("ww.network.wifi_util.run_command") as mock_run:
            mock_run.side_effect = ["wlan0", None, None]

            result = get_wifi_interfaces()
            self.assertIn("wlan0", result)

    def test_returns_empty_list_when_no_interfaces(self):
        from ww.network.wifi_util import get_wifi_interfaces

        with patch("ww.network.wifi_util.run_command", return_value=None):
            result = get_wifi_interfaces()
            self.assertEqual(result, [])

    def test_removes_duplicates(self):
        from ww.network.wifi_util import get_wifi_interfaces

        with patch("ww.network.wifi_util.run_command") as mock_run:
            mock_run.side_effect = ["wlan0", "wlan0", None, None]

            result = get_wifi_interfaces()
            self.assertEqual(result.count("wlan0"), 1)


class TestScanWifiWithNmcli(unittest.TestCase):
    def test_returns_scan_result(self):
        from ww.network.wifi_util import scan_wifi_with_nmcli

        with patch("ww.network.wifi_util.run_command") as mock_run:
            mock_run.side_effect = [True, "SSID: TestNetwork"]

            scan_result = scan_wifi_with_nmcli()
            assert scan_result is not None
            self.assertIn("SSID", scan_result)

    def test_returns_none_when_scan_fails(self):
        from ww.network.wifi_util import scan_wifi_with_nmcli

        with patch("ww.network.wifi_util.run_command", return_value=None):
            result = scan_wifi_with_nmcli()
            self.assertIsNone(result)


class TestScanWifiWithIw(unittest.TestCase):
    def test_returns_networks_when_interfaces_exist(self):
        from ww.network.wifi_util import scan_wifi_with_iw

        with patch("ww.network.wifi_util.get_wifi_interfaces", return_value=["wlan0"]):
            with patch("ww.network.wifi_util.run_command") as mock_run:
                mock_run.return_value = "SSID: TestNet"

                scan_result = scan_wifi_with_iw()
                assert scan_result is not None
                self.assertIn("Interface: wlan0", scan_result)

    def test_returns_none_when_no_interfaces(self):
        from ww.network.wifi_util import scan_wifi_with_iw

        with patch("ww.network.wifi_util.get_wifi_interfaces", return_value=[]):
            result = scan_wifi_with_iw()
            self.assertIsNone(result)


class TestScanWifiWithIwlist(unittest.TestCase):
    def test_returns_networks_when_interfaces_exist(self):
        from ww.network.wifi_util import scan_wifi_with_iwlist

        with patch("ww.network.wifi_util.get_wifi_interfaces", return_value=["wlan0"]):
            with patch("ww.network.wifi_util.run_command") as mock_run:
                mock_run.return_value = "SSID: TestNet"

                scan_result = scan_wifi_with_iwlist()
                assert scan_result is not None
                self.assertIn("Interface: wlan0", scan_result)

    def test_returns_none_when_no_interfaces(self):
        from ww.network.wifi_util import scan_wifi_with_iwlist

        with patch("ww.network.wifi_util.get_wifi_interfaces", return_value=[]):
            result = scan_wifi_with_iwlist()
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
