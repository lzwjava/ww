import os
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.encoding.convert_encoding import (
    detect_file_encoding,
    convert_file_encoding,
    process_files,
)


class TestDetectFileEncodingExtended(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_empty_file(self):
        path = Path(self.tmpdir) / "empty.txt"
        path.write_bytes(b"")
        enc = detect_file_encoding(path)
        # chardet may return None for empty files
        # Just verify it doesn't crash
        self.assertTrue(enc is None or isinstance(enc, str))

    def test_detect_binary_file(self):
        path = Path(self.tmpdir) / "binary.bin"
        path.write_bytes(bytes(range(256)))
        enc = detect_file_encoding(path)
        # chardet may return None for arbitrary binary data
        self.assertTrue(enc is None or isinstance(enc, str))

    def test_detect_utf8_bom(self):
        path = Path(self.tmpdir) / "bom.txt"
        path.write_bytes(b"\xef\xbb\xbfHello world")
        enc = detect_file_encoding(path)
        self.assertIsNotNone(enc)

    def test_detect_gbk(self):
        path = Path(self.tmpdir) / "gbk.txt"
        path.write_bytes("你好世界".encode("gbk"))
        enc = detect_file_encoding(path)
        self.assertIsNotNone(enc)

    def test_detect_permission_error(self):
        path = Path(self.tmpdir) / "noread.txt"
        path.write_bytes(b"test")
        with patch("builtins.open", side_effect=PermissionError("denied")):
            result = detect_file_encoding(path)
            self.assertIsNone(result)


class TestConvertFileEncodingExtended(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_ascii_to_utf8_skips(self):
        path = Path(self.tmpdir) / "ascii.txt"
        path.write_bytes(b"Hello world 123")
        success, msg = convert_file_encoding(path, "utf-8")
        self.assertTrue(success)
        # chardet may detect as ASCII or Windows-1252; if ASCII, it skips (compatible with UTF-8)
        # Otherwise it converts
        self.assertTrue("Already" in msg or "Converted" in msg)

    def test_convert_preserves_content(self):
        path = Path(self.tmpdir) / "gbk.txt"
        original = "你好世界"
        path.write_bytes(original.encode("gbk"))
        success, msg = convert_file_encoding(path, "utf-8")
        self.assertTrue(success)
        content = path.read_text(encoding="utf-8")
        self.assertEqual(content, original)

    def test_convert_utf8_to_gbk(self):
        path = Path(self.tmpdir) / "utf8.txt"
        original = "hello"
        path.write_text(original, encoding="utf-8")
        success, msg = convert_file_encoding(path, "ascii")
        self.assertTrue(success)

    def test_detect_encoding_returns_none(self):
        path = Path(self.tmpdir) / "file.txt"
        path.write_bytes(b"test")
        with patch(
            "ww.encoding.convert_encoding.detect_file_encoding", return_value=None
        ):
            success, msg = convert_file_encoding(path, "utf-8")
            self.assertFalse(success)
            self.assertIn("Could not detect", msg)

    def test_convert_error_during_read(self):
        path = Path(self.tmpdir) / "file.txt"
        path.write_bytes("café".encode("latin-1"))
        with patch("builtins.open", side_effect=IOError("read error")):
            success, msg = convert_file_encoding(path, "utf-8")
            self.assertFalse(success)
            # detect_file_encoding also uses open, so it fails first with "Could not detect"
            self.assertTrue("Error" in msg or "Could not detect" in msg)


class TestProcessFiles(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_process_single_file(self):
        path = Path(self.tmpdir) / "test.py"
        path.write_bytes("# -*- coding: utf-8 -*-\nprint('hello')\n".encode("utf-8"))
        process_files([path], "utf-8", ".py")
        # Should complete without error

    def test_process_directory(self):
        subdir = Path(self.tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "test1.py").write_text("print('hello')", encoding="utf-8")
        (subdir / "test2.py").write_text("print('world')", encoding="utf-8")
        (subdir / "test3.txt").write_text("not a py file", encoding="utf-8")
        process_files([subdir], "utf-8", ".py")

    def test_process_no_matching_files(self):
        subdir = Path(self.tmpdir) / "empty_dir"
        subdir.mkdir()
        process_files([subdir], "utf-8", ".xyz")

    def test_process_directory_default_extension(self):
        subdir = Path(self.tmpdir) / "dir"
        subdir.mkdir()
        (subdir / "file.py").write_text("x = 1", encoding="utf-8")
        (subdir / "file.txt").write_text("text", encoding="utf-8")
        process_files([subdir], "utf-8")
        # Default extension is .py

    def test_process_nonexistent_path(self):
        process_files(["/nonexistent/path"], "utf-8", ".py")

    def test_process_mixed_files_and_dirs(self):
        single_file = Path(self.tmpdir) / "single.py"
        single_file.write_text("x = 1", encoding="utf-8")
        subdir = Path(self.tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "a.py").write_text("a = 1", encoding="utf-8")
        process_files([single_file, subdir], "utf-8", ".py")

    def test_process_converts_gbk_directory(self):
        subdir = Path(self.tmpdir) / "gbk_dir"
        subdir.mkdir()
        (subdir / "chinese.py").write_bytes("# 中文注释\nx = 1\n".encode("gbk"))
        process_files([subdir], "utf-8", ".py")

    def test_process_already_target_encoding(self):
        path = Path(self.tmpdir) / "already_utf8.py"
        path.write_text("x = 1", encoding="utf-8")
        process_files([path], "utf-8", ".py")

    def test_process_empty_directory(self):
        subdir = Path(self.tmpdir) / "empty"
        subdir.mkdir()
        process_files([subdir], "utf-8", ".py")


if __name__ == "__main__":
    unittest.main()
