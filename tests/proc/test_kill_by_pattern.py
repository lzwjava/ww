import unittest
from unittest.mock import patch


class TestAskConfirm(unittest.TestCase):
    @patch("builtins.input")
    def test_returns_true_on_empty_input(self, mock_input):
        mock_input.return_value = ""
        from ww.proc.kill_by_pattern import ask_confirm

        result = ask_confirm(5)
        self.assertTrue(result)

    @patch("builtins.input")
    def test_returns_true_on_yes(self, mock_input):
        mock_input.return_value = "yes"
        from ww.proc.kill_by_pattern import ask_confirm

        result = ask_confirm(5)
        self.assertTrue(result)

    @patch("builtins.input")
    def test_returns_false_on_no(self, mock_input):
        mock_input.return_value = "no"
        from ww.proc.kill_by_pattern import ask_confirm

        result = ask_confirm(5)
        self.assertFalse(result)

    @patch("builtins.input")
    def test_returns_false_on_n(self, mock_input):
        mock_input.return_value = "n"
        from ww.proc.kill_by_pattern import ask_confirm

        result = ask_confirm(5)
        self.assertFalse(result)

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_returns_false_on_keyboard_interrupt(self, mock_input):
        from ww.proc.kill_by_pattern import ask_confirm

        result = ask_confirm(5)
        self.assertFalse(result)


class TestKillAll(unittest.TestCase):
    @patch("ww.proc.kill_by_pattern.platform_module")
    def test_kills_all_processes(self, mock_platform):
        mock_platform.kill_process.return_value = True
        from ww.proc.kill_by_pattern import kill_all

        processes = [(123, {}), (456, {})]
        kill_all(processes)
        self.assertEqual(mock_platform.kill_process.call_count, 2)

    @patch("ww.proc.kill_by_pattern.platform_module")
    def test_reports_partial_failure(self, mock_platform):
        mock_platform.kill_process.side_effect = [True, False]
        from ww.proc.kill_by_pattern import kill_all

        processes = [(123, {}), (456, {})]
        with patch("builtins.print") as mock_print:
            kill_all(processes)
            self.assertTrue(mock_print.called)


if __name__ == "__main__":
    unittest.main()
