import os
import re
import sys

from ww.note.create_note_utils import get_base_path


def extract_title(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return ""

    match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip().strip('"')


def main():
    count = 10
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass

    notes_dir = os.path.join(get_base_path(), "notes")
    if not os.path.isdir(notes_dir):
        print(f"Notes directory not found: {notes_dir}")
        return

    files = sorted(
        [f for f in os.listdir(notes_dir) if f.endswith(".md")],
        reverse=True,
    )[:count]

    for filename in files:
        path = os.path.join(notes_dir, filename)
        title = extract_title(path)
        print(f"{filename}  {title}")
