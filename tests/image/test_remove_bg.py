import os
import tempfile
import unittest

import numpy as np  # type: ignore[import-untyped]
from PIL import Image  # type: ignore[import-untyped]

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestDetectBackgroundColor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _solid_image(self, color):
        img_array = np.full((100, 100, 3), color, dtype=np.uint8)
        img = Image.fromarray(img_array, "RGB")
        fp = os.path.join(self.tmpdir, "img.png")
        img.save(fp)
        return fp

    def test_detects_white_background(self):
        from ww.image.remove_bg import detect_background_color

        fp = self._solid_image((255, 255, 255))
        result = detect_background_color(fp)
        self.assertEqual(result, (255, 255, 255))

    def test_detects_black_background(self):
        from ww.image.remove_bg import detect_background_color

        fp = self._solid_image((0, 0, 0))
        result = detect_background_color(fp)
        self.assertEqual(result, (0, 0, 0))

    def test_detects_custom_color(self):
        from ww.image.remove_bg import detect_background_color

        fp = self._solid_image((100, 150, 200))
        result = detect_background_color(fp)
        self.assertEqual(result, (100, 150, 200))

    def test_returns_tuple_of_three(self):
        from ww.image.remove_bg import detect_background_color

        fp = self._solid_image((50, 100, 150))
        result = detect_background_color(fp)
        self.assertEqual(len(result), 3)


class TestRemoveWhiteBackground(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_white_pixels_become_transparent(self):
        from ww.image.remove_bg import remove_white_background

        img_array = np.full((10, 10, 4), (255, 255, 255, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "input.png")
        img.save(fp)

        out_fp = os.path.join(self.tmpdir, "output.png")
        remove_white_background(fp, out_fp, tolerance=10)

        out_array = np.array(Image.open(out_fp).convert("RGBA"))
        self.assertEqual(out_array[0, 0, 3], 0)

    def test_non_white_pixels_remain_opaque(self):
        from ww.image.remove_bg import remove_white_background

        img_array = np.full((10, 10, 4), (0, 0, 0, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "black.png")
        img.save(fp)

        out_fp = os.path.join(self.tmpdir, "black_out.png")
        remove_white_background(fp, out_fp, tolerance=10)

        out_array = np.array(Image.open(out_fp).convert("RGBA"))
        self.assertEqual(out_array[0, 0, 3], 255)

    def test_output_file_is_created(self):
        from ww.image.remove_bg import remove_white_background

        img_array = np.full((5, 5, 4), (200, 200, 200, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "in.png")
        img.save(fp)
        out_fp = os.path.join(self.tmpdir, "out.png")
        remove_white_background(fp, out_fp)
        self.assertTrue(os.path.exists(out_fp))


class TestRemoveColorBackground(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_matching_pixels_become_transparent(self):
        from ww.image.remove_bg import remove_color_background

        img_array = np.full((10, 10, 4), (100, 150, 200, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "in.png")
        img.save(fp)

        out_fp = os.path.join(self.tmpdir, "out.png")
        remove_color_background(fp, out_fp, bg_color=(100, 150, 200), tolerance=10)

        out_array = np.array(Image.open(out_fp).convert("RGBA"))
        self.assertEqual(out_array[0, 0, 3], 0)

    def test_non_matching_pixels_stay_opaque(self):
        from ww.image.remove_bg import remove_color_background

        img_array = np.full((10, 10, 4), (255, 0, 0, 255), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGBA")
        fp = os.path.join(self.tmpdir, "in.png")
        img.save(fp)

        out_fp = os.path.join(self.tmpdir, "out.png")
        remove_color_background(fp, out_fp, bg_color=(0, 255, 0), tolerance=10)

        out_array = np.array(Image.open(out_fp).convert("RGBA"))
        self.assertEqual(out_array[0, 0, 3], 255)


if __name__ == "__main__":
    unittest.main()
