import unittest
from integration_tests.helpers import run_ww


class TestBase64Command(unittest.TestCase):
    def test_encode_decode_hello(self):
        returncode, stdout, stderr = run_ww("utils", "base64", "hello")
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Encoded string:", stdout)
        self.assertIn("aGVsbG8=", stdout)  # base64 of "hello"
        self.assertIn("Decoded string:", stdout)
        self.assertIn("hello", stdout)

    def test_encode_decode_with_spaces(self):
        returncode, stdout, stderr = run_ww("utils", "base64", "hello world")
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Encoded string:", stdout)
        self.assertIn("aGVsbG8gd29ybGQ=", stdout)  # base64 of "hello world"
        self.assertIn("Decoded string:", stdout)
        self.assertIn("hello world", stdout)

    def test_encode_decode_roundtrip(self):
        returncode, stdout, stderr = run_ww("utils", "base64", "test-string-123")
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("test-string-123", stdout)


if __name__ == "__main__":
    unittest.main()
