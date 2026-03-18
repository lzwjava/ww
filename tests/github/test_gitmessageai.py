import unittest
from unittest.mock import patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

DIFF = (
    "diff --git a/foo.py b/foo.py\nnew file mode 100644\n--- /dev/null\n+++ b/foo.py\n"
)
R = lambda stdout: type("R", (), {"stdout": stdout})()


class TestGitmessageai(unittest.TestCase):
    @patch("ww.github.gitmessageai.call_llm", return_value="feat: add feature")
    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,  # git add -A
            R(
                "diff --git a/foo.py b/foo.py\n--- a\n+++ b\n"
            ),  # git diff --staged --unified=0
            None,  # git commit
            None,  # git push
        ],
    )
    def test_generates_commit_message(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        gitmessageai(push=False, only_message=False, type="file")
        mock_llm.assert_called_once()

    @patch("ww.github.gitmessageai.call_llm", return_value="feat: add feature")
    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,
            R("diff --git a/foo.py b/foo.py\n"),
        ],
    )
    def test_only_message_does_not_commit(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        gitmessageai(push=False, only_message=True, type="file")
        self.assertEqual(mock_run.call_count, 2)

    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,
            R(""),
        ],
    )
    def test_no_changes_exits_early(self, mock_run):
        from ww.github.gitmessageai import gitmessageai

        gitmessageai(push=False, only_message=False, type="file")
        self.assertEqual(mock_run.call_count, 2)

    @patch("ww.github.gitmessageai.call_llm", return_value=None)
    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,
            R("diff --git a/foo.py b/foo.py\n"),
        ],
    )
    def test_no_llm_response_exits_gracefully(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        gitmessageai(push=False, only_message=False, type="file")


class TestGitmessageaiDirectory(unittest.TestCase):
    @patch("ww.github.gitmessageai.call_llm", return_value="feat: use directory")
    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,  # git -C /repo add -A
            R(
                "diff --git a/foo.py b/foo.py\n"
            ),  # git -C /repo diff --staged --unified=0
            None,  # git -C /repo commit
            None,  # git -C /repo push
        ],
    )
    def test_directory_prepends_C_flag(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        gitmessageai(push=True, type="file", directory="/repo")

        calls = mock_run.call_args_list
        # Every call should use ["git", "-C", "/repo", ...]
        for c in calls:
            args = c[0][0]
            self.assertEqual(args[:3], ["git", "-C", "/repo"])

    @patch("ww.github.gitmessageai.call_llm", return_value="feat: no dir")
    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,
            R("diff --git a/foo.py b/foo.py\n"),
            None,
            None,
        ],
    )
    def test_no_directory_uses_plain_git(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        gitmessageai(push=True, type="file", directory=None)

        calls = mock_run.call_args_list
        for c in calls:
            args = c[0][0]
            self.assertNotIn("-C", args)

    @patch("ww.github.gitmessageai.call_llm", return_value="feat: pull push")
    @patch("ww.github.gitmessageai.subprocess.run")
    def test_allow_pull_push_retries_with_directory(self, mock_run, mock_llm):
        import subprocess
        from ww.github.gitmessageai import gitmessageai

        mock_run.side_effect = [
            None,  # git -C /repo add -A
            R(DIFF),  # diff --staged --unified=0
            None,  # git -C /repo commit
            subprocess.CalledProcessError(1, "git push"),  # first push fails
            None,  # git -C /repo pull --rebase
            None,  # git -C /repo push (retry)
        ]
        gitmessageai(push=True, allow_pull_push=True, type="file", directory="/repo")

        calls = mock_run.call_args_list
        self.assertEqual(len(calls), 6)
        pull_call = calls[4][0][0]
        push_retry = calls[5][0][0]
        self.assertEqual(pull_call[:3], ["git", "-C", "/repo"])
        self.assertEqual(push_retry[:3], ["git", "-C", "/repo"])


if __name__ == "__main__":
    unittest.main()
