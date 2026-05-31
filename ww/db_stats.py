"""ww db — command usage statistics and history."""

import sys


def _get_conn():
    from ww.db import init_db

    return init_db()


def cmd_stats():
    """Show overall command usage statistics."""
    conn = _get_conn()

    total = conn.execute("SELECT COUNT(*) FROM command_log").fetchone()[0]
    if total == 0:
        print("No commands recorded yet.")
        conn.close()
        return

    print(f"Total commands recorded: {total}")
    print()

    # Top groups
    rows = conn.execute(
        "SELECT group_name, COUNT(*) as cnt FROM command_log "
        "WHERE group_name IS NOT NULL GROUP BY group_name ORDER BY cnt DESC LIMIT 15"
    ).fetchall()
    if rows:
        print("Top command groups:")
        for group, cnt in rows:
            bar = "#" * min(cnt, 40)
            print(f"  {group:<20s} {cnt:>5d}  {bar}")
        print()

    # Top full commands (group + subcmd)
    rows = conn.execute(
        "SELECT group_name, subcmd, COUNT(*) as cnt FROM command_log "
        "WHERE group_name IS NOT NULL GROUP BY group_name, subcmd ORDER BY cnt DESC LIMIT 15"
    ).fetchall()
    if rows:
        print("Top commands (group + subcmd):")
        for group, subcmd, cnt in rows:
            label = f"{group} {subcmd}" if subcmd else group
            print(f"  {label:<30s} {cnt:>5d}")
        print()

    # Error rate
    errors = conn.execute(
        "SELECT COUNT(*) FROM command_log WHERE exit_code != 0"
    ).fetchone()[0]
    print(f"Errors (exit_code != 0): {errors} / {total} ({100 * errors / total:.1f}%)")
    print()

    # Busiest days
    rows = conn.execute(
        "SELECT substr(timestamp, 1, 10) as day, COUNT(*) as cnt FROM command_log "
        "GROUP BY day ORDER BY cnt DESC LIMIT 5"
    ).fetchall()
    if rows:
        print("Busiest days:")
        for day, cnt in rows:
            print(f"  {day}  {cnt:>5d}")
        print()

    # First and last recorded
    first = conn.execute(
        "SELECT timestamp FROM command_log ORDER BY id ASC LIMIT 1"
    ).fetchone()
    last = conn.execute(
        "SELECT timestamp FROM command_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if first and last:
        print(f"First recorded: {first[0]}")
        print(f"Last recorded:  {last[0]}")

    conn.close()


def cmd_recent():
    """Show recent commands."""
    conn = _get_conn()
    limit = 20

    # Parse --limit N
    args = sys.argv[1:]  # already popped 'db' and 'recent'
    for i, a in enumerate(args):
        if a == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    rows = conn.execute(
        "SELECT id, timestamp, raw_command, exit_code FROM command_log "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()

    if not rows:
        print("No commands recorded yet.")
        conn.close()
        return

    print(f"Last {len(rows)} commands:")
    print()
    for rid, ts, raw, ec in reversed(rows):
        ts_short = ts[:19].replace("T", " ")
        status = "ok" if ec == 0 else f"ERR({ec})"
        print(f"  [{rid:>5d}] {ts_short}  ({status})  {raw}")

    conn.close()


def cmd_top():
    """Show most frequently used commands."""
    conn = _get_conn()
    limit = 20

    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    rows = conn.execute(
        "SELECT raw_command, COUNT(*) as cnt FROM command_log "
        "GROUP BY raw_command ORDER BY cnt DESC LIMIT ?",
        (limit,),
    ).fetchall()

    if not rows:
        print("No commands recorded yet.")
        conn.close()
        return

    print(f"Top {len(rows)} most-used commands:")
    print()
    for raw, cnt in rows:
        print(f"  {cnt:>5d}x  {raw}")

    conn.close()


def cmd_errors():
    """Show recent error commands."""
    conn = _get_conn()
    limit = 20

    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    rows = conn.execute(
        "SELECT id, timestamp, raw_command, exit_code FROM command_log "
        "WHERE exit_code != 0 ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()

    if not rows:
        print("No errors recorded.")
        conn.close()
        return

    print(f"Last {len(rows)} errors:")
    print()
    for rid, ts, raw, ec in reversed(rows):
        ts_short = ts[:19].replace("T", " ")
        print(f"  [{rid:>5d}] {ts_short}  exit={ec}  {raw}")

    conn.close()


def cmd_search():
    """Search command history."""
    conn = _get_conn()

    args = sys.argv[1:]
    query = None
    for i, a in enumerate(args):
        if not a.startswith("-") and a != "search":
            query = a
            break

    if not query:
        print("Usage: ww db search <pattern>")
        conn.close()
        return

    rows = conn.execute(
        "SELECT id, timestamp, raw_command, exit_code FROM command_log "
        "WHERE raw_command LIKE ? ORDER BY id DESC LIMIT 30",
        (f"%{query}%",),
    ).fetchall()

    if not rows:
        print(f"No commands matching '{query}'.")
        conn.close()
        return

    print(f"Commands matching '{query}':")
    print()
    for rid, ts, raw, ec in reversed(rows):
        ts_short = ts[:19].replace("T", " ")
        status = "ok" if ec == 0 else f"ERR({ec})"
        print(f"  [{rid:>5d}] {ts_short}  ({status})  {raw}")

    conn.close()


def main():
    subcmd = ""
    if len(sys.argv) > 1:
        subcmd = sys.argv.pop(1)

    if subcmd == "" or subcmd in ("--help", "-h"):
        print("Usage: ww db <command>")
        print()
        print("Track and query ww command usage history.")
        print()
        print("Commands:")
        print("  errors     Show recent error commands (--limit N)")
        print("  recent     Show recent commands (--limit N)")
        print("  search     Search command history by pattern")
        print("  stats      Show overall usage statistics")
        print("  top        Show most frequently used commands (--limit N)")
        return

    if subcmd == "stats":
        cmd_stats()
    elif subcmd == "recent":
        cmd_recent()
    elif subcmd == "top":
        cmd_top()
    elif subcmd == "errors":
        cmd_errors()
    elif subcmd == "search":
        cmd_search()
    else:
        print(f"Unknown db command: {subcmd}")
        sys.exit(1)
