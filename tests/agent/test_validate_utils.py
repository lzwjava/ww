import os
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.agent.validate_utils import (
    validate_grammar_fix,
    validate_markdown_syntax,
    validate_content_structure,
)


class TestValidateGrammarFix(unittest.TestCase):
    def test_passes_for_identical_content(self):
        content = "Hello world. This is a test."
        self.assertTrue(validate_grammar_fix(content, content))

    def test_passes_for_minor_grammar_fix(self):
        original = "Hello world. This are a test."
        fixed = "Hello world. This is a test."
        self.assertTrue(validate_grammar_fix(original, fixed))

    def test_raises_on_line_count_change_too_much(self):
        original = "Line 1\nLine 2\nLine 3\n"
        fixed = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\n"
        with self.assertRaises(Exception) as ctx:
            validate_grammar_fix(original, fixed, max_line_diff=1)
        self.assertIn("Line count changed", str(ctx.exception))

    def test_raises_on_length_change_too_much(self):
        original = "Hello."
        fixed = "Hello world this is a much longer sentence with extra words added."
        with self.assertRaises(Exception) as ctx:
            validate_grammar_fix(original, fixed, max_length_change=0.1)
        self.assertIn("Content length changed", str(ctx.exception))

    def test_raises_on_added_bold_markdown(self):
        original = "A long enough sentence to avoid length issues here."
        fixed = "A long enough sentence to avoid **length** issues here."
        with self.assertRaises(Exception) as ctx:
            validate_grammar_fix(original, fixed, max_length_change=1.0)
        self.assertIn("bold", str(ctx.exception))

    def test_raises_on_added_italic_markdown(self):
        original = "Hello world."
        fixed = "Hello *world*."
        with self.assertRaises(Exception) as ctx:
            validate_grammar_fix(original, fixed)
        self.assertIn("italic", str(ctx.exception))

    def test_empty_original_no_length_check(self):
        original = ""
        fixed = "ok"
        self.assertTrue(validate_grammar_fix(original, fixed))

    def test_custom_thresholds(self):
        original = "a\nb\nc\n" * 5
        fixed = ("a\nb\nc\n" * 5) + "d\n"
        # max_line_diff=2 should pass; also relax length change
        self.assertTrue(
            validate_grammar_fix(
                original, fixed, max_line_diff=2, max_length_change=0.5
            )
        )


class TestValidateMarkdownSyntax(unittest.TestCase):
    def test_passes_for_identical_content(self):
        content = "Some text without markdown."
        self.assertTrue(validate_markdown_syntax(content, content))

    def test_raises_on_added_bold(self):
        original = "Hello world"
        fixed = "Hello **world**"
        with self.assertRaises(Exception) as ctx:
            validate_markdown_syntax(original, fixed)
        self.assertIn("bold", str(ctx.exception))

    def test_raises_on_added_italic(self):
        original = "Hello world"
        fixed = "Hello *world*"
        with self.assertRaises(Exception) as ctx:
            validate_markdown_syntax(original, fixed)
        self.assertIn("italic", str(ctx.exception))

    def test_raises_on_significant_backtick_increase(self):
        original = "no code here"
        fixed = "no `code` `here` `now`"
        with self.assertRaises(Exception) as ctx:
            validate_markdown_syntax(original, fixed)
        self.assertIn("'", str(ctx.exception))

    def test_same_markdown_count_passes(self):
        content = "**bold** and *italic*"
        self.assertTrue(validate_markdown_syntax(content, content))

    def test_existing_bold_kept_passes(self):
        original = "**bold** text"
        fixed = "**bold** text."
        self.assertTrue(validate_markdown_syntax(original, fixed))


class TestValidateContentStructure(unittest.TestCase):
    def test_passes_for_identical_content(self):
        content = "First sentence. Second sentence."
        self.assertTrue(validate_content_structure(content, content))

    def test_raises_on_paragraph_structure_change(self):
        original = "Para 1.\n\nPara 2.\n"
        fixed = "Para 1.\n\n\n\nPara 2.\n"
        with self.assertRaises(Exception) as ctx:
            validate_content_structure(original, fixed)
        self.assertIn("Paragraph structure", str(ctx.exception))

    def test_raises_on_sentence_count_change(self):
        original = "One sentence."
        fixed = "One sentence! Two sentences? Three more. Four! Five?"
        with self.assertRaises(Exception) as ctx:
            validate_content_structure(original, fixed)
        self.assertIn("Sentence structure", str(ctx.exception))

    def test_passes_with_one_empty_line_diff(self):
        original = "A.\n\nB.\n"
        fixed = "A.\nB.\n"
        # 1 empty line diff is allowed
        self.assertTrue(validate_content_structure(original, fixed))

    def test_passes_with_minor_sentence_change(self):
        original = "Hello. World."
        fixed = "Hello! World."
        # 2 to 2 sentences
        self.assertTrue(validate_content_structure(original, fixed))


if __name__ == "__main__":
    unittest.main()
