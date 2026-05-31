import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestFrontmatterTitle(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_md(self, content):
        fp = os.path.join(self.tmpdir, "test.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        return fp

    def test_extracts_title_from_frontmatter(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md("---\ntitle: My Title\n---\n# Content\n")
        self.assertEqual(_frontmatter_title(fp), "My Title")

    def test_extracts_quoted_title(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md('---\ntitle: "Quoted Title"\n---\n# Content\n')
        self.assertEqual(_frontmatter_title(fp), "Quoted Title")

    def test_extracts_single_quoted_title(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md("---\ntitle: 'Single Quoted'\n---\n# Content\n")
        self.assertEqual(_frontmatter_title(fp), "Single Quoted")

    def test_returns_none_when_no_frontmatter(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md("# No Frontmatter\nSome content\n")
        self.assertIsNone(_frontmatter_title(fp))

    def test_returns_none_when_no_title_in_frontmatter(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md("---\nauthor: Someone\n---\n# Content\n")
        self.assertIsNone(_frontmatter_title(fp))

    def test_returns_none_for_empty_title(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md("---\ntitle: \n---\n# Content\n")
        self.assertIsNone(_frontmatter_title(fp))

    def test_handles_dot_end_marker(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md("---\ntitle: Dotted\n...\n# Content\n")
        self.assertEqual(_frontmatter_title(fp), "Dotted")

    def test_empty_file(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md("")
        self.assertIsNone(_frontmatter_title(fp))

    def test_case_insensitive_title(self):
        from ww.pdf.md2png import _frontmatter_title

        fp = self._write_md("---\nTitle: Capitalized\n---\n# Content\n")
        self.assertEqual(_frontmatter_title(fp), "Capitalized")


class TestChromePath(unittest.TestCase):
    def test_returns_which_result(self):
        from ww.pdf.md2png import _chrome_path

        with (
            patch("os.path.isfile", return_value=False),
            patch("shutil.which", return_value="/usr/bin/chromium"),
        ):
            result = _chrome_path()
            # _chrome_path returns the candidate string, not the which() result
            self.assertEqual(result, "google-chrome")

    @patch("shutil.which", return_value=None)
    @patch("os.path.isfile", return_value=True)
    @patch("os.path.isabs", return_value=True)
    def test_returns_absolute_path_if_exists(self, mock_isabs, mock_isfile, mock_which):
        from ww.pdf.md2png import _chrome_path

        result = _chrome_path()
        self.assertEqual(
            result,
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )

    @patch("shutil.which", return_value=None)
    @patch("os.path.isfile", return_value=False)
    @patch("os.path.isabs", side_effect=lambda p: p.startswith("/"))
    def test_returns_none_when_no_chrome(self, mock_isabs, mock_isfile, mock_which):
        from ww.pdf.md2png import _chrome_path

        result = _chrome_path()
        self.assertIsNone(result)


class TestMdToHtml(unittest.TestCase):
    @patch("subprocess.run")
    def test_calls_pandoc(self, mock_run):
        from ww.pdf.md2png import _md_to_html

        mock_run.return_value = MagicMock(returncode=0)
        result = _md_to_html("/tmp/input.md", "/tmp/output.html", "My Title")
        self.assertTrue(result)
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], "pandoc")
        self.assertIn("/tmp/input.md", cmd)
        self.assertIn("/tmp/output.html", cmd)

    @patch("subprocess.run")
    def test_returns_false_on_pandoc_error(self, mock_run):
        from ww.pdf.md2png import _md_to_html

        mock_run.return_value = MagicMock(returncode=1, stderr="pandoc error")
        result = _md_to_html("/tmp/input.md", "/tmp/output.html", "Title")
        self.assertFalse(result)


class TestHtmlToPdf(unittest.TestCase):
    @patch("os.path.isfile", return_value=True)
    @patch("subprocess.run")
    def test_calls_chrome_headless(self, mock_run, mock_isfile):
        from ww.pdf.md2png import _html_to_pdf

        mock_run.return_value = MagicMock(returncode=0)
        result = _html_to_pdf("/tmp/input.html", "/tmp/output.pdf", "/usr/bin/chrome")
        self.assertTrue(result)
        cmd = mock_run.call_args[0][0]
        self.assertIn("--headless=new", cmd)
        self.assertIn("/usr/bin/chrome", cmd[0])

    @patch("subprocess.run")
    def test_returns_false_on_chrome_error(self, mock_run):
        from ww.pdf.md2png import _html_to_pdf

        mock_run.return_value = MagicMock(returncode=1, stderr="chrome error")
        result = _html_to_pdf("/tmp/input.html", "/tmp/output.pdf", "/usr/bin/chrome")
        self.assertFalse(result)

    @patch("os.path.isfile", return_value=False)
    @patch("subprocess.run")
    def test_returns_false_when_no_pdf_produced(self, mock_run, mock_isfile):
        from ww.pdf.md2png import _html_to_pdf

        mock_run.return_value = MagicMock(returncode=0)
        result = _html_to_pdf("/tmp/input.html", "/tmp/output.pdf", "/usr/bin/chrome")
        self.assertFalse(result)


class TestPdfToPng(unittest.TestCase):
    @patch("shutil.copyfile")
    @patch("os.listdir", return_value=["page-01.png"])
    @patch("subprocess.run")
    def test_single_page(self, mock_run, mock_listdir, mock_copy):
        from ww.pdf.md2png import _pdf_to_png

        mock_run.return_value = MagicMock(returncode=0)
        result = _pdf_to_png("/tmp/input.pdf", "/tmp/output.png", 150)
        self.assertTrue(result)

    @patch("os.listdir", return_value=[])
    @patch("subprocess.run")
    def test_no_pages_generated(self, mock_run, mock_listdir):
        from ww.pdf.md2png import _pdf_to_png

        mock_run.return_value = MagicMock(returncode=0)
        result = _pdf_to_png("/tmp/input.pdf", "/tmp/output.png", 150)
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_returns_false_on_magick_error(self, mock_run):
        from ww.pdf.md2png import _pdf_to_png

        mock_run.return_value = MagicMock(returncode=1, stderr="magick error")
        result = _pdf_to_png("/tmp/input.pdf", "/tmp/output.png", 150)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
