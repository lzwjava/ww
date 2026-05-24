"""Open Zed connected to a remote machine via SSH.

Usage: ww zed [path]

    ww zed              # open / on remote
    ww zed /mnt/data/   # open /mnt/data/ on remote
    ww zed ~/projects   # open ~/projects on remote
"""

import subprocess
import sys

REMOTE_USER = "lzw"
REMOTE_HOST = "192.168.1.36"


def _build_ssh_url(path: str) -> str:
    path = path.strip()
    if not path:
        path = "/"
    if not path.startswith("/"):
        path = "/" + path
    return f"ssh://{REMOTE_USER}@{REMOTE_HOST}{path}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/"
    url = _build_ssh_url(path)
    print(f"Opening Zed: {url}")
    subprocess.run(["zed", url])
