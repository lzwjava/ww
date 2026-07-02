import os
import subprocess
import sys


def _detect_pkg_manager() -> tuple[str, str, str]:
    """Detect the Linux package manager.

    Returns:
        (pkg_format, install_cmd, query_cmd)
        e.g. ("deb", "apt", "dpkg") for Ubuntu/Debian/Linux Mint
             ("rpm", "dnf", "rpm") for Fedora/RHEL
    """
    # Check for dpkg first (Ubuntu/Debian/Linux Mint)
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


def _is_installed() -> bool:
    paths = [
        "/usr/bin/ghostty",
        "/usr/local/bin/ghostty",
    ]
    if any(os.path.isfile(p) for p in paths):
        return True

    # Check snap
    try:
        result = subprocess.run(
            ["snap", "list", "ghostty"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "ghostty" in result.stdout:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return False


def _install_deb() -> bool:
    """Install Ghostty on Debian/Ubuntu/Linux Mint using apt."""
    # First try: apt install ghostty (available in official Ubuntu repos 25.04+)
    print("Attempting: sudo apt install ghostty ...")
    result = subprocess.run(
        ["sudo", "apt", "install", "-y", "ghostty"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode == 0:
        return True

    # apt failed — package not found in repos. Try the PPA from mkasberg/ghostty-ubuntu.
    print("Ghostty not found in default repos. Trying the PPA installer...")
    print()

    # Check if curl is available
    try:
        subprocess.run(["curl", "--version"], capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("Error: curl is required to run the PPA installer.")
        print("Install it with: sudo apt install curl -y")
        return False

    # The mkasberg install script adds the PPA and installs
    print("Running the Ghostty Ubuntu PPA installer...")
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            "$(curl -fsSL https://raw.githubusercontent.com/mkasberg/ghostty-ubuntu/HEAD/install.sh)",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode == 0:
        return True

    print("PPA installer failed. Trying snap fallback...")
    # Fall back to snap
    try:
        result = subprocess.run(
            ["sudo", "snap", "install", "ghostty", "--classic"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            return True
        print("snap install also failed:")
        print(result.stderr)
    except FileNotFoundError:
        print("snap not available.")

    return False


def _install_rpm() -> bool:
    """Install Ghostty on Fedora/RHEL using dnf + COPR."""
    # Enable the COPR repository for Ghostty
    print("Enabling COPR repository (scottames/ghostty)...")
    result = subprocess.run(
        ["sudo", "dnf", "copr", "enable", "-y", "scottames/ghostty"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        print("Failed to enable COPR repository:")
        print(result.stderr)
        print()
        print("Trying Terra repository fallback...")
        # Fallback: Terra repo
        result = subprocess.run(
            [
                "sudo",
                "dnf",
                "install",
                "-y",
                "--nogpgcheck",
                "--repofrompath",
                "terra,https://repos.fyralabs.com/terra$releasever",
                "terra-release",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print("Terra repo also failed.")
            return False

    # Install ghostty
    print("Installing ghostty via dnf...")
    result = subprocess.run(
        ["sudo", "dnf", "install", "-y", "ghostty"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    return result.returncode == 0


def main():
    pkg_format, install_cmd, query_cmd = _detect_pkg_manager()
    distro_name = "Ubuntu/Debian/Linux Mint" if pkg_format == "deb" else "Fedora/RHEL"

    if _is_installed():
        print("Ghostty is already installed.")
        sys.exit(0)

    print("=" * 60)
    print("  Ghostty — A fast, native terminal emulator")
    print("  (ghostty.org)")
    print("=" * 60)
    print(f"  Detected: {distro_name} ({pkg_format})")
    print("=" * 60)
    print()

    success = _install_deb() if pkg_format == "deb" else _install_rpm()

    if success:
        print()
        print("Ghostty installed successfully!")
        print()
        print("To launch:  ghostty")
        print("Docs:       https://ghostty.org/docs")
        print("Config:     ~/.config/ghostty/config")
    else:
        print()
        print("Installation failed.")
        print()
        if pkg_format == "deb":
            print("Try manually:")
            print("  Method 1 (PPA):")
            print(
                '    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/mkasberg/ghostty-ubuntu/HEAD/install.sh)"'
            )
            print("  Method 2 (snap):")
            print("    sudo snap install ghostty --classic")
            print("  Method 3 (source):")
            print("    https://ghostty.org/docs/install/build")
        else:
            print("Try manually:")
            print("  Method 1 (COPR):")
            print("    sudo dnf copr enable scottames/ghostty")
            print("    sudo dnf install ghostty")
            print("  Method 2 (Terra):")
            print("    sudo dnf install --nogpgcheck \\")
            print(
                '      --repofrompath "terra,https://repos.fyralabs.com/terra$releasever" \\'
            )
            print("      terra-release")
            print("    sudo dnf install ghostty")
            print("  Method 3 (source):")
            print("    https://ghostty.org/docs/install/build")
        sys.exit(1)


if __name__ == "__main__":
    main()
