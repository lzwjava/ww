import base64
import unittest
from unittest.mock import patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestBase64Utils(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        text = "hello world"
        encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        decoded = base64.b64decode(encoded).decode("utf-8")
        self.assertEqual(decoded, text)

    @patch("sys.argv", ["base64utils", "hello"])
    def test_main_prints_encoded_and_decoded(self):
        from ww.utils.base64utils import main

        with patch("builtins.print") as mock_print:
            main()
            output = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("Encoded", output)
            self.assertIn("Decoded", output)

    @patch("sys.argv", ["base64utils", "test123"])
    def test_main_encodes_correctly(self):
        from ww.utils.base64utils import main

        expected_encoded = base64.b64encode(b"test123").decode("utf-8")
        with patch("builtins.print") as mock_print:
            main()
            all_output = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn(expected_encoded, all_output)


if __name__ == "__main__":
    unittest.main()
