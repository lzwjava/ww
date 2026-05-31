import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

try:
    import importlib.util

    _HAS_DEPS = importlib.util.find_spec("Quartz") is not None
    if _HAS_DEPS:
        from ww.image.screenshot import capture_screenshot  # noqa: F401
except ImportError:
    _HAS_DEPS = False


def setUpModule():
    if not _HAS_DEPS:
        raise unittest.SkipTest("Missing optional dependency: pyobjc (macOS only)")


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: pyobjc (macOS only)")
class TestCaptureScreenshot(unittest.TestCase):
    @patch("ww.image.screenshot.ImageGrab")
    @patch("ww.image.screenshot.Quartz")
    def test_returns_none_when_no_safari_window(self, mock_quartz, mock_imggrab):
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {mock_quartz.kCGWindowOwnerName: "Chrome"}
        ]
        from ww.image.screenshot import capture_screenshot

        tmpdir = tempfile.mkdtemp()
        try:
            result = capture_screenshot(tmpdir)
            self.assertIsNone(result)
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    @patch("ww.image.screenshot.ImageGrab")
    @patch("ww.image.screenshot.Quartz")
    def test_saves_screenshot_when_safari_found(self, mock_quartz, mock_imggrab):
        mock_quartz.kCGWindowOwnerName = "kCGWindowOwnerName"
        mock_quartz.kCGWindowName = "kCGWindowName"
        mock_quartz.kCGWindowListOptionOnScreenOnly = 1
        mock_quartz.kCGNullWindowID = 0

        mock_window = {
            "kCGWindowOwnerName": "Safari",
            "kCGWindowName": "Test Page",
            "kCGWindowBounds": {"X": 10, "Y": 20, "Width": 800, "Height": 600},
        }
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [mock_window]

        mock_img = MagicMock()
        mock_img.size = (800, 600)
        mock_imggrab.grab.return_value = mock_img

        from ww.image.screenshot import capture_screenshot

        tmpdir = tempfile.mkdtemp()
        try:
            result = capture_screenshot(tmpdir)
            self.assertIsNotNone(result)
            self.assertTrue(result.endswith(".png"))
            mock_img.save.assert_called_once()
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    @patch("ww.image.screenshot.ImageGrab")
    @patch("ww.image.screenshot.Quartz")
    def test_creates_directory(self, mock_quartz, mock_imggrab):
        mock_quartz.CGWindowListCopyWindowInfo.return_value = []
        from ww.image.screenshot import capture_screenshot

        tmpdir = tempfile.mkdtemp()
        subdir = os.path.join(tmpdir, "new_dir")
        try:
            capture_screenshot(subdir)
            self.assertTrue(os.path.isdir(subdir))
        finally:
            import shutil

            shutil.rmtree(tmpdir)


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: pyobjc (macOS only)")
class TestMain(unittest.TestCase):
    @patch("ww.image.screenshot.capture_screenshot")
    @patch("ww.image.screenshot.load_dotenv")
    def test_main_uses_env_dir(self, mock_dotenv, mock_capture):
        from ww.image.screenshot import main

        mock_capture.return_value = "/tmp/shot.png"
        with patch.dict(os.environ, {"SCREENSHOT_DIR": "/my/dir"}):
            with patch.object(sys, "argv", ["screenshot"]):
                main()
        mock_capture.assert_called_once_with("/my/dir")

    @patch("ww.image.screenshot.capture_screenshot")
    @patch("ww.image.screenshot.load_dotenv")
    def test_main_uses_dir_flag(self, mock_dotenv, mock_capture):
        from ww.image.screenshot import main

        mock_capture.return_value = "/tmp/shot.png"
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys, "argv", ["screenshot", "--dir", "/flag/dir"]):
                main()
        mock_capture.assert_called_once_with("/flag/dir")


if __name__ == "__main__":
    unittest.main()
