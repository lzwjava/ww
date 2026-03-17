import unittest
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestCallOpenrouterApi(unittest.TestCase):
    def setUp(self):
        from ww.github import gitmessageai

        self._orig_key = gitmessageai.OPENROUTER_API_KEY
        gitmessageai.OPENROUTER_API_KEY = "test-key"

    def tearDown(self):
        from ww.github import gitmessageai

        gitmessageai.OPENROUTER_API_KEY = self._orig_key

    @patch("ww.github.gitmessageai.requests.post")
    def test_returns_content_on_200(self, mock_post):
        from ww.github.gitmessageai import call_openrouter_api

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "feat: add feature"}}]},
        )
        result = call_openrouter_api("Generate commit message")
        self.assertEqual(result, "feat: add feature")

    def test_returns_none_when_api_key_missing(self):
        from ww.github import gitmessageai

        gitmessageai.OPENROUTER_API_KEY = None
        result = gitmessageai.call_openrouter_api("prompt")
        self.assertIsNone(result)

    def test_returns_none_for_unknown_model(self):
        from ww.github.gitmessageai import call_openrouter_api

        result = call_openrouter_api("prompt", model="nonexistent-model")
        self.assertIsNone(result)

    @patch("ww.github.gitmessageai.requests.post")
    def test_returns_none_on_non_200_status(self, mock_post):
        from ww.github.gitmessageai import call_openrouter_api

        mock_post.return_value = MagicMock(status_code=401, text="Unauthorized")
        result = call_openrouter_api("prompt")
        self.assertIsNone(result)

    @patch("ww.github.gitmessageai.requests.post", side_effect=Exception("timeout"))
    def test_returns_none_on_request_exception(self, mock_post):
        from ww.github.gitmessageai import call_openrouter_api

        result = call_openrouter_api("prompt")
        self.assertIsNone(result)

    @patch("ww.github.gitmessageai.requests.post")
    def test_returns_none_on_invalid_response_format(self, mock_post):
        from ww.github.gitmessageai import call_openrouter_api

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": []},
        )
        result = call_openrouter_api("prompt")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
