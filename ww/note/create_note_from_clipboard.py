import os
import re
import sys
from datetime import datetime

from ww.note.create_note_utils import (
    get_base_path,
    get_clipboard_content,
    clean_grok_tags,
    generate_title,
    create_filename,
    format_front_matter,
    clean_content,
    write_note,
)
from ww.note.check_duplicate_notes import check_duplicate_notes


def _generate_titles(content):
    full_title_prompt = lambda c: (
        f"Give a short English title (at most 6 words, no quotes, no explanation) for:\n{c}\n\nTitle:"
    )
    full_title = generate_title(content, 6, full_title_prompt)
    short_title = _title_to_slug(full_title)
    return full_title, short_title


def _title_to_slug(title):
    slug = title.lower().replace("'", "").replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise ValueError(f"Slug derived from title is empty: {title!r}")
    parts = slug.split("-")
    if len(parts) > 8:
        slug = "-".join(parts[:8])
    if len(slug) > 80:
        slug = slug[:80].rstrip("-")
    return slug


def _titles_from_custom(custom_title):
    full_title = custom_title
    short_title = re.sub(r"[^a-z0-9-]", "", custom_title.lower().replace(" ", "-"))
    return full_title, short_title


def create_note_from_content(content, custom_title=None, directory=None, date=None):
    if directory is None:
        directory = os.path.join(get_base_path(), "notes")
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
        full_title, short_title = _titles_from_custom(custom_title)
    else:
        full_title, short_title = _generate_titles(content)

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
