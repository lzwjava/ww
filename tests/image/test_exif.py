import os
import tempfile
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestIsImage(unittest.TestCase):
    def setUp(self):
        from ww.image.exif import _is_image

        self.func = _is_image

    def test_jpg_is_image(self):
        self.assertTrue(self.func("photo.jpg"))

    def test_jpeg_is_image(self):
        self.assertTrue(self.func("photo.jpeg"))

    def test_png_is_image(self):
        self.assertTrue(self.func("photo.png"))

    def test_heic_is_image(self):
        self.assertTrue(self.func("photo.heic"))

    def test_webp_is_image(self):
        self.assertTrue(self.func("photo.webp"))

    def test_tiff_is_image(self):
        self.assertTrue(self.func("photo.tiff"))

    def test_tif_is_image(self):
        self.assertTrue(self.func("photo.tif"))

    def test_uppercase_ext_is_image(self):
        self.assertTrue(self.func("photo.JPG"))

    def test_mixed_case_ext_is_image(self):
        self.assertTrue(self.func("photo.Png"))

    def test_txt_not_image(self):
        self.assertFalse(self.func("file.txt"))

    def test_pdf_not_image(self):
        self.assertFalse(self.func("file.pdf"))

    def test_no_ext_not_image(self):
        self.assertFalse(self.func("file"))

    def test_gif_not_image(self):
        self.assertFalse(self.func("animation.gif"))


class TestIsJpeg(unittest.TestCase):
    def setUp(self):
        from ww.image.exif import _is_jpeg

        self.func = _is_jpeg

    def test_jpg_is_jpeg(self):
        self.assertTrue(self.func("photo.jpg"))

    def test_jpeg_is_jpeg(self):
        self.assertTrue(self.func("photo.jpeg"))

    def test_uppercase_jpg_is_jpeg(self):
        self.assertTrue(self.func("photo.JPG"))

    def test_png_not_jpeg(self):
        self.assertFalse(self.func("photo.png"))

    def test_heic_not_jpeg(self):
        self.assertFalse(self.func("photo.heic"))

    def test_webp_not_jpeg(self):
        self.assertFalse(self.func("photo.webp"))

    def test_no_ext_not_jpeg(self):
        self.assertFalse(self.func("photo"))


class TestParseGpsCoords(unittest.TestCase):
    def setUp(self):
        from ww.image.exif import _parse_gps_coords

        self.func = _parse_gps_coords

    def test_north_latitude(self):
        # 40 deg 26 min 46.4 sec N
        result = self.func((40, 26, 46.4), "N")
        expected = 40 + 26 / 60.0 + 46.4 / 3600.0
        self.assertAlmostEqual(result, expected, places=6)

    def test_south_latitude(self):
        result = self.func((33, 51, 54), "S")
        expected = -(33 + 51 / 60.0 + 54 / 3600.0)
        self.assertAlmostEqual(result, expected, places=6)

    def test_east_longitude(self):
        result = self.func((113, 16, 10.2), "E")
        expected = 113 + 16 / 60.0 + 10.2 / 3600.0
        self.assertAlmostEqual(result, expected, places=6)

    def test_west_longitude(self):
        result = self.func((73, 58, 0), "W")
        expected = -(73 + 58 / 60.0 + 0 / 3600.0)
        self.assertAlmostEqual(result, expected, places=6)

    def test_zero_coords(self):
        result = self.func((0, 0, 0), "N")
        self.assertAlmostEqual(result, 0.0, places=6)

    def test_full_degrees_only(self):
        result = self.func((45, 0, 0), "N")
        self.assertAlmostEqual(result, 45.0, places=6)


class TestCollectImages(unittest.TestCase):
    def setUp(self):
        from ww.image.exif import _collect_images

        self.func = _collect_images
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _touch(self, name, subdir=None):
        d = os.path.join(self.tmpdir, subdir) if subdir else self.tmpdir
        os.makedirs(d, exist_ok=True)
        fp = os.path.join(d, name)
        with open(fp, "w") as f:
            f.write("")
        return fp

    def test_finds_images_non_recursive(self):
        self._touch("a.jpg")
        self._touch("b.png")
        self._touch("c.txt")
        results = list(self.func(self.tmpdir, recursive=False))
        names = [r[0] for r in results]
        self.assertIn("a.jpg", names)
        self.assertIn("b.png", names)
        self.assertNotIn("c.txt", names)

    def test_finds_images_recursive(self):
        self._touch("root.jpg")
        self._touch("sub.png", subdir="subdir")
        self._touch("deep.heic", subdir="subdir/deep")
        results = list(self.func(self.tmpdir, recursive=True))
        relpaths = [r[0] for r in results]
        self.assertIn("root.jpg", relpaths)
        self.assertIn(os.path.join("subdir", "sub.png"), relpaths)
        self.assertIn(os.path.join("subdir", "deep", "deep.heic"), relpaths)
        self.assertEqual(len(results), 3)

    def test_non_recursive_skips_subdirs(self):
        self._touch("root.jpg")
        self._touch("sub.jpg", subdir="subdir")
        results = list(self.func(self.tmpdir, recursive=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "root.jpg")

    def test_sorted_output(self):
        self._touch("z.jpg")
        self._touch("a.jpg")
        self._touch("m.jpg")
        results = list(self.func(self.tmpdir, recursive=False))
        names = [r[0] for r in results]
        self.assertEqual(names, sorted(names))

    def test_empty_directory(self):
        results = list(self.func(self.tmpdir, recursive=False))
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
