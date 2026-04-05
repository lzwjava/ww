import argparse
import os
import sys
from pathlib import Path

from ww.llm.openrouter_client import call_openrouter_api
from ww.note.create_normal_log import create_normal_log
from ww.note.create_note_utils import (
    get_base_path,
    get_clipboard_content,
    generate_title,
)
from ww.note.check_duplicate_notes import _are_notes_quick_similar
from ww.note.obfuscate_log import OBFUSCATE_PROMPT


def is_sensitive_content(content):
    sensitivity_prompt = lambda c: (
        f"Does the following text contain sensitive information such as passwords, API keys, or personal data? Respond with 'yes' or 'no' only: {c}"
    )
    response = generate_title(content, 1, sensitivity_prompt).lower()
    return response == "yes"


def obfuscate_content(content):
    prompt = OBFUSCATE_PROMPT.format(content=content)
    obfuscated = call_openrouter_api(prompt)
    if not obfuscated:
        return None
    return obfuscated


def _check_duplicate_logs(content):
    logs_dir = os.path.join(get_base_path(), "logs")
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        return False

    log_files = [f for f in logs_path.iterdir() if f.is_file()]
    if not log_files:
        return False

    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    latest_logs = log_files[:200]

    for log_file in latest_logs:
        try:
            existing = log_file.read_text(encoding="utf-8")
            if _are_notes_quick_similar(content, existing):
                print(f"[warn] DUPLICATE FOUND: Content similar to {log_file.name}")
                return True
        except Exception as e:
            print(f"[warn] Error checking {log_file.name}: {e}")
    return False


def _create_log_with_content(content, direct=False, ext=None):
    if len(content) > 1048576:
        print("Error: Content exceeds 1MB. Please shorten the log and try again.")
        return

    if _check_duplicate_logs(content):
        print("Duplicate log found. Aborting.")
        return

    if direct:
        create_normal_log(content, ext=ext)
        return

    if is_sensitive_content(content):
        print("Sensitive content detected. Obfuscating...")
        obfuscated = obfuscate_content(content)
        if not obfuscated:
            print("Error: Obfuscation failed.")
            return
        create_normal_log(obfuscated, ext=ext)
    else:
        create_normal_log(content, ext=ext)


def create_log():
    parser = argparse.ArgumentParser(description="Create a log entry from clipboard")
    parser.add_argument(
        "--direct", action="store_true", help="Skip sensitivity check and obfuscation"
    )
    parser.add_argument(
        "--ext",
        help="File extension to use (e.g. md, txt), skips AI extension detection",
    )
    args = parser.parse_args(sys.argv[1:])

    content = get_clipboard_content()
    _create_log_with_content(content, args.direct, ext=args.ext)


def create_log_from_file():
    parser = argparse.ArgumentParser(description="Create a log entry from a file")
    parser.add_argument("file", help="Path to the file to read content from")
    parser.add_argument(
        "--direct", action="store_true", help="Skip sensitivity check and obfuscation"
    )
    parser.add_argument(
        "--ext",
        help="File extension to use (e.g. md, txt), skips AI extension detection",
    )
    args = parser.parse_args(sys.argv[1:])

    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()
    _create_log_with_content(content, args.direct, ext=args.ext)
