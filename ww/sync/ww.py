"""Sync ww configuration (.env) between canonical location and CONFIG_DIR."""

import os
import shutil
from pathlib import Path


def _config_dir() -> Path:
    return Path(os.getenv("CONFIG_DIR") or str(Path.home() / "projects" / "config"))


def sync_ww_env(direction: str = "forth") -> None:
    """
    Sync ~/.config/ww/.env <-> $CONFIG_DIR/ww/.env

    forth (default): canonical -> CONFIG_DIR (save canonical config to shared dir)
    back:            CONFIG_DIR -> canonical (restore canonical from shared dir)
    """
    canonical = Path.home() / ".config" / "ww" / ".env"
    config_ww = _config_dir() / "ww" / ".env"

    if direction == "forth":
        src = canonical
        dst = config_ww
    elif direction == "back":
        src = config_ww
        dst = canonical
    else:
        print(f"Unknown direction: {direction} (use 'forth' or 'back')")
        return

    if not src.is_file():
        print(f"Source not found: {src}")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    print(f"Synced {src} -> {dst}")


def main():
    direction = "forth"
    args = os.environ.get("WW_SYNC_DIRECTION", "")
    if args in ("back", "forth"):
        direction = args

    # Also check command-line argument
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("back", "forth"):
        direction = sys.argv[1]

    sync_ww_env(direction)