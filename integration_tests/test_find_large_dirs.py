import os
import tempfile
import unittest
from integration_tests.helpers import run_ww, WW_PROJECT


class TestFindLargeDirsCommand(unittest.TestCase):
    def test_find_large_dirs_in_tmp(self):
        returncode, stdout, stderr = run_ww(
            "find-large-dirs", "--mb", "0", tempfile.gettempdir()
        )
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Finding directories", stdout)

    def test_find_large_dirs_default_path(self):
        returncode, stdout, stderr = run_ww(
            "find-large-dirs", "--mb", "999999", WW_PROJECT
        )
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Finding directories", stdout)

    def test_find_large_dirs_nonexistent_path(self):
        returncode, stdout, stderr = run_ww("find-large-dirs", "/nonexistent/path/xyz")
        self.assertNotEqual(returncode, 0)
        output = stdout + stderr
        self.assertIn("Error", output)

    def test_find_large_dirs_not_a_directory(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"content")
            tmpfile = f.name
        try:
            returncode, stdout, stderr = run_ww("find-large-dirs", tmpfile)
            self.assertNotEqual(returncode, 0)
            output = stdout + stderr
            self.assertIn("Error", output)
        finally:
            os.unlink(tmpfile)


if __name__ == "__main__":
    unittest.main()
