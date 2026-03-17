import sys


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv.pop(1)
        if cmd == "create-note":
            from ww.create.create_note import main as create_note_main

            create_note_main()
        elif cmd == "create-log":
            from ww.create.create_log import create_log

            create_log()
        elif cmd == "gif":
            from ww.gif.gif import main as gif_main

            gif_main()
        elif cmd == "gitmessageai":
            from ww.github.gitmessageai import gitmessageai
            import argparse
            from ww.github.gitmessageai import MODEL_MAPPING

            parser = argparse.ArgumentParser(
                description="Generate commit message with AI and commit changes."
            )
            parser.add_argument("--no-push", dest="push", action="store_false")
            parser.add_argument(
                "--only-message", dest="only_message", action="store_true"
            )
            parser.add_argument(
                "--model",
                type=str,
                default="grok-fast",
                choices=list(MODEL_MAPPING.keys()),
            )
            parser.add_argument(
                "--allow-pull-push", dest="allow_pull_push", action="store_true"
            )
            parser.add_argument(
                "--type", type=str, default="content", choices=["file", "content"]
            )
            args = parser.parse_args()
            gitmessageai(
                push=args.push,
                only_message=args.only_message,
                model=args.model,
                allow_pull_push=args.allow_pull_push,
                type=args.type,
            )
        elif cmd == "github-readme":
            from ww.github.readme import format_projects_to_markdown, all_projects
            import os

            github_username = "lzwjava"
            github_token = os.getenv("GITHUB_TOKEN")
            markdown_output = format_projects_to_markdown(
                all_projects, github_username, github_token
            )
            print(markdown_output)
        elif cmd == "find-large-dirs":
            from ww.macos.find_largest_directories import main as find_large_dirs_main

            find_large_dirs_main()
        elif cmd == "system-info":
            from ww.macos.get_system_info import main as system_info_main

            system_info_main()
        elif cmd == "mac-install":
            from ww.macos.install import main as mac_install_main

            mac_install_main()
        elif cmd == "list-fonts":
            from ww.macos.list_fonts import main as list_fonts_main

            list_fonts_main()
        elif cmd == "list-disks":
            from ww.macos.list_portable_disks import main as list_disks_main

            list_disks_main()
        elif cmd == "open-terminal":
            from ww.macos.open_terminal import main as open_terminal_main

            open_terminal_main()
        elif cmd == "toast":
            from ww.macos.toast import main as toast_main

            toast_main()
        elif cmd == "avatar":
            from ww.image.avatar import main as avatar_main

            avatar_main()
        elif cmd == "crop":
            from ww.image.crop import main as crop_main

            crop_main()
        elif cmd == "remove-bg":
            from ww.image.remove_bg import main as remove_bg_main

            remove_bg_main()
        elif cmd == "screenshot":
            from ww.image.screenshot import main as screenshot_main

            screenshot_main()
        elif cmd == "screenshot-linux":
            from ww.image.screenshot_linux import main as screenshot_linux_main

            screenshot_linux_main()
        elif cmd == "image-compress":
            from ww.image.image_compress import main as image_compress_main

            image_compress_main()
        elif cmd == "photo-compress":
            from ww.image.photo_compress import main as photo_compress_main

            photo_compress_main()
        elif cmd == "kill-by-pattern":
            from ww.proc.kill_by_pattern import main as kill_by_pattern_main

            kill_by_pattern_main()
        elif cmd == "kill-by-port":
            from ww.proc.kill_by_port import main as kill_by_port_main

            kill_by_port_main()
        elif cmd == "kill-jekyll":
            from ww.proc.kill_jekyll import main as kill_jekyll_main

            kill_jekyll_main()
        elif cmd == "kill-macos-proxy":
            from ww.proc.kill_macos_proxy import main as kill_macos_proxy_main

            kill_macos_proxy_main()
        elif cmd == "base64":
            from ww.utils.base64utils import main as base64_main

            base64_main()
        elif cmd == "ccr":
            from ww.utils.ccr import main as ccr_main

            ccr_main()
        elif cmd == "clean-zip":
            from ww.utils.clean_zip import main as clean_zip_main

            clean_zip_main()
        elif cmd == "decode-jwt":
            from ww.utils.decode_jwt import main as decode_jwt_main

            decode_jwt_main()
        elif cmd == "py2txt":
            from ww.utils.py2txt import main as py2txt_main

            py2txt_main()
        elif cmd == "request-proxy":
            from ww.utils.request_with_proxy import main as request_proxy_main

            request_proxy_main()
        elif cmd == "smart-unzip":
            from ww.utils.smart_unzip import main as smart_unzip_main

            smart_unzip_main()
        elif cmd == "unzip":
            from ww.utils.unzip import main as unzip_main

            unzip_main()
        elif cmd == "mvn":
            from ww.java.mvn import main as mvn_main

            mvn_main()
        elif cmd == "get-wifi-list":
            from ww.network.get_wifi_list import main as get_wifi_list_main

            get_wifi_list_main()
        elif cmd == "save-wifi-list":
            from ww.network.save_wifi_list import main as save_wifi_list_main

            save_wifi_list_main()
        elif cmd == "hack-wifi":
            from ww.network.hack_wifi import main as hack_wifi_main

            hack_wifi_main()
        elif cmd == "wifi-gen-password":
            from ww.network.generate_password import main as wifi_gen_password_main

            wifi_gen_password_main()
        elif cmd == "ip-scan":
            from ww.network.ip_scan import main as ip_scan_main

            ip_scan_main()
        elif cmd == "port-scan":
            from ww.network.port_scan import main as port_scan_main

            port_scan_main()
        elif cmd == "wifi-scan":
            from ww.network.wifi_scan import main as wifi_scan_main

            wifi_scan_main()
        elif cmd == "wifi-util":
            from ww.network.wifi_util import main as wifi_util_main

            wifi_util_main()
        elif cmd == "network-plot":
            from ww.network.network_plot import main as network_plot_main

            network_plot_main()
        elif cmd == "git-amend-push":
            from ww.git.git_amend_push import main as git_amend_push_main

            git_amend_push_main()
        elif cmd == "git-classify":
            from ww.git.git_classify_commit import main as git_classify_main

            git_classify_main()
        elif cmd == "find-commit":
            from ww.git.git_commit import main as find_commit_main

            find_commit_main()
        elif cmd == "git-delete-commit":
            from ww.git.git_delete_commit import main as git_delete_commit_main

            git_delete_commit_main()
        elif cmd == "git-diff-tree":
            from ww.git.git_diff_tree import main as git_diff_tree_main

            git_diff_tree_main()
        elif cmd == "git-check-filenames":
            from ww.git.git_filename import main as git_check_filenames_main

            git_check_filenames_main()
        elif cmd == "git-force-push":
            from ww.git.git_force_push import main as git_force_push_main

            git_force_push_main()
        elif cmd == "git-show":
            from ww.git.git_show_command import main as git_show_main

            git_show_main()
        elif cmd == "git-squash":
            from ww.git.git_squash import main as git_squash_main

            git_squash_main()
        elif cmd == "analyze-deps":
            from ww.java.analyze_deps import main as analyze_deps_main

            analyze_deps_main()
        elif cmd == "analyze-packages":
            from ww.java.analyze_packages import main as analyze_packages_main

            analyze_packages_main()
        elif cmd == "analyze-poms":
            from ww.java.analyze_poms import main as analyze_poms_main

            analyze_poms_main()
        elif cmd == "analyze-spring":
            from ww.java.analyze_spring_boot import main as analyze_spring_main

            analyze_spring_main()
        elif cmd == "clean-log":
            from ww.java.clean_log import main as clean_log_main

            clean_log_main()
        elif cmd == "search":
            from ww.search.search import main as search_main

            search_main()
        elif cmd == "search-bing":
            from ww.search.search_bing import main as search_bing_main

            search_bing_main()
        elif cmd == "search-code":
            from ww.search.search_code import main as search_code_main

            search_code_main()
        elif cmd == "search-ddg":
            from ww.search.search_duckduckgo import main as search_ddg_main

            search_ddg_main()
        elif cmd == "search-ecosia":
            from ww.search.search_ecosia import main as search_ecosia_main

            search_ecosia_main()
        elif cmd == "search-filename":
            from ww.search.search_filename import main as search_filename_main

            search_filename_main()
        elif cmd == "search-startpage":
            from ww.search.search_startpage import main as search_startpage_main

            search_startpage_main()
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        print("hello world")
