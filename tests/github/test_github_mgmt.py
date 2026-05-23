"""Tests for ww github github_mgmt module."""

import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("GITHUB_PAT_TOKEN", "test_fake_token")


class TestGetToken(unittest.TestCase):
    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            from ww.github.github_mgmt import _get_token

            with self.assertRaises(Exception) as ctx:
                _get_token()
            self.assertIn("GITHUB_PAT_TOKEN", str(ctx.exception))

    def test_returns_token_when_set(self):
        with patch.dict(os.environ, {"GITHUB_PAT_TOKEN": "my_token"}):
            from ww.github.github_mgmt import _get_token

            self.assertEqual(_get_token(), "my_token")


class TestFmtCount(unittest.TestCase):
    def test_below_1k(self):
        from ww.github.github_mgmt import _fmt_count

        self.assertEqual(_fmt_count(0), "0")
        self.assertEqual(_fmt_count(500), "500")
        self.assertEqual(_fmt_count(999), "999")

    def test_thousands(self):
        from ww.github.github_mgmt import _fmt_count

        self.assertEqual(_fmt_count(1000), "1.0K")
        self.assertEqual(_fmt_count(1500), "1.5K")
        self.assertEqual(_fmt_count(99999), "100.0K")

    def test_millions(self):
        from ww.github.github_mgmt import _fmt_count

        self.assertEqual(_fmt_count(1000000), "1.0M")
        self.assertEqual(_fmt_count(1500000), "1.5M")
        self.assertEqual(_fmt_count(2500000), "2.5M")


class TestGetUser(unittest.TestCase):
    @patch("ww.github.github_mgmt._get")
    def test_returns_user_data(self, mock_get):
        from ww.github.github_mgmt import _get_user

        mock_get.return_value = ({"login": "testuser", "name": "Test"}, {})
        result = _get_user()
        self.assertEqual(result["login"], "testuser")
        mock_get.assert_called_once_with("user")


class TestCmdInfo(unittest.TestCase):
    @patch("ww.github.github_mgmt._get")
    def test_prints_account_info(self, mock_get):
        from ww.github.github_mgmt import cmd_info
        import io
        from contextlib import redirect_stdout

        user_data = {
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "public_repos": 10,
            "followers": 5,
            "following": 3,
            "created_at": "2020-01-01T00:00:00Z",
            "plan": {"name": "free", "private_repos": 0},
        }
        rate_data = {
            "resources": {
                "core": {"remaining": 4999, "limit": 5000},
                "search": {"remaining": 30, "limit": 30},
            }
        }

        def side_effect(path):
            if path == "user":
                return user_data, {}
            if path == "rate_limit":
                return rate_data, {}
            return {}, {}

        mock_get.side_effect = side_effect

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_info()
        output = f.getvalue()

        self.assertIn("testuser", output)
        self.assertIn("Test User", output)
        self.assertIn("test@example.com", output)
        self.assertIn("10", output)
        self.assertIn("5", output)


class TestCmdRepos(unittest.TestCase):
    @patch("ww.github.github_mgmt._get")
    def test_prints_repos(self, mock_get):
        from ww.github.github_mgmt import cmd_repos
        import io
        from contextlib import redirect_stdout

        repos = [
            {
                "full_name": "user/repo1",
                "private": False,
                "stargazers_count": 10,
                "language": "Python",
                "pushed_at": "2024-01-01T00:00:00Z",
            },
            {
                "full_name": "user/repo2",
                "private": True,
                "stargazers_count": 0,
                "language": None,
                "pushed_at": "2024-01-02T00:00:00Z",
            },
        ]
        mock_get.return_value = (repos, {})

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_repos()
        output = f.getvalue()

        self.assertIn("user/repo1", output)
        self.assertIn("user/repo2", output)
        self.assertIn("[private]", output)
        self.assertIn("Python", output)


class TestCmdStarred(unittest.TestCase):
    @patch("ww.github.github_mgmt._get")
    def test_prints_starred(self, mock_get):
        from ww.github.github_mgmt import cmd_starred
        import io
        from contextlib import redirect_stdout

        repos = [
            {
                "full_name": "org/cool-project",
                "stargazers_count": 1000,
                "language": "Rust",
                "description": "A cool project",
            },
        ]
        mock_get.return_value = (repos, {})

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_starred()
        output = f.getvalue()

        self.assertIn("org/cool-project", output)
        self.assertIn("1000", output)
        self.assertIn("Rust", output)
        self.assertIn("A cool project", output)


class TestCmdFollowers(unittest.TestCase):
    @patch("ww.github.github_mgmt._get")
    def test_prints_followers(self, mock_get):
        from ww.github.github_mgmt import cmd_followers
        import io
        from contextlib import redirect_stdout

        users = [{"login": "alice"}, {"login": "bob"}]
        mock_get.return_value = (users, {})

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_followers()
        output = f.getvalue()

        self.assertIn("alice", output)
        self.assertIn("bob", output)


class TestCmdFollowing(unittest.TestCase):
    @patch("ww.github.github_mgmt._get")
    def test_prints_following(self, mock_get):
        from ww.github.github_mgmt import cmd_following
        import io
        from contextlib import redirect_stdout

        users = [{"login": "charlie"}]
        mock_get.return_value = (users, {})

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_following()
        output = f.getvalue()

        self.assertIn("charlie", output)


class TestCmdNotifications(unittest.TestCase):
    @patch("ww.github.github_mgmt._get")
    def test_prints_notifications(self, mock_get):
        from ww.github.github_mgmt import cmd_notifications
        import io
        from contextlib import redirect_stdout

        notifs = [
            {
                "repository": {"full_name": "org/repo"},
                "reason": "review_requested",
                "subject": {"title": "Fix bug #123"},
            },
        ]
        mock_get.return_value = (notifs, {})

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_notifications()
        output = f.getvalue()

        self.assertIn("org/repo", output)
        self.assertIn("review_requested", output)
        self.assertIn("Fix bug #123", output)

    @patch("ww.github.github_mgmt._get")
    def test_empty_notifications(self, mock_get):
        from ww.github.github_mgmt import cmd_notifications
        import io
        from contextlib import redirect_stdout

        mock_get.return_value = ([], {})

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_notifications()
        output = f.getvalue()

        self.assertIn("No unread", output)


class TestCmdRate(unittest.TestCase):
    @patch("ww.github.github_mgmt._get")
    def test_prints_rate_limits(self, mock_get):
        from ww.github.github_mgmt import cmd_rate
        import io
        from contextlib import redirect_stdout

        data = {
            "resources": {
                "core": {"remaining": 4990, "limit": 5000},
                "search": {"remaining": 25, "limit": 30},
            }
        }
        mock_get.return_value = (data, {})

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate()
        output = f.getvalue()

        self.assertIn("core", output)
        self.assertIn("4990", output)
        self.assertIn("5000", output)


class TestGetFunction(unittest.TestCase):
    @patch("ww.github.github_mgmt.requests.get")
    @patch("ww.github.github_mgmt._get_token", return_value="test_token")
    def test_success(self, mock_token, mock_get):
        from ww.github.github_mgmt import _get

        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = {"login": "test"}
        mock_resp.headers = {"x-ratelimit-remaining": "4999"}
        mock_get.return_value = mock_resp

        data, headers = _get("user")
        self.assertEqual(data["login"], "test")
        mock_get.assert_called_once()

    @patch("ww.github.github_mgmt.requests.get")
    @patch("ww.github.github_mgmt._get_token", return_value="test_token")
    def test_raises_on_error(self, mock_token, mock_get):
        from ww.github.github_mgmt import _get

        mock_resp = MagicMock(ok=False, status_code=401, text="Unauthorized")
        mock_get.return_value = mock_resp

        with self.assertRaises(Exception) as ctx:
            _get("user")
        self.assertIn("401", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
