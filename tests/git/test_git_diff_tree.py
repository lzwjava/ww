import subprocess
import unittest
from unittest.mock import patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestListFilesExcludingExt(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_excludes_specified_extension(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.return_value = "a.py\nb.js\nc.md\n"
        result = list_files_excluding_ext("/repo", "abc123", "py")
        self.assertNotIn("a.py", result)
        self.assertIn("b.js", result)
        self.assertIn("c.md", result)

    @patch("subprocess.check_output")
    def test_handles_leading_dot_in_extension(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.return_value = "a.py\nb.js\n"
        result = list_files_excluding_ext("/repo", "abc123", ".py")
        self.assertNotIn("a.py", result)
        self.assertIn("b.js", result)

    @patch("subprocess.check_output")
    def test_raises_runtime_error_on_failure(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.side_effect = subprocess.CalledProcessError(1, "git")
        with self.assertRaises(RuntimeError):
            list_files_excluding_ext("/repo", "abc123", "py")

    @patch("subprocess.check_output")
    def test_case_insensitive_extension_matching(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.return_value = "a.PY\nb.js\n"
        result = list_files_excluding_ext("/repo", "abc123", "py")
        self.assertNotIn("a.PY", result)
        self.assertIn("b.js", result)

    @patch("subprocess.check_output")
    def test_returns_empty_list_when_all_excluded(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.return_value = "a.py\nb.py\n"
        result = list_files_excluding_ext("/repo", "abc123", "py")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
