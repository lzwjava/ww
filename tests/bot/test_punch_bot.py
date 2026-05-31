import unittest
from unittest.mock import patch, MagicMock
import os
import datetime
import argparse
import tempfile
from pathlib import Path

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

try:
    from ww.bot import punch_bot

    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False
    punch_bot = MagicMock()


def setUpModule():
    if not _HAS_DEPS:
        raise unittest.SkipTest("Missing optional dependency: pytz")


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: pytz")
class TestSendTelegramMessage(unittest.TestCase):
    @patch.object(punch_bot, "requests")
    def test_send_success(self, mock_requests):
        resp = MagicMock()
        resp.status_code = 200
        mock_requests.post.return_value = resp
        punch_bot.send_telegram_message("token", "123", "hello")
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        self.assertIn("token", call_args[0][0])
        self.assertEqual(call_args[1]["params"]["chat_id"], "123")
        self.assertEqual(call_args[1]["params"]["text"], "hello")

    @patch("builtins.print")
    @patch.object(punch_bot, "requests")
    def test_send_failure(self, mock_requests, mock_print):
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "Bad Request"
        mock_requests.post.return_value = resp
        punch_bot.send_telegram_message("token", "123", "hello")
        mock_print.assert_called()


class TestSendReminder(unittest.TestCase):
    @patch.object(punch_bot, "send_telegram_message")
    def test_send_reminder_punch_in(self, mock_send):
        punch_bot.send_reminder("punch_in")
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][2]
        self.assertIn("punch in", msg)
        self.assertIn("punch_in", msg)

    @patch.object(punch_bot, "send_telegram_message")
    def test_send_reminder_punch_out(self, mock_send):
        punch_bot.send_reminder("punch_out")
        msg = mock_send.call_args[0][2]
        self.assertIn("punch out", msg)


class TestSendConfirmation(unittest.TestCase):
    @patch.object(punch_bot, "send_telegram_message")
    def test_send_confirmation_punch_in(self, mock_send):
        punch_bot.send_confirmation("punch_in")
        msg = mock_send.call_args[0][2]
        self.assertIn("already", msg)
        self.assertIn("punch in", msg)

    @patch.object(punch_bot, "send_telegram_message")
    def test_send_confirmation_punch_out(self, mock_send):
        punch_bot.send_confirmation("punch_out")
        msg = mock_send.call_args[0][2]
        self.assertIn("punch out", msg)


class TestParseTime(unittest.TestCase):
    def test_valid_hour_0(self):
        result = punch_bot.parse_time("0")
        self.assertEqual(result, datetime.time(0, 0))

    def test_valid_hour_12(self):
        result = punch_bot.parse_time("12")
        self.assertEqual(result, datetime.time(12, 0))

    def test_valid_hour_23(self):
        result = punch_bot.parse_time("23")
        self.assertEqual(result, datetime.time(23, 0))

    def test_invalid_hour_24(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            punch_bot.parse_time("24")

    def test_invalid_hour_negative(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            punch_bot.parse_time("-1")

    def test_invalid_hour_non_numeric(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            punch_bot.parse_time("abc")


class TestValidateSourceImage(unittest.TestCase):
    def test_valid_image(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image")
            path = f.name
        try:
            source_path, ext = punch_bot.validate_source_image(path)
            self.assertEqual(ext, "jpg")
            self.assertTrue(source_path.exists())
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            punch_bot.validate_source_image("/nonexistent/file.jpg")

    def test_no_extension(self):
        with tempfile.NamedTemporaryFile(suffix="", delete=False) as f:
            f.write(b"data")
            path = f.name
        try:
            with self.assertRaises(ValueError):
                punch_bot.validate_source_image(path)
        finally:
            os.unlink(path)


class TestGetNextNumber(unittest.TestCase):
    def test_nonexistent_dir(self):
        result = punch_bot.get_next_number(Path("/nonexistent"), "test", "jpg")
        self.assertEqual(result, 1)

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as d:
            result = punch_bot.get_next_number(Path(d), "test", "jpg")
            self.assertEqual(result, 1)

    def test_with_existing_files(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "test1.jpg").touch()
            Path(d, "test2.jpg").touch()
            Path(d, "test3.jpg").touch()
            result = punch_bot.get_next_number(Path(d), "test", "jpg")
            self.assertEqual(result, 4)

    def test_mixed_files(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "test1.jpg").touch()
            Path(d, "test5.jpg").touch()
            Path(d, "other.png").touch()
            result = punch_bot.get_next_number(Path(d), "test", "jpg")
            self.assertEqual(result, 6)

    def test_no_number_files(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "test.jpg").touch()
            result = punch_bot.get_next_number(Path(d), "test", "jpg")
            # stem is "test" which starts with "test" but number_part is ""
            self.assertEqual(result, 2)


class TestGetSourceMapping(unittest.TestCase):
    def test_returns_dict(self):
        result = punch_bot.get_source_mapping()
        self.assertIsInstance(result, dict)

    def test_has_telegram(self):
        result = punch_bot.get_source_mapping()
        self.assertEqual(result["telegram"], "Telegram Bot")

    def test_has_amazon(self):
        result = punch_bot.get_source_mapping()
        self.assertEqual(result["amazon"], "amazon.com")


class TestGenerateMarkdownContent(unittest.TestCase):
    def test_format(self):
        result = punch_bot.generate_markdown_content_func(
            "assets/images/test/1.jpg", "Telegram Bot"
        )
        self.assertIn("assets/images/test/1.jpg", result)
        self.assertIn("Telegram Bot", result)
        self.assertIn("responsive", result)
        self.assertIn("caption", result)


class TestCopyToClipboard(unittest.TestCase):
    @patch.object(punch_bot, "subprocess")
    def test_success(self, mock_subprocess):
        mock_subprocess.CalledProcessError = subprocess.CalledProcessError
        mock_subprocess.run.return_value = None
        result = punch_bot.copy_to_clipboard_func("text")
        self.assertTrue(result)

    @patch.object(punch_bot, "subprocess")
    def test_failure(self, mock_subprocess):
        mock_subprocess.CalledProcessError = subprocess.CalledProcessError
        mock_subprocess.FileNotFoundError = FileNotFoundError
        mock_subprocess.run.side_effect = FileNotFoundError
        result = punch_bot.copy_to_clipboard_func("text")
        self.assertFalse(result)


import subprocess


class TestDownloadTelegramFile(unittest.TestCase):
    @patch.object(punch_bot, "requests")
    def test_success(self, mock_requests):
        get_resp = MagicMock()
        get_resp.status_code = 200
        get_resp.json.return_value = {"result": {"file_path": "photos/test.jpg"}}
        dl_resp = MagicMock()
        dl_resp.status_code = 200
        dl_resp.content = b"imagedata"
        mock_requests.get.side_effect = [get_resp, dl_resp]

        result = punch_bot.download_telegram_file("bot_token", "file_id_123")
        self.assertIsNotNone(result)
        self.assertTrue(str(result).endswith(".jpg"))

    @patch.object(punch_bot, "requests")
    def test_get_file_failure(self, mock_requests):
        get_resp = MagicMock()
        get_resp.status_code = 404
        mock_requests.get.return_value = get_resp

        result = punch_bot.download_telegram_file("bot_token", "bad_id")
        self.assertIsNone(result)

    @patch.object(punch_bot, "requests")
    def test_download_failure(self, mock_requests):
        get_resp = MagicMock()
        get_resp.status_code = 200
        get_resp.json.return_value = {"result": {"file_path": "photos/test.jpg"}}
        dl_resp = MagicMock()
        dl_resp.status_code = 500
        mock_requests.get.side_effect = [get_resp, dl_resp]

        result = punch_bot.download_telegram_file("bot_token", "file_id")
        self.assertIsNone(result)

    @patch.object(punch_bot, "requests")
    def test_exception(self, mock_requests):
        mock_requests.get.side_effect = Exception("network error")
        result = punch_bot.download_telegram_file("bot_token", "file_id")
        self.assertIsNone(result)


class TestHandleTelegramPhoto(unittest.TestCase):
    def test_no_photo_no_document(self):
        result = punch_bot.handle_telegram_photo({"message": {}})
        self.assertIsNone(result)

    def test_no_message(self):
        result = punch_bot.handle_telegram_photo({})
        self.assertIsNone(result)

    @patch.object(punch_bot, "send_telegram_message")
    @patch.object(punch_bot, "process_and_save_image")
    @patch.object(punch_bot, "download_telegram_file")
    def test_with_photo(self, mock_download, mock_process, mock_send):
        temp_path = MagicMock()
        temp_path.exists.return_value = True
        temp_path.unlink = MagicMock()
        temp_path.__str__ = lambda s: "/tmp/test.jpg"
        mock_download.return_value = temp_path
        mock_process.return_value = (
            "markdown",
            "relative/path",
            Path("/tmp/target.jpg"),
        )

        update = {"message": {"photo": [{"file_id": "small"}, {"file_id": "large"}]}}
        result = punch_bot.handle_telegram_photo(update)
        self.assertEqual(result, "markdown")
        mock_download.assert_called_once_with(
            punch_bot.TELEGRAM_PUNCH_BOT_API_KEY, "large"
        )

    @patch.object(punch_bot, "send_telegram_message")
    @patch.object(punch_bot, "process_and_save_image")
    @patch.object(punch_bot, "download_telegram_file")
    def test_with_document(self, mock_download, mock_process, mock_send):
        temp_path = MagicMock()
        temp_path.exists.return_value = True
        temp_path.unlink = MagicMock()
        temp_path.__str__ = lambda s: "/tmp/test.png"
        mock_download.return_value = temp_path
        mock_process.return_value = ("md", "path", Path("/tmp/target.png"))

        update = {
            "message": {"document": {"file_id": "doc_id", "mime_type": "image/png"}}
        }
        result = punch_bot.handle_telegram_photo(update)
        self.assertEqual(result, "md")

    @patch.object(punch_bot, "download_telegram_file")
    def test_download_returns_none(self, mock_download):
        mock_download.return_value = None
        update = {"message": {"photo": [{"file_id": "id"}]}}
        result = punch_bot.handle_telegram_photo(update)
        self.assertIsNone(result)

    @patch.object(punch_bot, "send_telegram_message")
    @patch.object(punch_bot, "process_and_save_image")
    @patch.object(punch_bot, "download_telegram_file")
    def test_cleanup_on_success(self, mock_download, mock_process, mock_send):
        temp_path = MagicMock()
        temp_path.exists.return_value = True
        temp_path.__str__ = lambda s: "/tmp/test.jpg"
        mock_download.return_value = temp_path
        mock_process.return_value = ("md", "path", Path("/tmp/target.jpg"))

        update = {"message": {"photo": [{"file_id": "id"}]}}
        punch_bot.handle_telegram_photo(update)
        temp_path.unlink.assert_called_once()

    def test_document_not_image(self):
        update = {
            "message": {"document": {"file_id": "id", "mime_type": "application/pdf"}}
        }
        result = punch_bot.handle_telegram_photo(update)
        self.assertIsNone(result)


class TestProcessAndSaveImage(unittest.TestCase):
    @patch.object(punch_bot, "copy_to_clipboard_func")
    @patch.object(punch_bot, "generate_markdown_content_func")
    @patch.object(punch_bot, "shutil")
    @patch.object(punch_bot, "get_next_number")
    @patch.object(punch_bot, "validate_source_image")
    def test_process_and_save(
        self, mock_validate, mock_next, mock_shutil, mock_gen_md, mock_copy
    ):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "source.jpg"
            source.write_bytes(b"image data")
            mock_validate.return_value = (source, "jpg")
            mock_next.return_value = 1
            mock_gen_md.return_value = "markdown"

            # We need to patch the assets directory
            with patch.object(punch_bot, "Path") as mock_path_cls:
                assets_dir = Path(d) / "assets"
                assets_dir.mkdir(parents=True, exist_ok=True)
                # Make __file__ parent resolve to something predictable
                # We'll just patch the function to use our temp dir
                pass

            # Simpler: just test that it returns a tuple with 3 elements
            # by patching the directory creation
            mock_validate.return_value = (source, "jpg")
            mock_next.return_value = 1
            mock_gen_md.return_value = "markdown"
            mock_shutil.copy2 = MagicMock()

            # Can't easily test without filesystem, so test integration
            # by using a real temp directory
            md, rel, target = punch_bot.process_and_save_image(
                str(source), "testdir", "telegram"
            )
            self.assertIn("markdown", md)
            self.assertTrue(rel.startswith("assets/images/"))
            # Cleanup
            import shutil

            if target.parent.exists():
                shutil.rmtree(target.parent.parent)


if __name__ == "__main__":
    unittest.main()
