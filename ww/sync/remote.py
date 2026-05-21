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


def sync_hermes(
    direction: str = "forth", from_host: str = "localhost", to_host: str = ""
) -> None:
    """
    Sync ~/.hermes/ between two hosts.
    direction="forth": copy from from_host to to_host
    direction="back":  copy from to_host to from_host
    Each host is either "localhost" or "user@ip".
    """
    if not to_host:
        # Fallback: use env vars like the other sync commands
        remote_ip = os.getenv("WW_REMOTE_IP") or "192.168.1.3"
        remote_user = os.getenv("WW_REMOTE_USER") or "lzw"
        to_host = f"{remote_user}@{remote_ip}"

    if direction == "forth":
        src_host = from_host
        dst_host = to_host
    else:
        src_host = to_host
        dst_host = from_host

    src_path = "~/.hermes/"
    dst_path = "~/"

    def _scp_path(host: str, path: str) -> str:
        return path if host == "localhost" else f"{host}:{path}"

    src = _scp_path(src_host, src_path)
    dst = _scp_path(dst_host, dst_path)

    cmd = f"scp -r {src} {dst}"
    print(f"Syncing {src_host}:~/.hermes/ -> {dst_host}:~/.hermes/")
    print(f"  {cmd}")
    subprocess.run(cmd, shell=True, check=True)
