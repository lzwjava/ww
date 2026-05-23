import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestConvertPixelsToPoints(unittest.TestCase):
    def test_72_dpi_returns_same_value(self):
        from ww.pdf.scale_pdf import convert_pixels_to_points

        self.assertAlmostEqual(convert_pixels_to_points(72, 72), 72.0)

    def test_144_dpi_halves(self):
        from ww.pdf.scale_pdf import convert_pixels_to_points

        self.assertAlmostEqual(convert_pixels_to_points(144, 144), 72.0)

    def test_zero_pixels(self):
        from ww.pdf.scale_pdf import convert_pixels_to_points

        self.assertAlmostEqual(convert_pixels_to_points(0, 72), 0.0)

    def test_150_dpi(self):
        from ww.pdf.scale_pdf import convert_pixels_to_points

        result = convert_pixels_to_points(300, 150)
        self.assertAlmostEqual(result, 144.0)

    def test_fractional_result(self):
        from ww.pdf.scale_pdf import convert_pixels_to_points

        result = convert_pixels_to_points(100, 300)
        self.assertAlmostEqual(result, 24.0)


class TestGetImageDimensions(unittest.TestCase):
    def test_returns_correct_dimensions(self):
        from ww.pdf.scale_pdf import get_image_dimensions

        mock_image = MagicMock()
        mock_image.size = (612, 792)
        mock_image.info = {"dpi": (72, 72)}

        width, height, wp, hp, dpi = get_image_dimensions(mock_image)
        self.assertEqual(width, 612)
        self.assertEqual(height, 792)
        self.assertAlmostEqual(wp, 612.0)
        self.assertAlmostEqual(hp, 792.0)
        self.assertEqual(dpi, (72, 72))

    def test_uses_default_dpi_when_missing(self):
        from ww.pdf.scale_pdf import get_image_dimensions, DPI

        mock_image = MagicMock()
        mock_image.size = (100, 200)
        mock_image.info = {}

        width, height, wp, hp, dpi = get_image_dimensions(mock_image)
        self.assertEqual(dpi, (DPI, DPI))
        self.assertAlmostEqual(wp, 100 * 72 / DPI)
        self.assertAlmostEqual(hp, 200 * 72 / DPI)

    def test_high_dpi_image(self):
        from ww.pdf.scale_pdf import get_image_dimensions

        mock_image = MagicMock()
        mock_image.size = (2448, 3168)
        mock_image.info = {"dpi": (300, 300)}

        width, height, wp, hp, dpi = get_image_dimensions(mock_image)
        self.assertEqual(width, 2448)
        self.assertEqual(height, 3168)
        self.assertAlmostEqual(wp, 2448 * 72 / 300)
        self.assertAlmostEqual(hp, 3168 * 72 / 300)


class TestCalculateScaleFactor(unittest.TestCase):
    @patch("ww.pdf.scale_pdf.analyze_whitespace")
    @patch("ww.pdf.scale_pdf.get_image_dimensions")
    @patch("ww.pdf.scale_pdf.convert_from_path")
    def test_returns_scale_factor(self, mock_convert, mock_dims, mock_ws):
        from ww.pdf.scale_pdf import calculate_scale_factor

        mock_image = MagicMock()
        mock_convert.return_value = [mock_image]
        mock_dims.return_value = (612, 792, 612.0, 792.0, (72, 72))
        mock_ws.return_value = (50, 50, 50, 50)

        result = calculate_scale_factor("/tmp/test.pdf")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, float)

    @patch("ww.pdf.scale_pdf.convert_from_path")
    def test_returns_none_when_no_images(self, mock_convert):
        from ww.pdf.scale_pdf import calculate_scale_factor

        mock_convert.return_value = []
        result = calculate_scale_factor("/tmp/test.pdf")
        self.assertIsNone(result)

    @patch("ww.pdf.scale_pdf.analyze_whitespace")
    @patch("ww.pdf.scale_pdf.get_image_dimensions")
    @patch("ww.pdf.scale_pdf.convert_from_path")
    def test_handles_no_content_bounding_box(self, mock_convert, mock_dims, mock_ws):
        from ww.pdf.scale_pdf import calculate_scale_factor

        mock_image = MagicMock()
        mock_convert.return_value = [mock_image]
        mock_dims.return_value = (612, 792, 612.0, 792.0, (72, 72))
        mock_ws.return_value = (None, None, None, None)

        result = calculate_scale_factor("/tmp/test.pdf")
        self.assertIsNotNone(result)

    @patch("ww.pdf.scale_pdf.convert_from_path")
    def test_returns_none_on_exception(self, mock_convert):
        from ww.pdf.scale_pdf import calculate_scale_factor

        mock_convert.side_effect = Exception("poppler not installed")
        result = calculate_scale_factor("/tmp/test.pdf")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
