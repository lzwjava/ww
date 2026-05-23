import unittest
from unittest.mock import MagicMock, patch
import os
import json

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestCallOpenrouterApiWithMessages(unittest.TestCase):
    @patch("ww.llm.openrouter_client.requests.post")
    def test_returns_content_on_success(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            ok=True,
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

        mock_response = MagicMock(status_code=401, text="Unauthorized")
        mock_response.ok = False
        mock_post.return_value = mock_response
        messages = [{"role": "user", "content": "hello"}]
        with self.assertRaises(Exception):
            openrouter_client.call_openrouter_api_with_messages(
                messages, model="mistral"
            )

    @patch("ww.llm.openrouter_client.requests.post")
    def test_omits_max_tokens_when_not_specified(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            ok=True,
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
        )
        messages = [{"role": "user", "content": "test"}]
        openrouter_client.call_openrouter_api_with_messages(messages, model="mistral")
        _, kwargs = mock_post.call_args
        self.assertNotIn("max_tokens", kwargs["json"])

    @patch("ww.llm.openrouter_client.requests.post")
    def test_respects_custom_max_tokens(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            ok=True,
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
            ok=True,
            json=lambda: {"choices": [{"message": {"content": "wrapped"}}]},
        )
        result = openrouter_client.call_openrouter_api("test prompt", model="mistral")
        self.assertEqual(result, "wrapped")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["messages"][0]["role"], "user")
        self.assertEqual(kwargs["json"]["messages"][0]["content"], "test prompt")

    @patch("ww.llm.openrouter_client.requests.post")
    def test_raises_on_empty_content(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            ok=True,
            json=lambda: {"choices": [{"message": {"content": ""}}]},
        )
        messages = [{"role": "user", "content": "hello"}]
        with self.assertRaises(Exception) as ctx:
            openrouter_client.call_openrouter_api_with_messages(
                messages, model="mistral"
            )
        self.assertIn("empty content", str(ctx.exception))

    @patch("ww.llm.openrouter_client.requests.post")
    def test_raises_on_none_content(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            ok=True,
            json=lambda: {"choices": [{"message": {}}]},
        )
        messages = [{"role": "user", "content": "hello"}]
        with self.assertRaises(Exception) as ctx:
            openrouter_client.call_openrouter_api_with_messages(
                messages, model="mistral"
            )
        self.assertIn("empty content", str(ctx.exception))

    def test_raises_when_no_api_key(self):
        from ww.llm import openrouter_client

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            messages = [{"role": "user", "content": "hello"}]
            with self.assertRaises(Exception) as ctx:
                openrouter_client.call_openrouter_api_with_messages(
                    messages, model="mistral"
                )
            self.assertIn("OPENROUTER_API_KEY", str(ctx.exception))

    def test_raises_when_no_model(self):
        from ww.llm import openrouter_client

        with patch.dict(os.environ, {"MODEL": ""}, clear=False):
            messages = [{"role": "user", "content": "hello"}]
            with self.assertRaises(Exception) as ctx:
                openrouter_client.call_openrouter_api_with_messages(messages)
            self.assertIn("MODEL", str(ctx.exception))

    def test_uses_model_env_var(self):
        from ww.llm import openrouter_client

        with patch.dict(os.environ, {"MODEL": "env-model"}, clear=False):
            with patch("ww.llm.openrouter_client.requests.post") as mock_post:
                mock_post.return_value = MagicMock(
                    status_code=200,
                    ok=True,
                    json=lambda: {"choices": [{"message": {"content": "ok"}}]},
                )
                messages = [{"role": "user", "content": "test"}]
                openrouter_client.call_openrouter_api_with_messages(messages)
                _, kwargs = mock_post.call_args
                self.assertEqual(kwargs["json"]["model"], "env-model")

    @patch("ww.llm.openrouter_client.requests.post")
    def test_debug_prints(self, mock_post):
        from ww.llm import openrouter_client
        import io
        from contextlib import redirect_stdout

        mock_post.return_value = MagicMock(
            status_code=200,
            ok=True,
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
        )
        messages = [{"role": "user", "content": "test"}]
        f = io.StringIO()
        with redirect_stdout(f):
            openrouter_client.call_openrouter_api_with_messages(
                messages, model="mistral", debug=True
            )
        output = f.getvalue()
        self.assertIn("Request URL:", output)
        self.assertIn("Request Data:", output)
        self.assertIn("Response Status:", output)


class TestCheckProxy(unittest.TestCase):
    def test_no_proxy_configured(self):
        from ww.llm import openrouter_client

        env_patch = {
            "HTTP_PROXY": "",
            "HTTPS_PROXY": "",
            "http_proxy": "",
            "https_proxy": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            result = openrouter_client._check_proxy()
            self.assertEqual(result, "No proxy configured")

    @patch("socket.create_connection")
    def test_proxy_reachable(self, mock_connect):
        from ww.llm import openrouter_client

        mock_connect.return_value = MagicMock()
        with patch.dict(os.environ, {"HTTP_PROXY": "http://proxy:8080"}, clear=False):
            result = openrouter_client._check_proxy()
            self.assertIn("reachable", result)


class TestResolveModel(unittest.TestCase):
    def test_resolve_model_with_arg(self):
        from ww.llm import openrouter_client

        result = openrouter_client._resolve_model("my-model")
        self.assertEqual(result, "my-model")

    def test_resolve_model_from_env(self):
        from ww.llm import openrouter_client

        with patch.dict(os.environ, {"MODEL": "env-model"}, clear=False):
            result = openrouter_client._resolve_model(None)
            self.assertEqual(result, "env-model")

    def test_resolve_model_raises_when_empty(self):
        from ww.llm import openrouter_client

        with patch.dict(os.environ, {"MODEL": ""}, clear=False):
            with self.assertRaises(Exception):
                openrouter_client._resolve_model(None)


class TestExtractDeltaText(unittest.TestCase):
    def test_extracts_content(self):
        from ww.llm import openrouter_client

        payload = json.dumps({"choices": [{"delta": {"content": "hello"}}]})
        result = openrouter_client._extract_delta_text(payload)
        self.assertEqual(result, "hello")

    def test_returns_none_for_invalid_json(self):
        from ww.llm import openrouter_client

        result = openrouter_client._extract_delta_text("not json")
        self.assertIsNone(result)

    def test_returns_none_for_empty_choices(self):
        from ww.llm import openrouter_client

        payload = json.dumps({"choices": []})
        result = openrouter_client._extract_delta_text(payload)
        self.assertIsNone(result)

    def test_returns_none_for_no_delta(self):
        from ww.llm import openrouter_client

        payload = json.dumps({"choices": [{"delta": {}}]})
        result = openrouter_client._extract_delta_text(payload)
        self.assertIsNone(result)


class TestStreamOpenrouterApi(unittest.TestCase):
    @patch("ww.llm.openrouter_client.requests.post")
    def test_stream_yields_text(self, mock_post):
        from ww.llm import openrouter_client

        lines = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            b'data: {"choices":[{"delta":{"content":" World"}}]}',
            b"data: [DONE]",
        ]
        mock_response = MagicMock(ok=True)
        mock_response.iter_lines.return_value = lines
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "hi"}]
        result = list(
            openrouter_client.stream_openrouter_api_with_messages(
                messages, model="mistral"
            )
        )
        self.assertEqual(result, ["Hello", " World"])

    @patch("ww.llm.openrouter_client.requests.post")
    def test_stream_skips_empty_and_non_data(self, mock_post):
        from ww.llm import openrouter_client

        lines = [
            b"",
            b": comment",
            b'data: {"choices":[{"delta":{"content":"ok"}}]}',
            b"data: [DONE]",
        ]
        mock_response = MagicMock(ok=True)
        mock_response.iter_lines.return_value = lines
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "hi"}]
        result = list(
            openrouter_client.stream_openrouter_api_with_messages(
                messages, model="mistral"
            )
        )
        self.assertEqual(result, ["ok"])

    @patch("ww.llm.openrouter_client.requests.post")
    def test_stream_raises_on_error(self, mock_post):
        from ww.llm import openrouter_client

        mock_response = MagicMock(ok=False, status_code=500, text="Server Error")
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "hi"}]
        with self.assertRaises(Exception):
            list(
                openrouter_client.stream_openrouter_api_with_messages(
                    messages, model="mistral"
                )
            )

    def test_stream_raises_when_no_api_key(self):
        from ww.llm import openrouter_client

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            messages = [{"role": "user", "content": "hi"}]
            with self.assertRaises(Exception):
                list(
                    openrouter_client.stream_openrouter_api_with_messages(
                        messages, model="mistral"
                    )
                )

    @patch("ww.llm.openrouter_client.requests.post")
    def test_stream_wraps_prompt(self, mock_post):
        from ww.llm import openrouter_client

        mock_response = MagicMock(ok=True)
        mock_response.iter_lines.return_value = [b"data: [DONE]"]
        mock_post.return_value = mock_response

        result = list(
            openrouter_client.stream_openrouter_api("test prompt", model="mistral")
        )
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["messages"][0]["content"], "test prompt")
        self.assertEqual(result, [])

    @patch("ww.llm.openrouter_client.requests.post")
    def test_stream_includes_max_tokens(self, mock_post):
        from ww.llm import openrouter_client

        mock_response = MagicMock(ok=True)
        mock_response.iter_lines.return_value = [b"data: [DONE]"]
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "hi"}]
        list(
            openrouter_client.stream_openrouter_api_with_messages(
                messages, model="mistral", max_tokens=500
            )
        )
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["max_tokens"], 500)
        self.assertTrue(kwargs["json"]["stream"])


if __name__ == "__main__":
    unittest.main()
