import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestCopyToClipboard(unittest.TestCase):
    def test_pyperclip_success_returns_pyperclip(self):
        from ww.utils.ccr import copy_to_clipboard

        with patch.dict("sys.modules", {"pyperclip": MagicMock()}):
            import pyperclip

            pyperclip.copy = MagicMock()
            result = copy_to_clipboard("test text")
            self.assertEqual(result, "pyperclip")
            pyperclip.copy.assert_called_once_with("test text")

    def test_pyperclip_failure_returns_none(self):
        from ww.utils.ccr import copy_to_clipboard

        with patch.dict("sys.modules", {"pyperclip": None}):
            with patch("ww.utils.ccr.sys.platform", "darwin"):
                with patch("ww.utils.ccr.shutil.which", return_value=None):
                    result = copy_to_clipboard("test text")
                    self.assertIsNone(result)

    def test_darwin_pbcopy_fallback(self):
        from ww.utils.ccr import copy_to_clipboard

        with patch.dict("sys.modules", {"pyperclip": None}):
            with patch("ww.utils.ccr.sys.platform", "darwin"):
                with patch("ww.utils.ccr.shutil.which", return_value="/usr/bin/pbcopy"):
                    with patch("ww.utils.ccr.subprocess.Popen") as mock_popen:
                        mock_proc = MagicMock()
                        mock_proc.stdin = MagicMock()
                        mock_popen.return_value = mock_proc
                        result = copy_to_clipboard("test text")
                        self.assertEqual(result, "pbcopy")
                        mock_proc.stdin.write.assert_called_once()
                        mock_proc.stdin.close.assert_called_once()
                        mock_proc.wait.assert_called_once_with(timeout=2)

    def test_linux_xclip_fallback(self):
        from ww.utils.ccr import copy_to_clipboard

        with patch.dict("sys.modules", {"pyperclip": None}):
            with patch("ww.utils.ccr.sys.platform", "linux"):
                with patch("ww.utils.ccr.shutil.which") as mock_which:
                    mock_which.side_effect = (
                        lambda x: "/usr/bin/xclip" if x == "xclip" else None
                    )
                    with patch("ww.utils.ccr.subprocess.run") as mock_run:
                        result = copy_to_clipboard("test text")
                        self.assertEqual(result, "xclip")
                        mock_run.assert_called_once()

    def test_linux_xsel_fallback(self):
        from ww.utils.ccr import copy_to_clipboard

        with patch.dict("sys.modules", {"pyperclip": None}):
            with patch("ww.utils.ccr.sys.platform", "linux"):
                with patch("ww.utils.ccr.shutil.which") as mock_which:
                    mock_which.side_effect = (
                        lambda x: "/usr/bin/xsel" if x == "xsel" else None
                    )
                    with patch("ww.utils.ccr.subprocess.run") as mock_run:
                        result = copy_to_clipboard("test text")
                        self.assertEqual(result, "xsel")

    def test_windows_clip_fallback(self):
        from ww.utils.ccr import copy_to_clipboard

        with patch.dict("sys.modules", {"pyperclip": None}):
            with patch("ww.utils.ccr.sys.platform", "win32"):
                with patch(
                    "ww.utils.ccr.shutil.which",
                    return_value="C:\\Windows\\System32\\clip.exe",
                ):
                    with patch("ww.utils.ccr.subprocess.run") as mock_run:
                        result = copy_to_clipboard("test text")
                        self.assertEqual(result, "clip")


if __name__ == "__main__":
    unittest.main()
