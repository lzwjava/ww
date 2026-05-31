"""Background watcher for note queue — auto-processes pending entries when queue file changes."""

import hashlib
import json
import sys
import time
from pathlib import Path


def _queue_file() -> Path:
    return Path.home() / ".config" / "ww" / "note_queue.json"


def _file_hash(path: Path) -> str:
    """Quick hash of file content to detect changes."""
    try:
        return hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
    except (FileNotFoundError, OSError):
        return ""


def _print(msg: str) -> None:
    """Print with flush for real-time output in background."""
    print(msg, flush=True)


def watch(interval: float = 2.0) -> None:
    """Watch queue file for changes and auto-process pending entries.

    Args:
        interval: Seconds between checks (default: 2.0)
    """
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
