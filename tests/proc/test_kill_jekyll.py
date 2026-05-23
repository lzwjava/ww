import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGetJekyllProcesses(unittest.TestCase):
    @patch("ww.proc.kill_jekyll.subprocess.run")
    def test_returns_pids_from_ruby_lines(self, mock_run):
        from ww.proc.kill_jekyll import get_jekyll_processes

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME\n"
            "ruby     1234  user    5u  IPv4  0x123      0t0  TCP *:4000\n"
            "ruby     5678  user    5u  IPv4  0x456      0t0  TCP *:4000\n"
        )
        mock_run.return_value = mock_result

        pids = get_jekyll_processes()

        self.assertEqual(pids, {1234, 5678})
        mock_run.assert_called_once_with(
            ["lsof", "-i", ":4000"], capture_output=True, text=True, check=False
        )

    @patch("ww.proc.kill_jekyll.subprocess.run")
    def test_returns_empty_set_when_no_output(self, mock_run):
        from ww.proc.kill_jekyll import get_jekyll_processes

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        pids = get_jekyll_processes()
        self.assertEqual(pids, set())

    @patch("ww.proc.kill_jekyll.subprocess.run")
    def test_returns_empty_set_when_no_ruby_lines(self, mock_run):
        from ww.proc.kill_jekyll import get_jekyll_processes

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "COMMAND   PID   USER\nnode     9999  user\n"
        mock_run.return_value = mock_result

        pids = get_jekyll_processes()
        self.assertEqual(pids, set())

    @patch("ww.proc.kill_jekyll.subprocess.run")
    def test_returns_empty_set_on_error_exit_code(self, mock_run):
        from ww.proc.kill_jekyll import get_jekyll_processes

        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        pids = get_jekyll_processes()
        self.assertEqual(pids, set())

    @patch("ww.proc.kill_jekyll.subprocess.run")
    def test_returns_empty_set_on_file_not_found(self, mock_run):
        from ww.proc.kill_jekyll import get_jekyll_processes

        mock_run.side_effect = FileNotFoundError

        pids = get_jekyll_processes()
        self.assertEqual(pids, set())


class TestKillProcesses(unittest.TestCase):
    @patch("ww.proc.kill_jekyll.time.sleep")
    @patch("ww.proc.kill_jekyll.get_jekyll_processes")
    @patch("ww.proc.kill_jekyll.subprocess.run")
    def test_kills_and_returns_true_when_all_gone(self, mock_run, mock_get, mock_sleep):
        from ww.proc.kill_jekyll import kill_processes

        mock_get.return_value = set()
        mock_run.return_value = MagicMock()

        result = kill_processes({1234, 5678})

        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)
        mock_sleep.assert_called_once_with(0.5)

    @patch("ww.proc.kill_jekyll.time.sleep")
    @patch("ww.proc.kill_jekyll.get_jekyll_processes")
    @patch("ww.proc.kill_jekyll.subprocess.run")
    def test_returns_false_when_processes_remain(self, mock_run, mock_get, mock_sleep):
        from ww.proc.kill_jekyll import kill_processes

        mock_get.return_value = {1234}
        mock_run.return_value = MagicMock()

        result = kill_processes({1234})

        self.assertFalse(result)

    def test_returns_false_when_empty_pids(self):
        from ww.proc.kill_jekyll import kill_processes

        result = kill_processes(set())
        self.assertFalse(result)

    @patch("ww.proc.kill_jekyll.time.sleep")
    @patch("ww.proc.kill_jekyll.get_jekyll_processes")
    @patch("ww.proc.kill_jekyll.subprocess.run")
    def test_handles_kill_error(self, mock_run, mock_get, mock_sleep):
        from ww.proc.kill_jekyll import kill_processes

        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "kill")
        mock_get.return_value = set()

        result = kill_processes({1234})
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
