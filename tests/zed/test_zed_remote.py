import unittest

from ww.zed.zed_remote import _build_ssh_url, REMOTE_USER, REMOTE_HOST, DEFAULT_PREFIX


class TestBuildSshUrl(unittest.TestCase):
    def test_absolute_path(self):
        result = _build_ssh_url("/home/lzw/projects")
        self.assertEqual(result, f"ssh://{REMOTE_USER}@{REMOTE_HOST}/home/lzw/projects")

    def test_tilde_path(self):
        result = _build_ssh_url("~/projects")
        self.assertEqual(result, f"ssh://{REMOTE_USER}@{REMOTE_HOST}~/projects")

    def test_bare_name_maps_to_default_prefix(self):
        result = _build_ssh_url("zz")
        self.assertEqual(
            result, f"ssh://{REMOTE_USER}@{REMOTE_HOST}{DEFAULT_PREFIX}/zz"
        )

    def test_empty_path_defaults_to_root(self):
        result = _build_ssh_url("")
        self.assertEqual(result, f"ssh://{REMOTE_USER}@{REMOTE_HOST}/")

    def test_whitespace_only_defaults_to_root(self):
        result = _build_ssh_url("   ")
        self.assertEqual(result, f"ssh://{REMOTE_USER}@{REMOTE_HOST}/")

    def test_path_with_slash_not_prefixed(self):
        result = _build_ssh_url("mnt/data/project")
        self.assertEqual(result, f"ssh://{REMOTE_USER}@{REMOTE_HOST}/mnt/data/project")

    def test_root_path(self):
        result = _build_ssh_url("/")
        self.assertEqual(result, f"ssh://{REMOTE_USER}@{REMOTE_HOST}/")

    def test_deep_nested_bare_name(self):
        result = _build_ssh_url("deepseek-v4")
        self.assertEqual(
            result, f"ssh://{REMOTE_USER}@{REMOTE_HOST}{DEFAULT_PREFIX}/deepseek-v4"
        )

    def test_url_format_prefix(self):
        result = _build_ssh_url("/test")
        self.assertTrue(result.startswith("ssh://"))


if __name__ == "__main__":
    unittest.main()
