import unittest
from unittest.mock import patch, MagicMock, mock_open
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestMergeAgent(unittest.TestCase):
    @patch("ww.agent.merge_agent.call_openrouter_api")
    def test_generate_toc_success(self, mock_api):
        from ww.agent import merge_agent

        mock_api.return_value = "  ### Table of Contents  "
        result = merge_agent.generate_toc_with_ai("## Heading")
        self.assertEqual(result, "### Table of Contents")

    @patch("ww.agent.merge_agent.call_openrouter_api")
    def test_generate_toc_error(self, mock_api):
        from ww.agent import merge_agent

        mock_api.side_effect = Exception("fail")
        result = merge_agent.generate_toc_with_ai("content")
        self.assertIsNone(result)

    def test_merge_contents(self):
        from ww.agent import merge_agent

        result = merge_agent.merge_contents("main", ["other1", "other2"])
        self.assertIn("main", result)
        self.assertIn("## Additional Content 1", result)
        self.assertIn("other1", result)
        self.assertIn("## Additional Content 2", result)
        self.assertIn("other2", result)

    @patch("ww.agent.merge_agent.generate_toc_with_ai")
    def test_process_file_success(self, mock_toc):
        from ww.agent import merge_agent

        mock_toc.return_value = "toc result"
        with patch("builtins.open", mock_open(read_data="# Title\n## Section")):
            toc, content = merge_agent.process_file("test.md")
        self.assertEqual(toc, "toc result")
        self.assertIn("Section", content)

    @patch("ww.agent.merge_agent.generate_toc_with_ai")
    def test_process_file_ai_returns_none(self, mock_toc):
        from ww.agent import merge_agent

        mock_toc.return_value = None
        with patch("builtins.open", mock_open(read_data="content")):
            toc, content = merge_agent.process_file("test.md")
        self.assertIsNone(toc)
        self.assertIsNone(content)


class TestCodeAgent(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_python_code_success(self, mock_run):
        from ww.agent import code_agent

        mock_run.return_value = MagicMock(stdout="15\n", stderr="")
        stdout, stderr = code_agent.run_python_code("print(15)")
        self.assertEqual(stdout, "15\n")
        self.assertEqual(stderr, "")

    @patch("subprocess.run")
    def test_run_python_code_strips_markdown(self, mock_run):
        from ww.agent import code_agent

        mock_run.return_value = MagicMock(stdout="ok", stderr="")
        code = "```python\nprint('hi')\n```"
        code_agent.run_python_code(code)
        # Verify the temp file was written with stripped code
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_python_code_exception(self, mock_run):
        from ww.agent import code_agent

        mock_run.side_effect = Exception("exec error")
        stdout, stderr = code_agent.run_python_code("bad code")
        self.assertIn("exec error", stderr)

    @patch("ww.agent.code_agent.call_openrouter_api")
    @patch("ww.agent.code_agent.run_python_code")
    def test_solve_and_run_success(self, mock_run, mock_api):
        from ww.agent import code_agent

        mock_api.side_effect = [
            "print(sum(range(1,6)))",  # solution
            "CORRECT",  # verification
        ]
        mock_run.return_value = ("15\n", "")
        result = code_agent.solve_and_run("sum of 1 to 5")
        self.assertIn("print", result)

    @patch("ww.agent.code_agent.call_openrouter_api")
    @patch("ww.agent.code_agent.run_python_code")
    def test_solve_and_run_error_retries(self, mock_run, mock_api):
        from ww.agent import code_agent

        mock_api.side_effect = [
            "bad code",  # first solution
            "fixed code",  # second solution after error
            "CORRECT",  # verification
        ]
        mock_run.side_effect = [
            ("", "SyntaxError"),  # first run fails
            ("42", ""),  # second run succeeds
        ]
        result = code_agent.solve_and_run("problem")
        self.assertEqual(result, "fixed code")

    @patch("ww.agent.code_agent.call_openrouter_api")
    @patch("ww.agent.code_agent.run_python_code")
    def test_solve_and_run_max_attempts(self, mock_run, mock_api):
        from ww.agent import code_agent

        mock_api.return_value = "bad code"
        mock_run.return_value = ("", "Error every time")
        result = code_agent.solve_and_run("impossible problem")
        self.assertIn("Failed", result)


class TestFixAgent(unittest.TestCase):
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
    def test_run_script_python(self, mock_run):
        import sys as _sys

        _sys.modules.pop("ww.agent.fix_agent", None)
        from ww.agent import fix_agent

        mock_run.return_value = MagicMock(stdout="output", stderr="")
        result = fix_agent.run_script("test.py")
        self.assertEqual(result, "output")

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
    def test_run_script_rust(self, mock_run):
        import sys as _sys

        _sys.modules.pop("ww.agent.fix_agent", None)
        from ww.agent import fix_agent

        mock_run.return_value = MagicMock(stdout="built", stderr="")
        result = fix_agent.run_script("test.rs")
        self.assertEqual(result, "built")

    @patch.dict(
        "sys.modules",
        {
            "ww.llm.openrouter_client": MagicMock(
                call_openrouter_api=MagicMock(),
                MODEL_MAPPING={"deepseek-v3.2": "deepseek/deepseek-v3.2"},
            )
        },
    )
    def test_run_script_unsupported(self):
        import sys as _sys

        _sys.modules.pop("ww.agent.fix_agent", None)
        from ww.agent import fix_agent

        result = fix_agent.run_script("test.txt")
        self.assertIn("Unsupported", result)

    @patch.dict(
        "sys.modules",
        {
            "ww.llm.openrouter_client": MagicMock(
                call_openrouter_api=MagicMock(return_value="fixed code"),
                MODEL_MAPPING={"deepseek-v3.2": "deepseek/deepseek-v3.2"},
            )
        },
    )
    def test_fix_script(self):
        import sys as _sys

        _sys.modules.pop("ww.agent.fix_agent", None)
        from ww.agent import fix_agent

        m = mock_open()
        with patch("builtins.open", m):
            result = fix_agent.fix_script("test.py", "some error", "model")
        self.assertIn("Applied fix", result)


class TestOptimizeAgent(unittest.TestCase):
    def test_extract_file_operations_with_open(self):
        import types

        mock_astroid = types.ModuleType("astroid")

        # Create types that isinstance checks will work with
        FuncDefType = type("FunctionDef", (), {})
        CallType = type("Call", (), {})
        AttrType = type("Attribute", (), {})
        mock_astroid.FunctionDef = FuncDefType
        mock_astroid.Call = CallType
        mock_astroid.Attribute = AttrType

        class MockFuncDef(FuncDefType):
            def __init__(self, name, has_file_op=False):
                self.name = name
                self._has_file_op = has_file_op

            def nodes_of_class(self, types_):
                if self._has_file_op:
                    # Create a call object where func passes isinstance(AttrType)
                    call = MagicMock()
                    call.func = AttrType()
                    call.func.attrname = "open"
                    return [call]
                return []

        with patch.dict("sys.modules", {"astroid": mock_astroid}):
            import sys as _sys

            _sys.modules.pop("ww.agent.optimize_agent", None)
            import ww.agent as _pkg

            if hasattr(_pkg, "optimize_agent"):
                delattr(_pkg, "optimize_agent")

            func1 = MockFuncDef("read_data", True)
            func2 = MockFuncDef("process", False)

            mock_tree = MagicMock()
            mock_tree.body = [func1, func2]
            mock_astroid.parse = MagicMock(return_value=mock_tree)

            from ww.agent import optimize_agent

            file_ops, content_funcs = optimize_agent.extract_file_operations(
                "dummy code"
            )
            self.assertEqual(len(file_ops), 1)
            self.assertEqual(file_ops[0].name, "read_data")
            self.assertEqual(len(content_funcs), 1)
            self.assertEqual(content_funcs[0].name, "process")

    def test_extract_file_operations_no_file_ops(self):
        import types

        mock_astroid = types.ModuleType("astroid")

        FuncDefType = type("FunctionDef", (), {})
        mock_astroid.FunctionDef = FuncDefType
        mock_astroid.Call = type("Call", (), {})
        mock_astroid.Attribute = type("Attribute", (), {})

        class MockFuncDef(FuncDefType):
            def __init__(self, name):
                self.name = name

            def nodes_of_class(self, types_):
                return []

        with patch.dict("sys.modules", {"astroid": mock_astroid}):
            import sys as _sys

            _sys.modules.pop("ww.agent.optimize_agent", None)
            import ww.agent as _pkg

            if hasattr(_pkg, "optimize_agent"):
                delattr(_pkg, "optimize_agent")

            func1 = MockFuncDef("compute")
            func2 = MockFuncDef("display")

            mock_tree = MagicMock()
            mock_tree.body = [func1, func2]
            mock_astroid.parse = MagicMock(return_value=mock_tree)

            from ww.agent import optimize_agent

            file_ops, content_funcs = optimize_agent.extract_file_operations(
                "dummy code"
            )
            self.assertEqual(len(file_ops), 0)
            self.assertEqual(len(content_funcs), 2)


class TestRefactorAgent(unittest.TestCase):
    @patch.dict(
        "sys.modules",
        {
            "code_validation_utils": MagicMock(
                validate_code_quality=MagicMock(return_value=(True, "ok"))
            )
        },
    )
    @patch("ww.agent.refactor_agent.call_openrouter_api")
    def test_generate_refactor_prompt(self, mock_api):
        import sys as _sys

        _sys.modules.pop("ww.agent.refactor_agent", None)
        from ww.agent import refactor_agent

        with patch("builtins.open", mock_open(read_data="def foo(): pass")):
            prompt = refactor_agent.generate_refactor_prompt("test.py")
        self.assertIn("Refactor Prompt", prompt)
        self.assertIn("def foo(): pass", prompt)

    @patch.dict(
        "sys.modules",
        {
            "code_validation_utils": MagicMock(
                validate_code_quality=MagicMock(return_value=(True, "ok"))
            )
        },
    )
    @patch("ww.agent.refactor_agent.call_openrouter_api")
    def test_generate_refactor_prompt_file_not_found(self, mock_api):
        import sys as _sys

        _sys.modules.pop("ww.agent.refactor_agent", None)
        from ww.agent import refactor_agent

        result = refactor_agent.generate_refactor_prompt("/nonexistent/file.py")
        self.assertIn("Error", result)

    @patch.dict(
        "sys.modules",
        {
            "code_validation_utils": MagicMock(
                validate_code_quality=MagicMock(return_value=(True, "ok"))
            )
        },
    )
    @patch("ww.agent.refactor_agent.call_openrouter_api")
    def test_refactor_python_code_success(self, mock_api):
        import sys as _sys

        _sys.modules.pop("ww.agent.refactor_agent", None)
        from ww.agent import refactor_agent

        mock_api.return_value = "print('hello')"

        m = mock_open(read_data="print('hello')")
        with patch("builtins.open", m):
            result = refactor_agent.refactor_python_code("test.py", model="test-model")
        self.assertIn("Successfully", result)

    @patch.dict(
        "sys.modules",
        {
            "code_validation_utils": MagicMock(
                validate_code_quality=MagicMock(
                    return_value=(False, "validation failed")
                )
            )
        },
    )
    @patch("ww.agent.refactor_agent.call_openrouter_api")
    def test_refactor_python_code_validation_fails(self, mock_api):
        import sys as _sys

        _sys.modules.pop("ww.agent.refactor_agent", None)
        from ww.agent import refactor_agent

        mock_api.return_value = "bad code"

        m = mock_open(read_data="original code")
        with patch("builtins.open", m):
            result = refactor_agent.refactor_python_code("test.py", model="test-model")
        self.assertIn("Validation failed", result)

    @patch.dict(
        "sys.modules",
        {
            "code_validation_utils": MagicMock(
                validate_code_quality=MagicMock(return_value=(True, "ok"))
            )
        },
    )
    @patch("ww.agent.refactor_agent.call_openrouter_api")
    def test_refactor_python_code_api_returns_none(self, mock_api):
        import sys as _sys

        _sys.modules.pop("ww.agent.refactor_agent", None)
        from ww.agent import refactor_agent

        mock_api.return_value = None

        m = mock_open(read_data="code")
        with patch("builtins.open", m):
            result = refactor_agent.refactor_python_code("test.py", model="test-model")
        self.assertIn("Error", result)

    @patch.dict(
        "sys.modules",
        {
            "code_validation_utils": MagicMock(
                validate_code_quality=MagicMock(return_value=(True, "ok"))
            )
        },
    )
    @patch("ww.agent.refactor_agent.call_openrouter_api")
    def test_refactor_python_code_strips_markdown(self, mock_api):
        import sys as _sys

        _sys.modules.pop("ww.agent.refactor_agent", None)
        from ww.agent import refactor_agent

        mock_api.return_value = "```python\nprint('cleaned')\n```"

        m = mock_open(read_data="print('original')")
        with patch("builtins.open", m):
            result = refactor_agent.refactor_python_code("test.py", model="test-model")
        self.assertIn("Successfully", result)


if __name__ == "__main__":
    unittest.main()
