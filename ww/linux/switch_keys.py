"""ww linux switch-keys — swap Caps Lock and Left Ctrl on X11 (Linux Mint)."""

import argparse
import os
import subprocess
import sys


def _run(cmd: str) -> tuple[str, int]:
    """Run a shell command, return (stdout, exit_code)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", 1
    except FileNotFoundError:
        return "", 127


def _is_x11() -> bool:
    """Check if we're running under X11."""
    return os.environ.get("XDG_SESSION_TYPE") == "x11" or bool(
        os.environ.get("DISPLAY")
    )


# ── state detection ────────────────────────────────────────────────────────────


def _setxkbmap_has_swap() -> bool:
    """Check if ctrl:swapcaps is active via setxkbmap."""
    out, _ = _run("setxkbmap -query")
    for line in out.splitlines():
        if line.startswith("options") and "ctrl:swapcaps" in line:
            return True
    return False


def _xmodmap_has_swap() -> bool:
    """Check if the live xmodmap has swapped caps/ctrl."""
    out, rc = _run("xmodmap -pke")
    if rc != 0:
        return False
    found_kc66 = False
    found_kc37 = False
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            try:
                kc = int(parts[1])
            except ValueError:
                continue
            rest = " ".join(parts[2:])
            if kc == 66 and "Control" in rest:
                found_kc66 = True
            if kc == 37 and "Caps" in rest:
                found_kc37 = True
    return found_kc66 and found_kc37


def _xmodmap_file_has_swap() -> bool:
    """Check if ~/.Xmodmap contains the swap."""
    path = os.path.expanduser("~/.Xmodmap")
    if not os.path.isfile(path):
        return False
    with open(path) as f:
        content = f.read()
    return "keycode 66 = Control_L" in content and "keycode 37 = Caps_Lock" in content


def _detect_state() -> str:
    """Return 'on', 'off', or 'unknown'."""
    if not _is_x11():
        return "unknown"
    # Check live state first (both setxkbmap and xmodmap can apply it)
    if _setxkbmap_has_swap() or _xmodmap_has_swap():
        return "on"
    return "off"


# ── apply / revert ─────────────────────────────────────────────────────────────


def _enable_swap() -> None:
    """Apply the Caps Lock ↔ Ctrl swap at runtime."""
    _run("setxkbmap -option ctrl:swapcaps")
    print("  ✓ Caps Lock ↔ Left Ctrl swap enabled (runtime)")


def _disable_swap() -> None:
    """Revert Caps Lock ↔ Ctrl to default at runtime."""
    # Remove the swapcaps option and re-apply base options
    _run("setxkbmap -option")  # clear all options
    _run("setxkbmap -option terminate:ctrl_alt_bksp")  # restore preferred option
    # Reset xmodmap if it was loaded
    _run("xmodmap -e 'keycode 66 = Caps_Lock' -e 'keycode 37 = Control_L' 2>/dev/null")
    print("  ✓ Caps Lock ↔ Ctrl swap disabled (runtime)")


# ── persistence ────────────────────────────────────────────────────────────────

XMODMAP_PATH = os.path.expanduser("~/.Xmodmap")
XPROFILE_PATH = os.path.expanduser("~/.xprofile")

_XMODMAP_SWAP = """\
! Swap Caps Lock and Left Control — keycode-based approach
keycode 66 = Control_L
keycode 37 = Caps_Lock
clear Lock
clear Control
add Lock = Caps_Lock
add Control = Control_L"""

_XPROFILE_SWAP = """\
#!/bin/sh
# Swap Caps Lock and Left Control
setxkbmap -option ctrl:swapcaps
"""


def _install_persist() -> None:
    """Write ~/.Xmodmap and ensure ~/.xprofile loads it."""
    # Write Xmodmap
    with open(XMODMAP_PATH, "w") as f:
        f.write(_XMODMAP_SWAP)
    print(f"  ✓ Written {XMODMAP_PATH}")

    # Write or update .xprofile to load Xmodmap
    existing_xprofile = ""
    if os.path.isfile(XPROFILE_PATH):
        with open(XPROFILE_PATH) as f:
            existing_xprofile = f.read()

    if "xmodmap" not in existing_xprofile and "ctrl:swapcaps" not in existing_xprofile:
        with open(XPROFILE_PATH, "a") as f:
            if existing_xprofile and not existing_xprofile.endswith("\n"):
                f.write("\n")
            f.write("# Load Caps Lock ↔ Ctrl swap\n")
            f.write("[ -f ~/.Xmodmap ] && xmodmap ~/.Xmodmap\n")
        print(f"  ✓ Appended xmodmap load to {XPROFILE_PATH}")
    elif (
        "xmodmap ~/.Xmodmap" in existing_xprofile
        or "ctrl:swapcaps" in existing_xprofile
    ):
        print(f"  ✓ {XPROFILE_PATH} already loads the swap (no change)")


def _remove_persist() -> None:
    """Remove ~/.Xmodmap and clean up .xprofile."""
    removed: list[str] = []
    if os.path.isfile(XMODMAP_PATH):
        os.remove(XMODMAP_PATH)
        removed.append(f"  ✓ Removed {XMODMAP_PATH}")

    # Remove xmodmap lines from .xprofile
    if os.path.isfile(XPROFILE_PATH):
        with open(XPROFILE_PATH) as f:
            lines = f.readlines()
        filtered = []
        skipping = False
        for line in lines:
            stripped = line.strip()
            if stripped == "# Load Caps Lock ↔ Ctrl swap":
                skipping = True
                continue
            if skipping and "xmodmap ~/.Xmodmap" in stripped:
                skipping = False
                continue
            if skipping:
                skipping = False
                continue
            if "ctrl:swapcaps" in stripped and ("setxkbmap" in stripped):
                continue
            filtered.append(line)
        with open(XPROFILE_PATH, "w") as f:
            f.writelines(filtered)
        removed.append(f"  ✓ Cleaned swap lines from {XPROFILE_PATH}")

    if not removed:
        print("  No persistent config found, nothing to remove.")
    else:
        for msg in removed:
            print(msg)


# ── interactive ────────────────────────────────────────────────────────────────


def _prompt_yn(question: str) -> bool:
    """Ask a yes/no question, return True for yes."""
    answer = input(f"{question} (y/N): ").strip().lower()
    return answer == "y"


# ── main ───────────────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Swap Caps Lock and Left Control keys on X11 (Linux Mint).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "state",
        nargs="?",
        choices=["on", "off"],
        help="'on' to swap Caps ↔ Ctrl, 'off' to revert to default",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist the setting across reboots via ~/.Xmodmap and ~/.xprofile",
    )
    return parser.parse_args()


def run() -> None:
    """Entry point for `ww linux switch-keys`."""
    args = _parse_args()

    if not _is_x11():
        print("Error: not running under X11. This command only supports X11 sessions.")
        sys.exit(1)

    current = _detect_state()

    # ── show current state ──────────────────────────────────────────────────
    if args.state is None:
        print(f"Caps Lock ↔ Ctrl swap: {current.upper()}")
        print()
        if current == "on":
            print("Active via:", end=" ")
            sources: list[str] = []
            if _setxkbmap_has_swap():
                sources.append("setxkbmap option (ctrl:swapcaps)")
            if _xmodmap_has_swap():
                sources.append("xmodmap (live)")
            if _xmodmap_file_has_swap():
                sources.append("~/.Xmodmap (persistent)")
            print(", ".join(sources) if sources else "unknown")
            print()
            print("Usage:")
            print("  ww linux switch-keys off          Revert to default")
            print("  ww linux switch-keys off --persist Revert and remove persistence")
        else:
            print("Usage:")
            print("  ww linux switch-keys on            Enable swap (runtime)")
            print(
                "  ww linux switch-keys on --persist  Enable and persist across reboots"
            )
        return

    # ── sanity check: already in requested state ────────────────────────────
    if args.state == current:
        extra = " (and persisted)" if args.persist and _xmodmap_file_has_swap() else ""
        print(f"Caps Lock ↔ Ctrl swap is already {current}{extra}.")
        print("Nothing to do.")
        return

    # ── enable ──────────────────────────────────────────────────────────────
    if args.state == "on":
        _enable_swap()
        if args.persist:
            _install_persist()
        elif _prompt_yn("Also persist this setting across reboots?"):
            _install_persist()
        return

    # ── disable ─────────────────────────────────────────────────────────────
    if args.state == "off":
        _disable_swap()
        if args.persist:
            _remove_persist()
        elif os.path.isfile(XMODMAP_PATH) or os.path.isfile(XPROFILE_PATH):
            if _prompt_yn("Also remove persistent config (~/.Xmodmap)?"):
                _remove_persist()
        return
