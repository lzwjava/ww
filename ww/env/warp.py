import glob
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


def _open_browser(url: str) -> bool:
    for cmd in ["xdg-open", "gnome-open", "kde-open"]:
        try:
            subprocess.run([cmd, url], timeout=10)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False


def _find_rpm() -> str | None:
    downloads = os.path.expanduser("~/Downloads")
    candidates = sorted(
        glob.glob(os.path.join(downloads, "warp-terminal-*.rpm")),
        key=os.path.getmtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def main():
    if _is_installed():
        print("Warp is already installed.")
        sys.exit(0)

    print("=" * 60)
    print("  Warp — The Agentic Development Environment")
    print("  (warp.dev)")
    print("=" * 60)
    print()

    _open_browser("https://www.warp.dev/download")

    print("A browser window should open with the Warp download page.")
    print("Download the Linux RPM and save it to ~/Downloads.")
    print()
    try:
        input("Press Enter after the download is complete... ")
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)

    rpm_path = _find_rpm()
    if not rpm_path:
        print("No warp-terminal-*.rpm found in ~/Downloads.")
        retry = input("Try again? (y/N): ").strip().lower()
        if retry == "y":
            try:
                input("Press Enter after downloading... ")
            except KeyboardInterrupt:
                print("\nCancelled.")
                sys.exit(0)
            rpm_path = _find_rpm()
            if not rpm_path:
                print("Still not found. You can install the downloaded RPM manually:")
                print("  sudo dnf install ~/Downloads/warp-terminal-*.rpm")
                sys.exit(1)
        else:
            sys.exit(0)

    print(f"Found: {rpm_path}")
    print("Installing with sudo dnf...")

    result = subprocess.run(
        ["sudo", "dnf", "install", "-y", rpm_path],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode == 0:
        print()
        print("Warp installed successfully!")
        print()
        print("To launch:  warp-terminal")
        print("Docs:      https://docs.warp.dev")
    else:
        print("Installation failed:")
        print(result.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()