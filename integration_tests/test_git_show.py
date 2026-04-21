import unittest
from integration_tests.helpers import run_ww


class TestGitShowCommand(unittest.TestCase):
    def test_command_runs_without_error(self):
        returncode, stdout, stderr = run_ww("git", "show")
        output = stdout + stderr
        self.assertTrue(len(output) > 0, "Expected some output")
        self.assertNotIn("Traceback", output)

    def test_prints_commit_info(self):
        returncode, stdout, stderr = run_ww("git", "show")
        output = stdout + stderr
        self.assertIn("commit", output.lower())
