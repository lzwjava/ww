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
                mock_print.assert_called_with("hello world")


class TestMainUnknownCommand(unittest.TestCase):
    def test_exits_on_unknown_command(self):
        from ww.main import main

        with patch.object(sys, "argv", ["ww", "unknown-command"]):
            with self.assertRaises(SystemExit):
                main()


class TestMainDispatch(unittest.TestCase):
    """Test that each command dispatches to the correct sub-main function."""

    def _run_cmd(self, args, mock_target, extra_argv=None):
        """Patch mock_target, set sys.argv to args, call main(), assert called."""
        argv = args if extra_argv is None else args + extra_argv
        with patch.object(sys, "argv", argv):
            with patch(mock_target) as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_create_log_dispatches(self):
        with patch.object(sys, "argv", ["ww", "create-log"]):
            with patch("ww.create.create_log.create_log") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_find_large_dirs_dispatches(self):
        with patch.object(sys, "argv", ["ww", "find-large-dirs"]):
            with patch("ww.macos.find_largest_directories.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_system_info_dispatches(self):
        with patch.object(sys, "argv", ["ww", "system-info"]):
            with patch("ww.macos.get_system_info.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_mac_install_dispatches(self):
        with patch.object(sys, "argv", ["ww", "mac-install"]):
            with patch("ww.macos.install.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_list_fonts_dispatches(self):
        from unittest.mock import MagicMock

        mock_module = MagicMock()
        with patch.dict("sys.modules", {"ww.macos.list_fonts": mock_module}):
            with patch.object(sys, "argv", ["ww", "list-fonts"]):
                from ww.main import main

                main()
                mock_module.main.assert_called_once()

    def test_list_disks_dispatches(self):
        with patch.object(sys, "argv", ["ww", "list-disks"]):
            with patch("ww.macos.list_portable_disks.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_open_terminal_dispatches(self):
        with patch.object(sys, "argv", ["ww", "open-terminal"]):
            with patch("ww.macos.open_terminal.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_toast_dispatches(self):
        with patch.object(sys, "argv", ["ww", "toast"]):
            with patch("ww.macos.toast.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_avatar_dispatches(self):
        with patch.object(sys, "argv", ["ww", "avatar"]):
            with patch("ww.image.avatar.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_crop_dispatches(self):
        with patch.object(sys, "argv", ["ww", "crop"]):
            with patch("ww.image.crop.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_remove_bg_dispatches(self):
        with patch.object(sys, "argv", ["ww", "remove-bg"]):
            with patch("ww.image.remove_bg.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_screenshot_dispatches(self):
        with patch.object(sys, "argv", ["ww", "screenshot"]):
            with patch("ww.image.screenshot.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_screenshot_linux_dispatches(self):
        with patch.object(sys, "argv", ["ww", "screenshot-linux"]):
            with patch("ww.image.screenshot_linux.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_image_compress_dispatches(self):
        with patch.object(sys, "argv", ["ww", "image-compress"]):
            with patch("ww.image.image_compress.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_photo_compress_dispatches(self):
        with patch.object(sys, "argv", ["ww", "photo-compress"]):
            with patch("ww.image.photo_compress.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_kill_by_pattern_dispatches(self):
        with patch.object(sys, "argv", ["ww", "kill-by-pattern"]):
            with patch("ww.proc.kill_by_pattern.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_kill_by_port_dispatches(self):
        with patch.object(sys, "argv", ["ww", "kill-by-port"]):
            with patch("ww.proc.kill_by_port.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_kill_jekyll_dispatches(self):
        with patch.object(sys, "argv", ["ww", "kill-jekyll"]):
            with patch("ww.proc.kill_jekyll.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_kill_macos_proxy_dispatches(self):
        with patch.object(sys, "argv", ["ww", "kill-macos-proxy"]):
            with patch("ww.proc.kill_macos_proxy.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_base64_dispatches(self):
        with patch.object(sys, "argv", ["ww", "base64"]):
            with patch("ww.utils.base64utils.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_ccr_dispatches(self):
        with patch.object(sys, "argv", ["ww", "ccr"]):
            with patch("ww.utils.ccr.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_clean_zip_dispatches(self):
        with patch.object(sys, "argv", ["ww", "clean-zip"]):
            with patch("ww.utils.clean_zip.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_decode_jwt_dispatches(self):
        with patch.object(sys, "argv", ["ww", "decode-jwt"]):
            with patch("ww.utils.decode_jwt.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_py2txt_dispatches(self):
        with patch.object(sys, "argv", ["ww", "py2txt"]):
            with patch("ww.utils.py2txt.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_request_proxy_dispatches(self):
        with patch.object(sys, "argv", ["ww", "request-proxy"]):
            with patch("ww.utils.request_with_proxy.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_smart_unzip_dispatches(self):
        with patch.object(sys, "argv", ["ww", "smart-unzip"]):
            with patch("ww.utils.smart_unzip.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_unzip_dispatches(self):
        with patch.object(sys, "argv", ["ww", "unzip"]):
            with patch("ww.utils.unzip.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_mvn_dispatches(self):
        with patch.object(sys, "argv", ["ww", "mvn"]):
            with patch("ww.java.mvn.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_get_wifi_list_dispatches(self):
        with patch.object(sys, "argv", ["ww", "get-wifi-list"]):
            with patch("ww.network.get_wifi_list.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_save_wifi_list_dispatches(self):
        with patch.object(sys, "argv", ["ww", "save-wifi-list"]):
            with patch("ww.network.save_wifi_list.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_hack_wifi_dispatches(self):
        with patch.object(sys, "argv", ["ww", "hack-wifi"]):
            with patch("ww.network.hack_wifi.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_wifi_gen_password_dispatches(self):
        with patch.object(sys, "argv", ["ww", "wifi-gen-password"]):
            with patch("ww.network.generate_password.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_ip_scan_dispatches(self):
        with patch.object(sys, "argv", ["ww", "ip-scan"]):
            with patch("ww.network.ip_scan.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_port_scan_dispatches(self):
        with patch.object(sys, "argv", ["ww", "port-scan"]):
            with patch("ww.network.port_scan.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_wifi_scan_dispatches(self):
        with patch.object(sys, "argv", ["ww", "wifi-scan"]):
            with patch("ww.network.wifi_scan.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_wifi_util_dispatches(self):
        with patch.object(sys, "argv", ["ww", "wifi-util"]):
            with patch("ww.network.wifi_util.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_network_plot_dispatches(self):
        with patch.object(sys, "argv", ["ww", "network-plot"]):
            with patch("ww.network.network_plot.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_gif_dispatches(self):
        with patch.object(sys, "argv", ["ww", "gif"]):
            with patch("ww.gif.gif.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_github_readme_dispatches(self):
        with patch.object(sys, "argv", ["ww", "github-readme"]):
            with patch(
                "ww.github.readme.format_projects_to_markdown", return_value="md"
            ):
                with patch("builtins.print"):
                    from ww.main import main

                    main()


if __name__ == "__main__":
    unittest.main()
