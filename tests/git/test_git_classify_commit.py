import sys
import subprocess
import unittest
from unittest.mock import patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestClassifyCommit(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_classifies_python_file_as_code(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "src/main.py\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "code")

    @patch("subprocess.check_output")
    def test_classifies_markdown_file_as_md(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "README.md\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "md")

    @patch("subprocess.check_output")
    def test_classifies_yaml_as_others(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "config.yaml\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "others")

    @patch("subprocess.check_output")
    def test_returns_none_on_empty_output(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "\n"
        self.assertIsNone(classify_commit("/repo", "abc123"))

    @patch("subprocess.check_output")
    def test_raises_runtime_error_on_subprocess_failure(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.side_effect = subprocess.CalledProcessError(1, "git")
        with self.assertRaises(RuntimeError):
            classify_commit("/repo", "abc123")

    @patch("subprocess.check_output")
    def test_majority_type_wins(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "a.py\nb.py\nc.md\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "code")

    @patch("subprocess.check_output")
    def test_java_file_classified_as_code(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "Main.java\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "code")

    @patch("subprocess.check_output")
    def test_javascript_file_classified_as_code(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "app.js\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "code")


class TestListCommits(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_returns_list_of_commit_hashes(self, mock_out):
        from ww.git.git_classify_commit import list_commits

        mock_out.return_value = "abc123\ndef456\n"
        result = list_commits("/repo", "HEAD")
        self.assertEqual(result, ["abc123", "def456"])

    @patch("subprocess.check_output")
    def test_raises_on_git_failure(self, mock_out):
        from ww.git.git_classify_commit import list_commits

        mock_out.side_effect = subprocess.CalledProcessError(1, "git")
        with self.assertRaises(RuntimeError):
            list_commits("/repo", "HEAD")

    @patch("subprocess.check_output")
    def test_returns_empty_for_blank_output(self, mock_out):
        from ww.git.git_classify_commit import list_commits

        mock_out.return_value = ""
        result = list_commits("/repo", "HEAD")
        self.assertEqual(result, [])


class TestMain(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_main_prints_summary(self, mock_out):
        from ww.git.git_classify_commit import main

        # rev-list returns two commits; diff-tree returns files for each
        mock_out.side_effect = [
            "abc123\ndef456\n",  # list_commits
            "a.py\n",  # classify_commit for abc123
            "README.md\n",  # classify_commit for def456
        ]
        with patch.object(sys, "argv", ["git_classify_commit", "/repo"]):
            with patch("builtins.print") as mock_print:
                main()
                output = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("code", output)
                self.assertIn("md", output)

    @patch(
        "subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")
    )
    def test_main_handles_git_failure(self, mock_out):
        from ww.git.git_classify_commit import main

        with patch.object(sys, "argv", ["git_classify_commit", "/repo"]):
            with patch("builtins.print"):
                main()  # should not raise


if __name__ == "__main__":
    unittest.main()
