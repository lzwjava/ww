import unittest
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestCheckGitStatus(unittest.TestCase):
    @patch("subprocess.run")
    def test_raises_when_unstaged_changes(self, mock_run):
        from ww.git.git_force_push import check_git_status

        mock_run.return_value = MagicMock(stdout="M modified_file.py\n")
        with self.assertRaises(Exception) as ctx:
            check_git_status()
        self.assertIn("unstaged changes", str(ctx.exception))

    @patch("subprocess.run")
    def test_does_not_raise_when_clean(self, mock_run):
        from ww.git.git_force_push import check_git_status

        mock_run.return_value = MagicMock(stdout="")
        check_git_status()  # should not raise


class TestGetCurrentBranch(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_branch_name(self, mock_run):
        from ww.git.git_force_push import get_current_branch

        mock_run.return_value = MagicMock(stdout="my-feature-branch\n")
        result = get_current_branch()
        self.assertEqual(result, "my-feature-branch")

    @patch("subprocess.run")
    def test_returns_main(self, mock_run):
        from ww.git.git_force_push import get_current_branch

        mock_run.return_value = MagicMock(stdout="main\n")
        result = get_current_branch()
        self.assertEqual(result, "main")


class TestMain(unittest.TestCase):
    @patch("subprocess.run")
    def test_calls_force_push_with_current_branch(self, mock_run):
        from ww.git.git_force_push import main

        clean = MagicMock(stdout="")
        branch = MagicMock(stdout="feature-branch\n")
        push = MagicMock()
        mock_run.side_effect = [clean, branch, push]

        main()

        last_call = mock_run.call_args_list[-1]
        cmd = last_call[0][0]
        self.assertIn("--force-with-lease", cmd)
        self.assertIn("feature-branch", cmd)

    @patch("subprocess.run")
    def test_raises_when_dirty_working_tree(self, mock_run):
        from ww.git.git_force_push import main

        mock_run.return_value = MagicMock(stdout="M dirty.py\n")
        with self.assertRaises(SystemExit):
            main()


if __name__ == "__main__":
    unittest.main()
