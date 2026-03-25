import json
from pathlib import Path


def sanitize_dict(d: dict) -> dict:
    """Recursively sanitize dictionary values for sensitive keys."""
    sanitized = {}
    sensitive_patterns = ["token", "key", "secret", "password"]

    for k, v in d.items():
        is_sensitive = any(pattern in k.lower() for pattern in sensitive_patterns)

        if isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        elif is_sensitive and isinstance(v, str):
            sanitized[k] = "REDACTED"
        else:
            sanitized[k] = v

    return sanitized


def sync_claude_settings():
    """Read ~/.claude/settings.json, sanitize it, and save to ww/config/."""
    home = Path.home()
    settings_path = home / ".claude" / "settings.json"

    if not settings_path.exists():
        print(f"Error: {settings_path} not found.")
        return

    try:
        with open(settings_path, "r") as f:
            settings = json.load(f)
    except Exception as e:
        print(f"Error reading settings: {e}")
        return

    sanitized_settings = sanitize_dict(settings)

    # Ensure config directory exists relative to this file
    current_dir = Path(__file__).parent.parent
    config_dir = current_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    output_path = config_dir / "claude_code_settings.json"

    with open(output_path, "w") as f:
        json.dump(sanitized_settings, f, indent=2)

    print(f"Sanitized settings saved to {output_path}")


def main():
    sync_claude_settings()


if __name__ == "__main__":
    main()
