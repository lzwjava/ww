import os
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestDecodeJwtMain(unittest.TestCase):
    def test_decodes_valid_token_header(self):
        from ww.utils.decode_jwt import main

        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        with patch("builtins.print") as mock_print:
            with patch("sys.argv", ["decode_jwt", token]):
                main()

            calls = [str(c) for c in mock_print.call_args_list]
            output = " ".join(calls)

            self.assertIn("Header", output)
            self.assertIn("alg", output)
            self.assertIn("HS256", output)

    def test_decodes_valid_token_payload(self):
        from ww.utils.decode_jwt import main

        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        with patch("builtins.print") as mock_print:
            with patch("sys.argv", ["decode_jwt", token]):
                main()

            calls = [str(c) for c in mock_print.call_args_list]
            output = " ".join(calls)

            self.assertIn("Payload", output)
            self.assertIn("sub", output)
            self.assertIn("1234567890", output)

    def test_invalid_token_handled(self):
        from ww.utils.decode_jwt import main

        with patch("builtins.print") as mock_print:
            with patch("sys.argv", ["decode_jwt", "invalid.token.here"]):
                main()

            calls = [str(c) for c in mock_print.call_args_list]
            output = " ".join(calls)

            self.assertIn("Header decode error", output)


if __name__ == "__main__":
    unittest.main()
