"""Background watcher for note queue — auto-processes pending entries when queue file changes."""

import atexit
import hashlib
import json
import os
import sys
import time
from pathlib import Path


def _queue_file() -> Path:
    return Path.home() / ".config" / "ww" / "note_queue.json"


def _pid_file() -> Path:
    return Path.home() / ".config" / "ww" / "note_watch.pid"


def _file_hash(path: Path) -> str:
    """Quick hash of file content to detect changes."""
    try:
        return hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
    except (FileNotFoundError, OSError):
        return ""


def _print(msg: str) -> None:
    """Print with flush for real-time output in background."""
    print(msg, flush=True)


def _acquire_lock() -> bool:
    """Try to acquire a PID lock. Returns True if lock acquired, False if another instance is running."""
    pf = _pid_file()
    if pf.exists():
        try:
            old_pid = int(pf.read_text().strip())
            # Check if the process is still alive (kill -0)
            os.kill(old_pid, 0)
            _print(f"[watch] Another instance is already running (pid={old_pid})")
            return False
        except (ValueError, ProcessLookupError, PermissionError):
            # Stale PID file — process no longer exists
            pass
        except OSError:
            pass

    pf.write_text(str(os.getpid()))
    atexit.register(_release_lock)
    return True


def _release_lock() -> None:
    """Remove PID file on exit."""
    pf = _pid_file()
    try:
        if pf.exists() and pf.read_text().strip() == str(os.getpid()):
            pf.unlink()
    except OSError:
        pass


def watch(interval: float = 2.0) -> None:
    """Watch queue file for changes and auto-process pending entries.

    Args:
        interval: Seconds between checks (default: 2.0)
    """
    if not _acquire_lock():
        sys.exit(1)

    qf = _queue_file()
    last_hash = _file_hash(qf)
    _print(f"[watch] Monitoring {qf} (interval={interval}s)")
    _print("[watch] Press Ctrl+C to stop")

    while True:
        try:
            time.sleep(interval)
            current_hash = _file_hash(qf)

            if current_hash == last_hash:
                continue

            last_hash = current_hash

            # Check for pending entries
            try:
                queue = json.loads(qf.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            pending = [e for e in queue if e.get("status") == "pending"]
            if not pending:
                continue

            _print(f"\n[watch] Found {len(pending)} pending note(s), processing...")

            # Import and run processor
            from ww.note.note_queue_process import process_queue

            process_queue()

            # Update hash after processing
            last_hash = _file_hash(qf)
            _print("[watch] Waiting for next change...")

        except KeyboardInterrupt:
            _print("\n[watch] Stopped")
            sys.exit(0)
        except Exception as e:
            _print(f"[watch] Error: {e}")
            time.sleep(interval)


def main():
    """CLI entry point for 'ww note watch'."""
    import argparse

    parser = argparse.ArgumentParser(description="Watch note queue and auto-process")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Check interval in seconds (default: 2.0)",
    )
    args = parser.parse_args()

    watch(interval=args.interval)


if __name__ == "__main__":
    main()
