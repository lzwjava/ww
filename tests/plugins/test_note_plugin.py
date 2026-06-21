import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

# Import the note plugin from ~/.hermes/plugins/note/
_plugin_parent = str(Path.home() / ".hermes" / "plugins")
sys.path.insert(0, _plugin_parent)

from note import _strip_reasoning_tags, _content_as_text, _handle_note  # noqa: E402


class TestStripReasoningTags(unittest.TestCase):
    def test_removes_thinking_tags(self):
        text = "Hello <thinking>internal thought</thinking> world"
        result = _strip_reasoning_tags(text)
        self.assertNotIn("thinking", result)
        self.assertIn("Hello", result)
        self.assertIn("world", result)

    def test_removes_reasoning_tags(self):
        text = "Before <reasoning>chain of thought</reasoning> After"
        result = _strip_reasoning_tags(text)
        self.assertNotIn("reasoning", result)
        self.assertIn("Before", result)
        self.assertIn("After", result)

    def test_removes_scratchpad_tags(self):
        text = "A <scratchpad>notes</scratchpad> B"
        result = _strip_reasoning_tags(text)
        self.assertNotIn("scratchpad", result)

    def test_no_tags_unchanged(self):
        text = "Plain text without tags"
        result = _strip_reasoning_tags(text)
        self.assertEqual(result, text)

    def test_multiline_thinking_block(self):
        text = "Before\n<thinking>\nline1\nline2\n</thinking>\nAfter"
        result = _strip_reasoning_tags(text)
        self.assertNotIn("line1", result)
        self.assertIn("Before", result)
        self.assertIn("After", result)


class TestContentAsText(unittest.TestCase):
    def test_none_returns_empty(self):
        self.assertEqual(_content_as_text(None), "")

    def test_string_passthrough(self):
        self.assertEqual(_content_as_text("hello"), "hello")

    def test_list_of_text_parts(self):
        content = [
            {"type": "text", "text": "part1"},
            {"type": "text", "text": "part2"},
        ]
        result = _content_as_text(content)
        self.assertIn("part1", result)
        self.assertIn("part2", result)

    def test_list_filters_non_text_parts(self):
        content = [
            {"type": "text", "text": "visible"},
            {"type": "image", "url": "http://example.com/img.png"},
        ]
        result = _content_as_text(content)
        self.assertEqual(result, "visible")

    def test_empty_list_returns_empty(self):
        self.assertEqual(_content_as_text([]), "")

    def test_other_type_converts_to_string(self):
        result = _content_as_text(42)
        self.assertEqual(result, "42")


class TestHandleNoteParsing(unittest.TestCase):
    def test_no_assistant_messages(self):
        with patch("note._get_assistant_messages", return_value=[]):
            result = _handle_note("")
            self.assertIsNotNone(result)
            self.assertIn("No assistant responses", result)

    def test_invalid_number(self):
        msg = {"role": "assistant", "content": "hello"}
        with patch("note._get_assistant_messages", return_value=[msg]):
            result = _handle_note("99")
            self.assertIsNotNone(result)
            self.assertIn("Invalid", result)

    def test_title_arg(self):
        msg = {"role": "assistant", "content": "x" * 300}
        with patch("note._get_assistant_messages", return_value=[msg]):
            with patch(
                "ww.note.create_note_from_clipboard.create_note_from_content",
                return_value="/tmp/n.md",
            ):
                with patch("ww.github.gitmessageai.gitmessageai"):
                    result = _handle_note('--title "My Title"')
                    self.assertIsNotNone(result)
                    self.assertIn("saved", result.lower())

    def test_dir_arg(self):
        msg = {"role": "assistant", "content": "x" * 300}
        with patch("note._get_assistant_messages", return_value=[msg]):
            with patch(
                "ww.note.create_note_from_clipboard.create_note_from_content"
            ) as mock_create:
                mock_create.return_value = "/tmp/n.md"
                with patch("ww.github.gitmessageai.gitmessageai"):
                    _handle_note("--dir /custom/dir")
                    _, kwargs = mock_create.call_args
                    self.assertEqual(kwargs.get("directory"), "/custom/dir")
