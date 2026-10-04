"""Toggle Caps Lock <-> Left Ctrl swap.

Works on Ubuntu (GNOME via gsettings, both Wayland and X11) and falls back
to setxkbmap for plain X11 sessions.

Usage:
    ww keyboard capslock-ctrl           # toggle on/off
    ww keyboard capslock-ctrl on        # force swap on
    ww keyboard capslock-ctrl off       # force swap off
    ww keyboard capslock-ctrl status    # show current state
"""

import ast
import subprocess
import sys

SWAP_OPTION = "ctrl:swapcaps"
GSETTINGS_SCHEMA = "org.gnome.desktop.input-sources"


def _run(cmd: str) -> tuple[str, int]:
    """Run a shell command, return (stdout, exit_code)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", 1
    except FileNotFoundError:
        return "", 127


# ── GNOME / gsettings (Ubuntu default: works on Wayland and X11) ───────────────


def _gsettings_get() -> list[str] | None:
    """Return the current xkb-options list, or None if gsettings is unavailable."""
    out, rc = _run(f"gsettings get {GSETTINGS_SCHEMA} xkb-options")
    if rc != 0:
        return None
    text = out.strip()
    # Newer glib prefixes the value with the type, e.g. "@as []".
    if text.startswith("@"):
        _, _, text = text.partition(" ")
    try:
        parsed = ast.literal_eval(text)
        return parsed if isinstance(parsed, list) else None
    except (ValueError, SyntaxError):
        return None


def _gsettings_set(opts: list[str]) -> bool:
    """Write the xkb-options list. Returns True on success."""
    if opts:
        inner = ", ".join(f"'{o}'" for o in opts)
        value = f"[{inner}]"
    else:
        value = "[]"
    _, rc = _run(f'gsettings set {GSETTINGS_SCHEMA} xkb-options "{value}"')
    return rc == 0


# ── plain X11 fallback (setxkbmap) ─────────────────────────────────────────────


def _x11_get() -> list[str] | None:
    """Return current setxkbmap options, or None if setxkbmap is unavailable."""
    out, rc = _run("setxkbmap -query")
    if rc != 0:
        return None
    for line in out.splitlines():
        if line.startswith("options:"):
            opts = line.split(":", 1)[1].strip()
            return [o for o in opts.split(",") if o] if opts else []
    return []


def _x11_set(opts: list[str]) -> bool:
    if opts:
        _, rc = _run("setxkbmap -option " + ",".join(opts))
    else:
        _, rc = _run("setxkbmap -option")
    return rc == 0


# ── core ───────────────────────────────────────────────────────────────────────


def _current_options() -> list[str]:
    """Best-effort current xkb options from gsettings, then setxkbmap."""
    opts = _gsettings_get()
    if opts is not None:
        return opts
    opts = _x11_get()
    if opts is not None:
        return opts
    print("Error: could not read keyboard options.")
    print("       Requires gsettings (GNOME) or setxkbmap (X11).")
    sys.exit(1)


def _apply(opts: list[str]) -> None:
    """Write options via gsettings first, falling back to setxkbmap."""
    if _gsettings_get() is not None:
        if _gsettings_set(opts):
            return
        print("Warning: gsettings write failed, trying setxkbmap...")
    if _x11_set(opts):
        return
    print("Error: could not write keyboard options.")
    sys.exit(1)


def _has_swap(opts: list[str]) -> bool:
    return SWAP_OPTION in opts


def _print_status(has_swap: bool) -> None:
    state = (
        "ON (Caps Lock and Left Ctrl are swapped)"
        if has_swap
        else "OFF (default layout)"
    )
    print(f"Caps Lock <-> Ctrl swap: {state}")


def _usage() -> None:
    print("Usage: ww keyboard capslock-ctrl [on|off|status]")
    print("")
    print("  (no args)   Toggle the Caps Lock <-> Ctrl swap")
    print("  on          Force the swap on")
    print("  off         Force the swap off")
    print("  status      Show the current state")


def run() -> None:
    """Entry point for `ww keyboard capslock-ctrl`."""
    argv = sys.argv[1:]
    mode = argv[0] if argv else "toggle"

    if mode in ("--help", "-h", "help"):
        _usage()
        return
    if mode not in ("toggle", "on", "off", "status"):
        print(f"Unknown argument: {mode}")
        _usage()
        sys.exit(1)

    opts = _current_options()
    has_swap = _has_swap(opts)

    if mode == "status":
        _print_status(has_swap)
        return

    if mode == "toggle":
        target_swap = not has_swap
    elif mode == "on":
        target_swap = True
    else:  # off
        target_swap = False

    if target_swap == has_swap:
        _print_status(has_swap)
        print("Nothing to do.")
        return

    new_opts = list(opts)
    if target_swap and SWAP_OPTION not in new_opts:
        new_opts.append(SWAP_OPTION)
    elif not target_swap:
        new_opts = [o for o in new_opts if o != SWAP_OPTION]

    _apply(new_opts)

    if target_swap:
        print("Caps Lock <-> Ctrl swap: ENABLED")
    else:
        print("Caps Lock <-> Ctrl swap: DISABLED (back to default)")
