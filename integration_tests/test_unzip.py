import os
import tempfile
import unittest
import zipfile
from integration_tests.helpers import run_ww


class TestUnzipCommand(unittest.TestCase):
    def _create_test_zip(self, tmpdir, files):
        zip_path = os.path.join(tmpdir, "test.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return zip_path

    def test_extracts_to_folder_with_same_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_test_zip(
                tmpdir, {"hello.txt": "world", "sub/test.py": "print(1)"}
            )
            returncode, stdout, stderr = run_ww(
                "utils", "unzip", os.path.join(tmpdir, "test.zip")
            )
            self.assertEqual(returncode, 0, stderr)
            extracted_dir = os.path.join(tmpdir, "test")
            self.assertTrue(os.path.isdir(extracted_dir))
            self.assertIn("test", stdout)

    def test_extracts_file_contents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "Hello World Content"
            zip_path = self._create_test_zip(tmpdir, {"hello.txt": content})
            run_ww("utils", "unzip", zip_path)
            extracted_file = os.path.join(tmpdir, "test", "hello.txt")
            with open(extracted_file) as f:
                self.assertEqual(f.read(), content)


if __name__ == "__main__":
    unittest.main()
