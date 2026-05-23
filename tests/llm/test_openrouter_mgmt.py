"""Tests for ww llm openrouter_mgmt module."""

import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

os.environ.setdefault("OPENROUTER_MANAGEMENT_API_KEY", "test_fake_mgmt_key")


class TestGetMgmtKey(unittest.TestCase):
    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            from ww.llm.openrouter_mgmt import _get_mgmt_key

            with self.assertRaises(Exception) as ctx:
                _get_mgmt_key()
            self.assertIn("OPENROUTER_MANAGEMENT_API_KEY", str(ctx.exception))

    def test_returns_key_when_set(self):
        with patch.dict(os.environ, {"OPENROUTER_MANAGEMENT_API_KEY": "my_key"}):
            from ww.llm.openrouter_mgmt import _get_mgmt_key

            self.assertEqual(_get_mgmt_key(), "my_key")


class TestFmtTokens(unittest.TestCase):
    def test_below_1k(self):
        from ww.llm.openrouter_mgmt import _fmt_tokens

        self.assertEqual(_fmt_tokens(0), "0")
        self.assertEqual(_fmt_tokens(500), "500")
        self.assertEqual(_fmt_tokens(999), "999")

    def test_thousands(self):
        from ww.llm.openrouter_mgmt import _fmt_tokens

        self.assertEqual(_fmt_tokens(1000), "1.0K")
        self.assertEqual(_fmt_tokens(1500), "1.5K")
        self.assertEqual(_fmt_tokens(99999), "100.0K")

    def test_millions(self):
        from ww.llm.openrouter_mgmt import _fmt_tokens

        self.assertEqual(_fmt_tokens(1000000), "1.0M")
        self.assertEqual(_fmt_tokens(1500000), "1.5M")
        self.assertEqual(_fmt_tokens(2500000), "2.5M")


class TestGetFunction(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt.requests.get")
    @patch("ww.llm.openrouter_mgmt._get_mgmt_key", return_value="test_key")
    def test_success(self, mock_key, mock_get):
        from ww.llm.openrouter_mgmt import _get

        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = {"data": {"usage": 1.0}}
        mock_get.return_value = mock_resp

        result = _get("auth/key")
        self.assertEqual(result, {"data": {"usage": 1.0}})

    @patch("ww.llm.openrouter_mgmt.requests.get")
    @patch("ww.llm.openrouter_mgmt._get_mgmt_key", return_value="test_key")
    def test_raises_on_error(self, mock_key, mock_get):
        from ww.llm.openrouter_mgmt import _get

        mock_resp = MagicMock(ok=False, status_code=401, text="Unauthorized")
        mock_get.return_value = mock_resp

        with self.assertRaises(Exception) as ctx:
            _get("auth/key")
        self.assertIn("401", str(ctx.exception))


class TestGetKeyInfo(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt._get")
    def test_returns_key_data(self, mock_get):
        from ww.llm.openrouter_mgmt import get_key_info

        mock_get.return_value = {"data": {"usage": 5.0, "limit": 100.0}}
        result = get_key_info()
        self.assertEqual(result["usage"], 5.0)
        mock_get.assert_called_once_with("auth/key")


class TestGetCredits(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt._get")
    def test_returns_credits(self, mock_get):
        from ww.llm.openrouter_mgmt import get_credits

        mock_get.return_value = {"data": {"total_credits": 50.0, "total_usage": 10.0}}
        result = get_credits()
        self.assertEqual(result["total_credits"], 50.0)
        mock_get.assert_called_once_with("credits")


class TestGetModels(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt._get")
    def test_returns_models_list(self, mock_get):
        from ww.llm.openrouter_mgmt import get_models

        mock_get.return_value = {"data": [{"id": "gpt-4"}, {"id": "claude-3"}]}
        result = get_models()
        self.assertEqual(len(result), 2)
        mock_get.assert_called_once_with("models")


class TestGetActivity(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt._get")
    def test_returns_activity(self, mock_get):
        from ww.llm.openrouter_mgmt import get_activity

        mock_get.return_value = {"data": [{"date": "2024-01-01", "usage": 1.0}]}
        result = get_activity()
        self.assertEqual(len(result), 1)
        mock_get.assert_called_once_with("activity")


class TestCmdInfo(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt.get_credits")
    @patch("ww.llm.openrouter_mgmt.get_key_info")
    def test_prints_account_info(self, mock_key, mock_credits):
        from ww.llm.openrouter_mgmt import cmd_info
        import io
        from contextlib import redirect_stdout

        mock_key.return_value = {
            "usage": 5.0,
            "usage_daily": 0.5,
            "usage_weekly": 3.0,
            "usage_monthly": 5.0,
            "is_free_tier": False,
            "is_management_key": True,
            "limit": 100.0,
            "limit_remaining": 95.0,
        }
        mock_credits.return_value = {
            "total_credits": 50.0,
            "total_usage": 10.0,
        }

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_info()
        output = f.getvalue()

        self.assertIn("$50.00", output)
        self.assertIn("$10.00", output)
        self.assertIn("$40.00", output)
        self.assertIn("$5.00", output)


class TestCmdCredits(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt.get_credits")
    def test_prints_credits(self, mock_credits):
        from ww.llm.openrouter_mgmt import cmd_credits
        import io
        from contextlib import redirect_stdout

        mock_credits.return_value = {
            "total_credits": 100.0,
            "total_usage": 25.0,
        }

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_credits()
        output = f.getvalue()

        self.assertIn("$100.00", output)
        self.assertIn("$25.00", output)
        self.assertIn("$75.00", output)


class TestCmdActivity(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt.get_activity")
    def test_empty_activity(self, mock_activity):
        from ww.llm.openrouter_mgmt import cmd_activity
        import io
        from contextlib import redirect_stdout

        mock_activity.return_value = []

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_activity(days=7)
        output = f.getvalue()

        self.assertIn("No activity", output)

    @patch("ww.llm.openrouter_mgmt.get_activity")
    def test_prints_activity(self, mock_activity):
        from ww.llm.openrouter_mgmt import cmd_activity
        import io
        from contextlib import redirect_stdout

        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mock_activity.return_value = [
            {
                "date": today,
                "model": "gpt-4",
                "usage": 1.5,
                "byok_usage_inference": 0,
                "requests": 10,
                "prompt_tokens": 5000,
                "completion_tokens": 2000,
                "reasoning_tokens": 0,
            },
        ]

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_activity(days=7)
        output = f.getvalue()

        self.assertIn("gpt-4", output)
        self.assertIn("$1.5", output)


class TestCmdModels(unittest.TestCase):
    @patch("ww.llm.openrouter_mgmt.get_models")
    def test_prints_models(self, mock_models):
        from ww.llm.openrouter_mgmt import cmd_models
        import io
        from contextlib import redirect_stdout

        mock_models.return_value = [
            {
                "id": "gpt-4",
                "pricing": {"prompt": "0.00003", "completion": "0.00006"},
            },
        ]

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_models(as_json=False)
        output = f.getvalue()

        self.assertIn("gpt-4", output)
        self.assertIn("1 models", output)

    @patch("ww.llm.openrouter_mgmt.get_models")
    def test_json_output(self, mock_models):
        from ww.llm.openrouter_mgmt import cmd_models
        import io
        from contextlib import redirect_stdout

        models = [{"id": "gpt-4"}]
        mock_models.return_value = models

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_models(as_json=True)
        output = f.getvalue()

        self.assertIn('"id": "gpt-4"', output)
        self.assertIn("Total: 1 models", output)


if __name__ == "__main__":
    unittest.main()
