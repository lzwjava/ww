import os
import subprocess
from pathlib import Path


def remote_sync(local_path: str, remote_path: str, direction: str = "forth") -> None:
    """
    Sync a file or directory between local and remote using scp.
    direction="forth": local -> remote
    direction="back": remote -> local
    """
    remote_ip = os.getenv("WW_REMOTE_IP", "192.168.1.3")
    remote_user = os.getenv("WW_REMOTE_USER", "lzw")
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
