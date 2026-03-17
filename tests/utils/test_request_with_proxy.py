import requests
import sys
import unittest
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestRequestUrlWithProxy(unittest.TestCase):
    @patch("requests.get")
    def test_returns_response_on_success(self, mock_get):
        from ww.utils.request_with_proxy import request_url_with_proxy

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = request_url_with_proxy("http://example.com", {})
        self.assertEqual(result, mock_response)

    @patch("requests.get", side_effect=requests.RequestException("connection error"))
    def test_returns_none_on_exception(self, mock_get):
        from ww.utils.request_with_proxy import request_url_with_proxy

        result = request_url_with_proxy("http://example.com", {})
        self.assertIsNone(result)

    @patch("requests.get")
    def test_passes_proxy_to_requests(self, mock_get):
        from ww.utils.request_with_proxy import request_url_with_proxy

        mock_get.return_value = MagicMock(status_code=200)
        proxy = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        request_url_with_proxy("http://example.com", proxy)
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["proxies"], proxy)

    @patch("requests.get")
    def test_calls_raise_for_status(self, mock_get):
        from ww.utils.request_with_proxy import request_url_with_proxy

        mock_response = MagicMock()
        mock_get.return_value = mock_response
        request_url_with_proxy("http://example.com", {})
        mock_response.raise_for_status.assert_called_once()


class TestMain(unittest.TestCase):
    @patch("requests.get")
    def test_main_prints_status_and_content(self, mock_get):
        from ww.utils.request_with_proxy import main

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "A" * 200
        mock_get.return_value = mock_response

        with patch.object(sys, "argv", ["request-proxy", "http://example.com"]):
            with patch("builtins.print") as mock_print:
                main()
                output = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("200", output)
                self.assertIn("Content", output)

    @patch("requests.get", side_effect=requests.RequestException("fail"))
    def test_main_handles_request_failure(self, mock_get):
        from ww.utils.request_with_proxy import main

        with patch.object(sys, "argv", ["request-proxy", "http://example.com"]):
            with patch("builtins.print"):
                main()  # should not raise

    @patch("requests.get")
    def test_main_uses_proxy_flag(self, mock_get):
        from ww.utils.request_with_proxy import main

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "hello"
        mock_get.return_value = mock_response

        with patch.object(
            sys,
            "argv",
            ["request-proxy", "http://example.com", "--proxy", "http://127.0.0.1:7890"],
        ):
            main()
        _, kwargs = mock_get.call_args
        self.assertIn("http", kwargs["proxies"])


if __name__ == "__main__":
    unittest.main()
