import os
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
