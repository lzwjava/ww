import os
import tempfile
import unittest
from integration_tests.helpers import run_ww


class TestGifCommand(unittest.TestCase):
    def _create_png(self, path, color=(255, 0, 0)):
        try:
            from PIL import Image  # type: ignore[import-untyped]
            import numpy as np  # type: ignore[import-untyped]
        except ImportError:
            self.skipTest("PIL/numpy not installed")
        img = Image.fromarray(np.full((32, 32, 3), color, dtype=np.uint8))
        img.save(path, "PNG")

    def test_gif_created_from_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_png(os.path.join(tmpdir, "frame1.png"), (255, 0, 0))
            self._create_png(os.path.join(tmpdir, "frame2.png"), (0, 255, 0))
            output_gif = os.path.join(tmpdir, "out.gif")
            returncode, stdout, stderr = run_ww("gif", tmpdir, output_gif)
            self.assertEqual(returncode, 0, stderr)
            self.assertIn("GIF saved as", stdout)
            self.assertTrue(os.path.exists(output_gif))

    def test_gif_with_custom_duration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_png(os.path.join(tmpdir, "a.png"), (0, 0, 255))
            output_gif = os.path.join(tmpdir, "custom.gif")
            returncode, stdout, stderr = run_ww(
                "gif", tmpdir, output_gif, "--duration", "100"
            )
            self.assertEqual(returncode, 0, stderr)
            self.assertTrue(os.path.exists(output_gif))

    def test_gif_empty_folder_prints_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_gif = os.path.join(tmpdir, "empty.gif")
            returncode, stdout, stderr = run_ww("gif", tmpdir, output_gif)
            self.assertEqual(returncode, 0, stderr)
            self.assertIn("No images found", stdout)


if __name__ == "__main__":
    unittest.main()
