"""Clock.app alarm management.

Usage:
  ww alarm <minutes> [label]   Set an alarm N minutes from now
  ww alarm clear               Remove all alarms from the Clock app
  ww alarm list                List all alarms

Example:
  ww alarm 5 "eat"
  ww alarm clear
  ww alarm list
"""

import os
import plistlib
import subprocess
import sys
from datetime import datetime, timedelta

# Clock app alarm storage — plist is the source of truth on macOS 26+
_PLIST_PATH = os.path.expanduser("~/Library/Preferences/com.apple.mobiletimerd.plist")
# Legacy SQLite path (pre-26 macOS)
_DB_PATH = os.path.expanduser(
    "~/Library/Group Containers/group.com.apple.mobiletimerd/local.sqlite"
)


def _read_alarms_from_plist():
    """Read alarms from the mobiletimerd preferences plist."""
    if not os.path.exists(_PLIST_PATH):
        return None, None
    with open(_PLIST_PATH, "rb") as f:
        data = plistlib.load(f)
    alarms_section = data.get("MTAlarms", {})
    alarms = alarms_section.get("MTAlarms", [])
    return data, alarms


def _read_alarms_from_sqlite():
    """Read alarms from the legacy Core Data SQLite database."""
    if not os.path.exists(_DB_PATH):
        return []
    import sqlite3

    try:
        conn = sqlite3.connect(_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ZMTCDALARM")
        count = cursor.fetchone()[0]
        if count == 0:
            conn.close()
            return []
        cursor.execute("SELECT ZTITLE, ZHOUR, ZMINUTE, ZENABLED FROM ZMTCDALARM")
        rows = cursor.fetchall()
        conn.close()
        return [
            {"title": r[0], "hour": r[1], "minute": r[2], "enabled": bool(r[3])}
            for r in rows
        ]
    except Exception:
        return []


def _list_alarms():
    """List all alarms from plist and/or SQLite."""
    data, alarms = _read_alarms_from_plist()
    if alarms:
        print(f"Found {len(alarms)} alarm(s) (plist):")
        for a in alarms:
            alarm = a.get("$MTAlarm", a)
            h = alarm.get("MTAlarmHour", 0)
            m = alarm.get("MTAlarmMinute", 0)
            title = alarm.get("MTAlarmTitle", "(no label)")
            enabled = alarm.get("MTAlarmEnabled", True)
            status = "on" if enabled else "off"
            print(f"  {h:02d}:{m:02d}  {title}  [{status}]")
        return

    rows = _read_alarms_from_sqlite()
    if rows:
        print(f"Found {len(rows)} alarm(s) (sqlite):")
        for r in rows:
            label = r["title"] if r["title"] else "(no label)"
            status = "on" if r["enabled"] else "off"
            print(f"  {r['hour']:02d}:{r['minute']:02d}  {label}  [{status}]")
        return

    print("No alarms found.")


def _clear_all_alarms():
    """Remove all alarms from the Clock app.

    Tries the plist first (macOS 26+), falls back to SQLite (older macOS).
    Restarts mobiletimerd so the app picks up the changes.
    """
    # Try plist approach first
    data, alarms = _read_alarms_from_plist()
    if data is not None and alarms:
        count = len(alarms)
        # Show what we're removing
        print(f"Removing {count} alarm(s):")
        for a in alarms:
            alarm = a.get("$MTAlarm", a)
            h = alarm.get("MTAlarmHour", 0)
            m = alarm.get("MTAlarmMinute", 0)
            title = alarm.get("MTAlarmTitle", "(no label)")
            print(f"  {h:02d}:{m:02d}  {title}")

        # Clear the alarms array
        data["MTAlarms"]["MTAlarms"] = []
        with open(_PLIST_PATH, "wb") as f:
            plistlib.dump(data, f)

        # Restart mobiletimerd
        subprocess.run(["killall", "mobiletimerd"], capture_output=True)
        print(f"Done — {count} alarm(s) removed.")
        return

    # Fallback: try SQLite (older macOS)
    if not os.path.exists(_DB_PATH):
        print("Error: No alarm storage found (neither plist nor SQLite).")
        print("Make sure the Clock app has been opened at least once.")
        sys.exit(1)

    import sqlite3

    try:
        conn = sqlite3.connect(_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ZMTCDALARM")
        count = cursor.fetchone()[0]
        if count == 0:
            print("No alarms to clear.")
            conn.close()
            return
        cursor.execute("SELECT ZTITLE, ZHOUR, ZMINUTE FROM ZMTCDALARM")
        alarms = cursor.fetchall()
        cursor.execute("DELETE FROM ZMTCDALARM")
        conn.commit()
        conn.close()
        subprocess.run(["killall", "mobiletimerd"], capture_output=True)
        print(f"Cleared {count} alarm(s):")
        for title, hour, minute in alarms:
            label = title if title else "(no label)"
            print(f"  {hour:02d}:{minute:02d}  {label}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)


def _set_alarm(args):
    """Set an alarm N minutes from now."""
    try:
        minutes = float(args[0])
    except ValueError:
        print(f"Error: '{args[0]}' is not a valid number of minutes.")
        sys.exit(1)

    if minutes <= 0:
        print("Error: minutes must be positive.")
        sys.exit(1)

    label = args[1] if len(args) > 1 else ""

    total_seconds = minutes * 60
    target = datetime.now() + timedelta(seconds=total_seconds)
    time_str = target.strftime("%H:%M")

    h = int(total_seconds) // 3600
    m = (int(total_seconds) % 3600) // 60
    s = int(total_seconds) % 60
    if h > 0:
        dur_str = f"{h}h{m:02d}m{s:02d}s"
    elif m > 0:
        dur_str = f"{m}m{s:02d}s"
    else:
        dur_str = f"{s}s"

    notif_title = f"Alarm: {label}" if label else "Alarm"
    notif_body = f"{dur_str} is up! ({time_str})"

    script = (
        f"sleep {total_seconds} && "
        f'osascript -e \'display notification "{notif_body}" '
        f'with title "{notif_title}" sound name "default"\''
    )
    subprocess.Popen(
        ["bash", "-c", script],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Also open the Clock app alarm tab
    subprocess.run(["open", "clock-alarm://"], check=False)

    print(f"Alarm set for {time_str} (in {dur_str})", end="")
    if label:
        print(f'  label: "{label}"')
    else:
        print()


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww alarm <minutes> [label]")
        print("       ww alarm clear")
        print("       ww alarm list")
        print()
        print("Manage Clock.app alarms.")
        print()
        print("Commands:")
        print("  <minutes> [label]  Set an alarm N minutes from now")
        print("  clear              Remove all alarms from the Clock app")
        print("  list               List all alarms")
        print()
        print("Examples:")
        print("  ww alarm 5          # alarm in 5 minutes")
        print('  ww alarm 5 "eat"    # alarm in 5 minutes, labeled "eat"')
        print("  ww alarm 0.5        # alarm in 30 seconds")
        print("  ww alarm clear      # delete all alarms")
        print("  ww alarm list       # show all alarms")
        return

    if args[0] == "clear":
        _clear_all_alarms()
    elif args[0] == "list":
        _list_alarms()
    else:
        _set_alarm(args)
