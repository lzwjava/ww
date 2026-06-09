"""Clock.app alarm management.

Usage:
  ww alarm <minutes> [label]   Set an alarm N minutes from now
  ww alarm list                Open Clock.app to show alarms

Example:
  ww alarm 5 "eat"
  ww alarm list
"""

import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

_SHORTCUT_NAME = "ww-create-alarm-signed"


def _list_alarms():
    """Open Clock.app to the Alarms tab."""
    subprocess.run(["open", "-a", "Clock"], capture_output=True)
    print("Clock.app opened — check the Alarms tab.")


def _set_alarm(args):
    """Set an alarm N minutes from now via a Shortcuts.app workflow.

    Requires the 'ww-create-alarm-signed' shortcut in Shortcuts.app with:
      1. Receive text input from Shortcuts (type: Text)
      2. Split Text — separator: Custom "|"
      3. Get Item from List — index 1 (time "HH:MM")
      4. Date — parse "Item from List" as Date
      5. Get Item from List — index 2 (label)
      6. Create Alarm — time: Date, label: "Item from List"
    """
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

    # Send pipe-separated: "HH:MM|label"
    input_text = f"{time_str}|{label}" if label else f"{time_str}|"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ww-alarm-"
    ) as f:
        f.write(input_text)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["shortcuts", "run", _SHORTCUT_NAME, "--input-path", tmp_path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "not found" in stderr.lower() or "couldn't find" in stderr.lower():
                print(f"Error: Shortcut '{_SHORTCUT_NAME}' not found in Shortcuts.app.")
                print("Create it with a 'Create Alarm' action that accepts text input.")
                sys.exit(1)
            print(f"Shortcut error: {stderr}")
            sys.exit(1)
    finally:
        os.unlink(tmp_path)

    print(f"Alarm set for {time_str} (in {dur_str})", end="")
    if label:
        print(f'  label: "{label}"')
    else:
        print()


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww alarm <minutes> [label]")
        print("       ww alarm list")
        print()
        print("Manage Clock.app alarms via Shortcuts.app.")
        print()
        print("Commands:")
        print("  <minutes> [label]  Set an alarm N minutes from now")
        print("  list               Open Clock.app to show alarms")
        print()
        print("Examples:")
        print("  ww alarm 5          # alarm in 5 minutes")
        print('  ww alarm 5 "eat"    # alarm in 5 minutes, labeled "eat"')
        print("  ww alarm 0.5        # alarm in 30 seconds")
        print("  ww alarm list       # show all alarms in Clock.app")
        print()
        print(f"Requires shortcut '{_SHORTCUT_NAME}' in Shortcuts.app.")
        return

    if args[0] == "list":
        _list_alarms()
    else:
        _set_alarm(args)
