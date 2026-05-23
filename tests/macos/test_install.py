import os
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestInstallMain(unittest.TestCase):
    @patch("ww.macos.install.subprocess.run")
    @patch("sys.argv", ["install", "requests"])
    def test_installs_package(self, mock_run):
        from ww.macos.install import main

        main()
        mock_run.assert_called_once_with(
            [
                "/opt/homebrew/bin/python3",
                "-m",
                "pip",
                "install",
                "requests",
                "--break-system-packages",
            ]
        )

    @patch("ww.macos.install.subprocess.run")
    @patch("sys.argv", ["install", "numpy"])
    def test_installs_different_package(self, mock_run):
        from ww.macos.install import main

        main()
        call_args = mock_run.call_args[0][0]
        self.assertIn("numpy", call_args)
        self.assertIn("--break-system-packages", call_args)

    @patch("sys.argv", ["install"])
    def test_missing_package_arg_exits(self):
        from ww.macos.install import main

        with self.assertRaises(SystemExit):
            main()


if __name__ == "__main__":
    unittest.main()
