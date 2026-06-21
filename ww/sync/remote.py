import os
import subprocess
import shutil
from pathlib import Path


def _config_dir() -> Path:
    """Return CONFIG_DIR from env, default to ~/projects/config."""
    return Path(os.getenv("CONFIG_DIR") or str(Path.home() / "projects" / "config"))


def remote_sync(local_path: str, remote_path: str, direction: str = "forth") -> None:
    """
    Sync a file or directory between local and remote using scp.
    direction="forth": local -> remote
    direction="back": remote -> local
    """
    remote_ip = os.getenv("WW_REMOTE_IP") or "192.168.1.3"
    remote_user = os.getenv("WW_REMOTE_USER") or "lzw"
    remote_host = f"{remote_user}@{remote_ip}"

    if direction == "forth":
        src = local_path
        dst = f"{remote_host}:{remote_path}"
    else:
        src = f"{remote_host}:{remote_path}"
        dst = local_path

    cmd = f"scp -r {src} {dst}"
    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def sync_bashrc(direction: str = "forth") -> None:
    local_path = str(Path.home() / ".bashrc")
    remote_path = "~/.bashrc"
    remote_sync(local_path, remote_path, direction)


def sync_zprofile(direction: str = "forth") -> None:
    local_path = str(Path.home() / ".zprofile")
    remote_path = "~/.zprofile"
    remote_sync(local_path, remote_path, direction)


def sync_ssh(direction: str = "forth") -> None:
    local_path = str(Path.home() / ".ssh")
    remote_path = "~/.ssh"
    remote_sync(local_path, remote_path, direction)


def sync_zed(direction: str = "forth") -> None:
    """Sync ~/.config/zed/ directory (Zed Editor config)."""
    local_path = str(Path.home() / ".config" / "zed")
    remote_path = "~/.config/zed"
    remote_sync(local_path, remote_path, direction)


def sync_hermes(direction: str = "forth") -> None:
    """
    Sync select Hermes config between $CONFIG_DIR/hermes/ and ~/.hermes/.
    Synced items: config.yaml, SOUL.md, hooks/, plugins/, agent-hooks/, on-agent-done.sh.
    direction="forth": ~/.hermes/ -> $CONFIG_DIR/hermes/ (capture active config)
    direction="back":  $CONFIG_DIR/hermes/ -> ~/.hermes/ (restore config)
    """
    config_dir = _config_dir() / "hermes"
    home_dir = Path.home() / ".hermes"

    items = [
        "config.yaml",
        "SOUL.md",
        "hooks",
        "plugins",
        "agent-hooks",
        "on-agent-done.sh",
    ]

    if direction == "forth":
        src_base = home_dir
        dst_base = config_dir
    else:
        src_base = config_dir
        dst_base = home_dir

    if not src_base.is_dir():
        print(f"Source not found: {src_base}")
        return

    copied = []
    for rel in items:
        src_path = src_base / rel
        dst_path = dst_base / rel

        if not src_path.exists():
            print(f"  SKIP {rel} (not found in {src_base}/)")
            continue

        if src_path.is_file():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src_path, dst_path)
                copied.append(rel)
            except (PermissionError, OSError) as e:
                print(f"  SKIP {rel} ({e})")
        else:
            # directory — copy all files recursively (skip __pycache__)
            for f in sorted(src_path.rglob("*")):
                if not f.is_file():
                    continue
                if "__pycache__" in f.parts:
                    continue
                f_rel = f.relative_to(src_base)
                f_dst = dst_base / f_rel
                f_dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(f, f_dst)
                    copied.append(str(f_rel))
                except (PermissionError, OSError) as e:
                    print(f"  SKIP {f_rel} ({e})")

    if copied:
        print(f"Copied {len(copied)} file(s) from {src_base}/ -> {dst_base}/")
        for f in copied:
            print(f"  {f}")
    else:
        print("No files copied")
