import unittest
from unittest.mock import patch, MagicMock, mock_open
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestTitleAgent(unittest.TestCase):
    @patch("ww.agent.title_agent.call_openrouter_api")
    def test_generate_title_with_ai_success(self, mock_api):
        from ww.agent import title_agent

        mock_api.return_value = "  My Great Title  "
        result = title_agent.generate_title_with_ai("Some content here")
        self.assertEqual(result, "My Great Title")
        mock_api.assert_called_once()

    @patch("ww.agent.title_agent.call_openrouter_api")
    def test_generate_title_with_ai_custom_prompt(self, mock_api):
        from ww.agent import title_agent

        mock_api.return_value = "Custom Title"
        result = title_agent.generate_title_with_ai(
            "content", custom_prompt="Do something"
        )
        self.assertEqual(result, "Custom Title")
        call_args = mock_api.call_args[0][0]
        self.assertIn("Do something", call_args)

    @patch("ww.agent.title_agent.call_openrouter_api")
    def test_generate_title_with_ai_truncates_long_content(self, mock_api):
        from ww.agent import title_agent

        mock_api.return_value = "Title"
        long_content = "x" * 2000
        title_agent.generate_title_with_ai(long_content)
        call_args = mock_api.call_args[0][0]
        self.assertIn("...", call_args)

    @patch("ww.agent.title_agent.call_openrouter_api")
    def test_generate_title_with_ai_api_error(self, mock_api):
        from ww.agent import title_agent

        mock_api.side_effect = Exception("API error")
        result = title_agent.generate_title_with_ai("content")
        self.assertIsNone(result)

    def test_validate_title_valid(self):
        from ww.agent import title_agent

        self.assertTrue(title_agent.validate_title("Simple Title"))

    def test_validate_title_empty_raises(self):
        from ww.agent import title_agent

        with self.assertRaises(ValueError):
            title_agent.validate_title("")

    def test_validate_title_none_raises(self):
        from ww.agent import title_agent

        with self.assertRaises(ValueError):
            title_agent.validate_title(None)

    def test_validate_title_too_long(self):
        from ww.agent import title_agent

        with self.assertRaises(ValueError):
            title_agent.validate_title("x" * 101)

    def test_validate_title_markdown_raises(self):
        from ww.agent import title_agent

        with self.assertRaises(ValueError):
            title_agent.validate_title("**bold**")

    def test_validate_title_quotes_raises(self):
        from ww.agent import title_agent

        with self.assertRaises(ValueError):
            title_agent.validate_title('"quoted"')

    def test_validate_title_special_chars_raises(self):
        from ww.agent import title_agent

        with self.assertRaises(ValueError):
            title_agent.validate_title("title <with> brackets")


class TestGrammarAgent(unittest.TestCase):
    @patch("ww.agent.grammar_agent.call_openrouter_api")
    def test_fix_grammar_with_ai_success(self, mock_api):
        from ww.agent import grammar_agent

        mock_api.return_value = "  Fixed content  "
        result = grammar_agent.fix_grammar_with_ai("BAd grammar")
        self.assertEqual(result, "Fixed content")

    @patch("ww.agent.grammar_agent.call_openrouter_api")
    def test_fix_grammar_with_ai_error(self, mock_api):
        from ww.agent import grammar_agent

        mock_api.side_effect = Exception("fail")
        result = grammar_agent.fix_grammar_with_ai("content")
        self.assertIsNone(result)

    @patch("ww.agent.grammar_agent.fix_grammar_with_ai")
    def test_process_file_success(self, mock_fix):
        from ww.agent import grammar_agent

        mock_fix.return_value = "fixed text"
        with patch("builtins.open", mock_open(read_data="original text")):
            result = grammar_agent.process_file("test.md")
        self.assertEqual(result, "fixed text")

    @patch("ww.agent.grammar_agent.fix_grammar_with_ai")
    def test_process_file_ai_returns_none(self, mock_fix):
        from ww.agent import grammar_agent

        mock_fix.return_value = None
        with patch("builtins.open", mock_open(read_data="content")):
            result = grammar_agent.process_file("test.md")
        self.assertIsNone(result)


class TestSummaryAgent(unittest.TestCase):
    @patch("ww.agent.summary_agent.call_openrouter_api")
    def test_generate_summary_success(self, mock_api):
        from ww.agent import summary_agent

        mock_api.return_value = "  A summary  "
        result = summary_agent.generate_summary_with_ai("Long content")
        self.assertEqual(result, "A summary")

    @patch("ww.agent.summary_agent.call_openrouter_api")
    def test_generate_summary_error(self, mock_api):
        from ww.agent import summary_agent

        mock_api.side_effect = Exception("fail")
        result = summary_agent.generate_summary_with_ai("content")
        self.assertIsNone(result)

    @patch("ww.agent.summary_agent.generate_summary_with_ai")
    def test_process_file_success(self, mock_gen):
        from ww.agent import summary_agent

        mock_gen.return_value = "summary text"
        with patch("builtins.open", mock_open(read_data="content")):
            result = summary_agent.process_file("test.md")
        self.assertEqual(result, "summary text")


class TestFormatAgent(unittest.TestCase):
    @patch.dict(
        "sys.modules",
        {
            "ww.llm.openrouter_client": MagicMock(
                call_openrouter_api=MagicMock(),
                MODEL_MAPPING={"deepseek-v3.2": "deepseek/deepseek-v3.2"},
            )
        },
    )
    @patch("subprocess.run")
    def test_format_script_python(self, mock_run):
        import sys

        # Force reimport
        sys.modules.pop("ww.agent.format_agent", None)
        from ww.agent import format_agent

        mock_run.return_value = MagicMock(stdout="formatted", stderr="")
        result = format_agent.format_script("test.py")
        self.assertIn("formatted", result)
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "black")

    @patch.dict(
        "sys.modules",
        {
            "ww.llm.openrouter_client": MagicMock(
                call_openrouter_api=MagicMock(),
                MODEL_MAPPING={"deepseek-v3.2": "deepseek/deepseek-v3.2"},
            )
        },
    )
    @patch("subprocess.run")
    def test_format_script_rust(self, mock_run):
        import sys

        sys.modules.pop("ww.agent.format_agent", None)
        from ww.agent import format_agent

        mock_run.return_value = MagicMock(stdout="ok", stderr="")
        result = format_agent.format_script("test.rs")
        self.assertIn("ok", result)
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "rustfmt")

    @patch.dict(
        "sys.modules",
        {
            "ww.llm.openrouter_client": MagicMock(
                call_openrouter_api=MagicMock(),
                MODEL_MAPPING={"deepseek-v3.2": "deepseek/deepseek-v3.2"},
            )
        },
    )
    def test_format_script_unsupported(self):
        import sys

        sys.modules.pop("ww.agent.format_agent", None)
        from ww.agent import format_agent

        result = format_agent.format_script("test.txt")
        self.assertIn("Unsupported", result)

    @patch.dict(
        "sys.modules",
        {
            "ww.llm.openrouter_client": MagicMock(
                call_openrouter_api=MagicMock(),
                MODEL_MAPPING={"deepseek-v3.2": "deepseek/deepseek-v3.2"},
            )
        },
    )
    @patch("subprocess.run")
    def test_format_script_exception(self, mock_run):
        import sys

        sys.modules.pop("ww.agent.format_agent", None)
        from ww.agent import format_agent

        mock_run.side_effect = FileNotFoundError("not found")
        result = format_agent.format_script("test.py")
        self.assertIn("not found", result)


class TestNamingAgent(unittest.TestCase):
    @patch("ww.agent.naming_agent.call_openrouter_api")
    def test_get_name_suggestions(self, mock_api):
        from ww.agent import naming_agent

        mock_api.return_value = (
            "name1.py\nname2.py\nname3.py\nname4.py\nname5.py\nextra"
        )
        with patch("builtins.open", mock_open(read_data="file content")):
            result = naming_agent.get_name_suggestions("/path/to/file.py")
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], "name1.py")

    def test_is_text_file_true(self):
        from ww.agent import naming_agent

        with patch("builtins.open", mock_open(read_data="readable text")):
            result = naming_agent.is_text_file("test.txt")
        self.assertTrue(result)

    def test_is_text_file_false(self):
        from ww.agent import naming_agent

        m = mock_open()
        m.return_value.read.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "err")
        with patch("builtins.open", m):
            result = naming_agent.is_text_file("test.bin")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
