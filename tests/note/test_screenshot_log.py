import base64
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestEncodeImageToBase64(unittest.TestCase):
    def test_encodes_png_file(self):
        from ww.note.screenshot_log import _encode_image_to_base64

        from PIL import Image

        tmpfile = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmpfile.close()
        # Create a real small PNG so PIL can open it
        img = Image.new("RGB", (10, 10), color="red")
        img.save(tmpfile.name)
        try:
            b64_str, mime = _encode_image_to_base64(tmpfile.name)
            self.assertEqual(mime, "image/jpeg")
            decoded = base64.b64decode(b64_str)
            # JPEG starts with FF D8
            self.assertTrue(decoded[:2] == b"\xff\xd8")
        finally:
            os.unlink(tmpfile.name)


class TestGetScreenshotDir(unittest.TestCase):
    def test_returns_env_dir_when_set(self):
        from ww.note.screenshot_log import _get_screenshot_dir

        with patch.dict(os.environ, {"SCREENSHOT_DIR": "/my/screenshots"}):
            result = _get_screenshot_dir()
            self.assertEqual(result, "/my/screenshots")

    def test_returns_dot_when_env_empty(self):
        from ww.note.screenshot_log import _get_screenshot_dir

        with patch.dict(os.environ, {"SCREENSHOT_DIR": ""}):
            result = _get_screenshot_dir()
            self.assertEqual(result, ".")

    def test_returns_dot_when_env_unset(self):
        from ww.note.screenshot_log import _get_screenshot_dir

        with patch.dict(os.environ, {}, clear=True):
            result = _get_screenshot_dir()
            self.assertEqual(result, ".")


class TestGetLatestScreenshots(unittest.TestCase):
    def test_exits_when_dir_not_found(self):
        from ww.note.screenshot_log import _get_latest_screenshots

        with self.assertRaises(SystemExit):
            _get_latest_screenshots("/nonexistent_dir_xyz")

    def test_exits_when_no_images(self):
        from ww.note.screenshot_log import _get_latest_screenshots

        tmpdir = tempfile.mkdtemp()
        try:
            with self.assertRaises(SystemExit):
                _get_latest_screenshots(tmpdir)
        finally:
            os.rmdir(tmpdir)

    def test_returns_latest_png(self):
        from ww.note.screenshot_log import _get_latest_screenshots

        tmpdir = tempfile.mkdtemp()
        try:
            img = os.path.join(tmpdir, "shot.png")
            with open(img, "wb") as f:
                f.write(b"\x89PNG" + b"\x00" * 50)
            result = _get_latest_screenshots(tmpdir)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], img)
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    def test_returns_n_latest(self):
        from ww.note.screenshot_log import _get_latest_screenshots

        tmpdir = tempfile.mkdtemp()
        try:
            for i in range(3):
                p = os.path.join(tmpdir, f"s{i}.png")
                with open(p, "wb") as f:
                    f.write(b"\x89PNG" + b"\x00" * 10)
                os.utime(p, (i, i))
            result = _get_latest_screenshots(tmpdir, n=2)
            self.assertEqual(len(result), 2)
        finally:
            import shutil

            shutil.rmtree(tmpdir)


class TestGetVisionModel(unittest.TestCase):
    def test_returns_env_model(self):
        from ww.note.screenshot_log import _get_vision_model

        with patch.dict(os.environ, {"VISION_MODEL": "custom/model"}):
            result = _get_vision_model()
            self.assertEqual(result, "custom/model")

    def test_returns_default_when_env_empty(self):
        from ww.note.screenshot_log import _get_vision_model, DEFAULT_VISION_MODEL

        with patch.dict(os.environ, {"VISION_MODEL": ""}):
            result = _get_vision_model()
            self.assertEqual(result, DEFAULT_VISION_MODEL)


class TestSummarizeWithExtraPrompt(unittest.TestCase):
    @patch("ww.note.screenshot_log.call_openrouter_api", return_value="summarized text")
    def test_calls_api_with_extra_prompt(self, mock_api):
        from ww.note.screenshot_log import _summarize_with_extra_prompt

        result = _summarize_with_extra_prompt("description", "extra context")
        self.assertEqual(result, "summarized text")

    def test_returns_description_when_no_extra(self):
        from ww.note.screenshot_log import _summarize_with_extra_prompt

        result = _summarize_with_extra_prompt("description", None)
        self.assertEqual(result, "description")

    @patch("ww.note.screenshot_log.call_openrouter_api", return_value=None)
    def test_returns_description_when_api_fails(self, mock_api):
        from ww.note.screenshot_log import _summarize_with_extra_prompt

        result = _summarize_with_extra_prompt("description", "extra")
        self.assertEqual(result, "description")


class TestGenerateTitleFromContent(unittest.TestCase):
    @patch("ww.note.screenshot_log.call_openrouter_api", return_value="Test Title")
    def test_returns_title(self, mock_api):
        from ww.note.screenshot_log import _generate_title_from_content

        result = _generate_title_from_content("some content here")
        self.assertEqual(result, "Test Title")

    @patch("ww.note.screenshot_log.call_openrouter_api", return_value=None)
    def test_returns_fallback_when_api_fails(self, mock_api):
        from ww.note.screenshot_log import _generate_title_from_content

        result = _generate_title_from_content("content")
        self.assertEqual(result, "screenshot-note")

    @patch("ww.note.screenshot_log.call_openrouter_api", return_value='"Quoted Title"')
    def test_strips_quotes(self, mock_api):
        from ww.note.screenshot_log import _generate_title_from_content

        result = _generate_title_from_content("content")
        self.assertNotIn('"', result)


class TestBuildImageSection(unittest.TestCase):
    def test_builds_section_with_images(self):
        from ww.note.screenshot_log import _build_image_section

        result = _build_image_section(
            ["/notes/img/a.png", "/notes/img/b.png"], "/notes"
        )
        self.assertIn("Screenshots", result)
        self.assertIn("![screenshot]", result)


class TestFormatFrontMatterWithImage(unittest.TestCase):
    def test_contains_image_true(self):
        from ww.note.screenshot_log import _format_front_matter_with_image

        result = _format_front_matter_with_image("Title", True, "2024-01-01")
        self.assertIn("image: true", result)

    def test_contains_image_false(self):
        from ww.note.screenshot_log import _format_front_matter_with_image

        result = _format_front_matter_with_image("Title", False, "2024-01-01")
        self.assertIn("image: false", result)

    def test_quotes_title_with_colon(self):
        from ww.note.screenshot_log import _format_front_matter_with_image

        result = _format_front_matter_with_image("Title: Sub", True, "2024-01-01")
        self.assertIn('"Title: Sub"', result)

    def test_uses_today_when_no_date(self):
        from ww.note.screenshot_log import _format_front_matter_with_image

        result = _format_front_matter_with_image("Title", True)
        self.assertIn("title: Title", result)
        self.assertIn("image: true", result)


class TestGetGithubRepoUrl(unittest.TestCase):
    @patch("subprocess.check_output", return_value="git@github.com:user/repo.git\n")
    def test_converts_ssh_url(self, mock_cmd):
        from ww.note.screenshot_log import _get_github_repo_url

        result = _get_github_repo_url()
        self.assertEqual(result, "https://github.com/user/repo")

    @patch("subprocess.check_output", return_value="https://github.com/user/repo.git\n")
    def test_strips_dot_git(self, mock_cmd):
        from ww.note.screenshot_log import _get_github_repo_url

        result = _get_github_repo_url()
        self.assertEqual(result, "https://github.com/user/repo")

    @patch("subprocess.check_output", side_effect=FileNotFoundError)
    def test_returns_empty_on_error(self, mock_cmd):
        from ww.note.screenshot_log import _get_github_repo_url

        result = _get_github_repo_url()
        self.assertEqual(result, "")


class TestCreateNoteFile(unittest.TestCase):
    @patch("ww.note.screenshot_log.process_title_for_filename", return_value="my-title")
    @patch("ww.note.screenshot_log.get_base_path", return_value="/tmp/test_notes")
    def test_creates_file(self, mock_base, mock_slug):
        from ww.note.screenshot_log import _create_note_file

        tmpdir = tempfile.mkdtemp()
        try:
            with patch("ww.note.screenshot_log.get_base_path", return_value=tmpdir):
                result = _create_note_file(
                    "content here", "My Title", date="2024-01-01"
                )
                self.assertTrue(os.path.exists(result))
                with open(result) as f:
                    text = f.read()
                self.assertIn("content here", text)
                self.assertIn("My Title", text)
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    @patch("ww.note.screenshot_log.process_title_for_filename", return_value="my-title")
    def test_exits_when_file_exists(self, mock_slug):
        from ww.note.screenshot_log import _create_note_file

        tmpdir = tempfile.mkdtemp()
        try:
            notes_dir = os.path.join(tmpdir, "notes")
            os.makedirs(notes_dir)
            filepath = os.path.join(notes_dir, "2024-01-01-my-title-en.md")
            with open(filepath, "w") as f:
                f.write("existing")
            with patch("ww.note.screenshot_log.get_base_path", return_value=tmpdir):
                with self.assertRaises(SystemExit):
                    _create_note_file("content", "My Title", date="2024-01-01")
        finally:
            import shutil

            shutil.rmtree(tmpdir)

    @patch("ww.note.screenshot_log.process_title_for_filename", return_value="my-title")
    def test_appends_image_section(self, mock_slug):
        from ww.note.screenshot_log import _create_note_file

        tmpdir = tempfile.mkdtemp()
        try:
            img_path = os.path.join(tmpdir, "shot.png")
            with open(img_path, "wb") as f:
                f.write(b"\x89PNG")
            with patch("ww.note.screenshot_log.get_base_path", return_value=tmpdir):
                result = _create_note_file(
                    "content", "Title", image_paths=[img_path], date="2024-01-01"
                )
                with open(result) as f:
                    text = f.read()
                self.assertIn("Screenshots", text)
                self.assertIn("![screenshot]", text)
        finally:
            import shutil

            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()
