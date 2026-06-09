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
import sqlite3
import subprocess
import sys
import uuid as _uuid
from datetime import datetime, timedelta

_DB_PATH = os.path.expanduser(
    "~/Library/Group Containers/group.com.apple.mobiletimerd/local.sqlite"
)

# Core Data entity IDs
_ENT_ALARM = 4  # MTCDAlarm
_ENT_SOUND = 5  # MTCDSound


def _connect():
    if not os.path.exists(_DB_PATH):
        print("Error: Clock.app database not found. Open the Clock app at least once.")
        sys.exit(1)
    return sqlite3.connect(_DB_PATH)


def _list_alarms():
    """List all alarms from the SQLite database."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT Z_PK, ZENABLED, ZHOUR, ZMINUTE, ZTITLE FROM ZMTCDALARM ORDER BY Z_PK"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No alarms found.")
        return

    print(f"Found {len(rows)} alarm(s):")
    for pk, enabled, h, m, title in rows:
        label = title if title else "(no label)"
        status = "on" if enabled else "off"
        print(f"  {h:02d}:{m:02d}  {label}  [{status}]")


def _clear_all_alarms():
    """Remove all alarms from the Clock.app SQLite database."""
    conn = _connect()
    cur = conn.cursor()

    cur.execute("SELECT ZTITLE, ZHOUR, ZMINUTE FROM ZMTCDALARM")
    alarms = cur.fetchall()
    if not alarms:
        print("No alarms to clear.")
        conn.close()
        return

    count = len(alarms)
    print(f"Removing {count} alarm(s):")
    for title, h, m in alarms:
        label = title if title else "(no label)"
        print(f"  {h:02d}:{m:02d}  {label}")

    # Delete sound entries that reference alarms, then alarms themselves
    cur.execute("DELETE FROM ZMTCDSOUND WHERE ZALARM IN (SELECT Z_PK FROM ZMTCDALARM)")
    cur.execute("DELETE FROM ZMTCDALARM")
    conn.commit()
    conn.close()

    subprocess.run(["killall", "mobiletimerd"], capture_output=True)
    print(f"Done — {count} alarm(s) removed.")


def _set_alarm(args):
    """Set an alarm N minutes from now by writing to the Clock.app SQLite DB."""
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
    hour = target.hour
    minute = target.minute

    h = int(total_seconds) // 3600
    m = (int(total_seconds) % 3600) // 60
    s = int(total_seconds) % 60
    if h > 0:
        dur_str = f"{h}h{m:02d}m{s:02d}s"
    elif m > 0:
        dur_str = f"{m}m{s:02d}s"
    else:
        dur_str = f"{s}s"

    conn = _connect()
    cur = conn.cursor()

    # Get next Z_PK for alarm and sound
    cur.execute("SELECT MAX(Z_PK) FROM ZMTCDALARM")
    max_alarm_pk = cur.fetchone()[0] or 0
    new_alarm_pk = max_alarm_pk + 1

    cur.execute("SELECT MAX(Z_PK) FROM ZMTCDSOUND")
    max_sound_pk = cur.fetchone()[0] or 0
    new_sound_pk = max_sound_pk + 1

    # Update Z_PRIMARYKEY so Core Data stays in sync
    cur.execute(
        "UPDATE Z_PRIMARYKEY SET Z_MAX = ? WHERE Z_NAME = 'MTCDAlarm'",
        (new_alarm_pk,),
    )
    cur.execute(
        "UPDATE Z_PRIMARYKEY SET Z_MAX = ? WHERE Z_NAME = 'MTCDSound'",
        (new_sound_pk,),
    )

    now_ts = datetime.now().timestamp()  # Core Data timestamp (epoch)
    alarm_uuid = _uuid.uuid4().bytes  # 16-byte blob for ZMTID

    # Insert the alarm
    cur.execute(
        """INSERT INTO ZMTCDALARM
           (Z_PK, Z_ENT, Z_OPT, ZALLOWSSNOOZE, ZDAY, ZDISMISSEDACTION,
            ZENABLED, ZHOUR, ZMINUTE, ZMONTH, ZREPEATSCHEDULE,
            ZSILENTMODEOPTIONS, ZSLEEPALARM, ZSLEEPSCHEDULE, ZSNOOZEDURATION,
            ZYEAR, ZSOUND, ZDISMISSEDDATE, ZFIREDDATE, ZKEEPOFFUNTILDATE,
            ZLASTMODIFIEDDATE, ZSNOOZEFIREDATE, ZTITLE, ZMTID, ZCOORDINATIONPOLICY)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            new_alarm_pk,  # Z_PK
            _ENT_ALARM,  # Z_ENT
            1,  # Z_OPT
            1,  # ZALLOWSSNOOZE (true)
            0,  # ZDAY
            0,  # ZDISMISSEDACTION
            1,  # ZENABLED (true!)
            hour,  # ZHOUR
            minute,  # ZMINUTE
            0,  # ZMONTH
            0,  # ZREPEATSCHEDULE
            2,  # ZSILENTMODEOPTIONS
            0,  # ZSLEEPALARM
            0,  # ZSLEEPSCHEDULE
            9,  # ZSNOOZEDURATION
            0,  # ZYEAR
            new_sound_pk,  # ZSOUND (FK to ZMTCDSOUND)
            None,  # ZDISMISSEDDATE
            None,  # ZFIREDDATE
            None,  # ZKEEPOFFUNTILDATE
            now_ts,  # ZLASTMODIFIEDDATE
            None,  # ZSNOOZEFIREDATE
            label or None,  # ZTITLE
            alarm_uuid,  # ZMTID
            1,  # ZCOORDINATIONPOLICY
        ),
    )

    # Insert the corresponding sound entry
    cur.execute(
        """INSERT INTO ZMTCDSOUND
           (Z_PK, Z_ENT, Z_OPT, ZMEDIAITEMIDENTIFIER, ZSOUNDTYPE,
            ZALARM, ZDURATION, ZTIMER, ZVOLUMELEVEL,
            ZTONEIDENTIFIER, ZVIBRATIONIDENTIFIER)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            new_sound_pk,  # Z_PK
            _ENT_SOUND,  # Z_ENT
            1,  # Z_OPT
            0,  # ZMEDIAITEMIDENTIFIER
            2,  # ZSOUNDTYPE (system)
            new_alarm_pk,  # ZALARM (FK to ZMTCDALARM)
            0,  # ZDURATION
            None,  # ZTIMER
            -1.0,  # ZVOLUMELEVEL (default)
            "system:Radial",  # ZTONEIDENTIFIER
            "",  # ZVIBRATIONIDENTIFIER
        ),
    )

    conn.commit()
    conn.close()

    # Restart mobiletimerd so Clock.app picks up the new alarm
    subprocess.run(["killall", "mobiletimerd"], capture_output=True)

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
