import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestRunCommand(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_subprocess_result(self, mock_run):
        from ww.git.git_amend_push import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        result = run_command(["git", "status"])
        self.assertIsNotNone(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_uses_provided_repo_path_as_cwd(self, mock_run):
        from ww.git.git_amend_push import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_command(["git", "status"], repo_path=Path("/tmp"))
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["cwd"], "/tmp")

    @patch("subprocess.run")
    def test_passes_check_flag(self, mock_run):
        from ww.git.git_amend_push import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_command(["git", "status"], check=False)
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["check"], False)


class TestStageAmendPush(unittest.TestCase):
    @patch("subprocess.run")
    def test_stage_changes_calls_git_add(self, mock_run):
        from ww.git.git_amend_push import stage_changes

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        stage_changes(Path("/tmp"))
        cmd = mock_run.call_args[0][0]
        self.assertIn("add", cmd)
        self.assertIn("-A", cmd)

    @patch("subprocess.run")
    def test_amend_commit_calls_git_amend(self, mock_run):
        from ww.git.git_amend_push import amend_commit

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        amend_commit(Path("/tmp"))
        cmd = mock_run.call_args[0][0]
        self.assertIn("--amend", cmd)
        self.assertIn("--no-edit", cmd)

    @patch("subprocess.run")
    def test_push_changes_calls_force_with_lease(self, mock_run):
        from ww.git.git_amend_push import push_changes

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        push_changes(Path("/tmp"))
        cmd = mock_run.call_args[0][0]
        self.assertIn("--force-with-lease", cmd)


class TestMainAmendPush(unittest.TestCase):
    @patch("subprocess.run")
    def test_main_runs_all_three_steps(self, mock_run):
        from ww.git.git_amend_push import main
        import tempfile

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(sys, "argv", ["git_amend_push", tmpdir]):
                main()
        self.assertEqual(mock_run.call_count, 3)

    def test_main_exits_when_path_not_a_dir(self):
        from ww.git.git_amend_push import main

        with patch.object(sys, "argv", ["git_amend_push", "/nonexistent/path/xyz"]):
            with self.assertRaises(SystemExit):
                main()

    @patch("subprocess.run")
    def test_main_uses_cwd_when_no_args(self, mock_run):
        from ww.git.git_amend_push import main

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(sys, "argv", ["git_amend_push"]):
            main()
        self.assertEqual(mock_run.call_count, 3)


if __name__ == "__main__":
    unittest.main()
