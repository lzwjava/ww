import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestReadClipboard(unittest.TestCase):
    @patch("subprocess.run")
    def test_returns_stripped_text(self, mock_run):
        from ww.llm.compare import read_clipboard

        mock_run.return_value = MagicMock(stdout="  hello world  \n")
        result = read_clipboard()
        self.assertEqual(result, "hello world")

    @patch("subprocess.run")
    def test_returns_empty_when_clipboard_empty(self, mock_run):
        from ww.llm.compare import read_clipboard

        mock_run.return_value = MagicMock(stdout="")
        result = read_clipboard()
        self.assertEqual(result, "")


class TestQueryModel(unittest.TestCase):
    @patch("ww.llm.compare.call_openrouter_api", return_value="answer text")
    def test_returns_label_and_answer(self, mock_api):
        from ww.llm.compare import query_model

        label, answer = query_model("gpt", "openai/gpt-4", "prompt")
        self.assertEqual(label, "gpt")
        self.assertEqual(answer, "answer text")

    @patch("ww.llm.compare.call_openrouter_api", side_effect=Exception("API down"))
    def test_returns_error_on_exception(self, mock_api):
        from ww.llm.compare import query_model

        label, answer = query_model("gpt", "openai/gpt-4", "prompt")
        self.assertEqual(label, "gpt")
        self.assertIn("ERROR", answer)


class TestJudgeResponses(unittest.TestCase):
    @patch("ww.llm.compare.call_openrouter_api", return_value="Model A is best")
    def test_calls_judge_model(self, mock_api):
        from ww.llm.compare import judge_responses

        responses = [("gpt", "answer1"), ("claude", "answer2")]
        result = judge_responses("question", responses)
        self.assertEqual(result, "Model A is best")
        mock_api.assert_called_once()


class TestMain(unittest.TestCase):
    @patch("ww.llm.compare.judge_responses", return_value="winner")
    @patch("ww.llm.compare.read_clipboard", return_value="question")
    def test_runs_comparison(self, mock_clip, mock_judge):
        from ww.llm.compare import main, MODELS

        # Mock query_model to return valid labels from MODELS
        with patch("ww.llm.compare.query_model") as mock_query:
            mock_query.side_effect = lambda label, model_id, prompt: (
                label,
                f"answer from {label}",
            )
            main()
            self.assertEqual(mock_query.call_count, len(MODELS))

    @patch("ww.llm.compare.read_clipboard", return_value="")
    def test_exits_on_empty_clipboard(self, mock_clip):
        from ww.llm.compare import main

        with self.assertRaises(SystemExit):
            main()
