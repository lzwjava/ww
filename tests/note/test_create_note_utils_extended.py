import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGetFirstNWords(unittest.TestCase):
    def test_returns_first_n_words(self):
        from ww.note.create_note_utils import get_first_n_words

        result = get_first_n_words("one two three four five", 3)
        self.assertEqual(result, "one two three")

    def test_returns_all_when_fewer_than_n(self):
        from ww.note.create_note_utils import get_first_n_words

        result = get_first_n_words("one two", 10)
        self.assertEqual(result, "one two")

    def test_empty_text(self):
        from ww.note.create_note_utils import get_first_n_words

        result = get_first_n_words("", 5)
        self.assertEqual(result, "")


class TestCallLlmOrExit(unittest.TestCase):
    @patch("ww.note.create_note_utils.call_openrouter_api", return_value="result")
    def test_returns_result(self, mock_api):
        from ww.note.create_note_utils import _call_llm_or_exit

        result = _call_llm_or_exit("prompt", "error")
        self.assertEqual(result, "result")

    @patch("ww.note.create_note_utils.call_openrouter_api", return_value=None)
    def test_raises_on_empty_result(self, mock_api):
        from ww.note.create_note_utils import _call_llm_or_exit

        with self.assertRaises(RuntimeError):
            _call_llm_or_exit("prompt", "error msg")

    @patch(
        "ww.note.create_note_utils.call_openrouter_api", side_effect=Exception("boom")
    )
    def test_raises_on_api_exception(self, mock_api):
        from ww.note.create_note_utils import _call_llm_or_exit

        with self.assertRaises(RuntimeError):
            _call_llm_or_exit("prompt", "error")


class TestGenerateShortTitle(unittest.TestCase):
    @patch("ww.note.create_note_utils._call_llm_or_exit", return_value="Short Title")
    def test_returns_llm_result(self, mock_call):
        from ww.note.create_note_utils import generate_short_title

        result = generate_short_title("prompt")
        self.assertEqual(result, "Short Title")


class TestFixLiquidRawTags(unittest.TestCase):
    def test_no_code_blocks_unchanged(self):
        from ww.note.create_note_utils import fix_liquid_raw_tags

        content = "Hello world\nNo code blocks here"
        result = fix_liquid_raw_tags(content)
        self.assertEqual(result, content)

    def test_wraps_code_block_with_liquid(self):
        from ww.note.create_note_utils import fix_liquid_raw_tags

        content = "text\n```\nx = {{something}}\n```\nmore"
        result = fix_liquid_raw_tags(content)
        self.assertIn("{% raw %}", result)
        self.assertIn("{% endraw %}", result)

    def test_does_not_double_wrap(self):
        from ww.note.create_note_utils import fix_liquid_raw_tags

        content = "text\n{% raw %}\n```\nx = {{something}}\n```\n{% endraw %}"
        result = fix_liquid_raw_tags(content)
        count = result.count("{% raw %}")
        self.assertEqual(count, 1)

    def test_code_block_without_liquid_unchanged(self):
        from ww.note.create_note_utils import fix_liquid_raw_tags

        content = "text\n```\nprint('hello')\n```\nmore"
        result = fix_liquid_raw_tags(content)
        self.assertNotIn("{% raw %}", result)
        self.assertIn("print('hello')", result)

    def test_tilde_fence_detected(self):
        from ww.note.create_note_utils import fix_liquid_raw_tags

        content = "text\n~~~\nx = {% tag %}\n~~~\nmore"
        result = fix_liquid_raw_tags(content)
        self.assertIn("{% raw %}", result)


class TestWriteNote(unittest.TestCase):
    def test_writes_front_matter_and_content(self):
        from ww.note.create_note_utils import write_note

        tmpdir = tempfile.mkdtemp()
        filepath = os.path.join(tmpdir, "test.md")
        try:
            write_note(filepath, "---\ntitle: test\n---", "Hello content")
            with open(filepath) as f:
                text = f.read()
            self.assertIn("---", text)
            self.assertIn("Hello content", text)
        finally:
            import shutil

            shutil.rmtree(tmpdir)


class TestFormatFrontMatterAdditional(unittest.TestCase):
    def test_uses_today_when_no_date(self):
        from ww.note.create_note_utils import format_front_matter

        result = format_front_matter("Title")
        self.assertIn("title: Title", result)
        self.assertTrue(result.startswith("---"))
        self.assertTrue(result.endswith("---"))

    def test_contains_all_fields(self):
        from ww.note.create_note_utils import format_front_matter

        result = format_front_matter("Title", "2024-01-01")
        self.assertIn("audio: false", result)
        self.assertIn("generated: true", result)
        self.assertIn("image: false", result)
        self.assertIn("lang: en", result)
        self.assertIn("type: note", result)


if __name__ == "__main__":
    unittest.main()
