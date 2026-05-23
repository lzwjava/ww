import json
import os
import tempfile
import shutil
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestLoadWifiList(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_tmp_dir = None

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("ww.network.generate_password.TMP_DIR")
    def test_loads_valid_json(self, mock_tmp_dir):
        from ww.network.generate_password import load_wifi_list

        mock_tmp_dir = self.tmpdir
        wifi_data = [
            {
                "ssid": "MyWiFi",
                "bssid": "AA:BB:CC:DD:EE:FF",
                "full_line": "MyWiFi AA:BB:CC:DD:EE:FF",
            }
        ]
        fp = os.path.join(self.tmpdir, "wifi_list.json")
        with open(fp, "w") as f:
            json.dump(wifi_data, f)

        with patch("ww.network.generate_password.TMP_DIR", self.tmpdir):
            result = load_wifi_list()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["ssid"], "MyWiFi")

    @patch("ww.network.generate_password.TMP_DIR", "/nonexistent/dir")
    def test_exits_when_file_missing(self):
        from ww.network.generate_password import load_wifi_list

        with self.assertRaises(SystemExit):
            load_wifi_list()

    @patch("ww.network.generate_password.TMP_DIR")
    def test_loads_multiple_networks(self, mock_tmp_dir):
        from ww.network.generate_password import load_wifi_list

        wifi_data = [
            {"ssid": "Net1", "bssid": "11:22:33:44:55:66", "full_line": "Net1"},
            {"ssid": "Net2", "bssid": "AA:BB:CC:DD:EE:FF", "full_line": "Net2"},
        ]
        fp = os.path.join(self.tmpdir, "wifi_list.json")
        with open(fp, "w") as f:
            json.dump(wifi_data, f)

        with patch("ww.network.generate_password.TMP_DIR", self.tmpdir):
            result = load_wifi_list()

        self.assertEqual(len(result), 2)


class TestGeneratePasswords(unittest.TestCase):
    @patch("ww.network.generate_password.call_openrouter_api")
    def test_parses_json_array_response(self, mock_api):
        from ww.network.generate_password import generate_passwords

        mock_api.return_value = '["password1", "password2", "password3"]'

        passwords = generate_passwords("TestSSID", num_suggestions=3)

        self.assertEqual(passwords, ["password1", "password2", "password3"])
        mock_api.assert_called_once()

    @patch("ww.network.generate_password.call_openrouter_api")
    def test_parses_json_with_markdown_wrapper(self, mock_api):
        from ww.network.generate_password import generate_passwords

        mock_api.return_value = '```json\n["pass1", "pass2"]\n```'

        passwords = generate_passwords("TestSSID", num_suggestions=2)

        self.assertEqual(passwords, ["pass1", "pass2"])

    @patch("ww.network.generate_password.call_openrouter_api")
    def test_limits_to_num_suggestions(self, mock_api):
        from ww.network.generate_password import generate_passwords

        mock_api.return_value = '["p1", "p2", "p3", "p4", "p5"]'

        passwords = generate_passwords("TestSSID", num_suggestions=3)

        self.assertEqual(len(passwords), 3)

    @patch("ww.network.generate_password.call_openrouter_api")
    def test_filters_chinese_characters(self, mock_api):
        from ww.network.generate_password import generate_passwords

        mock_api.return_value = '["password1", "密码test", "password2"]'

        passwords = generate_passwords("TestSSID", num_suggestions=3)

        self.assertNotIn("密码test", passwords)
        self.assertIn("password1", passwords)
        self.assertIn("password2", passwords)

    @patch("ww.network.generate_password.call_openrouter_api")
    def test_returns_empty_on_invalid_json(self, mock_api):
        from ww.network.generate_password import generate_passwords

        mock_api.return_value = "not valid json at all"

        passwords = generate_passwords("TestSSID", num_suggestions=5)

        self.assertIsInstance(passwords, list)

    @patch("ww.network.generate_password.call_openrouter_api")
    def test_uses_specified_model(self, mock_api):
        from ww.network.generate_password import generate_passwords

        mock_api.return_value = '["pass1"]'

        generate_passwords("TestSSID", model="gpt-4o")

        _, kwargs = mock_api.call_args
        self.assertEqual(kwargs.get("model"), "gpt-4o")


class TestSavePasswordsToFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_creates_file_with_passwords(self):
        from ww.network.generate_password import save_passwords_to_file

        with patch("ww.network.generate_password.TMP_DIR", self.tmpdir):
            result = save_passwords_to_file(
                "AA:BB:CC:DD:EE:FF", ["pass1", "pass2", "pass3"]
            )

        expected_fp = os.path.join(self.tmpdir, "AA_BB_CC_DD_EE_FF_passwords.txt")
        self.assertEqual(result, expected_fp)
        self.assertTrue(os.path.exists(expected_fp))

        with open(expected_fp) as f:
            lines = f.read().strip().split("\n")
        self.assertEqual(lines, ["pass1", "pass2", "pass3"])

    def test_colons_replaced_in_filename(self):
        from ww.network.generate_password import save_passwords_to_file

        with patch("ww.network.generate_password.TMP_DIR", self.tmpdir):
            result = save_passwords_to_file("11:22:33:44:55:66", ["mypwd"])

        self.assertIn("11_22_33_44_55_66", result)

    def test_overwrites_existing_file(self):
        from ww.network.generate_password import save_passwords_to_file

        with patch("ww.network.generate_password.TMP_DIR", self.tmpdir):
            save_passwords_to_file("AA:BB:CC:DD:EE:FF", ["old_password"])
            save_passwords_to_file("AA:BB:CC:DD:EE:FF", ["new_password"])

        fp = os.path.join(self.tmpdir, "AA_BB_CC_DD_EE_FF_passwords.txt")
        with open(fp) as f:
            content = f.read().strip()
        self.assertEqual(content, "new_password")


if __name__ == "__main__":
    unittest.main()
