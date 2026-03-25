# Sync and Config Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize personal configuration synchronization and backup scripts from `blog-source` into the `ww` toolkit, making them portable via environment variables.

**Architecture:** New `ww/sync/` module for logic and `ww/config/` for data persistence, with command dispatch integrated into `ww/main.py`.

**Tech Stack:** Python 3, `subprocess`, `os`, `shutil`, `json`.

---

### Task 1: Environment and Project Setup

**Files:**
- Modify: `.env`
- Modify: `.gitignore`

- [ ] **Step 1: Add new environment variables to `.env`**

```bash
cat >> /Users/lzwjava/projects/ww/.env <<EOF
WW_REMOTE_IP=192.168.1.3
WW_REMOTE_USER=lzw
EOF
```

- [ ] **Step 2: Update `.gitignore` to exclude personal config backups**

```bash
cat >> /Users/lzwjava/projects/ww/.gitignore <<EOF

# Configuration backups
ww/config/claude_code_settings.json
ww/config/.bashrc
ww/config/.zprofile
ww/config/ssh_config
EOF
```

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p /Users/lzwjava/projects/ww/ww/sync /Users/lzwjava/projects/ww/ww/config
touch /Users/lzwjava/projects/ww/ww/sync/__init__.py /Users/lzwjava/projects/ww/ww/config/__init__.py
```

- [ ] **Step 4: Commit setup**

```bash
git add .env .gitignore ww/sync/ ww/config/
git commit -m "chore: setup sync and config migration infrastructure"
```

### Task 2: Implement Claude Code Sync

**Files:**
- Create: `ww/sync/claude.py`

- [ ] **Step 1: Port and refactor Claude Code sync logic**

```python
import json
import os

def sync_claude_config():
    """Sanitize and backup Claude Code config."""
    source_path = os.path.expanduser("~/.claude/settings.json")
    target_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "claude_code_settings.json")

    if not os.path.exists(source_path):
        print(f"Source not found: {source_path}")
        return

    with open(source_path, "r") as f:
        config = json.load(f)

    # Sanitization logic...
    if "env" in config:
        for key in config["env"]:
            if any(s in key.lower() for s in ["token", "key", "secret", "password"]):
                config["env"][key] = ""

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Synced to {target_path}")

if __name__ == "__main__":
    sync_claude_config()
```

- [ ] **Step 2: Commit Claude sync**

```bash
git add ww/sync/claude.py
git commit -m "feat(sync): add Claude Code config sync"
```

### Task 3: Implement Shell and SSH Sync

**Files:**
- Create: `ww/sync/remote.py`

- [ ] **Step 1: Create generic remote sync utility**

```python
import os
import subprocess

def remote_sync(local_path, remote_path, direction="forth"):
    ip = os.getenv("WW_REMOTE_IP", "192.168.1.3")
    user = os.getenv("WW_REMOTE_USER", "lzw")

    if direction == "forth":
        cmd = f"scp {local_path} {user}@{ip}:{remote_path}"
    else:
        cmd = f"scp {user}@{ip}:{remote_path} {local_path}"

    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def sync_bashrc(direction="forth"):
    local = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".bashrc")
    remote_sync(local, "~/.bashrc", direction)

def sync_zprofile(direction="forth"):
    local = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".zprofile")
    remote_sync(local, "~/.zprofile", direction)
```

- [ ] **Step 2: Commit remote sync**

```bash
git add ww/sync/remote.py
git commit -m "feat(sync): add remote shell and ssh sync logic"
```

### Task 4: CLI Integration

**Files:**
- Modify: `ww/main.py`

- [ ] **Step 1: Register sync commands**

```python
# In main.py, add to _print_help and the main loop:
if group == "sync":
    subcmd = _pop_subcmd()
    if subcmd == "claude":
        from ww.sync.claude import sync_claude_config
        sync_claude_config()
    elif subcmd in ("bashrc", "zprofile"):
        direction = _pop_subcmd() or "forth"
        from ww.sync.remote import sync_bashrc, sync_zprofile
        if subcmd == "bashrc": sync_bashrc(direction)
        else: sync_zprofile(direction)
```

- [ ] **Step 2: Commit CLI changes**

```bash
git add ww/main.py
git commit -m "feat(cli): add sync command group"
```

### Task 5: Data Migration and Cleanup

- [ ] **Step 1: Move existing config files**

```bash
cp /Users/lzwjava/projects/blog-source/scripts/config/* /Users/lzwjava/projects/ww/ww/config/
```

- [ ] **Step 2: Delete original files from blog-source**

```bash
rm -rf /Users/lzwjava/projects/blog-source/scripts/sync
rm -rf /Users/lzwjava/projects/blog-source/scripts/config
```

- [ ] **Step 3: Final commit and verification**

```bash
git add ww/config/
git commit -m "chore: migrate config data and cleanup blog-source"
```
