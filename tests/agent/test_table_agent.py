import unittest
from unittest.mock import patch, mock_open
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


from ww.agent.table_agent import (
    find_tables_in_content,
    analyze_table_complexity,
    optimize_table_with_ai,
    process_file,
)


class TestFindTablesInContent(unittest.TestCase):
    def test_single_table(self):
        content = (
            "Some text\n"
            "| Header1 | Header2 |\n"
            "|---------|--------|\n"
            "| Cell 1  | Cell 2  |\n"
            "\n"
            "More text"
        )
        tables = find_tables_in_content(content)
        self.assertEqual(len(tables), 1)
        self.assertIn("Header1", tables[0]["content"])

    def test_no_tables(self):
        content = "Just plain text\nNo tables here."
        tables = find_tables_in_content(content)
        self.assertEqual(len(tables), 0)

    def test_two_tables(self):
        content = (
            "Text\n"
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |\n"
            "\n"
            "Middle\n"
            "| C | D |\n"
            "|---|---|\n"
            "| 3 | 4 |\n"
        )
        tables = find_tables_in_content(content)
        self.assertEqual(len(tables), 2)

    def test_table_at_end(self):
        content = "Text\n| A | B |\n|---|---|\n| 1 | 2 |"
        tables = find_tables_in_content(content)
        self.assertEqual(len(tables), 1)

    def test_table_without_header_above(self):
        content = "|---|---|\n| 1 | 2 |\n"
        tables = find_tables_in_content(content)
        self.assertEqual(len(tables), 1)


class TestAnalyzeTableComplexity(unittest.TestCase):
    def test_mobile_friendly(self):
        table = "| A | B |\n|---|---|\n| 1 | 2 |"
        needs_opt, reason = analyze_table_complexity(table)
        self.assertFalse(needs_opt)
        self.assertIn("mobile-friendly", reason)

    def test_too_many_columns(self):
        table = "| A | B | C | D | E |\n|---|---|---|---|---|\n| 1 | 2 | 3 | 4 | 5 |"
        needs_opt, reason = analyze_table_complexity(table)
        self.assertTrue(needs_opt)
        self.assertIn("columns", reason)

    def test_long_content(self):
        long_cell = "x" * 60
        table = f"| A | B |\n|---|---|\n| {long_cell} | 2 |"
        needs_opt, reason = analyze_table_complexity(table)
        self.assertTrue(needs_opt)
        self.assertIn("long content", reason)

    def test_not_valid_table(self):
        table = "just one line"
        needs_opt, reason = analyze_table_complexity(table)
        self.assertFalse(needs_opt)
        self.assertIn("Not a valid", reason)


class TestOptimizeTableWithAi(unittest.TestCase):
    @patch("ww.agent.table_agent.call_openrouter_api")
    def test_success(self, mock_api):
        mock_api.return_value = "| A |\n|---|\n| 1 |\n\n| B |\n|---|\n| 2 |"
        result = optimize_table_with_ai("| A | B |\n|---|---|\n| 1 | 2 |")
        self.assertIn("| A |", result)

    @patch("ww.agent.table_agent.call_openrouter_api")
    def test_strips_code_blocks(self, mock_api):
        mock_api.return_value = "```\n| A |\n|---|\n| 1 |\n```"
        result = optimize_table_with_ai("| A | B |\n|---|---|\n| 1 | 2 |")
        self.assertIn("| A |", result)
        self.assertNotIn("```", result)

    @patch("ww.agent.table_agent.call_openrouter_api")
    def test_api_error(self, mock_api):
        mock_api.side_effect = Exception("API error")
        result = optimize_table_with_ai("| A | B |\n|---|---|\n| 1 | 2 |")
        self.assertIsNone(result)


class TestProcessFile(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="No tables here.")
    def test_no_tables(self, mock_file):
        result = process_file("test.md")
        self.assertIsNone(result)

    @patch("ww.agent.table_agent.optimize_table_with_ai")
    @patch("ww.agent.table_agent.analyze_table_complexity")
    @patch("ww.agent.table_agent.find_tables_in_content")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="| A | B | C | D | E |\n|---|---|---|---|---|\n| 1 | 2 | 3 | 4 | 5 |",
    )
    def test_optimize_needed(self, mock_file, mock_find, mock_analyze, mock_optimize):
        mock_find.return_value = [
            {
                "start": 0,
                "end": 2,
                "content": "table",
                "lines": [
                    "| A | B | C | D | E |",
                    "|---|---|---|---|---|",
                    "| 1 | 2 | 3 | 4 | 5 |",
                ],
            }
        ]
        mock_analyze.return_value = (True, "Too many columns")
        mock_optimize.return_value = "| A |\n|---|\n| 1 |"

        result = process_file("test.md")
        self.assertIsNotNone(result)

    @patch("ww.agent.table_agent.analyze_table_complexity")
    @patch("ww.agent.table_agent.find_tables_in_content")
    @patch("builtins.open", new_callable=mock_open, read_data="| A |\n|---|\n| 1 |")
    def test_already_friendly(self, mock_file, mock_find, mock_analyze):
        mock_find.return_value = [
            {
                "start": 0,
                "end": 2,
                "content": "table",
                "lines": ["| A |", "|---|", "| 1 |"],
            }
        ]
        mock_analyze.return_value = (False, "mobile-friendly")
        result = process_file("test.md")
        self.assertIsNotNone(result)

    @patch("ww.agent.table_agent.optimize_table_with_ai")
    @patch("ww.agent.table_agent.analyze_table_complexity")
    @patch("ww.agent.table_agent.find_tables_in_content")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="| A | B | C | D | E |\n|---|---|---|---|---|\n| 1 | 2 | 3 | 4 | 5 |",
    )
    def test_optimize_returns_none(
        self, mock_file, mock_find, mock_analyze, mock_optimize
    ):
        mock_find.return_value = [
            {
                "start": 0,
                "end": 2,
                "content": "table",
                "lines": [
                    "| A | B | C | D | E |",
                    "|---|---|---|---|---|",
                    "| 1 | 2 | 3 | 4 | 5 |",
                ],
            }
        ]
        mock_analyze.return_value = (True, "Too many columns")
        mock_optimize.return_value = None
        result = process_file("test.md")
        self.assertIsNotNone(result)

    @patch("builtins.open", side_effect=Exception("File error"))
    def test_file_error(self, mock_file):
        result = process_file("missing.md")
        self.assertIsNone(result)

    @patch("ww.agent.table_agent.analyze_table_complexity")
    @patch("ww.agent.table_agent.find_tables_in_content")
    @patch("builtins.open", new_callable=mock_open, read_data="| A |\n|---|\n| 1 |")
    def test_output_only(self, mock_file, mock_find, mock_analyze):
        mock_find.return_value = [
            {
                "start": 0,
                "end": 2,
                "content": "table",
                "lines": ["| A |", "|---|", "| 1 |"],
            }
        ]
        mock_analyze.return_value = (False, "mobile-friendly")
        result = process_file("test.md", output_only=True)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
