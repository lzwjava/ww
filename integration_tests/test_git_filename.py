import unittest
from integration_tests.helpers import run_ww


class TestGitFilenameCommand(unittest.TestCase):
    def test_command_runs_without_error(self):
        returncode, stdout, stderr = run_ww("git", "check-filenames")
        output = stdout + stderr
        self.assertTrue(len(output) > 0, "Expected some output")
        self.assertNotIn("Traceback", output)
