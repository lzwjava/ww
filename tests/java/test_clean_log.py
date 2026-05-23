import os
import sys
import tempfile
import unittest
import argparse
from io import StringIO
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.java.clean_log import is_valid_similarity_threshold, clean_log


class TestIsValidSimilarityThreshold(unittest.TestCase):
    def test_valid_values(self):
        self.assertEqual(is_valid_similarity_threshold("0.0"), 0.0)
        self.assertEqual(is_valid_similarity_threshold("1.0"), 1.0)
        self.assertEqual(is_valid_similarity_threshold("0.5"), 0.5)

    def test_below_range_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            is_valid_similarity_threshold("-0.1")

    def test_above_range_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            is_valid_similarity_threshold("1.1")

    def test_non_numeric_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            is_valid_similarity_threshold("abc")

    def test_integer_string(self):
        self.assertEqual(is_valid_similarity_threshold("1"), 1.0)
        self.assertEqual(is_valid_similarity_threshold("0"), 0.0)


class TestCleanLog(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir)

    def _write_log(self, lines):
        path = os.path.join(self.tmpdir, "test.log")
        with open(path, "w") as f:
            f.writelines(lines)
        return path

    def test_removes_exact_duplicates(self):
        log_lines = [
            "INFO | 2024-01-01 | thread-1 | Hello world\n",
            "INFO | 2024-01-01 | thread-1 | Hello world\n",
            "INFO | 2024-01-01 | thread-1 | Different message\n",
        ]
        input_path = self._write_log(log_lines)
        output_path = os.path.join(self.tmpdir, "out.log")

        clean_log(
            input_path=input_path,
            output_path=output_path,
            similarity_threshold=1.0,
            lines_to_compare=1,
        )

        with open(output_path) as f:
            result = f.readlines()
        # First line kept, second skipped as duplicate, third kept
        self.assertEqual(len(result), 2)

    def test_keeps_different_lines(self):
        log_lines = [
            "INFO | 2024-01-01 | thread-1 | Alpha message\n",
            "INFO | 2024-01-01 | thread-2 | Beta message\n",
        ]
        input_path = self._write_log(log_lines)
        output_path = os.path.join(self.tmpdir, "out.log")

        clean_log(
            input_path=input_path,
            output_path=output_path,
            similarity_threshold=1.0,
            lines_to_compare=1,
        )

        with open(output_path) as f:
            result = f.readlines()
        self.assertEqual(len(result), 2)

    def test_non_standard_line_passed_through(self):
        log_lines = [
            "This is not standard format\n",
            "Also non-standard\n",
        ]
        input_path = self._write_log(log_lines)
        output_path = os.path.join(self.tmpdir, "out.log")

        clean_log(
            input_path=input_path,
            output_path=output_path,
            similarity_threshold=1.0,
            lines_to_compare=1,
        )

        with open(output_path) as f:
            result = f.readlines()
        self.assertEqual(len(result), 2)

    def test_low_threshold_keeps_more_lines(self):
        log_lines = [
            "INFO | 2024-01-01 | thread-1 | Hello world\n",
            "INFO | 2024-01-01 | thread-1 | Hello earth\n",
            "INFO | 2024-01-01 | thread-1 | Goodbye world\n",
        ]
        input_path = self._write_log(log_lines)
        output_path = os.path.join(self.tmpdir, "out.log")

        # With threshold > max similarity, nothing is duplicate -> all kept
        clean_log(
            input_path=input_path,
            output_path=output_path,
            similarity_threshold=1.0,
            lines_to_compare=1,
        )

        with open(output_path) as f:
            result = f.readlines()
        # Threshold 1.0 means only exact matches are duplicates; these are all different
        self.assertEqual(len(result), 3)

    def test_inplace_overwrite(self):
        log_lines = [
            "INFO | 2024-01-01 | thread-1 | Hello\n",
            "INFO | 2024-01-01 | thread-1 | Hello\n",
        ]
        input_path = self._write_log(log_lines)

        clean_log(
            input_path=input_path,
            output_path=None,
            similarity_threshold=1.0,
            lines_to_compare=1,
        )

        with open(input_path) as f:
            result = f.readlines()
        self.assertEqual(len(result), 1)

    def test_stdin_stdout(self):
        log_data = "INFO | 2024-01-01 | t-1 | Msg A\nINFO | 2024-01-01 | t-1 | Msg A\n"
        fake_stdin = StringIO(log_data)
        fake_stdout = StringIO()

        with patch.object(sys, "stdin", fake_stdin), patch.object(
            sys, "stdout", fake_stdout
        ):
            clean_log(
                input_path=None,
                output_path=None,
                similarity_threshold=1.0,
                lines_to_compare=1,
            )

        output = fake_stdout.getvalue()
        # Should contain the kept line and the "Removed" summary
        self.assertIn("Msg A", output)
        self.assertIn("Removed", output)

    def test_invalid_lines_to_compare_raises(self):
        with self.assertRaises(ValueError):
            clean_log(lines_to_compare=0)
        with self.assertRaises(ValueError):
            clean_log(lines_to_compare=-1)


if __name__ == "__main__":
    unittest.main()
