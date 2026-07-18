#!/usr/bin/env python3
"""LLM-powered help: read a module file + main.py, then tell the user how to call it."""

import os
import sys

from ww.llm.openrouter_client import call_openrouter_api_with_messages


MODEL = "deepseek/deepseek-v4-flash"


def _resolve_path(path):
    """Resolve a path that may be relative to cwd or use ~ expansion."""
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    return path


def _find_wiring(main_py_path, filename):
    """Search main.py for the group that routes to this file."""
    basename = os.path.splitext(filename)[0]
    # The import line looks like: from ww.xxx.module import main as m
    # Find which group it's under
    with open(main_py_path) as f:
        content = f.read()

    # Try to find the import line
    # The import pattern: "from ww. something containing basename import"
    # We'll search for the basename in the main.py imports
    lines = content.split("\n")
    wiring_context = ""
    for i, line in enumerate(lines):
        if basename in line and "from ww" in line and "import" in line:
            # Found the import — grab surrounding context (group + subcmd)
            start = max(0, i - 15)
            end = min(len(lines), i + 3)
            wiring_context = "\n".join(
                f"{start + j + 1}:{lines[start + j]}" for j in range(end - start)
            )
            break

    return wiring_context


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww help <file_path>")
        print()
        print("Use LLM to read a command module file and tell you how to call it.")
        print()
        print("Examples:")
        print("  ww help ww/gcp_speech/transcribe.py")
        print("  ww help ~/projects/ww/ww/ffmpeg/merge.py")
        return

    file_path = _resolve_path(args[0])

    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Read the target file
    with open(file_path) as f:
        file_content = f.read()

    # Find how it's wired in main.py
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_py = os.path.join(project_root, "main.py")
    filename = os.path.basename(file_path)

    wiring = _find_wiring(main_py, filename) if os.path.isfile(main_py) else ""

    # Build the prompt
    prompt = f"""You are a helpful assistant that explains how to call a command in the `ww` CLI toolkit.

Given a Python module file and its wiring in main.py, tell the user the exact `ww` command to run.

Module file: {file_path}

Module content:
```python
{file_content}
```

Wiring in main.py (how it's imported/dispatched):
```
{wiring if wiring else "(not found — this file may not be wired into main.py yet)"}
```

Write a concise, terminal-friendly explanation:
1. The exact `ww` command to call (including subcommand if any)
2. Any required arguments or options
3. A brief example
4. Any prerequisites (env vars, external tools, etc.)

Output plain text only — no markdown formatting, no fenced blocks. Just clean terminal text.
"""

    messages = [
        {
            "role": "system",
            "content": "You are a CLI help assistant. Output concise, terminal-friendly text.",
        },
        {"role": "user", "content": prompt},
    ]

    print()
    print(f"🔍 Reading {file_path} ...")
    print()

    try:
        result = call_openrouter_api_with_messages(
            messages, model=MODEL, max_tokens=2000
        )
    except Exception as e:
        print(f"Error calling LLM: {e}", file=sys.stderr)
        sys.exit(1)

    print(result)
    print()
    print("─" * 50)


if __name__ == "__main__":
    main()
