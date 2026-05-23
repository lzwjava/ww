import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


from ww.image.whatsapp import (
    run_applescript,
    safari_execute_js,
    safari_get_url,
    safari_navigate,
    diagnose_page,
    extract_images_from_last_message,
)


class TestRunAppleScript(unittest.TestCase):
    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output text\n", stderr=""
        )
        result = run_applescript("tell app Finder to quit")
        self.assertEqual(result, "output text")

    @patch("subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error msg\n")
        result = run_applescript("bad script")
        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_timeout(self, mock_run):
        import subprocess as sp

        mock_run.side_effect = sp.TimeoutExpired(cmd="osascript", timeout=30)
        with self.assertRaises(sp.TimeoutExpired):
            run_applescript("slow script")


class TestSafariExecuteJs(unittest.TestCase):
    @patch("ww.image.whatsapp.run_applescript")
    def test_calls_run_applescript(self, mock_run):
        mock_run.return_value = "result"
        result = safari_execute_js("alert('hi')")
        self.assertEqual(result, "result")
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("tell application", call_args)
        self.assertIn("do JavaScript", call_args)

    @patch("ww.image.whatsapp.run_applescript")
    def test_escapes_quotes(self, mock_run):
        mock_run.return_value = "ok"
        safari_execute_js('say "hello"')
        call_args = mock_run.call_args[0][0]
        # The JS should have escaped quotes
        self.assertNotIn('say "hello"', call_args)


class TestSafariGetUrl(unittest.TestCase):
    @patch("ww.image.whatsapp.run_applescript")
    def test_returns_url(self, mock_run):
        mock_run.return_value = "https://web.whatsapp.com"
        result = safari_get_url()
        self.assertEqual(result, "https://web.whatsapp.com")

    @patch("ww.image.whatsapp.run_applescript")
    def test_no_document(self, mock_run):
        mock_run.return_value = ""
        result = safari_get_url()
        self.assertEqual(result, "")


class TestSafariNavigate(unittest.TestCase):
    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = safari_navigate("https://example.com")
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="failed\n")
        result = safari_navigate("https://example.com")
        self.assertFalse(result)


class TestDiagnosePage(unittest.TestCase):
    @patch("ww.image.whatsapp.safari_execute_js")
    def test_valid_json(self, mock_js):
        diag_data = json.dumps({"url": "https://web.whatsapp.com", "whatsapp": True})
        mock_js.return_value = diag_data
        result = diagnose_page()
        self.assertIsNotNone(result)
        self.assertTrue(result["whatsapp"])

    @patch("ww.image.whatsapp.safari_execute_js")
    def test_error_response(self, mock_js):
        mock_js.return_value = "ERROR: No Safari document"
        result = diagnose_page()
        self.assertIsNone(result)

    @patch("ww.image.whatsapp.safari_execute_js")
    def test_none_response(self, mock_js):
        mock_js.return_value = None
        result = diagnose_page()
        self.assertIsNone(result)

    @patch("ww.image.whatsapp.safari_execute_js")
    def test_invalid_json(self, mock_js):
        mock_js.return_value = "not json at all"
        result = diagnose_page()
        self.assertIsNone(result)


class TestExtractImagesFromLastMessage(unittest.TestCase):
    @patch("ww.image.whatsapp.safari_execute_js")
    @patch("ww.image.whatsapp.diagnose_page")
    @patch("ww.image.whatsapp.safari_get_url")
    @patch("os.makedirs")
    def test_no_messages(self, mock_makedirs, mock_url, mock_diag, mock_js):
        mock_url.return_value = "https://web.whatsapp.com"
        mock_diag.return_value = {"whatsapp": True, "msgContainers": 0}
        mock_js.return_value = json.dumps({"error": "No message containers found"})
        result = extract_images_from_last_message("/tmp/out")
        self.assertEqual(result, [])

    @patch("ww.image.whatsapp.safari_execute_js")
    @patch("ww.image.whatsapp.diagnose_page")
    @patch("ww.image.whatsapp.safari_get_url")
    @patch("os.makedirs")
    def test_js_returns_none(self, mock_makedirs, mock_url, mock_diag, mock_js):
        mock_url.return_value = "https://web.whatsapp.com"
        mock_diag.return_value = {"whatsapp": True, "msgContainers": 1}
        mock_js.return_value = None
        result = extract_images_from_last_message("/tmp/out")
        self.assertEqual(result, [])

    @patch("ww.image.whatsapp.safari_execute_js")
    @patch("ww.image.whatsapp.diagnose_page")
    @patch("ww.image.whatsapp.safari_get_url")
    @patch("os.makedirs")
    def test_js_returns_error(self, mock_makedirs, mock_url, mock_diag, mock_js):
        mock_url.return_value = "https://web.whatsapp.com"
        mock_diag.return_value = {"whatsapp": True, "msgContainers": 1}
        mock_js.return_value = "ERROR: something"
        result = extract_images_from_last_message("/tmp/out")
        self.assertEqual(result, [])

    @patch("ww.image.whatsapp.safari_execute_js")
    @patch("ww.image.whatsapp.diagnose_page")
    @patch("ww.image.whatsapp.safari_get_url")
    @patch("os.makedirs")
    def test_not_whatsapp(self, mock_makedirs, mock_url, mock_diag, mock_js):
        mock_url.return_value = "https://google.com"
        mock_diag.return_value = {"whatsapp": False}
        result = extract_images_from_last_message("/tmp/out")
        self.assertEqual(result, [])

    @patch("ww.image.whatsapp.safari_execute_js")
    @patch("ww.image.whatsapp.diagnose_page")
    @patch("ww.image.whatsapp.safari_get_url")
    @patch("os.makedirs")
    def test_invalid_json_from_js(self, mock_makedirs, mock_url, mock_diag, mock_js):
        mock_url.return_value = "https://web.whatsapp.com"
        mock_diag.return_value = {"whatsapp": True, "msgContainers": 1}
        mock_js.return_value = "not json"
        result = extract_images_from_last_message("/tmp/out")
        self.assertEqual(result, [])

    @patch("builtins.open", new_callable=mock_open)
    @patch("ww.image.whatsapp.safari_execute_js")
    @patch("ww.image.whatsapp.diagnose_page")
    @patch("ww.image.whatsapp.safari_get_url")
    @patch("os.makedirs")
    def test_valid_images_saved(
        self, mock_makedirs, mock_url, mock_diag, mock_js, mock_file
    ):
        mock_url.return_value = "https://web.whatsapp.com"
        mock_diag.return_value = {"whatsapp": True, "msgContainers": 1}
        import base64

        fake_data = base64.b64encode(b"\xff\xd8\xff\xe0fake-jpeg").decode()
        mock_js.return_value = json.dumps(
            {
                "images": [
                    {"index": 0, "data": fake_data, "width": 100, "height": 100}
                ],
                "total": 1,
            }
        )
        result = extract_images_from_last_message("/tmp/out")
        self.assertEqual(len(result), 1)
        self.assertIn("whatsapp-1.jpg", result[0])


if __name__ == "__main__":
    unittest.main()
