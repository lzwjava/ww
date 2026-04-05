import argparse
import json
import subprocess
from pathlib import Path

DEFAULT_REMOTE = "lzw@192.168.1.36"


def sync_openclaw_config(remote: str):
    """Fetch openclaw config from remote server, sanitize it, and save locally."""
    remote = f"{remote}:.openclaw/openclaw.json"
    tmp_path = Path("/tmp/openclaw_config.json")

    cmd = f"scp {remote} {tmp_path}"
    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

    with open(tmp_path, "r") as f:
        config = json.load(f)

    from ww.sync.claude import sanitize_dict

    sanitized = sanitize_dict(config)

    current_dir = Path(__file__).parent.parent
    config_dir = current_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    output_path = config_dir / "openclaw.json"
    with open(output_path, "w") as f:
        json.dump(sanitized, f, indent=2)

    print(f"Sanitized config saved to {output_path}")


def main():
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
