import os
import unittest
from unittest.mock import patch, MagicMock
import socket

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestIsHostUpByPort(unittest.TestCase):
    def test_open_port_returns_true(self):
        from ww.network.ip_scan import is_host_up_by_port

        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_instance

            result = is_host_up_by_port("192.168.1.1", 80)
            self.assertTrue(result)

    def test_closed_port_returns_false(self):
        from ww.network.ip_scan import is_host_up_by_port

        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 1
            mock_socket.return_value = mock_instance

            result = is_host_up_by_port("192.168.1.1", 80)
            self.assertFalse(result)

    def test_socket_error_returns_false(self):
        from ww.network.ip_scan import is_host_up_by_port

        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.side_effect = socket.error("Network error")
            mock_socket.return_value = mock_instance

            result = is_host_up_by_port("192.168.1.1", 80)
            self.assertFalse(result)


class TestIsHostUpByPing(unittest.TestCase):
    def test_successful_ping_returns_true(self):
        from ww.network.ip_scan import is_host_up_by_ping

        with patch("subprocess.check_output", return_value=b""):
            result = is_host_up_by_ping("192.168.1.1")
            self.assertTrue(result)

    def test_failed_ping_returns_false(self):
        from ww.network.ip_scan import is_host_up_by_ping
        import subprocess

        with patch(
            "subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "ping"),
        ):
            result = is_host_up_by_ping("192.168.1.1")
            self.assertFalse(result)


class TestIsHostUp(unittest.TestCase):
    def test_uses_port_when_specified(self):
        from ww.network.ip_scan import is_host_up

        with patch(
            "ww.network.ip_scan.is_host_up_by_port", return_value=True
        ) as mock_port:
            with patch("ww.network.ip_scan.is_host_up_by_ping") as mock_ping:
                result = is_host_up("192.168.1.1", port=80)
                self.assertTrue(result)
                mock_port.assert_called_once_with("192.168.1.1", 80)
                mock_ping.assert_not_called()

    def test_uses_ping_when_no_port(self):
        from ww.network.ip_scan import is_host_up

        with patch(
            "ww.network.ip_scan.is_host_up_by_ping", return_value=True
        ) as mock_ping:
            with patch("ww.network.ip_scan.is_host_up_by_port") as mock_port:
                result = is_host_up("192.168.1.1")
                self.assertTrue(result)
                mock_ping.assert_called_once_with("192.168.1.1")
                mock_port.assert_not_called()


class TestScanIp(unittest.TestCase):
    def test_up_host_append_to_list(self):
        from ww.network.ip_scan import scan_ip

        with patch("ww.network.ip_scan.is_host_up", return_value=True):
            up_ips = []
            scan_ip("192.168.1.1", up_ips)
            self.assertIn("192.168.1.1", up_ips)

    def test_down_host_not_in_list(self):
        from ww.network.ip_scan import scan_ip

        with patch("ww.network.ip_scan.is_host_up", return_value=False):
            up_ips = []
            scan_ip("192.168.1.1", up_ips)
            self.assertNotIn("192.168.1.1", up_ips)


class TestScanNetwork(unittest.TestCase):
    def test_returns_list_of_up_ips(self):
        from ww.network.ip_scan import scan_network

        with patch("ww.network.ip_scan.is_host_up") as mock_is_up:
            mock_is_up.side_effect = lambda ip, port=None: ip == "192.168.1.1"

            result = scan_network("192.168.1.0/29")
            self.assertEqual(result, ["192.168.1.1"])

    def test_empty_when_all_down(self):
        from ww.network.ip_scan import scan_network

        with patch("ww.network.ip_scan.is_host_up", return_value=False):
            result = scan_network("192.168.1.0/30")
            self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
