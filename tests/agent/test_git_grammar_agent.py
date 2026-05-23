import unittest
from unittest.mock import patch, mock_open
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


from ww.agent.git_grammar_agent import (
    fix_grammar_with_ai,
    process_file,
)


class TestFixGrammarWithAi(unittest.TestCase):
    @patch("ww.agent.git_grammar_agent.validate_grammar_fix", return_value=True)
    @patch("ww.agent.git_grammar_agent.call_openrouter_api")
    def test_success(self, mock_api, mock_validate):
        mock_api.return_value = "The cat sat on the mat."
        result = fix_grammar_with_ai("The cat sit on the mat.")
        self.assertEqual(result, "The cat sat on the mat.")

    @patch("ww.agent.git_grammar_agent.validate_grammar_fix", return_value=True)
    @patch("ww.agent.git_grammar_agent.call_openrouter_api")
    def test_strips_code_blocks(self, mock_api, mock_validate):
        mock_api.return_value = "```markdown\nFixed content here\n```"
        result = fix_grammar_with_ai("Original content here.")
        self.assertEqual(result, "Fixed content here")

    @patch("ww.agent.git_grammar_agent.validate_grammar_fix")
    @patch("ww.agent.git_grammar_agent.call_openrouter_api")
    def test_api_error(self, mock_api, mock_validate):
        mock_api.side_effect = Exception("API Error")
        result = fix_grammar_with_ai("Some content.")
        self.assertIsNone(result)

    @patch("ww.agent.git_grammar_agent.validate_grammar_fix")
    @patch("ww.agent.git_grammar_agent.call_openrouter_api")
    def test_validation_failure(self, mock_api, mock_validate):
        mock_api.return_value = "Fixed content."
        mock_validate.side_effect = Exception("Validation failed")
        result = fix_grammar_with_ai("Some content.")
        self.assertIsNone(result)

    @patch("ww.agent.git_grammar_agent.validate_grammar_fix", return_value=True)
    @patch("ww.agent.git_grammar_agent.call_openrouter_api")
    def test_no_code_blocks_just_stripped(self, mock_api, mock_validate):
        mock_api.return_value = "  Clean response with whitespace  "
        result = fix_grammar_with_ai("Content.")
        self.assertEqual(result, "Clean response with whitespace")


class TestProcessFile(unittest.TestCase):
    @patch("ww.agent.git_grammar_agent.fix_grammar_with_ai")
    @patch("ww.agent.git_grammar_agent.extract_changed_content")
    @patch("ww.agent.git_grammar_agent.get_git_diff_lines")
    @patch("builtins.open", new_callable=mock_open, read_data="Original content here.")
    def test_dry_run(self, mock_file, mock_diff, mock_extract, mock_fix):
        mock_diff.return_value = {1, 2}
        mock_extract.return_value = "Original content here."
        mock_fix.return_value = "Fixed content here."

        result = process_file("test.md", dry_run=True)
        self.assertEqual(result, "Fixed content here.")
        # File should be opened for reading (abs path used internally)
        read_call = mock_file.call_args_list[0]
        self.assertIn("test.md", read_call[0][0])
        self.assertEqual(read_call[0][1], "r")

    @patch("ww.agent.git_grammar_agent.apply_grammar_fixes_to_original")
    @patch("ww.agent.git_grammar_agent.fix_grammar_with_ai")
    @patch("ww.agent.git_grammar_agent.extract_changed_content")
    @patch("ww.agent.git_grammar_agent.get_git_diff_lines")
    @patch("builtins.open", new_callable=mock_open, read_data="Original content here.")
    def test_normal_run(self, mock_file, mock_diff, mock_extract, mock_fix, mock_apply):
        mock_diff.return_value = {1}
        mock_extract.return_value = "Original content here."
        mock_fix.return_value = "Fixed content here."
        mock_apply.return_value = "Applied fixed content."

        result = process_file("test.md", dry_run=False)
        self.assertEqual(result, "Fixed content here.")

    @patch("ww.agent.git_grammar_agent.get_git_diff_lines")
    def test_no_changes(self, mock_diff):
        mock_diff.return_value = set()
        result = process_file("test.md")
        self.assertIsNone(result)

    @patch("ww.agent.git_grammar_agent.fix_grammar_with_ai")
    @patch("ww.agent.git_grammar_agent.extract_changed_content")
    @patch("ww.agent.git_grammar_agent.get_git_diff_lines")
    @patch("builtins.open", new_callable=mock_open, read_data="Original content here.")
    def test_empty_extracted_content(
        self, mock_file, mock_diff, mock_extract, mock_fix
    ):
        mock_diff.return_value = {1}
        mock_extract.return_value = "   "
        result = process_file("test.md")
        self.assertIsNone(result)

    @patch("ww.agent.git_grammar_agent.fix_grammar_with_ai")
    @patch("ww.agent.git_grammar_agent.extract_changed_content")
    @patch("ww.agent.git_grammar_agent.get_git_diff_lines")
    @patch("builtins.open", new_callable=mock_open, read_data="Content")
    def test_ai_returns_none(self, mock_file, mock_diff, mock_extract, mock_fix):
        mock_diff.return_value = {1}
        mock_extract.return_value = "Content"
        mock_fix.return_value = None
        result = process_file("test.md")
        self.assertIsNone(result)

    @patch("builtins.open", side_effect=Exception("File error"))
    def test_file_error(self, mock_file):
        result = process_file("missing.md")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
