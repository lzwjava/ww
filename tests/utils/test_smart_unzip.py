import os
import tempfile
import unittest
import zipfile

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestSmartUnzip(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _make_zip(self, files):
        zip_path = os.path.join(self.tmpdir, "test.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return zip_path

    def test_creates_processed_zip(self):
        from ww.utils.smart_unzip import smart_unzip

        zip_path = self._make_zip({"file.txt": "hello"})
        smart_unzip(zip_path)
        out_path = os.path.join(self.tmpdir, "test_processed.zip")
        self.assertTrue(os.path.exists(out_path))

    def test_renames_extensionless_files_with_unknown(self):
        from ww.utils.smart_unzip import smart_unzip

        zip_path = self._make_zip({"no_ext": "data", "has.txt": "text"})
        smart_unzip(zip_path)
        out_path = os.path.join(self.tmpdir, "test_processed.zip")
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("no_ext", names)
        self.assertIn("has.txt", names)

    def test_files_with_extensions_preserved(self):
        from ww.utils.smart_unzip import smart_unzip

        zip_path = self._make_zip({"doc.pdf": "pdf content", "img.png": "png"})
        smart_unzip(zip_path)
        out_path = os.path.join(self.tmpdir, "test_processed.zip")
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("doc.pdf", names)
        self.assertIn("img.png", names)

    def test_output_zip_name_derived_from_input(self):
        from ww.utils.smart_unzip import smart_unzip

        zip_path = os.path.join(self.tmpdir, "myarchive.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file.txt", "content")
        smart_unzip(zip_path)
        expected = os.path.join(self.tmpdir, "myarchive_processed.zip")
        self.assertTrue(os.path.exists(expected))


if __name__ == "__main__":
    unittest.main()
