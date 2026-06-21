import os
import subprocess
from pathlib import Path

DEFAULT_REMOTE = "lzw@192.168.1.36"


def _config_dir() -> Path:
    """Return CONFIG_DIR from env, default to ~/projects/config."""
    return Path(os.getenv("CONFIG_DIR") or str(Path.home() / "projects" / "config"))


def sync_openclaw_config(remote: str):
    """Fetch openclaw config from remote server and save locally (no sanitization)."""
    remote_path = f"{remote}:.openclaw/openclaw.json"
    dst_dir = _config_dir() / "openclaw"
    dst_dir.mkdir(parents=True, exist_ok=True)
    output_path = dst_dir / "openclaw.json"

    cmd = f"scp {remote_path} {output_path}"
    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

    print(f"Copied to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync openclaw config from remote server"
    )
    parser.add_argument(
        "--remote",
        default=DEFAULT_REMOTE,
        help=f"Remote user@host (default: {DEFAULT_REMOTE})",
    )
    args = parser.parse_args()
    sync_openclaw_config(args.remote)


if __name__ == "__main__":
    main()
