import sys

from ww.env import load_env

load_env()


def _print_help():
    print("Usage: ww <group> [command] [options]")
    print("")
    print("Note:")
    print("  ww note                   Create a new note with git integration")
    print("  ww note log               Create a new log entry")
    print("  ww note obfuscate <file>  Obfuscate sensitive data in a file")
    print("")
    print("Screenshot:")
    print("  ww screenshot [DELAY]     Take a screenshot (macOS, --dir)")
    print("  ww screenshot-linux       Take a screenshot (Linux)")
    print("  ww screenshot note        Create a note from latest screenshot(s)")
    print(
        "  ww screenshot interact-note  Interactively capture screenshots and create a note"
    )
    print("")
    print("GIF:")
    print("  ww gif                    Create GIF from images")
    print("")
    print("GitHub:")
    print("  ww github info            Account info, plan, rate limits")
    print("  ww github repos           List your repos (recently pushed)")
    print("  ww github starred         List starred repos")
    print("  ww github followers       List followers")
    print("  ww github following       List following")
    print("  ww github notifications   List unread notifications")
    print("  ww github rate            Show rate limit details")
    print("  ww github gitmessageai    Generate AI commit message and commit")
    print()
    print("macOS:")
    print("  ww macos find-large-dirs  Find largest directories on disk")
    print("  ww macos system-info      Show system information")
    print("  ww macos install          Run macOS install tasks")
    print("  ww macos list-fonts       List installed fonts")
    print("  ww macos list-disks       List portable disks")
    print("  ww macos open-terminal    Open a new terminal window")
    print("  ww macos toast            Show macOS notification toast")
    print(
        "  ww macos charge-watch     Alert when charger is plugged in but not charging"
    )
    print(
        "  ww macos process          Analyze running processes and suggest what to kill"
    )
    print(
        "  ww macos settings-proxy   Set system proxy (HTTP/HTTPS 7890, SOCKS 7891) with bypass list"
    )
    print(
        "  ww macos apps             Audit installed apps by size and age (--no-llm, --json)"
    )
    print("  ww macos dock             List apps currently pinned to the Dock (--json)")
    print("")
    print("Image:")
    print("  ww image avatar           Process avatar image")
    print("  ww image crop             Crop an image")
    print("  ww image remove-bg        Remove image background")
    print("  ww image compress         Compress images")
    print("  ww image photo-compress   Compress photos")
    print("  ww image exif             Scan images for EXIF GPS location data")
    print("  ww image whatsapp         Download images from WhatsApp Web via Safari")
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
    print("  ww network discover           Discover devices on local network")
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
    print("  ww git gca                AI commit, no push (gemini-flash)")
    print("  ww git gpa                AI commit with pull+push (gemini-flash)")
    print("")
    print("Update:")
    print("  ww update [name...]        Update git repos (default: updated_repos)")
    print("")
    print("Latest:")
    print(
        "  ww latest notes [N]        Show filename and title of latest N notes (default 10)"
    )
    print("")
    print("  ww search                 Web search (multi-engine)")
    print("  ww search bing            Search with Bing")
    print("  ww search code            Search code")
    print("  ww search ddg             Search with DuckDuckGo")
    print("  ww search ecosia          Search with Ecosia")
    print("  ww search filename        Search by filename")
    print("  ww search startpage       Search with StartPage")
    print("  ww search tavily          Search with Tavily API")
    print("  ww search web --json      JSON output for LLM tool use")
    print("")
    print("PDF:")
    print("  ww pdf markdown-pdf       Convert a markdown file to PDF")
    print("  ww pdf pdf-pipeline       Batch convert markdown posts to PDFs")
    print("  ww pdf update-pdf         Convert markdown files changed in last commit")
    print("  ww pdf code2pdf           Convert code files in a directory to PDF")
    print("  ww pdf scale-pdf          Scale a PDF using pdfjam")
    print("  ww pdf test-latex         Test LaTeX/pandoc PDF generation")
    print("  ww pdf md2png             Convert markdown to PNG via HTML+PDF (Chrome)")
    print("")
    print("Copilot:")
    print("  ww copilot auth           Authenticate via GitHub OAuth device flow")
    print("  ww copilot models         List available Copilot models")
    print("  ww copilot chat           Chat with a Copilot model")
    print("")
    print("Sync:")
    print("  ww sync claude            Sync Claude Code settings (sanitized)")
    print("  ww sync bashrc [back|forth] Sync .bashrc file")
    print("  ww sync zprofile [back|forth] Sync .zprofile file")
    print("  ww sync ssh [back|forth]    Sync .ssh directory")
    print(
        "  ww sync hermes [back|forth]  Sync config.yaml, SOUL.md, hooks/, plugins/, agent-hooks/ (forth: ~/.hermes/ -> project)"
    )
    print("")
    print("Read (RAG):")
    print("  ww read index <dir>       Index documents in a directory (BGE + FAISS)")
    print("  ww read query <question>  Ask a question over indexed documents")
    print("  ww read query <q> --top-k N  Use N retrieved chunks (default 5)")
    print("")
    print("LLM:")
    print(
        "  ww llm compare            Compare 6 models on clipboard prompt, judge winner"
    )
    print("")
    print("OpenRouter:")
    print("  ww openrouter info        Account summary: credits, usage, key details")
    print("  ww openrouter credits     Show credits balance")
    print("  ww openrouter activity    Past week spend, requests, tokens (--days N)")
    print("  ww openrouter models      List available models")
    print("")
    print("Env:")
    print(
        "  ww env update             Pick a top Arena model and update MODEL= in .env"
    )
    print("")
    print("Display:")
    print("  ww display <dark|light|auto|show>")
    print(
        "                        Switch macOS appearance (dark/light/auto) or show current"
    )
    print("")
    print("Gen-image:")
    print("  ww gen-image              Generate image from clipboard text (Imagen 3)")
    print("")
    print("Action:")
    print("  ww action <workflow.yml>  Trigger a GitHub Actions workflow via gh CLI")
    print("")
    print("Degree (GDUFS 自考):")
    print("  ww degree                 AI-categorize recent self-study notices")
    print("  ww degree practical       Filter notices about 实践考核 / scores")
    print("  ww degree list            Raw scraped list (no AI)")
    print("  ww degree --pages N       Fetch N list pages (1-11, default 1)")
    print("")
    print("Marp:")
    print(
        "  ww marp <file.md>         Watch a markdown file and regenerate PDF via marp"
    )
    print("")
    print("Whisper:")
    print("  ww whisper <file.mp4>     Transcribe via whisper (Chinese, large, CUDA)")
    print(
        "  ww whisper refine <file.txt>  Refine transcription to .md via OpenRouter (deepseek-v4-flash)"
    )
    print("")
    print("Host:")
    print("  ww host                   Show all hosts")
    print("  ww host local             Local machine")
    print("  ww host workstation       Workstation (RTX 4070)")
    print("  ww host dmit              DMIT server")
    print("")
    print("Linux:")
    print("  ww linux gpu          Show GPU and CUDA details")
    print("  ww linux system       Comprehensive system overview")
    print("  ww linux disk         Show disk usage")
    print("  ww linux battery      Show battery status")
    print("  ww linux proxy-setup  Interactively configure APT proxy")
    print("  ww linux wol          Send a Wake-on-LAN packet")
    print("  ww linux terminal     Open a fullscreen terminal")
    print("")
    print("Cloudflare:")
    print(
        "  ww cloudflare monthly-visit  Monthly page views & visits from Web Analytics"
    )
    print("  ww cloudflare zones          List Cloudflare zones")
    print("  ww cloudflare datasets       List Web Analytics datasets")
    print("  ww cloudflare schema         Inspect GraphQL Account schema")
    print("  ww cloudflare pdf <file>     Parse Cloudflare Analytics PDF export")
    print("")
    print("Ghostty:")
    print("  ww ghostty                Open a Ghostty window at a random position")
    print("  ww ghostty close          Close all Ghostty windows")
    print("")
    print("Clash:")
    print("  ww clash select-provider    Select best proxy provider")
    print("  ww clash speed              Run speed test and select best proxy")
    print("  ww clash run                Full clash management with iterations")
    print("  ww clash top-proxies        Print top 5 fastest proxies (single-URL)")
    print("  ww clash top-proxies-multi  Print top 10 fastest proxies (multi-URL)")
    print("  ww clash speed-tiktok       Run speedtest + TikTok load time")
    print("  ww clash query-dns [host]   Test AliDNS DoH resolution")
    print("  ww clash gnome-proxy <set|unset>   Toggle GNOME proxy (Linux)")
    print("  ww clash macos-proxy <set|unset>   Toggle macOS proxy (networksetup)")
    print("  ww clash wifi <on|off>      Toggle macOS Wi-Fi")
    print("")
    print("Weather:")
    print("  ww weather                Today's weather (auto-detect location)")
    print("  ww weather N              Today + next N days (1-3)")
    print("  ww weather <city>         Weather for a city")
    print("  ww weather N <city>       N days for a city")
    print("  ww weather --detail       With network/location details")
    print("  ww weather --oneline      One-line summary")
    print("  ww weather --json         JSON output")
    print("")
    print("Completion:")
    print("  ww completion install     Install zsh tab completion")
    print("  ww completion script      Print completion script")


def _pop_subcmd():
    if len(sys.argv) > 1:
        return sys.argv.pop(1)
    return ""


def main():
    import os

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
            print("Tip: Use '/note' in hermes-agent to save assistant responses.")
            print("")
            if os.environ.get("NOTE_ENTER_CONFIRM", "1") != "0":
                try:
                    input("Press Enter to continue, Ctrl+C to quit... ")
                except KeyboardInterrupt:
                    print()
                    return
            from ww.note.note_workflow import main as m

            m()
        elif subcmd == "log":
            from ww.note.create_log import create_log

            create_log()
        elif subcmd == "log-file":
            from ww.note.create_log import create_log_from_file

            create_log_from_file()
        elif subcmd == "obfuscate":
            from ww.note.obfuscate_log import obfuscate_log

            obfuscate_log()
        else:
            print(f"Unknown note command: {subcmd}")
            sys.exit(1)

    elif group == "screenshot":
        # Only pop subcmd if it's "note" or "interact-note"; otherwise leave args for screenshot module
        if len(sys.argv) > 1 and sys.argv[1] in ("note", "interact-note"):
            subcmd = _pop_subcmd()
            if subcmd == "note":
                from ww.note.screenshot_log import main as m

                m()
            elif subcmd == "interact-note":
                from ww.image.interact_note import main as m

                m()
        else:
            from ww.image.screenshot import main as m

            m()

    elif group == "screenshot-linux":
        from ww.image.screenshot_linux import main as m

        m()

    elif group == "gif":
        from ww.gif.gif import main as m

        m()

    elif group == "github":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww github <command> [options]")
            print()
            print("Commands:")
            print("  info            Account info, plan, rate limits")
            print("  repos           List your repos (recently pushed)")
            print("  starred         List starred repos")
            print("  followers       List followers")
            print("  following       List following")
            print("  notifications   List unread notifications")
            print("  rate            Show rate limit details")
            print("  gitmessageai    Generate AI commit message and commit")
        elif subcmd == "info":
            from ww.github.github_mgmt import cmd_info

            cmd_info()
        elif subcmd == "repos":
            from ww.github.github_mgmt import cmd_repos

            cmd_repos()
        elif subcmd == "starred":
            from ww.github.github_mgmt import cmd_starred

            cmd_starred()
        elif subcmd == "followers":
            from ww.github.github_mgmt import cmd_followers

            cmd_followers()
        elif subcmd == "following":
            from ww.github.github_mgmt import cmd_following

            cmd_following()
        elif subcmd == "notifications":
            from ww.github.github_mgmt import cmd_notifications

            cmd_notifications()
        elif subcmd == "rate":
            from ww.github.github_mgmt import cmd_rate

            cmd_rate()
        elif subcmd == "gitmessageai":
            import argparse
            from ww.github.gitmessageai import gitmessageai

            parser = argparse.ArgumentParser(
                description="Generate commit message with AI and commit changes."
            )
            parser.add_argument("--no-push", dest="push", action="store_false")
            parser.add_argument(
                "--only-message", dest="only_message", action="store_true"
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
                allow_pull_push=args.allow_pull_push,
                type=args.type,
            )
        else:
            print(f"Unknown github command: {subcmd}")
            sys.exit(1)

    elif group == "macos":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww macos <command>")
            print("")
            print("Commands:")
            print("  find-large-dirs  Find largest directories on disk")
            print("  system-info      Show system information")
            print("  install          Run macOS install tasks")
            print("  list-fonts       List installed fonts")
            print("  list-disks       List portable disks")
            print("  open-terminal    Open a new terminal window")
            print("  toast            Show macOS notification toast")
            print(
                "  charge-watch     Alert when charger is plugged in but not charging"
            )
            print(
                "  process          Analyze running processes and suggest what to kill"
            )
            print("  settings-proxy   Set system proxy (HTTP/HTTPS 7890, SOCKS 7891)")
            print(
                "  apps             Audit installed apps by size and age (--no-llm, --json)"
            )
            print("  dock             List apps currently pinned to the Dock (--json)")
        elif subcmd == "find-large-dirs":
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
        elif subcmd == "charge-watch":
            from ww.macos.charge_watcher import main as m

            m()
        elif subcmd == "process":
            from ww.macos.process_analyze import main as m

            m()
        elif subcmd == "settings-proxy":
            from ww.macos.settings_proxy import main as m

            m()
        elif subcmd == "apps":
            from ww.macos.apps_audit import main as m

            m()
        elif subcmd == "dock":
            from ww.macos.dock import main as m

            m()
        else:
            print(f"Unknown macos command: {subcmd}")
            sys.exit(1)

    elif group == "image":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww image <command>")
            print("")
            print("Commands:")
            print("  avatar           Process avatar image")
            print("  crop             Crop an image")
            print("  remove-bg        Remove image background")
            print("  compress         Compress images")
            print("  photo-compress   Compress photos")
            print("  exif             Scan images for EXIF GPS location data")
            print("  whatsapp         Download images from WhatsApp Web via Safari")
        elif subcmd == "avatar":
            from ww.image.avatar import main as m

            m()
        elif subcmd == "crop":
            from ww.image.crop import main as m

            m()
        elif subcmd == "remove-bg":
            from ww.image.remove_bg import main as m

            m()
        elif subcmd == "compress":
            from ww.image.image_compress import main as m

            m()
        elif subcmd == "photo-compress":
            from ww.image.photo_compress import main as m

            m()
        elif subcmd == "exif":
            from ww.image.exif import main as m

            m()
        elif subcmd == "whatsapp":
            from ww.image.whatsapp import main as m

            m()
        else:
            print(f"Unknown image command: {subcmd}")
            sys.exit(1)

    elif group == "proc":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww proc <command>")
            print("")
            print("Commands:")
            print("  kill-pattern    Kill processes matching a pattern")
            print("  kill-port       Kill process on a given port")
            print("  kill-jekyll     Kill Jekyll server")
            print("  kill-proxy      Kill macOS proxy")
        elif subcmd == "kill-pattern":
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
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww utils <command>")
            print("")
            print("Commands:")
            print("  base64           Encode/decode base64")
            print("  ccr              CCR utility")
            print("  clean-zip        Clean zip files")
            print("  decode-jwt       Decode a JWT token")
            print("  py2txt           Convert Python files to text")
            print("  request-proxy    Make HTTP request via proxy")
            print("  smart-unzip      Smart unzip archives")
            print("  unzip            Unzip an archive")
        elif subcmd == "base64":
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
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww java <command>")
            print("")
            print("Commands:")
            print("  mvn               Maven project utilities")
            print("  analyze-deps      Analyze Java dependencies")
            print("  analyze-packages  Analyze Java packages")
            print("  analyze-poms      Analyze Maven POM files")
            print("  analyze-spring    Analyze Spring Boot project")
            print("  clean-log         Clean Java log files")
        elif subcmd == "mvn":
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
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww network <command>")
            print("")
            print("Commands:")
            print("  get-wifi-list      Get list of WiFi networks")
            print("  save-wifi-list     Save WiFi network list")
            print("  hack-wifi          WiFi password utilities")
            print("  wifi-gen-password  Generate WiFi password")
            print("  ip-scan            Scan IP addresses on network")
            print("  port-scan          Scan open ports")
            print("  wifi-scan          Scan for WiFi networks")
            print("  wifi-util          WiFi utility tools")
            print("  network-plot       Plot network topology")
            print("  discover           Discover devices on local network")
        elif subcmd == "get-wifi-list":
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
        elif subcmd == "discover":
            from ww.network.discover import main as m

            m()
        else:
            print(f"Unknown network command: {subcmd}")
            sys.exit(1)

    elif group == "git":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww git <command>")
            print("")
            print("Commands:")
            print("  amend-push         Amend last commit and force push")
            print("  classify           Classify git commits")
            print("  find-commit        Find a git commit")
            print("  delete-commit      Delete a git commit")
            print("  diff-tree          Show git diff tree")
            print("  check-filenames    Check git filenames")
            print("  force-push         Force push to remote")
            print("  show               Show git commit details")
            print("  squash             Squash git commits")
            print("  gca                AI commit, no push (gemini-flash)")
            print("  gpa                AI commit with pull+push (gemini-flash)")
        elif subcmd == "amend-push":
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
        elif subcmd == "gca":
            from ww.github.gitmessageai import gitmessageai

            gitmessageai(push=False)
        elif subcmd == "gpa":
            from ww.github.gitmessageai import gitmessageai

            gitmessageai(allow_pull_push=True)
        else:
            print(f"Unknown git command: {subcmd}")
            sys.exit(1)

    elif group == "search":
        _search_subcmds = {
            "bing",
            "code",
            "ddg",
            "filename",
            "startpage",
            "tavily",
            "web",
        }
        subcmd = sys.argv[1] if len(sys.argv) > 1 else ""
        if subcmd in _search_subcmds:
            sys.argv.pop(1)
            if subcmd in {"bing", "ddg", "startpage", "tavily"}:
                from ww.search.search_web import main as m

                sys.argv.insert(1, "--type")
                sys.argv.insert(2, subcmd)
                m()
            elif subcmd == "web":
                from ww.search.search_web import main as m

                m()
            elif subcmd == "code":
                from ww.search.search_code import main as m

                m()
            elif subcmd == "filename":
                from ww.search.search_filename import main as m

                m()
        else:
            from ww.search.search import main as m

            m()

    elif group == "pdf":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww pdf <command>")
            print("")
            print("Commands:")
            print("  markdown-pdf   Convert a markdown file to PDF")
            print("  pdf-pipeline   Batch convert markdown posts to PDFs")
            print("  update-pdf     Convert markdown files changed in last commit")
            print("  code2pdf       Convert code files in a directory to PDF")
            print("  scale-pdf      Scale a PDF using pdfjam")
            print("  test-latex     Test LaTeX/pandoc PDF generation")
            print("  md2png         Convert markdown to PNG via HTML+PDF (Chrome)")
        elif subcmd == "markdown-pdf":
            from ww.pdf.markdown_pdf import main as m

            m()
        elif subcmd == "pdf-pipeline":
            from ww.pdf.pdf_pipeline import main as m

            m()
        elif subcmd == "update-pdf":
            from ww.pdf.update_pdf import main as m

            m()
        elif subcmd == "code2pdf":
            from ww.pdf.code2pdf import main as m

            m()
        elif subcmd == "scale-pdf":
            from ww.pdf.scale_pdf import main as m

            m()
        elif subcmd == "test-latex":
            from ww.pdf.test_latex import main as m

            m()
        elif subcmd == "md2png":
            from ww.pdf.md2png import main as m

            m()
        else:
            print(f"Unknown pdf command: {subcmd}")
            sys.exit(1)

    elif group == "copilot":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww copilot <command>")
            print("")
            print("Commands:")
            print("  auth       Authenticate via GitHub OAuth device flow")
            print("  models     List available Copilot models")
            print("  chat       Chat with a Copilot model")
        elif subcmd == "auth":
            from ww.llm.copilot_auth import main as m

            m()
        elif subcmd == "models":
            import os
            from ww.llm.copilot_client import get_models

            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                print("Error: GITHUB_TOKEN not set. Run: ww copilot auth")
                sys.exit(1)
            models = get_models(github_token)
            for m in models:
                print(m.get("id", m))
        elif subcmd == "chat":
            import argparse
            from ww.llm.copilot_client import call_copilot_api

            parser = argparse.ArgumentParser(description="Chat with GitHub Copilot API")
            parser.add_argument("prompt", nargs="?", help="Prompt text")
            parser.add_argument("--model", type=str, default=None)
            parser.add_argument("--debug", action="store_true")
            args = parser.parse_args()
            prompt = args.prompt or input("Prompt: ")
            result = call_copilot_api(prompt, model=args.model, debug=args.debug)
            print(result)
        else:
            print(f"Unknown copilot command: {subcmd}")
            sys.exit(1)

    elif group == "sync":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww sync <command> [options]")
            print("")
            print("Commands:")
            print("  claude            Sync Claude Code settings (sanitized)")
            print("  bashrc [back|forth]  Sync .bashrc file")
            print("  zprofile [back|forth]  Sync .zprofile file")
            print("  zed [back|forth]     Sync ~/.config/zed/ directory (Zed config)")
            print("  ssh [back|forth]    Sync .ssh directory")
            print("  hermes                  Copy ww/config/hermes/ -> ~/.hermes/")
            print("  openclaw          Sync OpenClaw settings")
        elif subcmd == "claude":
            from ww.sync.claude import main as m

            m()
        elif subcmd == "bashrc":
            direction = _pop_subcmd()
            if direction in ("--help", "-h"):
                print("Usage: ww sync bashrc [back|forth]")
                print("  Sync .bashrc file")
                return
            direction = direction or "forth"
            from ww.sync.remote import sync_bashrc

            sync_bashrc(direction)
        elif subcmd == "zprofile":
            direction = _pop_subcmd()
            if direction in ("--help", "-h"):
                print("Usage: ww sync zprofile [back|forth]")
                print("  Sync .zprofile file")
                return
            direction = direction or "forth"
            from ww.sync.remote import sync_zprofile

            sync_zprofile(direction)
        elif subcmd == "zed":
            direction = _pop_subcmd()
            if direction in ("--help", "-h"):
                print("Usage: ww sync zed [back|forth]")
                print("  Sync ~/.config/zed/ directory (Zed Editor config)")
                return
            direction = direction or "forth"
            from ww.sync.remote import sync_zed

            sync_zed(direction)
        elif subcmd == "ssh":
            direction = _pop_subcmd()
            if direction in ("--help", "-h"):
                print("Usage: ww sync ssh [back|forth]")
                print("  Sync .ssh directory")
                return
            direction = direction or "forth"
            from ww.sync.remote import sync_ssh

            sync_ssh(direction)
        elif subcmd == "hermes":
            direction = _pop_subcmd()
            if direction in ("--help", "-h"):
                print("Usage: ww sync hermes [back|forth]")
                print(
                    "  Sync config.yaml, SOUL.md, hooks/, plugins/, agent-hooks/ (forth: ~/.hermes/ -> project, back: reverse)"
                )
                return
            direction = direction or "forth"
            from ww.sync.remote import sync_hermes

            sync_hermes(direction)
        elif subcmd == "openclaw":
            from ww.sync.openclaw import main as m

            m()
        else:
            print(f"Unknown sync command: {subcmd}")
            sys.exit(1)

    elif group == "linux":
        from ww.linux.main import main as m

        m()

    elif group == "host":
        from ww.machine.machine_info import main as m

        m()

    elif group == "cloudflare":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww cloudflare <command>")
            print("")
            print("Commands:")
            print("  monthly-visit  Monthly page views & visits from Web Analytics")
            print("  zones          List Cloudflare zones")
            print("  datasets       List Web Analytics datasets")
            print("  schema         Inspect GraphQL Account schema")
            print("  pdf <file>     Parse Cloudflare Analytics PDF export")
        elif subcmd == "monthly-visit":
            from ww.cloudflare.get_monthly_visit import main as m

            m()
        elif subcmd == "zones":
            from ww.cloudflare.get_zone_id import main as m

            m()
        elif subcmd == "datasets":
            from ww.cloudflare.get_web_analytics_datasets import main as m

            m()
        elif subcmd == "schema":
            from ww.cloudflare.get_schema import main as m

            m()
        elif subcmd == "pdf":
            from ww.cloudflare.read_analytics_data_from_pdf import main as m

            m()
        else:
            print(f"Unknown cloudflare command: {subcmd}")
            sys.exit(1)

    elif group == "ghostty":
        subcmd = _pop_subcmd()
        if subcmd in ("--help", "-h"):
            print("Usage: ww ghostty <command>")
            print("")
            print("Commands:")
            print("  (no args)   Open a Ghostty window at random position")
            print("  close       Close all Ghostty windows")
        elif subcmd == "" or subcmd == "random":
            from ww.ghostty.random_window import main as m

            m()
        elif subcmd == "close":
            from ww.ghostty.close import main as m

            m()
        else:
            print(f"Unknown ghostty command: {subcmd}")
            sys.exit(1)

    elif group == "clash":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww clash <command>")
            print("")
            print("Commands:")
            print("  select-provider    Select best proxy provider")
            print("  speed              Run speed test and select best proxy")
            print("  run                Full clash management with iterations")
            print("  top-proxies        Print top 5 fastest proxies (single-URL)")
            print("  top-proxies-multi  Print top 10 fastest proxies (multi-URL)")
            print("  speed-tiktok       Run speedtest + TikTok load time")
            print("  query-dns [host]   Test AliDNS DoH resolution")
            print("  gnome-proxy <set|unset>   Toggle GNOME proxy (Linux)")
            print("  macos-proxy <set|unset>   Toggle macOS proxy (networksetup)")
            print("  wifi <on|off>      Toggle macOS Wi-Fi")
        elif subcmd == "select-provider":
            from ww.clash.clash_select_provider import main as m

            m()
        elif subcmd == "speed":
            from ww.clash.clash_speed import main as m

            m()
        elif subcmd == "run":
            from ww.clash.clash import main as m

            m()
        elif subcmd == "top-proxies":
            from ww.clash.speed import main as m

            m()
        elif subcmd == "top-proxies-multi":
            from ww.clash.speed_plus import main as m

            m()
        elif subcmd == "speed-tiktok":
            from ww.clash.speed_tiktok import main as m

            m()
        elif subcmd == "query-dns":
            from ww.clash.query_dns import main as m

            m()
        elif subcmd == "gnome-proxy":
            from ww.clash.gnome_proxy import main as m

            m()
        elif subcmd == "macos-proxy":
            from ww.clash.networksetup import main as m

            m()
        elif subcmd == "wifi":
            from ww.clash.wifi_toggle import main as m

            m()
        else:
            print(f"Unknown clash command: {subcmd}")
            sys.exit(1)

    elif group == "display":
        from ww.display.appearance import main as m

        m()

    elif group == "gen-image":
        from ww.image.gen_image import main as m

        m()

    elif group == "action":
        from ww.action.action import main as m

        m()

    elif group == "openrouter":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww openrouter <command>")
            print()
            print("Commands:")
            print("  info      Account summary: credits, usage, key details")
            print("  credits   Show credits balance")
            print("  activity  Past week spend, requests, tokens (--days N)")
            print("  models    List available models (--json for raw)")
        elif subcmd == "info":
            from ww.llm.openrouter_mgmt import cmd_info

            cmd_info()
        elif subcmd == "credits":
            from ww.llm.openrouter_mgmt import cmd_credits

            cmd_credits()
        elif subcmd == "activity":
            from ww.llm.openrouter_mgmt import cmd_activity

            days = 7
            for i, a in enumerate(sys.argv):
                if a == "--days" and i + 1 < len(sys.argv):
                    days = int(sys.argv[i + 1])
            cmd_activity(days=days)
        elif subcmd == "models":
            from ww.llm.openrouter_mgmt import cmd_models

            cmd_models(as_json="--json" in sys.argv)
        else:
            print(f"Unknown openrouter command: {subcmd}")
            sys.exit(1)

    elif group == "llm":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww llm <command>")
            print("")
            print("Commands:")
            print("  compare    Compare 6 models on clipboard prompt, judge winner")
        elif subcmd == "compare":
            from ww.llm.compare import main as m

            m()
        else:
            print(f"Unknown llm command: {subcmd}")
            sys.exit(1)

    elif group == "env":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww env <command>")
            print("")
            print("Commands:")
            print("  update    Pick a top Arena model and update MODEL= in .env")
        elif subcmd == "update":
            from ww.llm.update_env import main as m

            m()
        else:
            print(f"Unknown env command: {subcmd}")
            sys.exit(1)

    elif group == "read":
        from ww.read.read_assistant import main as m

        m()

    elif group == "marp":
        from ww.marp.marp_watch import main as m

        m()

    elif group == "whisper":
        if len(sys.argv) > 1 and sys.argv[1] == "refine":
            sys.argv.pop(1)
            from ww.audio.whisper_refine import main as m

            m()
        else:
            from ww.audio.whisper_translate import main as m

            m()

    elif group == "update":
        from ww.git.git_update import main as m

        m()

    elif group == "degree":
        from ww.degree.degree import main as m

        m()

    elif group == "latest":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww latest <command>")
            print("")
            print("Commands:")
            print(
                "  notes [N]    Show filename and title of latest N notes (default 10)"
            )
        elif subcmd == "notes":
            from ww.note.latest_notes import main as m

            m()
        else:
            print(f"Unknown latest command: {subcmd}")
            sys.exit(1)

    elif group == "weather":
        from ww.weather.weather import main as m

        m()

    elif group == "completion":
        import os
        import shutil

        subcmd = _pop_subcmd()
        script_dir = os.path.join(os.path.dirname(__file__), "..", "completions")
        script_path = os.path.join(script_dir, "_ww")

        if subcmd == "script":
            if os.path.exists(script_path):
                with open(script_path) as f:
                    print(f.read())
            else:
                print("Error: completion script not found at", script_path)
                sys.exit(1)

        elif subcmd == "install":
            target_dir = os.path.expanduser("~/.zsh/completions")
            os.makedirs(target_dir, exist_ok=True)
            target = os.path.join(target_dir, "_ww")
            shutil.copy2(script_path, target)
            print(f"Installed completion script to {target}")
            print()
            print("Make sure your ~/.zshrc contains:")
            print("  fpath=(~/.zsh/completions $fpath)")
            print("  autoload -Uz compinit && compinit")
            print()
            print("Then restart your shell or run:")
            print("  source ~/.zshrc")

        else:
            print("Usage: ww completion <install|script>")
            print()
            print("Commands:")
            print("  install   Install zsh tab completion to ~/.zsh/completions/")
            print("  script    Print the completion script to stdout")

    else:
        print(f"Unknown command: {group}")
        sys.exit(1)
