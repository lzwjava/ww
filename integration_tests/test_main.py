import unittest
from integration_tests.helpers import run_ww


class TestWWNoArgs(unittest.TestCase):
    def test_no_args_prints_hello_world(self):
        returncode, stdout, stderr = run_ww()
        self.assertEqual(returncode, 0)
        self.assertIn("hello world", stdout)


class TestWWUnknownCommand(unittest.TestCase):
    def test_unknown_command_exits_nonzero(self):
        returncode, stdout, stderr = run_ww("nonexistent-command-xyz")
        self.assertNotEqual(returncode, 0)

    def test_unknown_command_prints_error(self):
        returncode, stdout, stderr = run_ww("nonexistent-command-xyz")
        output = stdout + stderr
        self.assertIn("Unknown command", output)


if __name__ == "__main__":
    unittest.main()
