import re
import sys
from datetime import datetime

from ww.create.create_note_utils import (
    get_clipboard_content,
    clean_grok_tags,
    generate_title,
    generate_short_title,
    create_filename,
    format_front_matter,
    clean_content,
    write_note,
)
from ww.create.check_duplicate_notes import check_duplicate_notes


def create_note_from_content(content, custom_title=None, directory="notes", date=None):
    """Create a note from provided content instead of clipboard"""
    if not content or not content.strip():
        print("Content is empty or invalid. Aborting.")
        sys.exit(1)
    if len(content.strip()) < 200:
        print("Content is less than 200 characters. Aborting.")
        sys.exit(1)

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    content = clean_grok_tags(content)

    if custom_title:
        full_title = custom_title
        short_title = custom_title.lower().replace(" ", "-")
        short_title = re.sub(r"[^a-z0-9-]", "", short_title)
    else:
        full_title_prompt = lambda c: (
            f"Generate a very short title in English (maximum six words, do not have single quote) for the following text and respond with only the title: {c}"
        )
        full_title = generate_title(content, 6, full_title_prompt)

        short_title_prompt = f"Generate a concise title for file naming (max 4 words, lowercase letters/numbers/hyphens only, no spaces/special chars/single quotes/underscores, use hyphens to join words) based on this title: {full_title}. Respond with just the title:"
        short_title = generate_short_title(short_title_prompt).lower()

        short_title = short_title.lower().strip("-")
        short_title = re.sub(r"[^a-z0-9-]", "", short_title)
        short_title = re.sub(r"-+", "-", short_title).strip("-")
        parts = short_title.split("-")
        if (
            not short_title
            or len(short_title) > 65
            or len(parts) > 6
            or any(len(p) > 15 or not p.isalnum() for p in parts)
        ):
            raise ValueError(
                f"Invalid short_title '{short_title}': must be only lowercase a-z0-9/-, <=65 chars, <=6 words (<=15 chars each). Regenerate."
            )

    file_path = create_filename(short_title, directory, date)
    front_matter = format_front_matter(full_title, date)
    content = clean_content(content)
    write_note(file_path, front_matter, content)
    return file_path


def create_note(date=None):
    if check_duplicate_notes():
        raise ValueError("Duplicate note found. Aborting note creation.")
    content = get_clipboard_content()
    return create_note_from_content(content, date=date)
