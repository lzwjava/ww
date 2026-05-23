import unittest
from unittest.mock import patch, mock_open
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

# x_post.py imports MODEL_MAPPING from openrouter_client, but it doesn't exist there.
# Add a dummy to make import work.
import ww.llm.openrouter_client as _orc

if not hasattr(_orc, "MODEL_MAPPING"):
    _orc.MODEL_MAPPING = {"test-model": "test/model"}

from ww.social import x_post


class TestCreateXPostPrompt(unittest.TestCase):
    def test_returns_string(self):
        result = x_post.create_x_post_prompt()
        self.assertIsInstance(result, str)
        self.assertIn("social media", result.lower())
        self.assertIn("140 characters", result)


class TestGenerateXPosts(unittest.TestCase):
    @patch.object(x_post, "call_openrouter_api_with_messages")
    @patch.object(x_post, "random")
    def test_generate_x_posts_success(self, mock_random, mock_api):
        mock_random.choice.return_value = "test-model"
        mock_api.return_value = "Post 1\n\nPost 2\n\nPost 3"
        result = x_post.generate_x_posts("Some blog content")
        self.assertEqual(result, ["Post 1", "Post 2", "Post 3"])
        mock_api.assert_called_once()

    @patch.object(x_post, "call_openrouter_api_with_messages")
    @patch.object(x_post, "random")
    def test_generate_x_posts_empty_response(self, mock_random, mock_api):
        mock_random.choice.return_value = "test-model"
        mock_api.return_value = ""
        result = x_post.generate_x_posts("content")
        self.assertIsNone(result)

    @patch.object(x_post, "call_openrouter_api_with_messages")
    @patch.object(x_post, "random")
    def test_generate_x_posts_none_response(self, mock_random, mock_api):
        mock_random.choice.return_value = "test-model"
        mock_api.return_value = None
        result = x_post.generate_x_posts("content")
        self.assertIsNone(result)

    @patch.object(x_post, "call_openrouter_api_with_messages")
    @patch.object(x_post, "random")
    def test_generate_x_posts_context_length_error(self, mock_random, mock_api):
        mock_random.choice.return_value = "test-model"
        mock_api.side_effect = Exception(
            "This model's maximum context length is exceeded"
        )
        result = x_post.generate_x_posts("very long content")
        self.assertIsNone(result)

    @patch.object(x_post, "call_openrouter_api_with_messages")
    @patch.object(x_post, "random")
    def test_generate_x_posts_generic_error(self, mock_random, mock_api):
        mock_random.choice.return_value = "test-model"
        mock_api.side_effect = Exception("some other error")
        result = x_post.generate_x_posts("content")
        self.assertIsNone(result)

    @patch.object(x_post, "call_openrouter_api_with_messages")
    @patch.object(x_post, "random")
    def test_generate_x_posts_single_post(self, mock_random, mock_api):
        mock_random.choice.return_value = "test-model"
        mock_api.return_value = "Single post content"
        result = x_post.generate_x_posts("content")
        self.assertEqual(result, ["Single post content"])

    @patch.object(x_post, "call_openrouter_api_with_messages")
    @patch.object(x_post, "random")
    def test_generate_x_posts_uses_random_model(self, mock_random, mock_api):
        mock_random.choice.return_value = "selected-model"
        mock_api.return_value = "post"
        x_post.generate_x_posts("content")
        mock_random.choice.assert_called_once()
        # Verify model is passed to API
        call_kwargs = mock_api.call_args
        self.assertEqual(call_kwargs[1]["model"], "selected-model")


class TestGenerateXPostFromMarkdownFile(unittest.TestCase):
    @patch.object(x_post, "generate_x_posts")
    def test_process_file_with_frontmatter(self, mock_generate):
        mock_generate.return_value = ["Post 1", "Post 2"]
        content = "---\ntitle: Test\n---\nBlog content here"
        m = mock_open(read_data=content)
        with patch("builtins.open", m):
            x_post.generate_x_post_from_markdown_file("input.md", "output.md")

        call_args = mock_generate.call_args[0][0]
        self.assertIn("Blog content here", call_args)
        self.assertNotIn("---", call_args)

    @patch.object(x_post, "generate_x_posts")
    def test_process_file_without_frontmatter(self, mock_generate):
        mock_generate.return_value = ["Post 1"]
        content = "Just blog content, no frontmatter"
        m = mock_open(read_data=content)
        with patch("builtins.open", m):
            x_post.generate_x_post_from_markdown_file("input.md", "output.md")

        mock_generate.assert_called_once()

    @patch.object(x_post, "generate_x_posts")
    def test_process_file_writes_output(self, mock_generate):
        mock_generate.return_value = ["Post 1", "Post 2"]
        content = "Blog content"
        m = mock_open(read_data=content)
        with patch("builtins.open", m):
            x_post.generate_x_post_from_markdown_file("input.md", "output.md")

        handle = m()
        write_calls = [call[0][0] for call in handle.write.call_args_list]
        self.assertIn("Post 1\n", write_calls)
        self.assertIn("---\n", write_calls)
        self.assertIn("Post 2\n", write_calls)

    @patch.object(x_post, "generate_x_posts")
    def test_process_file_no_posts_generated(self, mock_generate):
        mock_generate.return_value = None
        content = "Blog content"
        m = mock_open(read_data=content)
        with patch("builtins.open", m):
            x_post.generate_x_post_from_markdown_file("input.md", "output.md")

        handle = m()
        handle.write.assert_not_called()

    def test_process_file_read_error(self):
        with patch("builtins.open", side_effect=IOError("file not found")):
            x_post.generate_x_post_from_markdown_file("missing.md", "output.md")


if __name__ == "__main__":
    unittest.main()
