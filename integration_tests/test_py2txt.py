import os
import tempfile
import unittest
from integration_tests.helpers import run_ww


class TestPy2TxtCommand(unittest.TestCase):
    def test_converts_files_to_txt_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "readme.md"), "w") as f:
                f.write("# Hello")
            dest_dir = os.path.join(tmpdir, "txt")
            returncode, stdout, stderr = run_ww("utils", "py2txt", tmpdir, dest_dir)
            self.assertEqual(returncode, 0, stderr)
            output_txt = os.path.join(dest_dir, "readme.txt")
            self.assertTrue(os.path.exists(output_txt), f"File not found: {output_txt}")

    def test_preserves_file_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "Test content with special chars: $%^"
            with open(os.path.join(tmpdir, "data.json"), "w") as f:
                f.write(content)
            dest_dir = os.path.join(tmpdir, "txt")
            returncode, stdout, stderr = run_ww("utils", "py2txt", tmpdir, dest_dir)
            self.assertEqual(returncode, 0, stderr)
            output_txt = os.path.join(dest_dir, "data.txt")
            self.assertTrue(os.path.exists(output_txt))
            with open(output_txt) as f:
                self.assertEqual(f.read(), content)


if __name__ == "__main__":
    unittest.main()
