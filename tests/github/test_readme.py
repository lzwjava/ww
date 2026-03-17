import unittest
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestGetRealtimeCommitCount(unittest.TestCase):
    @patch("ww.github.readme.requests.get")
    def test_returns_count_from_link_header(self, mock_get):
        from ww.github.readme import get_realtime_commit_count

        mock_response = MagicMock()
        mock_response.headers = {
            "link": '<https://api.github.com/repos/u/r/commits?page=42>; rel="last"'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        self.assertEqual(get_realtime_commit_count("user", "repo"), 42)

    @patch("ww.github.readme.requests.get")
    def test_returns_1_when_no_link_header_and_commits_present(self, mock_get):
        from ww.github.readme import get_realtime_commit_count

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.json.return_value = [{"sha": "abc"}]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        self.assertEqual(get_realtime_commit_count("user", "repo"), 1)

    @patch("ww.github.readme.requests.get")
    def test_returns_0_on_http_error(self, mock_get):
        import requests

        from ww.github.readme import get_realtime_commit_count

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not Found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response
        self.assertEqual(get_realtime_commit_count("user", "nonexistent"), 0)

    @patch("ww.github.readme.requests.get", side_effect=Exception("connection error"))
    def test_returns_0_on_general_exception(self, mock_get):
        from ww.github.readme import get_realtime_commit_count

        self.assertEqual(get_realtime_commit_count("user", "repo"), 0)

    @patch("ww.github.readme.requests.get")
    def test_sets_authorization_header_when_token_provided(self, mock_get):
        from ww.github.readme import get_realtime_commit_count

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        get_realtime_commit_count("user", "repo", github_token="mytoken")
        _, kwargs = mock_get.call_args
        self.assertIn("Authorization", kwargs["headers"])
        self.assertIn("mytoken", kwargs["headers"]["Authorization"])


class TestFormatProjectsToMarkdown(unittest.TestCase):
    @patch("ww.github.readme.get_realtime_commit_count", return_value=100)
    def test_formats_table_with_pipe_separators(self, mock_count):
        from ww.github.readme import format_projects_to_markdown

        projects = [
            {
                "project": "my-repo",
                "url": "https://github.com/u/my-repo",
                "language": "Python",
            }
        ]
        result = format_projects_to_markdown(projects, "user")
        self.assertIn("|", result)
        self.assertIn("my-repo", result)
        self.assertIn("Python", result)
        self.assertIn("100", result)

    def test_returns_message_for_empty_list(self):
        from ww.github.readme import format_projects_to_markdown

        result = format_projects_to_markdown([], "user")
        self.assertIn("No project data", result)

    @patch("ww.github.readme.get_realtime_commit_count", return_value=0)
    def test_includes_header_row(self, mock_count):
        from ww.github.readme import format_projects_to_markdown

        projects = [{"project": "r", "url": "https://github.com/u/r", "language": "Go"}]
        result = format_projects_to_markdown(projects, "user")
        self.assertIn("project", result)
        self.assertIn("language", result)
        self.assertIn("commits", result)


if __name__ == "__main__":
    unittest.main()
