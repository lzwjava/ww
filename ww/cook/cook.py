"""Cooking timer with crontab-based recurring notifications.

Usage:
  ww cook <minutes>     Set a cooking timer for N minutes
  ww cook clear         Clear the cooking timer

When the timer expires, a macOS notification fires every 2 minutes
until 'ww cook clear' is run, using a system crontab entry.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time

_STATE_FILE = os.path.expanduser("~/.ww/cook.state")
_CRONTAB_MARKER = "# ww-cook-timer"


def _get_ww_path() -> str:
    """Find the ww CLI binary path."""
    ww = shutil.which("ww")
    if ww:
        return ww
    # Fallback for common locations
    for p in [
        "/opt/homebrew/bin/ww",
        "/usr/local/bin/ww",
        os.path.expanduser("~/.local/bin/ww"),
    ]:
        if os.path.exists(p):
            return p
    # Last resort: try uv run
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return f"cd {project_root} && uv run ww"


def _send_notification(message: str, title: str = "🍳 Cooking Timer"):
    """Send a macOS notification via osascript."""
    script = f'display notification "{message}" with title "{title}" sound name "Basso"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def _get_crontab() -> str:
    """Get current crontab content."""
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout


def _set_crontab(content: str):
    """Write crontab content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        tmp_path = f.name
    try:
        subprocess.run(["crontab", tmp_path], check=True, capture_output=True)
    finally:
        os.unlink(tmp_path)


def _add_cron_entry():
    """Add the minute-tick cron entry if not already present."""
    ww_path = _get_ww_path()
    cron_line = f"* * * * * {ww_path} cook _tick {_CRONTAB_MARKER}"

    current = _get_crontab()
    if _CRONTAB_MARKER in current:
        return  # already added

    if current and not current.endswith("\n"):
        current += "\n"
    current += cron_line + "\n"
    _set_crontab(current)


def _remove_cron_entry():
    """Remove the cook-timer cron entry(s)."""
    current = _get_crontab()
    lines = [ln for ln in current.splitlines() if _CRONTAB_MARKER not in ln]
    _set_crontab("\n".join(lines) + ("\n" if lines else ""))


def _tick():
    """Called every minute by crontab. Checks state and notifies if needed."""
    if not os.path.exists(_STATE_FILE):
        # State file gone — clean up crontab entry
        _remove_cron_entry()
        return

    state = {}
    with open(_STATE_FILE) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                state[k] = int(v)

    now = int(time.time())
    end_time = state.get("end_time", 0)
    last_notified = state.get("last_notified", 0)

    if now < end_time:
        return  # not yet expired

    # Notify every 2 minutes (120 seconds) after expiry
    if now - last_notified >= 120:
        minutes_over = (now - end_time) // 60
        msg = f"Cooking timer expired! {minutes_over} min ago — check the stove!"
        _send_notification(msg)
        state["last_notified"] = now
        with open(_STATE_FILE, "w") as f:
            f.write(f"end_time={end_time}\n")
            f.write(f"last_notified={now}\n")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww cook <minutes>")
        print("       ww cook clear")
        print()
        print("Set a cooking timer. When the timer expires,")
        print("a macOS notification fires every 2 minutes until cleared.")
        print()
        print("Commands:")
        print("  <minutes>  Set a cooking timer for N minutes")
        print("  clear      Clear the cooking timer and stop notifications")
        print()
        print("Examples:")
        print("  ww cook 20   # 20-minute timer")
        print("  ww cook 45   # 45-minute timer")
        return

    if args[0] == "clear":
        _remove_cron_entry()
        if os.path.exists(_STATE_FILE):
            os.unlink(_STATE_FILE)
        print("🍳 Cooking timer cleared.")
        return

    if args[0] == "_tick":
        _tick()
        return

    # Set timer
    try:
        minutes = float(args[0])
    except ValueError:
        print(f"Error: '{args[0]}' is not a valid number of minutes.")
        sys.exit(1)

    if minutes <= 0:
        print("Error: minutes must be positive.")
        sys.exit(1)

    # Calculate end timestamp (seconds since epoch)
    end_time = int(time.time() + minutes * 60)

    # Write state
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)
    with open(_STATE_FILE, "w") as f:
        f.write(f"end_time={end_time}\n")
        f.write("last_notified=0\n")

    # Add crontab entry
    _add_cron_entry()

    # Format duration for display
    total_seconds = int(minutes * 60)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        dur_str = f"{h}h{m:02d}m"
    elif m > 0:
        dur_str = f"{m}m"
    else:
        dur_str = f"{s}s"
    end_str = time.strftime("%H:%M", time.localtime(end_time))
    print(f"🍳 Cooking timer set for {dur_str} (ends at {end_str})")
    print("   You'll be notified every 2 minutes after it expires.")
    print("   Run 'ww cook clear' to stop.")
