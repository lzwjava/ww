import os
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestMain(unittest.TestCase):
    @patch("ww.proc.kill_by_port.input", return_value="")
    @patch("ww.proc.kill_by_port.print_process_details")
    @patch("ww.proc.kill_by_port.platform_module")
    def test_kills_process_on_default_port(
        self, mock_platform, mock_print_details, mock_input
    ):
        from ww.proc.kill_by_port import main

        mock_platform.find_process_on_port.return_value = ("1234", "node (1234)")
        mock_platform.get_process_details.return_value = {"name": "node", "pid": "1234"}
        mock_platform.kill_process.return_value = True

        with patch("sys.argv", ["kill_by_port"]):
            main()

        mock_platform.find_process_on_port.assert_called_once_with(8080)
        mock_platform.kill_process.assert_called_once_with("1234")

    @patch("ww.proc.kill_by_port.input", return_value="")
    @patch("ww.proc.kill_by_port.print_process_details")
    @patch("ww.proc.kill_by_port.platform_module")
    def test_kills_process_on_custom_port(
        self, mock_platform, mock_print_details, mock_input
    ):
        from ww.proc.kill_by_port import main

        mock_platform.find_process_on_port.return_value = ("5678", "python (5678)")
        mock_platform.get_process_details.return_value = None
        mock_platform.kill_process.return_value = True

        with patch("sys.argv", ["kill_by_port", "--port", "3000"]):
            main()

        mock_platform.find_process_on_port.assert_called_once_with(3000)

    @patch("ww.proc.kill_by_port.print_process_details")
    @patch("ww.proc.kill_by_port.platform_module")
    def test_no_process_found(self, mock_platform, mock_print_details):
        from ww.proc.kill_by_port import main

        mock_platform.find_process_on_port.return_value = (None, None)

        with patch("sys.argv", ["kill_by_port"]):
            main()

        mock_platform.kill_process.assert_not_called()
        mock_print_details.assert_not_called()

    @patch("ww.proc.kill_by_port.input", return_value="no")
    @patch("ww.proc.kill_by_port.print_process_details")
    @patch("ww.proc.kill_by_port.platform_module")
    def test_user_declines_kill(self, mock_platform, mock_print_details, mock_input):
        from ww.proc.kill_by_port import main

        mock_platform.find_process_on_port.return_value = ("1234", "node (1234)")
        mock_platform.get_process_details.return_value = {"name": "node"}

        with patch("sys.argv", ["kill_by_port"]):
            main()

        mock_platform.kill_process.assert_not_called()

    @patch("ww.proc.kill_by_port.input", return_value="n")
    @patch("ww.proc.kill_by_port.print_process_details")
    @patch("ww.proc.kill_by_port.platform_module")
    def test_user_declines_with_n(self, mock_platform, mock_print_details, mock_input):
        from ww.proc.kill_by_port import main

        mock_platform.find_process_on_port.return_value = ("1234", "node (1234)")
        mock_platform.get_process_details.return_value = {"name": "node"}

        with patch("sys.argv", ["kill_by_port"]):
            main()

        mock_platform.kill_process.assert_not_called()

    @patch("ww.proc.kill_by_port.input", side_effect=KeyboardInterrupt)
    @patch("ww.proc.kill_by_port.print_process_details")
    @patch("ww.proc.kill_by_port.platform_module")
    def test_keyboard_interrupt_cancels(
        self, mock_platform, mock_print_details, mock_input
    ):
        from ww.proc.kill_by_port import main

        mock_platform.find_process_on_port.return_value = ("1234", "node (1234)")
        mock_platform.get_process_details.return_value = {"name": "node"}

        with patch("sys.argv", ["kill_by_port"]):
            main()

        mock_platform.kill_process.assert_not_called()

    @patch("ww.proc.kill_by_port.input", return_value="")
    @patch("ww.proc.kill_by_port.print_process_details")
    @patch("ww.proc.kill_by_port.platform_module")
    def test_kill_failure_message(self, mock_platform, mock_print_details, mock_input):
        from ww.proc.kill_by_port import main

        mock_platform.find_process_on_port.return_value = ("1234", "node (1234)")
        mock_platform.get_process_details.return_value = {"name": "node"}
        mock_platform.kill_process.return_value = False

        with patch("sys.argv", ["kill_by_port"]):
            main()

        mock_platform.kill_process.assert_called_once_with("1234")


if __name__ == "__main__":
    unittest.main()
