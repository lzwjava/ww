import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestDetectEncoding(unittest.TestCase):
    def test_detects_utf8_file(self):
        from ww.encoding.check_encoding import detect_encoding

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write("Hello, world!\n".encode("utf-8"))
            f.flush()
            path = f.name

        try:
            result = detect_encoding(path)
            self.assertIn("encoding", result)
            self.assertIn("confidence", result)
            self.assertIsNotNone(result["encoding"])
            self.assertTrue(float(result["confidence"]) > 0)
        finally:
            os.unlink(path)

    def test_detects_ascii_file(self):
        from ww.encoding.check_encoding import detect_encoding

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write(b"plain ascii text\n")
            f.flush()
            path = f.name

        try:
            result = detect_encoding(path)
            self.assertIn("encoding", result)
            self.assertIsNotNone(result["encoding"])
            # chardet may report ascii, utf-8, or windows-1252 for pure ASCII content
            self.assertTrue(float(result["confidence"]) > 0)
        finally:
            os.unlink(path)

    def test_nonexistent_file_returns_error(self):
        from ww.encoding.check_encoding import detect_encoding

        result = detect_encoding("/nonexistent/path/file.txt")
        self.assertIn("error", result)

    def test_detects_latin1_content(self):
        from ww.encoding.check_encoding import detect_encoding

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            # Latin-1 specific characters
            f.write("café résumé\n".encode("latin-1"))
            f.flush()
            path = f.name

        try:
            result = detect_encoding(path)
            self.assertIn("encoding", result)
            self.assertIsNotNone(result["encoding"])
        finally:
            os.unlink(path)


class TestMain(unittest.TestCase):
    @patch("sys.argv", ["check_encoding"])
    def test_no_args_prints_usage_and_exits(self):
        from ww.encoding.check_encoding import main

        with self.assertRaises(SystemExit) as ctx:
            main()
        self.assertEqual(ctx.exception.code, 1)

    @patch("sys.argv", ["check_encoding", "/nonexistent/file.txt"])
    def test_nonexistent_file_exits(self):
        from ww.encoding.check_encoding import main

        with self.assertRaises(SystemExit) as ctx:
            main()
        self.assertEqual(ctx.exception.code, 1)

    @patch("sys.argv")
    def test_valid_file(self, mock_argv):
        from ww.encoding.check_encoding import main

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write(b"Hello, world!\n")
            f.flush()
            path = f.name

        try:
            mock_argv.__getitem__ = lambda self, i: ["check_encoding", path][i]
            mock_argv.__len__ = lambda self: 2
            main()  # should not raise
        finally:
            os.unlink(path)

    @patch("sys.argv")
    def test_error_in_detect_exits(self, mock_argv):
        from ww.encoding.check_encoding import main

        mock_argv.__getitem__ = lambda self, i: ["check_encoding", "/nonexistent"][i]
        mock_argv.__len__ = lambda self: 2

        with patch("ww.encoding.check_encoding.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_cls.return_value = mock_path

            with patch(
                "ww.encoding.check_encoding.detect_encoding",
                return_value={"error": "permission denied"},
            ):
                with self.assertRaises(SystemExit) as ctx:
                    main()
                self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
