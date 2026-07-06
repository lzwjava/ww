"""File-based queue for ww note — fast clipboard capture, deferred processing."""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def _queue_dir() -> Path:
    d = Path.home() / ".config" / "ww"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _queue_file() -> Path:
    return _queue_dir() / "note_queue.json"


def _load_queue() -> list[dict]:
    qf = _queue_file()
    if not qf.exists():
        return []
    try:
        return json.loads(qf.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_queue(queue: list[dict]) -> None:
    qf = _queue_file()
    tmp = qf.with_suffix(".tmp")
    tmp.write_text(json.dumps(queue, indent=2, ensure_ascii=False))
    tmp.rename(qf)  # atomic on POSIX


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _get_clipboard() -> str:
    """Read clipboard content. Works on macOS and Linux."""
    if sys.platform == "darwin":
        import subprocess

        return subprocess.check_output(["pbpaste"], text=True).strip()
    else:
        try:
            import pyperclip

            return pyperclip.paste().strip()
        except Exception:
            # fallback: try xclip
            import subprocess

            return subprocess.check_output(
                ["xclip", "-selection", "clipboard", "-o"], text=True
            ).strip()


def _enqueue(text: str, entry_type: str = "note", **extra) -> Optional[str]:
    """Core enqueue helper. Returns entry id if added, None if duplicate or empty."""
    if not text:
        print("[warn] Content is empty")
        return None
    if entry_type == "note" and len(text) < 200:
        print(f"[warn] Content too short ({len(text)} chars, need 200+), skipping")
        return None

    h = content_hash(text)
    queue = _load_queue()

    # Dedup: same hash + pending status
    for entry in queue:
        if entry["content_hash"] == h and entry["status"] == "pending":
            print(
                f"[skip] Already queued (id={entry['id']}, queued at {entry['queued_at']})"
            )
            return None

    entry_id = h
    now = datetime.now().isoformat(timespec="seconds")
    entry = {
        "id": entry_id,
        "content": text,
        "content_hash": h,
        "queued_at": now,
        "status": "pending",
        "type": entry_type,
        "note_path": None,
    }
    entry.update(extra)
    queue.append(entry)
    _save_queue(queue)
    print(
        f"[ok] Queued (id={entry_id}, {len(text)} chars, {len(queue)} total in queue)"
    )
    return entry_id


def enqueue_clipboard(text=None, code=False) -> Optional[str]:
    """Read clipboard and add to note queue. Returns entry id if added, None if duplicate or empty."""
    if text is None:
        text = _get_clipboard()
    extra = {}
    if code:
        extra["code"] = True
    return _enqueue(text, "note", **extra)


def enqueue_log(**kwargs) -> Optional[str]:
    """Read clipboard and add to log queue. Returns entry id if added, None if duplicate or empty."""
    text = _get_clipboard()
    return _enqueue(text, "log", **kwargs)


def enqueue_html(**kwargs) -> Optional[str]:
    """Read clipboard and add to HTML note queue. Returns entry id if added, None if duplicate or empty."""
    text = _get_clipboard()
    return _enqueue(text, "html", **kwargs)


def get_pending() -> list[dict]:
    return [e for e in _load_queue() if e["status"] == "pending"]


def get_all() -> list[dict]:
    return _load_queue()


def mark_done(entry_id: str, note_path: str) -> None:
    queue = _load_queue()
    for entry in queue:
        if entry["id"] == entry_id:
            entry["status"] = "done"
            entry["note_path"] = note_path
            entry["processed_at"] = datetime.now().isoformat(timespec="seconds")
            break
    _save_queue(queue)


def mark_failed(entry_id: str, error: str) -> None:
    queue = _load_queue()
    for entry in queue:
        if entry["id"] == entry_id:
            entry["status"] = "failed"
            entry["error"] = error
            entry["failed_at"] = datetime.now().isoformat(timespec="seconds")
            break
    _save_queue(queue)


def clear_done() -> int:
    """Remove all done/failed entries. Returns count removed."""
    queue = _load_queue()
    before = len(queue)
    queue = [e for e in queue if e["status"] == "pending"]
    _save_queue(queue)
    return before - len(queue)


def print_status() -> None:
    """Print queue status summary."""
    queue = _load_queue()
    if not queue:
        print("[ok] Queue is empty")
        return

    pending = [e for e in queue if e["status"] == "pending"]
    done = [e for e in queue if e["status"] == "done"]
    failed = [e for e in queue if e["status"] == "failed"]

    print(
        f"Queue: {len(queue)} entries ({len(pending)} pending, {len(done)} done, {len(failed)} failed)"
    )
    print()
    for entry in queue:
        status_icon = {"pending": "⏳", "done": "✅", "failed": "❌"}.get(
            entry["status"], "?"
        )
        preview = entry["content"][:80].replace("\n", " ")
        if len(entry["content"]) > 80:
            preview += "..."
        print(f"  {status_icon} [{entry['id']}] {entry['queued_at']}  {preview}")
        if entry.get("error"):
            print(f"    error: {entry['error']}")
        if entry.get("note_path"):
            print(f"    note: {entry['note_path']}")
