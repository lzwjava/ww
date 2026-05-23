import unittest
from unittest.mock import patch, MagicMock
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGetDeviceCode(unittest.TestCase):
    @patch("ww.llm.copilot_auth.requests.post")
    def test_returns_json_on_success(self, mock_post):
        from ww.llm import copilot_auth

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "device_code": "abc123",
            "user_code": "XXXX-YYYY",
            "verification_uri": "https://github.com/login/device",
        }
        mock_post.return_value = mock_response

        result = copilot_auth._get_device_code()
        self.assertEqual(result["device_code"], "abc123")
        self.assertEqual(result["user_code"], "XXXX-YYYY")
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("device/code", call_args[0][0])

    @patch("ww.llm.copilot_auth.requests.post")
    def test_raises_on_http_error(self, mock_post):
        from ww.llm import copilot_auth

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 422")
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            copilot_auth._get_device_code()


class TestPollForAccessToken(unittest.TestCase):
    @patch("ww.llm.copilot_auth.time.sleep")
    @patch("ww.llm.copilot_auth.requests.post")
    def test_returns_token_on_success(self, mock_post, mock_sleep):
        from ww.llm import copilot_auth

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"access_token": "gho_abc123"}
        mock_post.return_value = mock_response

        result = copilot_auth._poll_for_access_token("device-code", interval=0)
        self.assertEqual(result, "gho_abc123")

    @patch("ww.llm.copilot_auth.time.sleep")
    @patch("ww.llm.copilot_auth.requests.post")
    def test_retries_on_pending(self, mock_post, mock_sleep):
        from ww.llm import copilot_auth

        pending_response = MagicMock()
        pending_response.raise_for_status = MagicMock()
        pending_response.json.return_value = {"error": "authorization_pending"}

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()
        success_response.json.return_value = {"access_token": "gho_token"}

        mock_post.side_effect = [pending_response, success_response]

        result = copilot_auth._poll_for_access_token("device-code", interval=0)
        self.assertEqual(result, "gho_token")
        self.assertEqual(mock_post.call_count, 2)

    @patch("ww.llm.copilot_auth.time.sleep")
    @patch("ww.llm.copilot_auth.requests.post")
    def test_handles_slow_down(self, mock_post, mock_sleep):
        from ww.llm import copilot_auth

        slow_response = MagicMock()
        slow_response.raise_for_status = MagicMock()
        slow_response.json.return_value = {"error": "slow_down"}

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()
        success_response.json.return_value = {"access_token": "gho_token"}

        mock_post.side_effect = [slow_response, success_response]

        result = copilot_auth._poll_for_access_token("device-code", interval=1)
        self.assertEqual(result, "gho_token")

    @patch("ww.llm.copilot_auth.time.sleep")
    @patch("ww.llm.copilot_auth.requests.post")
    def test_raises_on_expired_token(self, mock_post, mock_sleep):
        from ww.llm import copilot_auth

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"error": "expired_token"}
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as ctx:
            copilot_auth._poll_for_access_token("device-code", interval=0)
        self.assertIn("expired", str(ctx.exception))

    @patch("ww.llm.copilot_auth.time.sleep")
    @patch("ww.llm.copilot_auth.requests.post")
    def test_raises_on_unknown_error(self, mock_post, mock_sleep):
        from ww.llm import copilot_auth

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "error": "some_other_error",
            "error_description": "bad",
        }
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as ctx:
            copilot_auth._poll_for_access_token("device-code", interval=0)
        self.assertIn("OAuth error", str(ctx.exception))


class TestSaveTokenToEnv(unittest.TestCase):
    def test_saves_new_token(self):
        from ww.llm import copilot_auth

        written_lines = []
        fake_file = MagicMock()
        fake_file.readlines.return_value = []
        fake_file.__enter__ = MagicMock(return_value=fake_file)
        fake_file.__exit__ = MagicMock(return_value=False)

        def fake_open(path, mode="r"):
            return fake_file

        with patch("builtins.open", side_effect=fake_open):
            with patch("os.path.exists", return_value=False):
                copilot_auth._save_token_to_env("gho_newtoken")

        fake_file.writelines.assert_called_once()
        lines = fake_file.writelines.call_args[0][0]
        self.assertTrue(any("GITHUB_TOKEN=gho_newtoken" in l for l in lines))

    def test_updates_existing_token(self):
        from ww.llm import copilot_auth

        fake_read = MagicMock()
        fake_read.readlines.return_value = [
            "OTHER_VAR=value\n",
            "GITHUB_TOKEN=old_token\n",
        ]

        fake_write = MagicMock()
        fake_write.__enter__ = MagicMock(return_value=fake_write)
        fake_write.__exit__ = MagicMock(return_value=False)

        call_count = [0]

        def fake_open(path, mode="r"):
            call_count[0] += 1
            if call_count[0] == 1:
                return fake_read
            return fake_write

        with patch("builtins.open", side_effect=fake_open):
            with patch("os.path.exists", return_value=True):
                copilot_auth._save_token_to_env("gho_newtoken")

        fake_write.writelines.assert_called_once()
        lines = fake_write.writelines.call_args[0][0]
        self.assertTrue(any("GITHUB_TOKEN=gho_newtoken" in l for l in lines))
        self.assertTrue(any("OTHER_VAR=value" in l for l in lines))
        self.assertFalse(any("old_token" in l for l in lines))

    def test_creates_file_if_not_exists(self):
        from ww.llm import copilot_auth

        fake_write = MagicMock()
        fake_write.__enter__ = MagicMock(return_value=fake_write)
        fake_write.__exit__ = MagicMock(return_value=False)

        def fake_open(path, mode="r"):
            return fake_write

        with patch("builtins.open", side_effect=fake_open):
            with patch("os.path.exists", return_value=False):
                copilot_auth._save_token_to_env("gho_newtoken")

        fake_write.writelines.assert_called_once()
        lines = fake_write.writelines.call_args[0][0]
        self.assertTrue(any("GITHUB_TOKEN=gho_newtoken" in l for l in lines))


class TestMain(unittest.TestCase):
    @patch("ww.llm.copilot_auth._save_token_to_env")
    @patch("ww.llm.copilot_auth._poll_for_access_token")
    @patch("ww.llm.copilot_auth._get_device_code")
    def test_main_flow(self, mock_device, mock_poll, mock_save):
        from ww.llm import copilot_auth

        mock_device.return_value = {
            "device_code": "abc",
            "user_code": "XXXX",
            "verification_uri": "https://github.com/login/device",
            "interval": 5,
        }
        mock_poll.return_value = "gho_token123"

        copilot_auth.main()

        mock_device.assert_called_once()
        mock_poll.assert_called_once_with("abc", 5)
        mock_save.assert_called_once_with("gho_token123")


if __name__ == "__main__":
    unittest.main()
