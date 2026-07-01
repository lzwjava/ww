import os
import subprocess
import sys


def _is_installed() -> bool:
    paths = [
        "/usr/bin/warp-terminal",
        "/usr/local/bin/warp-terminal",
        "/opt/Warp/warp-terminal",
    ]
    if any(os.path.isfile(p) for p in paths):
        return True
    try:
        result = subprocess.run(
            ["rpm", "-q", "warp-terminal"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _open_browser(url: str):
    """Open a URL in the user's default browser."""
    for cmd in ["xdg-open", "gnome-open", "kde-open"]:
        try:
            subprocess.run([cmd, url], timeout=10)
            print(f"  Opened: {url}")
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False


def main():
    if _is_installed():
        print("Warp is already installed.")
        sys.exit(0)

    download_url = "https://www.warp.dev/download"

    print("=" * 60)
    print("  Warp — The Agentic Development Environment")
    print("  (warp.dev)")
    print("=" * 60)
    print()
    print("The Warp RPM download requires a browser (captcha-protected).")
    print()

    opened = _open_browser(download_url)
    if opened:
        print()
        print("A browser window should open. Download the Linux RPM and")
        print("install it with:")
        print()
        print("  sudo dnf install ~/Downloads/warp-terminal-*.rpm")
        print()

    print("Or visit the download page yourself:")
    print(f"  {download_url}")
    print()
    print("After installation:")
    print("  - Launch:   warp-terminal")
    print("  - Docs:     https://docs.warp.dev")
    print()
    print("Note: Warp can also be built from source:")
    print("  https://github.com/warpdotdev/warp")


if __name__ == "__main__":
    main()