import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from ww.md._shared import frontmatter_title, resolve_path, resolve_output, md_to_html


class TestFrontmatterTitle(unittest.TestCase):
    def _write_tmp(self, content):
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_yaml_title_double_quotes(self):
        path = self._write_tmp('---\ntitle: "Hello World"\n---\n# Body\n')
        self.addCleanup(os.unlink, path)
        self.assertEqual(frontmatter_title(path), "Hello World")

    def test_yaml_title_single_quotes(self):
        path = self._write_tmp("---\ntitle: 'My Title'\n---\nContent\n")
        self.addCleanup(os.unlink, path)
        self.assertEqual(frontmatter_title(path), "My Title")

    def test_yaml_title_no_quotes(self):
        path = self._write_tmp("---\ntitle: Simple Title\n---\nContent\n")
        self.addCleanup(os.unlink, path)
        self.assertEqual(frontmatter_title(path), "Simple Title")

    def test_yaml_title_case_insensitive(self):
        path = self._write_tmp("---\nTitle: Mixed Case\n---\nContent\n")
        self.addCleanup(os.unlink, path)
        self.assertEqual(frontmatter_title(path), "Mixed Case")

    def test_no_frontmatter(self):
        path = self._write_tmp("# Just a heading\nSome text\n")
        self.addCleanup(os.unlink, path)
        self.assertIsNone(frontmatter_title(path))

    def test_empty_frontmatter(self):
        path = self._write_tmp("---\n---\nContent\n")
        self.addCleanup(os.unlink, path)
        self.assertIsNone(frontmatter_title(path))

    def test_frontmatter_with_dots_close(self):
        path = self._write_tmp("---\ntitle: Dot End\n...\nContent\n")
        self.addCleanup(os.unlink, path)
        self.assertEqual(frontmatter_title(path), "Dot End")

    def test_title_with_extra_whitespace(self):
        path = self._write_tmp("---\ntitle:    Spaced Out   \n---\n")
        self.addCleanup(os.unlink, path)
        self.assertEqual(frontmatter_title(path), "Spaced Out")

    def test_empty_title_value(self):
        path = self._write_tmp("---\ntitle:\n---\nContent\n")
        self.addCleanup(os.unlink, path)
        self.assertIsNone(frontmatter_title(path))

    def test_empty_file(self):
        path = self._write_tmp("")
        self.addCleanup(os.unlink, path)
        self.assertIsNone(frontmatter_title(path))


class TestResolvePath(unittest.TestCase):
    def test_exact_match(self):
        fd, path = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        self.addCleanup(os.unlink, path)
        result = resolve_path(path)
        self.assertEqual(result, path)

    def test_no_match(self):
        with self.assertRaises(SystemExit):
            with patch("ww.md._shared.os.getcwd", return_value="/tmp"):
                resolve_path("nonexistent_zzz_abc.md")

    def test_substring_match_single(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "my_unique_doc.md")
            with open(target, "w") as f:
                f.write("test")
            with patch("ww.md._shared.os.getcwd", return_value=tmpdir):
                result = resolve_path("unique_doc")
                self.assertEqual(result, target)

    def test_multiple_matches_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["abc_report.md", "xyz_report.md"]:
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write("test")
            with patch("ww.md._shared.os.getcwd", return_value=tmpdir):
                with self.assertRaises(SystemExit):
                    resolve_path("report")


class TestResolveOutput(unittest.TestCase):
    def test_explicit_output(self):
        result = resolve_output("/tmp/file.md", "/out/result.jpg", None, ".jpg")
        self.assertEqual(result, "/out/result.jpg")

    def test_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outdir = os.path.join(tmpdir, "output")
            result = resolve_output("/tmp/file.md", None, outdir, ".jpg")
            self.assertEqual(result, os.path.join(outdir, "file.jpg"))
            self.assertTrue(os.path.isdir(outdir))

    def test_default_output(self):
        result = resolve_output("/tmp/file.md", None, None, ".jpg")
        self.assertEqual(result, "/tmp/file.jpg")

    def test_non_md_extension(self):
        result = resolve_output("/tmp/file.txt", None, None, ".jpg")
        self.assertEqual(result, "/tmp/file.txt.jpg")


class TestMdToHtml(unittest.TestCase):
    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = md_to_html("/tmp/in.md", "/tmp/out.html", "Title")
        self.assertTrue(result)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], "pandoc")

    @patch("subprocess.run")
    def test_pandoc_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="pandoc error")
        result = md_to_html("/tmp/in.md", "/tmp/out.html", "Title")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
