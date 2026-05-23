import sys
import unittest
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGetCommitsWithDeletions(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_list_of_hashes(self, mock_run):
        from ww.git.git_delete_commit import get_commits_with_deletions

        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\ndef456\n")
        result = get_commits_with_deletions(5)
        self.assertEqual(result, ["abc123", "def456"])

    @patch("subprocess.run")
    def test_returns_empty_list_on_git_error(self, mock_run):
        from ww.git.git_delete_commit import get_commits_with_deletions

        mock_run.return_value = MagicMock(returncode=1, stderr="error", stdout="")
        result = get_commits_with_deletions(5)
        self.assertEqual(result, [])

    @patch("subprocess.run")
    def test_filters_empty_lines(self, mock_run):
        from ww.git.git_delete_commit import get_commits_with_deletions

        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n\ndef456\n")
        result = get_commits_with_deletions(5)
        self.assertEqual(result, ["abc123", "def456"])

    @patch("subprocess.run", side_effect=OSError("git not found"))
    def test_returns_empty_on_exception(self, mock_run):
        from ww.git.git_delete_commit import get_commits_with_deletions

        result = get_commits_with_deletions(5)
        self.assertEqual(result, [])


class TestGetChangedFilesCount(unittest.TestCase):
    @patch("subprocess.run")
    def test_parses_multiple_files_changed(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="commit abc123\n\n 3 files changed, 10 insertions(+)\n",
        )
        self.assertEqual(get_changed_files_count("abc123"), 3)

    @patch("subprocess.run")
    def test_parses_single_file_changed(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=" 1 files changed, 5 insertions(+)\n",
        )
        self.assertEqual(get_changed_files_count("abc123"), 1)

    @patch("subprocess.run")
    def test_returns_zero_on_nonzero_returncode(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertEqual(get_changed_files_count("abc123"), 0)

    @patch("subprocess.run")
    def test_returns_zero_when_no_match_in_output(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        mock_run.return_value = MagicMock(returncode=0, stdout="commit abc123\n\n")
        self.assertEqual(get_changed_files_count("abc123"), 0)

    @patch("subprocess.run", side_effect=OSError("fail"))
    def test_returns_zero_on_exception(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        self.assertEqual(get_changed_files_count("abc123"), 0)


if __name__ == "__main__":
    unittest.main()


class TestMain(unittest.TestCase):
    def test_exits_when_wrong_arg_count(self):
        from ww.git.git_delete_commit import main

        with patch.object(sys, "argv", ["prog"]):
            with self.assertRaises(SystemExit):
                main()

    def test_exits_when_args_not_int(self):
        from ww.git.git_delete_commit import main

        with patch.object(sys, "argv", ["prog", "abc", "xyz"]):
            with self.assertRaises(SystemExit):
                main()

    def test_exits_when_n_negative(self):
        from ww.git.git_delete_commit import main

        with patch.object(sys, "argv", ["prog", "-1", "0"]):
            with self.assertRaises(SystemExit):
                main()

    @patch("ww.git.git_delete_commit.get_commits_with_deletions", return_value=[])
    def test_prints_none_when_no_commits(self, mock_commits):
        from ww.git.git_delete_commit import main

        with patch.object(sys, "argv", ["prog", "5", "2"]):
            with patch("builtins.print") as mock_print:
                main()
                mock_print.assert_called_with("none")

    @patch("ww.git.git_delete_commit.get_changed_files_count", return_value=5)
    @patch(
        "ww.git.git_delete_commit.get_commits_with_deletions", return_value=["abc123"]
    )
    def test_prints_commit_when_files_exceed_threshold(self, mock_commits, mock_count):
        from ww.git.git_delete_commit import main

        with patch.object(sys, "argv", ["prog", "5", "3"]):
            with patch("builtins.print") as mock_print:
                with self.assertRaises(SystemExit) as ctx:
                    main()
                self.assertEqual(ctx.exception.code, 0)
                mock_print.assert_called_with("abc123: 5")

    @patch("ww.git.git_delete_commit.get_changed_files_count", return_value=1)
    @patch(
        "ww.git.git_delete_commit.get_commits_with_deletions", return_value=["abc123"]
    )
    def test_prints_none_when_files_below_threshold(self, mock_commits, mock_count):
        from ww.git.git_delete_commit import main

        with patch.object(sys, "argv", ["prog", "5", "3"]):
            with patch("builtins.print") as mock_print:
                main()
                mock_print.assert_called_with("none")


if __name__ == "__main__":
    unittest.main()
