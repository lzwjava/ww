import os
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.agent.code_validation_utils import (
    validate_python_syntax,
    check_main_guard_pattern,
    compare_code_lengths,
    count_non_empty_lines,
    extract_functions_from_code,
    get_function_code_block,
    validate_function_sizes,
    validate_code_quality,
)


class TestValidatePythonSyntax(unittest.TestCase):
    def test_valid_syntax(self):
        code = "x = 1\nprint(x)\n"
        ok, msg = validate_python_syntax(code)
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_invalid_syntax(self):
        code = "def foo(\n"
        ok, msg = validate_python_syntax(code)
        self.assertFalse(ok)
        self.assertIn("Syntax error", msg)

    def test_empty_string(self):
        ok, msg = validate_python_syntax("")
        self.assertTrue(ok)
        self.assertEqual(msg, "")


class TestCheckMainGuardPattern(unittest.TestCase):
    def test_has_guard_single_quotes(self):
        code = "if __name__ == '__main__':\n    pass\n"
        ok, msg = check_main_guard_pattern(code)
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_has_guard_double_quotes(self):
        code = 'if __name__ == "__main__":\n    pass\n'
        ok, msg = check_main_guard_pattern(code)
        self.assertTrue(ok)

    def test_missing_guard(self):
        code = "print('hello')\n"
        ok, msg = check_main_guard_pattern(code)
        self.assertFalse(ok)
        self.assertIn("Missing", msg)

    def test_custom_pattern(self):
        code = "def main():\n    pass\n"
        ok, msg = check_main_guard_pattern(code, pattern=r"def main\(\):")
        self.assertTrue(ok)


class TestCompareCodeLengths(unittest.TestCase):
    def test_similar_lengths_pass(self):
        original = "line1\nline2\nline3\n"
        new_code = "line1\nline2\nline3 updated\n"
        ok, msg = compare_code_lengths(original, new_code)
        self.assertTrue(ok)

    def test_too_much_change_fails(self):
        original = "line1\nline2\n"
        new_code = "line1\nline2\nline3\nline4\nline5\nline6\n"
        ok, msg = compare_code_lengths(original, new_code, max_change_ratio=0.5)
        self.assertFalse(ok)
        self.assertIn("changed too much", msg)

    def test_empty_original_returns_true(self):
        ok, msg = compare_code_lengths("", "something")
        self.assertTrue(ok)

    def test_custom_max_change_ratio(self):
        original = "a\nb\nc\n"
        new_code = "a\nb\nc\nd\ne\n"
        # ratio = 2/3 ≈ 0.67; should fail with 0.5, pass with 0.8
        ok_fail, _ = compare_code_lengths(original, new_code, max_change_ratio=0.5)
        ok_pass, _ = compare_code_lengths(original, new_code, max_change_ratio=0.8)
        self.assertFalse(ok_fail)
        self.assertTrue(ok_pass)


class TestCountNonEmptyLines(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(count_non_empty_lines("a\nb\nc\n"), 3)

    def test_with_blank_lines(self):
        self.assertEqual(count_non_empty_lines("a\n\nb\n\n"), 2)

    def test_whitespace_only_lines(self):
        self.assertEqual(count_non_empty_lines("a\n   \tb\n"), 2)

    def test_empty_string(self):
        self.assertEqual(count_non_empty_lines(""), 0)  # "".strip() is falsy


class TestExtractFunctionsFromCode(unittest.TestCase):
    def test_single_function(self):
        code = "def foo(x, y):\n    return x + y\n"
        self.assertEqual(extract_functions_from_code(code), ["foo"])

    def test_multiple_functions(self):
        code = "def bar():\n    pass\ndef baz(a):\n    pass\n"
        self.assertEqual(extract_functions_from_code(code), ["bar", "baz"])

    def test_no_functions(self):
        code = "x = 1\nprint(x)\n"
        self.assertEqual(extract_functions_from_code(code), [])


class TestGetFunctionCodeBlock(unittest.TestCase):
    def test_extract_first_function(self):
        code = "def foo():\n    return 1\ndef bar():\n    return 2\n"
        result = get_function_code_block(code, "foo", ["foo", "bar"])
        self.assertIn("def foo", result)
        self.assertNotIn("def bar", result)

    def test_extract_last_function(self):
        code = "def foo():\n    return 1\ndef bar():\n    return 2\n"
        result = get_function_code_block(code, "bar", ["foo", "bar"])
        self.assertIn("def bar", result)
        self.assertIn("return 2", result)

    def test_function_not_found(self):
        code = "def foo():\n    pass\n"
        result = get_function_code_block(code, "missing", ["foo"])
        self.assertEqual(result, "")


class TestValidateFunctionSizes(unittest.TestCase):
    def test_small_functions_pass(self):
        code = "def foo():\n    x = 1\n    return x\ndef bar():\n    pass\n"
        ok, msg = validate_function_sizes(code, max_lines=30)
        self.assertTrue(ok)

    def test_oversized_function_fails(self):
        lines = "\n".join([f"    x{i} = {i}" for i in range(50)])
        code = f"def big():\n{lines}\ndef small():\n    pass\n"
        ok, msg = validate_function_sizes(code, max_lines=10)
        self.assertFalse(ok)
        self.assertIn("big", msg)
        self.assertIn("lines", msg)

    def test_no_functions(self):
        ok, msg = validate_function_sizes("x = 1\n")
        self.assertTrue(ok)


class TestValidateCodeQuality(unittest.TestCase):
    def _good_code(self):
        return (
            "import os\n\n"
            "def foo():\n"
            "    return 1\n\n"
            "if __name__ == '__main__':\n"
            "    foo()\n"
        )

    def test_passes_all_defaults(self):
        ok, msg = validate_code_quality(self._good_code(), self._good_code())
        self.assertTrue(ok)
        self.assertIn("passed", msg)

    def test_fails_on_syntax_error(self):
        refactored = "def foo(:\n    pass\n"
        ok, msg = validate_code_quality(self._good_code(), refactored)
        self.assertFalse(ok)
        self.assertIn("Syntax error", msg)

    def test_fails_on_missing_main_guard(self):
        refactored = "import os\ndef foo():\n    return 1\n"
        ok, msg = validate_code_quality(self._good_code(), refactored)
        self.assertFalse(ok)
        self.assertIn("Missing", msg)

    def test_custom_options_skip_checks(self):
        bad_code = "x = 1\n"
        options = {
            "check_syntax": False,
            "check_main_guard": False,
            "check_length_similarity": False,
            "check_function_sizes": False,
        }
        ok, msg = validate_code_quality(self._good_code(), bad_code, options)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
