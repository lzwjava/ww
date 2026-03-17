from pathlib import Path

from ww.create.create_note_utils import (
    get_clipboard_content,
    clean_grok_tags,
    clean_content,
)


def _are_notes_quick_similar(content1, content2):
    if not content1 or not content2:
        return False

    len1 = len(content1)
    len2 = len(content2)
    if max(len1, len2) == 0:
        return False

    if abs(len1 - len2) / max(len1, len2) > 0.05:
        return False

    first500_1 = content1[:500]
    first500_2 = content2[:500]

    if len(first500_1) >= 250 and len(first500_2) >= 250:
        if first500_1[:250] != first500_2[:250]:
            return False
        matches = sum(c1 == c2 for c1, c2 in zip(first500_1[:500], first500_2[:500]))
        return matches >= 450

    return content1.strip() == content2.strip()


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


def check_duplicate_notes(notes_dir="notes") -> bool:
    """Check if clipboard content already exists in the latest 200 notes.

    Returns True if a duplicate is found, False otherwise.
    """
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
    latest_notes = note_files[:-1]

    print(f"[info] Checking against latest {len(latest_notes)} notes...")

    for note_file in latest_notes:
        try:
            note_content = _extract_content_without_frontmatter(note_file)
            if _are_notes_quick_similar(clipboard_content, note_content):
                print(f"[warn] DUPLICATE FOUND: Content similar to {note_file.name}")
                return True
        except Exception as e:
            print(f"[warn] Error checking {note_file.name}: {e}")
            continue

    print("[info] No duplicates found")
    return False
