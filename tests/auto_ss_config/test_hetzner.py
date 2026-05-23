import unittest
from unittest.mock import patch, MagicMock
import os
import sys

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

# Mock hcloud before import since hetzner.py uses module-level code
hcloud_mock = MagicMock()
sys.modules["hcloud"] = hcloud_mock
sys.modules["hcloud.hcloud"] = hcloud_mock

# Patch sys.argv before import to avoid argparse issues at module level
_original_argv = sys.argv
sys.argv = ["hetzner.py", "--create-snapshot"]
os.environ.setdefault("HERTZNER_API_KEY", "test-key")

from ww.auto_ss_config import hetzner

sys.argv = _original_argv


def _reset_client():
    """Reset all side effects on the module-level client mock."""
    hetzner.client.servers.create_image.side_effect = None
    hetzner.client.images.get_by_id.side_effect = None
    hetzner.client.servers.create.side_effect = None


class TestCreateSnapshot(unittest.TestCase):
    def setUp(self):
        _reset_client()

    def test_create_success(self):
        server = MagicMock()
        server.name = "test-server"
        response = MagicMock()
        response.image.id = "img-123"
        hetzner.client.servers.create_image.return_value = response

        result = hetzner.create_snapshot(server)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "img-123")

    def test_create_locked_error(self):
        server = MagicMock()
        server.name = "test-server"
        hetzner.client.servers.create_image.side_effect = Exception("Server is locked")

        result = hetzner.create_snapshot(server)
        self.assertIsNone(result)

    def test_create_other_error(self):
        server = MagicMock()
        server.name = "test-server"
        hetzner.client.servers.create_image.side_effect = Exception("Some other error")

        result = hetzner.create_snapshot(server)
        self.assertIsNone(result)


class TestCreateServerFromSnapshot(unittest.TestCase):
    def setUp(self):
        _reset_client()

    @patch("ww.auto_ss_config.hetzner.time")
    def test_create_success_first_attempt(self, mock_time):
        source = MagicMock()
        source.name = "source-server"
        source.server_type.name = "cx21"
        source.datacenter.name = "dc1"
        source.datacenter.location.name = "fsn1"

        snapshot = MagicMock()
        snapshot.status = "available"
        hetzner.client.images.get_by_id.return_value = snapshot

        response = MagicMock()
        response.server.id = "new-srv-123"
        response.root_password = "secret"
        hetzner.client.servers.create.return_value = response

        result = hetzner.create_server_from_snapshot("snap-123", source)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "new-srv-123")

    @patch("ww.auto_ss_config.hetzner.time")
    def test_create_custom_name(self, mock_time):
        source = MagicMock()
        source.name = "source-server"
        source.server_type.name = "cx21"
        source.datacenter.name = "dc1"
        source.datacenter.location.name = "fsn1"

        snapshot = MagicMock()
        snapshot.status = "available"
        hetzner.client.images.get_by_id.return_value = snapshot

        response = MagicMock()
        response.server.id = "new-srv-456"
        response.root_password = "pass"
        hetzner.client.servers.create.return_value = response

        result = hetzner.create_server_from_snapshot(
            "snap-123", source, new_name="my-custom"
        )
        self.assertIsNotNone(result)

    @patch("ww.auto_ss_config.hetzner.time")
    def test_snapshot_never_becomes_available(self, mock_time):
        source = MagicMock()
        source.name = "source-server"

        snapshot = MagicMock()
        snapshot.status = "creating"
        hetzner.client.images.get_by_id.return_value = snapshot

        result = hetzner.create_server_from_snapshot("snap-123", source)
        self.assertIsNone(result)

    @patch("ww.auto_ss_config.hetzner.time")
    def test_snapshot_not_found(self, mock_time):
        source = MagicMock()
        source.name = "source-server"
        hetzner.client.images.get_by_id.side_effect = Exception("Not found")

        result = hetzner.create_server_from_snapshot("bad-snap", source)
        self.assertIsNone(result)

    @patch("ww.auto_ss_config.hetzner.time")
    def test_server_creation_error(self, mock_time):
        source = MagicMock()
        source.name = "source-server"
        source.server_type.name = "cx21"
        source.datacenter.name = "dc1"
        source.datacenter.location.name = "fsn1"

        snapshot = MagicMock()
        snapshot.status = "available"
        hetzner.client.images.get_by_id.return_value = snapshot
        hetzner.client.servers.create.side_effect = Exception("Quota exceeded")

        result = hetzner.create_server_from_snapshot("snap-123", source)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
