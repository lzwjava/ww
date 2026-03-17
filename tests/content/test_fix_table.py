import os
import tempfile
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


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


if __name__ == "__main__":
    unittest.main()
