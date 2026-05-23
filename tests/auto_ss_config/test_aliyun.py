import unittest
from unittest.mock import patch, MagicMock
import os
import sys

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

# Mock all alibaba cloud SDK modules before import
for mod_name in [
    "alibabacloud_vpc20160428",
    "alibabacloud_vpc20160428.client",
    "alibabacloud_tea_openapi",
    "alibabacloud_tea_openapi.models",
    "alibabacloud_vpc20160428.models",
    "alibabacloud_tea_util",
    "alibabacloud_tea_util.client",
    "alibabacloud_tea_util.models",
]:
    sys.modules[mod_name] = MagicMock()

from ww.auto_ss_config import aliyun_elastic_ip_manager
from ww.auto_ss_config.aliyun_elastic_ip_manager import Sample

# Fix UtilClient mock - MagicMock blocks attributes starting with 'assert'
aliyun_elastic_ip_manager.UtilClient.assert_as_string = MagicMock()


class TestCreateClient(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ACCESS_ID_API_KEY": "test_id",
            "ALIBABA_CLOUD_ACCESS_API_KEY": "test_secret",
        },
    )
    @patch.object(aliyun_elastic_ip_manager, "Vpc20160428Client")
    @patch.object(aliyun_elastic_ip_manager, "open_api_models")
    def test_create_client(self, mock_models, mock_client):
        mock_config = MagicMock()
        mock_models.Config.return_value = mock_config
        result = Sample.create_client()
        mock_models.Config.assert_called_once()
        mock_client.assert_called_once_with(mock_config)
        self.assertEqual(mock_config.endpoint, "vpc.cn-hongkong.aliyuncs.com")


class TestBindEip(unittest.TestCase):
    @patch.object(Sample, "create_client")
    def test_bind_success(self, mock_create):
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        result = Sample.bind_eip("cn-hongkong", "eip-123", "i-456")
        self.assertTrue(result)
        mock_client.associate_eip_address_with_options.assert_called_once()

    @patch.object(Sample, "create_client")
    def test_bind_failure(self, mock_create):
        mock_client = MagicMock()
        mock_client.associate_eip_address_with_options.side_effect = Exception(
            "API error"
        )
        mock_create.return_value = mock_client
        result = Sample.bind_eip("cn-hongkong", "eip-123", "i-456")
        self.assertFalse(result)

    @patch.object(Sample, "create_client")
    def test_bind_error_with_message_and_data(self, mock_create):
        mock_client = MagicMock()
        error = Exception("API error")
        error.message = "detailed message"
        error.data = {"Recommend": "try again"}
        mock_client.associate_eip_address_with_options.side_effect = error
        mock_create.return_value = mock_client
        result = Sample.bind_eip("cn-hongkong", "eip-123", "i-456")
        self.assertFalse(result)


class TestUnbindEip(unittest.TestCase):
    @patch.object(Sample, "create_client")
    def test_unbind_success(self, mock_create):
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        result = Sample.unbind_eip("cn-hongkong", "eip-123", "i-456")
        self.assertTrue(result)
        mock_client.unassociate_eip_address_with_options.assert_called_once()

    @patch.object(Sample, "create_client")
    def test_unbind_failure(self, mock_create):
        mock_client = MagicMock()
        mock_client.unassociate_eip_address_with_options.side_effect = Exception(
            "error"
        )
        mock_create.return_value = mock_client
        result = Sample.unbind_eip("cn-hongkong", "eip-123", "i-456")
        self.assertFalse(result)


class TestCreateEip(unittest.TestCase):
    @patch.object(Sample, "create_client")
    def test_create_success(self, mock_create):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.body.allocation_id = "eip-new-123"
        mock_client.allocate_eip_address_with_options.return_value = mock_result
        mock_create.return_value = mock_client
        result = Sample.create_eip("cn-hongkong")
        self.assertEqual(result, "eip-new-123")

    @patch.object(Sample, "create_client")
    def test_create_failure(self, mock_create):
        mock_client = MagicMock()
        mock_client.allocate_eip_address_with_options.side_effect = Exception("error")
        mock_create.return_value = mock_client
        result = Sample.create_eip("cn-hongkong")
        self.assertIsNone(result)


class TestReleaseEip(unittest.TestCase):
    @patch.object(Sample, "create_client")
    def test_release_success(self, mock_create):
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        result = Sample.release_eip("eip-123")
        self.assertTrue(result)
        mock_client.release_eip_address_with_options.assert_called_once()

    @patch.object(Sample, "create_client")
    def test_release_failure(self, mock_create):
        mock_client = MagicMock()
        mock_client.release_eip_address_with_options.side_effect = Exception("error")
        mock_create.return_value = mock_client
        result = Sample.release_eip("eip-123")
        self.assertFalse(result)


class TestDescribeEip(unittest.TestCase):
    @patch.object(Sample, "create_client")
    def test_describe_found(self, mock_create):
        mock_client = MagicMock()
        mock_eip = MagicMock()
        mock_eip.instance_id = "i-456"
        mock_eip.allocation_id = "eip-789"
        mock_result = MagicMock()
        mock_result.body.eip_addresses.eip_address = [mock_eip]
        mock_result.body.to_map.return_value = {}
        mock_client.describe_eip_addresses_with_options.return_value = mock_result
        mock_create.return_value = mock_client
        result = Sample.describe_eip("cn-hongkong", "i-456")
        self.assertEqual(result, "eip-789")

    @patch.object(Sample, "create_client")
    def test_describe_not_found(self, mock_create):
        mock_client = MagicMock()
        mock_eip = MagicMock()
        mock_eip.instance_id = "i-other"
        mock_eip.allocation_id = "eip-other"
        mock_result = MagicMock()
        mock_result.body.eip_addresses.eip_address = [mock_eip]
        mock_result.body.to_map.return_value = {}
        mock_client.describe_eip_addresses_with_options.return_value = mock_result
        mock_create.return_value = mock_client
        result = Sample.describe_eip("cn-hongkong", "i-456")
        self.assertIsNone(result)

    @patch.object(Sample, "create_client")
    def test_describe_no_addresses(self, mock_create):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.body.eip_addresses = None
        mock_result.body.to_map.return_value = {}
        mock_client.describe_eip_addresses_with_options.return_value = mock_result
        mock_create.return_value = mock_client
        result = Sample.describe_eip("cn-hongkong", "i-456")
        self.assertIsNone(result)

    @patch.object(Sample, "create_client")
    def test_describe_failure(self, mock_create):
        mock_client = MagicMock()
        mock_client.describe_eip_addresses_with_options.side_effect = Exception("error")
        mock_create.return_value = mock_client
        result = Sample.describe_eip("cn-hongkong", "i-456")
        self.assertIsNone(result)

    @patch.object(Sample, "create_client")
    def test_describe_no_eip_address_list(self, mock_create):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.body.eip_addresses = MagicMock(spec=[])
        mock_result.body.eip_addresses.eip_address = None
        mock_result.body.to_map.return_value = {}
        mock_client.describe_eip_addresses_with_options.return_value = mock_result
        mock_create.return_value = mock_client
        result = Sample.describe_eip("cn-hongkong", "i-456")
        self.assertIsNone(result)


class TestMain(unittest.TestCase):
    @patch.object(Sample, "create_eip")
    def test_main_create_success(self, mock_create):
        mock_create.return_value = "eip-new"
        Sample.main(["create"])
        mock_create.assert_called_once_with("cn-hongkong")

    @patch.object(Sample, "create_eip")
    def test_main_create_failure(self, mock_create):
        mock_create.return_value = None
        Sample.main(["create"])

    @patch.object(Sample, "bind_eip")
    def test_main_bind_success(self, mock_bind):
        mock_bind.return_value = True
        Sample.main(["bind", "--allocation_id", "eip-123"])

    @patch.object(Sample, "bind_eip")
    def test_main_bind_failure(self, mock_bind):
        mock_bind.return_value = False
        Sample.main(["bind", "--allocation_id", "eip-123"])

    def test_main_bind_no_allocation_id(self):
        Sample.main(["bind"])

    @patch.object(Sample, "unbind_eip")
    def test_main_unbind_success(self, mock_unbind):
        mock_unbind.return_value = True
        Sample.main(["unbind", "--allocation_id", "eip-123"])

    def test_main_unbind_no_allocation_id(self):
        Sample.main(["unbind"])

    @patch.object(Sample, "release_eip")
    def test_main_release_success(self, mock_release):
        mock_release.return_value = True
        Sample.main(["release", "--allocation_id", "eip-123"])

    def test_main_release_no_allocation_id(self):
        Sample.main(["release"])

    @patch.object(Sample, "describe_eip")
    def test_main_describe_found(self, mock_describe):
        mock_describe.return_value = "eip-789"
        Sample.main(["describe"])

    @patch.object(Sample, "describe_eip")
    def test_main_describe_not_found(self, mock_describe):
        mock_describe.return_value = None
        Sample.main(["describe"])

    @patch.object(Sample, "describe_eip")
    @patch.object(Sample, "unbind_eip")
    @patch.object(Sample, "create_eip")
    @patch.object(Sample, "bind_eip")
    @patch.object(Sample, "release_eip")
    def test_main_all_success(
        self, mock_release, mock_bind, mock_create, mock_unbind, mock_describe
    ):
        mock_describe.side_effect = ["eip-old", "eip-new"]
        mock_unbind.return_value = True
        mock_create.return_value = "eip-new"
        mock_bind.return_value = True
        mock_release.return_value = True
        Sample.main(["all"])
        mock_describe.assert_called()
        mock_unbind.assert_called_once()
        mock_create.assert_called_once()
        mock_bind.assert_called_once()
        mock_release.assert_called_once_with("eip-old")

    @patch.object(Sample, "describe_eip")
    def test_main_all_no_eip(self, mock_describe):
        mock_describe.return_value = None
        Sample.main(["all"])

    @patch.object(Sample, "describe_eip")
    @patch.object(Sample, "unbind_eip")
    def test_main_all_unbind_failure(self, mock_unbind, mock_describe):
        mock_describe.return_value = "eip-old"
        mock_unbind.return_value = False
        Sample.main(["all"])

    @patch.object(Sample, "describe_eip")
    @patch.object(Sample, "unbind_eip")
    @patch.object(Sample, "create_eip")
    def test_main_all_create_failure(self, mock_create, mock_unbind, mock_describe):
        mock_describe.return_value = "eip-old"
        mock_unbind.return_value = True
        mock_create.return_value = None
        Sample.main(["all"])

    @patch.object(Sample, "describe_eip")
    @patch.object(Sample, "unbind_eip")
    @patch.object(Sample, "create_eip")
    @patch.object(Sample, "bind_eip")
    def test_main_all_bind_failure(
        self, mock_bind, mock_create, mock_unbind, mock_describe
    ):
        mock_describe.side_effect = ["eip-old", "eip-new"]
        mock_unbind.return_value = True
        mock_create.return_value = "eip-new"
        mock_bind.return_value = False
        Sample.main(["all"])

    @patch.object(Sample, "describe_eip")
    @patch.object(Sample, "unbind_eip")
    @patch.object(Sample, "create_eip")
    @patch.object(Sample, "bind_eip")
    @patch.object(Sample, "release_eip")
    def test_main_all_release_failure(
        self, mock_release, mock_bind, mock_create, mock_unbind, mock_describe
    ):
        mock_describe.side_effect = ["eip-old", None]
        mock_unbind.return_value = True
        mock_create.return_value = "eip-new"
        mock_bind.return_value = True
        mock_release.return_value = False
        Sample.main(["all"])


if __name__ == "__main__":
    unittest.main()
