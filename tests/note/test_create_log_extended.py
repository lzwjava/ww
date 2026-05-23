import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestIsSensitiveContent(unittest.TestCase):
    @patch("ww.note.create_log.generate_title", return_value="yes")
    def test_returns_true_when_llm_says_yes(self, mock_gen):
        from ww.note.create_log import is_sensitive_content

        result = is_sensitive_content("password: abc123")
        self.assertTrue(result)

    @patch("ww.note.create_log.generate_title", return_value="no")
    def test_returns_false_when_llm_says_no(self, mock_gen):
        from ww.note.create_log import is_sensitive_content

        result = is_sensitive_content("normal text")
        self.assertFalse(result)


class TestObfuscateContent(unittest.TestCase):
    @patch("ww.note.create_log.call_openrouter_api", return_value="obfuscated text")
    def test_returns_obfuscated(self, mock_api):
        from ww.note.create_log import obfuscate_content

        result = obfuscate_content("sensitive data")
        self.assertEqual(result, "obfuscated text")

    @patch("ww.note.create_log.call_openrouter_api", return_value=None)
    def test_returns_none_on_failure(self, mock_api):
        from ww.note.create_log import obfuscate_content

        result = obfuscate_content("sensitive data")
        self.assertIsNone(result)


class TestCheckDuplicateLogs(unittest.TestCase):
    def test_returns_false_when_no_logs_dir(self):
        from ww.note.create_log import _check_duplicate_logs

        with patch("ww.note.create_log.get_base_path", return_value="/nonexistent_xyz"):
            result = _check_duplicate_logs("content")
            self.assertFalse(result)

    def test_returns_false_when_empty_logs_dir(self):
        from ww.note.create_log import _check_duplicate_logs

        tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmpdir, "logs"))
        try:
            with patch("ww.note.create_log.get_base_path", return_value=tmpdir):
                result = _check_duplicate_logs("content")
                self.assertFalse(result)
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    @patch("ww.note.create_log._are_notes_quick_similar", return_value=True)
    def test_returns_true_on_duplicate(self, mock_similar):
        from ww.note.create_log import _check_duplicate_logs

        tmpdir = tempfile.mkdtemp()
        logs_dir = os.path.join(tmpdir, "logs")
        os.makedirs(logs_dir)
        with open(os.path.join(logs_dir, "test.log"), "w") as f:
            f.write("existing content")
        try:
            with patch("ww.note.create_log.get_base_path", return_value=tmpdir):
                result = _check_duplicate_logs("new content")
                self.assertTrue(result)
        finally:
            import shutil

            shutil.rmtree(tmpdir)


class TestCreateLogWithContent(unittest.TestCase):
    @patch("ww.note.create_log.create_normal_log")
    @patch("ww.note.create_log._check_duplicate_logs", return_value=False)
    @patch("ww.note.create_log.is_sensitive_content", return_value=False)
    def test_direct_mode_skips_sensitivity(self, mock_sens, mock_dup, mock_create):
        from ww.note.create_log import _create_log_with_content

        content = "x" * 100
        _create_log_with_content(content, direct=True)
        mock_sens.assert_not_called()
        mock_create.assert_called_once()

    @patch("ww.note.create_log.create_normal_log")
    @patch("ww.note.create_log._check_duplicate_logs", return_value=True)
    def test_aborts_on_duplicate(self, mock_dup, mock_create):
        from ww.note.create_log import _create_log_with_content

        _create_log_with_content("content", direct=True)
        mock_create.assert_not_called()

    @patch("ww.note.create_log.create_normal_log")
    @patch("ww.note.create_log.obfuscate_content", return_value="obfuscated")
    @patch("ww.note.create_log._check_duplicate_logs", return_value=False)
    @patch("ww.note.create_log.is_sensitive_content", return_value=True)
    def test_obfuscates_sensitive_content(
        self, mock_sens, mock_dup, mock_obf, mock_create
    ):
        from ww.note.create_log import _create_log_with_content

        _create_log_with_content("sensitive data here")
        mock_obf.assert_called_once()
        mock_create.assert_called_once()

    @patch("ww.note.create_log.create_normal_log")
    @patch("ww.note.create_log._check_duplicate_logs", return_value=False)
    @patch("ww.note.create_log.is_sensitive_content", return_value=False)
    def test_non_sensitive_content_created_directly(
        self, mock_sens, mock_dup, mock_create
    ):
        from ww.note.create_log import _create_log_with_content

        _create_log_with_content("normal content here")
        mock_create.assert_called_once()

    def test_rejects_content_over_1mb(self):
        from ww.note.create_log import _create_log_with_content

        huge = "x" * (1048576 + 1)
        result = _create_log_with_content(huge)
        self.assertIsNone(result)

    @patch("ww.note.create_log.create_normal_log")
    @patch("ww.note.create_log.obfuscate_content", return_value=None)
    @patch("ww.note.create_log._check_duplicate_logs", return_value=False)
    @patch("ww.note.create_log.is_sensitive_content", return_value=True)
    def test_aborts_when_obfuscation_fails(
        self, mock_sens, mock_dup, mock_obf, mock_create
    ):
        from ww.note.create_log import _create_log_with_content

        result = _create_log_with_content("sensitive data")
        self.assertIsNone(result)
        mock_create.assert_not_called()


class TestGetLatestMarkdownInDownloads(unittest.TestCase):
    def test_exits_when_no_downloads_dir(self):
        from ww.note.create_log import _get_latest_markdown_in_downloads

        with patch("pathlib.Path.exists", return_value=False):
            with self.assertRaises(SystemExit):
                _get_latest_markdown_in_downloads()

    def test_exits_when_no_md_files(self):
        from ww.note.create_log import _get_latest_markdown_in_downloads

        tmpdir = tempfile.mkdtemp()
        try:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                with self.assertRaises(SystemExit):
                    _get_latest_markdown_in_downloads()
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    def test_returns_latest_md_file(self):
        from ww.note.create_log import _get_latest_markdown_in_downloads

        tmpdir = tempfile.mkdtemp()
        downloads_dir = os.path.join(tmpdir, "Downloads")
        os.makedirs(downloads_dir)
        try:
            for i in range(3):
                p = os.path.join(downloads_dir, f"file{i}.md")
                with open(p, "w") as f:
                    f.write("content")
                os.utime(p, (i, i))
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = _get_latest_markdown_in_downloads()
            self.assertTrue(result.endswith(".md"))
        finally:
            import shutil

            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()
