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


if __name__ == "__main__":
    unittest.main()
