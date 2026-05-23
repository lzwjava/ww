import datetime as dt
import subprocess
import unittest
from unittest.mock import MagicMock, patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestParseArgs(unittest.TestCase):
    def test_default_days(self):
        from ww.git.git_commit import parse_args

        args = parse_args([])
        self.assertEqual(args.days, 365)

    def test_custom_days(self):
        from ww.git.git_commit import parse_args

        args = parse_args(["--days", "30"])
        self.assertEqual(args.days, 30)

    def test_default_ref(self):
        from ww.git.git_commit import parse_args

        args = parse_args([])
        self.assertEqual(args.ref, "HEAD")

    def test_custom_ref(self):
        from ww.git.git_commit import parse_args

        args = parse_args(["--ref", "main"])
        self.assertEqual(args.ref, "main")


class TestFormatBeforeDate(unittest.TestCase):
    def test_returns_formatted_date(self):
        from ww.git.git_commit import format_before_date

        now = dt.datetime(2024, 6, 15, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = format_before_date(30, now=now)
        self.assertIn("2024-05-16", result)
        # Check it has a timezone offset
        self.assertRegex(result, r"[+-]\d{4}")

    def test_zero_days_returns_same_date(self):
        from ww.git.git_commit import format_before_date

        now = dt.datetime(2024, 6, 15, 12, 0, 0, tzinfo=dt.timezone.utc)
        result = format_before_date(0, now=now)
        self.assertIn("2024-06-15", result)

    def test_raises_on_negative_days(self):
        from ww.git.git_commit import format_before_date

        with self.assertRaises(ValueError):
            format_before_date(-1)


class TestFindCommit(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_commit_hash(self, mock_run):
        from ww.git.git_commit import find_commit

        mock_run.return_value = MagicMock(
            returncode=0, stdout="abc123def456\n", stderr=""
        )
        result = find_commit("2024-01-01", "HEAD")
        self.assertEqual(result, "abc123def456")

    @patch("subprocess.run")
    def test_raises_when_no_commit(self, mock_run):
        from ww.git.git_commit import find_commit

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        with self.assertRaises(RuntimeError):
            find_commit("2020-01-01", "HEAD")

    @patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "git", stderr=b"err"),
    )
    def test_raises_on_git_error(self, mock_run):
        from ww.git.git_commit import find_commit

        with self.assertRaises(RuntimeError):
            find_commit("2024-01-01", "HEAD")


class TestMain(unittest.TestCase):
    @patch("ww.git.git_commit.find_commit", return_value="abc123")
    @patch("ww.git.git_commit.format_before_date", return_value="2024-01-01")
    def test_returns_0_on_success(self, mock_date, mock_find):
        from ww.git.git_commit import main

        result = main(["--days", "30"])
        self.assertEqual(result, 0)

    @patch("ww.git.git_commit.find_commit", side_effect=RuntimeError("no commit"))
    @patch("ww.git.git_commit.format_before_date", return_value="2024-01-01")
    def test_returns_1_on_error(self, mock_date, mock_find):
        from ww.git.git_commit import main

        result = main(["--days", "30"])
        self.assertEqual(result, 1)
