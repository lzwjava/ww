import os
import shutil
from pathlib import Path


def _config_dir() -> Path:
    """Return CONFIG_DIR from env, default to ~/projects/config."""
    return Path(os.getenv("CONFIG_DIR") or str(Path.home() / "projects" / "config"))


def sync_claude_settings():
    """Copy ~/.claude/settings.json -> $CONFIG_DIR/claude/settings.json (no sanitization)."""
    home = Path.home()
    settings_path = home / ".claude" / "settings.json"

    if not settings_path.exists():
        print(f"Error: {settings_path} not found.")
        return

    dst_dir = _config_dir() / "claude"
    dst_dir.mkdir(parents=True, exist_ok=True)
    output_path = dst_dir / "settings.json"

    shutil.copy2(settings_path, output_path)
    print(f"Copied {settings_path} -> {output_path}")


def main():
    sync_claude_settings()


if __name__ == "__main__":
    main()
