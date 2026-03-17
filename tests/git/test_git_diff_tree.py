import sys
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


class TestMain(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_main_prints_files_changed(self, mock_out):
        from ww.git.git_diff_tree import main

        mock_out.return_value = "a.py\nb.js\nc.md\n"
        with patch.object(sys, "argv", ["git_diff_tree", "/repo", "abc123"]):
            with patch("builtins.print") as mock_print:
                main()
                output = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("b.js", output)
                self.assertIn("c.md", output)

    @patch("subprocess.check_output")
    def test_main_prints_no_files_message_when_all_excluded(self, mock_out):
        from ww.git.git_diff_tree import main

        mock_out.return_value = "a.py\nb.py\n"
        with patch.object(sys, "argv", ["git_diff_tree", "/repo", "abc123"]):
            with patch("builtins.print") as mock_print:
                main()
                output = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("No files", output)

    @patch(
        "subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")
    )
    def test_main_handles_git_failure(self, mock_out):
        from ww.git.git_diff_tree import main

        with patch.object(sys, "argv", ["git_diff_tree", "/repo", "abc123"]):
            with patch("builtins.print"):
                main()  # should not raise


if __name__ == "__main__":
    unittest.main()
