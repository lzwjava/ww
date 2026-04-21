import os
import socket
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestIsPortOpen(unittest.TestCase):
    def test_open_port_returns_true(self):
        from ww.network.port_scan import is_port_open

        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_instance

            result = is_port_open("localhost", 80)
            self.assertTrue(result)
            mock_instance.settimeout.assert_called_once_with(1)
            mock_instance.close.assert_called_once()

    def test_closed_port_returns_false(self):
        from ww.network.port_scan import is_port_open

        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 1
            mock_socket.return_value = mock_instance

            result = is_port_open("localhost", 80)
            self.assertFalse(result)

    def test_socket_error_returns_false(self):
        from ww.network.port_scan import is_port_open

        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.side_effect = socket.error("Network error")
            mock_socket.return_value = mock_instance

            result = is_port_open("localhost", 80)
            self.assertFalse(result)


class TestScanPort(unittest.TestCase):
    def test_scan_open_port_appends_to_open_ports(self):
        from ww.network.port_scan import scan_port

        with patch("ww.network.port_scan.is_port_open", return_value=True):
            open_ports = []
            scan_port("localhost", 80, open_ports)
            self.assertIn(80, open_ports)

    def test_scan_closed_port_does_not_append(self):
        from ww.network.port_scan import scan_port

        with patch("ww.network.port_scan.is_port_open", return_value=False):
            open_ports = []
            scan_port("localhost", 80, open_ports)
            self.assertNotIn(80, open_ports)


class TestScanPorts(unittest.TestCase):
    def test_returns_list_of_open_ports(self):
        from ww.network.port_scan import scan_ports

        with patch("ww.network.port_scan.is_port_open") as mock_is_open:
            mock_is_open.side_effect = lambda h, p: p == 80

            result = scan_ports("localhost", 79, 81)
            self.assertEqual(result, [80])

    def test_returns_empty_when_all_closed(self):
        from ww.network.port_scan import scan_ports

        with patch("ww.network.port_scan.is_port_open", return_value=False):
            result = scan_ports("localhost", 1, 5)
            self.assertEqual(result, [])

    def test_returns_multiple_open_ports(self):
        from ww.network.port_scan import scan_ports

        with patch("ww.network.port_scan.is_port_open") as mock_is_open:
            mock_is_open.side_effect = lambda h, p: p in (80, 443)

            result = scan_ports("localhost", 80, 443)
            self.assertEqual(result, [80, 443])


if __name__ == "__main__":
    unittest.main()
