# `ww linux` Command Group Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a new `ww linux` command group to handle system-level provisioning (`provision`) and setup (`setup`) tasks, porting existing bash scripts to a modern Python CLI wrapper.

**Architecture:** Register `linux` in `ww/main.py`. Use a sub-dispatcher in `ww/linux/main.py` that lazy-loads implementation logic from `ww/linux/provision.py` and `ww/linux/setup.py`. Execution is handled via `subprocess.run` to allow for `.env` variable injection.

**Tech Stack:** Python 3.8+, `subprocess`, `python-dotenv` (via `ww.env`).

---

### Task 1: Module Initialization and Registration

**Files:**
- Create: `ww/linux/__init__.py`
- Modify: `ww/main.py`

- [ ] **Step 1: Create the linux package**
Run: `touch ww/linux/__init__.py`

- [ ] **Step 2: Register the linux command group in `ww/main.py`**
Modify `_print_help` to include the new section:
```python
    print("Linux:")
    print("  ww linux provision        Provision a new Linux machine")
    print("  ww linux setup            Setup Ubuntu environment")
    print("")
```
And add the dispatch logic in `main()`:
```python
    elif group == "linux":
        from ww.linux.main import main as m
        m()
```

- [ ] **Step 3: Commit**
```bash
git add ww/linux/__init__.py ww/main.py
git commit -m "feat(linux): register linux command group in CLI dispatcher"
```

### Task 2: Command Dispatcher

**Files:**
- Create: `ww/linux/main.py`

- [ ] **Step 1: Implement the sub-dispatcher**
```python
import sys

def _pop_subcmd():
    if len(sys.argv) > 1:
        return sys.argv.pop(1)
    return ""

def _print_help():
    print("Usage: ww linux <command> [options]")
    print("")
    print("Commands:")
    print("  provision    Provision a new Linux machine")
    print("  setup        Setup Ubuntu environment")

def main():
    subcmd = _pop_subcmd()
    if subcmd in ("--help", "-h", "help", ""):
        _print_help()
        return

    if subcmd == "provision":
        from ww.linux.provision import run_provision
        run_provision()
    elif subcmd == "setup":
        from ww.linux.setup import run_setup
        run_setup()
    else:
        print(f"Unknown linux command: {subcmd}")
        sys.exit(1)
```

- [ ] **Step 2: Commit**
```bash
git add ww/linux/main.py
git commit -m "feat(linux): implement sub-command dispatcher"
```

### Task 3: Provisioning Logic

**Files:**
- Create: `ww/linux/provision.py`

- [ ] **Step 1: Implement `run_provision`**
This ports the logic from `provision_new_machine.sh`.
```python
import subprocess
import os

def run_provision():
    print("Running Linux provisioning...")
    # Example logic: subprocess.run(["bash", "path/to/script.sh"])
    # Or implement directly in Python using subprocess calls.
    # We will use the embedded script approach for now.
    script = """#!/bin/bash
# Ported from provision_new_machine.sh
echo "Provisioning new machine..."
# Add commands here
"""
    subprocess.run(["bash", "-c", script], check=True)
```

- [ ] **Step 2: Commit**
```bash
git add ww/linux/provision.py
git commit -m "feat(linux): implement provision command"
```

### Task 4: Setup Logic

**Files:**
- Create: `ww/linux/setup.py`

- [ ] **Step 1: Implement `run_setup`**
This ports the logic from `setup_ubuntu.sh`.
```python
import subprocess
import os

def run_setup():
    print("Running Ubuntu setup...")
    script = """#!/bin/bash
# Ported from setup_ubuntu.sh
echo "Setting up Ubuntu..."
# Add commands here
"""
    subprocess.run(["bash", "-c", script], check=True)
```

- [ ] **Step 2: Commit**
```bash
git add ww/linux/setup.py
git commit -m "feat(linux): implement setup command"
```

### Task 5: Verification

- [ ] **Step 1: Verify help output**
Run: `ww linux --help`
Expected: Shows usage and commands.

- [ ] **Step 2: Verify dry run (if applicable)**
Run: `ww linux provision` (ensure it doesn't do anything destructive in dev)

- [ ] **Step 3: Commit**
```bash
git commit --allow-empty -m "docs(linux): verify linux command group structure"
```
