import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestFindProcessOnPort(unittest.TestCase):
    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_pid_and_info_when_found(self, mock_run):
        from ww.proc.kill_unix import find_process_on_port

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME\n"
            "node    12345  user   12u  IPv4 0x123      0t0  TCP *:8080\n"
        )
        mock_run.return_value = mock_result

        pid, info = find_process_on_port(8080)

        self.assertEqual(pid, "12345")
        self.assertIn("node", info)
        self.assertIn("12345", info)
        mock_run.assert_called_once_with(
            ["lsof", "-i", ":8080"], capture_output=True, text=True, check=False
        )

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_none_when_no_process(self, mock_run):
        from ww.proc.kill_unix import find_process_on_port

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        pid, info = find_process_on_port(9999)

        self.assertIsNone(pid)
        self.assertIsNone(info)

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_none_on_file_not_found(self, mock_run):
        from ww.proc.kill_unix import find_process_on_port

        mock_run.side_effect = FileNotFoundError

        pid, info = find_process_on_port(8080)
        self.assertIsNone(pid)
        self.assertIsNone(info)


class TestFindProcessesByPattern(unittest.TestCase):
    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_matching_processes(self, mock_run):
        from ww.proc.kill_unix import find_processes_by_pattern

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n"
            "user      1000   0.1  0.1  12345  6789 ?        S    10:00   0:01 /usr/bin/python3 server.py\n"
            "user      2000   0.0  0.0   5678  1234 ?        S    10:01   0:00 /usr/bin/node app.js\n"
        )
        mock_run.return_value = mock_result

        processes = find_processes_by_pattern("python")

        self.assertEqual(len(processes), 1)
        self.assertEqual(processes[0][0], "1000")
        self.assertIn("python3", processes[0][1])

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_case_insensitive_match(self, mock_run):
        from ww.proc.kill_unix import find_processes_by_pattern

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n"
            "user      1000   0.1  0.1  12345  6789 ?        S    10:00   0:01 /usr/bin/Python3 server.py\n"
        )
        mock_run.return_value = mock_result

        processes = find_processes_by_pattern("python")
        self.assertEqual(len(processes), 1)

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_empty_on_no_match(self, mock_run):
        from ww.proc.kill_unix import find_processes_by_pattern

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "USER       PID  %CPU %MEM\nuser      1000   0.1  0.1\n"
        mock_run.return_value = mock_result

        processes = find_processes_by_pattern("nonexistent")
        self.assertEqual(processes, [])

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_empty_on_error(self, mock_run):
        from ww.proc.kill_unix import find_processes_by_pattern

        mock_run.side_effect = FileNotFoundError

        processes = find_processes_by_pattern("test")
        self.assertEqual(processes, [])


class TestGetProcessDetails(unittest.TestCase):
    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_details_dict_when_found(self, mock_run):
        from ww.proc.kill_unix import get_process_details

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "  PID  PPID                  STARTED     ELAPSED COMMAND\n"
            " 1234  5678 Sat May 23 2026     1-02:30:00 /usr/bin/node server.js\n"
        )
        mock_run.return_value = mock_result

        details = get_process_details("1234")

        self.assertIsNotNone(details)
        self.assertEqual(details["pid"], "1234")
        self.assertEqual(details["ppid"], "5678")
        self.assertEqual(details["name"], "/usr/bin/node")
        self.assertIn("server.js", details["command"])

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_none_when_not_found(self, mock_run):
        from ww.proc.kill_unix import get_process_details

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        details = get_process_details("9999")
        self.assertIsNone(details)

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_none_on_file_not_found(self, mock_run):
        from ww.proc.kill_unix import get_process_details

        mock_run.side_effect = FileNotFoundError

        details = get_process_details("1234")
        self.assertIsNone(details)


class TestKillProcess(unittest.TestCase):
    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_true_when_process_killed(self, mock_run):
        from ww.proc.kill_unix import kill_process

        # First call: ps -p PID (process exists)
        check_exists = MagicMock()
        check_exists.returncode = 0

        # kill -9 call
        kill_result = MagicMock()

        # Second call: ps -p PID (process gone)
        check_gone = MagicMock()
        check_gone.returncode = 1

        mock_run.side_effect = [check_exists, kill_result, check_gone]

        result = kill_process("1234")
        self.assertTrue(result)

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_true_when_already_dead(self, mock_run):
        from ww.proc.kill_unix import kill_process

        check = MagicMock()
        check.returncode = 1
        mock_run.return_value = check

        result = kill_process("1234")
        self.assertTrue(result)

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_false_when_kill_fails(self, mock_run):
        from ww.proc.kill_unix import kill_process

        check_exists = MagicMock()
        check_exists.returncode = 0

        kill_result = MagicMock()

        check_still_alive = MagicMock()
        check_still_alive.returncode = 0

        mock_run.side_effect = [check_exists, kill_result, check_still_alive]

        result = kill_process("1234")
        self.assertFalse(result)

    @patch("ww.proc.kill_unix.subprocess.run")
    def test_returns_false_on_exception(self, mock_run):
        from ww.proc.kill_unix import kill_process

        mock_run.side_effect = FileNotFoundError

        result = kill_process("1234")
        self.assertFalse(result)


class TestPrintProcessDetails(unittest.TestCase):
    @patch("builtins.print")
    def test_prints_name_and_details(self, mock_print):
        from ww.proc.kill_unix import print_process_details

        details = {
            "name": "java",
            "pid": "1234",
            "ppid": "5678",
            "started": "Sat May 23 10:00:00 2026",
            "elapsed": "1-02:30:00",
            "command": "java -jar server.jar",
            "app_info": "IntelliJ IDEA",
        }

        print_process_details("myserver (1234)", details)

        # Check name was printed
        mock_print.assert_any_call("  Name: myserver (1234)")
        # Check java command is printed (special case for java)
        mock_print.assert_any_call("  Command: java -jar server.jar")
        # Check app_info printed
        mock_print.assert_any_call("  Application: IntelliJ IDEA")
        # Check elapsed
        mock_print.assert_any_call("  Running for: 1-02:30:00")

    @patch("builtins.print")
    def test_prints_fallback_when_no_details(self, mock_print):
        from ww.proc.kill_unix import print_process_details

        print_process_details("process (1234)", None)

        mock_print.assert_any_call("  Name: process (1234)")
        mock_print.assert_any_call(
            "  (Unable to retrieve detailed process information)"
        )

    @patch("builtins.print")
    def test_does_not_print_command_for_non_java(self, mock_print):
        from ww.proc.kill_unix import print_process_details

        details = {
            "name": "node",
            "pid": "1234",
            "ppid": "5678",
            "started": "10:00",
            "elapsed": "02:30",
            "command": "node app.js",
            "app_info": None,
        }

        print_process_details("myapp (1234)", details)

        # Should not print Command line for non-java processes
        for call in mock_print.call_args_list:
            args = call[0]
            if args and "Command:" in str(args[0]):
                self.fail("Command should not be printed for non-java processes")


if __name__ == "__main__":
    unittest.main()
