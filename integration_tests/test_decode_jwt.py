import unittest
from integration_tests.helpers import run_ww


class TestDecodeJWTCommand(unittest.TestCase):
    # A simple HS256 JWT: header={"alg":"HS256","typ":"JWT"}, payload={"sub":"1234567890","name":"John Doe","iat":1516239022}
    SAMPLE_JWT = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
        ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )

    def test_decode_jwt_header(self):
        returncode, stdout, stderr = run_ww("utils", "decode-jwt", self.SAMPLE_JWT)
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Header:", stdout)
        self.assertIn("HS256", stdout)
        self.assertIn("JWT", stdout)

    def test_decode_jwt_payload(self):
        returncode, stdout, stderr = run_ww("utils", "decode-jwt", self.SAMPLE_JWT)
        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Payload:", stdout)
        self.assertIn("1234567890", stdout)
        self.assertIn("John Doe", stdout)

    def test_decode_jwt_invalid_token(self):
        returncode, stdout, stderr = run_ww("utils", "decode-jwt", "not.a.jwt")
        # Should not crash — prints an error message instead
        output = stdout + stderr
        self.assertTrue(
            returncode != 0 or "error" in output.lower() or "decode" in output.lower()
        )


if __name__ == "__main__":
    unittest.main()
