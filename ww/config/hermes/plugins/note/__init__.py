"""note plugin — save assistant responses as markdown notes.

Registers ``/note`` slash command that takes the last assistant response
and creates a note file using the ``ww`` package's ``create_note_from_content``.

Usage:
    /note                        # save last response (LLM-generated title)
    /note 3                      # save 3rd assistant response
    /note --title "My Title"     # save with custom title
    /note --dir ~/my-notes       # save to custom directory
    /note 2 --title "Foo" --dir ~/notes
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
    i = 0
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        elif args[i] == "--dir" and i + 1 < len(args):
            note_dir = args[i + 1]
            i += 2
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

    # Create note via ww
    try:
        from ww.note.create_note_from_clipboard import create_note_from_content
    except ImportError:
        # Add ww project to path if not installed in current venv
        import sys

        ww_path = str(Path.home() / "projects" / "ww")
        if ww_path not in sys.path:
            sys.path.insert(0, ww_path)
        try:
            from ww.note.create_note_from_clipboard import create_note_from_content
        except ImportError:
            return (
                "'ww' package not installed. Install with: pip install -e ~/projects/ww"
            )

    try:
        print("Generating title via LLM...")
        file_path = create_note_from_content(
            text, custom_title=title, directory=note_dir
        )
    except ValueError as e:
        return f"Note rejected: {e}"
    except Exception as e:
        logger.debug("Note creation failed: %s", e, exc_info=True)
        return f"Note creation failed: {e}"

    # Auto git commit + push
    try:
        from ww.github.gitmessageai import gitmessageai

        note_dir_resolved = str(Path(file_path).parent) if file_path else None
        gitmessageai(allow_pull_push=True, directory=note_dir_resolved)
        return f"Note saved and pushed: {file_path}"
    except Exception as e:
        logger.debug("Git push failed: %s", e, exc_info=True)
        return f"Note saved but git push failed: {file_path} ({e})"


def register(ctx) -> None:
    """Plugin entry point — called by the Hermes plugin loader."""
    global _ctx
    _ctx = ctx
    ctx.register_command(
        "note",
        handler=_handle_note,
        description="Save the last assistant response as a note file.",
        args_hint="[number] [--title <title>] [--dir <dir>]",
    )
    logger.debug("note plugin registered /note command")
