import os
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestTitleToSlug(unittest.TestCase):
    def _call(self, title):
        from ww.note.create_note_from_clipboard import _title_to_slug

        return _title_to_slug(title)

    def test_simple_title(self):
        self.assertEqual(self._call("Hello World"), "hello-world")

    def test_removes_apostrophes(self):
        result = self._call("It's a Test")
        self.assertNotIn("'", result)

    def test_removes_special_chars(self):
        result = self._call("Hello! World?")
        self.assertNotIn("!", result)
        self.assertNotIn("?", result)

    def test_collapses_dashes(self):
        result = self._call("a---b")
        self.assertNotIn("--", result)

    def test_strips_leading_trailing_dashes(self):
        result = self._call("-hello-")
        self.assertFalse(result.startswith("-"))
        self.assertFalse(result.endswith("-"))

    def test_empty_slug_raises(self):
        with self.assertRaises(ValueError):
            self._call("!!!")

    def test_truncates_long_slug(self):
        long_title = " ".join(["word"] * 20)
        result = self._call(long_title)
        self.assertLessEqual(len(result), 80)
        parts = result.split("-")
        self.assertLessEqual(len(parts), 8)


class TestTitlesFromCustom(unittest.TestCase):
    def test_returns_both_titles(self):
        from ww.note.create_note_from_clipboard import _titles_from_custom

        full, short = _titles_from_custom("My Custom Title")
        self.assertEqual(full, "My Custom Title")
        self.assertIn("my-custom-title", short)


class TestGenerateTitles(unittest.TestCase):
    @patch(
        "ww.note.create_note_from_clipboard.generate_title", return_value="Test Title"
    )
    def test_returns_full_and_short(self, mock_gen):
        from ww.note.create_note_from_clipboard import _generate_titles

        full, short = _generate_titles("some content here")
        self.assertEqual(full, "Test Title")
        self.assertEqual(short, "test-title")


class TestCreateNoteFromContent(unittest.TestCase):
    @patch("ww.note.create_note_from_clipboard.write_note")
    @patch("ww.note.create_note_from_clipboard.clean_content", return_value="cleaned")
    @patch(
        "ww.note.create_note_from_clipboard.format_front_matter",
        return_value="---\n---",
    )
    @patch(
        "ww.note.create_note_from_clipboard.create_filename",
        return_value="/tmp/note.md",
    )
    @patch(
        "ww.note.create_note_from_clipboard.generate_title", return_value="Test Title"
    )
    @patch(
        "ww.note.create_note_from_clipboard.clean_grok_tags",
        return_value="cleaned content",
    )
    def test_creates_note_with_generated_title(
        self,
        mock_clean_grok,
        mock_gen_title,
        mock_create_fn,
        mock_fm,
        mock_clean,
        mock_write,
    ):
        from ww.note.create_note_from_clipboard import create_note_from_content

        content = "x" * 250
        result = create_note_from_content(content)
        self.assertEqual(result, "/tmp/note.md")
        mock_write.assert_called_once()

    def test_raises_on_empty_content(self):
        from ww.note.create_note_from_clipboard import create_note_from_content

        with self.assertRaises(ValueError):
            create_note_from_content("")

    def test_raises_on_short_content(self):
        from ww.note.create_note_from_clipboard import create_note_from_content

        with self.assertRaises(ValueError):
            create_note_from_content("short")

    @patch("ww.note.create_note_from_clipboard.write_note")
    @patch("ww.note.create_note_from_clipboard.clean_content", return_value="cleaned")
    @patch(
        "ww.note.create_note_from_clipboard.format_front_matter",
        return_value="---\n---",
    )
    @patch(
        "ww.note.create_note_from_clipboard.create_filename",
        return_value="/tmp/note.md",
    )
    @patch("ww.note.create_note_from_clipboard.clean_grok_tags", return_value="cleaned")
    def test_custom_title_skips_generation(
        self, mock_clean_grok, mock_create_fn, mock_fm, mock_clean, mock_write
    ):
        from ww.note.create_note_from_clipboard import create_note_from_content

        content = "x" * 250
        result = create_note_from_content(content, custom_title="My Title")
        self.assertEqual(result, "/tmp/note.md")


class TestCreateNote(unittest.TestCase):
    @patch(
        "ww.note.create_note_from_clipboard.create_note_from_content",
        return_value="/tmp/n.md",
    )
    @patch(
        "ww.note.create_note_from_clipboard.get_clipboard_content",
        return_value="x" * 250,
    )
    @patch(
        "ww.note.create_note_from_clipboard.check_duplicate_notes", return_value=False
    )
    def test_creates_note_from_clipboard(self, mock_dup, mock_clip, mock_create):
        from ww.note.create_note_from_clipboard import create_note

        result = create_note()
        self.assertEqual(result, "/tmp/n.md")

    @patch(
        "ww.note.create_note_from_clipboard.check_duplicate_notes", return_value=True
    )
    def test_raises_on_duplicate(self, mock_dup):
        from ww.note.create_note_from_clipboard import create_note

        with self.assertRaises(ValueError):
            create_note()


if __name__ == "__main__":
    unittest.main()
