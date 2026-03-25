# Linux Script Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate 8 Linux utility scripts from `blog-source` to a unified `ww linux` command group.

**Architecture:** Use a lazy-loading dispatcher in `ww/linux/main.py` that routes to individual modules in `ww/linux/`. Each module will contain the ported logic from the original Python scripts, refined for the `ww` environment.

**Tech Stack:** Python 3.8+, `subprocess`, `psutil`, `matplotlib` (optional dependency for disk charts).

---

### Task 1: Module Structure and CLI Registration

**Files:**
- Create: `ww/linux/__init__.py`
- Create: `ww/linux/main.py`
- Modify: `ww/main.py`

- [ ] **Step 1: Create the linux package**
Run: `touch ww/linux/__init__.py`

- [ ] **Step 2: Implement the linux sub-dispatcher in `ww/linux/main.py`**
```python
import sys

def _pop_subcmd():
    if len(sys.argv) > 1:
        return sys.argv.pop(1)
    return ""

def _print_help():
    print("Usage: ww linux <command> [options]")
    print("\nCommands:")
    print("  gpu          Show GPU and CUDA details")
    print("  system       Comprehensive system overview")
    print("  disk         Show disk usage")
    print("  battery      Show battery status")
    print("  proxy-setup  Interactively configure APT proxy")
    print("  wol          Send a Wake-on-LAN packet")
    print("  terminal     Open a fullscreen terminal")

def main():
    subcmd = _pop_subcmd()
    if subcmd in ("--help", "-h", "help", ""):
        _print_help()
        return

    if subcmd == "gpu":
        from ww.linux.gpu import run; run()
    elif subcmd == "system":
        from ww.linux.system import run; run()
    elif subcmd == "disk":
        from ww.linux.disk import run; run()
    elif subcmd == "battery":
        from ww.linux.battery import run; run()
    elif subcmd == "proxy-setup":
        from ww.linux.setup import run_proxy_setup; run_proxy_setup()
    elif subcmd == "wol":
        from ww.linux.net import run_wol; run_wol()
    elif subcmd == "terminal":
        from ww.linux.terminal import run; run()
    else:
        print(f"Unknown linux command: {subcmd}")
        sys.exit(1)
```

- [ ] **Step 3: Register the linux group in `ww/main.py`**
Add to `_print_help()` and the `main()` dispatch loop:
```python
    elif group == "linux":
        from ww.linux.main import main as m
        m()
```

- [ ] **Step 4: Commit**
```bash
git add ww/linux/__init__.py ww/linux/main.py ww/main.py
git commit -m "feat(linux): register linux command group and sub-dispatcher"
```

### Task 2: Port GPU and System Info Scripts

**Files:**
- Create: `ww/linux/gpu.py`
- Create: `ww/linux/system.py`

- [ ] **Step 1: Implement `ww/linux/gpu.py`**
Port logic from `blog-source/scripts/linux/get_gpu_info.py`. Wrap the `main()` logic into a `run()` function.

- [ ] **Step 2: Implement `ww/linux/system.py`**
Port logic from `blog-source/scripts/linux/get_system_info.py`. Wrap the `main()` logic into a `run()` function.

- [ ] **Step 3: Verify and Commit**
Run: `ww linux gpu` and `ww linux system` (verify they don't crash).
```bash
git add ww/linux/gpu.py ww/linux/system.py
git commit -m "feat(linux): port gpu and system info commands"
```

### Task 3: Port Disk and Battery Scripts

**Files:**
- Create: `ww/linux/disk.py`
- Create: `ww/linux/battery.py`

- [ ] **Step 1: Implement `ww/linux/disk.py`**
Port from `blog-source/scripts/linux/df.py`. Add a check for `matplotlib` import; if missing, print only text output.

- [ ] **Step 2: Implement `ww/linux/battery.py`**
Port from `blog-source/scripts/linux/system_battery_status.py`.

- [ ] **Step 3: Commit**
```bash
git add ww/linux/disk.py ww/linux/battery.py
git commit -m "feat(linux): port disk and battery commands"
```

### Task 4: Port Setup, Network, and Terminal Scripts

**Files:**
- Create: `ww/linux/setup.py`
- Create: `ww/linux/net.py`
- Create: `ww/linux/terminal.py`

- [ ] **Step 1: Implement `ww/linux/setup.py`**
Port `setup_apt_proxy.py`. Also check if `setup.py` has any other logic to include.

- [ ] **Step 2: Implement `ww/linux/net.py`**
Port `wakeonlan.py`. Use `os.getenv("MAG_MAC_ADDRESS")`.

- [ ] **Step 3: Implement `ww/linux/terminal.py`**
Port `random_terminal.py`.

- [ ] **Step 4: Commit**
```bash
git add ww/linux/setup.py ww/linux/net.py ww/linux/terminal.py
git commit -m "feat(linux): port setup, net, and terminal commands"
```

### Task 5: Final Verification and Cleanup

- [ ] **Step 1: Verify all commands help output**
Run: `ww linux`

- [ ] **Step 2: Delete source scripts**
Run: `rm -rf /Users/lzwjava/projects/blog-source/scripts/linux/`

- [ ] **Step 3: Commit cleanup**
```bash
git commit -m "chore(linux): remove source scripts after successful migration"
```
