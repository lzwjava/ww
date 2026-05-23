import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestUpdateRepo(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_true_on_success(self, mock_run):
        from ww.git.git_update import update_repo

        mock_run.return_value = MagicMock(returncode=0)
        result = update_repo("/tmp/repo")
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_returns_false_on_failure(self, mock_run):
        from ww.git.git_update import update_repo

        mock_run.return_value = MagicMock(returncode=1)
        result = update_repo("/tmp/repo")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_calls_git_pull_verbose(self, mock_run):
        from ww.git.git_update import update_repo

        mock_run.return_value = MagicMock(returncode=0)
        update_repo("/tmp/repo")
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, ["git", "pull", "--verbose"])

    @patch("subprocess.run")
    def test_passes_repo_path_as_cwd(self, mock_run):
        from ww.git.git_update import update_repo

        mock_run.return_value = MagicMock(returncode=0)
        update_repo("/my/repo")
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["cwd"], "/my/repo")


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
    @patch("subprocess.run")
    def test_main_with_specific_target(self, mock_run):
        from ww.git.git_update import main

        mock_run.return_value = MagicMock(returncode=0)
        with patch("os.path.isdir", return_value=True):
            with patch("os.path.abspath", return_value="/tmp/repo"):
                result = main(["/tmp/repo"])
        self.assertEqual(result, 0)

    @patch("subprocess.run")
    def test_main_returns_1_on_failure(self, mock_run):
        from ww.git.git_update import main

        mock_run.return_value = MagicMock(returncode=1)
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

    @patch("subprocess.run")
    def test_main_no_targets_uses_defaults(self, mock_run):
        from ww.git.git_update import main

        mock_run.return_value = MagicMock(returncode=0)
        with patch("os.path.isdir", return_value=True):
            with patch("os.path.abspath", return_value="/tmp"):
                result = main([])
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
