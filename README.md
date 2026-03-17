# ww

A cross-platform CLI toolkit for personal and enterprise automation, with LLM integration.
Notes, git, PDF, media, search and AI workflows — on any platform.
Works on macOS, Linux and Windows.

## Installation

```bash
pip install -e .
```

## Usage

```bash
ww <command> [options]
```

## Commands

### Notes & Logs

| Command | Description |
|---------|-------------|
| `create-note` | Create a new note from clipboard |
| `create-log` | Create a timestamped log entry |

### Git

| Command | Description |
|---------|-------------|
| `gitmessageai` | Generate AI commit message and commit/push changes |

`gitmessageai` options:
- `--no-push` — commit without pushing
- `--only-message` — print the message only, do not commit
- `--model <name>` — AI model to use (default: `grok-fast`)
- `--allow-pull-push` — pull before pushing
- `--type <file\|content>` — diff type to use (default: `content`)

### GitHub

| Command | Description |
|---------|-------------|
| `github-readme` | Generate a markdown summary of GitHub projects (requires `GITHUB_TOKEN`) |

### Images

| Command | Description |
|---------|-------------|
| `avatar` | Generate an avatar image |
| `crop` | Center-crop an image |
| `remove-bg` | Remove image background |
| `screenshot` | Take a screenshot (macOS) |
| `screenshot-linux` | Take a screenshot (Linux) |

### Media

| Command | Description |
|---------|-------------|
| `gif` | Create a GIF from images or video frames |

### macOS Utilities

| Command | Description |
|---------|-------------|
| `find-large-dirs` | Find the largest directories on disk |
| `system-info` | Print system information |
| `mac-install` | Run macOS setup/install script |
| `list-fonts` | List installed fonts |
| `list-disks` | List portable/external disks |
| `open-terminal` | Open a new Terminal window |
| `toast` | Show a macOS toast notification |

## Requirements

- Python >= 3.8
- See `pyproject.toml` for full dependency list
