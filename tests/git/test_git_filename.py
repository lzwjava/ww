import subprocess
import unittest
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestCheckGitFilenames(unittest.TestCase):
    @patch("subprocess.run")
    def test_valid_filenames_returns_true(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(
            returncode=0, stdout="src/main.py\nREADME.md\n"
        )
        self.assertTrue(check_git_filenames())

    @patch("subprocess.run")
    def test_filename_with_spaces_returns_false(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(
            returncode=0, stdout="src/file with spaces.py\n"
        )
        self.assertFalse(check_git_filenames())

    @patch("subprocess.run")
    def test_markdown_with_hyphens_is_valid(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(
            returncode=0, stdout="notes/2024-01-01-hello-world.md\n"
        )
        self.assertTrue(check_git_filenames())

    @patch("subprocess.run")
    def test_special_chars_in_non_md_returns_false(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(returncode=0, stdout="src/café.py\n")
        self.assertFalse(check_git_filenames())

    @patch("subprocess.run")
    def test_subprocess_error_returns_false(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        self.assertFalse(check_git_filenames())

    @patch("subprocess.run")
    def test_empty_file_list_returns_true(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(returncode=0, stdout="")
        self.assertTrue(check_git_filenames())


if __name__ == "__main__":
    unittest.main()
