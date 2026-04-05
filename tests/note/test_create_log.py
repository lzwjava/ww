import os
import shutil
import tempfile
from unittest.mock import patch

from ww.note.create_normal_log import generate_filename, create_normal_log

MARKDOWN_CONTENT = """🦞 Hey Boss. Here's the breakdown of that WhatsApp flapping:

**What happened:**
Between 12:01 and 12:11, your WhatsApp Web connection (`+1-555-000-0000`) was stuck in a **connect/disconnect loop** every ~60 seconds. Each cycle looked like this:
1. **Disconnected** (status 499) — WhatsApp Web session dropped
2. **Connected** — Re-established successfully
3. **~60s later** — Disconnected again (status 499)

**Root cause:**
- The loop was triggered by the **heartbeat monitor** detecting no inbound messages for 62+ minutes
- It forced a reconnect to "wake up" the session
- Each reconnect briefly succeeded, but the session was immediately flagged as stale again and dropped

**Why it stopped:**
- At **12:11:24**, the health-monitor did a full restart of the WhatsApp channel
- At **12:23:29**, you sent "ey" — the first inbound message in 84 minutes
- This broke the stale-session cycle. The connection has been stable since (last heartbeat at 12:25 shows `messagesHandled: 2`)

**Side note:**
Your Telegram bot is also throwing **409 Conflict** errors repeatedly — looks like another bot instance is running somewhere, fighting for the same `getUpdates` stream. That's a separate issue if you care to fix it.

**TL;DR:** WhatsApp was cycling because it was idle for too long. Your message at 12:23 fixed it. Connection is now stable. 🦞"""


def test_generate_filename_markdown_gets_md_extension():
    """Markdown-formatted content should get .md extension, not .log."""
    filename = generate_filename(MARKDOWN_CONTENT)
    assert filename.endswith(".md"), (
        f"Expected .md extension for markdown content, got: {filename}"
    )
    assert "." in filename
    name, ext = filename.rsplit(".", 1)
    assert ext == "md"
    assert len(name) > 0


def test_generate_filename_format_is_valid():
    """Filename should match name.ext pattern with only lowercase, digits, hyphens."""
    import re

    filename = generate_filename(MARKDOWN_CONTENT)
    assert re.match(r"^[a-z0-9-]+\.[a-z0-9]+$", filename), (
        f"Filename '{filename}' doesn't match expected format"
    )


def test_create_normal_log_writes_file_with_correct_extension():
    """Full integration: create_normal_log should write a .md file for markdown content."""
    tmpdir = tempfile.mkdtemp()
    try:
        with patch(
            "ww.note.create_normal_log.get_base_path", return_value=tmpdir
        ), patch("ww.note.create_normal_log.gitmessageai"):
            create_normal_log(content=MARKDOWN_CONTENT)

        logs_dir = os.path.join(tmpdir, "logs")
        files = os.listdir(logs_dir)
        assert len(files) == 1, f"Expected 1 file, got: {files}"

        created_file = files[0]
        assert created_file.endswith(".md"), (
            f"Expected .md extension, got: {created_file}"
        )

        file_path = os.path.join(logs_dir, created_file)
        with open(file_path, "r") as f:
            written = f.read()
        assert written == MARKDOWN_CONTENT
    finally:
        shutil.rmtree(tmpdir)
