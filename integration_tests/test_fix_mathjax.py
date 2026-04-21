import unittest
import tempfile
import os
import subprocess
import sys


WW_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestFixMathjaxCommand(unittest.TestCase):
    def _run(self, code):
        base_env = os.environ.copy()
        base_env["PYTHONPATH"] = WW_PROJECT + ":" + base_env.get("PYTHONPATH", "")
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
            env=base_env,
        )
        return result.returncode, result.stdout, result.stderr

    def test_mathjax_escaping(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(r"\(x^2\) and \(y\)")
            temp_path = f.name

        try:
            returncode, stdout, stderr = self._run(
                f"from ww.content.fix_mathjax import fix_mathjax_in_file; "
                f"fix_mathjax_in_file('{temp_path}')"
            )
            self.assertEqual(returncode, 0, stderr)

            with open(temp_path) as f:
                content = f.read()
            self.assertIn("\\\\(x^2\\\\)", content)
            self.assertIn("\\\\(y\\\\)", content)
        finally:
            os.unlink(temp_path)

    def test_mathjax_reset(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("\\\\(x^2\\\\)")
            temp_path = f.name

        try:
            returncode, stdout, stderr = self._run(
                f"from ww.content.fix_mathjax import fix_mathjax_in_file; "
                f"fix_mathjax_in_file('{temp_path}', reset=True)"
            )
            self.assertEqual(returncode, 0, stderr)

            with open(temp_path) as f:
                content = f.read()
            self.assertEqual(content, r"\(x^2\)")
        finally:
            os.unlink(temp_path)

    def test_mathjax_code_block_preserved(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("```\n\\(x^2\\)\n```\nInline: \\(y\\)")
            temp_path = f.name

        try:
            returncode, stdout, stderr = self._run(
                f"from ww.content.fix_mathjax import fix_mathjax_in_file; "
                f"fix_mathjax_in_file('{temp_path}')"
            )
            self.assertEqual(returncode, 0, stderr)

            with open(temp_path) as f:
                content = f.read()
            code_part = content.split("```")[1]
            inline_part = content.split("```")[2]
            self.assertIn("\\\\(x^2\\\\)", code_part)
            self.assertIn("\\\\(y\\\\)", inline_part)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
