import os
import shutil
import tempfile
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestProcessTablesInFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

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

    def test_table_already_has_blank_line_unchanged(self):
        from ww.content.fix_table import process_tables_in_file

        content = "## Heading\n\n|col1|col2|\n|---|---|\n|a|b|\n"
        fp = self._make_file(content)
        process_tables_in_file(fp, fix_tables=True)
        with open(fp, "r", encoding="utf-8") as f:
            result = f.read()
        self.assertIn("## Heading\n\n|", result)

    def test_code_blocks_preserved(self):
        from ww.content.fix_table import process_tables_in_file

        content = "## Heading\n\n```\n|not a table|\n```\n\nSome text.\n"
        fp = self._make_file(content)
        result = process_tables_in_file(fp)
        self.assertTrue(result)
        with open(fp, "r", encoding="utf-8") as f:
            out = f.read()
        self.assertIn("```", out)
        self.assertIn("|not a table|", out)

    def test_h3_heading_table(self):
        from ww.content.fix_table import process_tables_in_file

        fp = self._make_file("### Subheading\n|col1|col2|\n|---|---|\n|a|b|\n")
        process_tables_in_file(fp, fix_tables=True)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("\n\n|", content)

    def test_multiple_tables_in_file(self):
        from ww.content.fix_table import process_tables_in_file

        content = (
            "## Table 1\n|a|b|\n|---|---|\n|1|2|\n\n"
            "## Table 2\nc|d|\n|---|---|\n|3|4|\n"
        )
        fp = self._make_file(content)
        process_tables_in_file(fp, fix_tables=True)
        with open(fp, "r", encoding="utf-8") as f:
            result = f.read()
        self.assertIn("## Table 1", result)
        self.assertIn("## Table 2", result)


class TestProcessTablesInMarkdown(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

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

    def test_ignores_non_md_files(self):
        from ww.content.fix_table import process_tables_in_markdown

        txt_file = os.path.join(self.tmpdir, "readme.txt")
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("## H\n|a|b|\n|---|---|\n")
        md_file = os.path.join(self.tmpdir, "real.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("## H\n|a|b|\n|---|---|\n")
        process_tables_in_markdown(self.tmpdir)
        with open(txt_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "## H\n|a|b|\n|---|---|\n")

    def test_walks_subdirectories(self):
        from ww.content.fix_table import process_tables_in_markdown

        subdir = os.path.join(self.tmpdir, "sub")
        os.makedirs(subdir)
        fp = os.path.join(subdir, "nested.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("## H\n|a|b|\n|---|---|\n")
        process_tables_in_markdown(self.tmpdir)
        with open(fp, "r", encoding="utf-8") as f:
            f.read()  # no crash

    def test_fix_tables_propagates(self):
        from ww.content.fix_table import process_tables_in_markdown

        fp = os.path.join(self.tmpdir, "test.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("## Heading\n|col1|col2|\n|---|---|\n|a|b|\n")
        process_tables_in_markdown(self.tmpdir, fix_tables=True)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("\n\n|", content)

    def test_empty_directory(self):
        from ww.content.fix_table import process_tables_in_markdown

        # Should not raise
        process_tables_in_markdown(self.tmpdir)


if __name__ == "__main__":
    unittest.main()
