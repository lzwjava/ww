import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGenerateSquashMessage(unittest.TestCase):
    @patch("ww.git.git_squash.call_openrouter_api", return_value="feat: squash commits")
    def test_generates_message_via_api(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: add feature\npick def456 fix: fix bug\n"
        result = generate_squash_message(rebase_todo)
        self.assertEqual(result, "feat: squash commits")
        mock_api.assert_called_once()

    @patch(
        "ww.git.git_squash.call_openrouter_api",
        side_effect=Exception("API error"),
    )
    def test_falls_back_when_api_raises(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: add feature\npick def456 fix: fix bug\n"
        result = generate_squash_message(rebase_todo)
        self.assertIsNotNone(result)
        self.assertIn("+", result)

    @patch("ww.git.git_squash.call_openrouter_api", return_value="chore: empty")
    def test_empty_todo_still_calls_api(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        result = generate_squash_message("")
        self.assertEqual(result, "chore: empty")

    @patch("ww.git.git_squash.call_openrouter_api", return_value="fix: squash")
    def test_squash_lines_also_included(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: first\nsquash def456 fix: second\n"
        result = generate_squash_message(rebase_todo)
        self.assertEqual(result, "fix: squash")


class TestCheckGitStatus(unittest.TestCase):
    @patch("subprocess.run")
    def test_raises_when_uncommitted_changes(self, mock_run):
        from ww.git.git_squash import check_git_status

        mock_run.return_value = MagicMock(stdout=" M dirty.py\n")
        with self.assertRaises(Exception) as ctx:
            check_git_status()
        self.assertIn("unstaged changes", str(ctx.exception))

    @patch("subprocess.run")
    def test_passes_when_clean(self, mock_run):
        from ww.git.git_squash import check_git_status

        mock_run.return_value = MagicMock(stdout="")
        check_git_status()  # should not raise


class TestMainSquash(unittest.TestCase):
    @patch("ww.git.git_squash.call_openrouter_api", return_value="feat: squashed")
    @patch("subprocess.run")
    def test_main_prints_rebase_command(self, mock_run, mock_api):
        from ww.git.git_squash import main

        mock_run.return_value = MagicMock(stdout="")
        rebase_input = "pick abc123 feat: first\npick def456 fix: second\n"

        with patch.object(sys, "argv", ["git_squash", "2"]):
            with patch("sys.stdin", StringIO(rebase_input)):
                with patch("builtins.print") as mock_print:
                    main()
                    output = " ".join(str(c) for c in mock_print.call_args_list)
                    self.assertIn("HEAD~2", output)


if __name__ == "__main__":
    unittest.main()
