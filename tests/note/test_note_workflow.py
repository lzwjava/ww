import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGitToplevel(unittest.TestCase):
    @patch("subprocess.check_output", return_value="/repo/root\n")
    @patch("ww.note.note_workflow.get_base_path", return_value=".")
    def test_returns_stripped_path(self, mock_base, mock_cmd):
        from ww.note.note_workflow import _git_toplevel

        result = _git_toplevel()
        self.assertEqual(result, "/repo/root")

    @patch("subprocess.check_output", return_value="/repo/root\n")
    @patch("ww.note.note_workflow.get_base_path", return_value="/my/base")
    def test_uses_c_flag_when_base_not_dot(self, mock_base, mock_cmd):
        from ww.note.note_workflow import _git_toplevel

        _git_toplevel()
        cmd = mock_cmd.call_args[0][0]
        self.assertIn("-C", cmd)
        self.assertIn("/my/base", cmd)


class TestCheckUncommittedChanges(unittest.TestCase):
    @patch("subprocess.run")
    @patch("ww.note.note_workflow._git_toplevel", return_value="/repo")
    def test_raises_on_dirty_repo(self, mock_toplevel, mock_run):
        from ww.note.note_workflow import check_uncommitted_changes

        mock_run.return_value = MagicMock(stdout=" M somefile.py\n")
        with self.assertRaises(RuntimeError):
            check_uncommitted_changes()

    @patch("subprocess.run")
    @patch("ww.note.note_workflow._git_toplevel", return_value="/repo")
    def test_passes_on_clean_repo(self, mock_toplevel, mock_run):
        from ww.note.note_workflow import check_uncommitted_changes

        mock_run.return_value = MagicMock(stdout="")
        check_uncommitted_changes()  # Should not raise


class TestGitPullRebase(unittest.TestCase):
    @patch("subprocess.run")
    @patch("ww.note.note_workflow._git_toplevel", return_value="/repo")
    def test_calls_git_pull_rebase(self, mock_toplevel, mock_run):
        from ww.note.note_workflow import git_pull_rebase

        mock_run.return_value = MagicMock()
        git_pull_rebase()
        cmd = mock_run.call_args[0][0]
        self.assertIn("pull", cmd)
        self.assertIn("--rebase", cmd)

    @patch("subprocess.run", side_effect=Exception("fail"))
    @patch("ww.note.note_workflow._git_toplevel", return_value="/repo")
    def test_raises_on_failure(self, mock_toplevel, mock_run):
        from ww.note.note_workflow import git_pull_rebase

        with self.assertRaises(Exception):
            git_pull_rebase()


class TestOpenNoteInBrowser(unittest.TestCase):
    def test_returns_when_no_path(self):
        from ww.note.note_workflow import open_note_in_browser

        open_note_in_browser(None, "https://github.com/user/repo")  # Should not raise

    @patch("ww.note.note_workflow._open_url")
    @patch("ww.note.note_workflow._git_toplevel", return_value="/repo")
    def test_opens_url(self, mock_toplevel, mock_open):
        from ww.note.note_workflow import open_note_in_browser

        open_note_in_browser("/repo/notes/test.md", "https://github.com/user/repo")
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        self.assertIn("github.com", url)
        self.assertIn("notes/test.md", url)


class TestOpenUrl(unittest.TestCase):
    @patch("subprocess.run")
    def test_darwin_uses_open(self, mock_run):
        from ww.note.note_workflow import _open_url

        with patch("sys.platform", "darwin"):
            with patch.dict(os.environ, {"NOTE_BROWSER": ""}):
                _open_url("https://example.com")
        cmd = mock_run.call_args[0][0]
        self.assertIn("open", cmd)

    @patch("subprocess.run")
    def test_linux_uses_xdg_open(self, mock_run):
        from ww.note.note_workflow import _open_url

        with patch("sys.platform", "linux"):
            _open_url("https://example.com")
        cmd = mock_run.call_args[0][0]
        self.assertIn("xdg-open", cmd)

    @patch("subprocess.run")
    def test_darwin_with_browser_env(self, mock_run):
        from ww.note.note_workflow import _open_url

        with patch("sys.platform", "darwin"):
            with patch.dict(os.environ, {"NOTE_BROWSER": "Firefox"}):
                _open_url("https://example.com")
        cmd = mock_run.call_args[0][0][2]  # osascript -e script
        self.assertIn("Firefox", cmd)


class TestGenerateRandomDate(unittest.TestCase):
    def test_returns_valid_date_format(self):
        from ww.note.note_workflow import generate_random_date

        result = generate_random_date()
        datetime.strptime(result, "%Y-%m-%d")  # Should not raise

    def test_date_within_180_days(self):
        from ww.note.note_workflow import generate_random_date

        result = generate_random_date()
        date = datetime.strptime(result, "%Y-%m-%d")
        now = datetime.now()
        self.assertGreaterEqual(date, now - timedelta(days=180))
        self.assertLessEqual(date, now)


class TestParseArgs(unittest.TestCase):
    def test_default_args(self):
        from ww.note.note_workflow import parse_args

        with patch.object(sys, "argv", ["prog"]):
            args = parse_args()
        self.assertFalse(args.random)
        self.assertFalse(args.without_math)
        self.assertFalse(args.gemini)

    def test_random_flag(self):
        from ww.note.note_workflow import parse_args

        with patch.object(sys, "argv", ["prog", "--random"]):
            args = parse_args()
        self.assertTrue(args.random)

    def test_without_math_flag(self):
        from ww.note.note_workflow import parse_args

        with patch.object(sys, "argv", ["prog", "--without-math"]):
            args = parse_args()
        self.assertTrue(args.without_math)

    def test_repo_url_default(self):
        from ww.note.note_workflow import parse_args

        with patch.object(sys, "argv", ["prog"]):
            args = parse_args()
        self.assertIn("github.com", args.repo_url)


if __name__ == "__main__":
    unittest.main()
