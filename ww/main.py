import sys

from dotenv import load_dotenv

load_dotenv()


def _print_help():
    print("Usage: ww <group> [command] [options]")
    print("")
    print("Note:")
    print("  ww note                   Create a new note with git integration")
    print("  ww note log               Create a new log entry")
    print("")
    print("GIF:")
    print("  ww gif                    Create GIF from images")
    print("")
    print("GitHub:")
    print("  ww github gitmessageai    Generate AI commit message and commit")
    print("")
    print("macOS:")
    print("  ww macos find-large-dirs  Find largest directories on disk")
    print("  ww macos system-info      Show system information")
    print("  ww macos install          Run macOS install tasks")
    print("  ww macos list-fonts       List installed fonts")
    print("  ww macos list-disks       List portable disks")
    print("  ww macos open-terminal    Open a new terminal window")
    print("  ww macos toast            Show macOS notification toast")
    print("")
    print("Image:")
    print("  ww image avatar           Process avatar image")
    print("  ww image crop             Crop an image")
    print("  ww image remove-bg        Remove image background")
    print("  ww image screenshot       Take a screenshot")
    print("  ww image screenshot-linux Take a screenshot (Linux)")
    print("  ww image compress         Compress images")
    print("  ww image photo-compress   Compress photos")
    print("")
    print("Process:")
    print("  ww proc kill-pattern      Kill processes matching a pattern")
    print("  ww proc kill-port         Kill process on a given port")
    print("  ww proc kill-jekyll       Kill Jekyll server")
    print("  ww proc kill-proxy        Kill macOS proxy")
    print("")
    print("Utils:")
    print("  ww utils base64           Encode/decode base64")
    print("  ww utils ccr              CCR utility")
    print("  ww utils clean-zip        Clean zip files")
    print("  ww utils decode-jwt       Decode a JWT token")
    print("  ww utils py2txt           Convert Python files to text")
    print("  ww utils request-proxy    Make HTTP request via proxy")
    print("  ww utils smart-unzip      Smart unzip archives")
    print("  ww utils unzip            Unzip an archive")
    print("")
    print("Java:")
    print("  ww java mvn               Maven project utilities")
    print("  ww java analyze-deps      Analyze Java dependencies")
    print("  ww java analyze-packages  Analyze Java packages")
    print("  ww java analyze-poms      Analyze Maven POM files")
    print("  ww java analyze-spring    Analyze Spring Boot project")
    print("  ww java clean-log         Clean Java log files")
    print("")
    print("Network:")
    print("  ww network get-wifi-list      Get list of WiFi networks")
    print("  ww network save-wifi-list     Save WiFi network list")
    print("  ww network hack-wifi          WiFi password utilities")
    print("  ww network wifi-gen-password  Generate WiFi password")
    print("  ww network ip-scan            Scan IP addresses on network")
    print("  ww network port-scan          Scan open ports")
    print("  ww network wifi-scan          Scan for WiFi networks")
    print("  ww network wifi-util          WiFi utility tools")
    print("  ww network network-plot       Plot network topology")
    print("")
    print("Git:")
    print("  ww git amend-push         Amend last commit and force push")
    print("  ww git classify           Classify git commits")
    print("  ww git find-commit        Find a git commit")
    print("  ww git delete-commit      Delete a git commit")
    print("  ww git diff-tree          Show git diff tree")
    print("  ww git check-filenames    Check git filenames")
    print("  ww git force-push         Force push to remote")
    print("  ww git show               Show git commit details")
    print("  ww git squash             Squash git commits")
    print("")
    print("Search:")
    print("  ww search                 Web search (multi-engine)")
    print("  ww search bing            Search with Bing")
    print("  ww search code            Search code")
    print("  ww search ddg             Search with DuckDuckGo")
    print("  ww search ecosia          Search with Ecosia")
    print("  ww search filename        Search by filename")
    print("  ww search startpage       Search with StartPage")
    print("")
    print("Copilot:")
    print("  ww copilot auth           Authenticate via GitHub OAuth device flow")
    print("  ww copilot models         List available Copilot models")
    print("  ww copilot chat           Chat with a Copilot model")


def _pop_subcmd():
    if len(sys.argv) > 1:
        return sys.argv.pop(1)
    return ""


def main():
    if len(sys.argv) < 2:
        print("hello world")
        print("")
        _print_help()
        return

    group = sys.argv.pop(1)

    if group in ("--help", "-h", "help"):
        _print_help()
        return

    if group == "note":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd == "note":
            from ww.note.create_note import main as m

            m()
        elif subcmd == "log":
            from ww.note.create_log import create_log

            create_log()
        else:
            print(f"Unknown note command: {subcmd}")
            sys.exit(1)

    elif group == "gif":
        from ww.gif.gif import main as m

        m()

    elif group == "github":
        subcmd = _pop_subcmd()
        if subcmd == "gitmessageai":
            import argparse
            from ww.github.gitmessageai import gitmessageai, MODEL_MAPPING

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
        else:
            print(f"Unknown github command: {subcmd}")
            sys.exit(1)

    elif group == "macos":
        subcmd = _pop_subcmd()
        if subcmd == "find-large-dirs":
            from ww.macos.find_largest_directories import main as m

            m()
        elif subcmd == "system-info":
            from ww.macos.get_system_info import main as m

            m()
        elif subcmd == "install":
            from ww.macos.install import main as m

            m()
        elif subcmd == "list-fonts":
            from ww.macos.list_fonts import main as m

            m()
        elif subcmd == "list-disks":
            from ww.macos.list_portable_disks import main as m

            m()
        elif subcmd == "open-terminal":
            from ww.macos.open_terminal import main as m

            m()
        elif subcmd == "toast":
            from ww.macos.toast import main as m

            m()
        else:
            print(f"Unknown macos command: {subcmd}")
            sys.exit(1)

    elif group == "image":
        subcmd = _pop_subcmd()
        if subcmd == "avatar":
            from ww.image.avatar import main as m

            m()
        elif subcmd == "crop":
            from ww.image.crop import main as m

            m()
        elif subcmd == "remove-bg":
            from ww.image.remove_bg import main as m

            m()
        elif subcmd == "screenshot":
            from ww.image.screenshot import main as m

            m()
        elif subcmd == "screenshot-linux":
            from ww.image.screenshot_linux import main as m

            m()
        elif subcmd == "compress":
            from ww.image.image_compress import main as m

            m()
        elif subcmd == "photo-compress":
            from ww.image.photo_compress import main as m

            m()
        else:
            print(f"Unknown image command: {subcmd}")
            sys.exit(1)

    elif group == "proc":
        subcmd = _pop_subcmd()
        if subcmd == "kill-pattern":
            from ww.proc.kill_by_pattern import main as m

            m()
        elif subcmd == "kill-port":
            from ww.proc.kill_by_port import main as m

            m()
        elif subcmd == "kill-jekyll":
            from ww.proc.kill_jekyll import main as m

            m()
        elif subcmd == "kill-proxy":
            from ww.proc.kill_macos_proxy import main as m

            m()
        else:
            print(f"Unknown proc command: {subcmd}")
            sys.exit(1)

    elif group == "utils":
        subcmd = _pop_subcmd()
        if subcmd == "base64":
            from ww.utils.base64utils import main as m

            m()
        elif subcmd == "ccr":
            from ww.utils.ccr import main as m

            m()
        elif subcmd == "clean-zip":
            from ww.utils.clean_zip import main as m

            m()
        elif subcmd == "decode-jwt":
            from ww.utils.decode_jwt import main as m

            m()
        elif subcmd == "py2txt":
            from ww.utils.py2txt import main as m

            m()
        elif subcmd == "request-proxy":
            from ww.utils.request_with_proxy import main as m

            m()
        elif subcmd == "smart-unzip":
            from ww.utils.smart_unzip import main as m

            m()
        elif subcmd == "unzip":
            from ww.utils.unzip import main as m

            m()
        else:
            print(f"Unknown utils command: {subcmd}")
            sys.exit(1)

    elif group == "java":
        subcmd = _pop_subcmd()
        if subcmd == "mvn":
            from ww.java.mvn import main as m

            m()
        elif subcmd == "analyze-deps":
            from ww.java.analyze_deps import main as m

            m()
        elif subcmd == "analyze-packages":
            from ww.java.analyze_packages import main as m

            m()
        elif subcmd == "analyze-poms":
            from ww.java.analyze_poms import main as m

            m()
        elif subcmd == "analyze-spring":
            from ww.java.analyze_spring_boot import main as m

            m()
        elif subcmd == "clean-log":
            from ww.java.clean_log import main as m

            m()
        else:
            print(f"Unknown java command: {subcmd}")
            sys.exit(1)

    elif group == "network":
        subcmd = _pop_subcmd()
        if subcmd == "get-wifi-list":
            from ww.network.get_wifi_list import main as m

            m()
        elif subcmd == "save-wifi-list":
            from ww.network.save_wifi_list import main as m

            m()
        elif subcmd == "hack-wifi":
            from ww.network.hack_wifi import main as m

            m()
        elif subcmd == "wifi-gen-password":
            from ww.network.generate_password import main as m

            m()
        elif subcmd == "ip-scan":
            from ww.network.ip_scan import main as m

            m()
        elif subcmd == "port-scan":
            from ww.network.port_scan import main as m

            m()
        elif subcmd == "wifi-scan":
            from ww.network.wifi_scan import main as m

            m()
        elif subcmd == "wifi-util":
            from ww.network.wifi_util import main as m

            m()
        elif subcmd == "network-plot":
            from ww.network.network_plot import main as m

            m()
        else:
            print(f"Unknown network command: {subcmd}")
            sys.exit(1)

    elif group == "git":
        subcmd = _pop_subcmd()
        if subcmd == "amend-push":
            from ww.git.git_amend_push import main as m

            m()
        elif subcmd == "classify":
            from ww.git.git_classify_commit import main as m

            m()
        elif subcmd == "find-commit":
            from ww.git.git_commit import main as m

            m()
        elif subcmd == "delete-commit":
            from ww.git.git_delete_commit import main as m

            m()
        elif subcmd == "diff-tree":
            from ww.git.git_diff_tree import main as m

            m()
        elif subcmd == "check-filenames":
            from ww.git.git_filename import main as m

            m()
        elif subcmd == "force-push":
            from ww.git.git_force_push import main as m

            m()
        elif subcmd == "show":
            from ww.git.git_show_command import main as m

            m()
        elif subcmd == "squash":
            from ww.git.git_squash import main as m

            m()
        else:
            print(f"Unknown git command: {subcmd}")
            sys.exit(1)

    elif group == "search":
        _search_subcmds = {"bing", "code", "ddg", "ecosia", "filename", "startpage"}
        subcmd = sys.argv[1] if len(sys.argv) > 1 else ""
        if subcmd in _search_subcmds:
            sys.argv.pop(1)
            if subcmd == "bing":
                from ww.search.search_bing import main as m

                m()
            elif subcmd == "code":
                from ww.search.search_code import main as m

                m()
            elif subcmd == "ddg":
                from ww.search.search_duckduckgo import main as m

                m()
            elif subcmd == "ecosia":
                from ww.search.search_ecosia import main as m

                m()
            elif subcmd == "filename":
                from ww.search.search_filename import main as m

                m()
            elif subcmd == "startpage":
                from ww.search.search_startpage import main as m

                m()
        else:
            from ww.search.search import main as m

            m()

    else:
        print(f"Unknown command: {group}")
        sys.exit(1)
