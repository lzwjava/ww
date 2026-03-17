import os
import tempfile
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


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
        fix_mathjax_in_markdown(self.tmpdir, max_files=1)


if __name__ == "__main__":
    unittest.main()
