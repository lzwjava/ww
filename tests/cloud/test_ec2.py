import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

try:
    from ww.cloud import ec2

    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False
    ec2 = MagicMock()


def setUpModule():
    if not _HAS_DEPS:
        raise unittest.SkipTest("Missing optional dependency: PyYAML")


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
class TestGetEc2Instances(unittest.TestCase):
    @patch("ww.cloud.ec2.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Reservations:\n- Instances:\n  - InstanceId: i-123\n",
            returncode=0,
        )
        with patch(
            "ww.cloud.ec2.yaml.safe_load",
            return_value={"Reservations": [{"Instances": [{"InstanceId": "i-123"}]}]},
        ):
            result = ec2._get_ec2_instances()
            self.assertIsNotNone(result)
            self.assertIn("Reservations", result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_called_process_error(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "aws")
        result = ec2._get_ec2_instances()
        self.assertIsNone(result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_yaml_error(self, mock_run):
        mock_run.return_value = MagicMock(stdout="invalid: yaml: {{{", returncode=0)
        with patch(
            "ww.cloud.ec2.yaml.safe_load", side_effect=ec2.yaml.YAMLError("bad yaml")
        ):
            result = ec2._get_ec2_instances()
            self.assertIsNone(result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_unexpected_error(self, mock_run):
        mock_run.side_effect = RuntimeError("unexpected")
        result = ec2._get_ec2_instances()
        self.assertIsNone(result)


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
class TestGetEc2Instance(unittest.TestCase):
    @patch("ww.cloud.ec2.subprocess.run")
    def test_success(self, mock_run):
        instance_data = {
            "Reservations": [
                {"Instances": [{"InstanceId": "i-abc", "PublicIpAddress": "1.2.3.4"}]}
            ]
        }
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch("ww.cloud.ec2.yaml.safe_load", return_value=instance_data):
            result = ec2._get_ec2_instance("i-abc")
            self.assertIsNotNone(result)
            self.assertEqual(result["InstanceId"], "i-abc")

    @patch("ww.cloud.ec2.subprocess.run")
    def test_instance_not_found(self, mock_run):
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch("ww.cloud.ec2.yaml.safe_load", return_value={"Reservations": []}):
            result = ec2._get_ec2_instance("i-missing")
            self.assertIsNone(result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_no_reservations_key(self, mock_run):
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch("ww.cloud.ec2.yaml.safe_load", return_value={}):
            result = ec2._get_ec2_instance("i-abc")
            self.assertIsNone(result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_no_instances_in_reservation(self, mock_run):
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch("ww.cloud.ec2.yaml.safe_load", return_value={"Reservations": [{}]}):
            result = ec2._get_ec2_instance("i-abc")
            self.assertIsNone(result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_empty_instances(self, mock_run):
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch(
            "ww.cloud.ec2.yaml.safe_load",
            return_value={"Reservations": [{"Instances": []}]},
        ):
            result = ec2._get_ec2_instance("i-abc")
            self.assertIsNone(result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_called_process_error(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "aws")
        result = ec2._get_ec2_instance("i-abc")
        self.assertIsNone(result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_yaml_error(self, mock_run):
        mock_run.return_value = MagicMock(stdout="bad", returncode=0)
        with patch(
            "ww.cloud.ec2.yaml.safe_load", side_effect=ec2.yaml.YAMLError("bad")
        ):
            result = ec2._get_ec2_instance("i-abc")
            self.assertIsNone(result)


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
class TestCreateEc2Instance(unittest.TestCase):
    @patch("ww.cloud.ec2.subprocess.run")
    def test_success_with_name(self, mock_run):
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch(
            "ww.cloud.ec2.yaml.safe_load",
            return_value={"Instances": [{"InstanceId": "i-new"}]},
        ):
            result = ec2.create_ec2_instance(instance_name="test-instance")
            self.assertEqual(result, "i-new")

    @patch("ww.cloud.ec2.subprocess.run")
    def test_success_random_name(self, mock_run):
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch(
            "ww.cloud.ec2.yaml.safe_load",
            return_value={"Instances": [{"InstanceId": "i-rand"}]},
        ):
            result = ec2.create_ec2_instance()
            self.assertEqual(result, "i-rand")

    @patch("ww.cloud.ec2.subprocess.run")
    def test_custom_user_data(self, mock_run):
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch(
            "ww.cloud.ec2.yaml.safe_load",
            return_value={"Instances": [{"InstanceId": "i-custom"}]},
        ):
            result = ec2.create_ec2_instance(
                instance_name="test", user_data="#!/bin/bash\necho hello"
            )
            self.assertEqual(result, "i-custom")

    @patch("ww.cloud.ec2.subprocess.run")
    def test_called_process_error(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "aws")
        result = ec2.create_ec2_instance(instance_name="fail")
        self.assertIsNone(result)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_custom_type_and_zone(self, mock_run):
        mock_run.return_value = MagicMock(stdout="yaml", returncode=0)
        with patch(
            "ww.cloud.ec2.yaml.safe_load",
            return_value={"Instances": [{"InstanceId": "i-t"}]},
        ):
            result = ec2.create_ec2_instance(
                instance_name="test",
                instance_type="t3.large",
                availability_zone="ap-east-1b",
            )
            self.assertEqual(result, "i-t")


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
class TestDeleteAllEc2Instances(unittest.TestCase):
    @patch("ww.cloud.ec2.subprocess.run")
    def test_delete_specific_instance(self, mock_run):
        ec2.delete_all_ec2_instances(instance_id="i-del")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("i-del", args)

    @patch("ww.cloud.ec2.subprocess.run")
    def test_delete_specific_instance_error(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "aws")
        # Should not raise
        ec2.delete_all_ec2_instances(instance_id="i-fail")

    @patch("ww.cloud.ec2._get_ec2_instances")
    def test_delete_all_no_instances(self, mock_instances):
        mock_instances.return_value = None
        ec2.delete_all_ec2_instances()

    @patch("ww.cloud.ec2._get_ec2_instances")
    def test_delete_all_no_reservations(self, mock_instances):
        mock_instances.return_value = {}
        ec2.delete_all_ec2_instances()

    @patch("ww.cloud.ec2._get_ec2_instances")
    def test_delete_all_empty_reservations(self, mock_instances):
        mock_instances.return_value = {"Reservations": []}
        ec2.delete_all_ec2_instances()

    @patch("ww.cloud.ec2.subprocess.run")
    @patch("ww.cloud.ec2._get_ec2_instances")
    def test_delete_all_success(self, mock_instances, mock_run):
        mock_instances.return_value = {
            "Reservations": [
                {"Instances": [{"InstanceId": "i-1"}, {"InstanceId": "i-2"}]}
            ]
        }
        ec2.delete_all_ec2_instances()
        self.assertEqual(mock_run.call_count, 2)

    @patch("ww.cloud.ec2._get_ec2_instances")
    def test_delete_all_empty_instances_list(self, mock_instances):
        mock_instances.return_value = {"Reservations": [{"Instances": []}]}
        ec2.delete_all_ec2_instances()


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
class TestInstallOutlineServer(unittest.TestCase):
    @patch("ww.cloud.ec2.subprocess.run")
    @patch("ww.cloud.ec2._get_ec2_instance")
    @patch("ww.cloud.ec2.os.chmod")
    def test_success(self, mock_chmod, mock_get, mock_run):
        mock_get.return_value = {"InstanceId": "i-1", "PublicIpAddress": "1.2.3.4"}
        ec2.install_outline_server("i-1")
        mock_chmod.assert_called_once()
        mock_run.assert_called_once()

    @patch("ww.cloud.ec2._get_ec2_instance")
    def test_instance_not_found(self, mock_get):
        mock_get.return_value = None
        ec2.install_outline_server("i-missing")

    @patch("ww.cloud.ec2.subprocess.run")
    @patch("ww.cloud.ec2._get_ec2_instance")
    @patch("ww.cloud.ec2.os.chmod")
    def test_ssh_error(self, mock_chmod, mock_get, mock_run):
        import subprocess

        mock_get.return_value = {"InstanceId": "i-1", "PublicIpAddress": "1.2.3.4"}
        mock_run.side_effect = subprocess.CalledProcessError(1, "ssh")
        ec2.install_outline_server("i-1")


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: PyYAML")
class TestOpenFirewallPorts(unittest.TestCase):
    @patch("ww.cloud.ec2.subprocess.run")
    @patch("ww.cloud.ec2._get_ec2_instance")
    def test_success(self, mock_get, mock_run):
        mock_get.return_value = {
            "InstanceId": "i-1",
            "SecurityGroups": [{"GroupId": "sg-123"}],
        }
        ec2.open_firewall_ports("i-1")
        self.assertEqual(mock_run.call_count, 2)  # tcp + udp

    @patch("ww.cloud.ec2._get_ec2_instance")
    def test_instance_not_found(self, mock_get):
        mock_get.return_value = None
        ec2.open_firewall_ports("i-missing")

    @patch("ww.cloud.ec2._get_ec2_instance")
    def test_no_security_groups(self, mock_get):
        mock_get.return_value = {"InstanceId": "i-1", "SecurityGroups": []}
        ec2.open_firewall_ports("i-1")


if __name__ == "__main__":
    unittest.main()
