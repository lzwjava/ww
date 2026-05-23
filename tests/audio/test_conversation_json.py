import unittest
from unittest.mock import patch, mock_open
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


from ww.audio.conversation_json import (
    ensure_json_extension,
    validate_conversation,
    load_combined_conversation,
    resolve_output_path,
    write_conversation,
    DEFAULT_OUTPUT_DIRECTORY,
)


class TestEnsureJsonExtension(unittest.TestCase):
    def test_already_has_json_extension(self):
        self.assertEqual(ensure_json_extension("file.json"), "file.json")

    def test_adds_json_extension(self):
        self.assertEqual(ensure_json_extension("file"), "file.json")

    def test_other_extension(self):
        self.assertEqual(ensure_json_extension("file.txt"), "file.txt.json")


class TestValidateConversation(unittest.TestCase):
    def test_valid_conversation(self):
        data = [{"speaker": "Alice", "line": "Hello"}, {"speaker": "Bob", "line": "Hi"}]
        validate_conversation(data)  # Should not raise

    def test_not_a_list(self):
        with self.assertRaises(ValueError) as ctx:
            validate_conversation({"speaker": "A", "line": "B"})
        self.assertIn("list", str(ctx.exception))

    def test_item_not_dict(self):
        with self.assertRaises(ValueError) as ctx:
            validate_conversation(["not a dict"])
        self.assertIn("Item 1", str(ctx.exception))
        self.assertIn("object", str(ctx.exception))

    def test_missing_speaker(self):
        with self.assertRaises(ValueError) as ctx:
            validate_conversation([{"line": "Hello"}])
        self.assertIn("speaker", str(ctx.exception))

    def test_missing_line(self):
        with self.assertRaises(ValueError) as ctx:
            validate_conversation([{"speaker": "Alice"}])
        self.assertIn("line", str(ctx.exception))

    def test_empty_list(self):
        validate_conversation([])  # Should not raise


class TestLoadCombinedConversation(unittest.TestCase):
    def test_single_array(self):
        text = '[{"speaker": "A", "line": "hi"}]'
        result = load_combined_conversation(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["speaker"], "A")

    def test_multiple_arrays(self):
        text = '[{"speaker": "A", "line": "hi"}] [{"speaker": "B", "line": "yo"}]'
        result = load_combined_conversation(text)
        self.assertEqual(len(result), 2)

    def test_invalid_json(self):
        with self.assertRaises(ValueError) as ctx:
            load_combined_conversation("{not valid json}")
        self.assertIn("Invalid JSON", str(ctx.exception))

    def test_non_list_chunk(self):
        with self.assertRaises(ValueError) as ctx:
            load_combined_conversation('{"key": "value"}')
        self.assertIn("list", str(ctx.exception))

    def test_empty_input(self):
        with self.assertRaises(ValueError) as ctx:
            load_combined_conversation("")
        self.assertIn("No conversation items", str(ctx.exception))

    def test_whitespace_only(self):
        with self.assertRaises(ValueError) as ctx:
            load_combined_conversation("   ")
        self.assertIn("No conversation items", str(ctx.exception))


class TestResolveOutputPath(unittest.TestCase):
    def test_filename_without_dir(self):
        path = resolve_output_path("conv")
        self.assertEqual(path, os.path.join(DEFAULT_OUTPUT_DIRECTORY, "conv.json"))

    def test_filename_with_dir(self):
        path = resolve_output_path("/some/dir/conv.json")
        self.assertEqual(path, "/some/dir/conv.json")

    def test_already_json(self):
        path = resolve_output_path("conv.json")
        self.assertEqual(path, os.path.join(DEFAULT_OUTPUT_DIRECTORY, "conv.json"))


class TestWriteConversation(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_write_conversation(self, mock_makedirs, mock_file):
        data = [{"speaker": "A", "line": "hello"}]
        result = write_conversation("test", data)
        self.assertTrue(result.endswith("test.json"))
        mock_makedirs.assert_called_once()
        handle = mock_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn("speaker", written)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_write_with_absolute_path(self, mock_makedirs, mock_file):
        data = [{"speaker": "A", "line": "hello"}]
        result = write_conversation("/tmp/test.json", data)
        self.assertEqual(result, "/tmp/test.json")


class TestReadConversationInput(unittest.TestCase):
    @patch("builtins.input", side_effect=["line1", "q"])
    def test_basic_input(self, mock_input):
        from ww.audio.conversation_json import read_conversation_input

        result = read_conversation_input()
        self.assertEqual(result, "line1")

    @patch("builtins.input", side_effect=EOFError)
    def test_eof(self, mock_input):
        from ww.audio.conversation_json import read_conversation_input

        result = read_conversation_input()
        self.assertEqual(result, "")

    @patch("builtins.input", side_effect=["['hello']", "q"])
    def test_json_input(self, mock_input):
        from ww.audio.conversation_json import read_conversation_input

        result = read_conversation_input()
        self.assertEqual(result, "['hello']")


class TestMain(unittest.TestCase):
    @patch(
        "ww.audio.conversation_json.write_conversation", return_value="/tmp/out.json"
    )
    @patch("ww.audio.conversation_json.read_conversation_input")
    @patch("sys.argv", ["prog", "output"])
    def test_main_success(self, mock_read, mock_write):
        from ww.audio.conversation_json import main

        mock_read.return_value = '[{"speaker": "A", "line": "hi"}]'
        result = main()
        self.assertEqual(result, 0)

    @patch("ww.audio.conversation_json.read_conversation_input")
    @patch("sys.argv", ["prog", "output"])
    def test_main_empty_input(self, mock_read):
        from ww.audio.conversation_json import main

        mock_read.return_value = ""
        result = main()
        self.assertEqual(result, 1)

    @patch("ww.audio.conversation_json.read_conversation_input")
    @patch("sys.argv", ["prog", "output"])
    def test_main_invalid_json(self, mock_read):
        from ww.audio.conversation_json import main

        mock_read.return_value = "not json"
        result = main()
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
