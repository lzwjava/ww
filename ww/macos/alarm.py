"""Set an alarm N minutes from now using macOS notification + Clock app.

Usage: ww macos alarm <minutes> [label]
Example: ww macos alarm 5 "eat"
"""

import subprocess
import sys
from datetime import datetime, timedelta


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww macos alarm <minutes> [label]")
        print()
        print("Set an alarm N minutes from now.")
        print("Opens the Clock app alarm tab and schedules a system notification.")
        print()
        print("Arguments:")
        print("  minutes   Minutes from now (e.g. 5, 1.5, 30)")
        print('  label     Optional label (e.g. "eat")')
        print()
        print("Examples:")
        print("  ww macos alarm 5          # alarm in 5 minutes")
        print('  ww macos alarm 5 "eat"    # alarm in 5 minutes, labeled "eat"')
        print("  ww macos alarm 0.5        # alarm in 30 seconds")
        return

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

    # Schedule a macOS notification that fires after the delay
    notif_title = f"Alarm: {label}" if label else "Alarm"
    notif_body = f"{dur_str} is up! ({time_str})"

    # Use a background subprocess to wait then fire notification
    # osascript can't schedule future notifications easily, so we use a
    # shell one-liner with sleep + osascript
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
