import os
import re
import shutil
import tempfile
from unittest.mock import patch

from ww.note.create_normal_log import (
    generate_filename,
    generate_filename_with_ext,
    create_normal_log,
)

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


@patch(
    "ww.note.create_normal_log.call_openrouter_api",
    return_value="whatsapp-flapping-notes.md",
)
def test_generate_filename_returns_llm_result(mock_api):
    """generate_filename should return the LLM-generated filename."""
    filename = generate_filename(MARKDOWN_CONTENT)
    mock_api.assert_called_once()
    assert filename == "whatsapp-flapping-notes.md"


@patch("ww.note.create_normal_log.call_openrouter_api", return_value="my-notes.md")
def test_generate_filename_format_is_valid(mock_api):
    """Filename should match name.ext pattern with only lowercase, digits, hyphens."""
    filename = generate_filename(MARKDOWN_CONTENT)
    assert re.match(r"^[a-z0-9-]+\.[a-z0-9]+$", filename), (
        f"Filename '{filename}' doesn't match expected format"
    )


@patch("ww.note.create_normal_log.call_openrouter_api", return_value="server-log")
def test_generate_filename_with_ext_appends_extension(mock_api):
    """generate_filename_with_ext should strip any extension from LLM result and append the given one."""
    filename = generate_filename_with_ext(MARKDOWN_CONTENT, "md")
    assert filename == "server-log.md"


@patch(
    "ww.note.create_normal_log.call_openrouter_api",
    return_value="whatsapp-flapping-notes.md",
)
def test_generate_filename_passes_snippet_to_llm(mock_api):
    """generate_filename should pass content snippet to the LLM prompt."""
    generate_filename(MARKDOWN_CONTENT)
    call_args = mock_api.call_args[0][0]
    assert "WhatsApp" in call_args or "Hey Boss" in call_args


def test_create_normal_log_writes_file_with_log_extension():
    """create_normal_log defaults to .log extension when no ext specified."""
    tmpdir = tempfile.mkdtemp()
    try:
        with (
            patch("ww.note.create_normal_log.get_base_path", return_value=tmpdir),
            patch("ww.note.create_normal_log.gitmessageai"),
        ):
            create_normal_log(content=MARKDOWN_CONTENT)

        logs_dir = os.path.join(tmpdir, "logs")
        files = os.listdir(logs_dir)
        assert len(files) == 1, f"Expected 1 file, got: {files}"

        created_file = files[0]
        assert created_file.endswith(".log"), (
            f"Expected .log extension by default, got: {created_file}"
        )

        file_path = os.path.join(logs_dir, created_file)
        with open(file_path, "r") as f:
            written = f.read()
        assert written == MARKDOWN_CONTENT
    finally:
        shutil.rmtree(tmpdir)


def test_create_normal_log_with_custom_ext():
    """create_normal_log should use the provided ext."""
    tmpdir = tempfile.mkdtemp()
    try:
        with (
            patch("ww.note.create_normal_log.get_base_path", return_value=tmpdir),
            patch("ww.note.create_normal_log.gitmessageai"),
        ):
            create_normal_log(content=MARKDOWN_CONTENT, ext="md")

        logs_dir = os.path.join(tmpdir, "logs")
        files = os.listdir(logs_dir)
        assert len(files) == 1, f"Expected 1 file, got: {files}"

        created_file = files[0]
        assert created_file.endswith(".md"), (
            f"Expected .md extension, got: {created_file}"
        )
    finally:
        shutil.rmtree(tmpdir)


@patch(
    "ww.note.create_normal_log.call_openrouter_api",
    return_value="whatsapp-flapping-notes.md",
)
def test_create_normal_log_with_friendly_name(mock_llm):
    """create_normal_log with friendly_name=True uses LLM-generated filename."""
    tmpdir = tempfile.mkdtemp()
    try:
        with (
            patch("ww.note.create_normal_log.get_base_path", return_value=tmpdir),
            patch("ww.note.create_normal_log.gitmessageai"),
        ):
            create_normal_log(content=MARKDOWN_CONTENT, friendly_name=True)

        logs_dir = os.path.join(tmpdir, "logs")
        files = os.listdir(logs_dir)
        assert len(files) == 1, f"Expected 1 file, got: {files}"

        created_file = files[0]
        assert created_file == "whatsapp-flapping-notes.md"
    finally:
        shutil.rmtree(tmpdir)
