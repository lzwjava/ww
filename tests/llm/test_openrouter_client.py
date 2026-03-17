import unittest
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestCallOpenrouterApiWithMessages(unittest.TestCase):
    @patch("ww.llm.openrouter_client.requests.post")
    def test_returns_content_on_success(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "response text"}}]},
        )
        messages = [{"role": "user", "content": "hello"}]
        result = openrouter_client.call_openrouter_api_with_messages(
            messages, model="mistral"
        )
        self.assertEqual(result, "response text")

    def test_raises_on_unknown_model(self):
        from ww.llm import openrouter_client

        messages = [{"role": "user", "content": "hello"}]
        with self.assertRaises(Exception) as ctx:
            openrouter_client.call_openrouter_api_with_messages(
                messages, model="unknown-xyz"
            )
        self.assertIn("unknown-xyz", str(ctx.exception))

    @patch("ww.llm.openrouter_client.requests.post")
    def test_raises_on_non_200_response(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(status_code=401, text="Unauthorized")
        messages = [{"role": "user", "content": "hello"}]
        with self.assertRaises(Exception):
            openrouter_client.call_openrouter_api_with_messages(
                messages, model="mistral"
            )

    @patch("ww.llm.openrouter_client.requests.post")
    def test_uses_default_max_tokens_when_not_specified(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
        )
        messages = [{"role": "user", "content": "test"}]
        openrouter_client.call_openrouter_api_with_messages(messages, model="mistral")
        _, kwargs = mock_post.call_args
        self.assertEqual(
            kwargs["json"]["max_tokens"],
            openrouter_client.DEFAULT_TOKENS["mistral"],
        )

    @patch("ww.llm.openrouter_client.requests.post")
    def test_respects_custom_max_tokens(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
        )
        messages = [{"role": "user", "content": "test"}]
        openrouter_client.call_openrouter_api_with_messages(
            messages, model="mistral", max_tokens=1234
        )
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["max_tokens"], 1234)

    @patch("ww.llm.openrouter_client.requests.post")
    def test_call_openrouter_api_wraps_with_messages(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "wrapped"}}]},
        )
        result = openrouter_client.call_openrouter_api("test prompt", model="mistral")
        self.assertEqual(result, "wrapped")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["messages"][0]["role"], "user")
        self.assertEqual(kwargs["json"]["messages"][0]["content"], "test prompt")


if __name__ == "__main__":
    unittest.main()
