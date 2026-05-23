import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import base64

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

# Mock google.cloud.storage before import
sys.modules["google"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.storage"] = MagicMock()

# Mock ruamel.yaml
ruamel_mock = MagicMock()
sys.modules["ruamel"] = ruamel_mock
sys.modules["ruamel.yaml"] = ruamel_mock.yaml

from ww.auto_ss_config import upload_configs


class TestDecodeSsUrl(unittest.TestCase):
    def test_valid_ss_url(self):
        # method:password -> base64 -> YWVzLTI1Ni1nY206cGFzc3dvcmQxMjM=
        encoded = base64.urlsafe_b64encode(b"aes-256-gcm:password123").decode()
        url = f"ss://{encoded}@1.2.3.4:8388"
        result = upload_configs.decode_ss_url(url)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "ss")
        self.assertEqual(result["server"], "1.2.3.4")
        self.assertEqual(result["port"], 8388)
        self.assertEqual(result["cipher"], "aes-256-gcm")
        self.assertEqual(result["password"], "password123")

    def test_valid_ss_url_with_slash(self):
        encoded = base64.urlsafe_b64encode(b"chacha20:mypass").decode()
        url = f"ss://{encoded}@5.6.7.443:443/"
        result = upload_configs.decode_ss_url(url)
        self.assertIsNotNone(result)
        self.assertEqual(result["server"], "5.6.7.443")
        self.assertEqual(result["port"], 443)

    def test_invalid_ss_url(self):
        result = upload_configs.decode_ss_url("http://not-ss.com")
        self.assertIsNone(result)


class TestDecodeHy2Url(unittest.TestCase):
    def test_valid_hy2_url_with_port_and_sni(self):
        url = "hy2://mypassword@server.example.com:8443/?sni=sni.example.com"
        result = upload_configs.decode_hy2_url(url)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "hysteria2")
        self.assertEqual(result["server"], "server.example.com")
        self.assertEqual(result["port"], 8443)
        self.assertEqual(result["password"], "mypassword")
        self.assertEqual(result["sni"], "sni.example.com")

    def test_valid_hy2_url_default_port(self):
        url = "hy2://pass@server.example.com/?sni=sni.example.com"
        result = upload_configs.decode_hy2_url(url)
        self.assertIsNotNone(result)
        self.assertEqual(result["port"], 443)
        self.assertEqual(result["server"], "server.example.com")

    def test_hy2_url_no_sni(self):
        url = "hy2://pass@server.example.com:8443/"
        result = upload_configs.decode_hy2_url(url)
        self.assertIsNotNone(result)
        self.assertIsNone(result["sni"])

    def test_invalid_hy2_url(self):
        result = upload_configs.decode_hy2_url("http://not-hy2.com")
        self.assertIsNone(result)


class TestDecodeProxyUrl(unittest.TestCase):
    def test_ss_url(self):
        encoded = base64.urlsafe_b64encode(b"aes:pass").decode()
        result = upload_configs.decode_proxy_url(f"ss://{encoded}@1.2.3.4:8388")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "ss")

    def test_hy2_url(self):
        result = upload_configs.decode_proxy_url("hy2://pass@server.com:443/")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "hysteria2")

    def test_unknown_type(self):
        result = upload_configs.decode_proxy_url("vmess://something")
        self.assertIsNone(result)

    def test_strips_whitespace(self):
        encoded = base64.urlsafe_b64encode(b"aes:pass").decode()
        result = upload_configs.decode_proxy_url(f"  ss://{encoded}@1.2.3.4:8388  ")
        self.assertIsNotNone(result)


class TestCreateProxyConfig(unittest.TestCase):
    def test_ss_config(self):
        proxy = {
            "type": "ss",
            "server": "1.2.3.4",
            "port": 8388,
            "cipher": "aes-256-gcm",
            "password": "pass",
        }
        result = upload_configs.create_proxy_config(proxy, 0)
        self.assertEqual(result["name"], "My SS 1")
        self.assertEqual(result["type"], "ss")
        self.assertEqual(result["server"], "1.2.3.4")
        self.assertEqual(result["port"], 8388)
        self.assertTrue(result["udp"])
        self.assertEqual(result["plugin"], "")

    def test_hysteria2_config(self):
        proxy = {
            "type": "hysteria2",
            "server": "server.com",
            "port": 443,
            "password": "pass",
            "sni": "sni.com",
        }
        result = upload_configs.create_proxy_config(proxy, 1)
        self.assertEqual(result["name"], "My Hysteria2 2")
        self.assertEqual(result["type"], "hysteria2")
        self.assertEqual(result["sni"], "sni.com")

    def test_hysteria2_no_sni(self):
        proxy = {
            "type": "hysteria2",
            "server": "server.com",
            "port": 443,
            "password": "pass",
        }
        result = upload_configs.create_proxy_config(proxy, 0)
        self.assertNotIn("sni", result)

    def test_unknown_type(self):
        proxy = {"type": "vmess", "server": "1.2.3.4"}
        result = upload_configs.create_proxy_config(proxy, 0)
        self.assertIsNone(result)


class TestUpdateProxyGroups(unittest.TestCase):
    def test_update_existing_proxy_group(self):
        config = {
            "proxy-groups": [
                {"name": "Proxy", "type": "select", "proxies": ["old1"]},
                {"name": "Other", "type": "select", "proxies": []},
            ]
        }
        upload_configs.update_proxy_groups(config, ["new1", "new2"])
        self.assertEqual(config["proxy-groups"][0]["proxies"], ["new1", "new2"])

    def test_create_proxy_group_if_missing(self):
        config = {"proxy-groups": [{"name": "Other", "type": "select", "proxies": []}]}
        upload_configs.update_proxy_groups(config, ["new1"])
        proxy_groups = config["proxy-groups"]
        self.assertEqual(len(proxy_groups), 2)
        self.assertEqual(proxy_groups[-1]["name"], "Proxy")
        self.assertEqual(proxy_groups[-1]["proxies"], ["new1"])


class TestGetFilePath(unittest.TestCase):
    def test_returns_path(self):
        result = upload_configs._get_file_path("test.yaml")
        self.assertIn("test.yaml", result)
        self.assertTrue(os.path.isabs(result))


class TestUploadFile(unittest.TestCase):
    @patch.object(upload_configs, "storage")
    def test_upload_success(self, mock_storage):
        mock_client = MagicMock()
        mock_storage.Client.return_value = mock_client
        mock_bucket = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        result = upload_configs.upload_file("my-bucket", "/tmp/file.yaml", "dest.yaml")
        self.assertIn("my-bucket", result)
        self.assertIn("dest.yaml", result)
        mock_blob.upload_from_filename.assert_called_once_with("/tmp/file.yaml")
        mock_blob.make_public.assert_called_once()

    def test_upload_none_source(self):
        result = upload_configs.upload_file("my-bucket", None, "dest.yaml")
        self.assertIsNone(result)


class TestGenerateSsUrlsFile(unittest.TestCase):
    @patch.object(upload_configs, "_get_file_path")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_ss_urls(self, mock_file, mock_path):
        mock_path.return_value = "/tmp/ss_urls.txt"
        result = upload_configs.generate_ss_urls_file(["url1", "url2"])
        self.assertEqual(result, "/tmp/ss_urls.txt")
        handle = mock_file()
        self.assertEqual(handle.write.call_count, 2)


class TestGenerateSsConfig(unittest.TestCase):
    @patch.object(upload_configs, "_get_file_path")
    def test_generate_ss_config(self, mock_path):
        mock_path.return_value = "/tmp/ss.conf"
        result = upload_configs.generate_ss_config()
        self.assertEqual(result, "/tmp/ss.conf")


class TestGenerateClashConfig(unittest.TestCase):
    @patch.object(upload_configs, "YAML")
    @patch.object(upload_configs, "_get_file_path")
    def test_no_valid_proxies(self, mock_path, mock_yaml_class):
        mock_path.return_value = "/tmp/clash.yaml"
        result = upload_configs.generate_clash_config(["http://invalid.com"])
        self.assertIsNone(result)

    @patch.object(upload_configs, "YAML")
    @patch.object(upload_configs, "_get_file_path")
    def test_empty_urls(self, mock_path, mock_yaml_class):
        result = upload_configs.generate_clash_config([])
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
