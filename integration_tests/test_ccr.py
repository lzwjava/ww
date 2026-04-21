import unittest
from integration_tests.helpers import run_ww


class TestCcrCommand(unittest.TestCase):
    def test_command_runs(self):
        returncode, stdout, stderr = run_ww("utils", "ccr")
        output = stdout + stderr
        self.assertTrue(len(output) > 0, "Expected some output")

    def test_prints_command_string(self):
        returncode, stdout, stderr = run_ww("utils", "ccr")
        self.assertIn("ccr", stdout.lower())
