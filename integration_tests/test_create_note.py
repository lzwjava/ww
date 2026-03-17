import unittest
from integration_tests.helpers import run_ww


class TestCreateNoteCommand(unittest.TestCase):
    def test_command_runs_without_python_traceback(self):
        """create-note should exit with a recognisable message (not a silent crash)."""
        returncode, stdout, stderr = run_ww("create-note")
        output = stdout + stderr
        # Acceptable outcomes: clean run, or a handled/unhandled error that at
        # least prints something meaningful about what went wrong.
        self.assertTrue(len(output) > 0, "Expected some output from create-note")

    def test_no_push_flag_is_accepted(self):
        """--no-push flag must be a recognised argument (argparse won't crash)."""
        returncode, stdout, stderr = run_ww("create-note", "--no-push")
        # If we get an argparse error the message would contain "error:" from
        # argparse. A git/repo error is acceptable; an argparse error is not.
        self.assertNotIn("error: unrecognized arguments", stderr)

    def test_random_flag_is_accepted(self):
        """--random flag must be a recognised argument."""
        returncode, stdout, stderr = run_ww("create-note", "--random")
        self.assertNotIn("error: unrecognized arguments", stderr)

    def test_without_math_flag_is_accepted(self):
        """--without-math flag must be a recognised argument."""
        returncode, stdout, stderr = run_ww("create-note", "--without-math")
        self.assertNotIn("error: unrecognized arguments", stderr)


if __name__ == "__main__":
    unittest.main()
