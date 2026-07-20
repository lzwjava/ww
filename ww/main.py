import sys

from ww.env import load_env

load_env()


def _print_help():
    print("Usage: ww <group> [command] [options]")
    print("")
    print("Help:")
    print("  ww help <file_path>       LLM-powered help for a specific module file")
    print("  ww help                   Show this help")
    print("")
    print("Action:")
    print(
        "  ww action [workflow.yml]  Trigger a GitHub Actions workflow (default: gh-pages.yml)"
    )
    print("")
    print("Actions:")
    print(
        "  ww actions check          Check recent workflow runs (default: gh-pages.yml)"
    )
    print("  ww actions check --repo R --count N  Specify repo and count")
    print("")
    print("AMD Dev Cloud:")
    print(
        "  ww amd-dev-cloud snapshots    List snapshots (requires AMD_DEV_CLOUD_API_KEY)"
    )
    print(
        "  ww amd-dev-cloud start-train  Create GPU droplet from snapshot for training"
    )
    print("  ww amd-dev-cloud end-train    Snapshot and destroy a GPU droplet")
    print("  ww amd-dev-cloud delete-snapshot  Delete a snapshot")
    print("")
    print("Appearance:")
    print(
        "  ww appearance             Manage display appearance (dark/light/auto/show)"
    )
    print("")
    print("Benchmark:")
    print("  ww benchmark                  Run GPU benchmark locally")
    print("  ww benchmark --ssh HOST:PORT  Upload script and run on remote server")
    print("  ww benchmark --key PATH       SSH key (default: ~/.ssh/id_ed25519)")
    print("")
    print("Clash:")
    print("  ww clash query-dns [host]   Test AliDNS DoH resolution")
    print("  ww clash gnome-proxy <set|unset>   Toggle GNOME proxy (Linux)")
    print("  ww clash macos-proxy <set|unset>   Toggle macOS proxy (networksetup)")
    print("  ww clash run                Full clash management with iterations")
    print("  ww clash select-provider    Select best proxy provider")
    print("  ww clash speed              Run speed test and select best proxy")
    print("  ww clash speed-tiktok       Run speedtest + TikTok load time")
    print("  ww clash top-proxies        Print top 5 fastest proxies (single-URL)")
    print("  ww clash top-proxies-multi  Print top 10 fastest proxies (multi-URL)")
    print("  ww clash wifi <on|off>      Toggle macOS Wi-Fi")
    print("")
    print("Cloudflare:")
    print("  ww cloudflare datasets       List Web Analytics datasets")
    print(
        "  ww cloudflare monthly-visit  Monthly page views & visits from Web Analytics"
    )
    print("  ww cloudflare pdf <file>     Parse Cloudflare Analytics PDF export")
    print("  ww cloudflare schema         Inspect GraphQL Account schema")
    print("  ww cloudflare zones          List Cloudflare zones")
    print("")
    print("Completion:")
    print("  ww completion install     Install zsh tab completion")
    print("  ww completion script      Print completion script")
    print("")
    print("Cook:")
    print(
        "  ww cook <minutes>        Set a cooking timer (notifies every 2min after expiry)"
    )
    print("  ww cook clear            Clear the cooking timer and stop notifications")
    print("")
    print("Copilot:")
    print("  ww copilot auth           Authenticate via GitHub OAuth device flow")
    print("  ww copilot chat           Chat with a Copilot model")
    print("  ww copilot models         List available Copilot models")
    print("")
    print("Conversation:")
    print("  ww conversation json <n>  Capture conversation JSON from stdin/clipboard")
    print(
        "  ww conversation generate <file>  Generate audio from conversation JSON (GCloud TTS)"
    )
    print(
        "  ww conversation notes     Convert conversation JSON files to markdown notes"
    )
    print(
        "  ww conversation to-video <file>  Create video from audio file with cover image"
    )
    print("  ww conversation to-image <file>  Resize and crop image to 854x480")
    print("")
    print("DB (Command History):")
    print("  ww db errors              Show recent error commands (--limit N)")
    print("  ww db recent              Show recent commands (--limit N)")
    print("  ww db search <pattern>    Search command history")
    print("  ww db stats               Show overall usage statistics")
    print("  ww db top                 Show most frequently used commands (--limit N)")
    print("")
    print("Degree (GDUFS Self-Study Exam):")
    print("  ww degree --pages N       Fetch N list pages (1-11, default 1)")
    print(
        "  ww degree --months N      Only articles from last N months (default 3, 0=all)"
    )
    print("  ww degree                 AI-categorize recent self-study notices")
    print("  ww degree list            Raw scraped list (no AI)")
    print("  ww degree practical       Filter notices about practical exams / scores")
    print("")
    print("Display:")
    print("  ww display <dark|light|auto|show>")
    print(
        "                        Switch macOS appearance (dark/light/auto) or show current"
    )
    print("")
    print("Env:")
    print(
        "  ww env update             Pick a top Arena model and update MODEL= in .env"
    )
    print(
        "  ww env warp               Install Warp (the Agentic Dev Environment) on Linux"
    )
    print("  ww env ghostty           Install Ghostty terminal on Linux")
    print("  ww env github-desktop    Install GitHub Desktop on macOS and Linux")
    print("")
    print("FFmpeg:")
    print("  ww ffmpeg m4a <file1.m4a> [file2.m4a ...]")
    print("                           Convert .m4a file(s) to MP3, combining into one")
    print("  ww ffmpeg merge <file1> <file2> [... <fileN>]")
    print("                           Merge two or more audio/video files into one")
    print("")
    print("Format:")
    print("  ww format <file.json>     Pretty-print a JSON file in-place")
    print("")
    print("GCP Speech:")
    print("  ww gcp-speech transcribe <file> [--lang LANG]")
    print("                           Transcribe audio via Google Cloud Speech-to-Text")
    print("  ww gcp-speech result <job-id> [--wait]")
    print("                           Query the result of a previous transcription job")
    print("")
    print("Gen-image:")
    print("  ww gen-image              Generate image from clipboard text (Imagen 3)")
    print("")
    print("Gen-video:")
    print(
        "  ww gen-video <file>       Generate a 15s short-form video (9:16) from a markdown note"
    )
    print(
        "                           5 slides × 3s, centered images, top/bottom text, no audio"
    )
    print("  ww gen-video <file>       With --upload: generate + upload to YouTube")
    print(
        "  ww gen-video upload       Upload a video to YouTube via YouTube Data API v3"
    )
    print("  ww gen-video set-privacy  Change privacy of an uploaded YouTube video")
    print("  ww gen-video server       Start the gen-video API server (FastAPI)")
    print("")
    print("GIF:")
    print("  ww gif                    Create GIF from images")
    print("")
    print("Git:")
    print("  ww git amend-push         Amend last commit and force push")
    print("  ww git check-filenames    Check git filenames")
    print("  ww git classify           Classify git commits")
    print("  ww git delete-commit      Delete a git commit")
    print("  ww git diff-tree          Show git diff tree")
    print("  ww git find-commit        Find a git commit")
    print("  ww git force-push         Force push to remote")
    print("  ww git gca                AI commit, no push (gemini-flash)")
    print("  ww git gpa                AI commit with pull+push (gemini-flash)")
    print("  ww git show               Show git commit details")
    print("  ww git squash             Squash git commits")
    print("")
    print("GitHub:")
    print("  ww github followers       List followers")
    print("  ww github following       List following")
    print("  ww github gitmessageai    Generate AI commit message and commit")
    print("  ww github info            Account info, plan, rate limits")
    print("  ww github interests <u1> <u2>  Compare GitHub interests between two users")
    print("  ww github notifications   List unread notifications")
    print("  ww github profile <user>  Detailed profile report for any GitHub user")
    print("  ww github rate            Show rate limit details")
    print("  ww github repos           List your repos (recently pushed)")
    print("  ww github starred         List starred repos")
    print("")
    print("Ghostty:")
    print("  ww ghostty                Open a Ghostty window at a random position")
    print("  ww ghostty close          Close all Ghostty windows")
    print("  ww ghostty focus <N>      Focus a Ghostty window by index or title")
    print("  ww ghostty list           List all open Ghostty windows")
    print("")
    print("HackerNews:")
    print(
        "  ww hackernews [--count N] [topic]  AI-agent reads HN (LangGraph, default 10)"
    )
    print("")
    print("Headphone:")
    print(
        "  ww headphone              Test audio devices: play tone, record and playback"
    )
    print("  ww headphone list         List connected audio devices")
    print("")
    print("Hermes:")
    print("  ww hermes check            Check Hermes agent note plugin health")
    print("")
    print("Host:")
    print("  ww host                   Show all hosts")
    print("  ww host dmit              DMIT server")
    print("  ww host local             Local machine")
    print("  ww host workstation       Workstation (RTX 4070)")
    print("")
    print("HuggingFace:")
    print("  ww hf [username]          Show HuggingFace profile (default: lzwjava)")
    print(
        "  ww hf news                Trending models, datasets, and spaces (--limit N, --json)"
    )
    print(
        "  ww hf pull [repo] [path]  Download a HF model repo to local dir (--revision branch)"
    )
    print(
        "  ww hf push [path]         Upload local dir to HF model repo (--repo id, --message)"
    )
    print("  ww hf top30               Top 30 most-followed HF users")
    print("")
    print("Image:")
    print("  ww image avatar           Process avatar image")
    print("  ww image compress         Compress images")
    print("  ww image crop             Crop an image")
    print("  ww image exif             Scan images for EXIF GPS location data")
    print("  ww image photo-compress   Compress photos")
    print("  ww image remove-bg        Remove image background")
    print("  ww image whatsapp         Download images from WhatsApp Web via Safari")
    print("")
    print("Java:")
    print("  ww java analyze-deps      Analyze Java dependencies")
    print("  ww java analyze-packages  Analyze Java packages")
    print("  ww java analyze-poms      Analyze Maven POM files")
    print("  ww java analyze-spring    Analyze Spring Boot project")
    print("  ww java clean-log         Clean Java log files")
    print("  ww java mvn               Maven project utilities")
    print("")
    print("Inference:")
    print("  ww inference test [--model M]  Detect SGLang vs vLLM backend for a model")
    print("                              (default: tencent/hy3-preview)")
    print("")
    print("Latest:")
    print(
        "  ww latest notes [N]        Show filename and title of latest N notes (default 10)"
    )
    print("")
    print("Linux:")
    print("  ww linux battery      Show battery status")
    print("  ww linux disk         Show disk usage")
    print("  ww linux gpu          Show GPU and CUDA details")
    print("  ww linux proxy-setup  Interactively configure APT proxy")
    print("  ww linux switch-keys  Swap Caps Lock and Left Control keys")
    print("  ww linux system       Comprehensive system overview")
    print("  ww linux terminal     Open a fullscreen terminal")
    print("  ww linux wol          Send a Wake-on-LAN packet")
    print("")
    print("LLM:")
    print(
        "  ww llm compare            Compare 6 models on clipboard prompt, judge winner"
    )
    print("")
    print("macOS:")
    print(
        "  ww macos apps             Audit installed apps by size and age (--no-llm, --json)"
    )
    print(
        "  ww macos charge-watch     Alert when charger is plugged in but not charging"
    )
    print("  ww macos dock             List apps currently pinned to the Dock (--json)")
    print("  ww alarm [clear|list|<min>] Clock alarms: set, list, or remove all")
    print("  ww macos find-large-dirs  Find largest directories on disk")
    print("  ww macos install          Run macOS install tasks")
    print("  ww macos list-disks       List portable disks")
    print("  ww macos list-fonts       List installed fonts")
    print("  ww macos open-terminal    Open a new terminal window")
    print(
        "  ww macos process          Analyze running processes and suggest what to kill"
    )
    print(
        "  ww macos settings-proxy   Set system proxy (HTTP/HTTPS 7890, SOCKS 7891) with bypass list"
    )
    print("  ww macos system-info      Show system information")
    print("  ww macos toast            Show macOS notification toast")
    print("")
    print("Maps:")
    print("  ww maps directions <from> <to> [--mode M]       Route directions")
    print("  ww maps elevation <lat,lng>            Elevation for location")
    print("  ww maps geocode <address>              Address to lat/lng")
    print("  ww maps home [lat,lng]                 Distance/time to home")
    print("  ww maps ip <address>                   Geolocate an IP")
    print("  ww maps location --paste [origin]      Trip report from clipboard URL")
    print("  ww maps nearby <lat,lng> [radius] [type]        Nearby places")
    print("  ww maps office [lat,lng]               Distance/time to OneLink office")
    print("  ww maps place <place_id>               Place details")
    print("  ww maps reverse <lat,lng>              Lat/lng to address")
    print("  ww maps search <query> [--near L] [--radius M]  Places text search")
    print("  ww maps test                           Test all Google Maps APIs")
    print("  ww maps timezone <lat,lng>             Timezone for location")
    print("")
    print("Markdown:")
    print(
        "  ww md md2img              Convert markdown to JPG/PNG via HTML screenshot (Playwright)"
    )
    print("")
    print("Marp:")
    print(
        "  ww marp <file.md>         Watch a markdown file and regenerate PDF via marp"
    )
    print("")
    print("Math:")
    print("  ww math tanh              Tanh (Hyperbolic Tangent) reference")
    print("  ww math tanh --plot       Generate and open tanh figure")
    print("  ww math tanh --values     Tanh value table")
    print("  ww math tanh --all        Tanh comprehensive reference")
    print("  ww math tanh x1 x2 ...    Custom x values for the table")
    print("")
    print("Network:")
    print("  ww network discover           Discover devices on local network")
    print("  ww network get-wifi-list      Get list of WiFi networks")
    print("  ww network hack-wifi          WiFi password utilities")
    print("  ww network ip-scan            Scan IP addresses on network")
    print("  ww network network-plot       Plot network topology")
    print("  ww network port-scan          Scan open ports")
    print("  ww network save-wifi-list     Save WiFi network list")
    print(
        "  ww network speed              Internet speed test (ping, jitter, bandwidth)"
    )
    print("  ww network physical-speed     Estimate speed via EM Doppler shift")
    print("  ww network wifi-gen-password  Generate WiFi password")
    print("  ww network wifi-scan          Scan for WiFi networks")
    print("  ww network wifi-scan-best     Scan WiFi and recommend best signal")
    print("  ww network wifi-util          WiFi utility tools")
    print("")
    print("News:")
    print(
        "  ww news nytimes [--count N]  Summarize NYTimes Chinese articles (default: 10)"
    )
    print(
        "  ww news finance [query]      Search and summarize finance news (default: 10)"
    )
    print("")
    print("Note:")
    print("  ww note                   Quick: clipboard → queue (fast)")
    print("  ww note --sync            Full pipeline: create, fix, commit, push")
    print("  ww note --code            LLM-wrap code in clipboard, then queue")
    print("  ww note process           Drain queue: create notes, commit, push")
    print("  ww note status            Show queue status")
    print("  ww note clear             Clear done/failed entries from queue")
    print("  ww note watch             Auto-process queue when new notes arrive")
    print("  ww note log               Quick: clipboard → log queue (fast)")
    print("  ww note html              Quick: clipboard → Jekyll HTML note (visual)")
    print("  ww note obfuscate <file>  Obfuscate sensitive data in a file")
    print("")
    print("OpenRouter:")
    print("  ww openrouter activity    Past week spend, requests, tokens (--days N)")
    print("  ww openrouter credits     Show credits balance")
    print("  ww openrouter info        Account summary: credits, usage, key details")
    print("  ww openrouter models      List available models")
    print("")
    print("PDF:")
    print("  ww pdf code2pdf           Convert code files in a directory to PDF")
    print("  ww pdf markdown-pdf       Convert a markdown file to PDF")
    print("  ww pdf md2png             Convert markdown to PNG via HTML+PDF (Chrome)")
    print("  ww pdf pdf-pipeline       Batch convert markdown posts to PDFs")
    print("  ww pdf scale-pdf          Scale a PDF using pdfjam")
    print("  ww pdf test-latex         Test LaTeX/pandoc PDF generation")
    print("  ww pdf update-pdf         Convert markdown files changed in last commit")
    print("")
    print("Process:")
    print("  ww proc kill-jekyll       Kill Jekyll server")
    print("  ww proc kill-pattern      Kill processes matching a pattern")
    print("  ww proc kill-port         Kill process on a given port")
    print("  ww proc kill-proxy        Kill macOS proxy")
    print("")
    print("Projects:")
    print("  ww projects count         Count directories in ~/projects")
    print("  ww projects update [name|@cat...]  Update git repos (default: repos.json)")
    print("")
    print("Qwen (Vision):")
    print("  ww qwen vl [--image file] [prompt]  Query local Qwen2-VL vision model")
    print("")
    print("Read (RAG):")
    print("  ww read index <dir>       Index documents in a directory (BGE + FAISS)")
    print("  ww read query <question>  Ask a question over indexed documents")
    print("  ww read query <q> --top-k N  Use N retrieved chunks (default 5)")
    print("")
    print("RunPod:")
    print(
        "  ww runpod start <gpu> [name]  Create and start a pod (rtx4000ada, h200, a100, ...)"
    )
    print("  ww runpod list                List all pods")
    print("  ww runpod ssh <pod_id>        SSH into a pod")
    print("  ww runpod stop <pod_id>       Stop a pod")
    print("  ww runpod delete <pod_id>     Delete a pod")
    print("  ww runpod gpus                List available GPU types")
    print("  ww runpod send <file>         Send a file (one-time code)")
    print("  ww runpod receive <code>      Receive a file via code")
    print("  ww runpod user                Account info")
    print("  ww runpod billing             Billing history")
    print("  ww runpod raw <args...>       Pass raw args to runpodctl")
    print("")
    print("Screenshot:")
    print("  ww screenshot [DELAY]     Take a screenshot (macOS, --dir)")
    print(
        "  ww screenshot interact-note [--skip-analysis]  Interactively capture screenshots and create a note"
    )
    print(
        "  ww screenshot note [--skip-analysis]  Create a note from latest screenshot(s)"
    )
    print(
        "  ww screenshot-linux       Take a screenshot (Linux, --no-save to clipboard, --area 1-4 for quadrant)"
    )
    print("")
    print("Search:")
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
    print("Sync:")
    print("  ww sync bashrc [back|forth] Sync .bashrc file")
    print("  ww sync claude            Sync Claude Code settings")
    print(
        "  ww sync hermes [back|forth]  Sync config.yaml, SOUL.md, hooks/, plugins/, agent-hooks/ (forth: ~/.hermes/ -> $CONFIG_DIR)"
    )
    print("  ww sync ssh [back|forth]    Sync .ssh directory")
    print("  ww sync ww [back|forth]    Sync .env to/from $CONFIG_DIR/ww/")
    print("  ww sync zed [back|forth]   Sync ~/.config/zed/ directory (Zed config)")
    print("  ww sync zprofile [back|forth] Sync .zprofile file")
    print("")
    print("Torch:")
    print("  ww torch                  Find all Pythons and check which have PyTorch")
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
    print("Vision Model:")
    print(
        "  ww vision-model test [--model MODEL]  Test VISION_MODEL via OpenRouter (image + text)"
    )
    print("")
    print("Weather:")
    print("  ww rain                   Record video, analyze rain intensity (in-car)")
    print("  ww rain --seconds 5       Longer video capture")
    print("  ww weather                Today's weather (auto-detect location)")
    print("  ww weather N              Today + next N days (1-3)")
    print("  ww weather <city>         Weather for a city")
    print("  ww weather N <city>       N days for a city")
    print("  ww weather --detail       With network/location details")
    print("  ww weather --json         JSON output")
    print("  ww weather --oneline      One-line summary")
    print("")
    print("Whisper:")
    print("  ww whisper <file.mp4>     Transcribe via whisper (Chinese, large, CUDA)")
    print(
        "  ww whisper diarize <file> Transcribe with speaker labels (whisperx + pyannote)"
    )
    print(
        "  ww whisper organize <file.txt>  Lightly clean: fix grammar, remove noise, third-person narration"
    )
    print(
        "  ww whisper refine <file.txt>  Refine transcription to .md via OpenRouter (deepseek-v4-flash)"
    )
    print("")
    print("Transcript:")
    print(
        "  ww transcript <file.json>      Extract transcript from Google Cloud STT JSON to markdown"
    )
    print("  ww transcript <file.json> -o out.md  Write markdown to file")
    print("")
    print("X (Twitter):")
    print(
        "  ww x post --n 5           Generate X posts from markdown files in original/"
    )
    print("  ww x unfollow --count 500           Smart bulk unfollow via LLM")
    print("  ww x unfollow --count 500 --delay 3  Adjust delay between unfollows")
    print("")
    print("Zed:")
    print(
        "  ww zed [path]             Open Zed connected to remote workstation via SSH"
    )


def _pop_subcmd():
    if len(sys.argv) > 1:
        return sys.argv.pop(1)
    return ""


def main():
    # Capture raw args before any popping for logging
    raw_args = list(sys.argv)
    exit_code = 0

    if len(sys.argv) < 2:
        from ww.db import log_command, parse_command

        group_name, subcmd = parse_command(raw_args)
        log_command(raw_args, group_name, subcmd, 0)
        print("hello world")
        print("")
        _print_help()
        return

    try:
        _main_dispatch(raw_args)
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 1
        raise
    except Exception:
        exit_code = 1
        raise
    finally:
        from ww.db import log_command, parse_command

        group_name, subcmd = parse_command(raw_args)
        log_command(raw_args, group_name, subcmd, exit_code)


def _main_dispatch(raw_args: list):
    import os

    group = sys.argv.pop(1)

    if group in ("--help", "-h"):
        _print_help()
        return

    if group == "help":
        # ww help <file_path> — LLM-powered help for a specific module
        # Don't pop the file path — let the help module read it from sys.argv
        if len(sys.argv) <= 1:
            _print_help()
            return
        from ww.help_llm.help import main as m

        m()
        return

    if group == "note":
        subcmd = _pop_subcmd()
        # If subcmd starts with '-', it's a flag (e.g. --sync), not a subcommand
        if subcmd.startswith("-"):
            if subcmd in ("--help", "-h"):
                _print_help()
                return
            sys.argv.insert(1, subcmd)  # push back for argparse
            subcmd = ""

        if subcmd == "" or subcmd == "note":
            # Check if --sync flag is present → old behavior (full pipeline)
            if "--sync" in sys.argv:
                sys.argv.remove("--sync")
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
            elif "--code" in sys.argv:
                sys.argv.remove("--code")
                from ww.note.note_queue import enqueue_clipboard
                from ww.note.create_note_utils import wrap_code_snippets

                raw = __import__("pyperclip").paste().strip()
                if not raw:
                    print("[warn] Clipboard is empty")
                    return
                print(f"[info] Wrapping code snippets via LLM ({len(raw)} chars)...")
                processed = wrap_code_snippets(raw)
                enqueue_clipboard(text=processed, code=True)
            else:
                # Fast path: read clipboard → queue → return instantly
                from ww.note.note_queue import enqueue_clipboard

                enqueue_clipboard()
        elif subcmd == "process":
            from ww.note.note_queue_process import main as process_main

            process_main()
        elif subcmd == "status":
            from ww.note.note_queue import print_status

            print_status()
        elif subcmd == "clear":
            from ww.note.note_queue import clear_done

            removed = clear_done()
            print(f"[ok] Cleared {removed} done/failed entries")
        elif subcmd == "watch":
            from ww.note.note_watcher import main as watch_main

            watch_main()
        elif subcmd == "log":
            import argparse
            from ww.note.note_queue import enqueue_log

            log_parser = argparse.ArgumentParser(
                prog="ww note log", description="Create a log entry (queued)"
            )
            log_parser.add_argument(
                "--ext", help="File extension to use (e.g. md, txt)"
            )
            log_parser.add_argument(
                "--detect-ext",
                action="store_true",
                help="Use LLM to detect file extension from content",
            )
            log_parser.add_argument(
                "--friendly-name",
                action="store_true",
                help="Use LLM to generate a friendly filename instead of timestamp",
            )
            log_args, _ = log_parser.parse_known_args(sys.argv[1:])
            kwargs = {}
            if log_args.ext:
                kwargs["ext"] = log_args.ext
            if log_args.detect_ext:
                kwargs["detect_ext"] = True
            if log_args.friendly_name:
                kwargs["friendly_name"] = True
            enqueue_log(**kwargs)
        elif subcmd == "html":
            from ww.note.create_note_html import main as html_main

            html_main()
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
            print("  interests <u1> <u2>  Compare GitHub interests between two users")
            print("  profile <user>  Detailed profile report for any GitHub user")
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
        elif subcmd == "profile":
            from ww.github.github_mgmt import cmd_profile

            username = _pop_subcmd()
            if not username:
                print("Usage: ww github profile <username>")
                sys.exit(1)
            cmd_profile(username)
        elif subcmd == "interests":
            from ww.github.github_mgmt import cmd_interests

            user1 = _pop_subcmd()
            user2 = _pop_subcmd()
            if not user1 or not user2:
                print("Usage: ww github interests <user1> <user2>")
                sys.exit(1)
            cmd_interests(user1, user2)
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
            print("  compare          Compare two files in Beyond Compare")
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
        elif subcmd == "compare":
            from ww.utils.compare import main as m

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
            print("  wifi-scan-best     Scan WiFi and recommend best signal")
            print("  wifi-util          WiFi utility tools")
            print("  network-plot       Plot network topology")
            print("  discover           Discover devices on local network")
            print("  speed              Internet speed test (ping, jitter, bandwidth)")
            print("  physical-speed     Estimate speed via EM Doppler shift")
            print(
                "  ip                 Show real WAN IP (bypasses proxy), track changes"
            )
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
        elif subcmd == "wifi-scan-best":
            from ww.network.wifi_scan_best import main as m

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
        elif subcmd == "speed":
            from ww.network.speed import main as m

            m()
        elif subcmd == "physical-speed":
            from ww.network.physical_speed import main as m

            m()
        elif subcmd == "ip":
            from ww.network.wan_ip import main as m

            m()
        else:
            print(f"Unknown network command: {subcmd}")
            sys.exit(1)

    elif group == "news":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww news <command>")
            print("")
            print("Commands:")
            print(
                "  nytimes [--count N]  Summarize NYTimes Chinese articles (default: 10)"
            )
            print(
                "  finance [query]      Search and summarize finance news (default: 10)"
            )
        elif subcmd == "nytimes":
            from ww.news.nytimes import main as m

            m()
        elif subcmd == "finance":
            from ww.news.finance import main as m

            m()
        else:
            print(f"Unknown news command: {subcmd}")
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
            print("  editor             Set git editor (zed|vscode)")
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
        elif subcmd == "editor":
            from ww.git.git_editor import main as m

            m()
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

    elif group == "md":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww md <command>")
            print("")
            print("Commands:")
            print(
                "  md2img         Convert markdown to JPG/PNG via HTML screenshot (Playwright)"
            )
        elif subcmd == "md2img":
            from ww.md.md2img import main as m

            m()
        else:
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

    elif group == "conversation":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww conversation <command> [options]")
            print("")
            print("Commands:")
            print("  json <name>       Capture conversation JSON from stdin/clipboard")
            print(
                "  generate <file>   Generate audio from conversation JSON (GCloud TTS)"
            )
            print(
                "  notes             Convert conversation JSON files to markdown notes"
            )
            print("  to-video <file>   Create video from audio file with cover image")
            print("  to-image <file>   Resize and crop image to 854x480")
            print("")
            print("Options:")
            print("  --output-dir DIR  Output directory for audio/JSON files")
            print("  --type en|cn      Language type for voices (default: en)")
            print("  --seed N          Random seed for voice selection")
        elif subcmd == "json":
            from ww.conversation.json import main as m

            m()
        elif subcmd == "generate":
            from ww.conversation.generate import main as m

            m()
        elif subcmd == "notes":
            from ww.conversation.notes import main as m

            m()
        elif subcmd == "to-video":
            from ww.conversation.video import main as m

            m()
        elif subcmd == "to-image":
            from ww.conversation.image import main as m

            m()
        else:
            print(f"Unknown conversation command: {subcmd}")
            sys.exit(1)

    elif group == "db":
        from ww.db_stats import main as m

        m()

    elif group == "sync":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww sync <command> [options]")
            print("")
            print("Commands:")
            print("  claude            Sync Claude Code settings")
            print("  bashrc [back|forth]  Sync .bashrc file")
            print("  zprofile [back|forth]  Sync .zprofile file")
            print("  zed [back|forth]     Sync ~/.config/zed/ directory (Zed config)")
            print("  ssh [back|forth]    Sync .ssh directory")
            print("  hermes [back|forth]  Sync ~/.hermes/ <-> $CONFIG_DIR/hermes/")
            print("  openclaw          Sync OpenClaw settings")
            print("  ww [back|forth]   Sync .env to/from $CONFIG_DIR/ww/")
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
                    "  Sync config.yaml, SOUL.md, hooks/, plugins/, agent-hooks/ (forth: ~/.hermes/ -> $CONFIG_DIR, back: reverse)"
                )
                return
            direction = direction or "forth"
            from ww.sync.remote import sync_hermes

            sync_hermes(direction)
        elif subcmd == "openclaw":
            from ww.sync.openclaw import main as m

            m()
        elif subcmd == "ww":
            direction = _pop_subcmd()
            if direction in ("--help", "-h"):
                print("Usage: ww sync ww [back|forth]")
                print("  Sync .env to/from $CONFIG_DIR/ww/")
                return
            direction = direction or "forth"
            from ww.sync.ww import sync_ww_env

            sync_ww_env(direction)
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
            print("  list        List all open Ghostty windows")
            print("  focus <N>   Focus a window by index or title substring")
            print("  close       Close all Ghostty windows")
        elif subcmd == "" or subcmd == "random":
            from ww.ghostty.random_window import main as m

            m()
        elif subcmd == "list":
            from ww.ghostty.list_windows import main as m

            m()
        elif subcmd == "focus":
            from ww.ghostty.focus import main as m

            m()
        elif subcmd == "close":
            from ww.ghostty.close import main as m

            m()
        else:
            print(f"Unknown ghostty command: {subcmd}")
            sys.exit(1)

    elif group == "benchmark":
        from ww.benchmark.gpu_bench import main as m

        m()

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

    elif group == "appearance":
        from ww.display.appearance import main as m

        m()

    elif group == "gen-image":
        from ww.image.gen_image import main as m

        m()

    elif group == "gen-video":
        if len(sys.argv) > 1 and sys.argv[1] == "upload":
            sys.argv.pop(1)  # consume 'upload'
            from ww.gen_video.youtube_upload import main as m

            m()
        elif len(sys.argv) > 1 and sys.argv[1] == "set-privacy":
            sys.argv.pop(1)  # consume 'set-privacy'
            from ww.gen_video.youtube_set_privacy import main as m

            m()
        elif len(sys.argv) > 1 and sys.argv[1] == "server":
            sys.argv.pop(1)  # consume 'server'
            from ww.gen_video.server import main as m

            m()
        else:
            from ww.gen_video.video import main as m

            m()

    elif group == "action":
        from ww.action.action import main as m

        m()

    elif group == "actions":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww actions <command>")
            print()
            print("Commands:")
            print("  check   Check recent workflow runs (default: gh-pages.yml)")
        elif subcmd == "check":
            from ww.actions.check import main as m

            m()
        else:
            print(f"Unknown actions command: {subcmd}")
            sys.exit(1)

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

    elif group == "math":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww math <command>")
            print("")
            print("Commands:")
            print("  tanh      Tanh (Hyperbolic Tangent) reference")
        elif subcmd == "tanh":
            from ww.math.tanh import main as m

            m()
        else:
            print(f"Unknown math command: {subcmd}")
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

    elif group == "hf":
        subcmd = _pop_subcmd()
        if subcmd == "news":
            from ww.hf.hf import cmd_news

            cmd_news()
        elif subcmd == "top30":
            from ww.hf.hf import cmd_top30

            cmd_top30()
        elif subcmd == "push":
            from ww.hf.push import cmd_push

            cmd_push()
        elif subcmd == "pull":
            from ww.hf.push import cmd_pull

            cmd_pull()
        elif subcmd in ("", "--help", "-h"):
            from ww.hf.hf import main as m

            m()
        else:
            # Treat as username for profile lookup
            from ww.hf.hf import cmd_info

            cmd_info(subcmd)

    elif group == "env":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww env <command>")
            print("")
            print("Commands:")
            print("  update    Pick a top Arena model and update MODEL= in .env")
            print("  warp      Install Warp (the Agentic Dev Environment) on Linux")
            print("  ghostty   Install Ghostty terminal on Linux")
            print("  github-desktop   Install GitHub Desktop on macOS and Linux")
        elif subcmd == "update":
            from ww.llm.update_env import main as m

            m()
        elif subcmd == "warp":
            from ww.env.warp import main as m

            m()
        elif subcmd == "ghostty":
            from ww.env.ghostty import main as m

            m()
        elif subcmd == "github-desktop":
            from ww.env.github_desktop import main as m

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

    elif group == "maps":
        from ww.maps.maps import main as m

        m()

    elif group == "hackernews":
        from ww.hackernews.agent import main as m

        m()

    elif group == "headphone":
        subcmd = _pop_subcmd()
        if subcmd.startswith("-"):
            if subcmd in ("--help", "-h"):
                print("Usage: ww headphone [command] [options]")
                print("")
                print("Commands:")
                print(
                    "  test        List audio devices, play test tone, record and playback (default)"
                )
                print("  list        Only list connected audio devices")
                print("")
                print("Options:")
                print("  --output-device N   Specify output device index")
                print("  --input-device N    Specify input device index")
                return
            sys.argv.insert(1, subcmd)  # push back for argparse
            from ww.audio.headphone import main as headphone_main

            headphone_main()
        elif subcmd == "list":
            from ww.audio.headphone import main as headphone_main

            sys.argv.insert(1, "--list-only")
            headphone_main()
        else:
            from ww.audio.headphone import main as headphone_main

            headphone_main()

    elif group == "hermes":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww hermes <command>")
            print("")
            print("Commands:")
            print("  check   Check Hermes agent note plugin health")
            print("")
            print("Examples:")
            print("  ww hermes check")
        elif subcmd == "check":
            from ww.hermes.check import main as m

            m()
        else:
            print(f"Unknown hermes command: {subcmd}")
            sys.exit(1)

    elif group == "whisper":
        if len(sys.argv) > 1 and sys.argv[1] == "refine":
            sys.argv.pop(1)
            from ww.audio.whisper_refine import main as m

            m()
        elif len(sys.argv) > 1 and sys.argv[1] == "organize":
            sys.argv.pop(1)
            from ww.audio.whisper_organize import main as m

            m()
        elif len(sys.argv) > 1 and sys.argv[1] == "diarize":
            sys.argv.pop(1)
            from ww.audio.whisper_diarize import main as m

            m()
        else:
            from ww.audio.whisper_translate import main as m

            m()

    elif group == "transcript":
        from ww.audio.transcript import main as m

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
        if len(sys.argv) > 1 and sys.argv[1] == "rain":
            sys.argv.pop(1)  # consume 'rain' subcmd
            from ww.weather.rain import main as m

            m()
        else:
            from ww.weather.weather import main as m

            m()

    elif group == "rain":
        from ww.weather.rain import main as m

        m()

    elif group == "torch":
        from ww.torch.detect import run

        run()

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

    elif group == "zed":
        from ww.zed.zed_remote import main as m

        m()

    elif group == "projects":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww projects <command>")
            print("")
            print("Commands:")
            print("  count    Count directories in ~/projects")
            print(
                "  init     Clone repos from repos.json into ~/projects (git clone --depth=10)"
            )
            print("  update   Update git repos (default: repos.json config)")
        elif subcmd == "count":
            from ww.projects.projects_count import main as m

            m()
        elif subcmd == "init":
            from ww.projects.projects_init import main as m

            m()
        elif subcmd == "update":
            from ww.git.git_update import main as m

            m()
        else:
            print(f"Unknown projects command: {subcmd}")
            sys.exit(1)

    elif group == "qwen":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww qwen <command>")
            print("")
            print("Commands:")
            print("  vl          Query local Qwen2-VL vision model with an image")
            print("")
            print("Examples:")
            print("  ww qwen vl --image ~/photo.jpg")
            print("  ww qwen vl 'Describe this photo' --image ~/photo.jpg")
        elif subcmd == "vl":
            from ww.qwen.vision import main as m

            m()
        else:
            print(f"Unknown qwen command: {subcmd}")
            sys.exit(1)

    elif group == "inference":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww inference <command>")
            print("")
            print("Commands:")
            print(
                "  test  Detect SGLang vs vLLM backend for a model (default: tencent/hy3-preview)"
            )
        elif subcmd == "test":
            from ww.inference.test import main as m

            m()
        else:
            print(f"Unknown inference command: {subcmd}")
            sys.exit(1)

    elif group == "x":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww x <command>")
            print("")
            print("Commands:")
            print(
                "  post      Generate X/Twitter posts from markdown files in original/"
            )
            print("  unfollow   Smart bulk unfollow on X/Twitter using LLM decisions")
            print("")
            print("Examples:")
            print("  ww x unfollow --count 500")
            print("  ww x unfollow --count 500 --delay 3")
            print("  ww x post --n 5")
        elif subcmd == "unfollow":
            from ww.social.x_bulk_unfollow import main as m

            m()
        elif subcmd == "post":
            from ww.social.x_post import main as m

            m()
        else:
            print(f"Unknown x command: {subcmd}")
            sys.exit(1)

    elif group == "alarm":
        from ww.alarm.alarm import main as m

        m()

    elif group == "cook":
        from ww.cook.cook import main as m

        m()

    elif group == "format":
        from ww.format.format import main as m

        m()

    elif group == "ffmpeg":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww ffmpeg <command>")
            print("")
            print("Commands:")
            print("  m4a     Convert .m4a file(s) to MP3, combining multiple into one")
            print("  merge   Merge two or more audio/video files into one")
            print("")
            print("Examples:")
            print("  ww ffmpeg m4a recording.m4a")
            print("  ww ffmpeg m4a part1.m4a part2.m4a")
            print("  ww ffmpeg merge intro.mp3 main.mp3 outro.mp3")
            print("  ww ffmpeg merge part1.mp4 part2.mp4")
        elif subcmd == "m4a":
            from ww.ffmpeg.m4a import main as m

            m()
        elif subcmd == "merge":
            from ww.ffmpeg.merge import main as m

            m()
        else:
            print(f"Unknown ffmpeg command: {subcmd}")
            sys.exit(1)

    elif group == "gcp-speech":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww gcp-speech <command>")
            print("")
            print("Commands:")
            print("  transcribe   Transcribe audio via Google Cloud Speech-to-Text")
            print("  result       Query the result of a previous transcription job")
            print("")
            print("Examples:")
            print("  ww gcp-speech transcribe ~/Downloads/recording.mp3")
            print(
                "  ww gcp-speech transcribe ~/Downloads/recording-zh.mp3 --lang cmn-Hans-CN"
            )
            print("  ww gcp-speech result <job-id>")
        elif subcmd == "transcribe":
            from ww.gcp_speech.transcribe import main as m

            m()
        elif subcmd == "result":
            from ww.gcp_speech.result import main as m

            m()
        else:
            print(f"Unknown gcp-speech command: {subcmd}")
            sys.exit(1)

    elif group == "runpod":
        from ww.runpod.runpod import main as m

        m()

    elif group == "amd-dev-cloud":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww amd-dev-cloud <command>")
            print("")
            print("Commands:")
            print("  snapshots        List all snapshots")
            print("  delete-snapshot  Delete a snapshot")
            print("  start-train      Create GPU droplet from snapshot for training")
            print("  end-train        Snapshot and destroy a GPU droplet")
        elif subcmd == "snapshots":
            from ww.amd_dev_cloud.snapshots import main as m

            m()
        elif subcmd == "delete-snapshot":
            from ww.amd_dev_cloud.delete_snapshot import main as m

            m()
        elif subcmd == "start-train":
            from ww.amd_dev_cloud.start_train import main as m

            m()
        elif subcmd == "end-train":
            from ww.amd_dev_cloud.end_train import main as m

            m()
        else:
            print(f"Unknown amd-dev-cloud command: {subcmd}")
            sys.exit(1)

    elif group == "vision-model":
        subcmd = _pop_subcmd()
        if subcmd == "" or subcmd in ("--help", "-h"):
            print("Usage: ww vision-model <command>")
            print("")
            print("Commands:")
            print(
                "  test [--model MODEL] [--image PATH]  Test VISION_MODEL via OpenRouter (image + text)"
            )
            print("")
            print("Examples:")
            print("  ww vision-model test")
            print("  ww vision-model test --model openai/gpt-4o-mini")
        elif subcmd == "test":
            from ww.vision_model.test import main as m

            m()
        else:
            print(f"Unknown vision-model command: {subcmd}")
            sys.exit(1)

    else:
        # Suggest similar commands when exact match fails
        all_groups = [
            "action",
            "actions",
            "amd-dev-cloud",
            "benchmark",
            "clash",
            "cloudflare",
            "completion",
            "cook",
            "copilot",
            "format",
            "ffmpeg",
            "gcp-speech",
            "conversation",
            "db",
            "degree",
            "display",
            "env",
            "gen-image",
            "gen-video",
            "math",
            "gif",
            "git",
            "github",
            "ghostty",
            "hackernews",
            "headphone",
            "hermes",
            "hf",
            "host",
            "image",
            "inference",
            "java",
            "latest",
            "linux",
            "llm",
            "macos",
            "marp",
            "md",
            "network",
            "note",
            "openrouter",
            "pdf",
            "proc",
            "projects",
            "qwen",
            "rain",
            "read",
            "runpod",
            "screenshot",
            "screenshot-linux",
            "search",
            "sync",
            "torch",
            "transcript",
            "utils",
            "vision-model",
            "weather",
            "whisper",
            "x",
            "zed",
        ]
        matches = [g for g in all_groups if g.startswith(group)]
        if matches:
            print(f"Unknown command: {group}")
            print(f"Did you mean: {', '.join(matches)}?")
        else:
            print(f"Unknown command: {group}")
        sys.exit(1)


if __name__ == "__main__":
    main()
