# Design Spec: 2026-03-26-sync-and-config-migration.md

## Overview
Migrate configuration synchronization and backup scripts from `blog-source/scripts/sync` and `blog-source/scripts/config` into the `ww` toolkit. This migration centralizes personal infrastructure management and makes environment-specific values configurable.

## Goals
- Decentralize logic from `blog-source` and centralize in `ww`.
- Replace hardcoded environment values (IPs, users) with `.env` variables.
- Maintain existing functionality for Claude Code, SSH, Bash/Zsh, and tool deployment.
- Clean up the source repository post-migration.

## Architecture
### 1. New Module Structure
- `ww/sync/`: Contains implementation logic for various sync tasks.
    - `claude.py`: Claude Code settings sanitization and backup.
    - `shell.py`: `.bashrc` and `.zprofile` sync logic.
    - `ssh.py`: SSH config sync.
    - `deploy.py`: Tool deployment (e.g., `gitmessageai.py` to `~/bin/`).
- `ww/config/`: Storage for backed-up/sanitized configuration files.

### 2. Configuration (`.env`)
New variables to be added:
- `WW_REMOTE_IP`: Target IP for sync (default: `192.168.1.3`)
- `WW_REMOTE_USER`: Remote username (default: `lzw`)

### 3. Command Dispatch (`ww/main.py`)
Add a `sync` group with subcommands:
- `ww sync claude`
- `ww sync bashrc [back|forth]`
- `ww sync zprofile [back|forth]`
- `ww sync ssh`
- `ww sync deploy` (specifically for `gitmessageai.py`)

## Implementation Plan
1.  **Preparation**: Add `WW_REMOTE_IP` and `WW_REMOTE_USER` to `.env`.
2.  **Porting**:
    - Copy `sync_claude_code_config.py` to `ww/sync/claude.py`, updating paths to use `ww`'s internal structure.
    - Consolidate `sync_bashrc.py` and `sync_zprofile.py` into `ww/sync/shell.py` using `os.getenv`.
    - Create `ww/sync/deploy.py` for `gitmessageai.py`.
3.  **Data Move**: Copy files from `blog-source/scripts/config/` to `ww/config/`.
4.  **CLI Integration**: Register commands in `ww/main.py`.
5.  **Verification**: Test commands (dry-run where possible).
6.  **Cleanup**: Delete `blog-source/scripts/sync/` and `blog-source/scripts/config/`.

## Success Criteria
- `ww sync claude` correctly sanitizes and saves to `ww/config/claude_code_settings.json`.
- `ww sync bashrc` correctly uses `.env` values for `scp` commands.
- All original files in `blog-source` are removed.
