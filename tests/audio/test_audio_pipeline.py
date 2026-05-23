import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

# Mock heavy dependencies before importing the module
sys.modules["pydub"] = MagicMock()
sys.modules["pydub.audio_segment"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.texttospeech"] = MagicMock()
sys.modules["markdown"] = MagicMock()
sys.modules["bs4"] = MagicMock()
sys.modules["yaml"] = MagicMock()

from ww.audio.audio_pipeline import (
    split_into_sentences,
    split_text,
    md_to_text,
    get_last_n_files,
    text_to_speech,
    OUTPUT_DIRECTORY,
)


class TestSplitIntoSentences(unittest.TestCase):
    def test_simple_sentences(self):
        text = "Hello world. How are you? I am fine."
        result = split_into_sentences(text)
        self.assertEqual(len(result), 3)
        self.assertIn("Hello world", result[0])

    def test_chinese_sentences(self):
        # The regex requires space after sentence-ending punctuation
        text = "你好。 你好吗？ 我很好！"
        result = split_into_sentences(text)
        self.assertEqual(len(result), 3)

    def test_single_sentence(self):
        text = "Just one sentence"
        result = split_into_sentences(text)
        self.assertEqual(len(result), 1)

    def test_empty_string(self):
        result = split_into_sentences("")
        self.assertEqual(result, [""])


class TestSplitText(unittest.TestCase):
    def test_short_text(self):
        text = "Short text."
        result = split_text(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Short text.")

    def test_multiple_sentences(self):
        text = "First sentence. Second sentence. Third sentence."
        result = split_text(text)
        self.assertTrue(len(result) >= 1)
        for chunk in result:
            self.assertLessEqual(len(chunk.encode("utf-8")), 3000)

    def test_custom_max_bytes(self):
        text = "Hello. World. Foo. Bar."
        result = split_text(text, max_bytes=15)
        for chunk in result:
            self.assertLessEqual(len(chunk.encode("utf-8")), 15)

    def test_empty_text(self):
        result = split_text("")
        self.assertEqual(result, [])


class TestMdToText(unittest.TestCase):
    def test_with_frontmatter(self):
        m = mock_open(read_data="---\ntitle: Test\n---\n# Hello\nWorld")
        with patch("builtins.open", m):
            # Mock markdown.markdown and BeautifulSoup
            import ww.audio.audio_pipeline as mod

            with patch.object(mod, "markdown") as mock_md, patch.object(
                mod, "BeautifulSoup"
            ) as mock_bs, patch.object(mod, "yaml") as mock_yaml, patch.object(
                mod, "unescape", side_effect=lambda x: x
            ):
                mock_md.markdown.return_value = "<h1>Hello</h1><p>World</p>"
                mock_soup = MagicMock()
                mock_soup.get_text.return_value = "Hello\nWorld"
                mock_bs.return_value = mock_soup
                mock_yaml.safe_load.return_value = {"title": "Test"}

                text, front_matter = md_to_text("test.md")
                self.assertIn("Hello", text)
                self.assertEqual(front_matter.get("title"), "Test")

    def test_without_frontmatter(self):
        m = mock_open(read_data="# No Frontmatter\nContent here")
        with patch("builtins.open", m):
            import ww.audio.audio_pipeline as mod

            with patch.object(mod, "markdown") as mock_md, patch.object(
                mod, "BeautifulSoup"
            ) as mock_bs, patch.object(mod, "unescape", side_effect=lambda x: x):
                mock_md.markdown.return_value = "<p>Content here</p>"
                mock_soup = MagicMock()
                mock_soup.get_text.return_value = "Content here"
                mock_bs.return_value = mock_soup

                text, front_matter = md_to_text("test.md")
                self.assertIn("Content here", text)
                self.assertEqual(front_matter, {})

    def test_file_error(self):
        with patch("builtins.open", side_effect=Exception("File not found")):
            text, front_matter = md_to_text("missing.md")
            self.assertEqual(text, "")
            self.assertEqual(front_matter, {})


class TestGetLastNFiles(unittest.TestCase):
    @patch("os.walk")
    def test_returns_sorted_files(self, mock_walk):
        mock_walk.return_value = [
            ("/dir", [], ["c.md", "a.md", "b.md"]),
        ]
        result = get_last_n_files("/dir", n=2)
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0].endswith("c.md"))

    @patch("os.walk")
    def test_no_md_files(self, mock_walk):
        mock_walk.return_value = [("/dir", [], ["file.txt"])]
        result = get_last_n_files("/dir")
        self.assertEqual(result, [])

    @patch("os.walk", side_effect=Exception("Permission denied"))
    def test_walk_error(self, mock_walk):
        result = get_last_n_files("/dir")
        self.assertEqual(result, [])


class TestTextToSpeech(unittest.TestCase):
    def test_dry_run(self):
        result = text_to_speech("Hello", "output.mp3", "posts", dry_run=True)
        self.assertTrue(result)

    def test_no_chunks(self):
        import ww.audio.audio_pipeline as mod

        with patch.object(mod, "split_text", return_value=[]):
            result = text_to_speech("", "output.mp3", "posts")
            self.assertFalse(result)

    def test_success_en_us(self):
        import ww.audio.audio_pipeline as mod

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"fake-audio-data"
        mock_client.synthesize_speech.return_value = mock_response

        mock_segment = MagicMock()
        mock_segment.__add__ = MagicMock(return_value=mock_segment)

        with patch.object(
            mod, "split_text", return_value=["Hello world."]
        ), patch.object(mod, "texttospeech") as mock_tts, patch.object(
            mod, "AudioSegment"
        ) as mock_audio, patch("tempfile.NamedTemporaryFile") as mock_tmp, patch(
            "os.remove"
        ):
            mock_tts.TextToSpeechClient.return_value = mock_client
            mock_tts.VoiceSelectionParams.return_value = MagicMock()
            mock_tts.AudioConfig.return_value = MagicMock()

            mock_tmp_file = MagicMock()
            mock_tmp_file.name = "/tmp/test.mp3"
            mock_tmp.return_value.__enter__ = MagicMock(return_value=mock_tmp_file)
            mock_tmp.return_value.__exit__ = MagicMock(return_value=False)

            mock_audio.from_mp3.return_value = mock_segment

            result = text_to_speech(
                "Hello world.", "output.mp3", "posts", language_code="en-US"
            )
            self.assertTrue(result)
            mock_segment.export.assert_called_once()

    def test_api_error_returns_false(self):
        import ww.audio.audio_pipeline as mod

        with patch.object(
            mod, "split_text", return_value=["Hello world."]
        ), patch.object(mod, "texttospeech") as mock_tts:
            mock_client = MagicMock()
            mock_tts.TextToSpeechClient.return_value = mock_client
            mock_tts.VoiceSelectionParams.return_value = MagicMock()
            mock_tts.AudioConfig.return_value = MagicMock()
            mock_client.synthesize_speech.side_effect = Exception("API error")

            result = text_to_speech("Hello world.", "output.mp3", "posts")
            self.assertFalse(result)

    def test_language_code_variants(self):
        import ww.audio.audio_pipeline as mod

        with patch.object(mod, "split_text", return_value=["Test."]), patch.object(
            mod, "texttospeech"
        ) as mock_tts:
            mock_client = MagicMock()
            mock_tts.TextToSpeechClient.return_value = mock_client
            mock_tts.VoiceSelectionParams.return_value = MagicMock()
            mock_tts.AudioConfig.return_value = MagicMock()
            mock_client.synthesize_speech.side_effect = Exception("stop here")

            for lang in [
                "cmn-CN",
                "es-ES",
                "fr-FR",
                "yue-HK",
                "ja-JP",
                "hi-IN",
                "de-DE",
                "ar-XA",
            ]:
                result = text_to_speech(
                    "Test.", f"out_{lang}.mp3", "posts", language_code=lang
                )
                self.assertFalse(result)


class TestProcessMarkdownFiles(unittest.TestCase):
    @patch("ww.audio.audio_pipeline.get_last_n_files")
    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["en"])
    @patch("os.path.isdir", return_value=True)
    @patch("os.makedirs")
    def test_posts_skip_existing(
        self, mock_makedirs, mock_isdir, mock_listdir, mock_exists, mock_get_files
    ):
        mock_get_files.return_value = ["/dir/test-en.md"]
        from ww.audio.audio_pipeline import process_markdown_files

        process_markdown_files("posts", "_posts", "/out", n=1)
        mock_get_files.assert_called_once()

    @patch("os.makedirs")
    def test_invalid_task(self, mock_makedirs):
        from ww.audio.audio_pipeline import process_markdown_files

        process_markdown_files("invalid", "/in", "/out")


class TestOutputDirectory(unittest.TestCase):
    def test_output_directory_value(self):
        self.assertEqual(OUTPUT_DIRECTORY, "assets/audios")


if __name__ == "__main__":
    unittest.main()
