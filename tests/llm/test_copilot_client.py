import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGetCopilotToken(unittest.TestCase):
    @patch("requests.get")
    def test_returns_token(self, mock_get):
        from ww.llm.copilot_client import _get_copilot_token

        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = {"token": "copilot_token_123"}
        mock_get.return_value = mock_resp
        result = _get_copilot_token("github_token")
        self.assertEqual(result, "copilot_token_123")

    @patch("requests.get")
    def test_raises_on_failure(self, mock_get):
        from ww.llm.copilot_client import _get_copilot_token

        mock_resp = MagicMock(ok=False, status_code=401, reason="Unauthorized")
        mock_get.return_value = mock_resp
        with self.assertRaises(RuntimeError):
            _get_copilot_token("bad_token")


class TestGetModels(unittest.TestCase):
    @patch("ww.llm.copilot_client._get_copilot_token", return_value="token")
    @patch("requests.get")
    def test_returns_models(self, mock_get, mock_token):
        from ww.llm.copilot_client import get_models

        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = {"data": [{"id": "gpt-4"}]}
        mock_get.return_value = mock_resp
        result = get_models("github_token")
        self.assertEqual(len(result), 1)

    @patch("ww.llm.copilot_client._get_copilot_token", return_value="token")
    @patch("requests.get")
    def test_raises_on_failure(self, mock_get, mock_token):
        from ww.llm.copilot_client import get_models

        mock_resp = MagicMock(ok=False, status_code=500, reason="Error")
        mock_get.return_value = mock_resp
        with self.assertRaises(RuntimeError):
            get_models("github_token")


class TestCallCopilotApiWithMessages(unittest.TestCase):
    @patch("ww.llm.copilot_client._get_copilot_token", return_value="token")
    @patch("requests.post")
    @patch.dict(os.environ, {"GITHUB_TOKEN": "gh_token", "MODEL": "gpt-4"})
    def test_returns_content(self, mock_post, mock_token):
        from ww.llm.copilot_client import call_copilot_api_with_messages

        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = {"choices": [{"message": {"content": "hello"}}]}
        mock_post.return_value = mock_resp
        result = call_copilot_api_with_messages([{"role": "user", "content": "hi"}])
        self.assertEqual(result, "hello")

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_when_no_github_token(self):
        from ww.llm.copilot_client import call_copilot_api_with_messages

        with self.assertRaises(RuntimeError):
            call_copilot_api_with_messages([{"role": "user", "content": "hi"}])

    @patch.dict(os.environ, {"GITHUB_TOKEN": "gh_token"}, clear=True)
    def test_raises_when_no_model(self):
        from ww.llm.copilot_client import call_copilot_api_with_messages

        with self.assertRaises(RuntimeError):
            call_copilot_api_with_messages([{"role": "user", "content": "hi"}])

    @patch("ww.llm.copilot_client._get_copilot_token", return_value="token")
    @patch("requests.post")
    @patch.dict(os.environ, {"GITHUB_TOKEN": "gh_token"})
    def test_raises_on_api_error(self, mock_post, mock_token):
        from ww.llm.copilot_client import call_copilot_api_with_messages

        mock_resp = MagicMock(
            ok=False, status_code=400, reason="Bad Request", text="err"
        )
        mock_post.return_value = mock_resp
        with self.assertRaises(RuntimeError):
            call_copilot_api_with_messages(
                [{"role": "user", "content": "hi"}], model="gpt-4"
            )


class TestCallCopilotApi(unittest.TestCase):
    @patch(
        "ww.llm.copilot_client.call_copilot_api_with_messages", return_value="response"
    )
    def test_wraps_prompt_in_messages(self, mock_call):
        from ww.llm.copilot_client import call_copilot_api

        result = call_copilot_api("hello", model="gpt-4")
        self.assertEqual(result, "response")
        messages = mock_call.call_args[0][0]
        self.assertEqual(messages[0]["content"], "hello")
