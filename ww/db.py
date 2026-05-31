"""SQLite database for tracking ww command usage."""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def get_db_path() -> str:
    """Resolve DB_PATH from env. Defaults to BASE_PATH/ww.db."""
    db_path = os.environ.get("DB_PATH", "").strip()
    if db_path:
        return db_path
    base_path = os.environ.get("BASE_PATH", "").strip()
    if base_path and base_path != ".":
        return os.path.join(base_path, "ww.db")
    # Fallback: project root
    project_root = str(Path(__file__).parent.parent)
    return os.path.join(project_root, "ww.db")


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Get a SQLite connection, creating parent dirs if needed."""
    if db_path is None:
        db_path = get_db_path()
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=3000")
    return conn


def init_db(db_path: str | None = None) -> sqlite3.Connection:
    """Initialize the database and create tables if they don't exist."""
    conn = get_connection(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS command_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            raw_command TEXT    NOT NULL,
            group_name  TEXT,
            subcmd      TEXT,
            exit_code   INTEGER,
            cwd         TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_command_log_timestamp
        ON command_log(timestamp)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_command_log_group
        ON command_log(group_name)
    """)
    conn.commit()
    return conn


def log_command(
    raw_args: list[str],
    group_name: str | None = None,
    subcmd: str | None = None,
    exit_code: int = 0,
    cwd: str | None = None,
    db_path: str | None = None,
) -> None:
    """Log a command invocation to the database."""
    try:
        conn = get_connection(db_path)
        # Ensure table exists (cheap no-op if already created)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS command_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                raw_command TEXT    NOT NULL,
                group_name  TEXT,
                subcmd      TEXT,
                exit_code   INTEGER,
                cwd         TEXT
            )
        """)
        timestamp = datetime.now(timezone.utc).isoformat()
        raw_command = " ".join(raw_args)
        if cwd is None:
            cwd = os.getcwd()
        conn.execute(
            "INSERT INTO command_log (timestamp, raw_command, group_name, subcmd, exit_code, cwd) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, raw_command, group_name, subcmd, exit_code, cwd),
        )
        conn.commit()
        conn.close()
    except Exception:
        # Never let logging break the actual command
        pass


def parse_command(raw_args: list[str]) -> tuple[str | None, str | None]:
    """Parse group and subcommand from raw args (ww <group> [subcmd] ...).

    Returns (group_name, subcmd) — either may be None.
    """
    if len(raw_args) < 2:
        return None, None
    group = raw_args[1]
    if group.startswith("-"):
        return None, None
    subcmd = (
        raw_args[2] if len(raw_args) > 2 and not raw_args[2].startswith("-") else None
    )
    return group, subcmd
