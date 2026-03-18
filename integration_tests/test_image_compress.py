import os
import tempfile
import unittest
from integration_tests.helpers import run_ww


class TestImageCompressCommand(unittest.TestCase):
    def _create_test_png(self, path):
        try:
            from PIL import Image  # type: ignore[import-untyped]
            import numpy as np  # type: ignore[import-untyped]
        except ImportError:
            self.skipTest("PIL/numpy not installed")
        img = Image.fromarray(np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8))
        img.save(path, "PNG")

    def test_compress_image_creates_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "test.png")
            self._create_test_png(input_path)
            returncode, stdout, stderr = run_ww(
                "image", "compress", input_path, "--compression_factor", "0.5"
            )
            self.assertEqual(returncode, 0, stderr)
            self.assertIn("Compressed image saved as:", stdout)
            output_path = os.path.join(tmpdir, "test_compressed.png")
            self.assertTrue(os.path.exists(output_path), "Compressed file not created")

    def test_compress_image_default_factor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "img.png")
            self._create_test_png(input_path)
            returncode, stdout, stderr = run_ww("image", "compress", input_path)
            self.assertEqual(returncode, 0, stderr)
            self.assertIn("Compressed image saved as:", stdout)


if __name__ == "__main__":
    unittest.main()
