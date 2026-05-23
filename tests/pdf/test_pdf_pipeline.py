import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.pdf import pdf_pipeline


class TestGetAllMdFiles(unittest.TestCase):
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    def test_finds_md_files(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = ["post1.md", "post2.md", "image.png"]
        result = pdf_pipeline.get_all_md_files("_posts")
        # 2 md files * 9 languages = 18
        self.assertEqual(len(result), 18)

    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    def test_missing_language_dir(self, mock_exists):
        mock_exists.return_value = False
        result = pdf_pipeline.get_all_md_files("_posts")
        self.assertEqual(len(result), 0)

    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    def test_empty_directory(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = []
        result = pdf_pipeline.get_all_md_files("_posts")
        self.assertEqual(len(result), 0)

    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    def test_only_md_files(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = ["a.md", "b.txt", "c.py", "d.md"]
        result = pdf_pipeline.get_all_md_files("_posts")
        # 2 md files * 9 languages
        for f in result:
            self.assertTrue(f.endswith(".md"))


class TestGetLastNFiles(unittest.TestCase):
    @patch("ww.pdf.pdf_pipeline.get_all_md_files")
    @patch("ww.pdf.pdf_pipeline.os.path.getmtime")
    def test_returns_sorted_by_mtime(self, mock_mtime, mock_get_all):
        mock_get_all.return_value = [
            "_posts/en/a.md",
            "_posts/en/b.md",
            "_posts/en/c.md",
        ]
        mock_mtime.side_effect = [100, 300, 200]
        result = pdf_pipeline.get_last_n_files("_posts", n=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "_posts/en/b.md")
        self.assertEqual(result[1], "_posts/en/c.md")

    @patch("ww.pdf.pdf_pipeline.get_all_md_files")
    @patch("ww.pdf.pdf_pipeline.os.path.getmtime")
    def test_n_larger_than_files(self, mock_mtime, mock_get_all):
        mock_get_all.return_value = ["_posts/en/a.md"]
        mock_mtime.side_effect = [100]
        result = pdf_pipeline.get_last_n_files("_posts", n=10)
        self.assertEqual(len(result), 1)

    @patch("ww.pdf.pdf_pipeline.get_all_md_files")
    def test_exception_returns_empty(self, mock_get_all):
        mock_get_all.side_effect = Exception("error")
        result = pdf_pipeline.get_last_n_files("_posts")
        self.assertEqual(result, [])


class TestProcessMarkdownFiles(unittest.TestCase):
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    def test_no_md_files(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = ["file.txt"]
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    def test_missing_lang_dir(self, mock_exists):
        mock_exists.return_value = False
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.pdf_pipeline.text_to_pdf_from_markdown")
    @patch("ww.pdf.pdf_pipeline.os.makedirs")
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.remove")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    @patch("builtins.open", create=True)
    def test_process_valid_file(
        self,
        mock_file_open,
        mock_listdir,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        # Only the first language dir exists and has files
        def exists_side_effect(path):
            if "_posts/en" in str(path):
                return True
            if "assets" in str(path):
                return False
            if ".cleaned" in str(path):
                return False
            return False

        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ["test.md"]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = (
            "---\ntitle: Test\n---\n\nContent"
        )
        mock_pdf.return_value = True

        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.pdf_pipeline.text_to_pdf_from_markdown")
    @patch("ww.pdf.pdf_pipeline.os.makedirs")
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.remove")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    @patch("builtins.open", create=True)
    def test_skip_existing_pdf(
        self,
        mock_file_open,
        mock_listdir,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        def exists_side_effect(path):
            if "_posts/en" in str(path):
                return True
            if "assets/pdfs/en/test.pdf" in str(path):
                return True
            return False

        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ["test.md"]
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs")
        mock_pdf.assert_not_called()

    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    def test_with_n_parameter(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = []
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs", n=5)

    @patch("ww.pdf.pdf_pipeline.text_to_pdf_from_markdown")
    @patch("ww.pdf.pdf_pipeline.os.makedirs")
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.remove")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    @patch("builtins.open", create=True)
    def test_empty_front_matter(
        self,
        mock_file_open,
        mock_listdir,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        def exists_side_effect(path):
            if "_posts/en" in str(path):
                return True
            return False

        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ["test.md"]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = "---\ntitle: T\n---\n"
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs")
        mock_pdf.assert_not_called()

    @patch("ww.pdf.pdf_pipeline.text_to_pdf_from_markdown")
    @patch("ww.pdf.pdf_pipeline.os.makedirs")
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.remove")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    @patch("builtins.open", create=True)
    def test_max_files_limit(
        self,
        mock_file_open,
        mock_listdir,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        call_count = [0]

        def exists_side_effect(path):
            if "_posts/en" in str(path):
                return True
            if ".cleaned" in str(path):
                return False
            # For output files
            return False

        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ["a.md", "b.md"]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = "---\ntitle: T\n---\n\nBody"
        mock_pdf.return_value = True
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs", max_files=1)

    @patch("ww.pdf.pdf_pipeline.text_to_pdf_from_markdown")
    @patch("ww.pdf.pdf_pipeline.os.makedirs")
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.remove")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    @patch("builtins.open", create=True)
    def test_read_error_handled(
        self,
        mock_file_open,
        mock_listdir,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        def exists_side_effect(path):
            if "_posts/en" in str(path):
                return True
            return False

        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ["test.md"]
        mock_file_open.side_effect = IOError("read error")
        # Should not raise
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.pdf_pipeline.text_to_pdf_from_markdown")
    @patch("ww.pdf.pdf_pipeline.os.makedirs")
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.remove")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    @patch("builtins.open", create=True)
    def test_title_with_single_quotes(
        self,
        mock_file_open,
        mock_listdir,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        def exists_side_effect(path):
            if "_posts/en" in str(path):
                return True
            if ".cleaned" in str(path):
                return False
            return False

        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ["test.md"]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = (
            "---\ntitle: 'Single Quoted'\n---\n\nBody"
        )
        mock_pdf.return_value = True
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs")

    @patch("ww.pdf.pdf_pipeline.text_to_pdf_from_markdown")
    @patch("ww.pdf.pdf_pipeline.os.makedirs")
    @patch("ww.pdf.pdf_pipeline.os.path.exists")
    @patch("ww.pdf.pdf_pipeline.os.remove")
    @patch("ww.pdf.pdf_pipeline.os.listdir")
    @patch("builtins.open", create=True)
    def test_dry_run(
        self,
        mock_file_open,
        mock_listdir,
        mock_remove,
        mock_exists,
        mock_makedirs,
        mock_pdf,
    ):
        def exists_side_effect(path):
            if "_posts/en" in str(path):
                return True
            if ".cleaned" in str(path):
                return False
            return False

        mock_exists.side_effect = exists_side_effect
        mock_listdir.return_value = ["test.md"]
        mock_file_open.return_value.__enter__ = lambda s: s
        mock_file_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_file_open.return_value.read.return_value = "---\ntitle: T\n---\n\nBody"
        mock_pdf.return_value = True
        pdf_pipeline.process_markdown_files("_posts", "assets/pdfs", dry_run=True)


if __name__ == "__main__":
    unittest.main()
