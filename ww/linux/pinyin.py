"""ww linux pinyin — Set up Chinese Pinyin input via IBus+libpinyin.

Usage: ww linux pinyin [--install]

Installs ibus-libpinyin if missing, registers it as the IBus engine,
sets GTK/QT/XMODIFIERS environment variables in ~/.bashrc, and restarts
ibus-daemon so the change takes effect in new terminal sessions.

After setup: press Ctrl+Space to toggle Chinese/English input.
"""

import os
import subprocess
import sys

HOME = os.path.expanduser("~")
BASHRC = os.path.join(HOME, ".bashrc")

IBUS_ENGINE = "libpinyin"
ENV_LINES = [
    "",
    "# Chinese input method (IBus+libpinyin) — set by ww linux pinyin",
    "export GTK_IM_MODULE=ibus",
    "export QT_IM_MODULE=ibus",
    "export XMODIFIERS=@im=ibus",
]


def _check_engine() -> bool:
    """Return True if libpinyin package is installed."""
    try:
        r = subprocess.run(
            ["dpkg", "-l", "ibus-libpinyin"],
            capture_output=True,
            text=True,
        )
        return r.returncode == 0 and "ii" in r.stdout
    except FileNotFoundError:
        return False


def _install_engine() -> bool:
    """Install ibus-libpinyin package via sudo. Returns True on success."""
    print("[pinyin] Installing ibus-libpinyin (sudo required)...")
    r = subprocess.run(
        ["sudo", "-n", "apt", "install", "-y", "ibus-libpinyin"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"[error] apt install failed:\n{r.stderr}")
        return False
    print(r.stdout[-500:] if r.stdout else "")
    return True


def _set_engine() -> bool:
    """Set the IBus engine to libpinyin. Returns True on success."""
    print("[pinyin] Registering libpinyin as IBus engine...")
    # Try gsettings first (works in GUI sessions)
    r = subprocess.run(
        [
            "gsettings",
            "set",
            "org.freedesktop.ibus.general",
            "preload-engines",
            "['libpinyin', 'xkb:us::eng']",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(
            "[pinyin] gsettings unavailable (non-GUI session), using dconf fallback..."
        )
        subprocess.run(
            [
                "dconf",
                "write",
                "/desktop/ibus/general/preload-engines",
                "['libpinyin', 'xkb:us::eng']",
            ],
            capture_output=True,
        )
    return True


def _ensure_env_vars() -> bool:
    """Add IM environment variables to ~/.bashrc if missing."""
    if not os.path.isfile(BASHRC):
        print(f"[warn] {BASHRC} not found, skipping env vars")
        return False

    with open(BASHRC) as f:
        content = f.read()

    if "XMODIFIERS=@im=ibus" in content:
        print("[pinyin] Environment variables already set in ~/.bashrc")
        return True

    with open(BASHRC, "a") as f:
        f.write("\n".join(ENV_LINES) + "\n")
    print("[pinyin] Added IM environment variables to ~/.bashrc")
    return True


def _restart_ibus_daemon() -> bool:
    """Ensure ibus-daemon is running. Start it if not already running."""
    # Check if daemon is running
    r = subprocess.run(
        ["pgrep", "-f", "ibus-daemon"],
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        print("[pinyin] ibus-daemon already running")
        return True

    print("[pinyin] Starting ibus-daemon...")
    subprocess.Popen(
        ["ibus-daemon", "--panel", "disable", "--xim"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("[pinyin] ibus-daemon started")
    return True


def run() -> None:
    """Main entry point for ww linux pinyin."""
    install = "--install" in sys.argv

    engine_ok = _check_engine()
    if not engine_ok:
        if install:
            if not _install_engine():
                sys.exit(1)
        else:
            print(
                "[pinyin] libpinyin engine not found. Run with --install to install it:"
            )
            print("  ww linux pinyin --install")
            sys.exit(1)

    _set_engine()
    _ensure_env_vars()
    _restart_ibus_daemon()

    print()
    print("[ok] Chinese Pinyin input is set up. New terminal sessions will have it.")
    print("     Press Ctrl+Space to toggle Chinese/English input.")
    print("     (If you're on SSH, Chinese input is handled on your client side.)")
