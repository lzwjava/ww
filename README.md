# ww

🌐 **English** | [中文](README-CN.md)

---

A cross-platform CLI toolkit for developer productivity. Covers git workflows, GitHub management, note-taking, screenshot capture, image processing (crop, compress, background removal, EXIF scanning, face-aware crop), PDF conversion (Markdown, LaTeX, code-to-PDF), web search (multi-engine), network diagnostics (WiFi scanning, IP/port scanning, network topology, speed tests), system monitoring (macOS, Linux), process management, Clash proxy control, Java/Maven analysis, RAG document indexing, LLM model comparison, OpenRouter account management, GitHub Actions triggering, Whisper/GCP speech transcription, conversation-to-audio/video generation, Google Maps queries, RunPod cloud GPU management, HF model pull/push, news summarization, HN reader agent, and more — many commands enhanced with LLM-powered intelligence.

## Installation

**With [uv](https://docs.astral.sh/uv/) (recommended):**

```bash
uv sync
```

**With pip:**

```bash
pip install -e .
```

After install, run `ww` directly — no activation needed with `uv run ww ...`.

Requires a `.env` file with `OPENROUTER_API_KEY` (and `MODEL`, `VISION_MODEL`) for LLM-powered commands. See [Env](#env).

## Usage

```bash
ww <group> [command] [options]
```

Run `ww help` for the full command list, or `ww help <file_path>` for LLM-powered help about a specific module.

## Command Groups

[Help](#help) · [Action & Actions](#action) · [Alarm](#macos) · [AMD Dev Cloud](#amd-dev-cloud) · [Appearance](#appearance) · [Benchmark](#benchmark) · [Clash](#clash) · [Cloudflare](#cloudflare) · [Completion](#completion) · [Cook](#cook) · [Copilot](#copilot) · [Conversation](#conversation) · [DB](#db-command-history) · [Degree](#degree) · [Display](#display) · [Env](#env) · [FFmpeg](#ffmpeg) · [Format](#format) · [GCP Speech](#gcp-speech) · [Gen-image](#gen-image) · [Gen-video](#gen-video) · [GIF](#gif) · [Git](#git) · [GitHub](#github) · [Ghostty](#ghostty) · [HackerNews](#hackernews) · [Headphone](#headphone) · [Hermes](#hermes) · [Host](#host) · [HuggingFace](#huggingface) · [Image](#image) · [Inference](#inference) · [Java](#java) · [Keyboard](#keyboard) · [Latest](#latest) · [Linux](#linux) · [LLM](#llm) · [macOS](#macos) · [Maps](#maps) · [Markdown](#markdown) · [Marp](#marp) · [Math](#math) · [Memory](#memory) · [Monitor](#monitor) · [Network](#network) · [News](#news) · [Note](#note) · [OpenRouter](#openrouter) · [PDF](#pdf) · [Pi](#pi) · [Process](#process) · [Projects](#projects) · [Qwen](#qwen-vision) · [Read (RAG)](#read-rag) · [RunPod](#runpod) · [Screenshot](#screenshot) · [Search](#search) · [SGLang](#sglang) · [Sync](#sync) · [Torch](#torch) · [Transcript](#transcript) · [Utils](#utils) · [Vision Model](#vision-model) · [Weather & Rain](#weather) · [Whisper](#whisper) · [X (Twitter)](#x-twitter) · [Zed](#zed)

---

### Help

| Command | Description |
|---------|-------------|
| `ww help` | Show the full command list |
| `ww help <file_path>` | LLM-powered help for a specific module file |

### Action

| Command | Description |
|---------|-------------|
| `ww action [workflow.yml]` | Trigger a GitHub Actions workflow (default: gh-pages.yml) |
| `ww actions check [--repo R] [--count N]` | Check recent workflow runs (default: gh-pages.yml) |

### AMD Dev Cloud

| Command | Description |
|---------|-------------|
| `ww amd-dev-cloud snapshots` | List snapshots (requires `AMD_DEV_CLOUD_API_KEY`) |
| `ww amd-dev-cloud start-train` | Create GPU droplet from snapshot for training |
| `ww amd-dev-cloud end-train` | Snapshot and destroy a GPU droplet |
| `ww amd-dev-cloud delete-snapshot` | Delete a snapshot |

### Appearance

| Command | Description |
|---------|-------------|
| `ww appearance` | Manage display appearance (dark/light/auto/show) |

### Benchmark

| Command | Description |
|---------|-------------|
| `ww benchmark` | Run GPU benchmark locally |
| `ww benchmark --ssh HOST:PORT` | Upload script and run on a remote server |
| `ww benchmark --key PATH` | SSH key (default: `~/.ssh/id_ed25519`) |

### Clash

| Command | Description |
|---------|-------------|
| `ww clash query-dns [host]` | Test AliDNS DoH resolution |
| `ww clash gnome-proxy <set\|unset>` | Toggle GNOME proxy (Linux) |
| `ww clash macos-proxy <set\|unset>` | Toggle macOS proxy (networksetup) |
| `ww clash run` | Full clash management with iterations |
| `ww clash select-provider` | Select best proxy provider |
| `ww clash speed` | Run speed test and select best proxy |
| `ww clash speed-tiktok` | Run speedtest + TikTok load time |
| `ww clash top-proxies` | Print top 5 fastest proxies (single-URL) |
| `ww clash top-proxies-multi` | Print top 10 fastest proxies (multi-URL) |
| `ww clash wifi <on\|off>` | Toggle macOS Wi-Fi |

### Cloudflare

| Command | Description |
|---------|-------------|
| `ww cloudflare datasets` | List Web Analytics datasets |
| `ww cloudflare monthly-visit` | Monthly page views & visits from Web Analytics |
| `ww cloudflare pdf <file>` | Parse Cloudflare Analytics PDF export |
| `ww cloudflare schema` | Inspect GraphQL Account schema |
| `ww cloudflare zones` | List Cloudflare zones |

### Completion

| Command | Description |
|---------|-------------|
| `ww completion install` | Install zsh tab completion |
| `ww completion script` | Print the completion script |

### Cook

| Command | Description |
|---------|-------------|
| `ww cook <minutes>` | Set a cooking timer (notifies every 2 min after expiry) |
| `ww cook clear` | Clear the cooking timer and stop notifications |

### Copilot

| Command | Description |
|---------|-------------|
| `ww copilot auth` | Authenticate via GitHub OAuth device flow |
| `ww copilot chat` | Chat with a Copilot model |
| `ww copilot models` | List available Copilot models |

### Conversation

| Command | Description |
|---------|-------------|
| `ww conversation json <n>` | Capture conversation JSON from stdin/clipboard |
| `ww conversation generate <file>` | Generate audio from conversation JSON (GCloud TTS) |
| `ww conversation notes` | Convert conversation JSON files to markdown notes |
| `ww conversation to-video <file>` | Create video from audio file with cover image |
| `ww conversation to-image <file>` | Resize and crop image to 854×480 |

### DB (Command History)

| Command | Description |
|---------|-------------|
| `ww db errors` | Show recent error commands (`--limit N`) |
| `ww db recent` | Show recent commands (`--limit N`) |
| `ww db search <pattern>` | Search command history |
| `ww db stats` | Show overall usage statistics |
| `ww db top` | Show most frequently used commands (`--limit N`) |

### Degree (GDUFS Self-Study Exam)

| Command | Description |
|---------|-------------|
| `ww degree` | AI-categorize recent self-study notices |
| `ww degree list` | Raw scraped list (no AI) |
| `ww degree practical` | Filter notices about practical exams / scores |
| `ww degree --pages N` | Fetch N list pages (1–11, default 1) |
| `ww degree --months N` | Only articles from last N months (default 3, 0=all) |

### Display

| Command | Description |
|---------|-------------|
| `ww display <dark\|light\|auto\|show>` | Switch macOS appearance or show current |

### Env

| Command | Description |
|---------|-------------|
| `ww env update` | Pick a top Arena model and update `MODEL=` in `.env` |

### FFmpeg

| Command | Description |
|---------|-------------|
| `ww ffmpeg m4a <file1.m4a> [file2.m4a ...]` | Convert `.m4a` file(s) to MP3, combining into one |
| `ww ffmpeg merge <file1> <file2> [... <fileN>]` | Merge two or more audio/video files into one |

### Format

| Command | Description |
|---------|-------------|
| `ww format <file.json>` | Pretty-print a JSON file in-place |

### GCP Speech

| Command | Description |
|---------|-------------|
| `ww gcp-speech transcribe <file> [--lang LANG]` | Transcribe audio via Google Cloud Speech-to-Text |
| `ww gcp-speech result <job-id> [--wait]` | Query the result of a previous transcription job |

### Gen-image

| Command | Description |
|---------|-------------|
| `ww gen-image` | Generate image from clipboard text (Imagen 3) |

### Gen-video

| Command | Description |
|---------|-------------|
| `ww gen-video <file>` | Generate a 15s short-form video (9:16) from a markdown note — 5 slides × 3s, centered images, top/bottom text, no audio |
| `ww gen-video <file> --upload` | Generate + upload to YouTube |
| `ww gen-video upload` | Upload a video to YouTube via YouTube Data API v3 |
| `ww gen-video set-privacy` | Change privacy of an uploaded YouTube video |
| `ww gen-video server` | Start the gen-video API server (FastAPI) |
| `ww gen-video generate` | Read pasteboard content and send to gen-video server |
| `ww gen-video query <id>` | Query the status of a video generation job |

### GIF

| Command | Description |
|---------|-------------|
| `ww gif` | Create GIF from images |

### Git

| Command | Description |
|---------|-------------|
| `ww git amend-push` | Amend last commit and force push |
| `ww git check-filenames` | Check git filenames |
| `ww git classify` | Classify git commits |
| `ww git delete-commit` | Delete a git commit |
| `ww git diff-tree` | Show git diff tree |
| `ww git find-commit` | Find a git commit |
| `ww git force-push` | Force push to remote |
| `ww git gca` | AI commit, no push (gemini-flash) |
| `ww git gpa` | AI commit with pull + push (gemini-flash) |
| `ww git show` | Show git commit details |
| `ww git squash` | Squash git commits |

### GitHub

| Command | Description |
|---------|-------------|
| `ww github followers` | List followers |
| `ww github following` | List following |
| `ww github gitmessageai` | Generate AI commit message and commit |
| `ww github info` | Account info, plan, rate limits |
| `ww github interests <u1> <u2>` | Compare GitHub interests between two users |
| `ww github notifications` | List unread notifications |
| `ww github profile <user>` | Detailed profile report for any GitHub user |
| `ww github rate` | Show rate limit details |
| `ww github repos` | List your repos (recently pushed) |
| `ww github starred` | List starred repos |

### Ghostty

| Command | Description |
|---------|-------------|
| `ww ghostty` | Open a Ghostty window at a random position |
| `ww ghostty close` | Close all Ghostty windows |
| `ww ghostty focus <N>` | Focus a Ghostty window by index or title |
| `ww ghostty list` | List all open Ghostty windows |

### HackerNews

| Command | Description |
|---------|-------------|
| `ww hackernews [--count N] [topic]` | AI-agent reads HN (LangGraph, default 10) |

### Headphone

| Command | Description |
|---------|-------------|
| `ww headphone` | Test audio devices: play tone, record and playback |
| `ww headphone list` | List connected audio devices |

### Hermes

| Command | Description |
|---------|-------------|
| `ww hermes check` | Check Hermes agent note plugin health |

### Host

| Command | Description |
|---------|-------------|
| `ww host` | Show all hosts |
| `ww host dmit` | DMIT server |
| `ww host local` | Local machine |
| `ww host workstation` | Workstation (RTX 4070) |

### HuggingFace

| Command | Description |
|---------|-------------|
| `ww hf [username]` | Show HuggingFace profile (default: lzwjava) |
| `ww hf news` | Trending models, datasets, and spaces (`--limit N`, `--json`) |
| `ww hf pull [repo] [path]` | Download a HF model repo to local dir (`--revision branch`) |
| `ww hf push [path]` | Upload local dir to HF model repo (`--repo id`, `--message`) |
| `ww hf top30` | Top 30 most-followed HF users |

### Image

| Command | Description |
|---------|-------------|
| `ww image avatar` | Process avatar image |
| `ww image compress` | Compress images |
| `ww image crop` | Crop an image |
| `ww image exif` | Scan images for EXIF GPS location data |
| `ww image face` | Face-aware crop to resume/visa/ID sizes |
| `ww image photo-compress` | Compress photos |
| `ww image remove-bg` | Remove image background |
| `ww image whatsapp` | Download images from WhatsApp Web via Safari |

### Inference

| Command | Description |
|---------|-------------|
| `ww inference test [--model M]` | Detect SGLang vs vLLM backend for a model (default: tencent/hy3-preview) |

### Java

| Command | Description |
|---------|-------------|
| `ww java analyze-deps` | Analyze Java dependencies |
| `ww java analyze-packages` | Analyze Java packages |
| `ww java analyze-poms` | Analyze Maven POM files |
| `ww java analyze-spring` | Analyze Spring Boot project |
| `ww java clean-log` | Clean Java log files |
| `ww java mvn` | Maven project utilities |

### Keyboard

| Command | Description |
|---------|-------------|
| `ww keyboard capslock-ctrl` | Toggle Caps Lock ↔ Left Ctrl swap (Ubuntu/GNOME) |
| `ww env warp` | Install Warp (the Agentic Dev Environment) on Linux |
| `ww env ghostty` | Install Ghostty terminal on Linux |
| `ww env github-desktop` | Install GitHub Desktop on macOS and Linux |
| `ww env zed` | Install Zed editor on macOS and Linux |

### Latest

| Command | Description |
|---------|-------------|
| `ww latest notes [N]` | Show filename and title of latest N notes (default 10) |

### Linux

| Command | Description |
|---------|-------------|
| `ww linux battery` | Show battery status |
| `ww linux disk` | Show disk usage |
| `ww linux gpu` | Show GPU and CUDA details |
| `ww linux proxy-setup` | Interactively configure APT proxy |
| `ww linux screen-lock` | Control idle screen lock delay (Ubuntu/GNOME) |
| `ww linux switch-keys` | Swap Caps Lock and Left Control keys |
| `ww linux system` | Comprehensive system overview |
| `ww linux terminal` | Open a fullscreen terminal |
| `ww linux wol` | Send a Wake-on-LAN packet |

### LLM

| Command | Description |
|---------|-------------|
| `ww llm compare` | Compare 6 models on clipboard prompt, judge winner |

### macOS

| Command | Description |
|---------|-------------|
| `ww alarm [clear\|list\|<min>]` | Clock alarms: set, list, or remove all |
| `ww macos apps` | Audit installed apps by size and age (`--no-llm`, `--json`) |
| `ww macos charge-watch` | Alert when charger is plugged in but not charging |
| `ww macos dock` | List apps currently pinned to the Dock (`--json`) |
| `ww macos find-large-dirs` | Find largest directories on disk |
| `ww macos install` | Run macOS install tasks |
| `ww macos list-disks` | List portable disks |
| `ww macos list-fonts` | List installed fonts |
| `ww macos open-terminal` | Open a new terminal window |
| `ww macos process` | Analyze running processes and suggest what to kill |
| `ww macos settings-proxy` | Set system proxy (HTTP/HTTPS 7890, SOCKS 7891) with bypass list |
| `ww macos system-info` | Show system information |
| `ww macos toast` | Show macOS notification toast |

### Maps

| Command | Description |
|---------|-------------|
| `ww maps directions <from> <to> [--mode M]` | Route directions |
| `ww maps elevation <lat,lng>` | Elevation for a location |
| `ww maps geocode <address>` | Address to lat/lng |
| `ww maps home [lat,lng]` | Distance/time to home |
| `ww maps ip <address>` | Geolocate an IP |
| `ww maps location --paste [origin]` | Trip report from clipboard URL |
| `ww maps nearby <lat,lng> [radius] [type]` | Nearby places |
| `ww maps office [lat,lng]` | Distance/time to OneLink office |
| `ww maps place <place_id>` | Place details |
| `ww maps reverse <lat,lng>` | Lat/lng to address |
| `ww maps search <query> [--near L] [--radius M]` | Places text search |
| `ww maps test` | Test all Google Maps APIs |
| `ww maps timezone <lat,lng>` | Timezone for a location |

### Markdown

| Command | Description |
|---------|-------------|
| `ww md md2img` | Convert markdown to JPG/PNG via HTML screenshot (Playwright) |

### Marp

| Command | Description |
|---------|-------------|
| `ww marp <file.md>` | Watch a markdown file and regenerate PDF via marp |

### Math

| Command | Description |
|---------|-------------|
| `ww math tanh [x1 x2 ...]` | Tanh (hyperbolic tangent) reference table |
| `ww math tanh --plot` | Generate and open tanh figure |
| `ww math tanh --values` | Tanh value table |
| `ww math tanh --all` | Tanh comprehensive reference |

### Memory

| Command | Description |
|---------|-------------|
| `ww memory <host>` | Remote memory chip diagnostics (SPD, usage, health) |

### Monitor

| Command | Description |
|---------|-------------|
| `ww monitor huggingface` | Check top 10 trending HF models, alert on change |
| `ww monitor huggingface --now` | Force alert even if unchanged |

### Network

| Command | Description |
|---------|-------------|
| `ww network discover` | Discover devices on local network |
| `ww network get-wifi-list` | Get list of WiFi networks |
| `ww network hack-wifi` | WiFi password utilities |
| `ww network ip-scan` | Scan IP addresses on network |
| `ww network network-plot` | Plot network topology |
| `ww network physical-speed` | Estimate speed via EM Doppler shift |
| `ww network port-scan` | Scan open ports |
| `ww network save-wifi-list` | Save WiFi network list |
| `ww network speed` | Internet speed test (ping, jitter, bandwidth) |
| `ww network wifi-gen-password` | Generate WiFi password |
| `ww network wifi-scan` | Scan for WiFi networks |
| `ww network wifi-scan-best` | Scan WiFi and recommend best signal |
| `ww network wifi-util` | WiFi utility tools |

### News

| Command | Description |
|---------|-------------|
| `ww news nytimes [--count N]` | Summarize NYTimes Chinese articles (default: 10) |
| `ww news finance [query]` | Search and summarize finance news (default: 10) |

### Note

| Command | Description |
|---------|-------------|
| `ww note` | Quick: clipboard → queue (fast) |
| `ww note --sync` | Full pipeline: create, fix, commit, push |
| `ww note --private` | Save to private-notes dir, skip git push |
| `ww note --code` | LLM-wrap code in clipboard, then queue |
| `ww note process` | Drain queue: create notes, commit, push |
| `ww note status` | Show queue status |
| `ww note clear` | Clear done/failed entries from queue |
| `ww note watch` | Auto-process queue when new notes arrive |
| `ww note log` | Quick: clipboard → log queue (fast) |
| `ww note html` | Quick: clipboard → Jekyll HTML note (visual) |
| `ww note obfuscate <file>` | Obfuscate sensitive data in a file |

### OpenRouter

| Command | Description |
|---------|-------------|
| `ww openrouter activity` | Past week spend, requests, tokens (`--days N`) |
| `ww openrouter credits` | Show credits balance |
| `ww openrouter info` | Account summary: credits, usage, key details |
| `ww openrouter models` | List available models |

### PDF

| Command | Description |
|---------|-------------|
| `ww pdf code2pdf` | Convert code files in a directory to PDF |
| `ww pdf markdown-pdf` | Convert a markdown file to PDF |
| `ww pdf md2png` | Convert markdown to PNG via HTML+PDF (Chrome) |
| `ww pdf pdf-pipeline` | Batch convert markdown posts to PDFs |
| `ww pdf scale-pdf` | Scale a PDF using pdfjam |
| `ww pdf test-latex` | Test LaTeX/pandoc PDF generation |
| `ww pdf update-pdf` | Convert markdown files changed in last commit |

### Pi

| Command | Description |
|---------|-------------|
| `ww pi set-model <provider>/<model>` | Set pi agent default model |
| `ww pi show-model` | Show pi agent default model |

### Process

| Command | Description |
|---------|-------------|
| `ww proc kill-jekyll` | Kill Jekyll server |
| `ww proc kill-pattern` | Kill processes matching a pattern |
| `ww proc kill-port` | Kill process on a given port |
| `ww proc kill-proxy` | Kill macOS proxy |

### Projects

| Command | Description |
|---------|-------------|
| `ww projects count` | Count directories in ~/projects |
| `ww projects update [name\|@cat...]` | Update git repos (default: repos.json) |

### Qwen (Vision)

| Command | Description |
|---------|-------------|
| `ww qwen vl [--image file] [prompt]` | Query local Qwen2-VL vision model |

### Read (RAG)

| Command | Description |
|---------|-------------|
| `ww read index <dir>` | Index documents in a directory (BGE + FAISS) |
| `ww read query <question>` | Ask a question over indexed documents |
| `ww read query <q> --top-k N` | Use N retrieved chunks (default 5) |

### RunPod

| Command | Description |
|---------|-------------|
| `ww runpod start <gpu> [name]` | Create and start a pod (rtx4000ada, h200, a100, ...) |
| `ww runpod list` | List all pods |
| `ww runpod ssh <pod_id>` | SSH into a pod |
| `ww runpod stop <pod_id>` | Stop a pod |
| `ww runpod delete <pod_id>` | Delete a pod |
| `ww runpod gpus` | List available GPU types |
| `ww runpod send <file>` | Send a file (one-time code) |
| `ww runpod receive <code>` | Receive a file via code |
| `ww runpod user` | Account info |
| `ww runpod billing` | Billing history |
| `ww runpod raw <args...>` | Pass raw args to runpodctl |

### Screenshot

| Command | Description |
|---------|-------------|
| `ww screenshot [DELAY]` | Take a screenshot (macOS, `--dir`) |
| `ww screenshot-linux` | Take a screenshot (Linux; `--no-save` to clipboard, `--area 1-4` for quadrant) |
| `ww screenshot note [--skip-analysis]` | Create a note from latest screenshot(s) |
| `ww screenshot interact-note [--skip-analysis]` | Interactively capture screenshots and create a note |

### Search

| Command | Description |
|---------|-------------|
| `ww search` | Web search (multi-engine) |
| `ww search bing` | Search with Bing |
| `ww search code` | Search code |
| `ww search ddg` | Search with DuckDuckGo |
| `ww search ecosia` | Search with Ecosia |
| `ww search filename` | Search by filename |
| `ww search startpage` | Search with StartPage |
| `ww search tavily` | Search with Tavily API |
| `ww search web --json` | JSON output for LLM tool use |

### SGLang

| Command | Description |
|---------|-------------|
| `ww sglang test [--port P]` | Test a local SGLang server with different input lengths (TTFT, tok/s, response check; default: http://localhost:30010) |

### Sync

| Command | Description |
|---------|-------------|
| `ww sync bashrc [back\|forth]` | Sync `.bashrc` file |
| `ww sync claude` | Sync Claude Code settings (sanitized) |
| `ww sync hermes [back\|forth]` | Sync config.yaml, SOUL.md, hooks/, plugins/, agent-hooks/ |
| `ww sync ssh [back\|forth]` | Sync `.ssh` directory |
| `ww sync ww [back\|forth]` | Sync `.env` to/from `$CONFIG_DIR/ww/` |
| `ww sync zed [back\|forth]` | Sync `~/.config/zed/` directory (Zed config) |
| `ww sync zprofile [back\|forth]` | Sync `.zprofile` file |

### Torch

| Command | Description |
|---------|-------------|
| `ww torch` | Find all Pythons and check which have PyTorch |

### Transcript

| Command | Description |
|---------|-------------|
| `ww transcript <file.json> [-o out.md]` | Extract transcript from Google Cloud STT JSON to markdown |

### Utils

| Command | Description |
|---------|-------------|
| `ww utils base64` | Encode/decode base64 |
| `ww utils ccr` | CCR utility |
| `ww utils clean-zip` | Clean zip files |
| `ww utils decode-jwt` | Decode a JWT token |
| `ww utils py2txt` | Convert Python files to text |
| `ww utils request-proxy` | Make HTTP request via proxy |
| `ww utils smart-unzip` | Smart unzip archives |
| `ww utils unzip` | Unzip an archive |

### Vision Model

| Command | Description |
|---------|-------------|
| `ww vision-model test [--model MODEL]` | Test `VISION_MODEL` via OpenRouter (image + text) |

### Weather

| Command | Description |
|---------|-------------|
| `ww weather` | Today's weather (auto-detect location) |
| `ww weather N` | Today + next N days (1–3) |
| `ww weather <city>` | Weather for a city |
| `ww weather N <city>` | N days for a city |
| `ww weather --detail` | With network/location details |
| `ww weather --json` | JSON output |
| `ww weather --oneline` | One-line summary |
| `ww rain [--seconds 5]` | Record video, analyze rain intensity (in-car) |

### Whisper

| Command | Description |
|---------|-------------|
| `ww whisper <file.mp4>` | Transcribe via whisper (Chinese, large, CUDA) |
| `ww whisper <file> --low-memory` | Low-VRAM transcription (faster-whisper: fp16 ~3.2 GB / int8 ~1.1 GB for large-v3) |
| `ww whisper diarize <file>` | Transcribe with speaker labels (whisperx + pyannote) |
| `ww whisper organize <file.txt>` | Lightly clean: fix grammar, remove noise, third-person narration |
| `ww whisper refine <file.txt>` | Refine transcription to `.md` via OpenRouter |

### X (Twitter)

| Command | Description |
|---------|-------------|
| `ww x post --n 5` | Generate X posts from markdown files in `original/` |
| `ww x unfollow --count 500` | Smart bulk unfollow via LLM |
| `ww x unfollow --count 500 --delay 3` | Adjust delay between unfollows |

### Zed

| Command | Description |
|---------|-------------|
| `ww zed [path]` | Open Zed connected to remote workstation via SSH |

## Requirements

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- `.env` with `OPENROUTER_API_KEY` (and optionally `MODEL`, `VISION_MODEL`) for LLM features
- See `pyproject.toml` for the full dependency list
