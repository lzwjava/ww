import os
import subprocess
import sys
import tempfile
import unittest


WW_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_ww(*args, input_text=None, timeout=30):
    """Run ww CLI command and return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env["PYTHONPATH"] = WW_PROJECT + ":" + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", "from ww.main import main; main()"] + list(args),
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=WW_PROJECT,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


class TestWWNoArgs(unittest.TestCase):
    def test_no_args_prints_hello_world(self):
        returncode, stdout, stderr = run_ww()
        self.assertEqual(returncode, 0)
        self.assertIn("hello world", stdout)


class TestWWUnknownCommand(unittest.TestCase):
    def test_unknown_command_exits_nonzero(self):
        returncode, stdout, stderr = run_ww("nonexistent-command-xyz")
        self.assertNotEqual(returncode, 0)

    def test_unknown_command_prints_error(self):
        returncode, stdout, stderr = run_ww("nonexistent-command-xyz")
        output = stdout + stderr
        self.assertIn("Unknown command", output)


class TestBase64Command(unittest.TestCase):
    def test_encode_decode_hello(self):
        returncode, stdout, stderr = run_ww("base64", "hello")
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Encoded string:", stdout)
        self.assertIn("aGVsbG8=", stdout)  # base64 of "hello"
        self.assertIn("Decoded string:", stdout)
        self.assertIn("hello", stdout)

    def test_encode_decode_with_spaces(self):
        returncode, stdout, stderr = run_ww("base64", "hello world")
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Encoded string:", stdout)
        self.assertIn("aGVsbG8gd29ybGQ=", stdout)  # base64 of "hello world"
        self.assertIn("Decoded string:", stdout)
        self.assertIn("hello world", stdout)

    def test_encode_decode_roundtrip(self):
        returncode, stdout, stderr = run_ww("base64", "test-string-123")
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("test-string-123", stdout)


class TestDecodeJWTCommand(unittest.TestCase):
    # A simple HS256 JWT: header={"alg":"HS256","typ":"JWT"}, payload={"sub":"1234567890","name":"John Doe","iat":1516239022}
    SAMPLE_JWT = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
        ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )

    def test_decode_jwt_header(self):
        returncode, stdout, stderr = run_ww("decode-jwt", self.SAMPLE_JWT)
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Header:", stdout)
        self.assertIn("HS256", stdout)
        self.assertIn("JWT", stdout)

    def test_decode_jwt_payload(self):
        returncode, stdout, stderr = run_ww("decode-jwt", self.SAMPLE_JWT)
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Payload:", stdout)
        self.assertIn("1234567890", stdout)
        self.assertIn("John Doe", stdout)

    def test_decode_jwt_invalid_token(self):
        returncode, stdout, stderr = run_ww("decode-jwt", "not.a.jwt")
        # Should not crash — prints an error message instead
        output = stdout + stderr
        self.assertTrue(
            returncode != 0 or "error" in output.lower() or "decode" in output.lower()
        )


class TestFindLargeDirsCommand(unittest.TestCase):
    def test_find_large_dirs_in_tmp(self):
        returncode, stdout, stderr = run_ww(
            "find-large-dirs", "--mb", "0", tempfile.gettempdir()
        )
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Finding directories", stdout)

    def test_find_large_dirs_default_path(self):
        returncode, stdout, stderr = run_ww(
            "find-large-dirs", "--mb", "999999", WW_PROJECT
        )
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Finding directories", stdout)

    def test_find_large_dirs_nonexistent_path(self):
        returncode, stdout, stderr = run_ww("find-large-dirs", "/nonexistent/path/xyz")
        self.assertNotEqual(returncode, 0)
        output = stdout + stderr
        self.assertIn("Error", output)

    def test_find_large_dirs_not_a_directory(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"content")
            tmpfile = f.name
        try:
            returncode, stdout, stderr = run_ww("find-large-dirs", tmpfile)
            self.assertNotEqual(returncode, 0)
            output = stdout + stderr
            self.assertIn("Error", output)
        finally:
            os.unlink(tmpfile)


class TestImageCompressCommand(unittest.TestCase):
    def _create_test_png(self, path):
        try:
            from PIL import Image
            import numpy as np
        except ImportError:
            self.skipTest("PIL/numpy not installed")
        img = Image.fromarray(np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8))
        img.save(path, "PNG")

    def test_compress_image_creates_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "test.png")
            self._create_test_png(input_path)
            returncode, stdout, stderr = run_ww(
                "image-compress", input_path, "--compression_factor", "0.5"
            )
            self.assertEqual(returncode, 0, stderr)
            self.assertIn("Compressed image saved as:", stdout)
            output_path = os.path.join(tmpdir, "test_compressed.png")
            self.assertTrue(os.path.exists(output_path), "Compressed file not created")

    def test_compress_image_default_factor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "img.png")
            self._create_test_png(input_path)
            returncode, stdout, stderr = run_ww("image-compress", input_path)
            self.assertEqual(returncode, 0, stderr)
            self.assertIn("Compressed image saved as:", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
