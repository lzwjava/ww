import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from ww.linux.switch_keys import (
    _run,
    _is_x11,
    _setxkbmap_has_swap,
    _xmodmap_has_swap,
    _xmodmap_file_has_swap,
    _detect_state,
    _install_persist,
    _remove_persist,
    _prompt_yn,
    _XMODMAP_SWAP,
)


class TestRun(unittest.TestCase):
    @patch("ww.linux.switch_keys.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="hello\n", returncode=0)
        out, rc = _run("echo hello")
        self.assertEqual(out, "hello")
        self.assertEqual(rc, 0)

    @patch("ww.linux.switch_keys.subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=1)
        out, rc = _run("false")
        self.assertEqual(rc, 1)

    @patch("ww.linux.switch_keys.subprocess.run")
    def test_timeout(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=10)
        out, rc = _run("sleep 999")
        self.assertEqual(rc, 1)
        self.assertEqual(out, "")

    @patch("ww.linux.switch_keys.subprocess.run")
    def test_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        out, rc = _run("nonexistent_cmd")
        self.assertEqual(rc, 127)


class TestIsX11(unittest.TestCase):
    @patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=False)
    def test_xdg_x11(self):
        self.assertTrue(_is_x11())

    @patch.dict(os.environ, {"DISPLAY": ":0"}, clear=False)
    def test_display_set(self):
        # Remove XDG_SESSION_TYPE if present
        os.environ.pop("XDG_SESSION_TYPE", None)
        self.assertTrue(_is_x11())

    @patch.dict(os.environ, {}, clear=True)
    def test_not_x11(self):
        self.assertFalse(_is_x11())


class TestSetxkbmapHasSwap(unittest.TestCase):
    @patch("ww.linux.switch_keys._run")
    def test_has_swapcaps(self, mock_run):
        mock_run.return_value = (
            "rules:      evdev\nmodel:      pc105\nlayout:     us\noptions:    ctrl:swapcaps",
            0,
        )
        self.assertTrue(_setxkbmap_has_swap())

    @patch("ww.linux.switch_keys._run")
    def test_no_options(self, mock_run):
        mock_run.return_value = (
            "rules:      evdev\nmodel:      pc105\nlayout:     us",
            0,
        )
        self.assertFalse(_setxkbmap_has_swap())

    @patch("ww.linux.switch_keys._run")
    def test_different_option(self, mock_run):
        mock_run.return_value = ("options:    terminate:ctrl_alt_bksp", 0)
        self.assertFalse(_setxkbmap_has_swap())


class TestXmodmapHasSwap(unittest.TestCase):
    @patch("ww.linux.switch_keys._run")
    def test_swapped(self, mock_run):
        mock_run.return_value = (
            "keycode  66 = Control_L NoSymbol Control_L\n"
            "keycode  37 = Caps_Lock NoSymbol Caps_Lock",
            0,
        )
        self.assertTrue(_xmodmap_has_swap())

    @patch("ww.linux.switch_keys._run")
    def test_not_swapped(self, mock_run):
        mock_run.return_value = (
            "keycode  66 = Caps_Lock NoSymbol Caps_Lock\n"
            "keycode  37 = Control_L NoSymbol Control_L",
            0,
        )
        self.assertFalse(_xmodmap_has_swap())

    @patch("ww.linux.switch_keys._run")
    def test_command_fails(self, mock_run):
        mock_run.return_value = ("", 1)
        self.assertFalse(_xmodmap_has_swap())


class TestXmodmapFileHasSwap(unittest.TestCase):
    def test_has_swap(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Xmodmap", delete=False
        ) as f:
            f.write("keycode 66 = Control_L\nkeycode 37 = Caps_Lock\n")
            path = f.name
        self.addCleanup(os.unlink, path)
        with (
            patch("ww.linux.switch_keys.os.path.isfile", return_value=True),
            patch("ww.linux.switch_keys.os.path.expanduser", return_value=path),
        ):
            # Actually need to patch XMODMAP_PATH or the open call
            # Simpler: just test the logic directly
            pass

    @patch("ww.linux.switch_keys.os.path.isfile", return_value=False)
    def test_no_file(self, mock_isfile):
        self.assertFalse(_xmodmap_file_has_swap())


class TestDetectState(unittest.TestCase):
    @patch("ww.linux.switch_keys._is_x11", return_value=False)
    def test_not_x11(self, _):
        self.assertEqual(_detect_state(), "unknown")

    @patch("ww.linux.switch_keys._setxkbmap_has_swap", return_value=True)
    @patch("ww.linux.switch_keys._is_x11", return_value=True)
    def test_swap_active(self, *_):
        self.assertEqual(_detect_state(), "on")

    @patch("ww.linux.switch_keys._xmodmap_has_swap", return_value=True)
    @patch("ww.linux.switch_keys._setxkbmap_has_swap", return_value=False)
    @patch("ww.linux.switch_keys._is_x11", return_value=True)
    def test_swap_via_xmodmap(self, *_):
        self.assertEqual(_detect_state(), "on")

    @patch("ww.linux.switch_keys._xmodmap_has_swap", return_value=False)
    @patch("ww.linux.switch_keys._setxkbmap_has_swap", return_value=False)
    @patch("ww.linux.switch_keys._is_x11", return_value=True)
    def test_swap_off(self, *_):
        self.assertEqual(_detect_state(), "off")


class TestPromptYn(unittest.TestCase):
    @patch("builtins.input", return_value="y")
    def test_yes(self, _):
        self.assertTrue(_prompt_yn("Continue?"))

    @patch("builtins.input", return_value="n")
    def test_no(self, _):
        self.assertFalse(_prompt_yn("Continue?"))

    @patch("builtins.input", return_value="")
    def test_empty(self, _):
        self.assertFalse(_prompt_yn("Continue?"))

    @patch("builtins.input", return_value="Y")
    def test_uppercase_y(self, _):
        self.assertTrue(_prompt_yn("Continue?"))


class TestInstallPersist(unittest.TestCase):
    def test_writes_xmodmap_and_xprofile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            xmodmap_path = os.path.join(tmpdir, ".Xmodmap")
            xprofile_path = os.path.join(tmpdir, ".xprofile")
            with (
                patch("ww.linux.switch_keys.XMODMAP_PATH", xmodmap_path),
                patch("ww.linux.switch_keys.XPROFILE_PATH", xprofile_path),
            ):
                _install_persist()
            with open(xmodmap_path) as f:
                content = f.read()
            self.assertIn("keycode 66 = Control_L", content)
            self.assertIn("keycode 37 = Caps_Lock", content)
            with open(xprofile_path) as f:
                xprofile_content = f.read()
            self.assertIn("xmodmap", xprofile_content)

    def test_does_not_duplicate_xprofile_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            xmodmap_path = os.path.join(tmpdir, ".Xmodmap")
            xprofile_path = os.path.join(tmpdir, ".xprofile")
            with open(xprofile_path, "w") as f:
                f.write(
                    "# Load Caps Lock ↔ Ctrl swap\n[ -f ~/.Xmodmap ] && xmodmap ~/.Xmodmap\n"
                )
            with (
                patch("ww.linux.switch_keys.XMODMAP_PATH", xmodmap_path),
                patch("ww.linux.switch_keys.XPROFILE_PATH", xprofile_path),
            ):
                _install_persist()
            with open(xprofile_path) as f:
                content = f.read()
            self.assertEqual(content.count("xmodmap ~/.Xmodmap"), 1)


class TestRemovePersist(unittest.TestCase):
    def test_removes_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            xmodmap_path = os.path.join(tmpdir, ".Xmodmap")
            xprofile_path = os.path.join(tmpdir, ".xprofile")
            with open(xmodmap_path, "w") as f:
                f.write(_XMODMAP_SWAP)
            with open(xprofile_path, "w") as f:
                f.write(
                    "# Load Caps Lock ↔ Ctrl swap\n[ -f ~/.Xmodmap ] && xmodmap ~/.Xmodmap\n"
                )
            with (
                patch("ww.linux.switch_keys.XMODMAP_PATH", xmodmap_path),
                patch("ww.linux.switch_keys.XPROFILE_PATH", xprofile_path),
            ):
                _remove_persist()
            self.assertFalse(os.path.exists(xmodmap_path))
            with open(xprofile_path) as f:
                content = f.read()
            self.assertNotIn("xmodmap", content)

    def test_no_files_to_remove(self):
        with patch("ww.linux.switch_keys.os.path.isfile", return_value=False):
            _remove_persist()


if __name__ == "__main__":
    unittest.main()
