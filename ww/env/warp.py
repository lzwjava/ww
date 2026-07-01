import glob
import os
import subprocess
import sys


def _detect_pkg_manager() -> tuple[str, str, str]:
    """Detect the Linux package manager.

    Returns:
        (pkg_format, install_cmd, query_cmd)
        e.g. ("deb", "apt", "dpkg") for Ubuntu/Debian
             ("rpm", "dnf", "rpm") for Fedora/RHEL
    """
    # Check for dpkg first (Ubuntu/Debian)
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

    # Fallback to rpm (Fedora/RHEL)
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

    # Last resort — check for apt directly
    if os.path.isfile("/usr/bin/apt") or os.path.isfile("/usr/bin/apt-get"):
        return ("deb", "apt", "dpkg")

    # If dnf exists, use rpm
    if os.path.isfile("/usr/bin/dnf"):
        return ("rpm", "dnf", "rpm")

    print(
        "Warning: could not detect package manager (dpkg, rpm, or dnf not found).",
        file=sys.stderr,
    )
    print("Defaulting to dpkg/apt (Debian/Ubuntu).", file=sys.stderr)
    return ("deb", "apt", "dpkg")


def _is_installed(pkg_format: str, query_cmd: str) -> bool:
    paths = [
        "/usr/bin/warp-terminal",
        "/usr/local/bin/warp-terminal",
        "/opt/Warp/warp-terminal",
    ]
    if any(os.path.isfile(p) for p in paths):
        return True

    try:
        if query_cmd == "dpkg":
            result = subprocess.run(
                ["dpkg", "-l", "warp-terminal"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # dpkg -l lists installed packages with 'ii' in first two columns
            return result.returncode == 0 and any(
                line.startswith("ii") and "warp-terminal" in line
                for line in result.stdout.splitlines()
            )
        else:
            # rpm -q
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


def _find_package(pkg_format: str) -> str | None:
    downloads = os.path.expanduser("~/Downloads")
    if pkg_format == "deb":
        pattern = "warp-terminal*.deb"
    else:
        pattern = "warp-terminal*.rpm"
    candidates = sorted(
        glob.glob(os.path.join(downloads, pattern)),
        key=os.path.getmtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def main():
    pkg_format, install_cmd, query_cmd = _detect_pkg_manager()
    distro_name = "Ubuntu/Debian" if pkg_format == "deb" else "Fedora/RHEL"

    if _is_installed(pkg_format, query_cmd):
        print("Warp is already installed.")
        sys.exit(0)

    print("=" * 60)
    print("  Warp — The Agentic Development Environment")
    print("  (warp.dev)")
    print("=" * 60)
    print(f"  Detected: {distro_name} ({pkg_format})")
    print("=" * 60)
    print()

    _open_browser("https://www.warp.dev/download")

    print("A browser window should open with the Warp download page.")
    if pkg_format == "deb":
        print("Download the Linux .deb package and save it to ~/Downloads.")
    else:
        print("Download the Linux RPM and save it to ~/Downloads.")
    print()
    try:
        input("Press Enter after the download is complete... ")
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)

    pkg_path = _find_package(pkg_format)
    if not pkg_path:
        ext = ".deb" if pkg_format == "deb" else ".rpm"
        print(f"No warp-terminal-*{ext} found in ~/Downloads.")
        retry = input("Try again? (y/N): ").strip().lower()
        if retry == "y":
            try:
                input("Press Enter after downloading... ")
            except KeyboardInterrupt:
                print("\nCancelled.")
                sys.exit(0)
            pkg_path = _find_package(pkg_format)
            if not pkg_path:
                print(f"Still not found. You can install the downloaded {ext} manually:")
                if pkg_format == "deb":
                    print("  sudo dpkg -i ~/Downloads/warp-terminal-*.deb")
                    print("  sudo apt-get install -f -y   # fix dependencies")
                else:
                    print("  sudo dnf install ~/Downloads/warp-terminal-*.rpm")
                sys.exit(1)
        else:
            sys.exit(0)

    print(f"Found: {pkg_path}")
    print(f"Installing with sudo {install_cmd}...")

    if pkg_format == "deb":
        # dpkg -i installs the .deb, then apt-get -f fixes missing deps
        result = subprocess.run(
            ["sudo", "dpkg", "-i", pkg_path],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            # Resolve dependencies
            subprocess.run(
                ["sudo", "apt-get", "install", "-f", "-y"],
                capture_output=True,
                text=True,
                timeout=300,
            )
        else:
            print("dpkg install failed:")
            print(result.stderr)
            # Try apt anyway — it can sometimes fix it
            print("Attempting apt install -f to resolve...")
            subprocess.run(
                ["sudo", "apt-get", "install", "-f", "-y"],
                capture_output=True,
                text=True,
                timeout=300,
            )
    else:
        # RPM-based: dnf install -y
        result = subprocess.run(
            ["sudo", "dnf", "install", "-y", pkg_path],
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