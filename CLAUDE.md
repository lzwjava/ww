# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ww` is a Python CLI toolkit for personal and enterprise automation with LLM integration. It provides 90+ command modules covering git workflows, GitHub management, note-taking, image processing, web search, network diagnostics, system monitoring, and more.

## Setup & Installation

```bash
uv sync              # Install dependencies (recommended)
uv run ww <command>  # Run without activating venv
pip install -e .     # Alternative: development install
```

Requires a `.env` file with API keys (loaded via `python-dotenv`):
- `OPENROUTER_API_KEY` — required for all LLM-powered commands
- `MODEL` — default LLM model (e.g. `deepseek/deepseek-v3.2`)
- `VISION_MODEL` — vision model (e.g. `google/gemini-2.5-flash-image`)

## Running Commands

```bash
ww <group> [command] [options]
```

## Architecture

### Entry Point & Dispatch

`ww/main.py` (~1330 lines) is the single command dispatcher. It uses lazy string-based routing — each command name maps to a function imported on-demand via `if/elif` chains. To add a new command, register it in `main.py` and implement the function in the appropriate module.

### Module Layout

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
| `ww/content/` | Markdown processing: MathJax delimiter normalization, table formatting |
| `ww/hf/` | HuggingFace profile display |
| `ww/read/` | RAG document indexing and querying (BGE + FAISS) |

### LLM Integration

All LLM calls go through `ww/llm/openrouter_client.py`. It wraps the OpenRouter API and supports model aliases. Default token limits vary by model. For vision/image tasks, the project uses `google-genai` (Gemini) directly.

### Conventions

- **Commit style**: Conventional Commits (`feat`, `fix`, `chore`, `docs`, etc.)
- **Python requirement**: `>=3.11`
- **Build backend**: Hatchling (`pyproject.toml`)
- **Package manager**: `uv` (recommended)
- **Linting**: Ruff configured (see `pyproject.toml` for rule exclusions)
- **Type checking**: Pyright in `basic` mode
- **No test suite** — manual testing preferred
