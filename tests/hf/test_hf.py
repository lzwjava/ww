import unittest
from unittest.mock import patch, MagicMock

from ww.hf.hf import _fmt_date, cmd_info


class TestFmtDate(unittest.TestCase):
    def test_valid_iso(self):
        self.assertEqual(_fmt_date("2024-01-15T10:30:00Z"), "2024-01-15")

    def test_empty_string(self):
        self.assertEqual(_fmt_date(""), "?")

    def test_none(self):
        self.assertEqual(_fmt_date(None), "?")

    def test_date_only(self):
        self.assertEqual(_fmt_date("2023-06-01"), "2023-06-01")


class TestCmdInfo(unittest.TestCase):
    @patch("ww.hf.hf.requests.get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "fullname": "Test User",
            "user": "testuser",
            "createdAt": "2023-01-01T00:00:00Z",
            "isPro": False,
            "numModels": 5,
            "numDatasets": 2,
            "numSpaces": 1,
            "numLikes": 100,
            "numFollowers": 50,
            "numFollowing": 30,
        }
        mock_get.return_value = mock_resp
        # Should not raise
        cmd_info("testuser")
        mock_get.assert_called_once()

    @patch("ww.hf.hf.requests.get")
    def test_404_exits(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        with self.assertRaises(SystemExit):
            cmd_info("nobody")

    @patch("ww.hf.hf.requests.get")
    def test_server_error_exits(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_get.return_value = mock_resp
        with self.assertRaises(SystemExit):
            cmd_info("someuser")

    @patch("ww.hf.hf.requests.get")
    def test_default_username(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"user": "lzwjava"}
        mock_get.return_value = mock_resp
        cmd_info()
        url = mock_get.call_args[0][0]
        self.assertIn("lzwjava", url)

    @patch("ww.hf.hf.requests.get")
    def test_with_details_bio(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "user": "test",
            "fullname": "Test",
            "details": "AI researcher",
            "createdAt": "2023-01-01T00:00:00Z",
        }
        mock_get.return_value = mock_resp
        cmd_info("test")


if __name__ == "__main__":
    unittest.main()
