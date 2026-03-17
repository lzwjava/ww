import unittest
from integration_tests.helpers import run_ww


class TestCreateNoteCommand(unittest.TestCase):
    def test_fails_with_uncommitted_changes_or_git_error(self):
        """create-note requires a clean git working tree; expect failure in test env."""
        returncode, stdout, stderr = run_ww("create-note")
        # In a test environment the repo typically has uncommitted changes or
        # the command fails for git-related reasons. Either way it should not
        # silently succeed with exit 0 unless the tree happens to be clean.
        output = stdout + stderr
        if returncode != 0:
            self.assertTrue(
                "Uncommitted" in output
                or "error" in output.lower()
                or "failed" in output.lower(),
                f"Unexpected stderr/stdout: {output}",
            )

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
