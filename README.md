# ww

🌐 **English** | [中文](README-CN.md)

---

A cross-platform CLI toolkit for developer productivity. Covers git workflows, GitHub management, note-taking, screenshot capture, image processing (crop, compress, background removal, EXIF scanning), PDF conversion (Markdown, LaTeX, code-to-PDF), web search (multi-engine), network diagnostics (WiFi scanning, IP/port scanning, network topology), system monitoring (macOS, Linux), process management, Clash proxy control, Java/Maven analysis, RAG document indexing, LLM model comparison, OpenRouter account management, GitHub Actions triggering, speech transcription (Whisper), presentation generation (Marp), Cloudflare analytics, and more — many commands enhanced with LLM-powered intelligence.

## Installation

```bash
pip install -e .
```

## Usage

```bash
ww <group> [command] [options]
```

## Commands

### Note

| Command | Description |
|---------|-------------|
| `ww note` | Create a new note with git integration |
| `ww note log` | Create a new log entry |
| `ww note log-file` | Create a log entry from a file |
| `ww note obfuscate <file>` | Obfuscate sensitive data in a file |

### Screenshot

| Command | Description |
|---------|-------------|
| `ww screenshot [DELAY]` | Take a screenshot (macOS, `--dir`) |
| `ww screenshot-linux` | Take a screenshot (Linux, saves to SCREENSHOT_DIR, default: assets/screenshots) |
| `ww screenshot note` | Create a note from latest screenshot(s) (`-n`, `--prompt`) |
| `ww screenshot interact-note` | Interactively capture screenshots and create a note |

### Git

| Command | Description |
|---------|-------------|
| `ww git amend-push` | Amend last commit and force push |
| `ww git classify` | Classify git commits |
| `ww git find-commit` | Find a git commit |
| `ww git delete-commit` | Delete a git commit |
| `ww git diff-tree` | Show git diff tree |
| `ww git check-filenames` | Check git filenames |
| `ww git force-push` | Force push to remote |
| `ww git show` | Show git commit details |
| `ww git squash` | Squash git commits |
| `ww git gca` | AI commit, no push (gemini-flash) |
| `ww git gpa` | AI commit with pull+push (gemini-flash) |

### GitHub

| Command | Description |
|---------|-------------|
| `ww github info` | Account info, plan, rate limits |
| `ww github repos` | List your repos (recently pushed) |
| `ww github starred` | List starred repos |
| `ww github followers` | List followers |
| `ww github following` | List following |
| `ww github notifications` | List unread notifications |
| `ww github rate` | Show rate limit details |
| `ww github gitmessageai` | Generate AI commit message and commit |

### Image

| Command | Description |
|---------|-------------|
| `ww image avatar` | Process avatar image |
| `ww image crop` | Crop an image |
| `ww image remove-bg` | Remove image background |
| `ww image compress` | Compress images |
| `ww image photo-compress` | Compress photos |
| `ww image exif` | Scan images for EXIF GPS location data |
| `ww image whatsapp` | Download images from WhatsApp Web via Safari |

### GIF

| Command | Description |
|---------|-------------|
| `ww gif` | Create GIF from images |

### PDF

| Command | Description |
|---------|-------------|
| `ww pdf markdown-pdf` | Convert a markdown file to PDF |
| `ww pdf pdf-pipeline` | Batch convert markdown posts to PDFs |
| `ww pdf update-pdf` | Convert markdown files changed in last commit |
| `ww pdf code2pdf` | Convert code files in a directory to PDF |
| `ww pdf scale-pdf` | Scale a PDF using pdfjam |
| `ww pdf test-latex` | Test LaTeX/pandoc PDF generation |
| `ww pdf md2png` | Convert markdown to PNG via HTML+PDF (Chrome) |

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

### macOS

| Command | Description |
|---------|-------------|
| `ww macos find-large-dirs` | Find largest directories on disk |
| `ww macos system-info` | Show system information |
| `ww macos install` | Run macOS install tasks |
| `ww macos list-fonts` | List installed fonts |
| `ww macos list-disks` | List portable disks |
| `ww macos open-terminal` | Open a new terminal window |
| `ww macos toast` | Show macOS notification toast |
| `ww macos charge-watch` | Alert when charger is plugged in but not charging |
| `ww macos process` | Analyze running processes and suggest what to kill |
| `ww macos settings-proxy` | Set system proxy (HTTP/HTTPS 7890, SOCKS 7891) with bypass list |
| `ww macos apps` | Audit installed apps by size and age (`--no-llm`, `--json`) |
| `ww macos dock` | List apps currently pinned to the Dock (`--json`) |

### Linux

| Command | Description |
|---------|-------------|
| `ww linux gpu` | Show GPU and CUDA details |
| `ww linux system` | Comprehensive system overview |
| `ww linux disk` | Show disk usage |
| `ww linux battery` | Show battery status |
| `ww linux proxy-setup` | Interactively configure APT proxy |
| `ww linux wol` | Send a Wake-on-LAN packet |
| `ww linux terminal` | Open a fullscreen terminal |

### Network

| Command | Description |
|---------|-------------|
| `ww network get-wifi-list` | Get list of WiFi networks |
| `ww network save-wifi-list` | Save WiFi network list |
| `ww network hack-wifi` | WiFi password utilities |
| `ww network wifi-gen-password` | Generate WiFi password |
| `ww network ip-scan` | Scan IP addresses on network |
| `ww network port-scan` | Scan open ports |
| `ww network wifi-scan` | Scan for WiFi networks |
| `ww network wifi-util` | WiFi utility tools |
| `ww network network-plot` | Plot network topology |
| `ww network discover` | Discover devices on local network (ARP + OUI + port probe) |

### Process

| Command | Description |
|---------|-------------|
| `ww proc kill-pattern` | Kill processes matching a pattern |
| `ww proc kill-port` | Kill process on a given port |
| `ww proc kill-jekyll` | Kill Jekyll server |
| `ww proc kill-proxy` | Kill macOS proxy |

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

### Java

| Command | Description |
|---------|-------------|
| `ww java mvn` | Maven project utilities |
| `ww java analyze-deps` | Analyze Java dependencies |
| `ww java analyze-packages` | Analyze Java packages |
| `ww java analyze-poms` | Analyze Maven POM files |
| `ww java analyze-spring` | Analyze Spring Boot project |
| `ww java clean-log` | Clean Java log files |

### Copilot

| Command | Description |
|---------|-------------|
| `ww copilot auth` | Authenticate via GitHub OAuth device flow |
| `ww copilot models` | List available Copilot models |
| `ww copilot chat` | Chat with a Copilot model |

### Sync

| Command | Description |
|---------|-------------|
| `ww sync claude` | Sync Claude Code settings (sanitized) |
| `ww sync bashrc [back\|forth]` | Sync .bashrc file |
| `ww sync zprofile [back\|forth]` | Sync .zprofile file |
| `ww sync zed [back\|forth]` | Sync ~/.config/zed/ directory (Zed config) |
| `ww sync ssh [back\|forth]` | Sync .ssh directory |
| `ww sync hermes [back\|forth]` | Sync config.yaml, SOUL.md, hooks/, plugins/, agent-hooks/ |

### Update

| Command | Description |
|---------|-------------|
| `ww update [name...]` | Update git repos (default: updated_repos) |

### Latest

| Command | Description |
|---------|-------------|
| `ww latest notes [N]` | Show filename and title of latest N notes (default 10) |

### Read (RAG)

| Command | Description |
|---------|-------------|
| `ww read index <dir>` | Index documents in a directory (BGE + FAISS) |
| `ww read query <question>` | Ask a question over indexed documents |
| `ww read query <q> --top-k N` | Use N retrieved chunks (default 5) |

### LLM

| Command | Description |
|---------|-------------|
| `ww llm compare` | Compare 6 models on clipboard prompt, judge winner |

### OpenRouter

| Command | Description |
|---------|-------------|
| `ww openrouter info` | Account summary: credits, usage, key details |
| `ww openrouter credits` | Show credits balance |
| `ww openrouter activity` | Past week spend, requests, tokens (`--days N`) |
| `ww openrouter models` | List available models |

### Env

| Command | Description |
|---------|-------------|
| `ww env update` | Pick a top Arena model and update MODEL= in .env |

### Display

| Command | Description |
|---------|-------------|
| `ww display <dark\|light\|auto\|show>` | Switch macOS appearance or show current |

### Gen-image

| Command | Description |
|---------|-------------|
| `ww gen-image` | Generate image from clipboard text (Imagen 3) |

### Action

| Command | Description |
|---------|-------------|
| `ww action <workflow.yml>` | Trigger a GitHub Actions workflow via gh CLI |

### Degree

| Command | Description |
|---------|-------------|
| `ww degree` | AI-categorize recent self-study notices |
| `ww degree practical` | Filter notices about practical exams / scores |
| `ww degree list` | Raw scraped list (no AI) |
| `ww degree --pages N` | Fetch N list pages (1-11, default 1) |

### Marp

| Command | Description |
|---------|-------------|
| `ww marp <file.md>` | Watch a markdown file and regenerate PDF via marp |

### Whisper

| Command | Description |
|---------|-------------|
| `ww whisper <file.mp4>` | Transcribe via whisper (Chinese, large, CUDA) |
| `ww whisper refine <file.txt>` | Refine transcription to .md via OpenRouter |

### Host

| Command | Description |
|---------|-------------|
| `ww host` | Show all hosts |
| `ww host local` | Local machine |
| `ww host workstation` | Workstation (RTX 4070) |
| `ww host dmit` | DMIT server |

### Cloudflare

| Command | Description |
|---------|-------------|
| `ww cloudflare monthly-visit` | Monthly page views & visits from Web Analytics |
| `ww cloudflare zones` | List Cloudflare zones |
| `ww cloudflare datasets` | List Web Analytics datasets |
| `ww cloudflare schema` | Inspect GraphQL Account schema |
| `ww cloudflare pdf <file>` | Parse Cloudflare Analytics PDF export |

### Ghostty

| Command | Description |
|---------|-------------|
| `ww ghostty` | Open a Ghostty window at a random position |
| `ww ghostty close` | Close all Ghostty windows |

### Clash

| Command | Description |
|---------|-------------|
| `ww clash select-provider` | Select best proxy provider |
| `ww clash speed` | Run speed test and select best proxy |
| `ww clash run` | Full clash management with iterations |
| `ww clash top-proxies` | Print top 5 fastest proxies (single-URL) |
| `ww clash top-proxies-multi` | Print top 10 fastest proxies (multi-URL) |
| `ww clash speed-tiktok` | Run speedtest + TikTok load time |
| `ww clash query-dns [host]` | Test AliDNS DoH resolution |
| `ww clash gnome-proxy <set\|unset>` | Toggle GNOME proxy (Linux) |
| `ww clash macos-proxy <set\|unset>` | Toggle macOS proxy (networksetup) |
| `ww clash wifi <on\|off>` | Toggle macOS Wi-Fi |

## Requirements

- Python >= 3.8
- See `pyproject.toml` for full dependency list
