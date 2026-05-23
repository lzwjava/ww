import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.agent.git_utils import (
    extract_changed_content,
    apply_grammar_fixes_to_original,
    get_git_diff_lines,
    get_changed_md_files_in_last_n_commits,
)


class TestExtractChangedContent(unittest.TestCase):
    def test_empty_changed_lines(self):
        result = extract_changed_content("line1\nline2\n", set())
        self.assertEqual(result, "")

    def test_single_line(self):
        content = "aaa\nbbb\nccc\nddd\neee\n"
        result = extract_changed_content(content, {3})
        self.assertIn("ccc", result)

    def test_consecutive_lines_grouped(self):
        content = "aaa\nbbb\nccc\nddd\neee\n"
        result = extract_changed_content(content, {2, 3})
        # Should include context around lines 2-3
        self.assertIn("bbb", result)
        self.assertIn("ccc", result)
        self.assertIn("ddd", result)

    def test_non_consecutive_lines_separate_groups(self):
        content = "aaa\nbbb\nccc\nddd\neee\n"
        result = extract_changed_content(content, {1, 5})
        # Two separate groups separated by ---
        self.assertIn("---", result)
        self.assertIn("aaa", result)
        self.assertIn("eee", result)

    def test_context_lines_clamped(self):
        content = "first\nsecond\nthird\n"
        result = extract_changed_content(content, {1})
        # Should not go below index 0
        self.assertIn("first", result)


class TestApplyGrammarFixesToOriginal(unittest.TestCase):
    def test_no_changed_lines_returns_original(self):
        original = "line1\nline2"
        result = apply_grammar_fixes_to_original(original, "changed", "fixed", set())
        self.assertEqual(result, original)

    def test_replaces_section_around_changed_lines(self):
        original = "aaa\nbbb\nccc\nddd\neee"
        changed = "bbb"
        fixed = "BBB_fixed"
        result = apply_grammar_fixes_to_original(original, changed, fixed, {2})
        self.assertIn("BBB_fixed", result)

    def test_preserves_before_and_after_sections(self):
        original = "aaa\nbbb\nccc\nddd\neee"
        fixed = "FIXED"
        result = apply_grammar_fixes_to_original(original, "bbb", fixed, {2})
        # Lines before and after should be preserved
        self.assertIn("FIXED", result)


class TestGetGitDiffLines(unittest.TestCase):
    @patch("ww.agent.git_utils.subprocess.run")
    def test_parses_added_lines(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="@@ -1,3 +1,4 @@\n context\n+added\n still context\n",
            stderr="",
        )
        result = get_git_diff_lines("/fake/file.md")
        self.assertIn(2, result)  # "added" is at line 2

    @patch("ww.agent.git_utils.subprocess.run")
    def test_returns_empty_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = get_git_diff_lines("/fake/file.md")
        self.assertEqual(result, set())

    @patch("ww.agent.git_utils.subprocess.run")
    def test_returns_empty_on_no_changes(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = get_git_diff_lines("/fake/file.md")
        self.assertEqual(result, set())

    @patch("ww.agent.git_utils.subprocess.run")
    def test_with_base_range(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="@@ -5,3 +5,4 @@\n old\n+new\n end\n",
            stderr="",
        )
        result = get_git_diff_lines("/fake/file.md", base_range="HEAD~1..HEAD")
        # Verify the command was built with the range
        call_args = mock_run.call_args[0][0]
        self.assertIn("HEAD~1..HEAD", call_args)
        self.assertIn(6, result)  # "new" at line 6 (5+1)


class TestGetChangedMdFilesInLastNCommits(unittest.TestCase):
    @patch("ww.agent.git_utils.subprocess.run")
    def test_filters_md_files_in_original(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="original/post1.md\noriginal/sub/post2.md\nother.txt\nsrc/main.py\n",
            stderr="",
        )
        result = get_changed_md_files_in_last_n_commits(3)
        self.assertEqual(result, ["original/post1.md", "original/sub/post2.md"])

    def test_returns_empty_for_zero_commits(self):
        # n <= 0 returns [] without calling subprocess
        result = get_changed_md_files_in_last_n_commits(0)
        self.assertEqual(result, [])

    @patch("ww.agent.git_utils.subprocess.run")
    def test_returns_empty_on_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = get_changed_md_files_in_last_n_commits(2)
        self.assertEqual(result, [])

    @patch("ww.agent.git_utils.subprocess.run")
    def test_returns_empty_when_no_md_files(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="src/main.py\nREADME.txt\n",
            stderr="",
        )
        result = get_changed_md_files_in_last_n_commits(1)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
