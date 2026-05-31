import sys
import unittest
from unittest.mock import patch, MagicMock

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


def _dispatch(argv, mock_target):
    """Helper: run main() with given argv while mocking the target path.

    Falls back to sys.modules injection if the target module can't be imported
    (e.g., macOS-only modules on Linux).
    """
    module_path, _, func_name = mock_target.rpartition(".")
    try:
        with patch.object(sys, "argv", argv):
            with patch(mock_target) as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()
                return mock_fn
    except (AttributeError, ModuleNotFoundError, ImportError):
        mock_module = MagicMock()
        with patch.dict("sys.modules", {module_path: mock_module}):
            with patch.object(sys, "argv", argv):
                from ww.main import main

                main()
                getattr(mock_module, func_name).assert_called_once()
                return getattr(mock_module, func_name)


def _dispatch_print(argv):
    """Helper: run main() with given argv, return the mock_print."""
    with patch.object(sys, "argv", argv):
        with patch("builtins.print") as mock_print:
            from ww.main import main

            main()
            return mock_print


def _dispatch_exit(test_case, argv):
    """Helper: assert main() calls sys.exit(1)."""
    with patch.object(sys, "argv", argv):
        with patch("builtins.print"):
            from ww.main import main

            with test_case.assertRaises(SystemExit):
                main()


# ---------------------------------------------------------------------------
# _print_help
# ---------------------------------------------------------------------------
class TestPrintHelp(unittest.TestCase):
    def test_print_help_contains_usage(self):
        from ww.main import _print_help

        with patch("builtins.print") as mock_print:
            _print_help()
            all_text = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("Usage: ww <group>", all_text)

    def test_print_help_covers_all_groups(self):
        from ww.main import _print_help

        with patch("builtins.print") as mock_print:
            _print_help()
            all_text = " ".join(str(c) for c in mock_print.call_args_list)
            for keyword in [
                "note",
                "screenshot",
                "GIF",
                "GitHub",
                "macOS",
                "Image",
                "Process",
                "Utils",
                "Java",
                "Network",
                "Git",
                "Update",
                "Latest",
                "search",
                "PDF",
                "Copilot",
                "Sync",
                "LLM",
                "Env",
                "Display",
                "Gen-image",
                "Action",
                "Degree",
                "Marp",
                "Whisper",
                "Linux",
                "Cloudflare",
                "Clash",
            ]:
                self.assertIn(keyword, all_text, f"Help missing keyword: {keyword}")


# ---------------------------------------------------------------------------
# _pop_subcmd
# ---------------------------------------------------------------------------
class TestPopSubcmd(unittest.TestCase):
    def test_pop_subcmd_with_arg(self):
        from ww.main import _pop_subcmd

        with patch.object(sys, "argv", ["ww", "mysub"]):
            result = _pop_subcmd()
            self.assertEqual(result, "mysub")

    def test_pop_subcmd_empty(self):
        from ww.main import _pop_subcmd

        with patch.object(sys, "argv", ["ww"]):
            result = _pop_subcmd()
            self.assertEqual(result, "")

    def test_pop_subcmd_removes_from_argv(self):
        from ww.main import _pop_subcmd

        with patch.object(sys, "argv", ["ww", "first", "second"]):
            result = _pop_subcmd()
            self.assertEqual(result, "first")
            self.assertEqual(sys.argv, ["ww", "second"])


# ---------------------------------------------------------------------------
# main() no args / help
# ---------------------------------------------------------------------------
class TestMainBasics(unittest.TestCase):
    def test_no_args_prints_hello_and_help(self):
        mock_print = _dispatch_print(["ww"])
        mock_print.assert_any_call("hello world")

    def test_help_long_flag(self):
        mock_print = _dispatch_print(["ww", "--help"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("Usage", all_text)

    def test_help_short_flag(self):
        mock_print = _dispatch_print(["ww", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("Usage", all_text)

    def test_help_word(self):
        mock_print = _dispatch_print(["ww", "help"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("Usage", all_text)

    def test_unknown_group_exits(self):
        with patch.object(sys, "argv", ["ww", "nonexistent-group-xyz"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# note group
# ---------------------------------------------------------------------------
class TestNoteDispatch(unittest.TestCase):
    def test_note_log(self):
        _dispatch(["ww", "note", "log"], "ww.note.create_log.create_log")

    def test_note_log_file(self):
        _dispatch(["ww", "note", "log-file"], "ww.note.create_log.create_log_from_file")

    def test_note_obfuscate(self):
        _dispatch(["ww", "note", "obfuscate"], "ww.note.obfuscate_log.obfuscate_log")

    def test_note_empty_prints_tip(self):
        def test_note_empty_prints_tip(self):
            with patch.dict(os.environ, {"NOTE_ENTER_CONFIRM": "1"}):
                with patch.object(sys, "argv", ["ww", "note"]):
                    with patch("builtins.input", side_effect=KeyboardInterrupt):
                        with patch("builtins.print") as mock_print:
                            from ww.main import main

                            main()
                            mock_print.assert_any_call(
                                "Tip: Use '/note' in hermes-agent to save assistant responses."
                            )

        def test_note_empty_keyboard_interrupt_returns(self):
            with patch.dict(os.environ, {"NOTE_ENTER_CONFIRM": "1"}):
                with patch.object(sys, "argv", ["ww", "note"]):
                    with patch("builtins.input", side_effect=KeyboardInterrupt):
                        with patch("builtins.print"):
                            from ww.main import main

                            # Should return without error
                            main()
                        main()

    def test_note_empty_enter_proceeds(self):
        with patch.object(sys, "argv", ["ww", "note"]):
            with patch("builtins.input", return_value=""):
                with patch("builtins.print"):
                    with patch("ww.note.note_workflow.main") as mock_m:
                        from ww.main import main

                        main()
                        mock_m.assert_called_once()

    def test_note_unknown_subcmd_exits(self):
        with patch.object(sys, "argv", ["ww", "note", "bogus"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# screenshot group
# ---------------------------------------------------------------------------
class TestScreenshotDispatch(unittest.TestCase):
    def test_screenshot_plain(self):
        _dispatch(["ww", "screenshot"], "ww.image.screenshot.main")

    def test_screenshot_note(self):
        _dispatch(["ww", "screenshot", "note"], "ww.note.screenshot_log.main")

    def test_screenshot_interact_note(self):
        _dispatch(["ww", "screenshot", "interact-note"], "ww.image.interact_note.main")

    def test_screenshot_linux(self):
        _dispatch(["ww", "screenshot-linux"], "ww.image.screenshot_linux.main")


# ---------------------------------------------------------------------------
# gif group
# ---------------------------------------------------------------------------
class TestGifDispatch(unittest.TestCase):
    def test_gif(self):
        _dispatch(["ww", "gif"], "ww.gif.gif.main")


# ---------------------------------------------------------------------------
# github group
# ---------------------------------------------------------------------------
class TestGithubDispatch(unittest.TestCase):
    def test_github_empty(self):
        mock_print = _dispatch_print(["ww", "github"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("gitmessageai", all_text)

    def test_github_help(self):
        mock_print = _dispatch_print(["ww", "github", "--help"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("gitmessageai", all_text)

    def test_github_gitmessageai(self):
        with patch.object(sys, "argv", ["ww", "github", "gitmessageai"]):
            with patch("ww.github.gitmessageai.gitmessageai") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()
                kwargs = mock_fn.call_args
                self.assertTrue(kwargs.kwargs.get("push", True))
                self.assertFalse(kwargs.kwargs.get("only_message", False))
                self.assertFalse(kwargs.kwargs.get("allow_pull_push", False))
                self.assertEqual(kwargs.kwargs.get("type", "content"), "content")

    def test_github_gitmessageai_no_push(self):
        with patch.object(sys, "argv", ["ww", "github", "gitmessageai", "--no-push"]):
            with patch("ww.github.gitmessageai.gitmessageai") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()
                self.assertFalse(mock_fn.call_args.kwargs["push"])

    def test_github_gitmessageai_only_message(self):
        with patch.object(
            sys, "argv", ["ww", "github", "gitmessageai", "--only-message"]
        ):
            with patch("ww.github.gitmessageai.gitmessageai") as mock_fn:
                from ww.main import main

                main()
                self.assertTrue(mock_fn.call_args.kwargs["only_message"])

    def test_github_gitmessageai_allow_pull_push(self):
        with patch.object(
            sys, "argv", ["ww", "github", "gitmessageai", "--allow-pull-push"]
        ):
            with patch("ww.github.gitmessageai.gitmessageai") as mock_fn:
                from ww.main import main

                main()
                self.assertTrue(mock_fn.call_args.kwargs["allow_pull_push"])

    def test_github_gitmessageai_type_file(self):
        with patch.object(
            sys, "argv", ["ww", "github", "gitmessageai", "--type", "file"]
        ):
            with patch("ww.github.gitmessageai.gitmessageai") as mock_fn:
                from ww.main import main

                main()
                self.assertEqual(mock_fn.call_args.kwargs["type"], "file")

    def test_github_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "github", "badcmd"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# macos group
# ---------------------------------------------------------------------------
class TestMacosDispatch(unittest.TestCase):
    def test_macos_empty(self):
        mock_print = _dispatch_print(["ww", "macos"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("find-large-dirs", all_text)

    def test_macos_help(self):
        mock_print = _dispatch_print(["ww", "macos", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("find-large-dirs", all_text)

    def test_macos_find_large_dirs(self):
        _dispatch(
            ["ww", "macos", "find-large-dirs"], "ww.macos.find_largest_directories.main"
        )

    def test_macos_system_info(self):
        _dispatch(["ww", "macos", "system-info"], "ww.macos.get_system_info.main")

    def test_macos_install(self):
        _dispatch(["ww", "macos", "install"], "ww.macos.install.main")

    def test_macos_list_fonts(self):
        mock_module = MagicMock()
        with patch.dict("sys.modules", {"ww.macos.list_fonts": mock_module}):
            with patch.object(sys, "argv", ["ww", "macos", "list-fonts"]):
                from ww.main import main

                main()
                mock_module.main.assert_called_once()

    def test_macos_list_disks(self):
        _dispatch(["ww", "macos", "list-disks"], "ww.macos.list_portable_disks.main")

    def test_macos_open_terminal(self):
        _dispatch(["ww", "macos", "open-terminal"], "ww.macos.open_terminal.main")

    def test_macos_toast(self):
        _dispatch(["ww", "macos", "toast"], "ww.macos.toast.main")

    def test_macos_charge_watch(self):
        _dispatch(["ww", "macos", "charge-watch"], "ww.macos.charge_watcher.main")

    def test_macos_process(self):
        _dispatch(["ww", "macos", "process"], "ww.macos.process_analyze.main")

    def test_macos_settings_proxy(self):
        _dispatch(["ww", "macos", "settings-proxy"], "ww.macos.settings_proxy.main")

    def test_macos_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "macos", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# image group
# ---------------------------------------------------------------------------
class TestImageDispatch(unittest.TestCase):
    def test_image_empty(self):
        mock_print = _dispatch_print(["ww", "image"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("avatar", all_text)

    def test_image_help(self):
        mock_print = _dispatch_print(["ww", "image", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("remove-bg", all_text)

    def test_image_avatar(self):
        _dispatch(["ww", "image", "avatar"], "ww.image.avatar.main")

    def test_image_crop(self):
        _dispatch(["ww", "image", "crop"], "ww.image.crop.main")

    def test_image_remove_bg(self):
        _dispatch(["ww", "image", "remove-bg"], "ww.image.remove_bg.main")

    def test_image_compress(self):
        _dispatch(["ww", "image", "compress"], "ww.image.image_compress.main")

    def test_image_photo_compress(self):
        _dispatch(["ww", "image", "photo-compress"], "ww.image.photo_compress.main")

    def test_image_exif(self):
        _dispatch(["ww", "image", "exif"], "ww.image.exif.main")

    def test_image_whatsapp(self):
        _dispatch(["ww", "image", "whatsapp"], "ww.image.whatsapp.main")

    def test_image_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "image", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# proc group
# ---------------------------------------------------------------------------
class TestProcDispatch(unittest.TestCase):
    def test_proc_empty(self):
        mock_print = _dispatch_print(["ww", "proc"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("kill-pattern", all_text)

    def test_proc_help(self):
        mock_print = _dispatch_print(["ww", "proc", "--help"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("kill-port", all_text)

    def test_proc_kill_pattern(self):
        _dispatch(["ww", "proc", "kill-pattern"], "ww.proc.kill_by_pattern.main")

    def test_proc_kill_port(self):
        _dispatch(["ww", "proc", "kill-port"], "ww.proc.kill_by_port.main")

    def test_proc_kill_jekyll(self):
        _dispatch(["ww", "proc", "kill-jekyll"], "ww.proc.kill_jekyll.main")

    def test_proc_kill_proxy(self):
        _dispatch(["ww", "proc", "kill-proxy"], "ww.proc.kill_macos_proxy.main")

    def test_proc_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "proc", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# utils group
# ---------------------------------------------------------------------------
class TestUtilsDispatch(unittest.TestCase):
    def test_utils_empty(self):
        mock_print = _dispatch_print(["ww", "utils"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("base64", all_text)

    def test_utils_help(self):
        mock_print = _dispatch_print(["ww", "utils", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("decode-jwt", all_text)

    def test_utils_base64(self):
        _dispatch(["ww", "utils", "base64"], "ww.utils.base64utils.main")

    def test_utils_ccr(self):
        _dispatch(["ww", "utils", "ccr"], "ww.utils.ccr.main")

    def test_utils_clean_zip(self):
        _dispatch(["ww", "utils", "clean-zip"], "ww.utils.clean_zip.main")

    def test_utils_decode_jwt(self):
        _dispatch(["ww", "utils", "decode-jwt"], "ww.utils.decode_jwt.main")

    def test_utils_py2txt(self):
        _dispatch(["ww", "utils", "py2txt"], "ww.utils.py2txt.main")

    def test_utils_request_proxy(self):
        _dispatch(["ww", "utils", "request-proxy"], "ww.utils.request_with_proxy.main")

    def test_utils_smart_unzip(self):
        _dispatch(["ww", "utils", "smart-unzip"], "ww.utils.smart_unzip.main")

    def test_utils_unzip(self):
        _dispatch(["ww", "utils", "unzip"], "ww.utils.unzip.main")

    def test_utils_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "utils", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# java group
# ---------------------------------------------------------------------------
class TestJavaDispatch(unittest.TestCase):
    def test_java_empty(self):
        mock_print = _dispatch_print(["ww", "java"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("mvn", all_text)

    def test_java_help(self):
        mock_print = _dispatch_print(["ww", "java", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("analyze-deps", all_text)

    def test_java_mvn(self):
        _dispatch(["ww", "java", "mvn"], "ww.java.mvn.main")

    def test_java_analyze_deps(self):
        _dispatch(["ww", "java", "analyze-deps"], "ww.java.analyze_deps.main")

    def test_java_analyze_packages(self):
        _dispatch(["ww", "java", "analyze-packages"], "ww.java.analyze_packages.main")

    def test_java_analyze_poms(self):
        _dispatch(["ww", "java", "analyze-poms"], "ww.java.analyze_poms.main")

    def test_java_analyze_spring(self):
        _dispatch(["ww", "java", "analyze-spring"], "ww.java.analyze_spring_boot.main")

    def test_java_clean_log(self):
        _dispatch(["ww", "java", "clean-log"], "ww.java.clean_log.main")

    def test_java_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "java", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# network group
# ---------------------------------------------------------------------------
class TestNetworkDispatch(unittest.TestCase):
    def test_network_empty(self):
        mock_print = _dispatch_print(["ww", "network"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("get-wifi-list", all_text)

    def test_network_help(self):
        mock_print = _dispatch_print(["ww", "network", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("port-scan", all_text)

    def test_network_get_wifi_list(self):
        _dispatch(["ww", "network", "get-wifi-list"], "ww.network.get_wifi_list.main")

    def test_network_save_wifi_list(self):
        _dispatch(["ww", "network", "save-wifi-list"], "ww.network.save_wifi_list.main")

    def test_network_hack_wifi(self):
        _dispatch(["ww", "network", "hack-wifi"], "ww.network.hack_wifi.main")

    def test_network_wifi_gen_password(self):
        _dispatch(
            ["ww", "network", "wifi-gen-password"], "ww.network.generate_password.main"
        )

    def test_network_ip_scan(self):
        _dispatch(["ww", "network", "ip-scan"], "ww.network.ip_scan.main")

    def test_network_port_scan(self):
        _dispatch(["ww", "network", "port-scan"], "ww.network.port_scan.main")

    def test_network_wifi_scan(self):
        _dispatch(["ww", "network", "wifi-scan"], "ww.network.wifi_scan.main")

    def test_network_wifi_util(self):
        _dispatch(["ww", "network", "wifi-util"], "ww.network.wifi_util.main")

    def test_network_network_plot(self):
        _dispatch(["ww", "network", "network-plot"], "ww.network.network_plot.main")

    def test_network_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "network", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# git group
# ---------------------------------------------------------------------------
class TestGitDispatch(unittest.TestCase):
    def test_git_empty(self):
        mock_print = _dispatch_print(["ww", "git"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("amend-push", all_text)

    def test_git_help(self):
        mock_print = _dispatch_print(["ww", "git", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("squash", all_text)

    def test_git_amend_push(self):
        _dispatch(["ww", "git", "amend-push"], "ww.git.git_amend_push.main")

    def test_git_classify(self):
        _dispatch(["ww", "git", "classify"], "ww.git.git_classify_commit.main")

    def test_git_find_commit(self):
        _dispatch(["ww", "git", "find-commit"], "ww.git.git_commit.main")

    def test_git_delete_commit(self):
        _dispatch(["ww", "git", "delete-commit"], "ww.git.git_delete_commit.main")

    def test_git_diff_tree(self):
        _dispatch(["ww", "git", "diff-tree"], "ww.git.git_diff_tree.main")

    def test_git_check_filenames(self):
        _dispatch(["ww", "git", "check-filenames"], "ww.git.git_filename.main")

    def test_git_force_push(self):
        _dispatch(["ww", "git", "force-push"], "ww.git.git_force_push.main")

    def test_git_show(self):
        _dispatch(["ww", "git", "show"], "ww.git.git_show_command.main")

    def test_git_squash(self):
        _dispatch(["ww", "git", "squash"], "ww.git.git_squash.main")

    def test_git_gca(self):
        with patch.object(sys, "argv", ["ww", "git", "gca"]):
            with patch("ww.github.gitmessageai.gitmessageai") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with(push=False)

    def test_git_gpa(self):
        with patch.object(sys, "argv", ["ww", "git", "gpa"]):
            with patch("ww.github.gitmessageai.gitmessageai") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with(allow_pull_push=True)

    def test_git_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "git", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# search group
# ---------------------------------------------------------------------------
class TestSearchDispatch(unittest.TestCase):
    def test_search_default(self):
        _dispatch(["ww", "search"], "ww.search.search.main")

    def test_search_bing(self):
        with patch.object(sys, "argv", ["ww", "search", "bing"]):
            with patch("ww.search.search_web.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_search_ddg(self):
        with patch.object(sys, "argv", ["ww", "search", "ddg"]):
            with patch("ww.search.search_web.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_search_startpage(self):
        with patch.object(sys, "argv", ["ww", "search", "startpage"]):
            with patch("ww.search.search_web.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_search_tavily(self):
        with patch.object(sys, "argv", ["ww", "search", "tavily"]):
            with patch("ww.search.search_web.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_search_web(self):
        with patch.object(sys, "argv", ["ww", "search", "web"]):
            with patch("ww.search.search_web.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()

    def test_search_code(self):
        _dispatch(["ww", "search", "code"], "ww.search.search_code.main")

    def test_search_filename(self):
        _dispatch(["ww", "search", "filename"], "ww.search.search_filename.main")

    def test_search_no_subcmd(self):
        # When search has no recognized subcmd, it falls through to search.main
        _dispatch(["ww", "search"], "ww.search.search.main")


# ---------------------------------------------------------------------------
# pdf group
# ---------------------------------------------------------------------------
class TestPdfDispatch(unittest.TestCase):
    def test_pdf_empty(self):
        mock_print = _dispatch_print(["ww", "pdf"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("markdown-pdf", all_text)

    def test_pdf_help(self):
        mock_print = _dispatch_print(["ww", "pdf", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("md2png", all_text)

    def test_pdf_markdown_pdf(self):
        _dispatch(["ww", "pdf", "markdown-pdf"], "ww.pdf.markdown_pdf.main")

    def test_pdf_pdf_pipeline(self):
        _dispatch(["ww", "pdf", "pdf-pipeline"], "ww.pdf.pdf_pipeline.main")

    def test_pdf_update_pdf(self):
        _dispatch(["ww", "pdf", "update-pdf"], "ww.pdf.update_pdf.main")

    def test_pdf_code2pdf(self):
        _dispatch(["ww", "pdf", "code2pdf"], "ww.pdf.code2pdf.main")

    def test_pdf_scale_pdf(self):
        _dispatch(["ww", "pdf", "scale-pdf"], "ww.pdf.scale_pdf.main")

    def test_pdf_test_latex(self):
        _dispatch(["ww", "pdf", "test-latex"], "ww.pdf.test_latex.main")

    def test_pdf_md2png(self):
        _dispatch(["ww", "pdf", "md2png"], "ww.pdf.md2png.main")

    def test_pdf_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "pdf", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# copilot group
# ---------------------------------------------------------------------------
class TestCopilotDispatch(unittest.TestCase):
    def test_copilot_empty(self):
        mock_print = _dispatch_print(["ww", "copilot"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("auth", all_text)

    def test_copilot_help(self):
        mock_print = _dispatch_print(["ww", "copilot", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("chat", all_text)

    def test_copilot_auth(self):
        _dispatch(["ww", "copilot", "auth"], "ww.llm.copilot_auth.main")

    def test_copilot_models_with_token(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}):
            with patch.object(sys, "argv", ["ww", "copilot", "models"]):
                with patch(
                    "ww.llm.copilot_client.get_models", return_value=[{"id": "gpt-4o"}]
                ) as mock_fn:
                    with patch("builtins.print") as mock_print:
                        from ww.main import main

                        main()
                        mock_fn.assert_called_once_with("fake-token")
                        mock_print.assert_any_call("gpt-4o")

    def test_copilot_models_no_token_exits(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}, clear=False):
            with patch.object(sys, "argv", ["ww", "copilot", "models"]):
                with patch.dict(os.environ, {"GITHUB_TOKEN": ""}):
                    with patch("builtins.print"):
                        from ww.main import main

                        with self.assertRaises(SystemExit):
                            main()

    def test_copilot_chat_with_prompt(self):
        with patch.object(sys, "argv", ["ww", "copilot", "chat", "hello"]):
            with patch(
                "ww.llm.copilot_client.call_copilot_api", return_value="hi"
            ) as mock_fn:
                with patch("builtins.print") as mock_print:
                    from ww.main import main

                    main()
                    mock_fn.assert_called_once()
                    self.assertEqual(mock_fn.call_args.args[0], "hello")
                    mock_print.assert_any_call("hi")

    def test_copilot_chat_default_model(self):
        with patch.object(sys, "argv", ["ww", "copilot", "chat", "test"]):
            with patch(
                "ww.llm.copilot_client.call_copilot_api", return_value="ok"
            ) as mock_fn:
                with patch("builtins.print"):
                    from ww.main import main

                    main()
                    self.assertIsNone(mock_fn.call_args.kwargs.get("model"))
                    self.assertFalse(mock_fn.call_args.kwargs.get("debug", False))

    def test_copilot_chat_with_model_flag(self):
        with patch.object(
            sys, "argv", ["ww", "copilot", "chat", "test", "--model", "gpt-4o"]
        ):
            with patch(
                "ww.llm.copilot_client.call_copilot_api", return_value="ok"
            ) as mock_fn:
                with patch("builtins.print"):
                    from ww.main import main

                    main()
                    self.assertEqual(mock_fn.call_args.kwargs.get("model"), "gpt-4o")

    def test_copilot_chat_with_debug_flag(self):
        with patch.object(sys, "argv", ["ww", "copilot", "chat", "test", "--debug"]):
            with patch(
                "ww.llm.copilot_client.call_copilot_api", return_value="ok"
            ) as mock_fn:
                with patch("builtins.print"):
                    from ww.main import main

                    main()
                    self.assertTrue(mock_fn.call_args.kwargs.get("debug"))

    def test_copilot_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "copilot", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# sync group
# ---------------------------------------------------------------------------
class TestSyncDispatch(unittest.TestCase):
    def test_sync_empty(self):
        mock_print = _dispatch_print(["ww", "sync"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("claude", all_text)

    def test_sync_help(self):
        mock_print = _dispatch_print(["ww", "sync", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("ssh", all_text)

    def test_sync_claude(self):
        _dispatch(["ww", "sync", "claude"], "ww.sync.claude.main")

    def test_sync_bashrc_default(self):
        with patch.object(sys, "argv", ["ww", "sync", "bashrc"]):
            with patch("ww.sync.remote.sync_bashrc") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("forth")

    def test_sync_bashrc_back(self):
        with patch.object(sys, "argv", ["ww", "sync", "bashrc", "back"]):
            with patch("ww.sync.remote.sync_bashrc") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("back")

    def test_sync_bashrc_help(self):
        with patch.object(sys, "argv", ["ww", "sync", "bashrc", "--help"]):
            with patch("builtins.print") as mock_print:
                from ww.main import main

                main()
                all_text = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("back", all_text)

    def test_sync_zprofile_default(self):
        with patch.object(sys, "argv", ["ww", "sync", "zprofile"]):
            with patch("ww.sync.remote.sync_zprofile") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("forth")

    def test_sync_zprofile_back(self):
        with patch.object(sys, "argv", ["ww", "sync", "zprofile", "back"]):
            with patch("ww.sync.remote.sync_zprofile") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("back")

    def test_sync_zprofile_help(self):
        with patch.object(sys, "argv", ["ww", "sync", "zprofile", "-h"]):
            with patch("builtins.print") as mock_print:
                from ww.main import main

                main()
                all_text = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("zprofile", all_text)

    def test_sync_zed_default(self):
        with patch.object(sys, "argv", ["ww", "sync", "zed"]):
            with patch("ww.sync.remote.sync_zed") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("forth")

    def test_sync_zed_back(self):
        with patch.object(sys, "argv", ["ww", "sync", "zed", "back"]):
            with patch("ww.sync.remote.sync_zed") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("back")

    def test_sync_zed_help(self):
        with patch.object(sys, "argv", ["ww", "sync", "zed", "-h"]):
            with patch("builtins.print") as mock_print:
                from ww.main import main

                main()
                all_text = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("zed", all_text)

    def test_sync_ssh_default(self):
        with patch.object(sys, "argv", ["ww", "sync", "ssh"]):
            with patch("ww.sync.remote.sync_ssh") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("forth")

    def test_sync_ssh_back(self):
        with patch.object(sys, "argv", ["ww", "sync", "ssh", "back"]):
            with patch("ww.sync.remote.sync_ssh") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("back")

    def test_sync_ssh_help(self):
        with patch.object(sys, "argv", ["ww", "sync", "ssh", "-h"]):
            with patch("builtins.print") as mock_print:
                from ww.main import main

                main()
                all_text = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("ssh", all_text)

    def test_sync_hermes_default(self):
        with patch.object(sys, "argv", ["ww", "sync", "hermes"]):
            with patch("ww.sync.remote.sync_hermes") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("forth")

    def test_sync_hermes_back(self):
        with patch.object(sys, "argv", ["ww", "sync", "hermes", "back"]):
            with patch("ww.sync.remote.sync_hermes") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once_with("back")

    def test_sync_hermes_help(self):
        with patch.object(sys, "argv", ["ww", "sync", "hermes", "-h"]):
            with patch("builtins.print") as mock_print:
                from ww.main import main

                main()
                all_text = " ".join(str(c) for c in mock_print.call_args_list)
                self.assertIn("hermes", all_text)

    def test_sync_openclaw(self):
        _dispatch(["ww", "sync", "openclaw"], "ww.sync.openclaw.main")

    def test_sync_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "sync", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# linux group
# ---------------------------------------------------------------------------
class TestLinuxDispatch(unittest.TestCase):
    def test_linux(self):
        _dispatch(["ww", "linux"], "ww.linux.main.main")


# ---------------------------------------------------------------------------
# cloudflare group
# ---------------------------------------------------------------------------
class TestCloudflareDispatch(unittest.TestCase):
    def test_cloudflare_empty(self):
        mock_print = _dispatch_print(["ww", "cloudflare"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("monthly-visit", all_text)

    def test_cloudflare_help(self):
        mock_print = _dispatch_print(["ww", "cloudflare", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("zones", all_text)

    def test_cloudflare_monthly_visit(self):
        _dispatch(
            ["ww", "cloudflare", "monthly-visit"],
            "ww.cloudflare.get_monthly_visit.main",
        )

    def test_cloudflare_zones(self):
        _dispatch(["ww", "cloudflare", "zones"], "ww.cloudflare.get_zone_id.main")

    def test_cloudflare_datasets(self):
        _dispatch(
            ["ww", "cloudflare", "datasets"],
            "ww.cloudflare.get_web_analytics_datasets.main",
        )

    def test_cloudflare_schema(self):
        _dispatch(["ww", "cloudflare", "schema"], "ww.cloudflare.get_schema.main")

    def test_cloudflare_pdf(self):
        _dispatch(
            ["ww", "cloudflare", "pdf"],
            "ww.cloudflare.read_analytics_data_from_pdf.main",
        )

    def test_cloudflare_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "cloudflare", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# clash group
# ---------------------------------------------------------------------------
class TestClashDispatch(unittest.TestCase):
    def test_clash_empty(self):
        mock_print = _dispatch_print(["ww", "clash"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("select-provider", all_text)

    def test_clash_help(self):
        mock_print = _dispatch_print(["ww", "clash", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("speed", all_text)

    def test_clash_select_provider(self):
        mock_module = MagicMock()
        with patch.dict("sys.modules", {"ww.clash.clash_select_provider": mock_module}):
            with patch.object(sys, "argv", ["ww", "clash", "select-provider"]):
                from ww.main import main

                main()
                mock_module.main.assert_called_once()

    def test_clash_speed(self):
        mock_module = MagicMock()
        with patch.dict("sys.modules", {"ww.clash.clash_speed": mock_module}):
            with patch.object(sys, "argv", ["ww", "clash", "speed"]):
                from ww.main import main

                main()
                mock_module.main.assert_called_once()

    def test_clash_run(self):
        mock_module = MagicMock()
        with patch.dict("sys.modules", {"ww.clash.clash": mock_module}):
            with patch.object(sys, "argv", ["ww", "clash", "run"]):
                from ww.main import main

                main()
                mock_module.main.assert_called_once()

    def test_clash_top_proxies(self):
        _dispatch(["ww", "clash", "top-proxies"], "ww.clash.speed.main")

    def test_clash_top_proxies_multi(self):
        _dispatch(["ww", "clash", "top-proxies-multi"], "ww.clash.speed_plus.main")

    def test_clash_speed_tiktok(self):
        _dispatch(["ww", "clash", "speed-tiktok"], "ww.clash.speed_tiktok.main")

    def test_clash_query_dns(self):
        _dispatch(["ww", "clash", "query-dns"], "ww.clash.query_dns.main")

    def test_clash_gnome_proxy(self):
        _dispatch(["ww", "clash", "gnome-proxy"], "ww.clash.gnome_proxy.main")

    def test_clash_macos_proxy(self):
        _dispatch(["ww", "clash", "macos-proxy"], "ww.clash.networksetup.main")

    def test_clash_wifi(self):
        _dispatch(["ww", "clash", "wifi"], "ww.clash.wifi_toggle.main")

    def test_clash_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "clash", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# display group
# ---------------------------------------------------------------------------
class TestDisplayDispatch(unittest.TestCase):
    def test_display(self):
        _dispatch(["ww", "display"], "ww.display.appearance.main")


# ---------------------------------------------------------------------------
# gen-image group
# ---------------------------------------------------------------------------
class TestGenImageDispatch(unittest.TestCase):
    def test_gen_image(self):
        _dispatch(["ww", "gen-image"], "ww.image.gen_image.main")


# ---------------------------------------------------------------------------
# action group
# ---------------------------------------------------------------------------
class TestActionDispatch(unittest.TestCase):
    def test_action(self):
        _dispatch(["ww", "action"], "ww.action.action.main")


# ---------------------------------------------------------------------------
# llm group
# ---------------------------------------------------------------------------
class TestLlmDispatch(unittest.TestCase):
    def test_llm_empty(self):
        mock_print = _dispatch_print(["ww", "llm"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("compare", all_text)

    def test_llm_help(self):
        mock_print = _dispatch_print(["ww", "llm", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("compare", all_text)

    def test_llm_compare(self):
        _dispatch(["ww", "llm", "compare"], "ww.llm.compare.main")

    def test_llm_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "llm", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# env group
# ---------------------------------------------------------------------------
class TestEnvDispatch(unittest.TestCase):
    def test_env_empty(self):
        mock_print = _dispatch_print(["ww", "env"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("update", all_text)

    def test_env_help(self):
        mock_print = _dispatch_print(["ww", "env", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("update", all_text)

    def test_env_update(self):
        _dispatch(["ww", "env", "update"], "ww.llm.update_env.main")

    def test_env_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "env", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# read group
# ---------------------------------------------------------------------------
class TestReadDispatch(unittest.TestCase):
    def test_read(self):
        _dispatch(["ww", "read"], "ww.read.read_assistant.main")


# ---------------------------------------------------------------------------
# marp group
# ---------------------------------------------------------------------------
class TestMarpDispatch(unittest.TestCase):
    def test_marp(self):
        _dispatch(["ww", "marp"], "ww.marp.marp_watch.main")


# ---------------------------------------------------------------------------
# whisper group
# ---------------------------------------------------------------------------
class TestWhisperDispatch(unittest.TestCase):
    def test_whisper_default(self):
        _dispatch(["ww", "whisper"], "ww.audio.whisper_translate.main")

    def test_whisper_refine(self):
        _dispatch(["ww", "whisper", "refine"], "ww.audio.whisper_refine.main")


# ---------------------------------------------------------------------------
# update group
# ---------------------------------------------------------------------------
class TestUpdateDispatch(unittest.TestCase):
    def test_update(self):
        _dispatch(["ww", "projects", "update"], "ww.git.git_update.main")


# ---------------------------------------------------------------------------
# degree group
# ---------------------------------------------------------------------------
class TestDegreeDispatch(unittest.TestCase):
    def test_degree(self):
        _dispatch(["ww", "degree"], "ww.degree.degree.main")


# ---------------------------------------------------------------------------
# latest group
# ---------------------------------------------------------------------------
class TestLatestDispatch(unittest.TestCase):
    def test_latest_empty(self):
        mock_print = _dispatch_print(["ww", "latest"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("notes", all_text)

    def test_latest_help(self):
        mock_print = _dispatch_print(["ww", "latest", "-h"])
        all_text = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("notes", all_text)

    def test_latest_notes(self):
        _dispatch(["ww", "latest", "notes"], "ww.note.latest_notes.main")

    def test_latest_unknown_exits(self):
        with patch.object(sys, "argv", ["ww", "latest", "nope"]):
            with patch("builtins.print"):
                from ww.main import main

                with self.assertRaises(SystemExit):
                    main()


# ---------------------------------------------------------------------------
# search with --json flag (web --json)
# ---------------------------------------------------------------------------
class TestSearchWebJson(unittest.TestCase):
    def test_search_web_json(self):
        with patch.object(sys, "argv", ["ww", "search", "web", "--json"]):
            with patch("ww.search.search_web.main") as mock_fn:
                from ww.main import main

                main()
                mock_fn.assert_called_once()
                # --json remains in argv for search_web to handle
                self.assertIn("--json", sys.argv)


if __name__ == "__main__":
    unittest.main()
