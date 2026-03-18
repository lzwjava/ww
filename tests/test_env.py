import os
import tempfile
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestLoadEnv(unittest.TestCase):
    def setUp(self):
        self._orig_base = os.environ.pop("BASE_PATH", None)
        self._orig_sentinel = os.environ.pop("_WW_ENV_TEST_SENTINEL", None)

    def tearDown(self):
        if self._orig_base is not None:
            os.environ["BASE_PATH"] = self._orig_base
        else:
            os.environ.pop("BASE_PATH", None)
        os.environ.pop("_WW_ENV_TEST_SENTINEL", None)

    def test_load_env_succeeds_without_base_path(self):
        from ww.env import load_env

        # Should not raise even if BASE_PATH is unset
        load_env()

    def test_load_env_loads_base_path_dotenv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, ".env")
            with open(env_file, "w") as f:
                f.write("_WW_ENV_TEST_SENTINEL=from_base_path\n")

            os.environ["BASE_PATH"] = tmpdir
            from ww.env import load_env

            load_env()
            self.assertEqual(os.environ.get("_WW_ENV_TEST_SENTINEL"), "from_base_path")

    def test_load_env_skips_missing_base_path_dotenv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["BASE_PATH"] = tmpdir
            # No .env file in tmpdir
            from ww.env import load_env

            load_env()  # should not raise

    def test_load_env_ignores_dot_base_path(self):
        os.environ["BASE_PATH"] = "."
        from ww.env import load_env

        load_env()  # should not attempt to load ./.env specially (no error)

    def test_base_path_env_overrides_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, ".env")
            with open(env_file, "w") as f:
                f.write("_WW_ENV_TEST_SENTINEL=overridden\n")

            os.environ["BASE_PATH"] = tmpdir
            os.environ["_WW_ENV_TEST_SENTINEL"] = "original"
            from ww.env import load_env

            load_env()
            self.assertEqual(os.environ.get("_WW_ENV_TEST_SENTINEL"), "overridden")


if __name__ == "__main__":
    unittest.main()
