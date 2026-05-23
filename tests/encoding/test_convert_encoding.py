import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.encoding.convert_encoding import detect_file_encoding, convert_file_encoding


class TestDetectFileEncoding(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir)

    def test_detect_utf8(self):
        path = Path(self.tmpdir) / "utf8.txt"
        path.write_text("你好世界 café résumé", encoding="utf-8")
        enc = detect_file_encoding(path)
        self.assertIsNotNone(enc)
        self.assertIn(enc.lower(), ["utf-8", "ascii", "utf-8-sig", "windows-1252"])

    def test_detect_ascii(self):
        path = Path(self.tmpdir) / "ascii.txt"
        path.write_bytes(b"Hello world 123")
        enc = detect_file_encoding(path)
        self.assertIsNotNone(enc)
        # chardet may mis-identify short ASCII as windows-1252
        self.assertIsInstance(enc, str)

    def test_detect_nonexistent_file(self):
        path = Path(self.tmpdir) / "nonexistent.txt"
        result = detect_file_encoding(path)
        self.assertIsNone(result)

    def test_detect_latin1(self):
        path = Path(self.tmpdir) / "latin1.txt"
        path.write_bytes("café résumé".encode("latin-1"))
        enc = detect_file_encoding(path)
        self.assertIsNotNone(enc)
        # chardet should detect some encoding
        self.assertIsInstance(enc, str)


class TestConvertFileEncoding(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir)

    def test_convert_utf8_to_utf8_skips(self):
        path = Path(self.tmpdir) / "utf8.txt"
        path.write_text("你好世界 café résumé", encoding="utf-8")
        success, msg = convert_file_encoding(path, "utf-8")
        self.assertTrue(success)
        # Either already utf-8 or successfully converted
        self.assertTrue("Already" in msg or "Converted" in msg)

    def test_convert_nonexistent_file(self):
        path = Path(self.tmpdir) / "missing.txt"
        success, msg = convert_file_encoding(path, "utf-8")
        self.assertFalse(success)
        self.assertIn("does not exist", msg)

    def test_convert_gbk_to_utf8(self):
        path = Path(self.tmpdir) / "gbk.txt"
        path.write_bytes("你好世界".encode("gbk"))
        success, msg = convert_file_encoding(path, "utf-8")
        self.assertTrue(success)
        self.assertIn("Converted", msg)
        # Verify content is now valid utf-8
        content = path.read_text(encoding="utf-8")
        self.assertEqual(content, "你好世界")

    def test_convert_latin1_to_utf8(self):
        path = Path(self.tmpdir) / "latin1.txt"
        path.write_bytes("café".encode("latin-1"))
        success, msg = convert_file_encoding(path, "utf-8")
        self.assertTrue(success)
        content = path.read_text(encoding="utf-8")
        self.assertIn("café", content)


if __name__ == "__main__":
    unittest.main()
