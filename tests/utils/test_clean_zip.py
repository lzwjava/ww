import os
import tempfile
import unittest
import zipfile

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestCleanZip(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _make_zip(self, files):
        zip_path = os.path.join(self.tmpdir, "input.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return zip_path

    def test_removes_files_without_extensions(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"valid.txt": "hello", "no_extension": "world"})
        clean_zip(zip_path)
        out_path = os.path.join(self.tmpdir, "input_output.zip")
        self.assertTrue(os.path.exists(out_path))
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("valid.txt", names)
        self.assertNotIn("no_extension", names)

    def test_keeps_directories(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"dir/": "", "dir/file.txt": "content"})
        clean_zip(zip_path)
        out_path = os.path.join(self.tmpdir, "input_output.zip")
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("dir/", names)
        self.assertIn("dir/file.txt", names)

    def test_does_not_create_output_when_no_valid_files(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"noext1": "a", "noext2": "b"})
        clean_zip(zip_path)
        out_path = os.path.join(self.tmpdir, "input_output.zip")
        self.assertFalse(os.path.exists(out_path))

    def test_output_path_naming(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"a.txt": "content"})
        clean_zip(zip_path)
        expected = os.path.join(self.tmpdir, "input_output.zip")
        self.assertTrue(os.path.exists(expected))

    def test_keeps_multiple_extensions(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"a.tar.gz": "x", "b.py": "y", "noext": "z"})
        clean_zip(zip_path)
        out_path = os.path.join(self.tmpdir, "input_output.zip")
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("a.tar.gz", names)
        self.assertIn("b.py", names)
        self.assertNotIn("noext", names)


if __name__ == "__main__":
    unittest.main()
