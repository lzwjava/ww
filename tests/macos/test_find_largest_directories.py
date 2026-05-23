import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestRunCommand(unittest.TestCase):
    @patch("ww.macos.find_largest_directories.subprocess.run")
    def test_returns_stdout_on_success(self, mock_run):
        from ww.macos.find_largest_directories import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="output\n")
        self.assertEqual(run_command("ls"), "output\n")

    @patch("ww.macos.find_largest_directories.subprocess.run")
    def test_returns_none_on_failure(self, mock_run):
        from ww.macos.find_largest_directories import run_command

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(run_command("bad"))

    @patch("ww.macos.find_largest_directories.subprocess.run", side_effect=Exception)
    def test_returns_none_on_exception(self, mock_run):
        from ww.macos.find_largest_directories import run_command

        self.assertIsNone(run_command("fail"))


class TestGetDirectorySizeKb(unittest.TestCase):
    @patch(
        "ww.macos.find_largest_directories.run_command",
        return_value="2048\t/path/to/dir\n",
    )
    def test_returns_size(self, mock_rc):
        from ww.macos.find_largest_directories import get_directory_size_kb

        self.assertEqual(get_directory_size_kb("/path/to/dir"), 2048)

    @patch("ww.macos.find_largest_directories.run_command", return_value=None)
    def test_returns_zero_on_failure(self, mock_rc):
        from ww.macos.find_largest_directories import get_directory_size_kb

        self.assertEqual(get_directory_size_kb("/bad"), 0)

    @patch(
        "ww.macos.find_largest_directories.run_command", return_value="not_a_number\n"
    )
    def test_returns_zero_on_value_error(self, mock_rc):
        from ww.macos.find_largest_directories import get_directory_size_kb

        self.assertEqual(get_directory_size_kb("/bad"), 0)


class TestFormatSize(unittest.TestCase):
    def test_kb(self):
        from ww.macos.find_largest_directories import format_size

        self.assertEqual(format_size(500), "500 KB")

    def test_mb(self):
        from ww.macos.find_largest_directories import format_size

        self.assertEqual(format_size(2048), "2 MB")

    def test_gb(self):
        from ww.macos.find_largest_directories import format_size

        self.assertEqual(format_size(2 * 1024 * 1024), "2.0 GB")


class TestFindLargeDirectories(unittest.TestCase):
    @patch("ww.macos.find_largest_directories.get_directory_size_kb")
    def test_finds_large_dirs(self, mock_size):
        from ww.macos.find_largest_directories import find_large_directories

        # Create a real temp directory with subdirs
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "big"))
            os.makedirs(os.path.join(tmpdir, "small"))
            # Create a file (should be skipped)
            with open(os.path.join(tmpdir, "afile"), "w") as f:
                f.write("x")

            def size_side_effect(path):
                if "big" in path:
                    return 5000
                return 100

            mock_size.side_effect = size_side_effect
            result = find_large_directories(tmpdir, min_size_kb=1024)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][0], "big")
            self.assertEqual(result[0][1], 5000)

    def test_empty_directory(self):
        from ww.macos.find_largest_directories import find_large_directories

        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_large_directories(tmpdir)
            self.assertEqual(result, [])

    @patch("ww.macos.find_largest_directories.Path")
    def test_handles_os_error(self, mock_path_cls):
        from ww.macos.find_largest_directories import find_large_directories

        mock_path_instance = MagicMock()
        mock_path_instance.resolve.side_effect = OSError("permission denied")
        mock_path_cls.return_value = mock_path_instance

        result = find_large_directories("/test")
        self.assertEqual(result, [])


class TestMain(unittest.TestCase):
    @patch(
        "ww.macos.find_largest_directories.find_large_directories",
        return_value=[("dir1", 5000)],
    )
    @patch("pathlib.Path.is_dir", return_value=True)
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.resolve", return_value=Path("/test"))
    @patch("sys.argv", ["find-large-dirs", "--mb", "1", "/test"])
    def test_main_with_results(self, *mocks):
        from ww.macos.find_largest_directories import main

        main()  # should not raise

    @patch("ww.macos.find_largest_directories.find_large_directories", return_value=[])
    @patch("pathlib.Path.is_dir", return_value=True)
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.resolve", return_value=Path("/test"))
    @patch("sys.argv", ["find-large-dirs", "/test"])
    def test_main_no_results(self, *mocks):
        from ww.macos.find_largest_directories import main

        main()  # should not raise

    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.resolve", return_value=Path("/bad"))
    @patch("sys.argv", ["find-large-dirs", "/bad"])
    def test_main_nonexistent_path(self, *mocks):
        from ww.macos.find_largest_directories import main

        with self.assertRaises(SystemExit):
            main()

    @patch("pathlib.Path.is_dir", return_value=False)
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.resolve", return_value=Path("/file"))
    @patch("sys.argv", ["find-large-dirs", "/file"])
    def test_main_not_a_directory(self, *mocks):
        from ww.macos.find_largest_directories import main

        with self.assertRaises(SystemExit):
            main()


if __name__ == "__main__":
    unittest.main()
