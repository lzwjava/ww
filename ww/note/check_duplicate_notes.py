import os
from pathlib import Path

from ww.note.create_note_utils import (
    get_base_path,
    get_clipboard_content,
    clean_grok_tags,
    clean_content,
)


def _char_similarity(text1, text2):
    """Character-by-character similarity ratio between two strings."""
    if not text1 or not text2:
        return 0.0
    matches = sum(c1 == c2 for c1, c2 in zip(text1, text2))
    return matches / max(len(text1), len(text2))


def _are_notes_quick_similar(content1, content2):
    """Fast similarity check between two note contents.

    Checks both the first N and last N characters.
    If either region matches, the notes are considered duplicates.
    """
    if not content1 or not content2:
        return False

    len1 = len(content1)
    len2 = len(content2)
    if max(len1, len2) == 0:
        return False

    # Quick length check within 5% tolerance
    if abs(len1 - len2) / max(len1, len2) > 0.05:
        return False

    # Short content: exact match
    if len1 < 100 or len2 < 100:
        return content1.strip() == content2.strip()

    # Check first 200 chars
    first_match = False
    first200_1 = content1[:200]
    first200_2 = content2[:200]
    if first200_1[:100] == first200_2[:100]:
        if _char_similarity(first200_1, first200_2) >= 0.90:
            first_match = True

    # Check last 200 chars
    last_match = False
    last200_1 = content1[-200:]
    last200_2 = content2[-200:]
    if last200_1[-100:] == last200_2[-100:]:
        if _char_similarity(last200_1, last200_2) >= 0.90:
            last_match = True

    return first_match or last_match


def _extract_content_without_frontmatter(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        sections = content.split("---", 2)
        if len(sections) >= 3:
            return sections[2].strip()
        return content.strip()
    except Exception as e:
        print(f"[warn] Error reading {file_path}: {e}")
        return ""


def _is_duplicate_of_any(clipboard_content, note_files):
    for note_file in note_files:
        try:
            note_content = _extract_content_without_frontmatter(note_file)
            if _are_notes_quick_similar(clipboard_content, note_content):
                print(f"[warn] DUPLICATE FOUND: Content similar to {note_file.name}")
                return True
        except Exception as e:
            print(f"[warn] Error checking {note_file.name}: {e}")
    return False


def check_duplicate_notes(notes_dir=None) -> bool:
    """Check if clipboard content already exists in the latest 200 notes.

    Returns True if a duplicate is found, False otherwise.
    """
    if notes_dir is None:
        notes_dir = os.path.join(get_base_path(), "notes")
    clipboard_content = get_clipboard_content()
    if not clipboard_content or not clipboard_content.strip():
        print("[info] No content in clipboard")
        return False

    clipboard_content = clean_grok_tags(clipboard_content)
    clipboard_content = clean_content(clipboard_content)

    notes_path = Path(notes_dir)
    if not notes_path.exists():
        print(f"[warn] Notes directory not found: {notes_path}")
        return False

    note_files = list(notes_path.glob("*.md"))
    if not note_files:
        print("[info] No notes found")
        return False

    note_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    latest_notes = note_files[1:]  # Exclude newest file (current clipboard)

    print(f"[info] Checking against latest {len(latest_notes)} notes...")
    return _is_duplicate_of_any(clipboard_content, latest_notes)
