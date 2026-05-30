# AGENTS.md — Coding Guide for ww

## Project Overview

`ww` is a Python CLI toolkit with 90+ command modules covering git workflows, GitHub management, note-taking, image processing, web search, network diagnostics, system monitoring, and more — many enhanced with LLM-powered intelligence via OpenRouter.

## Setup

```bash
uv sync              # Install deps (recommended)
uv run ww <command>  # Run without activating venv
```

Requires `.env` with:
- `OPENROUTER_API_KEY` — LLM-powered commands
- `MODEL` — default LLM model (e.g. `deepseek/deepseek-v3.2`)
- `VISION_MODEL` — vision model (e.g. `google/gemini-2.5-flash-image`)
- `BASE_PATH` — optional override for project root

## Architecture

### Entry Point & Dispatch

`ww/main.py` (~1330 lines) is the single command dispatcher. It uses lazy string-based routing — each command name maps to a function imported on-demand via `if/elif` chains. To add a new command:

1. Add the `elif group == "your-group":` block in `main.py`
2. Implement `main()` in `ww/your_module/your_file.py`
3. Register the help text in `_print_help()`

### Module Layout

Each subdirectory under `ww/` is a command module. Every module exposes a `main()` function that `main.py` imports on-demand. Key modules:

| Module | Purpose |
|--------|---------|
| `ww/llm/` | OpenRouter API wrapper (`openrouter_client.py`) + account management (`openrouter_mgmt.py`) |
| `ww/github/` | GitHub API: repos, starred, notifications + AI commit messages (`gitmessageai.py`) |
| `ww/git/` | Git operations: commit, squash, amend, force-push, diff, classify |
| `ww/note/` | Note/log creation with git integration, screenshot-to-note, clipboard notes |
| `ww/image/` | PIL/numpy image processing: background removal, crop, compress, EXIF, screenshots |
| `ww/search/` | Multi-engine web search (Bing, DuckDuckGo, StartPage, Ecosia, Tavily) |
| `ww/macos/` | macOS tools: notifications, fonts, disk, process analysis, proxy, app audit, dock |
| `ww/linux/` | Linux tools: GPU/CUDA info, system overview, disk, battery, proxy, WoL, key swap |
| `ww/network/` | WiFi scanning, IP/port scanning, network topology, device discovery |
| `ww/pdf/` | PDF conversion: Markdown→PDF, LaTeX, code-to-PDF, scaling, MD→PNG |
| `ww/java/` | Spring Boot/Maven analysis: POM parsing, dependency analysis, package analysis |
| `ww/audio/` | Whisper transcription, refinement, translation, organization |
| `ww/cloudflare/` | Cloudflare Web Analytics: visits, zones, datasets, GraphQL schema |
| `ww/clash/` | Clash proxy management: speed test, provider selection, DNS, proxy toggling |
| `ww/sync/` | Sync configs between machines: bashrc, zprofile, ssh, hermes, zed, claude |
| `ww/weather/` | Weather with auto-detect location, multi-day forecast |
| `ww/ghostty/` | Ghostty terminal window management: open, list, focus, close |
| `ww/degree/` | GDUFS self-study notice scraping and AI categorization |
| `ww/hf/` | HuggingFace profile display |
| `ww/display/` | macOS dark/light mode switching |
| `ww/read/` | RAG document indexing and querying (BGE + FAISS) |
| `ww/env/` | `.env` loading and model updates |

Also present but not wired into main CLI: `ww/ml/`, `ww/torch_llm/`, `ww/mmlu/`, `ww/agent/`, `ww/trading/`, `ww/social/`, `ww/selenium/`, `ww/ansible/`, `ww/arduino/`, `ww/canvas/`, `ww/bot/`, `ww/crawler/`, `ww/graph/`, `ww/kalman/`, `ww/langchain_test/`, `ww/linear/`, `ww/ocr/`, `ww/pico/`, `ww/pl/`, `ww/plot/`, `ww/postgres/`, `ww/scheme/`, `ww/supabase/`, `ww/tooluse/`, `ww/video/`, `ww/vscode/`, `ww/wandbrun/`, `ww/youtube/`, `ww/zed/`, `ww/zig/`

### LLM Integration

All LLM calls go through `ww/llm/openrouter_client.py`. Key function:

```python
call_openrouter_api_with_messages(messages, model=None, max_tokens=None, debug=False)
```

- Uses OpenRouter's `/api/v1/chat/completions` endpoint
- Reads `OPENROUTER_API_KEY` and `MODEL` from env
- Supports proxy detection and debugging
- Model aliases and per-model token limits configured elsewhere

For vision/image tasks, the project uses `google-genai` (Gemini) directly, separate from OpenRouter.

### Env Loading

`ww/env.py` loads `.env` from three locations (in order):
1. Current working directory
2. Project root (parent of `ww/`)
3. `BASE_PATH` if set

## Build & Tooling

- **Build backend**: Hatchling (`pyproject.toml`)
- **Package manager**: `uv` (recommended)
- **Python**: `>=3.11`
- **Linting**: Ruff configured with intentional rule exclusions:
  - `E731` — lambda assignments used as prompt builders
  - `E722` — bare except in network/system code
  - `F841` — unused local variables
  - Per-file `E402` exceptions for `ww/search/`, `ww/mmlu/`, `ww/networkx/`, `ww/social/`
- **Type checking**: Pyright in `basic` mode, Python 3.11 target, excludes `ww/ml/`
- **No test suite** — manual testing preferred

## Code Conventions

- Each module exposes a `main()` function as its CLI entry point
- Lazy imports inside `main()` or at function level — not at module top
- `sys.argv` manipulation via `_pop_subcmd()` for subcommand parsing
- Environment variables via `python-dotenv` (`ww.env.load_env()`)
- Commit style: Conventional Commits (`feat`, `fix`, `chore`, `docs`, etc.)
- CLI output is plain text to stdout, no rich/color libraries by default

## Adding a New Command

1. Create `ww/your_module/your_file.py` with a `main()` function
2. In `ww/main.py`, add `elif group == "your-group":` with subcommand routing
3. Add help text in `_print_help()` and in the group's own help block
4. Import lazily: `from ww.your_module.your_file import main as m` inside the elif branch

## Pitfalls

- `main.py` is large (~1330 lines) — always check existing patterns before adding new command groups
- `ww/ml/` and `ww/torch_llm/` are excluded from ruff and pyright — ML code has different standards
- No test suite — verify changes manually with `uv run ww <command>`
- `.env` file is required for LLM commands — missing keys raise exceptions at runtime
- macOS-specific commands use `pyobjc-framework-Quartz` — only available on Darwin
