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


if __name__ == "__main__":
    unittest.main()
