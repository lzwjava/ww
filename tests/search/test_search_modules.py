import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestSearchPosts(unittest.TestCase):
    @patch("ww.search.search.print_ack_output")
    @patch("subprocess.run")
    @patch("ww.search.search.check_ack", return_value="/usr/bin/ack")
    def test_calls_ack_with_query(self, mock_ack, mock_run, mock_print):
        from ww.search.search import search_posts

        mock_run.return_value = MagicMock(returncode=0, stdout="match1\nmatch2\n")
        search_posts("test query")
        cmd = mock_run.call_args[0][0]
        self.assertIn("test query", cmd)
        self.assertNotIn("-i", cmd)

    @patch("ww.search.search.print_ack_output")
    @patch("subprocess.run")
    @patch("ww.search.search.check_ack", return_value="/usr/bin/ack")
    def test_ignore_case_flag(self, mock_ack, mock_run, mock_print):
        from ww.search.search import search_posts

        mock_run.return_value = MagicMock(returncode=0, stdout="")
        search_posts("query", ignore_case=True)
        cmd = mock_run.call_args[0][0]
        self.assertIn("-i", cmd)

    @patch("ww.search.search.print_ack_output")
    @patch("subprocess.run")
    @patch("ww.search.search.check_ack", return_value="/usr/bin/ack")
    def test_custom_dirs(self, mock_ack, mock_run, mock_print):
        from ww.search.search import search_posts

        mock_run.return_value = MagicMock(returncode=0, stdout="")
        search_posts("query", dirs=["custom_dir"])
        cmd = mock_run.call_args[0][0]
        self.assertIn("custom_dir", cmd)

    @patch("subprocess.run")
    @patch("ww.search.search.check_ack", return_value="/usr/bin/ack")
    def test_prints_error_on_nonzero_return(self, mock_ack, mock_run):
        from ww.search.search import search_posts

        mock_run.return_value = MagicMock(returncode=2, stderr="error msg")
        with patch("builtins.print") as mock_print:
            search_posts("query")
            output = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("Error", output)


class TestSearchCode(unittest.TestCase):
    @patch("ww.search.search_code.print_ack_output")
    @patch("subprocess.run")
    @patch("ww.search.search_code.check_ack", return_value="/usr/bin/ack")
    def test_calls_ack_with_code_types(self, mock_ack, mock_run, mock_print):
        from ww.search.search_code import search_code

        mock_run.return_value = MagicMock(returncode=0, stdout="")
        search_code("def test")
        cmd = mock_run.call_args[0][0]
        self.assertIn("--code", cmd)
        self.assertIn("def test", cmd)

    @patch("ww.search.search_code.print_ack_output")
    @patch("subprocess.run")
    @patch("ww.search.search_code.check_ack", return_value="/usr/bin/ack")
    def test_ignore_case(self, mock_ack, mock_run, mock_print):
        from ww.search.search_code import search_code

        mock_run.return_value = MagicMock(returncode=0, stdout="")
        search_code("query", ignore_case=True)
        cmd = mock_run.call_args[0][0]
        self.assertIn("-i", cmd)


class TestSearchFilename(unittest.TestCase):
    @patch("subprocess.run")
    @patch("ww.search.search_filename.check_ack", return_value="/usr/bin/ack")
    def test_prints_matches(self, mock_ack, mock_run):
        from ww.search.search_filename import search_filenames

        mock_run.return_value = MagicMock(
            returncode=0, stdout="notes/a.md\nnotes/b.md\n"
        )
        with patch("builtins.print") as mock_print:
            search_filenames("test")
            output = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("a.md", output)

    @patch("subprocess.run")
    @patch("ww.search.search_filename.check_ack", return_value="/usr/bin/ack")
    def test_prints_no_matches(self, mock_ack, mock_run):
        from ww.search.search_filename import search_filenames

        mock_run.return_value = MagicMock(returncode=0, stdout="")
        with patch("builtins.print") as mock_print:
            search_filenames("nonexistent")
            output = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("No matching filenames", output)

    @patch("subprocess.run")
    @patch("ww.search.search_filename.check_ack", return_value="/usr/bin/ack")
    def test_error_on_bad_returncode(self, mock_ack, mock_run):
        from ww.search.search_filename import search_filenames

        mock_run.return_value = MagicMock(returncode=2, stderr="err")
        with patch("builtins.print") as mock_print:
            search_filenames("query")
            output = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("Error", output)


class TestDeleteMatches(unittest.TestCase):
    def test_deletes_existing_files(self):
        from ww.search.search_filename import _delete_matches
        import tempfile

        tmpdir = tempfile.mkdtemp()
        f1 = os.path.join(tmpdir, "a.md")
        f2 = os.path.join(tmpdir, "b.md")
        with open(f1, "w") as f:
            f.write("a")
        with open(f2, "w") as f:
            f.write("b")
        try:
            _delete_matches([f1, f2])
            self.assertFalse(os.path.exists(f1))
            self.assertFalse(os.path.exists(f2))
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    def test_handles_missing_files(self):
        from ww.search.search_filename import _delete_matches

        with patch("builtins.print") as mock_print:
            _delete_matches(["/nonexistent/file.md"])
            output = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("not found", output)
