import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestFontForLang(unittest.TestCase):
    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_en_returns_helvetica(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("en"), "Helvetica")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_zh_returns_pingfang_sc(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("zh"), "PingFang SC")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_hant_returns_pingfang_tc(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("hant"), "PingFang TC")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_ja_returns_hiragino(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("ja"), "Hiragino Sans")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_hi_returns_kohinoor(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("hi"), "Kohinoor Devanagari")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_ar_returns_geeza_pro(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("ar"), "Geeza Pro")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_unknown_returns_arial_unicode(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("ko"), "Arial Unicode MS")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_fr_returns_helvetica(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("fr"), "Helvetica")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_de_returns_helvetica(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("de"), "Helvetica")

    @patch("ww.pdf.pdf_base.platform")
    def test_darwin_es_returns_helvetica(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Darwin"
        self.assertEqual(_font_for_lang("es"), "Helvetica")

    @patch("ww.pdf.pdf_base.platform")
    def test_linux_en_returns_dejavu(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Linux"
        self.assertEqual(_font_for_lang("en"), "DejaVu Sans")

    @patch("ww.pdf.pdf_base.platform")
    def test_linux_zh_returns_noto_cjk_sc(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Linux"
        self.assertEqual(_font_for_lang("zh"), "Noto Sans CJK SC")

    @patch("ww.pdf.pdf_base.platform")
    def test_linux_hant_returns_noto_cjk_tc(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Linux"
        self.assertEqual(_font_for_lang("hant"), "Noto Sans CJK TC")

    @patch("ww.pdf.pdf_base.platform")
    def test_linux_ja_returns_noto_cjk_jp(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Linux"
        self.assertEqual(_font_for_lang("ja"), "Noto Sans CJK JP")

    @patch("ww.pdf.pdf_base.platform")
    def test_linux_hi_returns_noto_devanagari(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Linux"
        self.assertEqual(_font_for_lang("hi"), "Noto Sans Devanagari")

    @patch("ww.pdf.pdf_base.platform")
    def test_linux_ar_returns_noto_naskh(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Linux"
        self.assertEqual(_font_for_lang("ar"), "Noto Naskh Arabic")

    @patch("ww.pdf.pdf_base.platform")
    def test_linux_unknown_returns_noto_sans(self, mock_platform):
        from ww.pdf.pdf_base import _font_for_lang

        mock_platform.system.return_value = "Linux"
        self.assertEqual(_font_for_lang("ko"), "Noto Sans")


class TestTextToPdfFromMarkdownDryRun(unittest.TestCase):
    def test_dry_run_prints_message(self):
        from ww.pdf.pdf_base import text_to_pdf_from_markdown

        with patch("builtins.print") as mock_print:
            result = text_to_pdf_from_markdown(
                "/tmp/input.md", "/tmp/output.pdf", dry_run=True
            )
            self.assertIsNone(result)
            calls = [str(c) for c in mock_print.call_args_list]
            self.assertTrue(any("Dry run" in c for c in calls))

    def test_dry_run_does_not_call_subprocess(self):
        from ww.pdf.pdf_base import text_to_pdf_from_markdown

        with patch("subprocess.run") as mock_run:
            with patch("builtins.print"):
                text_to_pdf_from_markdown(
                    "/tmp/input.md", "/tmp/output.pdf", dry_run=True
                )
                mock_run.assert_not_called()


class TestTextToPdfFromMarkdown(unittest.TestCase):
    @patch("os.path.exists", return_value=True)
    @patch("subprocess.run")
    def test_calls_pandoc_with_xelatex(self, mock_run, mock_exists):
        from ww.pdf.pdf_base import text_to_pdf_from_markdown

        mock_run.return_value = MagicMock(returncode=0)
        result = text_to_pdf_from_markdown("/tmp/input-en.md", "/tmp/output.pdf")
        self.assertTrue(result)
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], "pandoc")
        self.assertIn("--pdf-engine", cmd)
        self.assertIn("xelatex", cmd)

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.run")
    def test_returns_false_on_pandoc_error(self, mock_run, mock_exists):
        from ww.pdf.pdf_base import text_to_pdf_from_markdown

        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        result = text_to_pdf_from_markdown("/tmp/input.md", "/tmp/output.pdf")
        self.assertFalse(result)

    def test_raises_when_input_not_exists(self):
        from ww.pdf.pdf_base import text_to_pdf_from_markdown

        with self.assertRaises(Exception):
            text_to_pdf_from_markdown("/nonexistent/input.md", "/tmp/output.pdf")

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.run")
    def test_includes_toc_flags(self, mock_run, mock_exists):
        from ww.pdf.pdf_base import text_to_pdf_from_markdown

        mock_run.return_value = MagicMock(returncode=0)
        text_to_pdf_from_markdown(
            "/tmp/input.md",
            "/tmp/output.pdf",
            toc=True,
            toc_depth=3,
            toc_title="Table of Contents",
            toc_own_page=True,
        )
        cmd = mock_run.call_args[0][0]
        self.assertIn("--toc", cmd)
        self.assertIn("--toc-depth", cmd)

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.run")
    def test_extra_pandoc_args_appended(self, mock_run, mock_exists):
        from ww.pdf.pdf_base import text_to_pdf_from_markdown

        mock_run.return_value = MagicMock(returncode=0)
        text_to_pdf_from_markdown(
            "/tmp/input.md",
            "/tmp/output.pdf",
            extra_pandoc_args=["--highlight-style", "tango"],
        )
        cmd = mock_run.call_args[0][0]
        self.assertIn("--highlight-style", cmd)
        self.assertIn("tango", cmd)

    def test_extra_pandoc_args_type_check(self):
        from ww.pdf.pdf_base import text_to_pdf_from_markdown

        with patch("os.path.exists", return_value=True):
            with self.assertRaises(TypeError):
                text_to_pdf_from_markdown(
                    "/tmp/input.md",
                    "/tmp/output.pdf",
                    extra_pandoc_args="not-a-list",
                )


class TestMergePdfs(unittest.TestCase):
    @patch("ww.pdf.pdf_base.PdfWriter")
    @patch("ww.pdf.pdf_base.PdfReader")
    @patch("os.path.exists", return_value=True)
    def test_merges_multiple_pdfs(self, mock_exists, mock_reader_cls, mock_writer_cls):
        from ww.pdf.pdf_base import merge_pdfs

        mock_writer = MagicMock()
        mock_writer_cls.return_value = mock_writer

        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_reader_cls.return_value = mock_reader

        with patch("builtins.print"):
            with patch("builtins.open", unittest.mock.mock_open()):
                result = merge_pdfs(["/tmp/a.pdf", "/tmp/b.pdf"], "/tmp/merged.pdf")
        self.assertTrue(result)
        self.assertEqual(mock_writer.add_page.call_count, 4)

    @patch("ww.pdf.pdf_base.PdfWriter")
    @patch("os.path.exists")
    def test_skips_missing_files(self, mock_exists, mock_writer_cls):
        from ww.pdf.pdf_base import merge_pdfs

        mock_exists.return_value = False
        mock_writer = MagicMock()
        mock_writer_cls.return_value = mock_writer

        with patch("builtins.print"):
            result = merge_pdfs(["/nonexistent.pdf"], "/tmp/merged.pdf")
        self.assertFalse(result)

    @patch("ww.pdf.pdf_base.PdfWriter", None)
    @patch("ww.pdf.pdf_base.PdfReader", None)
    def test_returns_false_when_pypdf_unavailable(self):
        from ww.pdf.pdf_base import merge_pdfs

        with patch("builtins.print"):
            result = merge_pdfs(["/tmp/a.pdf"], "/tmp/merged.pdf")
        self.assertFalse(result)

    @patch("ww.pdf.pdf_base.PdfWriter")
    @patch("ww.pdf.pdf_base.PdfReader")
    @patch("os.path.exists", return_value=True)
    def test_returns_false_on_reader_error(
        self, mock_exists, mock_reader_cls, mock_writer_cls
    ):
        from ww.pdf.pdf_base import merge_pdfs

        mock_writer = MagicMock()
        mock_writer_cls.return_value = mock_writer
        mock_reader_cls.side_effect = Exception("corrupt pdf")

        with patch("builtins.print"):
            result = merge_pdfs(["/tmp/bad.pdf"], "/tmp/merged.pdf")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
