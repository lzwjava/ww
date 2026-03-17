import os
import tempfile
import unittest

import numpy as np  # type: ignore[import-untyped]
from PIL import Image  # type: ignore[import-untyped]

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestCompressImage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_compresses_rgb_image_and_saves_file(self):
        from ww.image.image_compress import compress_image

        img_array = np.random.randint(0, 256, (20, 20, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = os.path.join(self.tmpdir, "test.png")
        img.save(img_path)

        output_path = compress_image(img_path, compression_factor=0.5)
        self.assertTrue(os.path.exists(output_path))
        self.assertIn("_compressed", output_path)

    def test_compresses_grayscale_image(self):
        from ww.image.image_compress import compress_image

        img_array = np.random.randint(0, 256, (20, 20), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = os.path.join(self.tmpdir, "gray.png")
        img.save(img_path)

        output_path = compress_image(img_path, compression_factor=0.5)
        self.assertTrue(os.path.exists(output_path))

    def test_output_path_naming_convention(self):
        from ww.image.image_compress import compress_image

        img_array = np.ones((10, 10, 3), dtype=np.uint8) * 128
        img = Image.fromarray(img_array)
        img_path = os.path.join(self.tmpdir, "original.jpg")
        img.save(img_path)

        output_path = compress_image(img_path, compression_factor=0.3)
        self.assertEqual(
            output_path, os.path.join(self.tmpdir, "original_compressed.jpg")
        )

    def test_output_image_is_valid(self):
        from ww.image.image_compress import compress_image

        img_array = np.ones((10, 10, 3), dtype=np.uint8) * 200
        img = Image.fromarray(img_array)
        img_path = os.path.join(self.tmpdir, "solid.png")
        img.save(img_path)

        output_path = compress_image(img_path, compression_factor=1.0)
        out_img = Image.open(output_path)
        self.assertIsNotNone(out_img)


if __name__ == "__main__":
    unittest.main()
