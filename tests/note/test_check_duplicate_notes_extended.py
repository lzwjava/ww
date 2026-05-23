import os
import tempfile
import shutil
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestAreNotesQuickSimilarExtended(unittest.TestCase):
    """Extended tests for _are_notes_quick_similar beyond what's in the base test file."""

    def setUp(self):
        from ww.note.check_duplicate_notes import _are_notes_quick_similar

        self.func = _are_notes_quick_similar

    def test_identical_short_strings(self):
        self.assertTrue(self.func("hello world", "hello world"))

    def test_different_short_strings(self):
        self.assertFalse(self.func("hello", "world"))

    def test_identical_long_strings_with_matching_prefix(self):
        # 500+ chars, all matching
        content = "x" * 600
        self.assertTrue(self.func(content, content))

    def test_long_strings_with_minor_differences(self):
        # Nearly identical: 500+ chars with < 50 different in first 500
        base = "a" * 500
        modified = "a" * 460 + "b" * 40  # 40 diffs out of 500 → 460 matches ≥ 450
        # But lengths must also be within 5%
        self.assertTrue(self.func(base, modified))

    def test_long_strings_with_many_differences(self):
        base = "a" * 500
        modified = "a" * 400 + "b" * 100  # 400 matches < 450
        self.assertFalse(self.func(base, modified))

    def test_different_first_250_chars_returns_false(self):
        content1 = "a" * 250 + "x" * 250
        content2 = "b" * 250 + "x" * 250
        self.assertFalse(self.func(content1, content2))

    def test_length_difference_exceeds_5_percent(self):
        # Even if first 500 match, if lengths differ > 5%, should fail
        content1 = "a" * 1000
        content2 = "a" * 900  # diff = 100/1000 = 10% > 5%
        self.assertFalse(self.func(content1, content2))

    def test_length_difference_within_5_percent(self):
        content1 = "a" * 500
        content2 = "a" * 480  # diff = 20/500 = 4% ≤ 5%
        # But content2 is only 480 < 500, so first500_2 is 480 chars
        # len(first500_2) = 480 >= 250, so it enters the long path
        self.assertTrue(self.func(content1, content2))

    def test_content_with_frontmatter_like_structure(self):
        content = "---\ntitle: Test\n---\nBody content here."
        self.assertTrue(self.func(content, content))

    def test_none_like_empty(self):
        self.assertFalse(self.func("", "anything"))
        self.assertFalse(self.func("anything", ""))

    def test_whitespace_only_content(self):
        self.assertTrue(self.func("   ", "   "))
        self.assertFalse(self.func("   ", "abc"))


class TestExtractContentWithoutFrontmatterExtended(unittest.TestCase):
    """Extended tests for _extract_content_without_frontmatter."""

    def setUp(self):
        from ww.note.check_duplicate_notes import _extract_content_without_frontmatter

        self.func = _extract_content_without_frontmatter
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_file_with_full_frontmatter(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("---\ntitle: Hello\ndate: 2026-01-01\n---\n\nThe actual content.")
        result = self.func(fp)
        self.assertEqual(result, "The actual content.")

    def test_file_with_no_frontmatter(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("Just some plain text content.")
        result = self.func(fp)
        self.assertEqual(result, "Just some plain text content.")

    def test_file_with_only_one_separator(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("---\nPartial frontmatter")
        result = self.func(fp)
        # Only one ---, so sections < 3, returns full content stripped
        self.assertEqual(result, "---\nPartial frontmatter")

    def test_file_with_two_separators(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("---\ntitle: Test\n---")
        result = self.func(fp)
        # Three sections: ["", "title: Test\n", ""]
        self.assertEqual(result, "")

    def test_empty_file(self):
        fp = os.path.join(self.tmpdir, "empty.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("")
        result = self.func(fp)
        self.assertEqual(result, "")

    def test_nonexistent_file_returns_empty(self):
        result = self.func("/nonexistent/path/file.md")
        self.assertEqual(result, "")

    def test_frontmatter_with_extra_dashes_in_body(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("---\ntitle: Test\n---\nContent with --- inside.")
        result = self.func(fp)
        self.assertEqual(result, "Content with --- inside.")

    def test_utf8_content(self):
        fp = os.path.join(self.tmpdir, "note.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("---\ntitle: 测试\n---\n这是中文内容。")
        result = self.func(fp)
        self.assertEqual(result, "这是中文内容。")

    def test_multiline_frontmatter(self):
        fp = os.path.join(self.tmpdir, "note.md")
        content = "---\ntitle: Multi\nauthor: Test\ntags: [a, b]\n---\n\nLine 1\nLine 2\nLine 3"
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        result = self.func(fp)
        self.assertEqual(result, "Line 1\nLine 2\nLine 3")


if __name__ == "__main__":
    unittest.main()
