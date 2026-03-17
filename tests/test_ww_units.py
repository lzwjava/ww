import os

# Must be set before any ww imports that pull in openrouter_client
os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch


# ===========================================================================
# ww/content/fix_mathjax.py
# ===========================================================================


class TestFixMathjaxInFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _make_file(self, content, name="test.md"):
        fp = os.path.join(self.tmpdir, name)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        return fp

    def test_replaces_backslash_paren(self):
        from ww.content.fix_mathjax import fix_mathjax_in_file

        fp = self._make_file(r"Here is math \(x+y\) done.")
        result = fix_mathjax_in_file(fp)
        self.assertTrue(result)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(r"\\(", content)
        self.assertIn(r"\\)", content)

    def test_skips_already_fixed_file(self):
        from ww.content.fix_mathjax import fix_mathjax_in_file

        fp = self._make_file(r"Here is math \\(x+y\\) done.")
        result = fix_mathjax_in_file(fp)
        self.assertFalse(result)

    def test_no_replacements_needed(self):
        from ww.content.fix_mathjax import fix_mathjax_in_file

        fp = self._make_file("No math here, just plain text.")
        result = fix_mathjax_in_file(fp)
        self.assertFalse(result)

    def test_reset_mode_reverses_replacements(self):
        from ww.content.fix_mathjax import fix_mathjax_in_file

        fp = self._make_file(r"Here is math \\(x+y\\) done.")
        result = fix_mathjax_in_file(fp, reset=True)
        self.assertTrue(result)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(r"\(", content)
        self.assertNotIn(r"\\(", content)

    def test_nonexistent_file_returns_false(self):
        from ww.content.fix_mathjax import fix_mathjax_in_file

        result = fix_mathjax_in_file("/nonexistent/path/file.md")
        self.assertFalse(result)

    def test_gemini_mode_replaces_dollar_sign(self):
        from ww.content.fix_mathjax import fix_mathjax_in_file

        fp = self._make_file("Math: $x+y$ end.")
        fix_mathjax_in_file(fp, gemini=True)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(r"\\(", content)

    def test_replaces_backslash_bracket(self):
        from ww.content.fix_mathjax import fix_mathjax_in_file

        fp = self._make_file(r"Display math: \[x+y\]")
        result = fix_mathjax_in_file(fp)
        self.assertTrue(result)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(r"\\[", content)


class TestFixMathjaxInMarkdown(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_processes_md_files_in_directory(self):
        from ww.content.fix_mathjax import fix_mathjax_in_markdown

        fp = os.path.join(self.tmpdir, "test.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(r"Math: \(x\)")
        fix_mathjax_in_markdown(self.tmpdir)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(r"\\(", content)

    def test_skips_non_md_files(self):
        from ww.content.fix_mathjax import fix_mathjax_in_markdown

        fp = os.path.join(self.tmpdir, "test.txt")
        original = r"Math: \(x\)"
        with open(fp, "w", encoding="utf-8") as f:
            f.write(original)
        fix_mathjax_in_markdown(self.tmpdir)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, original)

    def test_max_files_stops_early(self):
        from ww.content.fix_mathjax import fix_mathjax_in_markdown

        for i in range(3):
            fp = os.path.join(self.tmpdir, f"test{i}.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(r"Math: \(x\)")
        # max_files=1 should process only 1 file and stop
        fix_mathjax_in_markdown(self.tmpdir, max_files=1)


# ===========================================================================
# ww/content/fix_table.py
# ===========================================================================


class TestProcessTablesInFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _make_file(self, content):
        fp = os.path.join(self.tmpdir, "test.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        return fp

    def test_returns_true_on_success(self):
        from ww.content.fix_table import process_tables_in_file

        fp = self._make_file("## Heading\n|col1|col2|\n|---|---|\n|a|b|\n")
        result = process_tables_in_file(fp)
        self.assertTrue(result)

    def test_fix_tables_adds_blank_line_between_heading_and_table(self):
        from ww.content.fix_table import process_tables_in_file

        fp = self._make_file("## Heading\n|col1|col2|\n|---|---|\n|a|b|\n")
        process_tables_in_file(fp, fix_tables=True)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("\n\n|", content)

    def test_nonexistent_file_returns_false(self):
        from ww.content.fix_table import process_tables_in_file

        result = process_tables_in_file("/nonexistent/file.md")
        self.assertFalse(result)

    def test_file_with_no_tables_still_succeeds(self):
        from ww.content.fix_table import process_tables_in_file

        fp = self._make_file("# Just a heading\n\nSome plain text.\n")
        result = process_tables_in_file(fp)
        self.assertTrue(result)


class TestProcessTablesInMarkdown(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_processes_all_md_files(self):
        from ww.content.fix_table import process_tables_in_markdown

        fp = os.path.join(self.tmpdir, "test.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("## H\n|a|b|\n|---|---|\n")
        process_tables_in_markdown(self.tmpdir)
        with open(fp, "r", encoding="utf-8") as f:
            f.read()  # no crash

    def test_max_files_limit_respected(self):
        from ww.content.fix_table import process_tables_in_markdown

        for i in range(3):
            fp = os.path.join(self.tmpdir, f"f{i}.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write("## H\n|a|b|\n|---|---|\n")
        process_tables_in_markdown(self.tmpdir, max_files=1)


# ===========================================================================
# ww/create/check_duplicate_notes.py
# ===========================================================================


class TestAreNotesQuickSimilar(unittest.TestCase):
    def setUp(self):
        from ww.create.check_duplicate_notes import _are_notes_quick_similar

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
        from ww.create.check_duplicate_notes import _extract_content_without_frontmatter

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


# ===========================================================================
# ww/create/create_note_utils.py
# ===========================================================================


class TestProcessTitleForFilename(unittest.TestCase):
    def setUp(self):
        from ww.create.create_note_utils import process_title_for_filename

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
        from ww.create.create_note_utils import clean_grok_tags

        content = "Normal content without grok tags"
        result = clean_grok_tags(content)
        self.assertEqual(result, content)

    @patch(
        "ww.create.create_note_utils.call_openrouter_api",
        return_value="Cleaned content",
    )
    def test_calls_api_when_grok_tags_present(self, mock_api):
        from ww.create.create_note_utils import clean_grok_tags

        content = 'Text <grok:render type="markdown">data</grok:render> more'
        result = clean_grok_tags(content)
        self.assertEqual(result, "Cleaned content")
        mock_api.assert_called_once()

    @patch("ww.create.create_note_utils.call_openrouter_api", return_value=None)
    def test_returns_original_when_api_fails(self, mock_api):
        from ww.create.create_note_utils import clean_grok_tags

        content = 'Text <grok:render type="markdown">data</grok:render> more'
        result = clean_grok_tags(content)
        self.assertEqual(result, content)


class TestCreateFilename(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_creates_filename_with_given_date(self):
        from ww.create.create_note_utils import create_filename

        fp = create_filename("my-title", notes_dir=self.tmpdir, date="2024-01-01")
        self.assertIn("2024-01-01", fp)
        self.assertIn("my-title", fp)
        self.assertTrue(fp.endswith(".md"))

    def test_appends_counter_when_file_exists(self):
        from ww.create.create_note_utils import create_filename

        fp1 = create_filename("my-title", notes_dir=self.tmpdir, date="2024-01-01")
        with open(fp1, "w") as f:
            f.write("content")
        fp2 = create_filename("my-title", notes_dir=self.tmpdir, date="2024-01-01")
        self.assertNotEqual(fp1, fp2)
        self.assertIn("-1-", fp2)

    def test_creates_notes_dir_if_missing(self):
        from ww.create.create_note_utils import create_filename

        new_dir = os.path.join(self.tmpdir, "new_notes")
        create_filename("title", notes_dir=new_dir, date="2024-01-01")
        self.assertTrue(os.path.exists(new_dir))

    def test_uses_today_date_when_not_specified(self):
        import datetime
        from ww.create.create_note_utils import create_filename

        fp = create_filename("title", notes_dir=self.tmpdir)
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.assertIn(today, fp)


class TestFormatFrontMatter(unittest.TestCase):
    def setUp(self):
        from ww.create.create_note_utils import format_front_matter

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
        from ww.create.create_note_utils import clean_content

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


# ===========================================================================
# ww/git/git_classify_commit.py
# ===========================================================================


class TestClassifyCommit(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_classifies_python_file_as_code(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "src/main.py\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "code")

    @patch("subprocess.check_output")
    def test_classifies_markdown_file_as_md(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "README.md\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "md")

    @patch("subprocess.check_output")
    def test_classifies_yaml_as_others(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "config.yaml\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "others")

    @patch("subprocess.check_output")
    def test_returns_none_on_empty_output(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "\n"
        self.assertIsNone(classify_commit("/repo", "abc123"))

    @patch("subprocess.check_output")
    def test_raises_runtime_error_on_subprocess_failure(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.side_effect = subprocess.CalledProcessError(1, "git")
        with self.assertRaises(RuntimeError):
            classify_commit("/repo", "abc123")

    @patch("subprocess.check_output")
    def test_majority_type_wins(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "a.py\nb.py\nc.md\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "code")

    @patch("subprocess.check_output")
    def test_java_file_classified_as_code(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "Main.java\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "code")

    @patch("subprocess.check_output")
    def test_javascript_file_classified_as_code(self, mock_out):
        from ww.git.git_classify_commit import classify_commit

        mock_out.return_value = "app.js\n"
        self.assertEqual(classify_commit("/repo", "abc123"), "code")


# ===========================================================================
# ww/git/git_diff_tree.py
# ===========================================================================


class TestListFilesExcludingExt(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_excludes_specified_extension(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.return_value = "a.py\nb.js\nc.md\n"
        result = list_files_excluding_ext("/repo", "abc123", "py")
        self.assertNotIn("a.py", result)
        self.assertIn("b.js", result)
        self.assertIn("c.md", result)

    @patch("subprocess.check_output")
    def test_handles_leading_dot_in_extension(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.return_value = "a.py\nb.js\n"
        result = list_files_excluding_ext("/repo", "abc123", ".py")
        self.assertNotIn("a.py", result)
        self.assertIn("b.js", result)

    @patch("subprocess.check_output")
    def test_raises_runtime_error_on_failure(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.side_effect = subprocess.CalledProcessError(1, "git")
        with self.assertRaises(RuntimeError):
            list_files_excluding_ext("/repo", "abc123", "py")

    @patch("subprocess.check_output")
    def test_case_insensitive_extension_matching(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.return_value = "a.PY\nb.js\n"
        result = list_files_excluding_ext("/repo", "abc123", "py")
        self.assertNotIn("a.PY", result)
        self.assertIn("b.js", result)

    @patch("subprocess.check_output")
    def test_returns_empty_list_when_all_excluded(self, mock_out):
        from ww.git.git_diff_tree import list_files_excluding_ext

        mock_out.return_value = "a.py\nb.py\n"
        result = list_files_excluding_ext("/repo", "abc123", "py")
        self.assertEqual(result, [])


# ===========================================================================
# ww/git/git_delete_commit.py
# ===========================================================================


class TestGetCommitsWithDeletions(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_list_of_hashes(self, mock_run):
        from ww.git.git_delete_commit import get_commits_with_deletions

        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\ndef456\n")
        result = get_commits_with_deletions(5)
        self.assertEqual(result, ["abc123", "def456"])

    @patch("subprocess.run")
    def test_returns_empty_list_on_git_error(self, mock_run):
        from ww.git.git_delete_commit import get_commits_with_deletions

        mock_run.return_value = MagicMock(returncode=1, stderr="error", stdout="")
        result = get_commits_with_deletions(5)
        self.assertEqual(result, [])

    @patch("subprocess.run")
    def test_filters_empty_lines(self, mock_run):
        from ww.git.git_delete_commit import get_commits_with_deletions

        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n\ndef456\n")
        result = get_commits_with_deletions(5)
        self.assertEqual(result, ["abc123", "def456"])

    @patch("subprocess.run", side_effect=Exception("git not found"))
    def test_returns_empty_on_exception(self, mock_run):
        from ww.git.git_delete_commit import get_commits_with_deletions

        result = get_commits_with_deletions(5)
        self.assertEqual(result, [])


class TestGetChangedFilesCount(unittest.TestCase):
    @patch("subprocess.run")
    def test_parses_multiple_files_changed(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="commit abc123\n\n 3 files changed, 10 insertions(+)\n",
        )
        self.assertEqual(get_changed_files_count("abc123"), 3)

    @patch("subprocess.run")
    def test_parses_single_file_changed(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=" 1 files changed, 5 insertions(+)\n",
        )
        self.assertEqual(get_changed_files_count("abc123"), 1)

    @patch("subprocess.run")
    def test_returns_zero_on_nonzero_returncode(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertEqual(get_changed_files_count("abc123"), 0)

    @patch("subprocess.run")
    def test_returns_zero_when_no_match_in_output(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        mock_run.return_value = MagicMock(returncode=0, stdout="commit abc123\n\n")
        self.assertEqual(get_changed_files_count("abc123"), 0)

    @patch("subprocess.run", side_effect=Exception("fail"))
    def test_returns_zero_on_exception(self, mock_run):
        from ww.git.git_delete_commit import get_changed_files_count

        self.assertEqual(get_changed_files_count("abc123"), 0)


# ===========================================================================
# ww/git/git_filename.py
# ===========================================================================


class TestCheckGitFilenames(unittest.TestCase):
    @patch("subprocess.run")
    def test_valid_filenames_returns_true(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(
            returncode=0, stdout="src/main.py\nREADME.md\n"
        )
        self.assertTrue(check_git_filenames())

    @patch("subprocess.run")
    def test_filename_with_spaces_returns_false(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(
            returncode=0, stdout="src/file with spaces.py\n"
        )
        self.assertFalse(check_git_filenames())

    @patch("subprocess.run")
    def test_markdown_with_hyphens_is_valid(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(
            returncode=0, stdout="notes/2024-01-01-hello-world.md\n"
        )
        self.assertTrue(check_git_filenames())

    @patch("subprocess.run")
    def test_special_chars_in_non_md_returns_false(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(returncode=0, stdout="src/café.py\n")
        self.assertFalse(check_git_filenames())

    @patch("subprocess.run")
    def test_subprocess_error_returns_false(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        self.assertFalse(check_git_filenames())

    @patch("subprocess.run")
    def test_empty_file_list_returns_true(self, mock_run):
        from ww.git.git_filename import check_git_filenames

        mock_run.return_value = MagicMock(returncode=0, stdout="")
        self.assertTrue(check_git_filenames())


# ===========================================================================
# ww/git/git_show_command.py
# ===========================================================================


class TestFormatFileList(unittest.TestCase):
    def setUp(self):
        from ww.git.git_show_command import format_file_list

        self.func = format_file_list

    def test_returns_none_for_empty_list(self):
        result = self.func([], "Files")
        self.assertIn("None", result)
        self.assertIn("Files", result)

    def test_numbers_files_sequentially(self):
        result = self.func(["a.py", "b.py"], "Files")
        self.assertIn("1.", result)
        self.assertIn("2.", result)

    def test_includes_filenames(self):
        result = self.func(["a.py", "b.md"], "Changed")
        self.assertIn("a.py", result)
        self.assertIn("b.md", result)

    def test_includes_title(self):
        result = self.func(["a.py"], "Python files")
        self.assertIn("Python files", result)


class TestGetLastCommitInfo(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_returns_dict_with_expected_keys(self, mock_out):
        from ww.git.git_show_command import get_last_commit_info

        mock_out.side_effect = [
            "abc123def456 feat: add feature",
            "\na.py\nb.md\n",
        ]
        result = get_last_commit_info()
        self.assertIsNotNone(result)
        self.assertIn("hash", result)
        self.assertIn("message", result)
        self.assertIn("python_files", result)
        self.assertIn("all_files", result)

    @patch("subprocess.check_output")
    def test_truncates_hash_to_8_chars(self, mock_out):
        from ww.git.git_show_command import get_last_commit_info

        mock_out.side_effect = [
            "abc123def456 feat: add feature",
            "\na.py\n",
        ]
        result = get_last_commit_info()
        self.assertEqual(len(result["hash"]), 8)
        self.assertEqual(result["hash"], "abc123de")

    @patch("subprocess.check_output")
    def test_filters_python_files_correctly(self, mock_out):
        from ww.git.git_show_command import get_last_commit_info

        mock_out.side_effect = [
            "abc123def456 chore: update",
            "\na.py\nb.md\nc.js\n",
        ]
        result = get_last_commit_info()
        self.assertIn("a.py", result["python_files"])
        self.assertNotIn("b.md", result["python_files"])
        self.assertNotIn("c.js", result["python_files"])

    @patch(
        "subprocess.check_output",
        side_effect=subprocess.CalledProcessError(1, "git"),
    )
    def test_returns_none_on_subprocess_error(self, mock_out):
        from ww.git.git_show_command import get_last_commit_info

        result = get_last_commit_info()
        self.assertIsNone(result)


# ===========================================================================
# ww/git/git_squash.py
# ===========================================================================


class TestGenerateSquashMessage(unittest.TestCase):
    @patch("ww.git.git_squash.call_openrouter_api", return_value="feat: squash commits")
    def test_generates_message_via_api(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: add feature\npick def456 fix: fix bug\n"
        result = generate_squash_message(rebase_todo)
        self.assertEqual(result, "feat: squash commits")
        mock_api.assert_called_once()

    @patch(
        "ww.git.git_squash.call_openrouter_api",
        side_effect=Exception("API error"),
    )
    def test_falls_back_when_api_raises(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: add feature\npick def456 fix: fix bug\n"
        result = generate_squash_message(rebase_todo)
        # Fallback joins parts[2] tokens from each pick line
        self.assertIsNotNone(result)
        self.assertIn("+", result)

    @patch("ww.git.git_squash.call_openrouter_api", return_value="chore: empty")
    def test_empty_todo_still_calls_api(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        result = generate_squash_message("")
        self.assertEqual(result, "chore: empty")

    @patch("ww.git.git_squash.call_openrouter_api", return_value="fix: squash")
    def test_squash_lines_also_included(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: first\nsquash def456 fix: second\n"
        result = generate_squash_message(rebase_todo)
        self.assertEqual(result, "fix: squash")


# ===========================================================================
# ww/git/git_amend_push.py
# ===========================================================================


class TestRunCommand(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_subprocess_result(self, mock_run):
        from ww.git.git_amend_push import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        result = run_command(["git", "status"])
        self.assertIsNotNone(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_uses_provided_repo_path_as_cwd(self, mock_run):
        from ww.git.git_amend_push import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_command(["git", "status"], repo_path=Path("/tmp"))
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["cwd"], "/tmp")

    @patch("subprocess.run")
    def test_passes_check_flag(self, mock_run):
        from ww.git.git_amend_push import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_command(["git", "status"], check=False)
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["check"], False)


# ===========================================================================
# ww/image/image_compress.py
# ===========================================================================


class TestCompressImage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_compresses_rgb_image_and_saves_file(self):
        import numpy as np
        from PIL import Image

        from ww.image.image_compress import compress_image

        img_array = np.random.randint(0, 256, (20, 20, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = os.path.join(self.tmpdir, "test.png")
        img.save(img_path)

        output_path = compress_image(img_path, compression_factor=0.5)
        self.assertTrue(os.path.exists(output_path))
        self.assertIn("_compressed", output_path)

    def test_compresses_grayscale_image(self):
        import numpy as np
        from PIL import Image

        from ww.image.image_compress import compress_image

        img_array = np.random.randint(0, 256, (20, 20), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = os.path.join(self.tmpdir, "gray.png")
        img.save(img_path)

        output_path = compress_image(img_path, compression_factor=0.5)
        self.assertTrue(os.path.exists(output_path))

    def test_output_path_naming_convention(self):
        import numpy as np
        from PIL import Image

        from ww.image.image_compress import compress_image

        img_array = np.ones((10, 10, 3), dtype=np.uint8) * 128
        img = Image.fromarray(img_array)
        img_path = os.path.join(self.tmpdir, "original.jpg")
        img.save(img_path)

        output_path = compress_image(img_path, compression_factor=0.3)
        self.assertEqual(
            output_path, os.path.join(self.tmpdir, "original_compressed.jpg")
        )

    def test_output_image_is_valid(self):
        import numpy as np
        from PIL import Image

        from ww.image.image_compress import compress_image

        img_array = np.ones((10, 10, 3), dtype=np.uint8) * 200
        img = Image.fromarray(img_array)
        img_path = os.path.join(self.tmpdir, "solid.png")
        img.save(img_path)

        output_path = compress_image(img_path, compression_factor=1.0)
        out_img = Image.open(output_path)
        self.assertIsNotNone(out_img)


# ===========================================================================
# ww/image/remove_bg.py
# ===========================================================================


class TestDetectBackgroundColor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _solid_image(self, color):
        import numpy as np
        from PIL import Image

        img_array = np.full((100, 100, 3), color, dtype=np.uint8)
        img = Image.fromarray(img_array, "RGB")
        fp = os.path.join(self.tmpdir, "img.png")
        img.save(fp)
        return fp

    def test_detects_white_background(self):
        from ww.image.remove_bg import detect_background_color

        fp = self._solid_image((255, 255, 255))
        result = detect_background_color(fp)
        self.assertEqual(result, (255, 255, 255))

    def test_detects_black_background(self):
        from ww.image.remove_bg import detect_background_color

        fp = self._solid_image((0, 0, 0))
        result = detect_background_color(fp)
        self.assertEqual(result, (0, 0, 0))

    def test_detects_custom_color(self):
        from ww.image.remove_bg import detect_background_color

        fp = self._solid_image((100, 150, 200))
        result = detect_background_color(fp)
        self.assertEqual(result, (100, 150, 200))

    def test_returns_tuple_of_three(self):
        from ww.image.remove_bg import detect_background_color

        fp = self._solid_image((50, 100, 150))
        result = detect_background_color(fp)
        self.assertEqual(len(result), 3)


class TestRemoveWhiteBackground(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_white_pixels_become_transparent(self):
        import numpy as np
        from PIL import Image

        from ww.image.remove_bg import remove_white_background

        img_array = np.full((10, 10, 4), (255, 255, 255, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "input.png")
        img.save(fp)

        out_fp = os.path.join(self.tmpdir, "output.png")
        remove_white_background(fp, out_fp, tolerance=10)

        out_array = np.array(Image.open(out_fp).convert("RGBA"))
        self.assertEqual(out_array[0, 0, 3], 0)

    def test_non_white_pixels_remain_opaque(self):
        import numpy as np
        from PIL import Image

        from ww.image.remove_bg import remove_white_background

        img_array = np.full((10, 10, 4), (0, 0, 0, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "black.png")
        img.save(fp)

        out_fp = os.path.join(self.tmpdir, "black_out.png")
        remove_white_background(fp, out_fp, tolerance=10)

        out_array = np.array(Image.open(out_fp).convert("RGBA"))
        self.assertEqual(out_array[0, 0, 3], 255)

    def test_output_file_is_created(self):
        import numpy as np
        from PIL import Image

        from ww.image.remove_bg import remove_white_background

        img_array = np.full((5, 5, 4), (200, 200, 200, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "in.png")
        img.save(fp)
        out_fp = os.path.join(self.tmpdir, "out.png")
        remove_white_background(fp, out_fp)
        self.assertTrue(os.path.exists(out_fp))


class TestRemoveColorBackground(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_matching_pixels_become_transparent(self):
        import numpy as np
        from PIL import Image

        from ww.image.remove_bg import remove_color_background

        img_array = np.full((10, 10, 4), (100, 150, 200, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "in.png")
        img.save(fp)

        out_fp = os.path.join(self.tmpdir, "out.png")
        remove_color_background(fp, out_fp, bg_color=(100, 150, 200), tolerance=10)

        out_array = np.array(Image.open(out_fp).convert("RGBA"))
        self.assertEqual(out_array[0, 0, 3], 0)

    def test_non_matching_pixels_stay_opaque(self):
        import numpy as np
        from PIL import Image

        from ww.image.remove_bg import remove_color_background

        img_array = np.full((10, 10, 4), (255, 0, 0, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "in.png")
        img.save(fp)

        out_fp = os.path.join(self.tmpdir, "out.png")
        remove_color_background(fp, out_fp, bg_color=(0, 255, 0), tolerance=10)

        out_array = np.array(Image.open(out_fp).convert("RGBA"))
        self.assertEqual(out_array[0, 0, 3], 255)


# ===========================================================================
# ww/github/readme.py
# ===========================================================================


class TestGetRealtimeCommitCount(unittest.TestCase):
    @patch("ww.github.readme.requests.get")
    def test_returns_count_from_link_header(self, mock_get):
        from ww.github.readme import get_realtime_commit_count

        mock_response = MagicMock()
        mock_response.headers = {
            "link": '<https://api.github.com/repos/u/r/commits?page=42>; rel="last"'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        self.assertEqual(get_realtime_commit_count("user", "repo"), 42)

    @patch("ww.github.readme.requests.get")
    def test_returns_1_when_no_link_header_and_commits_present(self, mock_get):
        from ww.github.readme import get_realtime_commit_count

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.json.return_value = [{"sha": "abc"}]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        self.assertEqual(get_realtime_commit_count("user", "repo"), 1)

    @patch("ww.github.readme.requests.get")
    def test_returns_0_on_http_error(self, mock_get):
        import requests

        from ww.github.readme import get_realtime_commit_count

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not Found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response
        self.assertEqual(get_realtime_commit_count("user", "nonexistent"), 0)

    @patch("ww.github.readme.requests.get", side_effect=Exception("connection error"))
    def test_returns_0_on_general_exception(self, mock_get):
        from ww.github.readme import get_realtime_commit_count

        self.assertEqual(get_realtime_commit_count("user", "repo"), 0)

    @patch("ww.github.readme.requests.get")
    def test_sets_authorization_header_when_token_provided(self, mock_get):
        from ww.github.readme import get_realtime_commit_count

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        get_realtime_commit_count("user", "repo", github_token="mytoken")
        _, kwargs = mock_get.call_args
        self.assertIn("Authorization", kwargs["headers"])
        self.assertIn("mytoken", kwargs["headers"]["Authorization"])


class TestFormatProjectsToMarkdown(unittest.TestCase):
    @patch("ww.github.readme.get_realtime_commit_count", return_value=100)
    def test_formats_table_with_pipe_separators(self, mock_count):
        from ww.github.readme import format_projects_to_markdown

        projects = [
            {
                "project": "my-repo",
                "url": "https://github.com/u/my-repo",
                "language": "Python",
            }
        ]
        result = format_projects_to_markdown(projects, "user")
        self.assertIn("|", result)
        self.assertIn("my-repo", result)
        self.assertIn("Python", result)
        self.assertIn("100", result)

    def test_returns_message_for_empty_list(self):
        from ww.github.readme import format_projects_to_markdown

        result = format_projects_to_markdown([], "user")
        self.assertIn("No project data", result)

    @patch("ww.github.readme.get_realtime_commit_count", return_value=0)
    def test_includes_header_row(self, mock_count):
        from ww.github.readme import format_projects_to_markdown

        projects = [{"project": "r", "url": "https://github.com/u/r", "language": "Go"}]
        result = format_projects_to_markdown(projects, "user")
        self.assertIn("project", result)
        self.assertIn("language", result)
        self.assertIn("commits", result)


# ===========================================================================
# ww/github/gitmessageai.py  (standalone call_openrouter_api)
# ===========================================================================


class TestGitmessageaiCallOpenrouterApi(unittest.TestCase):
    def setUp(self):
        from ww.github import gitmessageai

        self._orig_key = gitmessageai.OPENROUTER_API_KEY
        gitmessageai.OPENROUTER_API_KEY = "test-key"

    def tearDown(self):
        from ww.github import gitmessageai

        gitmessageai.OPENROUTER_API_KEY = self._orig_key

    @patch("ww.github.gitmessageai.requests.post")
    def test_returns_content_on_200(self, mock_post):
        from ww.github.gitmessageai import call_openrouter_api

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "feat: add feature"}}]},
        )
        result = call_openrouter_api("Generate commit message")
        self.assertEqual(result, "feat: add feature")

    def test_returns_none_when_api_key_missing(self):
        from ww.github import gitmessageai

        gitmessageai.OPENROUTER_API_KEY = None
        result = gitmessageai.call_openrouter_api("prompt")
        self.assertIsNone(result)

    def test_returns_none_for_unknown_model(self):
        from ww.github.gitmessageai import call_openrouter_api

        result = call_openrouter_api("prompt", model="nonexistent-model")
        self.assertIsNone(result)

    @patch("ww.github.gitmessageai.requests.post")
    def test_returns_none_on_non_200_status(self, mock_post):
        from ww.github.gitmessageai import call_openrouter_api

        mock_post.return_value = MagicMock(status_code=401, text="Unauthorized")
        result = call_openrouter_api("prompt")
        self.assertIsNone(result)

    @patch("ww.github.gitmessageai.requests.post", side_effect=Exception("timeout"))
    def test_returns_none_on_request_exception(self, mock_post):
        from ww.github.gitmessageai import call_openrouter_api

        result = call_openrouter_api("prompt")
        self.assertIsNone(result)

    @patch("ww.github.gitmessageai.requests.post")
    def test_returns_none_on_invalid_response_format(self, mock_post):
        from ww.github.gitmessageai import call_openrouter_api

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": []},
        )
        result = call_openrouter_api("prompt")
        self.assertIsNone(result)


# ===========================================================================
# ww/llm/openrouter_client.py
# ===========================================================================


class TestCallOpenrouterApiWithMessages(unittest.TestCase):
    @patch("ww.llm.openrouter_client.requests.post")
    def test_returns_content_on_success(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "response text"}}]},
        )
        messages = [{"role": "user", "content": "hello"}]
        result = openrouter_client.call_openrouter_api_with_messages(
            messages, model="mistral"
        )
        self.assertEqual(result, "response text")

    def test_raises_on_unknown_model(self):
        from ww.llm import openrouter_client

        messages = [{"role": "user", "content": "hello"}]
        with self.assertRaises(Exception) as ctx:
            openrouter_client.call_openrouter_api_with_messages(
                messages, model="unknown-xyz"
            )
        self.assertIn("unknown-xyz", str(ctx.exception))

    @patch("ww.llm.openrouter_client.requests.post")
    def test_raises_on_non_200_response(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(status_code=401, text="Unauthorized")
        messages = [{"role": "user", "content": "hello"}]
        with self.assertRaises(Exception):
            openrouter_client.call_openrouter_api_with_messages(
                messages, model="mistral"
            )

    @patch("ww.llm.openrouter_client.requests.post")
    def test_uses_default_max_tokens_when_not_specified(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
        )
        messages = [{"role": "user", "content": "test"}]
        openrouter_client.call_openrouter_api_with_messages(messages, model="mistral")
        _, kwargs = mock_post.call_args
        self.assertEqual(
            kwargs["json"]["max_tokens"],
            openrouter_client.DEFAULT_TOKENS["mistral"],
        )

    @patch("ww.llm.openrouter_client.requests.post")
    def test_respects_custom_max_tokens(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "ok"}}]},
        )
        messages = [{"role": "user", "content": "test"}]
        openrouter_client.call_openrouter_api_with_messages(
            messages, model="mistral", max_tokens=1234
        )
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["max_tokens"], 1234)

    @patch("ww.llm.openrouter_client.requests.post")
    def test_call_openrouter_api_wraps_with_messages(self, mock_post):
        from ww.llm import openrouter_client

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "wrapped"}}]},
        )
        result = openrouter_client.call_openrouter_api("test prompt", model="mistral")
        self.assertEqual(result, "wrapped")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["messages"][0]["role"], "user")
        self.assertEqual(kwargs["json"]["messages"][0]["content"], "test prompt")


# ===========================================================================
# ww/utils/clean_zip.py
# ===========================================================================


class TestCleanZip(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _make_zip(self, files):
        zip_path = os.path.join(self.tmpdir, "input.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return zip_path

    def test_removes_files_without_extensions(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"valid.txt": "hello", "no_extension": "world"})
        clean_zip(zip_path)
        out_path = os.path.join(self.tmpdir, "input_output.zip")
        self.assertTrue(os.path.exists(out_path))
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("valid.txt", names)
        self.assertNotIn("no_extension", names)

    def test_keeps_directories(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"dir/": "", "dir/file.txt": "content"})
        clean_zip(zip_path)
        out_path = os.path.join(self.tmpdir, "input_output.zip")
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("dir/", names)
        self.assertIn("dir/file.txt", names)

    def test_does_not_create_output_when_no_valid_files(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"noext1": "a", "noext2": "b"})
        clean_zip(zip_path)
        out_path = os.path.join(self.tmpdir, "input_output.zip")
        self.assertFalse(os.path.exists(out_path))

    def test_output_path_naming(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"a.txt": "content"})
        clean_zip(zip_path)
        expected = os.path.join(self.tmpdir, "input_output.zip")
        self.assertTrue(os.path.exists(expected))

    def test_keeps_multiple_extensions(self):
        from ww.utils.clean_zip import clean_zip

        zip_path = self._make_zip({"a.tar.gz": "x", "b.py": "y", "noext": "z"})
        clean_zip(zip_path)
        out_path = os.path.join(self.tmpdir, "input_output.zip")
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("a.tar.gz", names)
        self.assertIn("b.py", names)
        self.assertNotIn("noext", names)


# ===========================================================================
# ww/utils/smart_unzip.py
# ===========================================================================


class TestSmartUnzip(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _make_zip(self, files):
        zip_path = os.path.join(self.tmpdir, "test.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return zip_path

    def test_creates_processed_zip(self):
        from ww.utils.smart_unzip import smart_unzip

        zip_path = self._make_zip({"file.txt": "hello"})
        smart_unzip(zip_path)
        out_path = os.path.join(self.tmpdir, "test_processed.zip")
        self.assertTrue(os.path.exists(out_path))

    def test_renames_extensionless_files_with_unknown(self):
        from ww.utils.smart_unzip import smart_unzip

        zip_path = self._make_zip({"no_ext": "data", "has.txt": "text"})
        smart_unzip(zip_path)
        out_path = os.path.join(self.tmpdir, "test_processed.zip")
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        # extensionless file should be renamed to original name (arcname restored)
        self.assertIn("no_ext", names)
        self.assertIn("has.txt", names)

    def test_files_with_extensions_preserved(self):
        from ww.utils.smart_unzip import smart_unzip

        zip_path = self._make_zip({"doc.pdf": "pdf content", "img.png": "png"})
        smart_unzip(zip_path)
        out_path = os.path.join(self.tmpdir, "test_processed.zip")
        with zipfile.ZipFile(out_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("doc.pdf", names)
        self.assertIn("img.png", names)

    def test_output_zip_name_derived_from_input(self):
        from ww.utils.smart_unzip import smart_unzip

        zip_path = os.path.join(self.tmpdir, "myarchive.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file.txt", "content")
        smart_unzip(zip_path)
        expected = os.path.join(self.tmpdir, "myarchive_processed.zip")
        self.assertTrue(os.path.exists(expected))


if __name__ == "__main__":
    unittest.main()
