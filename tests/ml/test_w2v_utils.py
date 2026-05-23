import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

import numpy as np
import torch
from ww.ml.word_vectors.w2v_utils import (
    build_dataset,
    read_glove_vecs,
    Word2VecModel,
    SkipGramDataset,
    relu,
    softmax,
    SimilarityCallback,
)


class TestBuildDataset(unittest.TestCase):
    def test_basic_build(self):
        words = ["the", "cat", "sat", "the", "dog", "the", "cat"]
        data, count, dictionary, reverse_dictionary = build_dataset(words, 5)
        self.assertEqual(dictionary["UNK"], 0)
        self.assertIn("the", dictionary)
        self.assertEqual(len(data), len(words))
        for idx, word in reverse_dictionary.items():
            self.assertEqual(dictionary[word], idx)

    def test_all_unknown_words(self):
        words = ["rare1", "rare2", "rare3"]
        data, count, dictionary, reverse_dictionary = build_dataset(words, 2)
        self.assertIn("UNK", [c[0] for c in count])
        # With n_words=2, dictionary has UNK + 1 most common word
        # So at most 2 distinct indices; at least some should be UNK (0)
        self.assertIn(0, data)

    def test_empty_word_list(self):
        words = []
        data, count, dictionary, reverse_dictionary = build_dataset(words, 5)
        self.assertEqual(len(data), 0)
        self.assertIn("UNK", dictionary)

    def test_single_word(self):
        words = ["hello"]
        data, count, dictionary, reverse_dictionary = build_dataset(words, 5)
        self.assertEqual(len(data), 1)
        self.assertIn("hello", dictionary)

    def test_n_words_limit(self):
        words = ["a", "b", "c", "a", "b", "a"]
        data, count, dictionary, reverse_dictionary = build_dataset(words, 3)
        self.assertEqual(len(dictionary), 3)


class TestReadGloveVecs(unittest.TestCase):
    def test_read_valid_file(self):
        import tempfile

        content = "hello 0.1 0.2 0.3\nworld 0.4 0.5 0.6\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            words, vec_map = read_glove_vecs(path)
            self.assertIn("hello", words)
            self.assertIn("world", words)
            np.testing.assert_array_almost_equal(vec_map["hello"], [0.1, 0.2, 0.3])
            np.testing.assert_array_almost_equal(vec_map["world"], [0.4, 0.5, 0.6])
        finally:
            os.unlink(path)

    def test_read_single_word(self):
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test 1.0 2.0\n")
            path = f.name
        try:
            words, vec_map = read_glove_vecs(path)
            self.assertEqual(len(words), 1)
            self.assertIn("test", vec_map)
        finally:
            os.unlink(path)


class TestWord2VecModel(unittest.TestCase):
    def test_model_creation(self):
        model = Word2VecModel(vocab_size=100, embedding_dim=50)
        self.assertEqual(model.vocab_size, 100)
        self.assertEqual(model.embedding_dim, 50)

    def test_forward_pass(self):
        model = Word2VecModel(vocab_size=10, embedding_dim=5)
        center = torch.tensor([0, 1, 2])
        context = torch.tensor([3, 4, 5])
        output = model(center, context)
        self.assertEqual(output.shape, (3,))

    def test_embedding_shapes(self):
        model = Word2VecModel(vocab_size=20, embedding_dim=10)
        self.assertEqual(model.in_embeddings.weight.shape, (20, 10))
        self.assertEqual(model.out_embeddings.weight.shape, (20, 10))


class TestSkipGramDataset(unittest.TestCase):
    def test_pairs_generation(self):
        data = [0, 1, 2, 3, 4]
        dataset = SkipGramDataset(data, window_size=1)
        self.assertTrue(len(dataset) > 0)

    def test_len(self):
        data = [0, 1, 2]
        dataset = SkipGramDataset(data, window_size=1)
        self.assertEqual(len(dataset), 4)

    def test_getitem(self):
        data = [10, 20, 30]
        dataset = SkipGramDataset(data, window_size=1)
        center, context = dataset[0]
        self.assertIsInstance(center, torch.Tensor)
        self.assertIsInstance(context, torch.Tensor)

    def test_empty_data(self):
        data = []
        dataset = SkipGramDataset(data, window_size=1)
        self.assertEqual(len(dataset), 0)

    def test_single_element(self):
        data = [5]
        dataset = SkipGramDataset(data, window_size=2)
        self.assertEqual(len(dataset), 0)


class TestMaybeDownload(unittest.TestCase):
    @patch("ww.ml.word_vectors.w2v_utils.os.path.exists")
    @patch("ww.ml.word_vectors.w2v_utils.os.stat")
    def test_file_exists_correct_size(self, mock_stat, mock_exists):
        mock_exists.return_value = True
        mock_stat.return_value = MagicMock(st_size=12345)
        from ww.ml.word_vectors.w2v_utils import maybe_download

        result = maybe_download("test.zip", "http://example.com/", 12345)
        self.assertEqual(result, "test.zip")

    @patch("ww.ml.word_vectors.w2v_utils.os.path.exists")
    @patch("ww.ml.word_vectors.w2v_utils.os.stat")
    def test_file_exists_wrong_size(self, mock_stat, mock_exists):
        mock_exists.return_value = True
        mock_stat.return_value = MagicMock(st_size=999)
        from ww.ml.word_vectors.w2v_utils import maybe_download

        with self.assertRaises(Exception) as ctx:
            maybe_download("test.zip", "http://example.com/", 12345)
        self.assertIn("Failed to verify", str(ctx.exception))

    @patch("ww.ml.word_vectors.w2v_utils.os.path.exists")
    @patch("ww.ml.word_vectors.w2v_utils.os.stat")
    @patch("ww.ml.word_vectors.w2v_utils.urllib.request.urlretrieve")
    def test_file_not_exists_downloads(self, mock_retrieve, mock_stat, mock_exists):
        mock_exists.return_value = False
        mock_retrieve.return_value = ("test.zip", None)
        mock_stat.return_value = MagicMock(st_size=12345)
        from ww.ml.word_vectors.w2v_utils import maybe_download

        result = maybe_download("test.zip", "http://example.com/", 12345)
        self.assertEqual(result, "test.zip")
        mock_retrieve.assert_called_once()


class TestInitializeParameters(unittest.TestCase):
    def test_shapes(self):
        from ww.ml.word_vectors.w2v_utils import initialize_parameters

        params = initialize_parameters(100, 64)
        self.assertEqual(params["W1"].shape, (64, 100))
        self.assertEqual(params["b1"].shape, (64, 1))
        self.assertEqual(params["W2"].shape, (100, 64))
        self.assertEqual(params["b2"].shape, (100, 1))

    def test_biases_are_zeros(self):
        from ww.ml.word_vectors.w2v_utils import initialize_parameters

        params = initialize_parameters(50, 32)
        np.testing.assert_array_equal(params["b1"].numpy(), np.zeros((32, 1)))
        np.testing.assert_array_equal(params["b2"].numpy(), np.zeros((50, 1)))

    def test_deterministic(self):
        from ww.ml.word_vectors.w2v_utils import initialize_parameters

        p1 = initialize_parameters(10, 5)
        p2 = initialize_parameters(10, 5)
        np.testing.assert_array_equal(p1["W1"].numpy(), p2["W1"].numpy())


class TestReluSoftmax(unittest.TestCase):
    def test_relu_positive(self):
        x = torch.tensor([1.0, 2.0, 3.0])
        result = relu(x)
        np.testing.assert_array_equal(result.numpy(), [1.0, 2.0, 3.0])

    def test_relu_negative(self):
        x = torch.tensor([-1.0, -2.0, 3.0])
        result = relu(x)
        np.testing.assert_array_equal(result.numpy(), [0.0, 0.0, 3.0])

    def test_softmax_sums_to_1(self):
        x = torch.tensor([1.0, 2.0, 3.0])
        result = softmax(x)
        self.assertAlmostEqual(result.sum().item(), 1.0, places=5)


class TestSimilarityCallback(unittest.TestCase):
    def test_get_sim(self):
        model = Word2VecModel(vocab_size=10, embedding_dim=5)
        reverse_dict = {i: f"word_{i}" for i in range(10)}
        device = torch.device("cpu")
        callback = SimilarityCallback(model, reverse_dict, device)
        with torch.no_grad():
            sim = callback._get_sim(0)
        self.assertEqual(len(sim), 10)
        self.assertAlmostEqual(sim[0], 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
