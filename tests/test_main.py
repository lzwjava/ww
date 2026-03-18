import sys
import unittest
from unittest.mock import patch

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestMainNoArgs(unittest.TestCase):
    def test_prints_hello_world_when_no_args(self):
        from ww.main import main

        with patch.object(sys, "argv", ["ww"]):
            with patch("builtins.print") as mock_print:
                main()
                mock_print.assert_any_call("hello world")

    def test_help_flag(self):
        from ww.main import main

        with patch.object(sys, "argv", ["ww", "--help"]):
            with patch("builtins.print"):
                main()


class TestMainUnknownCommand(unittest.TestCase):
    def test_exits_on_unknown_command(self):
        from ww.main import main

        with patch.object(sys, "argv", ["ww", "unknown-command"]):
            with self.assertRaises(SystemExit):
                main()


class TestMainDispatch(unittest.TestCase):
    """Test that each command dispatches to the correct sub-main function."""

    def _run(self, argv, mock_target):
        with patch.object(sys, "argv", argv):
            with patch(mock_target) as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    # note
    def test_create_log_dispatches(self):
        with patch.object(sys, "argv", ["ww", "note", "log"]):
            with patch("ww.note.create_log.create_log") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    # gif
    def test_gif_dispatches(self):
        self._run(["ww", "gif"], "ww.gif.gif.main")

    # macos
    def test_find_large_dirs_dispatches(self):
        self._run(
            ["ww", "macos", "find-large-dirs"], "ww.macos.find_largest_directories.main"
        )

    def test_system_info_dispatches(self):
        self._run(["ww", "macos", "system-info"], "ww.macos.get_system_info.main")

    def test_mac_install_dispatches(self):
        self._run(["ww", "macos", "install"], "ww.macos.install.main")

    def test_list_fonts_dispatches(self):
        from unittest.mock import MagicMock

        mock_module = MagicMock()
        with patch.dict("sys.modules", {"ww.macos.list_fonts": mock_module}):
            with patch.object(sys, "argv", ["ww", "macos", "list-fonts"]):
                from ww.main import main

                main()
                mock_module.main.assert_called_once()

    def test_list_disks_dispatches(self):
        self._run(["ww", "macos", "list-disks"], "ww.macos.list_portable_disks.main")

    def test_open_terminal_dispatches(self):
        self._run(["ww", "macos", "open-terminal"], "ww.macos.open_terminal.main")

    def test_toast_dispatches(self):
        self._run(["ww", "macos", "toast"], "ww.macos.toast.main")

    # image
    def test_avatar_dispatches(self):
        self._run(["ww", "image", "avatar"], "ww.image.avatar.main")

    def test_crop_dispatches(self):
        self._run(["ww", "image", "crop"], "ww.image.crop.main")

    def test_remove_bg_dispatches(self):
        self._run(["ww", "image", "remove-bg"], "ww.image.remove_bg.main")

    def test_screenshot_dispatches(self):
        self._run(["ww", "image", "screenshot"], "ww.image.screenshot.main")

    def test_screenshot_linux_dispatches(self):
        self._run(["ww", "image", "screenshot-linux"], "ww.image.screenshot_linux.main")

    def test_image_compress_dispatches(self):
        self._run(["ww", "image", "compress"], "ww.image.image_compress.main")

    def test_photo_compress_dispatches(self):
        self._run(["ww", "image", "photo-compress"], "ww.image.photo_compress.main")

    # proc
    def test_kill_by_pattern_dispatches(self):
        self._run(["ww", "proc", "kill-pattern"], "ww.proc.kill_by_pattern.main")

    def test_kill_by_port_dispatches(self):
        self._run(["ww", "proc", "kill-port"], "ww.proc.kill_by_port.main")

    def test_kill_jekyll_dispatches(self):
        self._run(["ww", "proc", "kill-jekyll"], "ww.proc.kill_jekyll.main")

    def test_kill_macos_proxy_dispatches(self):
        self._run(["ww", "proc", "kill-proxy"], "ww.proc.kill_macos_proxy.main")

    # utils
    def test_base64_dispatches(self):
        self._run(["ww", "utils", "base64"], "ww.utils.base64utils.main")

    def test_ccr_dispatches(self):
        self._run(["ww", "utils", "ccr"], "ww.utils.ccr.main")

    def test_clean_zip_dispatches(self):
        self._run(["ww", "utils", "clean-zip"], "ww.utils.clean_zip.main")

    def test_decode_jwt_dispatches(self):
        self._run(["ww", "utils", "decode-jwt"], "ww.utils.decode_jwt.main")

    def test_py2txt_dispatches(self):
        self._run(["ww", "utils", "py2txt"], "ww.utils.py2txt.main")

    def test_request_proxy_dispatches(self):
        self._run(["ww", "utils", "request-proxy"], "ww.utils.request_with_proxy.main")

    def test_smart_unzip_dispatches(self):
        self._run(["ww", "utils", "smart-unzip"], "ww.utils.smart_unzip.main")

    def test_unzip_dispatches(self):
        self._run(["ww", "utils", "unzip"], "ww.utils.unzip.main")

    # java
    def test_mvn_dispatches(self):
        self._run(["ww", "java", "mvn"], "ww.java.mvn.main")

    # network
    def test_get_wifi_list_dispatches(self):
        self._run(["ww", "network", "get-wifi-list"], "ww.network.get_wifi_list.main")

    def test_save_wifi_list_dispatches(self):
        self._run(["ww", "network", "save-wifi-list"], "ww.network.save_wifi_list.main")

    def test_hack_wifi_dispatches(self):
        self._run(["ww", "network", "hack-wifi"], "ww.network.hack_wifi.main")

    def test_wifi_gen_password_dispatches(self):
        self._run(
            ["ww", "network", "wifi-gen-password"], "ww.network.generate_password.main"
        )

    def test_ip_scan_dispatches(self):
        self._run(["ww", "network", "ip-scan"], "ww.network.ip_scan.main")

    def test_port_scan_dispatches(self):
        self._run(["ww", "network", "port-scan"], "ww.network.port_scan.main")

    def test_wifi_scan_dispatches(self):
        self._run(["ww", "network", "wifi-scan"], "ww.network.wifi_scan.main")

    def test_wifi_util_dispatches(self):
        self._run(["ww", "network", "wifi-util"], "ww.network.wifi_util.main")

    def test_network_plot_dispatches(self):
        self._run(["ww", "network", "network-plot"], "ww.network.network_plot.main")


if __name__ == "__main__":
    unittest.main()
