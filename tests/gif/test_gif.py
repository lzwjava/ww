import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestImagesToGif(unittest.TestCase):
    @patch("PIL.Image.open")
    def test_returns_when_no_images(self, mock_open):
        from ww.gif.gif import images_to_gif

        tmpdir = tempfile.mkdtemp()
        try:
            with patch("builtins.print") as mock_print:
                images_to_gif(tmpdir, "/tmp/out.gif", 300)
                output = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("No images found", output)
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    @patch("PIL.Image.open")
    def test_saves_gif_with_images(self, mock_open):
        from ww.gif.gif import images_to_gif

        tmpdir = tempfile.mkdtemp()
        try:
            # Create dummy image files
            for name in ["a.png", "b.jpg"]:
                with open(os.path.join(tmpdir, name), "wb") as f:
                    f.write(b"\x89PNG")

            mock_img = MagicMock()
            mock_img.convert.return_value = mock_img
            mock_open.return_value = mock_img

            output_gif = os.path.join(tmpdir, "out.gif")
            images_to_gif(tmpdir, output_gif, 300)
            mock_img.save.assert_called_once()
        finally:
            import shutil

            shutil.rmtree(tmpdir)


class TestCaptureWindowScreenshot(unittest.TestCase):
    @patch("platform.system", return_value="Linux")
    def test_returns_false_on_unsupported_platform(self, mock_platform):
        from ww.gif.gif import capture_window_screenshot

        result = capture_window_screenshot("Safari", "/tmp/shot.png")
        self.assertFalse(result)

    @patch("platform.system", return_value="Windows")
    @patch("PIL.ImageGrab.grab")
    def test_windows_captures_fullscreen(self, mock_grab, mock_platform):
        from ww.gif.gif import capture_window_screenshot

        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        mock_grab.return_value = mock_img

        result = capture_window_screenshot("anything", "/tmp/shot.png")
        self.assertTrue(result)
        mock_grab.assert_called_once()


class TestMain(unittest.TestCase):
    def test_prints_help_when_no_args(self):
        from ww.gif.gif import main

        with patch("sys.argv", ["gif"]):
            with patch("argparse.ArgumentParser.print_help") as mock_help:
                main()
                mock_help.assert_called_once()

    @patch("ww.gif.gif.images_to_gif")
    def test_calls_images_to_gif_with_folder(self, mock_convert):
        from ww.gif.gif import main

        with patch(
            "sys.argv", ["gif", "/tmp/imgs", "/tmp/out.gif", "--duration", "500"]
        ):
            main()
        mock_convert.assert_called_once()
