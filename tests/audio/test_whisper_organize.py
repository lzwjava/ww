import os
import tempfile
import unittest

from ww.audio.whisper_organize import (
    _output_path,
    _build_prompt,
    _read_input,
    ORGANIZE_RULE,
)


class TestOutputPath(unittest.TestCase):
    def test_txt_to_organized_md(self):
        result = _output_path("/tmp/transcript.txt")
        self.assertEqual(result, "/tmp/transcript.organized.md")

    def test_already_md(self):
        result = _output_path("/tmp/audio.md")
        self.assertEqual(result, "/tmp/audio.organized.md")

    def test_path_preservation(self):
        result = _output_path("/home/user/notes/meeting.txt")
        self.assertEqual(result, "/home/user/notes/meeting.organized.md")


class TestBuildPrompt(unittest.TestCase):
    def test_contains_rule(self):
        prompt = _build_prompt("Hello world transcript")
        self.assertIn(ORGANIZE_RULE, prompt)

    def test_contains_transcript(self):
        transcript = "A: Hello, how are you?"
        prompt = _build_prompt(transcript)
        self.assertIn(transcript, prompt)

    def test_separator(self):
        prompt = _build_prompt("test")
        self.assertIn("---", prompt)


class TestReadInput(unittest.TestCase):
    def test_reads_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello transcript")
            path = f.name
        self.addCleanup(os.unlink, path)
        abs_path, content = _read_input(path)
        self.assertEqual(content, "Hello transcript")
        self.assertTrue(os.path.isabs(abs_path))

    def test_file_not_found_exits(self):
        with self.assertRaises(SystemExit):
            _read_input("/nonexistent/path/file.txt")

    def test_absolute_path_returned(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("content")
            path = f.name
        self.addCleanup(os.unlink, path)
        abs_path, _ = _read_input(path)
        self.assertTrue(os.path.isabs(abs_path))


if __name__ == "__main__":
    unittest.main()
