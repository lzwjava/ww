import unittest
from unittest.mock import MagicMock, patch


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


class TestCopyToClipboard(unittest.TestCase):
    @patch("subprocess.Popen")
    def test_returns_false_when_pyperclip_fails_and_no_platform_tools(self, mock_popen):
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
    def test_prints_to_stdout_when_no_path(self):
        from ww.search.common import write_output

        with patch("builtins.print") as mock_print:
            with patch("ww.search.common.copy_to_clipboard", return_value=True):
                write_output("test content", None)
                self.assertTrue(mock_print.called)

    def test_writes_to_file_when_path_provided(self):
        import tempfile
        import os
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


if __name__ == "__main__":
    unittest.main()
