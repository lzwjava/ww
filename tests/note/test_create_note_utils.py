import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestProcessTitleForFilename(unittest.TestCase):
    def setUp(self):
        from ww.note.create_note_utils import process_title_for_filename

        self.func = process_title_for_filename

    def test_lowercases_title(self):
        self.assertEqual(self.func("Hello World"), "hello-world")

    def test_replaces_spaces_with_dashes(self):
        result = self.func("hello world test")
        self.assertNotIn(" ", result)
        self.assertIn("-", result)

    def test_removes_special_characters(self):
        result = self.func("Hello! World?")
        self.assertNotIn("!", result)
        self.assertNotIn("?", result)

    def test_strips_leading_trailing_whitespace(self):
        result = self.func("  hello  ")
        self.assertEqual(result, "hello")

    def test_collapses_multiple_spaces(self):
        result = self.func("a  b")
        self.assertEqual(result, "a-b")


class TestCleanGrokTags(unittest.TestCase):
    def test_passthrough_when_no_grok_tags(self):
        from ww.note.create_note_utils import clean_grok_tags

        content = "Normal content without grok tags"
        result = clean_grok_tags(content)
        self.assertEqual(result, content)

    @patch(
        "ww.note.create_note_utils.call_openrouter_api",
        return_value="Cleaned content",
    )
    def test_calls_api_when_grok_tags_present(self, mock_api):
        from ww.note.create_note_utils import clean_grok_tags

        content = 'Text <grok:render type="markdown">data</grok:render> more'
        result = clean_grok_tags(content)
        self.assertEqual(result, "Cleaned content")
        mock_api.assert_called_once()

    @patch("ww.note.create_note_utils.call_openrouter_api", return_value=None)
    def test_returns_original_when_api_fails(self, mock_api):
        from ww.note.create_note_utils import clean_grok_tags

        content = 'Text <grok:render type="markdown">data</grok:render> more'
        result = clean_grok_tags(content)
        self.assertEqual(result, content)


class TestGetBasePath(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("BASE_PATH", None)

    def test_returns_dot_when_unset(self):
        os.environ.pop("BASE_PATH", None)
        from ww.note.create_note_utils import get_base_path

        self.assertEqual(get_base_path(), ".")

    def test_returns_dot_when_empty(self):
        os.environ["BASE_PATH"] = ""
        from ww.note.create_note_utils import get_base_path

        self.assertEqual(get_base_path(), ".")

    def test_returns_dot_when_explicit_dot(self):
        os.environ["BASE_PATH"] = "."
        from ww.note.create_note_utils import get_base_path

        self.assertEqual(get_base_path(), ".")

    def test_returns_absolute_path(self):
        os.environ["BASE_PATH"] = "/some/project"
        from ww.note.create_note_utils import get_base_path

        self.assertEqual(get_base_path(), "/some/project")

    def test_strips_whitespace(self):
        os.environ["BASE_PATH"] = "  /some/project  "
        from ww.note.create_note_utils import get_base_path

        self.assertEqual(get_base_path(), "/some/project")


class TestCreateFilename(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ.pop("BASE_PATH", None)

    def tearDown(self):
        os.environ.pop("BASE_PATH", None)

    def test_creates_filename_with_given_date(self):
        from ww.note.create_note_utils import create_filename

        fp = create_filename("my-title", notes_dir=self.tmpdir, date="2024-01-01")
        self.assertIn("2024-01-01", fp)
        self.assertIn("my-title", fp)
        self.assertTrue(fp.endswith(".md"))

    def test_appends_counter_when_file_exists(self):
        from ww.note.create_note_utils import create_filename

        fp1 = create_filename("my-title", notes_dir=self.tmpdir, date="2024-01-01")
        with open(fp1, "w") as f:
            f.write("content")
        fp2 = create_filename("my-title", notes_dir=self.tmpdir, date="2024-01-01")
        self.assertNotEqual(fp1, fp2)
        self.assertIn("-1-", fp2)

    def test_creates_notes_dir_if_missing(self):
        from ww.note.create_note_utils import create_filename

        new_dir = os.path.join(self.tmpdir, "new_notes")
        create_filename("title", notes_dir=new_dir, date="2024-01-01")
        self.assertTrue(os.path.exists(new_dir))

    def test_uses_today_date_when_not_specified(self):
        import datetime
        from ww.note.create_note_utils import create_filename

        fp = create_filename("title", notes_dir=self.tmpdir)
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.assertIn(today, fp)

    def test_default_notes_dir_uses_base_path(self):
        os.environ["BASE_PATH"] = self.tmpdir
        from ww.note.create_note_utils import create_filename

        fp = create_filename("title", date="2024-01-01")
        self.assertTrue(fp.startswith(self.tmpdir))
        self.assertIn("notes", fp)

    def test_explicit_notes_dir_overrides_base_path(self):
        os.environ["BASE_PATH"] = "/should/not/be/used"
        explicit = os.path.join(self.tmpdir, "explicit")
        from ww.note.create_note_utils import create_filename

        fp = create_filename("title", notes_dir=explicit, date="2024-01-01")
        self.assertTrue(fp.startswith(explicit))


class TestFormatFrontMatter(unittest.TestCase):
    def setUp(self):
        from ww.note.create_note_utils import format_front_matter

        self.func = format_front_matter

    def test_contains_title(self):
        result = self.func("My Title", date="2024-01-01")
        self.assertIn("title: My Title", result)

    def test_starts_and_ends_with_dashes(self):
        result = self.func("Title", date="2024-01-01")
        self.assertTrue(result.startswith("---"))
        self.assertTrue(result.endswith("---"))

    def test_title_with_colon_gets_quoted(self):
        result = self.func("Title: With Colon", date="2024-01-01")
        self.assertIn('"Title: With Colon"', result)

    def test_title_already_quoted_not_double_quoted(self):
        result = self.func('"Already: Quoted"', date="2024-01-01")
        self.assertNotIn('""', result)


class TestCleanContent(unittest.TestCase):
    def setUp(self):
        from ww.note.create_note_utils import clean_content

        self.func = clean_content

    def test_removes_h1_heading(self):
        result = self.func("# My Title\n\nActual content here")
        self.assertNotIn("# My Title", result)
        self.assertIn("Actual content here", result)

    def test_removes_leading_separator_line(self):
        result = self.func("---\n\nActual content here")
        self.assertNotIn("---", result)
        self.assertIn("Actual content here", result)

    def test_strips_outer_whitespace(self):
        result = self.func("\n\n  Some content  \n\n")
        self.assertEqual(result, result.strip())

    def test_plain_content_unchanged(self):
        result = self.func("Normal content without heading")
        self.assertEqual(result, "Normal content without heading")

    def test_removes_multiple_leading_separators(self):
        result = self.func("---\n\n---\n\nContent")
        self.assertNotIn("---", result)
        self.assertIn("Content", result)


if __name__ == "__main__":
    unittest.main()
