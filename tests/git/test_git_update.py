import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestPullRepo(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_true_on_success(self, mock_run):
        from ww.git.git_update import pull_repo

        mock_run.return_value = MagicMock(returncode=0)
        result = pull_repo("/tmp/repo")
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_returns_false_on_failure(self, mock_run):
        from ww.git.git_update import pull_repo

        mock_run.return_value = MagicMock(returncode=1)
        result = pull_repo("/tmp/repo")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_calls_git_pull_verbose(self, mock_run):
        from ww.git.git_update import pull_repo

        mock_run.return_value = MagicMock(returncode=0)
        pull_repo("/tmp/repo")
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, ["git", "pull", "--verbose"])

    @patch("subprocess.run")
    def test_passes_repo_path_as_cwd(self, mock_run):
        from ww.git.git_update import pull_repo

        mock_run.return_value = MagicMock(returncode=0)
        pull_repo("/my/repo")
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["cwd"], "/my/repo")


class TestFetchRepo(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_needs_pull_when_behind(self, mock_run):
        from ww.git.git_update import fetch_repo

        # rev-parse branch, rev-parse upstream, fetch, rev-list count
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n"),  # branch
            MagicMock(returncode=0),  # has upstream
            MagicMock(returncode=0),  # fetch
            MagicMock(returncode=0, stdout="3\n"),  # behind 3
        ]
        path, needs_pull, ok = fetch_repo("/tmp/repo")
        self.assertTrue(needs_pull)
        self.assertTrue(ok)

    @patch("subprocess.run")
    def test_returns_no_pull_when_up_to_date(self, mock_run):
        from ww.git.git_update import fetch_repo

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n"),  # branch
            MagicMock(returncode=0),  # has upstream
            MagicMock(returncode=0),  # fetch
            MagicMock(returncode=0, stdout="0\n"),  # behind 0
        ]
        path, needs_pull, ok = fetch_repo("/tmp/repo")
        self.assertFalse(needs_pull)
        self.assertTrue(ok)

    @patch("subprocess.run")
    def test_returns_fail_on_fetch_error(self, mock_run):
        from ww.git.git_update import fetch_repo

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n"),  # branch
            MagicMock(returncode=0),  # has upstream
            MagicMock(returncode=1),  # fetch fails
        ]
        path, needs_pull, ok = fetch_repo("/tmp/repo")
        self.assertFalse(needs_pull)
        self.assertFalse(ok)


class TestResolveRepos(unittest.TestCase):
    @patch("os.path.isdir", return_value=True)
    def test_resolves_existing_directory(self, mock_isdir):
        from ww.git.git_update import resolve_repos

        result = resolve_repos(["./mydir"])
        self.assertEqual(result, ["./mydir"])

    @patch("os.path.isabs", return_value=True)
    def test_resolves_absolute_path(self, mock_isabs):
        from ww.git.git_update import resolve_repos

        result = resolve_repos(["/abs/path"])
        self.assertEqual(result, ["/abs/path"])

    @patch("pathlib.Path.exists", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.path.isabs", return_value=False)
    def test_resolves_name_in_repos_base(self, mock_isabs, mock_isdir, mock_exists):
        from ww.git.git_update import resolve_repos

        result = resolve_repos(["pytorch"])
        self.assertEqual(len(result), 1)
        self.assertIn("pytorch", result[0])

    @patch("pathlib.Path.exists", return_value=False)
    @patch("os.path.isdir", return_value=False)
    @patch("os.path.isabs", return_value=False)
    def test_skips_nonexistent_repo(self, mock_isabs, mock_isdir, mock_exists):
        from ww.git.git_update import resolve_repos

        result = resolve_repos(["nonexistent_repo_xyz"])
        self.assertEqual(result, [])


class TestMain(unittest.TestCase):
    @patch("ww.git.git_update.pull_repo", return_value=True)
    @patch("ww.git.git_update.fetch_repo", return_value=("/tmp/repo", True, True))
    def test_main_with_specific_target(self, mock_fetch, mock_pull):
        from ww.git.git_update import main

        with patch("os.path.isdir", return_value=True):
            with patch("os.path.abspath", return_value="/tmp/repo"):
                result = main(["/tmp/repo"])
        self.assertEqual(result, 0)

    @patch("ww.git.git_update.pull_repo", return_value=False)
    @patch("ww.git.git_update.fetch_repo", return_value=("/tmp/repo", True, True))
    def test_main_returns_1_on_failure(self, mock_fetch, mock_pull):
        from ww.git.git_update import main

        with patch("os.path.isdir", return_value=True):
            with patch("os.path.abspath", return_value="/tmp/repo"):
                result = main(["/tmp/repo"])
        self.assertEqual(result, 1)

    def test_main_skips_non_directory(self):
        from ww.git.git_update import main

        with patch("os.path.isdir", return_value=False):
            with patch("os.path.abspath", return_value="/nonexistent"):
                with patch(
                    "ww.git.git_update.resolve_repos", return_value=["/nonexistent"]
                ):
                    result = main(["/nonexistent"])
        self.assertEqual(result, 1)

    @patch("ww.git.git_update.pull_repo", return_value=True)
    @patch("ww.git.git_update.fetch_repo", return_value=("/tmp/repo", True, True))
    def test_main_no_targets_uses_defaults(self, mock_fetch, mock_pull):
        from ww.git.git_update import main

        with patch("os.path.isdir", return_value=True):
            with patch("os.path.abspath", return_value="/tmp"):
                result = main([])
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
