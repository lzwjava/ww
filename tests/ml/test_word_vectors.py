import os
import sys
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

try:
    import numpy as np

    # word_vectors.py uses bare 'from w2v_utils import *' (not relative),
    # so we need to add the package directory to sys.path for it to resolve.
    _wv_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "ww", "ml", "word_vectors"
    )
    _wv_dir = os.path.abspath(_wv_dir)
    if _wv_dir not in sys.path:
        sys.path.insert(0, _wv_dir)

    # Import the module - it handles missing files gracefully by creating sample vectors
    import ww.ml.word_vectors.word_vectors as wv_module

    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False


def setUpModule():
    if not _HAS_DEPS:
        raise unittest.SkipTest("Missing optional dependency: torch")


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: torch")
class TestCosineSimilarity(unittest.TestCase):
    def test_same_vector_returns_1(self):
        a = np.array([1.0, 2.0, 3.0])
        result = wv_module.cosine_similarity(a, a)
        self.assertAlmostEqual(result, 1.0, places=5)

    def test_opposite_vectors_returns_neg1(self):
        a = np.array([1.0, 2.0, 3.0])
        result = wv_module.cosine_similarity(a, -a)
        self.assertAlmostEqual(result, -1.0, places=5)

    def test_orthogonal_vectors_returns_0(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        result = wv_module.cosine_similarity(a, b)
        self.assertAlmostEqual(result, 0.0, places=5)

    def test_scale_independent(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 5.0, 6.0])
        r1 = wv_module.cosine_similarity(a, b)
        r2 = wv_module.cosine_similarity(a * 2, b * 4)
        self.assertAlmostEqual(r1, r2, places=5)


class TestCosineSimilarityNumpy(unittest.TestCase):
    def test_same_vector(self):
        a = np.array([1.0, 2.0, 3.0])
        result = wv_module.cosine_similarity_numpy(a, a)
        self.assertAlmostEqual(result, 1.0, places=5)

    def test_opposite_vectors(self):
        a = np.array([1.0, 2.0, 3.0])
        result = wv_module.cosine_similarity_numpy(a, -a)
        self.assertAlmostEqual(result, -1.0, places=5)

    def test_orthogonal(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        result = wv_module.cosine_similarity_numpy(a, b)
        self.assertAlmostEqual(result, 0.0, places=5)

    def test_zero_vector_returns_0(self):
        a = np.array([1.0, 2.0])
        z = np.array([0.0, 0.0])
        result = wv_module.cosine_similarity_numpy(a, z)
        self.assertEqual(result, 0)


class TestSafeGetWordVector(unittest.TestCase):
    def test_known_word(self):
        vec_map = {"hello": np.array([1.0, 2.0]), "world": np.array([3.0, 4.0])}
        result = wv_module.safe_get_word_vector("hello", vec_map, default_dim=2)
        np.testing.assert_array_equal(result, vec_map["hello"])

    def test_case_insensitive(self):
        vec_map = {"hello": np.array([1.0, 2.0])}
        result = wv_module.safe_get_word_vector("HELLO", vec_map, default_dim=2)
        np.testing.assert_array_equal(result, vec_map["hello"])

    def test_unknown_word_returns_random(self):
        vec_map = {"hello": np.array([1.0, 2.0])}
        result = wv_module.safe_get_word_vector("missing", vec_map, default_dim=50)
        self.assertEqual(len(result), 50)


class TestCompleteAnalogy(unittest.TestCase):
    def test_basic_analogy(self):
        a = np.array([3, 3])
        a_nw = np.array([2, 4])
        a_s = np.array([3, 2])
        c = np.array([-2, 1])
        vec_map = {
            "a": a,
            "a_nw": a_nw,
            "a_s": a_s,
            "c": c,
            "c_n": np.array([-2, 2]),
            "c_ne": np.array([-1, 2]),
            "c_e": np.array([-1, 1]),
            "c_se": np.array([-1, 0]),
            "c_s": np.array([-2, 0]),
            "c_sw": np.array([-3, 0]),
            "c_w": np.array([-3, 1]),
            "c_nw": np.array([-3, 2]),
        }
        result = wv_module.complete_analogy("a", "a_nw", "c", vec_map)
        self.assertEqual(result, "c_nw")

    def test_analogy_a_to_south(self):
        a = np.array([3, 3])
        a_s = np.array([3, 2])
        c = np.array([-2, 1])
        vec_map = {
            "a": a,
            "a_s": a_s,
            "c": c,
            "c_n": np.array([-2, 2]),
            "c_s": np.array([-2, 0]),
        }
        result = wv_module.complete_analogy("a", "a_s", "c", vec_map)
        self.assertEqual(result, "c_s")

    def test_missing_word_returns_none(self):
        vec_map = {"a": np.array([1, 2]), "b": np.array([3, 4])}
        result = wv_module.complete_analogy("a", "b", "missing", vec_map)
        self.assertIsNone(result)

    def test_best_word_not_input(self):
        a = np.array([3, 3])
        c = np.array([-2, 1])
        vec_map = {
            "a": a,
            "synonym_of_a": a,
            "c": c,
            "c_n": np.array([-2, 2]),
        }
        result = wv_module.complete_analogy("a", "synonym_of_a", "c", vec_map)
        self.assertNotEqual(result, "c")


class TestLoadOrCreateWordVectors(unittest.TestCase):
    def test_load_glove_format(self):
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello 0.1 0.2 0.3\nworld 0.4 0.5 0.6\n")
            path = f.name
        try:
            words, vec_map = wv_module.load_or_create_word_vectors(path)
            self.assertIn("hello", words)
            self.assertIn("world", words)
            self.assertEqual(len(vec_map["hello"]), 3)
        finally:
            os.unlink(path)

    def test_create_from_text_file(self):
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, dir="."
        ) as f:
            f.write("the cat sat on the mat and the dog ran in the park\n")
            path = f.name
        try:
            words, vec_map = wv_module.load_or_create_word_vectors(path)
            self.assertTrue(len(words) > 0)
            self.assertTrue(any(w in vec_map for w in ["the", "cat", "dog"]))
        finally:
            os.unlink(path)

    def test_nonexistent_file_creates_sample(self):
        words, vec_map = wv_module.load_or_create_word_vectors(
            "/nonexistent/path/file.txt"
        )
        self.assertIn("father", vec_map)
        self.assertIn("mother", vec_map)
        self.assertEqual(len(vec_map["father"]), 50)


if __name__ == "__main__":
    unittest.main()
