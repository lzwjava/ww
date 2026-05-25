"""Open Zed connected to a remote machine via SSH.

Usage: ww zed [path]

    ww zed              # open / on remote
    ww zed /mnt/data/   # open /mnt/data/ on remote
    ww zed ~/projects   # open ~/projects on remote
    ww zed zz           # alias -> /mnt/data/zz
    ww zed deepseek-v4  # alias -> /mnt/data/deepseek-v4
"""

import subprocess
import sys

REMOTE_USER = "lzw"
REMOTE_HOST = "192.168.1.36"

# Bare names (no slashes) map to /mnt/data/<name>
DEFAULT_PREFIX = "/mnt/data"


def _build_ssh_url(path: str) -> str:
    path = path.strip()
    if not path:
        path = "/"
    elif not path.startswith("/") and not path.startswith("~"):
        if "/" not in path:
            path = f"{DEFAULT_PREFIX}/{path}"
        else:
            path = "/" + path
    return f"ssh://{REMOTE_USER}@{REMOTE_HOST}{path}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/"
    url = _build_ssh_url(path)
    print(f"Opening Zed: {url}")
    subprocess.run(["zed", url])
