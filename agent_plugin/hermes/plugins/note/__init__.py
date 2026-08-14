"""note plugin — save assistant responses as markdown notes.

Registers ``/note`` slash command that enqueues the last assistant response
for deferred processing via ``ww note process`` (fast, no git/LLM inline).

Usage:
    /note                        # save last response
    /note 3                      # save 3rd assistant response
    /note --title "My Title"     # save with custom title
    /note --dir ~/my-notes       # save to custom directory
    /note --code                 # LLM-wrap code in fences, then save
    /note 2 --title "Foo" --dir ~/notes --code
"""

from __future__ import annotations

import logging
import os
import re
import shlex
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Module-level plugin context, set during register()
_ctx = None


def _strip_reasoning_tags(text: str) -> str:
    """Remove <thinking>...</thinking> and similar reasoning blocks."""
    return re.sub(
        r"<(?:thinking|reasoning|scratchpad)>.*?</(?:thinking|reasoning|scratchpad)>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()


def _content_as_text(content: Any) -> str:
    """Extract plain text from assistant message content."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            str(part.get("text", ""))
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        return "\n".join(p for p in parts if p)
    return str(content)


def _get_assistant_messages():
    """Get assistant messages from the active CLI conversation history."""
    if _ctx is None:
        return []
    cli = _ctx._manager._cli_ref
    if cli is None:
        return []
    return [m for m in cli.conversation_history if m.get("role") == "assistant"]


def _handle_note(raw_args: str) -> Optional[str]:
    """Handle /note [number] [--title <title>] [--dir <dir>]."""
    # Load ww's .env so LLM calls work even without shell-level exports
    try:
        from dotenv import load_dotenv

        load_dotenv(Path.home() / "projects" / "ww" / ".env", override=False)
    except ImportError:
        pass
    # Ensure MODEL is set — check ww .env explicitly if dotenv didn't populate it
    if not os.environ.get("MODEL"):
        env_path = Path.home() / "projects" / "ww" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("MODEL=") and not line.startswith("#"):
                    os.environ.setdefault("MODEL", line.split("=", 1)[1].strip())
                    break
    try:
        args = shlex.split(raw_args)
    except ValueError:
        args = raw_args.split()

    # Parse arguments
    number = None
    title = None
    note_dir = None
    code = False
    i = 0
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        elif args[i] == "--dir" and i + 1 < len(args):
            note_dir = args[i + 1]
            i += 2
        elif args[i] == "--code":
            code = True
            i += 1
        elif number is None and args[i].isdigit():
            number = int(args[i])
            i += 1
        else:
            i += 1

    assistant = _get_assistant_messages()
    if not assistant:
        return "No assistant responses to save."

    # Pick the response
    if number is not None:
        idx = number - 1
        if idx < 0 or idx >= len(assistant):
            return f"Invalid response number. Use 1-{len(assistant)}."
    else:
        idx = len(assistant) - 1
        while idx >= 0 and not _content_as_text(assistant[idx].get("content")):
            idx -= 1
        if idx < 0:
            return "No content to save in assistant responses."

    text = _strip_reasoning_tags(_content_as_text(assistant[idx].get("content")))
    if not text:
        return "No content to save in that assistant response."

    # Enqueue for deferred processing (fast, no git/LLM inline)
    try:
        from ww.note.note_queue import _enqueue
    except ImportError:
        import sys

        ww_path = str(Path.home() / "projects" / "ww")
        if ww_path not in sys.path:
            sys.path.insert(0, ww_path)
        try:
            from ww.note.note_queue import _enqueue
        except ImportError:
            return (
                "'ww' package not installed. Install with: pip install -e ~/projects/ww"
            )

    extra = {}
    if title:
        extra["custom_title"] = title
    if note_dir:
        extra["directory"] = note_dir
    if code:
        extra["code"] = True
        try:
            from ww.note.create_note_utils import wrap_code_snippets

            text = wrap_code_snippets(text)
        except ImportError:
            return "'ww' package not installed or missing wrap_code_snippets."

    entry_id = _enqueue(text, "note", **extra)
    if entry_id:
        return f"Queued for processing: {entry_id} — run 'ww note process' to commit"
    return "Note skipped (empty, too short, or already queued)"


def register(ctx) -> None:
    """Plugin entry point — called by the Hermes plugin loader."""
    global _ctx
    _ctx = ctx
    ctx.register_command(
        "note",
        handler=_handle_note,
        description="Save the last assistant response as a note file.",
        args_hint="[number] [--title <title>] [--dir <dir>] [--code]",
    )
    logger.debug("note plugin registered /note command")
