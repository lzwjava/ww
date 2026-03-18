import unittest
from unittest.mock import patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGitmessageai(unittest.TestCase):
    @patch("ww.github.gitmessageai.call_llm", return_value="feat: add feature")
    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,  # git add -A
            type(
                "R", (), {"stdout": "diff --git a/foo.py b/foo.py\n--- a\n+++ b\n"}
            )(),  # git diff --staged --unified=0
            type(
                "R", (), {"stdout": "diff --git a/foo.py b/foo.py\n"}
            )(),  # git diff --staged
            None,  # git commit
            None,  # git push
        ],
    )
    def test_generates_commit_message(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        # Should not raise
        gitmessageai(push=False, only_message=False, type="file")
        mock_llm.assert_called_once()

    @patch("ww.github.gitmessageai.call_llm", return_value="feat: add feature")
    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,
            type("R", (), {"stdout": "diff --git a/foo.py b/foo.py\n"})(),
            type("R", (), {"stdout": "diff --git a/foo.py b/foo.py\n"})(),
        ],
    )
    def test_only_message_does_not_commit(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        gitmessageai(push=False, only_message=True, type="file")
        # git commit should not be called (only add + diff + llm)
        self.assertEqual(mock_run.call_count, 2)

    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,
            type("R", (), {"stdout": ""})(),
        ],
    )
    def test_no_changes_exits_early(self, mock_run):
        from ww.github.gitmessageai import gitmessageai

        # Should return early without committing
        gitmessageai(push=False, only_message=False, type="file")
        # Only git add and git diff should have been called
        self.assertEqual(mock_run.call_count, 2)

    @patch("ww.github.gitmessageai.call_llm", return_value=None)
    @patch(
        "ww.github.gitmessageai.subprocess.run",
        side_effect=[
            None,
            type("R", (), {"stdout": "diff --git a/foo.py b/foo.py\n"})(),
        ],
    )
    def test_no_llm_response_exits_gracefully(self, mock_run, mock_llm):
        from ww.github.gitmessageai import gitmessageai

        # Should not raise even when LLM returns None
        gitmessageai(push=False, only_message=False, type="file")


if __name__ == "__main__":
    unittest.main()
