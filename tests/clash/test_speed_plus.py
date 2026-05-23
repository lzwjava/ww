import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGetAllProxyNames(unittest.TestCase):
    @patch("ww.clash.speed_plus.requests.get")
    def test_success_filters_groups(self, mock_get):
        from ww.clash.speed_plus import get_all_proxy_names

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "proxies": {
                "node1": {},
                "node2": {},
                "DIRECT": {},
                "REJECT": {},
                "GLOBAL": {},
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_all_proxy_names()
        self.assertIn("node1", result)
        self.assertIn("node2", result)
        self.assertNotIn("DIRECT", result)
        self.assertNotIn("REJECT", result)
        self.assertNotIn("GLOBAL", result)

    @patch("ww.clash.speed_plus.requests.get")
    def test_connection_error(self, mock_get):
        from ww.clash.speed_plus import get_all_proxy_names
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("refused")
        result = get_all_proxy_names()
        self.assertEqual(result, [])

    @patch("ww.clash.speed_plus.requests.get")
    def test_timeout(self, mock_get):
        from ww.clash.speed_plus import get_all_proxy_names
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("timeout")
        result = get_all_proxy_names()
        self.assertEqual(result, [])

    @patch("ww.clash.speed_plus.requests.get")
    def test_request_exception(self, mock_get):
        from ww.clash.speed_plus import get_all_proxy_names
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("err")
        result = get_all_proxy_names()
        self.assertEqual(result, [])


class TestTestProxyLatency(unittest.TestCase):
    @patch("ww.clash.speed_plus.requests.get")
    def test_success(self, mock_get):
        from ww.clash.speed_plus import test_proxy_latency

        mock_response = MagicMock()
        mock_response.json.return_value = {"delay": 250}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        name, url, latency = test_proxy_latency("proxy1", "https://www.google.com")
        self.assertEqual(name, "proxy1")
        self.assertEqual(url, "https://www.google.com")
        self.assertEqual(latency, 250)

    @patch("ww.clash.speed_plus.requests.get")
    def test_request_error(self, mock_get):
        from ww.clash.speed_plus import test_proxy_latency
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("fail")
        name, url, latency = test_proxy_latency("proxy1", "https://www.google.com")
        self.assertEqual(name, "proxy1")
        self.assertIsNone(latency)

    @patch("ww.clash.speed_plus.requests.get")
    def test_url_encoding(self, mock_get):
        from ww.clash.speed_plus import test_proxy_latency

        mock_response = MagicMock()
        mock_response.json.return_value = {"delay": 300}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        name, url, latency = test_proxy_latency("special proxy", "https://example.com")
        call_args = mock_get.call_args
        self.assertIn("special%20proxy", call_args[0][0])


class TestGetAverageLatency(unittest.TestCase):
    @patch("ww.clash.speed_plus.test_proxy_latency")
    def test_all_successful(self, mock_latency):
        from ww.clash.speed_plus import get_average_latency

        mock_latency.side_effect = [
            ("p1", "https://www.google.com", 100),
            ("p1", "https://www.youtube.com", 200),
            ("p1", "https://www.twitter.com", 300),
            ("p1", "https://github.com", 400),
            ("p1", "https://www.reddit.com", 500),
            ("p1", "https://grok.com", 600),
        ]
        result = get_average_latency("p1")
        self.assertAlmostEqual(result, 350.0)

    @patch("ww.clash.speed_plus.test_proxy_latency")
    def test_partial_success(self, mock_latency):
        from ww.clash.speed_plus import get_average_latency

        mock_latency.side_effect = [
            ("p1", "https://www.google.com", 100),
            ("p1", "https://www.youtube.com", None),
            ("p1", "https://www.twitter.com", 300),
            ("p1", "https://github.com", None),
            ("p1", "https://www.reddit.com", 500),
            ("p1", "https://grok.com", None),
        ]
        result = get_average_latency("p1")
        self.assertAlmostEqual(result, 300.0)

    @patch("ww.clash.speed_plus.test_proxy_latency")
    def test_all_failed(self, mock_latency):
        from ww.clash.speed_plus import get_average_latency

        mock_latency.side_effect = [
            ("p1", url, None)
            for url in [
                "https://www.google.com",
                "https://www.youtube.com",
                "https://www.twitter.com",
                "https://github.com",
                "https://www.reddit.com",
                "https://grok.com",
            ]
        ]
        result = get_average_latency("p1")
        self.assertIsNone(result)


class TestGetTopProxies(unittest.TestCase):
    @patch("ww.clash.speed_plus.get_average_latency")
    @patch("ww.clash.speed_plus.get_all_proxy_names")
    def test_returns_sorted(self, mock_names, mock_avg):
        from ww.clash.speed_plus import get_top_proxies

        mock_names.return_value = ["p1", "p2", "p3"]
        # Use a dict-based side_effect since ThreadPoolExecutor runs concurrently
        latency_map = {"p1": 300.0, "p2": 100.0, "p3": 200.0}
        mock_avg.side_effect = lambda name: latency_map[name]

        result = get_top_proxies(num_results=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "p2")
        self.assertAlmostEqual(result[0]["average_latency"], 100.0)

    @patch("ww.clash.speed_plus.get_all_proxy_names")
    def test_no_proxies(self, mock_names):
        from ww.clash.speed_plus import get_top_proxies

        mock_names.return_value = []
        result = get_top_proxies()
        self.assertEqual(result, [])

    @patch("ww.clash.speed_plus.get_average_latency")
    @patch("ww.clash.speed_plus.get_all_proxy_names")
    def test_all_failed(self, mock_names, mock_avg):
        from ww.clash.speed_plus import get_top_proxies

        mock_names.return_value = ["p1", "p2"]
        mock_avg.side_effect = [None, None]

        result = get_top_proxies()
        self.assertEqual(result, [])


class TestGenerateReport(unittest.TestCase):
    def test_with_results(self):
        from ww.clash.speed_plus import generate_report

        top = [
            {"name": "p1", "average_latency": 100.5},
            {"name": "p2", "average_latency": 200.3},
        ]
        generate_report(top)  # Should not raise

    def test_empty_results(self):
        from ww.clash.speed_plus import generate_report

        generate_report([])  # Should not raise


class TestMain(unittest.TestCase):
    @patch("ww.clash.speed_plus.get_top_proxies")
    def test_main(self, mock_top):
        from ww.clash.speed_plus import main

        mock_top.return_value = [
            {"name": "p1", "average_latency": 100.0},
        ]
        main()  # Should not raise

    @patch("ww.clash.speed_plus.get_top_proxies")
    def test_main_empty(self, mock_top):
        from ww.clash.speed_plus import main

        mock_top.return_value = []
        main()  # Should not raise


if __name__ == "__main__":
    unittest.main()
