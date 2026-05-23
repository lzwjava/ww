import os
import tempfile
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestReadInputFile(unittest.TestCase):
    def test_reads_file_content(self):
        from ww.note.obfuscate_log import read_input_file

        tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        tmpfile.write("test content")
        tmpfile.close()
        try:
            result = read_input_file(tmpfile.name)
            self.assertEqual(result, "test content")
        finally:
            os.unlink(tmpfile.name)


class TestShowDiff(unittest.TestCase):
    def test_returns_false_when_no_diff(self):
        from ww.note.obfuscate_log import show_diff

        result = show_diff("same text", "same text")
        self.assertFalse(result)

    def test_returns_true_when_diff(self):
        from ww.note.obfuscate_log import show_diff

        result = show_diff("original", "obfuscated")
        self.assertTrue(result)


class TestObfuscateLogPrompt(unittest.TestCase):
    def test_prompt_contains_content_placeholder(self):
        from ww.note.obfuscate_log import OBFUSCATE_PROMPT

        self.assertIn("{content}", OBFUSCATE_PROMPT)

    def test_prompt_includes_redaction_instructions(self):
        from ww.note.obfuscate_log import OBFUSCATE_PROMPT

        self.assertIn("API_KEY_REDACTED", OBFUSCATE_PROMPT)
        self.assertIn("PASSWORD_REDACTED", OBFUSCATE_PROMPT)
