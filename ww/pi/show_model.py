"""Show the default startup model of the pi coding agent."""

import sys

from ww.pi.set_model import load_settings, settings_path


def main():
    settings = load_settings()
    provider = settings.get("defaultProvider", "")
    model = settings.get("defaultModel", "")
    if not provider and not model:
        print(f"No default model set in {settings_path()}")
        sys.exit(1)
    print(f"{provider}/{model}")


if __name__ == "__main__":
    main()
