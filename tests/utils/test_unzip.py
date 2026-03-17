import os
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestUnzip(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.zip_path = os.path.join(self.tmpdir, "archive.zip")
        with zipfile.ZipFile(self.zip_path, "w") as zf:
            zf.writestr("hello.txt", "hello world")
            zf.writestr("sub/nested.txt", "nested content")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_extracts_to_subfolder_named_after_zip(self):
        from ww.utils.unzip import unzip

        unzip(self.zip_path)
        dest = os.path.join(self.tmpdir, "archive")
        self.assertTrue(os.path.isdir(dest))

    def test_extracted_files_exist(self):
        from ww.utils.unzip import unzip

        unzip(self.zip_path)
        dest = os.path.join(self.tmpdir, "archive")
        self.assertTrue(os.path.exists(os.path.join(dest, "hello.txt")))

    def test_extracts_nested_files(self):
        from ww.utils.unzip import unzip

        unzip(self.zip_path)
        dest = os.path.join(self.tmpdir, "archive")
        self.assertTrue(os.path.exists(os.path.join(dest, "sub", "nested.txt")))

    def test_prints_extraction_path(self):
        from ww.utils.unzip import unzip

        with patch("builtins.print") as mock_print:
            unzip(self.zip_path)
            output = str(mock_print.call_args)
            self.assertIn("archive", output)


class TestUnzipMain(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.zip_path = os.path.join(self.tmpdir, "test.zip")
        with zipfile.ZipFile(self.zip_path, "w") as zf:
            zf.writestr("file.txt", "data")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_main_extracts_zip(self):
        from ww.utils.unzip import main

        with patch.object(sys, "argv", ["unzip", self.zip_path]):
            main()
        dest = os.path.join(self.tmpdir, "test")
        self.assertTrue(os.path.isdir(dest))


if __name__ == "__main__":
    unittest.main()
