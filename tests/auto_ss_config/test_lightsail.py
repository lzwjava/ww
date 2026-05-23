import unittest
from unittest.mock import patch, MagicMock
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.auto_ss_config import lightsail


class TestGetLightsailInstances(unittest.TestCase):
    @patch.object(lightsail, "subprocess")
    @patch.object(lightsail, "yaml")
    def test_success(self, mock_yaml, mock_subprocess):
        mock_result = MagicMock()
        mock_result.stdout = "instances:\n  - name: test\n"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.CalledProcessError = Exception
        mock_yaml.safe_load.return_value = {"instances": [{"name": "test"}]}

        result = lightsail._get_lightsail_instances()
        self.assertIsNotNone(result)
        self.assertIn("instances", result)

    @patch.object(lightsail, "subprocess")
    def test_called_process_error(self, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception
        mock_subprocess.run.side_effect = Exception("command failed")

        result = lightsail._get_lightsail_instances()
        self.assertIsNone(result)

    @patch.object(lightsail, "subprocess")
    @patch.object(lightsail, "yaml")
    def test_yaml_error(self, mock_yaml, mock_subprocess):
        mock_result = MagicMock()
        mock_result.stdout = "invalid"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.CalledProcessError = Exception
        mock_yaml.safe_load.side_effect = Exception("YAML error")
        mock_yaml.YAMLError = Exception

        result = lightsail._get_lightsail_instances()
        self.assertIsNone(result)


class TestGetLightsailInstance(unittest.TestCase):
    @patch.object(lightsail, "subprocess")
    @patch.object(lightsail, "yaml")
    def test_success(self, mock_yaml, mock_subprocess):
        mock_result = MagicMock()
        mock_result.stdout = "instance:\n  name: test\n"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.CalledProcessError = Exception
        mock_yaml.safe_load.return_value = {
            "instance": {"name": "test", "publicIpAddress": "1.2.3.4"}
        }

        result = lightsail._get_lightsail_instance("test")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "test")

    @patch.object(lightsail, "subprocess")
    @patch.object(lightsail, "yaml")
    def test_not_found(self, mock_yaml, mock_subprocess):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.CalledProcessError = Exception
        mock_yaml.safe_load.return_value = {}

        result = lightsail._get_lightsail_instance("nonexistent")
        self.assertIsNone(result)

    @patch.object(lightsail, "subprocess")
    def test_called_process_error(self, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception
        mock_subprocess.run.side_effect = Exception("command failed")

        result = lightsail._get_lightsail_instance("test")
        self.assertIsNone(result)


class TestCreateLightsailInstance(unittest.TestCase):
    @patch.object(lightsail, "subprocess")
    def test_create_with_name(self, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception
        mock_subprocess.run.return_value = None

        result = lightsail.create_lightsail_instance("my-instance")
        self.assertEqual(result, "my-instance")
        mock_subprocess.run.assert_called_once()
        cmd = mock_subprocess.run.call_args[0][0]
        self.assertIn("my-instance", cmd)
        self.assertIn("--blueprint-id", cmd)

    @patch.object(lightsail, "subprocess")
    def test_create_with_random_name(self, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception
        mock_subprocess.run.return_value = None

        result = lightsail.create_lightsail_instance()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)

    @patch.object(lightsail, "subprocess")
    def test_create_failure(self, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception
        mock_subprocess.run.side_effect = Exception("create failed")

        result = lightsail.create_lightsail_instance("test")
        self.assertIsNone(result)

    @patch.object(lightsail, "subprocess")
    def test_create_with_custom_bundle(self, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception
        mock_subprocess.run.return_value = None

        result = lightsail.create_lightsail_instance(
            "test", availability_zone="us-east-1a", bundle_id="medium_2_0"
        )
        self.assertEqual(result, "test")

    @patch.object(lightsail, "subprocess")
    def test_create_with_user_data(self, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception
        mock_subprocess.run.return_value = None

        result = lightsail.create_lightsail_instance(
            "test", user_data="#!/bin/bash\necho hello"
        )
        self.assertEqual(result, "test")


class TestDeleteAllLightsailInstances(unittest.TestCase):
    @patch.object(lightsail, "subprocess")
    def test_delete_specific_instance(self, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception

        lightsail.delete_all_lightsail_instances("my-instance")
        mock_subprocess.run.assert_called_once()
        cmd = mock_subprocess.run.call_args[0][0]
        self.assertIn("delete-instance", cmd)
        self.assertIn("my-instance", cmd)

    @patch.object(lightsail, "_get_lightsail_instances")
    def test_delete_no_instances(self, mock_get):
        mock_get.return_value = None
        lightsail.delete_all_lightsail_instances()

    @patch.object(lightsail, "_get_lightsail_instances")
    def test_delete_empty_instances(self, mock_get):
        mock_get.return_value = {"instances": []}
        lightsail.delete_all_lightsail_instances()

    @patch.object(lightsail, "subprocess")
    @patch.object(lightsail, "_get_lightsail_instances")
    def test_delete_all(self, mock_get, mock_subprocess):
        mock_subprocess.CalledProcessError = Exception
        mock_get.return_value = {"instances": [{"name": "inst1"}, {"name": "inst2"}]}

        lightsail.delete_all_lightsail_instances()
        self.assertEqual(mock_subprocess.run.call_count, 2)


class TestInstallOutlineServer(unittest.TestCase):
    @patch.object(lightsail, "os")
    @patch.object(lightsail, "subprocess")
    @patch.object(lightsail, "_get_lightsail_instance")
    def test_install_success(self, mock_get, mock_subprocess, mock_os):
        mock_subprocess.CalledProcessError = Exception
        mock_get.return_value = {"name": "test", "publicIpAddress": "1.2.3.4"}

        lightsail.install_outline_server("test")
        mock_os.chmod.assert_called_once()
        mock_subprocess.run.assert_called_once()

    @patch.object(lightsail, "_get_lightsail_instance")
    def test_instance_not_found(self, mock_get):
        mock_get.return_value = None
        # Should return without error
        lightsail.install_outline_server("nonexistent")


class TestOpenFirewallPorts(unittest.TestCase):
    @patch.object(lightsail, "subprocess")
    def test_opens_tcp_and_udp(self, mock_subprocess):
        lightsail.open_firewall_ports("test-instance")
        self.assertEqual(mock_subprocess.run.call_count, 2)
        # Check one call is for tcp and one for udp
        calls = [str(c) for c in mock_subprocess.run.call_args_list]
        tcp_found = any("tcp" in c for c in calls)
        udp_found = any("udp" in c for c in calls)
        self.assertTrue(tcp_found)
        self.assertTrue(udp_found)


if __name__ == "__main__":
    unittest.main()
