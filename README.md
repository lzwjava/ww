# ww

A cross-platform CLI toolkit for developer productivity — git workflows, note management, image/PDF processing, web search, and system utilities, with LLM-powered helpers.

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
| `ww note obfuscate <file>` | Obfuscate sensitive data in a file |

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
| `ww github gitmessageai` | Generate AI commit message and commit |

### Image

| Command | Description |
|---------|-------------|
| `ww image avatar` | Process avatar image |
| `ww image crop` | Crop an image |
| `ww image remove-bg` | Remove image background |
| `ww image screenshot` | Take a screenshot (macOS) |
| `ww image screenshot-linux` | Take a screenshot (Linux) |
| `ww image compress` | Compress images |
| `ww image photo-compress` | Compress photos |

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
| `ww sync ssh [back\|forth]` | Sync .ssh directory |

## Requirements

- Python >= 3.8
- See `pyproject.toml` for full dependency list
