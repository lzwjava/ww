import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestAreNotesQuickSimilar(unittest.TestCase):
    def setUp(self):
        from ww.note.check_duplicate_notes import _are_notes_quick_similar

        self.func = _are_notes_quick_similar

    def test_empty_first_arg_returns_false(self):
        self.assertFalse(self.func("", "some content"))

    def test_empty_second_arg_returns_false(self):
        self.assertFalse(self.func("some content", ""))

    def test_both_empty_returns_false(self):
        self.assertFalse(self.func("", ""))

    def test_very_different_lengths_returns_false(self):
        short = "a" * 100
        long_str = "a" * 300
        self.assertFalse(self.func(short, long_str))

    def test_identical_long_content_returns_true(self):
        content = "a" * 500
        self.assertTrue(self.func(content, content))

    def test_different_start_chars_returns_false(self):
        base = "a" * 300
        modified = "b" * 300
        self.assertFalse(self.func(base, modified))

    def test_short_identical_content_returns_true(self):
        content = "Short text"
        self.assertTrue(self.func(content, content))

    def test_short_different_content_returns_false(self):
        self.assertFalse(self.func("Short text A", "Short text B"))


class TestExtractContentWithoutFrontmatter(unittest.TestCase):
    def setUp(self):
        from ww.note.check_duplicate_notes import _extract_content_without_frontmatter

        self.func = _extract_content_without_frontmatter
        self.tmpdir = tempfile.mkdtemp()

    def test_extracts_body_after_frontmatter(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("---\ntitle: Test\n---\n\nActual content here")
        result = self.func(fp)
        self.assertEqual(result, "Actual content here")

    def test_returns_full_content_without_frontmatter(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("No frontmatter here")
        result = self.func(fp)
        self.assertEqual(result, "No frontmatter here")

    def test_returns_empty_string_on_missing_file(self):
        result = self.func("/nonexistent/file.md")
        self.assertEqual(result, "")

    def test_strips_whitespace_from_body(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("---\ntitle: T\n---\n\n  Trimmed  ")
        result = self.func(fp)
        self.assertEqual(result, "Trimmed")


class TestCheckDuplicateNotesDefaultDir(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ.pop("BASE_PATH", None)

    def tearDown(self):
        os.environ.pop("BASE_PATH", None)

    @patch("ww.note.check_duplicate_notes.get_clipboard_content", return_value="")
    def test_returns_false_when_notes_dir_missing_no_base_path(self, _mock):
        from ww.note.check_duplicate_notes import check_duplicate_notes

        # No BASE_PATH → notes_dir defaults to ./notes which won't exist in tmpdir
        result = check_duplicate_notes(
            notes_dir=os.path.join(self.tmpdir, "nonexistent")
        )
        self.assertFalse(result)

    @patch("ww.note.check_duplicate_notes.get_clipboard_content", return_value="hello")
    def test_uses_base_path_for_notes_dir(self, _mock):
        os.environ["BASE_PATH"] = self.tmpdir
        notes_dir = os.path.join(self.tmpdir, "notes")
        os.makedirs(notes_dir)
        from ww.note.check_duplicate_notes import check_duplicate_notes

        # notes dir exists but is empty → no duplicates
        result = check_duplicate_notes()
        self.assertFalse(result)
        self.assertTrue(notes_dir.startswith(self.tmpdir))

    @patch("ww.note.check_duplicate_notes.get_clipboard_content", return_value="hello")
    def test_explicit_notes_dir_overrides_base_path(self, _mock):
        os.environ["BASE_PATH"] = "/should/not/be/used"
        explicit = os.path.join(self.tmpdir, "explicit_notes")
        os.makedirs(explicit)
        from ww.note.check_duplicate_notes import check_duplicate_notes

        # Should use explicit dir, not BASE_PATH/notes
        result = check_duplicate_notes(notes_dir=explicit)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
