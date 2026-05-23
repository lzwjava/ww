import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.pdf import update_pdf


class TestGetAllMdFiles(unittest.TestCase):
    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.os.listdir")
    def test_finds_md_files(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = ["post1.md", "post2.md", "image.png"]
        result = update_pdf.get_all_md_files("_posts")
        self.assertEqual(len(result), 18)  # 2 files * 9 languages

    @patch("ww.pdf.update_pdf.os.path.exists")
    def test_missing_language_dir(self, mock_exists):
        mock_exists.return_value = False
        result = update_pdf.get_all_md_files("_posts")
        self.assertEqual(len(result), 0)

    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.os.listdir")
    def test_empty_directory(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = []
        result = update_pdf.get_all_md_files("_posts")
        self.assertEqual(len(result), 0)


class TestGetLastNFiles(unittest.TestCase):
    @patch("ww.pdf.update_pdf.get_all_md_files")
    @patch("ww.pdf.update_pdf.os.path.getmtime")
    def test_returns_last_n(self, mock_mtime, mock_get_all):
        mock_get_all.return_value = [
            "_posts/en/a.md",
            "_posts/en/b.md",
            "_posts/en/c.md",
        ]
        mock_mtime.side_effect = [100, 300, 200]
        result = update_pdf.get_last_n_files("_posts", n=2)
        self.assertEqual(len(result), 2)
        # Should be sorted by mtime descending: b (300), c (200)
        self.assertEqual(result[0], "_posts/en/b.md")

    @patch("ww.pdf.update_pdf.get_all_md_files")
    def test_exception_returns_empty(self, mock_get_all):
        mock_get_all.side_effect = Exception("error")
        result = update_pdf.get_last_n_files("_posts")
        self.assertEqual(result, [])


class TestGetChangedFiles(unittest.TestCase):
    @patch("ww.pdf.update_pdf.subprocess.run")
    @patch("ww.pdf.update_pdf.get_base_path", return_value="/repo")
    def test_returns_changed_md_files(self, mock_base, mock_run):
        mock_run.return_value = MagicMock(
            stdout="_posts/en/post1.md\n_posts/zh/post2.md\nREADME.md\n",
            returncode=0,
        )
        result = update_pdf.get_changed_files()
        self.assertEqual(len(result), 2)
        self.assertIn("_posts/en/post1.md", result)
        self.assertIn("_posts/zh/post2.md", result)
        self.assertNotIn("README.md", result)

    @patch("ww.pdf.update_pdf.subprocess.run")
    @patch("ww.pdf.update_pdf.get_base_path", return_value="/repo")
    def test_no_changed_files(self, mock_base, mock_run):
        mock_run.return_value = MagicMock(stdout="\n", returncode=0)
        result = update_pdf.get_changed_files()
        self.assertEqual(len(result), 0)

    @patch("ww.pdf.update_pdf.subprocess.run")
    @patch("ww.pdf.update_pdf.get_base_path", return_value="/repo")
    def test_git_error(self, mock_base, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = update_pdf.get_changed_files()
        self.assertEqual(result, [])


class TestProcessMarkdownFiles(unittest.TestCase):
    @patch("ww.pdf.update_pdf.get_changed_files")
    def test_no_files_to_process(self, mock_changed):
        mock_changed.return_value = []
        update_pdf.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.get_changed_files")
    def test_changed_file_not_found(self, mock_changed, mock_exists):
        mock_changed.return_value = ["_posts/en/missing.md"]
        mock_exists.return_value = False
        update_pdf.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.update_pdf.text_to_pdf_from_markdown")
    @patch("ww.pdf.update_pdf.os.makedirs")
    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.os.remove")
    @patch("ww.pdf.update_pdf.get_changed_files")
    @patch("builtins.open", create=True)
    def test_process_valid_markdown(
        self,
        mock_file_open,
        mock_changed,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        mock_changed.return_value = ["_posts/en/test.md"]
        # First exists call: for changed file exists check -> True
        # Second: for output_filename exists check -> False
        # Third+: for cleanup
        mock_exists.side_effect = [True, False, False, False]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = (
            "---\ntitle: Test\n---\n\nContent here"
        )
        mock_pdf.return_value = True

        update_pdf.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.update_pdf.text_to_pdf_from_markdown")
    @patch("ww.pdf.update_pdf.os.makedirs")
    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.os.remove")
    @patch("ww.pdf.update_pdf.get_changed_files")
    @patch("builtins.open", create=True)
    def test_skip_existing_output(
        self,
        mock_file_open,
        mock_changed,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        mock_changed.return_value = ["_posts/en/test.md"]
        mock_exists.side_effect = [True, True]  # file exists, output exists
        update_pdf.process_markdown_files("_posts", "assets/pdfs")
        mock_pdf.assert_not_called()

    @patch("ww.pdf.update_pdf.text_to_pdf_from_markdown")
    @patch("ww.pdf.update_pdf.os.makedirs")
    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.get_changed_files")
    @patch("builtins.open", create=True)
    def test_empty_front_matter(
        self, mock_file_open, mock_changed, mock_exists, mock_makedirs, mock_pdf
    ):
        mock_changed.return_value = ["_posts/en/test.md"]
        mock_exists.side_effect = [True, False, False]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        # Front matter with no content after
        mock_file_open.return_value.read.return_value = "---\ntitle: Test\n---\n"
        update_pdf.process_markdown_files("_posts", "assets/pdfs")
        mock_pdf.assert_not_called()

    @patch("ww.pdf.update_pdf.text_to_pdf_from_markdown")
    @patch("ww.pdf.update_pdf.os.makedirs")
    @patch("ww.pdf.update_pdf.get_changed_files")
    @patch("builtins.open", side_effect=IOError("read error"))
    @patch("ww.pdf.update_pdf.os.path.exists", return_value=True)
    def test_read_error(
        self, mock_exists, mock_open, mock_changed, mock_makedirs, mock_pdf
    ):
        mock_changed.return_value = ["_posts/en/test.md"]
        # Should not raise
        update_pdf.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.update_pdf.text_to_pdf_from_markdown")
    @patch("ww.pdf.update_pdf.os.makedirs")
    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.os.remove")
    @patch("ww.pdf.update_pdf.get_changed_files")
    @patch("builtins.open", create=True)
    def test_max_files_limit(
        self,
        mock_file_open,
        mock_changed,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        mock_changed.return_value = ["_posts/en/test1.md", "_posts/en/test2.md"]
        mock_exists.side_effect = [True, False, False, False, True, False, False, False]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = "---\ntitle: T\n---\n\nBody"
        mock_pdf.return_value = True
        update_pdf.process_markdown_files("_posts", "assets/pdfs", max_files=1)

    @patch("ww.pdf.update_pdf.text_to_pdf_from_markdown")
    @patch("ww.pdf.update_pdf.os.makedirs")
    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.os.remove")
    @patch("ww.pdf.update_pdf.get_changed_files")
    @patch("builtins.open", create=True)
    def test_title_with_quotes(
        self,
        mock_file_open,
        mock_changed,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        mock_changed.return_value = ["_posts/en/test.md"]
        mock_exists.side_effect = [True, False, False, False]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = (
            '---\ntitle: "Quoted Title"\n---\n\nBody text'
        )
        mock_pdf.return_value = True
        update_pdf.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.update_pdf.text_to_pdf_from_markdown")
    @patch("ww.pdf.update_pdf.os.makedirs")
    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.os.remove")
    @patch("ww.pdf.update_pdf.get_changed_files")
    @patch("builtins.open", create=True)
    def test_pandoc_error(
        self,
        mock_file_open,
        mock_changed,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        mock_changed.return_value = ["_posts/en/test.md"]
        mock_exists.side_effect = [True, False, False, False]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = "---\ntitle: T\n---\n\nBody"
        mock_pdf.return_value = False  # pandoc error
        update_pdf.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.update_pdf.text_to_pdf_from_markdown")
    @patch("ww.pdf.update_pdf.os.makedirs")
    @patch("ww.pdf.update_pdf.os.path.exists")
    @patch("ww.pdf.update_pdf.os.remove")
    @patch("ww.pdf.update_pdf.get_changed_files")
    @patch("builtins.open", create=True)
    def test_dry_run(
        self,
        mock_file_open,
        mock_changed,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        mock_changed.return_value = ["_posts/en/test.md"]
        mock_exists.side_effect = [True, False, False, False]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = "---\ntitle: T\n---\n\nBody"
        mock_pdf.return_value = True
        update_pdf.process_markdown_files("_posts", "assets/pdfs", dry_run=True)


if __name__ == "__main__":
    unittest.main()
