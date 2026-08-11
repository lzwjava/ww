import os
import platform
import subprocess
import sys


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _is_installed() -> bool:
    if _is_macos():
        return os.path.isdir("/Applications/Zed.app")

    # Linux: check binary paths
    paths = [
        "/usr/local/bin/zed",
        "/usr/bin/zed",
        os.path.expanduser("~/.local/bin/zed"),
    ]
    if any(os.path.isfile(p) for p in paths):
        return True

    # Fallback: check PATH via which
    try:
        result = subprocess.run(
            ["which", "zed"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return False


def _pick_downloader() -> str | None:
    """Return 'curl' or 'wget' if available, else None."""
    for tool in ("curl", "wget"):
        try:
            subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return tool
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _install_script() -> bool:
    """Install Zed via the official installer script (macOS and Linux)."""
    downloader = _pick_downloader()
    if not downloader:
        print(
            "Error: neither curl nor wget is available. Install one first, e.g.",
            file=sys.stderr,
        )
        print("  sudo apt install curl -y", file=sys.stderr)
        return False

    if downloader == "curl":
        cmd = "curl -fsSL https://zed.dev/install.sh | sh"
    else:
        cmd = "wget -qO- https://zed.dev/install.sh | sh"

    print(f"Installing Zed via the official installer script ({downloader})...")
    print(f"  {cmd}")
    result = subprocess.run(
        ["/bin/bash", "-c", cmd],
        timeout=600,
    )
    if result.returncode != 0:
        print("Installer script failed.", file=sys.stderr)
        return False

    # The pipe's exit code is that of `sh`, which can mask curl failures.
    # Verify the binary actually exists before reporting success.
    if not _is_installed():
        print("Installer exited 0 but Zed was not found on PATH.", file=sys.stderr)
        return False
    return True


def _install_macos() -> bool:
    """Install Zed on macOS. Try Homebrew cask first, fall back to the script."""
    try:
        subprocess.run(
            ["brew", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("Homebrew not found, using the official installer script...")
        return _install_script()

    print("Installing Zed via Homebrew...")
    print("  brew install --cask zed")
    result = subprocess.run(
        ["brew", "install", "--cask", "zed"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode == 0:
        return True

    print("brew install failed:")
    print(result.stderr)
    print()
    print("Trying the official installer script...")
    return _install_script()


def main():
    system_name = "macOS" if _is_macos() else "Linux"

    if _is_installed():
        print("Zed is already installed.")
        if _is_macos():
            print("Launch: open -a Zed")
        else:
            print("Launch: zed")
        sys.exit(0)

    print("=" * 60)
    print("  Zed — High-performance, multiplayer code editor")
    print("  (zed.dev)")
    print("=" * 60)
    print(f"  Detected: {system_name}")
    print("=" * 60)
    print()

    success = _install_macos() if _is_macos() else _install_script()

    if success:
        print()
        print("Zed installed successfully!")
        print()
        if _is_macos():
            print("To launch:  open -a Zed")
        else:
            print("To launch:  zed")
        print("Docs:      https://zed.dev/docs")
        print(
            "CLI:       zed --help  (first run may prompt to install the CLI into PATH)"
        )
    else:
        print()
        print("Installation failed.")
        print()
        if _is_macos():
            print("Try manually:")
            print("  brew install --cask zed")
            print("  Or: curl -fsSL https://zed.dev/install.sh | sh")
        else:
            print("Try manually:")
            print("  curl -fsSL https://zed.dev/install.sh | sh")
            print("  This installs to ~/.local/bin/zed")
        sys.exit(1)


if __name__ == "__main__":
    main()