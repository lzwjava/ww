import os
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestIsPhoneNumber(unittest.TestCase):
    def test_valid_phone(self):
        from ww.sync.claude import _is_phone_number

        self.assertTrue(_is_phone_number("+1-555-123-4567"))

    def test_valid_digits_and_spaces(self):
        from ww.sync.claude import _is_phone_number

        self.assertTrue(_is_phone_number("123 456 7890"))

    def test_invalid_short_number(self):
        from ww.sync.claude import _is_phone_number

        self.assertFalse(_is_phone_number("123"))

    def test_non_phone_string(self):
        from ww.sync.claude import _is_phone_number

        self.assertFalse(_is_phone_number("hello world"))


class TestSanitizeDict(unittest.TestCase):
    def test_redacts_token_key(self):
        from ww.sync.claude import sanitize_dict

        result = sanitize_dict({"api_token": "secret123"})
        self.assertEqual(result["api_token"], "REDACTED")

    def test_redacts_password_key(self):
        from ww.sync.claude import sanitize_dict

        result = sanitize_dict({"password": "mypass"})
        self.assertEqual(result["password"], "REDACTED")

    def test_redacts_key_in_name(self):
        from ww.sync.claude import sanitize_dict

        result = sanitize_dict({"secret_key": "abc"})
        self.assertEqual(result["secret_key"], "REDACTED")

    def test_preserves_normal_values(self):
        from ww.sync.claude import sanitize_dict

        result = sanitize_dict({"name": "test", "count": 42})
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["count"], 42)

    def test_recurses_into_nested_dict(self):
        from ww.sync.claude import sanitize_dict

        result = sanitize_dict({"outer": {"inner_token": "val"}})
        self.assertEqual(result["outer"]["inner_token"], "REDACTED")

    def test_sanitizes_list_items(self):
        from ww.sync.claude import sanitize_dict

        result = sanitize_dict({"items": [{"token": "v1"}, {"name": "v2"}]})
        self.assertEqual(result["items"][0]["token"], "REDACTED")
        self.assertEqual(result["items"][1]["name"], "v2")

    def test_redacts_phone_numbers(self):
        from ww.sync.claude import sanitize_dict

        result = sanitize_dict({"phone": "+1-555-123-4567"})
        self.assertEqual(result["phone"], "REDACTED")


class TestSanitizeValue(unittest.TestCase):
    def test_sanitizes_dict(self):
        from ww.sync.claude import sanitize_value

        result = sanitize_value({"token": "secret"})
        self.assertEqual(result["token"], "REDACTED")

    def test_sanitizes_phone(self):
        from ww.sync.claude import sanitize_value

        result = sanitize_value("+1-555-123-4567")
        self.assertEqual(result, "REDACTED")

    def test_preserves_normal_value(self):
        from ww.sync.claude import sanitize_value

        result = sanitize_value("normal string")
        self.assertEqual(result, "normal string")
