import os
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

DIFF = (
    "diff --git a/foo.py b/foo.py\nnew file mode 100644\n--- /dev/null\n+++ b/foo.py\n"
)


def _R(stdout):
    return type("R", (), {"stdout": stdout})()


class TestParseFileChanges(unittest.TestCase):
    def test_detects_new_file(self):
        from ww.github.gitmessageai import _parse_file_changes

        diff = "diff --git a/foo.py b/foo.py\nnew file mode 100644\n"
        result = _parse_file_changes(diff)
        self.assertEqual(len(result), 1)
        self.assertIn("Added file", result[0])

    def test_detects_deleted_file(self):
        from ww.github.gitmessageai import _parse_file_changes

        diff = "diff --git a/foo.py b/foo.py\ndeleted file mode 100644\n"
        result = _parse_file_changes(diff)
        self.assertEqual(len(result), 1)
        self.assertIn("Deleted file", result[0])

    def test_detects_updated_file(self):
        from ww.github.gitmessageai import _parse_file_changes

        diff = "diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n"
        result = _parse_file_changes(diff)
        self.assertEqual(len(result), 1)
        self.assertIn("Updated file", result[0])

    def test_detects_renamed_file(self):
        from ww.github.gitmessageai import _parse_file_changes

        diff = "diff --git a/old.py b/new.py\nsimilarity index 95%\n"
        result = _parse_file_changes(diff)
        self.assertEqual(len(result), 1)
        self.assertIn("Renamed", result[0])

    def test_empty_diff_returns_empty(self):
        from ww.github.gitmessageai import _parse_file_changes

        result = _parse_file_changes("")
        self.assertEqual(result, [])


class TestBuildPrompt(unittest.TestCase):
    def test_file_type_returns_prompt_and_changes(self):
        from ww.github.gitmessageai import _build_prompt

        diff = "diff --git a/foo.py b/foo.py\nnew file mode 100644\n"
        prompt, changes = _build_prompt("file", diff)
        self.assertIsNotNone(prompt)
        self.assertIsNotNone(changes)

    def test_file_type_no_changes_returns_none(self):
        from ww.github.gitmessageai import _build_prompt

        prompt, changes = _build_prompt("file", "no diff here")
        self.assertIsNone(prompt)
        self.assertIsNone(changes)

    def test_content_type_returns_prompt(self):
        from ww.github.gitmessageai import _build_prompt

        prompt, changes = _build_prompt("content", "some diff output")
        self.assertIsNotNone(prompt)
        self.assertIsNone(changes)


class TestCleanCommitMessage(unittest.TestCase):
    def test_removes_backticks(self):
        from ww.github.gitmessageai import _clean_commit_message

        result = _clean_commit_message("```feat: add feature```")
        self.assertNotIn("```", result)

    def test_strips_whitespace(self):
        from ww.github.gitmessageai import _clean_commit_message

        result = _clean_commit_message("  feat: add  ")
        self.assertEqual(result, "feat: add")


class TestPushWithFallback(unittest.TestCase):
    @patch("subprocess.run")
    def test_push_succeeds(self, mock_run):
        from ww.github.gitmessageai import _push_with_fallback

        _push_with_fallback(["git"], allow_pull_push=False)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_push_fails_raises(self, mock_run):
        import subprocess
        from ww.github.gitmessageai import _push_with_fallback

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        with self.assertRaises(subprocess.CalledProcessError):
            _push_with_fallback(["git"], allow_pull_push=False)

    @patch("subprocess.run")
    def test_push_fails_pull_push_retries(self, mock_run):
        import subprocess
        from ww.github.gitmessageai import _push_with_fallback

        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "git"),  # push fails
            None,  # pull --rebase
            None,  # push retry
        ]
        _push_with_fallback(["git"], allow_pull_push=True)
        self.assertEqual(mock_run.call_count, 3)


class TestGitmessageaiContent(unittest.TestCase):
    @patch("ww.github.gitmessageai.call_llm", return_value="feat: content change")
    @patch("ww.github.gitmessageai.subprocess.run")
    def test_content_type_uses_full_diff(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        mock_run.side_effect = [
            None,  # git add -A
            _R(""),  # git diff --staged --unified=0 (empty, triggers early return)
        ]
        gitmessageai(push=False, type="content")

    @patch("ww.github.gitmessageai.call_llm", return_value="feat: content")
    @patch("ww.github.gitmessageai.subprocess.run")
    def test_content_type_with_diff(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        mock_run.side_effect = [
            None,  # git add -A
            _R("diff"),  # git diff --staged --unified=0 (file mode)
            _R("full diff content"),  # git diff --staged (content mode)
            None,  # git commit
        ]
        gitmessageai(push=False, type="content")
        mock_llm.assert_called_once()

    def test_invalid_type_returns(self):
        from ww.github.gitmessageai import gitmessageai

        with patch("ww.github.gitmessageai.subprocess.run") as mock_run:
            mock_run.side_effect = [None, _R("diff")]
            gitmessageai(push=False, type="invalid")


class TestGitmessageaiEdgeCases(unittest.TestCase):
    @patch("ww.github.gitmessageai.call_llm", return_value="  ")
    @patch("ww.github.gitmessageai.subprocess.run")
    def test_empty_commit_message_aborts(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        mock_run.side_effect = [
            None,  # git add -A
            _R("diff --git a/foo.py b/foo.py\nnew file mode\n"),
        ]
        gitmessageai(push=False)

    @patch("ww.github.gitmessageai.call_llm", return_value="feat: msg")
    @patch("ww.github.gitmessageai.subprocess.run")
    def test_push_flag_false_prints_local(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        mock_run.side_effect = [
            None,
            _R(DIFF),
            None,  # commit
        ]
        with patch("builtins.print") as mock_print:
            gitmessageai(push=False)
            output = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("locally", output)

    @patch("ww.github.gitmessageai.call_llm", return_value="feat: push")
    @patch("ww.github.gitmessageai.subprocess.run")
    def test_push_flag_true_calls_push(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        mock_run.side_effect = [
            None,
            _R(DIFF),
            None,  # commit
            None,  # push
        ]
        gitmessageai(push=True)
        call_cmds = [c[0][0] for c in mock_run.call_args_list]
        self.assertIn("push", call_cmds[-1])
