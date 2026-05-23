import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestRunCommand(unittest.TestCase):
    @patch("ww.macos.open_terminal.subprocess.run")
    def test_returns_result(self, mock_run):
        from ww.macos.open_terminal import run_command

        mock_result = MagicMock(returncode=0)
        mock_run.return_value = mock_result
        result = run_command("echo hi")
        self.assertEqual(result, mock_result)

    @patch("ww.macos.open_terminal.subprocess.run", side_effect=Exception("err"))
    def test_returns_none_on_error(self, mock_run):
        from ww.macos.open_terminal import run_command

        result = run_command("bad")
        self.assertIsNone(result)


class TestOpenGhosttyAtPath(unittest.TestCase):
    def test_empty_path_returns_false(self):
        from ww.macos.open_terminal import open_ghostty_at_path

        self.assertFalse(open_ghostty_at_path("", 1))

    def test_zero_number_returns_false(self):
        from ww.macos.open_terminal import open_ghostty_at_path

        self.assertFalse(open_ghostty_at_path("/tmp", 0))

    def test_negative_number_returns_false(self):
        from ww.macos.open_terminal import open_ghostty_at_path

        self.assertFalse(open_ghostty_at_path("/tmp", -1))

    @patch("os.path.exists", return_value=False)
    def test_nonexistent_path_returns_false(self, mock_exists):
        from ww.macos.open_terminal import open_ghostty_at_path

        self.assertFalse(open_ghostty_at_path("/nonexistent", 1))

    @patch("ww.macos.open_terminal.run_command")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.expanduser", side_effect=lambda x: x)
    def test_opens_multiple_terminals(self, mock_expand, mock_exists, mock_rc):
        from ww.macos.open_terminal import open_ghostty_at_path

        mock_rc.return_value = MagicMock(returncode=0)
        result = open_ghostty_at_path("/tmp", 3)
        self.assertTrue(result)
        self.assertEqual(mock_rc.call_count, 3)

    @patch("ww.macos.open_terminal.run_command")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.expanduser", side_effect=lambda x: x)
    def test_partial_failure_returns_false(self, mock_expand, mock_exists, mock_rc):
        from ww.macos.open_terminal import open_ghostty_at_path

        mock_rc.return_value = MagicMock(returncode=1, stderr="error")
        result = open_ghostty_at_path("/tmp", 2)
        self.assertFalse(result)

    @patch("ww.macos.open_terminal.run_command")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.expanduser", side_effect=lambda x: x)
    def test_expands_home_path(self, mock_expand, mock_exists, mock_rc):
        from ww.macos.open_terminal import open_ghostty_at_path

        mock_rc.return_value = MagicMock(returncode=0)
        open_ghostty_at_path("~/projects", 1)
        mock_expand.assert_called_with("~/projects")


class TestMain(unittest.TestCase):
    @patch("ww.macos.open_terminal.open_ghostty_at_path", return_value=True)
    @patch("sys.argv", ["open_terminal", "--path", "/tmp", "--number", "1"])
    def test_main_success(self, mock_open):
        from ww.macos.open_terminal import main

        with self.assertRaises(SystemExit) as ctx:
            main()
        self.assertEqual(ctx.exception.code, 0)
        mock_open.assert_called_once_with("/tmp", 1)

    @patch("ww.macos.open_terminal.open_ghostty_at_path", return_value=False)
    @patch("sys.argv", ["open_terminal", "--path", "/tmp", "--number", "1"])
    def test_main_failure_exits_1(self, mock_open):
        from ww.macos.open_terminal import main

        with self.assertRaises(SystemExit) as ctx:
            main()
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
