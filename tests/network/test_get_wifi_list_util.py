import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


from ww.network.get_wifi_list_util import (
    parse_nmcli_output,
    get_wifi_list,
    check_current_connection,
    test_wifi_connection as wifi_connect_fn,
    save_successful_connections,
)


class TestParseNmcliOutput(unittest.TestCase):
    def test_valid_output(self):
        output = (
            "SSID  BSSID  MODE  CHAN  FREQ  RATE  BANDWIDTH  SIGNAL  BARS  SECURITY  WPA-FLAGS  RSN-FLAGS  ACTIVE  IN-USE\n"
            "MyNet  AA:BB:CC:DD:EE:FF  Infra  6  2437 MHz  130 Mbit/s  40 MHz  80  ▂▄▆█  WPA2  --  --  no  --"
        )
        result = parse_nmcli_output(output)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["ssid"], "MyNet")
        self.assertEqual(result[0]["signal"], "80")

    def test_multiple_networks(self):
        output = (
            "SSID  BSSID  MODE  CHAN  FREQ  RATE  BANDWIDTH  SIGNAL  BARS  SECURITY  WPA-FLAGS  RSN-FLAGS  ACTIVE  IN-USE\n"
            "Net1  AA:BB:CC:DD:EE:01  Infra  1  2412 MHz  54 Mbit/s  20 MHz  70  ▂▄▆_  WPA2  --  --  no  --\n"
            "Net2  AA:BB:CC:DD:EE:02  Infra  11  2462 MHz  130 Mbit/s  40 MHz  90  ▂▄▆█  WPA2  --  --  yes  *"
        )
        result = parse_nmcli_output(output)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["ssid"], "Net1")
        self.assertEqual(result[1]["ssid"], "Net2")

    def test_empty_output(self):
        result = parse_nmcli_output("")
        self.assertEqual(result, [])

    def test_header_only(self):
        output = "SSID  BSSID  MODE  CHAN"
        result = parse_nmcli_output(output)
        self.assertEqual(result, [])

    def test_empty_line_skipped(self):
        output = (
            "SSID  BSSID  MODE  CHAN  FREQ  RATE  BANDWIDTH  SIGNAL  BARS  SECURITY  WPA-FLAGS  RSN-FLAGS  ACTIVE  IN-USE\n"
            "\n"
            "Net1  AA:BB:CC:DD:EE:01  Infra  1  2412 MHz  54 Mbit/s  20 MHz  70  ▂▄▆_  WPA2  --  --  no  --"
        )
        result = parse_nmcli_output(output)
        self.assertEqual(len(result), 1)


class TestGetWifiList(unittest.TestCase):
    @patch("ww.network.get_wifi_list_util.scan_wifi_with_nmcli")
    def test_nmcli_success(self, mock_nmcli):
        mock_nmcli.return_value = (
            "SSID  BSSID  MODE  CHAN  FREQ  RATE  BANDWIDTH  SIGNAL  BARS  SECURITY  WPA-FLAGS  RSN-FLAGS  ACTIVE  IN-USE\n"
            "Net1  AA:BB:CC:DD:EE:01  Infra  1  2412 MHz  54 Mbit/s  20 MHz  70  ▂▄▆_  WPA2  --  --  no  --"
        )
        result = get_wifi_list()
        self.assertEqual(len(result), 1)

    @patch("ww.network.get_wifi_list_util.scan_wifi_with_iwlist")
    @patch("ww.network.get_wifi_list_util.scan_wifi_with_iw")
    @patch("ww.network.get_wifi_list_util.scan_wifi_with_nmcli")
    def test_all_fail(self, mock_nmcli, mock_iw, mock_iwlist):
        mock_nmcli.return_value = None
        mock_iw.return_value = None
        mock_iwlist.return_value = None
        result = get_wifi_list()
        self.assertEqual(result, [])

    @patch("ww.network.get_wifi_list_util.scan_wifi_with_iw")
    @patch("ww.network.get_wifi_list_util.scan_wifi_with_nmcli")
    def test_nmcli_empty_fallback_iw(self, mock_nmcli, mock_iw):
        mock_nmcli.return_value = "SSID  BSSID"  # header only, no networks parsed
        mock_iw.return_value = "some iw output"
        result = get_wifi_list()
        self.assertEqual(result, [])


class TestCheckCurrentConnection(unittest.TestCase):
    @patch("ww.network.get_wifi_list_util.run_command")
    def test_nmcli_success(self, mock_run):
        mock_run.return_value = "wlan0  connected  MyNet"
        result = check_current_connection()
        self.assertIn("Network Status", result)
        self.assertIn("MyNet", result)

    @patch("ww.network.get_wifi_list_util.run_command")
    def test_iwconfig_fallback(self, mock_run):
        mock_run.side_effect = [None, 'wlan0  IEEE 802.11  ESSID:"Net"']
        result = check_current_connection()
        self.assertIn("IW Config", result)

    @patch("ww.network.get_wifi_list_util.run_command", return_value=None)
    def test_no_connection(self, mock_run):
        result = check_current_connection()
        self.assertIsNone(result)


class TestTestWifiConnection(unittest.TestCase):
    @patch("ww.network.get_wifi_list_util.get_wifi_interfaces", return_value=[])
    def test_no_interface(self, mock_ifaces):
        success, error = wifi_connect_fn("TestNet")
        self.assertFalse(success)
        self.assertIn("No WiFi interface", error)

    @patch("subprocess.run")
    @patch("ww.network.get_wifi_list_util.get_wifi_interfaces", return_value=["wlan0"])
    def test_successful_connection(self, mock_ifaces, mock_run):
        # delete, add, up, ping, cleanup calls
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        success, error = wifi_connect_fn("TestNet")
        self.assertTrue(success)
        self.assertIsNone(error)

    @patch("subprocess.run")
    @patch("ww.network.get_wifi_list_util.get_wifi_interfaces", return_value=["wlan0"])
    def test_activation_failure(self, mock_ifaces, mock_run):
        def side_effect(cmd, **kwargs):
            if "connection up" in cmd:
                return MagicMock(returncode=1, stderr="Activation failed", stdout="")
            return MagicMock(returncode=0, stderr="", stdout="")

        mock_run.side_effect = side_effect
        success, error = wifi_connect_fn("TestNet")
        self.assertFalse(success)
        self.assertIn("nmcli error", error)

    @patch("subprocess.run")
    @patch("ww.network.get_wifi_list_util.get_wifi_interfaces", return_value=["wlan0"])
    def test_wrong_password(self, mock_ifaces, mock_run):
        def side_effect(cmd, **kwargs):
            if "connection up" in cmd:
                return MagicMock(
                    returncode=1, stderr="Secrets were required", stdout=""
                )
            return MagicMock(returncode=0, stderr="", stdout="")

        mock_run.side_effect = side_effect
        success, error = wifi_connect_fn("TestNet", password="wrong")
        self.assertFalse(success)
        self.assertIn("Wrong password", error)

    @patch("subprocess.run")
    @patch("ww.network.get_wifi_list_util.get_wifi_interfaces", return_value=["wlan0"])
    def test_timeout(self, mock_ifaces, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="nmcli", timeout=30)
        success, error = wifi_connect_fn("TestNet")
        self.assertFalse(success)
        self.assertIn("timeout", error.lower())


class TestSaveSuccessfulConnections(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    def test_save_new_file(self, mock_makedirs, mock_exists, mock_file):
        networks = [
            {
                "ssid": "Net1",
                "bssid": "AA:BB",
                "mode": "Infra",
                "channel": "1",
                "frequency": "2412",
                "rate": "54",
                "bandwidth": "20",
                "signal": "70",
                "bars": "▂▄▆_",
                "security": "WPA2",
                "active": "no",
                "in_use": "--",
            }
        ]
        save_successful_connections(networks, "tmp/wifi.csv")
        mock_makedirs.assert_called_once()
        handle = mock_file()
        self.assertTrue(handle.write.call_count > 0)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    def test_save_existing_file(self, mock_makedirs, mock_exists, mock_file):
        networks = [
            {
                "ssid": "Net1",
                "bssid": "AA:BB",
                "mode": "Infra",
                "channel": "1",
                "frequency": "2412",
                "rate": "54",
                "bandwidth": "20",
                "signal": "70",
                "bars": "▂▄▆_",
                "security": "WPA2",
                "active": "no",
                "in_use": "--",
            }
        ]
        save_successful_connections(networks)
        mock_makedirs.assert_called_once()


if __name__ == "__main__":
    unittest.main()
