import json
import os
import platform
import subprocess
import sys
import urllib.request
import tempfile


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _detect_pkg_manager() -> tuple[str, str, str]:
    """Detect the Linux package manager.

    Returns:
        (pkg_format, install_cmd, query_cmd)
        e.g. ("deb", "apt", "dpkg") for Ubuntu/Debian
             ("rpm", "dnf", "rpm") for Fedora/RHEL
    """
    try:
        subprocess.run(
            ["dpkg", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return ("deb", "apt", "dpkg")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        subprocess.run(
            ["rpm", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return ("rpm", "dnf", "rpm")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if os.path.isfile("/usr/bin/apt") or os.path.isfile("/usr/bin/apt-get"):
        return ("deb", "apt", "dpkg")

    if os.path.isfile("/usr/bin/dnf"):
        return ("rpm", "dnf", "rpm")

    print(
        "Warning: could not detect package manager (dpkg, rpm, or dnf not found).",
        file=sys.stderr,
    )
    print("Defaulting to dpkg/apt (Debian/Ubuntu).", file=sys.stderr)
    return ("deb", "apt", "dpkg")


def _is_installed() -> bool:
    if _is_macos():
        return os.path.isdir("/Applications/GitHub Desktop.app")

    # Linux: check binary paths
    paths = [
        "/usr/bin/github-desktop",
        "/usr/local/bin/github-desktop",
    ]
    if any(os.path.isfile(p) for p in paths):
        return True

    # Check dpkg
    try:
        result = subprocess.run(
            ["dpkg", "-l", "github-desktop"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and any(
            line.startswith("ii") and "github-desktop" in line
            for line in result.stdout.splitlines()
        ):
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check rpm
    try:
        result = subprocess.run(
            ["rpm", "-q", "github-desktop"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return False


def _get_latest_release() -> dict | None:
    """Fetch the latest shiftkey/desktop release info from GitHub API."""
    url = "https://api.github.com/repos/shiftkey/desktop/releases/latest"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ww/1.0",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Failed to fetch latest release info: {e}", file=sys.stderr)
        return None


def _download_file(url: str, dest: str) -> bool:
    """Download a file from url to dest. Returns True on success."""
    try:
        print(f"  Downloading {os.path.basename(dest)} ...")
        req = urllib.request.Request(url, headers={"User-Agent": "ww/1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  Download failed: {e}", file=sys.stderr)
        return False


def _install_macos() -> bool:
    """Install GitHub Desktop on macOS via Homebrew."""
    print("Installing GitHub Desktop via Homebrew...")
    print("  brew install --cask github")
    result = subprocess.run(
        ["brew", "install", "--cask", "github"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode == 0:
        return True
    print("brew install failed:")
    print(result.stderr)
    return False


def _install_deb() -> bool:
    """Install GitHub Desktop on Debian/Ubuntu via shiftkey .deb."""
    print("Fetching latest GitHub Desktop Linux release...")
    release = _get_latest_release()
    if not release:
        return False

    tag = release["tag_name"]
    print(f"  Latest: {tag}")

    # Find the amd64 .deb asset
    asset_name = None
    download_url = None
    for asset in release.get("assets", []):
        name = asset["name"]
        if name.endswith(".deb") and ("amd64" in name or "x86_64" in name):
            asset_name = name
            download_url = asset["browser_download_url"]
            break

    if not asset_name or not download_url:
        print("Could not find amd64 .deb asset in latest release.", file=sys.stderr)
        # Show available assets for debugging
        names = [a["name"] for a in release.get("assets", [])]
        print(f"  Available: {', '.join(names[:10])}", file=sys.stderr)
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        deb_path = os.path.join(tmpdir, asset_name)
        if not _download_file(download_url, deb_path):
            return False

        print("  Installing via dpkg ...")
        result = subprocess.run(
            ["sudo", "dpkg", "-i", deb_path],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print("  dpkg install had issues, attempting dependency fix...")
            print(result.stderr)

        print("  Resolving dependencies ...")
        subprocess.run(
            ["sudo", "apt-get", "install", "-f", "-y"],
            capture_output=True,
            text=True,
            timeout=300,
        )

    # Verify the binary exists now
    return _is_installed()


def _install_rpm() -> bool:
    """Install GitHub Desktop on Fedora/RHEL via shiftkey .rpm."""
    print("Fetching latest GitHub Desktop Linux release...")
    release = _get_latest_release()
    if not release:
        return False

    tag = release["tag_name"]
    print(f"  Latest: {tag}")

    # Find the x86_64 .rpm asset
    asset_name = None
    download_url = None
    for asset in release.get("assets", []):
        name = asset["name"]
        if name.endswith(".rpm") and "x86_64" in name:
            asset_name = name
            download_url = asset["browser_download_url"]
            break

    if not asset_name or not download_url:
        print("Could not find x86_64 .rpm asset in latest release.", file=sys.stderr)
        names = [a["name"] for a in release.get("assets", [])]
        print(f"  Available: {', '.join(names[:10])}", file=sys.stderr)
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        rpm_path = os.path.join(tmpdir, asset_name)
        if not _download_file(download_url, rpm_path):
            return False

        print("  Installing via dnf ...")
        result = subprocess.run(
            ["sudo", "dnf", "install", "-y", rpm_path],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print("dnf install failed:")
            print(result.stderr)
            return False

    return _is_installed()


def main():
    if _is_macos():
        system_name = "macOS"
        install_fn = _install_macos
    else:
        pkg_format, install_cmd, query_cmd = _detect_pkg_manager()
        system_name = (
            "Ubuntu/Debian/Linux Mint" if pkg_format == "deb" else "Fedora/RHEL"
        )
        install_fn = _install_deb if pkg_format == "deb" else _install_rpm

    if _is_installed():
        print("GitHub Desktop is already installed.")
        if _is_macos():
            print("Launch: open -a 'GitHub Desktop'")
        else:
            print("Launch: github-desktop")
        sys.exit(0)

    print("=" * 60)
    print("  GitHub Desktop — GUI client for Git and GitHub")
    print("  (desktop.github.com)")
    print("=" * 60)
    print(f"  Detected: {system_name}")
    print("=" * 60)
    print()

    success = install_fn()

    if success:
        print()
        print("GitHub Desktop installed successfully!")
        print()
        if _is_macos():
            print("To launch:  open -a 'GitHub Desktop'")
        else:
            print("To launch:  github-desktop")
        print("Website:   https://desktop.github.com")
    else:
        print()
        print("Installation failed.")
        print()
        if _is_macos():
            print("Try manually:")
            print("  brew install --cask github")
            print("  Or download from https://desktop.github.com")
        elif pkg_format == "deb":
            print("Try manually:")
            print("  1. Download the .deb from:")
            print("     https://github.com/shiftkey/desktop/releases/latest")
            print("  2. Install:")
            print("     sudo dpkg -i ~/Downloads/GitHubDesktop-linux-*.deb")
            print("     sudo apt-get install -f -y")
        else:
            print("Try manually:")
            print("  1. Download the .rpm from:")
            print("     https://github.com/shiftkey/desktop/releases/latest")
            print("  2. Install:")
            print("     sudo dnf install ~/Downloads/GitHubDesktop-linux-*.rpm")
        sys.exit(1)


if __name__ == "__main__":
    main()
