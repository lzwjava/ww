import os
import subprocess
from pathlib import Path


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


def sync_hermes() -> None:
    """
    Copy Hermes config from ww/config/hermes/ to ~/.hermes/.
    Preserves directory structure (plugins/, hooks/, etc.).
    """
    import shutil

    src_dir = Path(__file__).resolve().parent.parent / "config" / "hermes"
    dst_dir = Path.home() / ".hermes"

    if not src_dir.is_dir():
        print(f"Source not found: {src_dir}")
        return

    copied = []
    for src_file in sorted(src_dir.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        copied.append(str(rel))

    if copied:
        print(f"Copied {len(copied)} file(s) from {src_dir} -> {dst_dir}/")
        for f in copied:
            print(f"  {f}")
    else:
        print(f"No files found in {src_dir}")
