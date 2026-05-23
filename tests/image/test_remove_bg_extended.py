import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestConvertToPng(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("ww.image.remove_bg.Image")
    def test_converts_and_saves(self, mock_image_cls):
        from ww.image.remove_bg import convert_to_png

        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_image_cls.open.return_value = mock_img

        input_path = os.path.join(self.tmpdir, "input.jpg")
        output_path = os.path.join(self.tmpdir, "output.png")

        result = convert_to_png(input_path, output_path)

        mock_image_cls.open.assert_called_once_with(input_path)
        mock_img.convert.assert_called_once_with("RGBA")
        mock_img.convert.return_value.save.assert_called_once_with(output_path, "PNG")
        self.assertEqual(result, output_path)

    @patch("ww.image.remove_bg.Image")
    def test_auto_generates_output_path(self, mock_image_cls):
        from ww.image.remove_bg import convert_to_png

        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_image_cls.open.return_value = mock_img

        input_path = os.path.join(self.tmpdir, "photo.jpg")
        result = convert_to_png(input_path, output_path=None)

        expected = os.path.join(self.tmpdir, "photo.png")
        self.assertEqual(result, expected)

    @patch("ww.image.remove_bg.Image")
    def test_rgba_mode_skips_convert(self, mock_image_cls):
        from ww.image.remove_bg import convert_to_png

        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_image_cls.open.return_value = mock_img

        result = convert_to_png("in.jpg", "out.png")
        mock_img.convert.assert_not_called()
        mock_img.save.assert_called_once_with("out.png", "PNG")


class TestDetectBackgroundColor(unittest.TestCase):
    @patch("ww.image.remove_bg.np")
    @patch("ww.image.remove_bg.Image")
    def test_returns_most_common_corner_color(self, mock_image_cls, mock_np):
        from ww.image.remove_bg import detect_background_color

        mock_img = MagicMock()
        mock_image_cls.open.return_value.convert.return_value = mock_img

        # Simulate numpy operations
        mock_data = MagicMock()
        mock_data.shape = (100, 100, 3)
        mock_np.array.return_value = mock_data
        mock_np.concatenate.return_value = "corner_pixels"
        mock_np.unique.return_value = (
            [[255, 255, 255], [0, 0, 0]],
            [800, 200],
        )
        mock_np.argmax.return_value = 0

        result = detect_background_color("test.png")

        mock_image_cls.open.assert_called_once_with("test.png")
        self.assertEqual(result, (255, 255, 255))


class TestRemoveWhiteBackground(unittest.TestCase):
    @patch("ww.image.remove_bg.np")
    @patch("ww.image.remove_bg.Image")
    def test_sets_white_pixels_transparent(self, mock_image_cls, mock_np):
        from ww.image.remove_bg import remove_white_background

        mock_img = MagicMock()
        mock_image_cls.open.return_value.convert.return_value = mock_img

        # Create mock RGBA array with shape (10, 10, 4)
        import numpy as real_np

        data = real_np.full((2, 2, 4), 255, dtype=real_np.uint8)
        mock_np.array.return_value = data

        # Mock mask operations
        white_mask = real_np.ones((2, 2), dtype=bool)
        mock_np.__getitem__ = MagicMock()
        data[white_mask, 3] = 0

        mock_np.array.return_value = data
        mock_image_cls.fromarray.return_value = MagicMock()

        remove_white_background("in.png", "out.png", tolerance=30)

        mock_image_cls.open.assert_called_once_with("in.png")
        mock_image_cls.fromarray.assert_called_once()
        mock_image_cls.fromarray.return_value.save.assert_called_once_with(
            "out.png", "PNG"
        )


class TestRemoveColorBackground(unittest.TestCase):
    @patch("ww.image.remove_bg.np")
    @patch("ww.image.remove_bg.Image")
    def test_opens_and_saves(self, mock_image_cls, mock_np):
        from ww.image.remove_bg import remove_color_background

        mock_img = MagicMock()
        mock_image_cls.open.return_value.convert.return_value = mock_img

        mock_data = MagicMock()
        mock_data.__getitem__ = MagicMock(return_value=MagicMock())
        mock_np.array.return_value = mock_data
        mock_np.abs.return_value = MagicMock(__le__=MagicMock(return_value=MagicMock()))
        mock_np.full.return_value = MagicMock()
        mock_np.ones.return_value = MagicMock()
        mock_image_cls.fromarray.return_value = MagicMock()

        remove_color_background(
            "in.png", "out.png", bg_color=(100, 150, 200), tolerance=20
        )

        mock_image_cls.open.assert_called_once_with("in.png")
        mock_image_cls.fromarray.assert_called_once()
        mock_image_cls.fromarray.return_value.save.assert_called_once_with(
            "out.png", "PNG"
        )


class TestApplyEdgeSmoothing(unittest.TestCase):
    @patch("ww.image.remove_bg.ImageFilter")
    @patch("ww.image.remove_bg.Image")
    def test_splits_blurs_and_merges(self, mock_image_cls, mock_filter):
        from ww.image.remove_bg import apply_edge_smoothing

        mock_img = MagicMock()
        mock_image_cls.open.return_value.convert.return_value = mock_img
        mock_img.split.return_value = (
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        alpha_channel = mock_img.split.return_value[3]
        blurred_alpha = MagicMock()
        alpha_channel.filter.return_value = blurred_alpha

        apply_edge_smoothing("in.png", "out.png")

        mock_image_cls.open.assert_called_once_with("in.png")
        alpha_channel.filter.assert_called_once()
        mock_filter.GaussianBlur.assert_called_once_with(radius=0.5)
        mock_image_cls.merge.assert_called_once_with(
            "RGBA",
            (
                mock_img.split.return_value[0],
                mock_img.split.return_value[1],
                mock_img.split.return_value[2],
                blurred_alpha,
            ),
        )
        mock_image_cls.merge.return_value.save.assert_called_once_with("out.png", "PNG")


if __name__ == "__main__":
    unittest.main()
