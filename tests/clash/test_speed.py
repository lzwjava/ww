import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGetAllProxyNames(unittest.TestCase):
    @patch("ww.clash.speed.requests.get")
    def test_success(self, mock_get):
        from ww.clash.speed import get_all_proxy_names

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "proxies": {
                "proxy1": {},
                "proxy2": {},
                "DIRECT": {},
                "REJECT": {},
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_all_proxy_names()
        self.assertIn("proxy1", result)
        self.assertIn("proxy2", result)
        self.assertNotIn("DIRECT", result)
        self.assertNotIn("REJECT", result)

    @patch("ww.clash.speed.requests.get")
    def test_connection_error(self, mock_get):
        from ww.clash.speed import get_all_proxy_names
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("refused")
        result = get_all_proxy_names()
        self.assertEqual(result, [])

    @patch("ww.clash.speed.requests.get")
    def test_timeout(self, mock_get):
        from ww.clash.speed import get_all_proxy_names
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("timeout")
        result = get_all_proxy_names()
        self.assertEqual(result, [])

    @patch("ww.clash.speed.requests.get")
    def test_request_exception(self, mock_get):
        from ww.clash.speed import get_all_proxy_names
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("error")
        result = get_all_proxy_names()
        self.assertEqual(result, [])

    @patch("ww.clash.speed.requests.get")
    def test_empty_proxies(self, mock_get):
        from ww.clash.speed import get_all_proxy_names

        mock_response = MagicMock()
        mock_response.json.return_value = {"proxies": {}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_all_proxy_names()
        self.assertEqual(result, [])


class TestTestProxyLatency(unittest.TestCase):
    @patch("ww.clash.speed.requests.get")
    def test_success(self, mock_get):
        from ww.clash.speed import test_proxy_latency

        mock_response = MagicMock()
        mock_response.json.return_value = {"delay": 150}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        name, latency = test_proxy_latency("proxy1")
        self.assertEqual(name, "proxy1")
        self.assertEqual(latency, 150)

    @patch("ww.clash.speed.requests.get")
    def test_request_error(self, mock_get):
        from ww.clash.speed import test_proxy_latency
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("fail")
        name, latency = test_proxy_latency("proxy1")
        self.assertEqual(name, "proxy1")
        self.assertIsNone(latency)

    @patch("ww.clash.speed.requests.get")
    def test_url_encoding(self, mock_get):
        from ww.clash.speed import test_proxy_latency

        mock_response = MagicMock()
        mock_response.json.return_value = {"delay": 200}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        name, latency = test_proxy_latency("proxy with spaces")
        self.assertEqual(name, "proxy with spaces")
        # Verify URL was encoded properly
        call_args = mock_get.call_args
        self.assertIn("proxy%20with%20spaces", call_args[0][0])


class TestGetTopProxies(unittest.TestCase):
    @patch("ww.clash.speed.test_proxy_latency")
    @patch("ww.clash.speed.get_all_proxy_names")
    def test_returns_sorted_top_n(self, mock_names, mock_latency):
        from ww.clash.speed import get_top_proxies

        mock_names.return_value = ["p1", "p2", "p3"]
        # Use dict-based side_effect since ThreadPoolExecutor runs concurrently
        latency_map = {"p1": 300, "p2": 100, "p3": 200}
        mock_latency.side_effect = lambda name: (name, latency_map[name])

        result = get_top_proxies(num_results=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "p2")
        self.assertEqual(result[0]["latency"], 100)
        self.assertEqual(result[1]["name"], "p3")
        self.assertEqual(result[1]["latency"], 200)

    @patch("ww.clash.speed.get_all_proxy_names")
    def test_no_proxies(self, mock_names):
        from ww.clash.speed import get_top_proxies

        mock_names.return_value = []
        result = get_top_proxies()
        self.assertEqual(result, [])

    @patch("ww.clash.speed.test_proxy_latency")
    @patch("ww.clash.speed.get_all_proxy_names")
    def test_all_failed(self, mock_names, mock_latency):
        from ww.clash.speed import get_top_proxies

        mock_names.return_value = ["p1", "p2"]
        mock_latency.side_effect = lambda name: (name, None)

        result = get_top_proxies()
        self.assertEqual(result, [])

    @patch("ww.clash.speed.test_proxy_latency")
    @patch("ww.clash.speed.get_all_proxy_names")
    def test_name_filter(self, mock_names, mock_latency):
        from ww.clash.speed import get_top_proxies

        mock_names.return_value = ["us-east-1", "us-west-2", "jp-1", "uk-1"]
        latency_map = {"us-east-1": 100, "us-west-2": 200}
        mock_latency.side_effect = lambda name: (name, latency_map.get(name))

        result = get_top_proxies(num_results=5, name_filter=["us"])
        self.assertEqual(len(result), 2)

    @patch("ww.clash.speed.get_all_proxy_names")
    def test_name_filter_no_match(self, mock_names):
        from ww.clash.speed import get_top_proxies

        mock_names.return_value = ["p1", "p2"]
        result = get_top_proxies(name_filter=["nonexistent"])
        self.assertEqual(result, [])


class TestMain(unittest.TestCase):
    @patch("ww.clash.speed.get_top_proxies")
    def test_main_with_results(self, mock_top):
        from ww.clash.speed import main

        mock_top.return_value = [
            {"name": "p1", "latency": 100},
            {"name": "p2", "latency": 200},
        ]
        main()  # Should not raise

    @patch("ww.clash.speed.get_top_proxies")
    def test_main_no_results(self, mock_top):
        from ww.clash.speed import main

        mock_top.return_value = []
        main()  # Should not raise


if __name__ == "__main__":
    unittest.main()
