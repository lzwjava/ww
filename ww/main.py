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
            parser = argparse.ArgumentParser(description="Generate commit message with AI and commit changes.")
            parser.add_argument("--no-push", dest="push", action="store_false")
            parser.add_argument("--only-message", dest="only_message", action="store_true")
            parser.add_argument("--model", type=str, default="grok-fast", choices=list(MODEL_MAPPING.keys()))
            parser.add_argument("--allow-pull-push", dest="allow_pull_push", action="store_true")
            parser.add_argument("--type", type=str, default="content", choices=["file", "content"])
            args = parser.parse_args()
            gitmessageai(push=args.push, only_message=args.only_message, model=args.model, allow_pull_push=args.allow_pull_push, type=args.type)
        elif cmd == "github-readme":
            from ww.github.readme import format_projects_to_markdown, all_projects
            import os
            github_username = "lzwjava"
            github_token = os.getenv("GITHUB_TOKEN")
            markdown_output = format_projects_to_markdown(all_projects, github_username, github_token)
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
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        print("hello world")
