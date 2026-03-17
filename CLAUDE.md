# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ww` is a Python CLI toolkit for personal automation with LLM integration. It provides git workflows, note management, image processing, web search, and macOS utilities.

## Setup & Installation

```bash
pip install -e .   # Development install
```

Requires a `.env` file with API keys (loaded via `python-dotenv`):
- `OPENROUTER_API_KEY` — required for all LLM-powered commands

## Running Commands

```bash
ww <command> [options]
```

There are no tests or linting configurations in this project.

## Architecture

### Entry Point & Dispatch

`ww/main.py` is the single command dispatcher. It uses lazy string-based routing — each command name maps to a function imported on-demand. To add a new command, register it in `main.py` and implement the function in the appropriate module.

### Module Layout

| Module | Purpose |
|--------|---------|
| `ww/llm/` | OpenRouter API wrapper supporting Claude, Gemini, GPT, DeepSeek, etc. |
| `ww/github/` | AI-powered commit message generation (`gitmessageai.py`) using git diffs |
| `ww/git/` | Git operations: commit, squash, amend, force-push, diff utilities |
| `ww/create/` | Note/log creation with git integration and MathJax fixing |
| `ww/content/` | Markdown processing: MathJax delimiter normalization, table formatting |
| `ww/image/` | PIL/numpy-based image processing: background removal, cropping, GIF |
| `ww/search/` | Multi-engine web search (Bing, DuckDuckGo, StartPage, Ecosia) |
| `ww/macos/` | macOS-specific tools: notifications, fonts, disk detection, directory sizing |
| `ww/java/` | Spring Boot/Maven project analysis: POM parsing, dependency analysis |

### LLM Integration

All LLM calls go through `ww/llm/openrouter_client.py`. It wraps the OpenRouter API and supports model aliases. Default token limits vary by model (e.g., Gemini-Flash: 400K, Claude-Opus: 8K).

### Conventions

- **Commit style**: Conventional Commits (`feat`, `fix`, `chore`, `docs`, etc.)
- **Python requirement**: `>=3.8`
- **Build backend**: Hatchling (`pyproject.toml`)
- No test suite, no linting config
