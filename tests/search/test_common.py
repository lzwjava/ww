import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestFormatLlmOutput(unittest.TestCase):
    def test_formats_single_result(self):
        from ww.search.common import format_llm_output

        results = [
            {"title": "Test", "url": "https://example.com", "content": "test content"}
        ]
        output = format_llm_output(results)
        self.assertIn("Source 1", output)
        self.assertIn("Test", output)
        self.assertIn("https://example.com", output)
        self.assertIn("test content", output)

    def test_formats_multiple_results(self):
        from ww.search.common import format_llm_output

        results = [
            {"title": "First", "url": "https://first.com", "content": "content1"},
            {"title": "Second", "url": "https://second.com", "content": "content2"},
        ]
        output = format_llm_output(results)
        self.assertIn("Source 1", output)
        self.assertIn("Source 2", output)
        self.assertIn("First", output)
        self.assertIn("Second", output)

    def test_handles_missing_content(self):
        from ww.search.common import format_llm_output

        results = [{"title": "Test", "url": "https://example.com"}]
        output = format_llm_output(results)
        self.assertIn("No content extracted", output)

    def test_empty_results(self):
        from ww.search.common import format_llm_output

        output = format_llm_output([])
        self.assertEqual(output, "")

    def test_separator_present(self):
        from ww.search.common import format_llm_output

        results = [
            {"title": "A", "url": "https://a.com", "content": "c1"},
            {"title": "B", "url": "https://b.com", "content": "c2"},
        ]
        output = format_llm_output(results)
        self.assertIn("-" * 40, output)


class TestFormatAckLine(unittest.TestCase):
    @patch("builtins.print")
    def test_double_dash_prints_empty_line(self, mock_print):
        from ww.search.common import _format_ack_line

        _format_ack_line("-- separator --")
        mock_print.assert_called_with()

    @patch("builtins.print")
    def test_colon_separated_line_printed_verbatim(self, mock_print):
        from ww.search.common import _format_ack_line

        _format_ack_line("file.md:10:some content")
        mock_print.assert_called_with("file.md:10:some content")

    @patch("builtins.print")
    def test_hyphen_separated_line_converted(self, mock_print):
        from ww.search.common import _format_ack_line

        _format_ack_line("file.md-10-some content")
        mock_print.assert_called_with("file.md:10:some content")

    @patch("builtins.print")
    def test_plain_line_printed_verbatim(self, mock_print):
        from ww.search.common import _format_ack_line

        _format_ack_line("plain text no delimiters")
        mock_print.assert_called_with("plain text no delimiters")

    @patch("builtins.print")
    def test_line_starting_with_dash_printed_verbatim(self, mock_print):
        from ww.search.common import _format_ack_line

        _format_ack_line("-leading-dash text")
        mock_print.assert_called_with("-leading-dash text")


class TestPrintAckOutput(unittest.TestCase):
    @patch("builtins.print")
    def test_empty_stdout_prints_no_matches(self, mock_print):
        from ww.search.common import print_ack_output

        print_ack_output("")
        calls = [str(c) for c in mock_print.call_args_list]
        self.assertTrue(any("No matches found" in c for c in calls))

    @patch("builtins.print")
    def test_none_stdout_prints_no_matches(self, mock_print):
        from ww.search.common import print_ack_output

        print_ack_output(None)
        calls = [str(c) for c in mock_print.call_args_list]
        self.assertTrue(any("No matches found" in c for c in calls))

    @patch("builtins.print")
    def test_stdout_with_lines_processed(self, mock_print):
        from ww.search.common import print_ack_output

        print_ack_output("line1\nline2\n")
        self.assertTrue(mock_print.call_count > 0)


class TestCopyToClipboard(unittest.TestCase):
    @patch("subprocess.Popen")
    def test_returns_false_when_popen_fails(self, mock_popen):
        mock_popen.side_effect = Exception("no pbcopy")
        from ww.search.common import copy_to_clipboard

        result = copy_to_clipboard("test text")
        self.assertFalse(result)

    @patch("subprocess.Popen")
    def test_returns_true_on_popen_success(self, mock_popen):
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        from ww.search.common import copy_to_clipboard

        result = copy_to_clipboard("test text")
        self.assertTrue(result)


class TestWriteOutput(unittest.TestCase):
    @patch("builtins.print")
    def test_prints_to_stdout_when_no_path(self, mock_print):
        from ww.search.common import write_output

        with patch("ww.search.common.copy_to_clipboard", return_value=True):
            write_output("test content", None)
            self.assertTrue(mock_print.called)

    def test_writes_to_file_when_path_provided(self):
        from ww.search.common import write_output

        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            temp_path = f.name

        try:
            with patch("builtins.print"):
                with patch("ww.search.common.copy_to_clipboard", return_value=True):
                    write_output("test content", temp_path)
            with open(temp_path, "r") as f:
                self.assertEqual(f.read(), "test content")
        finally:
            os.unlink(temp_path)


class TestSiteTargets(unittest.TestCase):
    def test_known_domain_returns_selected_elements(self):
        from ww.search.common import _site_targets, SITE_SELECTORS

        mock_soup = MagicMock()
        mock_elements = [MagicMock(), MagicMock()]
        mock_soup.select.return_value = mock_elements

        result = _site_targets(mock_soup, "https://zhihu.com/question/123")
        self.assertEqual(result, mock_elements)
        mock_soup.select.assert_called_with(SITE_SELECTORS["zhihu.com"])

    def test_unknown_domain_returns_none(self):
        from ww.search.common import _site_targets

        mock_soup = MagicMock()
        result = _site_targets(mock_soup, "https://unknown-site.com/page")
        self.assertIsNone(result)
        mock_soup.select.assert_not_called()

    def test_wikipedia_domain(self):
        from ww.search.common import _site_targets, SITE_SELECTORS

        mock_soup = MagicMock()
        mock_soup.select.return_value = ["el"]
        result = _site_targets(mock_soup, "https://en.wikipedia.org/wiki/Python")
        self.assertEqual(result, ["el"])
        mock_soup.select.assert_called_with(SITE_SELECTORS["wikipedia.org"])

    def test_github_domain(self):
        from ww.search.common import _site_targets, SITE_SELECTORS

        mock_soup = MagicMock()
        mock_soup.select.return_value = ["el"]
        result = _site_targets(mock_soup, "https://github.com/user/repo")
        self.assertEqual(result, ["el"])
        mock_soup.select.assert_called_with(SITE_SELECTORS["github.com"])

    def test_baidu_zhidao_domain(self):
        from ww.search.common import _site_targets, SITE_SELECTORS

        mock_soup = MagicMock()
        mock_soup.select.return_value = ["el"]
        result = _site_targets(mock_soup, "https://zhidao.baidu.com/question/123")
        self.assertEqual(result, ["el"])
        mock_soup.select.assert_called_with(SITE_SELECTORS["zhidao.baidu.com"])


class TestCheckAck(unittest.TestCase):
    @patch("shutil.which", return_value="/usr/local/bin/ack")
    def test_returns_path_when_ack_found(self, mock_which):
        from ww.search.common import check_ack

        result = check_ack()
        self.assertEqual(result, "/usr/local/bin/ack")
        mock_which.assert_called_once_with("ack")

    @patch("shutil.which", return_value=None)
    def test_exits_when_ack_not_found(self, mock_which):
        from ww.search.common import check_ack

        with self.assertRaises(SystemExit):
            check_ack()


if __name__ == "__main__":
    unittest.main()
