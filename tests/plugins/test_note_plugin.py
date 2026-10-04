import json
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

# Import the note plugin from the repo copy (agent_plugin/) — the source of
# truth that gets deployed to ~/.hermes/plugins. Importing the installed copy
# would make these tests depend on the machine's plugin version.
_plugin_parent = str(
    Path(__file__).resolve().parents[2] / "agent_plugin" / "hermes" / "plugins"
)
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
    def _mock_deps(self, msg_content="x" * 300):
        """Mock external deps and point the note queue at a temp file.
        Returns the temp queue file path."""
        msg = {"role": "assistant", "content": msg_content}
        self._patchers = ExitStack()
        self._patchers.enter_context(
            patch("note._get_assistant_messages", return_value=[msg])
        )
        self._patchers.enter_context(patch("dotenv.load_dotenv"))
        queue_file = Path(tempfile.mkdtemp()) / "note_queue.json"
        self._patchers.enter_context(
            patch("ww.note.note_queue._queue_file", return_value=queue_file)
        )
        return queue_file

    def setUp(self):
        self._stack = ExitStack()

    def tearDown(self):
        self._stack.close()

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
        queue_file = self._mock_deps()
        result = _handle_note('--title "My Title"')
        self.assertIsNotNone(result)
        self.assertIn("Queued", result)
        entries = json.loads(queue_file.read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].get("custom_title"), "My Title")
        self.assertEqual(entries[0].get("status"), "pending")

    def test_dir_arg(self):
        queue_file = self._mock_deps()
        result = _handle_note("--dir /custom/dir")
        self.assertIsNotNone(result)
        self.assertIn("Queued", result)
        entries = json.loads(queue_file.read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].get("directory"), "/custom/dir")
