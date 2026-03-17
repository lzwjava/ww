import unittest
from unittest.mock import patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGenerateSquashMessage(unittest.TestCase):
    @patch("ww.git.git_squash.call_openrouter_api", return_value="feat: squash commits")
    def test_generates_message_via_api(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: add feature\npick def456 fix: fix bug\n"
        result = generate_squash_message(rebase_todo)
        self.assertEqual(result, "feat: squash commits")
        mock_api.assert_called_once()

    @patch(
        "ww.git.git_squash.call_openrouter_api",
        side_effect=Exception("API error"),
    )
    def test_falls_back_when_api_raises(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: add feature\npick def456 fix: fix bug\n"
        result = generate_squash_message(rebase_todo)
        self.assertIsNotNone(result)
        self.assertIn("+", result)

    @patch("ww.git.git_squash.call_openrouter_api", return_value="chore: empty")
    def test_empty_todo_still_calls_api(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        result = generate_squash_message("")
        self.assertEqual(result, "chore: empty")

    @patch("ww.git.git_squash.call_openrouter_api", return_value="fix: squash")
    def test_squash_lines_also_included(self, mock_api):
        from ww.git.git_squash import generate_squash_message

        rebase_todo = "pick abc123 feat: first\nsquash def456 fix: second\n"
        result = generate_squash_message(rebase_todo)
        self.assertEqual(result, "fix: squash")


if __name__ == "__main__":
    unittest.main()
