import unittest
from unittest.mock import patch, mock_open
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


from ww.agent.toc_agent import (
    validate_toc,
    generate_toc_with_ai,
    find_existing_toc,
    process_file,
)


class TestValidateToc(unittest.TestCase):
    def test_valid_toc(self):
        toc = (
            "### Table of Contents\n\n"
            "1. [First Section](#first-section)\n"
            "   - Key point one\n"
            "   - Key point two\n"
            "2. [Second Section](#second-section)\n"
        )
        self.assertTrue(validate_toc(toc))

    def test_empty_toc(self):
        with self.assertRaises(ValueError) as ctx:
            validate_toc("")
        self.assertIn("empty", str(ctx.exception))

    def test_none_toc(self):
        with self.assertRaises(ValueError):
            validate_toc(None)

    def test_wrong_header(self):
        toc = "## Wrong Header\n1. [Title](#title)\n"
        with self.assertRaises(ValueError) as ctx:
            validate_toc(toc)
        self.assertIn("Table of Contents", str(ctx.exception))

    def test_no_numbered_items(self):
        toc = "### Table of Contents\n\nSome text without items.\n"
        with self.assertRaises(ValueError) as ctx:
            validate_toc(toc)
        self.assertIn("at least one", str(ctx.exception))

    def test_invalid_anchor(self):
        toc = "### Table of Contents\n\n1. [Title](bad-anchor)\n"
        with self.assertRaises(ValueError):
            validate_toc(toc)

    def test_valid_with_bold_format(self):
        toc = "### Table of Contents\n\n1. **[First Section](#first-section)**\n"
        self.assertTrue(validate_toc(toc))


class TestGenerateTocWithAi(unittest.TestCase):
    @patch("ww.agent.toc_agent.call_openrouter_api")
    def test_success(self, mock_api):
        mock_api.return_value = "### Table of Contents\n\n1. [Section](#section)\n"
        result = generate_toc_with_ai("# Content\n\nSome text.")
        self.assertIn("Table of Contents", result)

    @patch("ww.agent.toc_agent.call_openrouter_api")
    def test_strips_bold_formatting(self, mock_api):
        mock_api.return_value = "1. **[Title](#title)**"
        result = generate_toc_with_ai("content")
        self.assertNotIn("**[", result)
        self.assertNotIn("]**", result)

    @patch("ww.agent.toc_agent.call_openrouter_api")
    def test_code_blocks_returns_none(self, mock_api):
        mock_api.return_value = "```\n### Table of Contents\n1. [Title](#title)\n```"
        result = generate_toc_with_ai("content")
        self.assertIsNone(result)

    @patch("ww.agent.toc_agent.call_openrouter_api")
    def test_api_error(self, mock_api):
        mock_api.side_effect = Exception("API Error")
        result = generate_toc_with_ai("content")
        self.assertIsNone(result)


class TestFindExistingToc(unittest.TestCase):
    def test_find_toc(self):
        content = (
            "Some text\n### Table of Contents\n\n1. [Title](#title)\n\n## Next Section"
        )
        start, end = find_existing_toc(content)
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

    def test_no_toc(self):
        content = "No TOC here\n## Section"
        start, end = find_existing_toc(content)
        self.assertIsNone(start)
        self.assertIsNone(end)

    def test_toc_at_end(self):
        content = "Text\n### Table of Contents\n\n1. [Title](#title)"
        start, end = find_existing_toc(content)
        self.assertIsNotNone(start)
        self.assertEqual(end, len(content))


class TestProcessFile(unittest.TestCase):
    @patch("ww.agent.toc_agent.generate_toc_with_ai")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="---\ntitle: Test\n---\n\n# Content\n\nSome text.",
    )
    def test_process_file_success(self, mock_file, mock_ai):
        mock_ai.return_value = "### Table of Contents\n\n1. [Content](#content)\n"
        result = process_file("test.md")
        self.assertIsNotNone(result)
        self.assertIn("Table of Contents", result)

    @patch("ww.agent.toc_agent.generate_toc_with_ai")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="---\ntitle: Test\n---\n\n# Content",
    )
    def test_process_file_ai_returns_none(self, mock_file, mock_ai):
        mock_ai.return_value = None
        result = process_file("test.md")
        self.assertIsNone(result)

    @patch("ww.agent.toc_agent.generate_toc_with_ai")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="---\ntitle: Test\n---\n\n# Content",
    )
    def test_process_file_output_only(self, mock_file, mock_ai):
        mock_ai.return_value = "### Table of Contents\n\n1. [Content](#content)\n"
        result = process_file("test.md", output_only=True)
        self.assertIsNotNone(result)

    @patch("ww.agent.toc_agent.generate_toc_with_ai")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="---\ntitle: Test\n---\n\n# Content",
    )
    def test_process_file_with_update(self, mock_file, mock_ai):
        mock_ai.return_value = "### Table of Contents\n\n1. [Content](#content)\n"
        result = process_file("test.md", update=True)
        self.assertIsNotNone(result)

    @patch("builtins.open", side_effect=Exception("File error"))
    def test_process_file_read_error(self, mock_file):
        result = process_file("missing.md")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
