"""ww linux screen-lock — control the Ubuntu/GNOME idle screen lock.

Usage:
    ww linux screen-lock                 # show current settings
    ww linux screen-lock status          # same as above
    ww linux screen-lock delay           # lock 2h after the screen blanks
    ww linux screen-lock delay 30m       # lock 30m after the screen blanks
    ww linux screen-lock off             # stop locking after idle
    ww linux screen-lock on              # re-enable the automatic lock
    ww linux screen-lock blank 3h        # idle time before the screen blanks
    ww linux screen-lock blank never     # never blank the screen
    ww linux screen-lock suspend-pw off  # no password after waking from suspend
    ww linux screen-lock lockdown on     # disable the lock screen entirely

Time format: 2h, 30m, 45s, 1h30m, or plain seconds (7200).
`never` / `off` / `0` means "no delay" (used by `blank`).
"""

import re
import shutil
import subprocess
import sys
from typing import NoReturn

SCREENSAVER = "org.gnome.desktop.screensaver"
SESSION = "org.gnome.desktop.session"
LOCKDOWN = "org.gnome.desktop.lockdown"

DEFAULT_DELAY = 2 * 3600  # 2 hours

_TIME_RE = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$", re.IGNORECASE)


# ── gsettings helpers ──────────────────────────────────────────────────────────


def _gs(args: list[str]) -> tuple[str, int]:
    """Run `gsettings <args>`, return (stdout, exit_code)."""
    try:
        r = subprocess.run(
            ["gsettings", *args], capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip(), r.returncode
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "", 1


def _require() -> None:
    """Exit with an error if gsettings / GNOME schemas are unavailable."""
    if not shutil.which("gsettings"):
        print("Error: gsettings not found.")
        print("       This command only works on GNOME (Ubuntu's default desktop).")
        sys.exit(1)
    out, rc = _gs(["list-schemas"])
    if rc != 0 or SCREENSAVER not in out.splitlines():
        print("Error: GNOME screensaver schema not found.")
        print("       This command only works on GNOME (Ubuntu's default desktop).")
        sys.exit(1)


def _get(schema: str, key: str) -> str | None:
    out, rc = _gs(["get", schema, key])
    return out if rc == 0 else None


def _set(schema: str, key: str, value: str) -> bool:
    _, rc = _gs(["set", schema, key, value])
    return rc == 0


def _get_bool(schema: str, key: str) -> bool | None:
    raw = _get(schema, key)
    if raw is None:
        return None
    return raw == "true"


def _get_int(schema: str, key: str) -> int | None:
    raw = _get(schema, key)
    if raw is None:
        return None
    # Values come back as "uint32 7200", "int32 0", or plain "0".
    try:
        return int(raw.split()[-1])
    except ValueError:
        return None


# ── time parsing / formatting ─────────────────────────────────────────────────


def _parse_time(text: str) -> int | None:
    """Parse '2h', '1h30m', '45s', '7200' (seconds) or 'never'/'off'/'0' -> 0."""
    t = text.strip().lower()
    if not t:
        return None
    if t in ("never", "none", "off"):
        return 0
    if t.isdigit():
        return int(t)
    m = _TIME_RE.match(t)
    if m and any(m.groups()):
        h, mo, s = (int(g) if g else 0 for g in m.groups())
        return h * 3600 + mo * 60 + s
    return None


def _fmt_time(secs: int) -> str:
    """Format seconds as '2h', '1h 30m', '45s', or 'never' for 0."""
    if secs == 0:
        return "never"
    parts: list[str] = []
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s:
        parts.append(f"{s}s")
    return " ".join(parts)


def _yn(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "on" if value else "off"


def _bad_time(text: str) -> NoReturn:
    print(f"Error: cannot parse time: {text}")
    print("       Use 2h, 30m, 45s, 1h30m, plain seconds (7200), or 'never'.")
    sys.exit(1)


# ── commands ──────────────────────────────────────────────────────────────────


def _status() -> None:
    lock = _get_bool(SCREENSAVER, "lock-enabled")
    delay = _get_int(SCREENSAVER, "lock-delay")
    idle = _get_int(SESSION, "idle-delay")
    suspend = _get_bool(SCREENSAVER, "ubuntu-lock-on-suspend")
    lockdown = _get_bool(LOCKDOWN, "disable-lock-screen")

    print("Screen lock (Ubuntu/GNOME):")
    print(f"  Automatic screen lock : {_yn(lock)}")
    if lock and delay is not None:
        if delay == 0:
            print("                          (locks as soon as the screen blanks)")
        else:
            print(f"                          (locks {_fmt_time(delay)} after blank)")
    if idle is None:
        print("  Blank screen delay    : unknown")
    elif idle == 0:
        print("  Blank screen delay    : never (screen stays on)")
    else:
        print(f"  Blank screen delay    : {_fmt_time(idle)} of inactivity")
    if suspend is not None:
        print(f"  Password after suspend: {_yn(suspend)}")
    if lockdown:
        print("  Lockdown              : lock screen disabled (Super+L too)")

    print()
    if lock and idle == 0:
        print("Note: the screen never blanks, so the idle lock will never trigger.")
        print("      Run `ww linux screen-lock blank 10m` to enable idle locking.")
    elif lock and delay:
        print("Note: the lock delay counts from when the screen blanks")
        if idle:
            print(f"      (after {_fmt_time(idle)} of inactivity).")
        elif idle is None:
            print("      (blank delay unknown).")
        else:
            print("      (the screen never blanks, so it never triggers).")
        print("      For a lock N hours after idle instead, set 'blank <time>'")
        print("      and keep 'delay 0s'.")

    print()
    print("Usage:")
    print("  ww linux screen-lock delay [time]   Lock after a delay (default 2h)")
    print("  ww linux screen-lock off            Stop locking after idle")
    print("  ww linux screen-lock on             Re-enable the automatic lock")
    print("  ww linux screen-lock blank [time]   Idle time before blanking")
    print("  ww linux screen-lock suspend-pw on|off  Password after wake from suspend")
    print("  ww linux screen-lock lockdown on|off    Disable the lock screen entirely")


def _set_delay(secs: int) -> None:
    if not _set(SCREENSAVER, "lock-enabled", "true"):
        print("Error: failed to enable the automatic screen lock.")
        sys.exit(1)
    if not _set(SCREENSAVER, "lock-delay", str(secs)):
        print("Error: failed to set the lock delay.")
        sys.exit(1)

    idle = _get_int(SESSION, "idle-delay")
    print("Automatic screen lock: on")
    if secs == 0:
        print("Lock delay: locks as soon as the screen blanks")
    else:
        print(f"Lock delay: {_fmt_time(secs)} after the screen blanks")

    if idle == 0:
        print()
        print("Warning: the screen is set to never blank, so this lock will never")
        print("         trigger. Run `ww linux screen-lock blank 10m` to fix that.")
    elif idle:
        print()
        print(f"Screen blanks after {_fmt_time(idle)} of inactivity, then locks")
        print(f"{_fmt_time(idle + secs)} after going idle.")


def _enable_lock() -> None:
    if not _set(SCREENSAVER, "lock-enabled", "true"):
        print("Error: failed to enable the automatic screen lock.")
        sys.exit(1)
    delay = _get_int(SCREENSAVER, "lock-delay") or 0
    print("Automatic screen lock: on")
    if delay:
        print(f"Lock delay: {_fmt_time(delay)} after the screen blanks")
    else:
        print("Lock delay: locks as soon as the screen blanks")


def _disable_lock() -> None:
    if not _set(SCREENSAVER, "lock-enabled", "false"):
        print("Error: failed to disable the automatic screen lock.")
        sys.exit(1)
    print("Automatic screen lock: off (no lock after idle)")
    print()
    print("Note: the password after waking from suspend is a separate setting:")
    print("  ww linux screen-lock suspend-pw off")
    print("A password after reboot/logout comes from the login screen")
    print("(Settings -> System -> Users -> Automatic Login), not from here.")


def _blank(text: str | None) -> None:
    if text is None:
        idle = _get_int(SESSION, "idle-delay")
        if idle is None:
            print("Blank screen delay: unknown")
        elif idle == 0:
            print("Blank screen delay: never (screen stays on)")
        else:
            print(f"Blank screen delay: {_fmt_time(idle)} of inactivity")
        print()
        print("Usage: ww linux screen-lock blank <time|never>")
        return

    secs = _parse_time(text)
    if secs is None:
        _bad_time(text)
    if not _set(SESSION, "idle-delay", str(secs)):
        print("Error: failed to set the blank screen delay.")
        sys.exit(1)
    if secs == 0:
        print("Blank screen delay: never (screen stays on)")
        print("Note: idle locking never triggers if the screen never blanks.")
    else:
        print(f"Blank screen delay: {_fmt_time(secs)} of inactivity")


def _suspend_pw(arg: str | None) -> None:
    if arg not in ("on", "off"):
        print("Usage: ww linux screen-lock suspend-pw on|off")
        sys.exit(1)
    if _get(SCREENSAVER, "ubuntu-lock-on-suspend") is None:
        print("Error: 'ubuntu-lock-on-suspend' is not available on this system.")
        sys.exit(1)
    value = "true" if arg == "on" else "false"
    if not _set(SCREENSAVER, "ubuntu-lock-on-suspend", value):
        print("Error: failed to update the suspend password setting.")
        sys.exit(1)
    if arg == "on":
        print("Password after wake from suspend: on")
    else:
        print("Password after wake from suspend: off")


def _lockdown(arg: str | None) -> None:
    if arg not in ("on", "off"):
        print("Usage: ww linux screen-lock lockdown on|off")
        sys.exit(1)
    if not _set(LOCKDOWN, "disable-lock-screen", "true" if arg == "on" else "false"):
        print("Error: failed to update the lockdown setting.")
        sys.exit(1)
    if arg == "on":
        print("Lock screen disabled system-wide (including the Super+L shortcut).")
    else:
        print("Lock screen re-enabled system-wide.")


def _help() -> None:
    print("Usage: ww linux screen-lock [command] [options]")
    print()
    print("Commands:")
    print("  status                 Show current screen-lock settings (default)")
    print("  delay [time]           Lock [time] after the screen blanks (default 2h)")
    print("  on                     Turn the automatic screen lock on")
    print("  off                    Turn the automatic screen lock off")
    print("  blank [time|never]     Idle time before the screen blanks")
    print("  suspend-pw on|off      Ask for a password when waking from suspend")
    print("  lockdown on|off        Disable the lock screen entirely (drastic)")
    print("  help                   Show this help")
    print()
    print("Time format: 2h, 30m, 45s, 1h30m, or plain seconds (7200).")
    print("'never' / 'off' / '0' means no delay (used by 'blank').")


# ── entry point ───────────────────────────────────────────────────────────────


def run() -> None:
    """Entry point for `ww linux screen-lock`."""
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "status"
    arg = argv[1] if len(argv) > 1 else None

    if cmd in ("--help", "-h", "help"):
        _help()
        return

    _require()

    if cmd == "status":
        _status()
    elif cmd == "delay":
        text = arg if arg is not None else "2h"
        secs = _parse_time(text)
        if secs is None:
            _bad_time(text)
        _set_delay(secs)
    elif cmd == "on":
        _enable_lock()
    elif cmd == "off":
        _disable_lock()
    elif cmd == "blank":
        _blank(arg)
    elif cmd == "suspend-pw":
        _suspend_pw(arg)
    elif cmd == "lockdown":
        _lockdown(arg)
    else:
        print(f"Unknown screen-lock command: {cmd}")
        _help()
        sys.exit(1)
