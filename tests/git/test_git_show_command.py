import subprocess
import unittest
from unittest.mock import patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestFormatFileList(unittest.TestCase):
    def setUp(self):
        from ww.git.git_show_command import format_file_list

        self.func = format_file_list

    def test_returns_none_for_empty_list(self):
        result = self.func([], "Files")
        self.assertIn("None", result)
        self.assertIn("Files", result)

    def test_numbers_files_sequentially(self):
        result = self.func(["a.py", "b.py"], "Files")
        self.assertIn("1.", result)
        self.assertIn("2.", result)

    def test_includes_filenames(self):
        result = self.func(["a.py", "b.md"], "Changed")
        self.assertIn("a.py", result)
        self.assertIn("b.md", result)

    def test_includes_title(self):
        result = self.func(["a.py"], "Python files")
        self.assertIn("Python files", result)


class TestGetLastCommitInfo(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_returns_dict_with_expected_keys(self, mock_out):
        from ww.git.git_show_command import get_last_commit_info

        mock_out.side_effect = [
            "abc123def456 feat: add feature",
            "\na.py\nb.md\n",
        ]
        result = get_last_commit_info()
        assert result is not None
        self.assertIn("hash", result)
        self.assertIn("message", result)
        self.assertIn("python_files", result)
        self.assertIn("all_files", result)

    @patch("subprocess.check_output")
    def test_truncates_hash_to_8_chars(self, mock_out):
        from ww.git.git_show_command import get_last_commit_info

        mock_out.side_effect = [
            "abc123def456 feat: add feature",
            "\na.py\n",
        ]
        result = get_last_commit_info()
        assert result is not None
        self.assertEqual(len(result["hash"]), 8)
        self.assertEqual(result["hash"], "abc123de")

    @patch("subprocess.check_output")
    def test_filters_python_files_correctly(self, mock_out):
        from ww.git.git_show_command import get_last_commit_info

        mock_out.side_effect = [
            "abc123def456 chore: update",
            "\na.py\nb.md\nc.js\n",
        ]
        result = get_last_commit_info()
        assert result is not None
        self.assertIn("a.py", result["python_files"])
        self.assertNotIn("b.md", result["python_files"])
        self.assertNotIn("c.js", result["python_files"])

    @patch(
        "subprocess.check_output",
        side_effect=subprocess.CalledProcessError(1, "git"),
    )
    def test_returns_none_on_subprocess_error(self, mock_out):
        from ww.git.git_show_command import get_last_commit_info

        result = get_last_commit_info()
        self.assertIsNone(result)


class TestMain(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_main_returns_zero_with_python_files(self, mock_out):
        from ww.git.git_show_command import main

        mock_out.side_effect = [
            "abc123def456 feat: add feature",
            "\nww/main.py\nREADME.md\n",
        ]
        with patch("builtins.print"):
            with patch("os.path.exists", return_value=True):
                result = main()
        self.assertEqual(result, 0)

    @patch("subprocess.check_output")
    def test_main_returns_zero_with_no_python_files(self, mock_out):
        from ww.git.git_show_command import main

        mock_out.side_effect = [
            "abc123def456 docs: update readme",
            "\nREADME.md\n",
        ]
        with patch("builtins.print"):
            result = main()
        self.assertEqual(result, 0)

    @patch(
        "subprocess.check_output",
        side_effect=subprocess.CalledProcessError(1, "git"),
    )
    def test_main_returns_one_when_git_fails(self, mock_out):
        from ww.git.git_show_command import main

        with patch("builtins.print"):
            result = main()
        self.assertEqual(result, 1)

    @patch("subprocess.check_output")
    def test_main_copies_to_clipboard_when_pyperclip_available(self, mock_out):
        from ww.git.git_show_command import main
        import ww.git.git_show_command as module

        mock_out.side_effect = [
            "abc123def456 feat: clipboard",
            "\nscript.py\n",
        ]
        original = module.CLIPBOARD_AVAILABLE
        try:
            module.CLIPBOARD_AVAILABLE = True
            with patch("pyperclip.copy") as mock_copy:
                with patch("builtins.print"):
                    with patch("os.path.exists", return_value=True):
                        main()
                mock_copy.assert_called_once_with("python script.py")
        finally:
            module.CLIPBOARD_AVAILABLE = original


if __name__ == "__main__":
    unittest.main()
