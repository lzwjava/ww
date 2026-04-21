import unittest
import tempfile
import os
import subprocess
import sys


class TestFixTableCommand(unittest.TestCase):
    def _run(self, code):
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    def test_table_blank_line_added(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("## Heading\n| A | B |\n|---|---|\n| 1 | 2 |")
            temp_path = f.name

        try:
            returncode, stdout, stderr = self._run(
                f"from ww.content.fix_table import process_tables_in_file; "
                f"process_tables_in_file('{temp_path}', fix_tables=True)"
            )
            self.assertEqual(returncode, 0, stderr)

            with open(temp_path) as f:
                content = f.read()
            self.assertIn("## Heading\n\n| A | B |", content)
        finally:
            os.unlink(temp_path)

    def test_table_code_block_preserved(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("## Heading\n```\n| A | B |\n```\n| C | D |\n|---|---|\n| 1 | 2 |")
            temp_path = f.name

        try:
            returncode, stdout, stderr = self._run(
                f"from ww.content.fix_table import process_tables_in_file; "
                f"process_tables_in_file('{temp_path}', fix_tables=True)"
            )
            self.assertEqual(returncode, 0, stderr)

            with open(temp_path) as f:
                content = f.read()
            self.assertIn("```", content.split("## Heading")[1])
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
