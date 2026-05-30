import os
import re
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
        raise ValueError("Content is empty or invalid.")
    if len(content.strip()) < 200:
        raise ValueError(
            f"Content is less than 200 characters ({len(content.strip())} chars). Aborting."
        )

    # Check for duplicates before creating
    from ww.note.check_duplicate_notes import (
        _are_notes_quick_similar,
        _extract_content_without_frontmatter,
    )
    from pathlib import Path

    notes_path = Path(directory)
    if notes_path.exists():
        note_files = sorted(
            notes_path.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True
        )
        cleaned_content = clean_grok_tags(content)
        cleaned_content = clean_content(cleaned_content)

        for note_file in note_files[:200]:  # Check against latest 200 notes
            try:
                existing_content = _extract_content_without_frontmatter(note_file)
                if _are_notes_quick_similar(cleaned_content, existing_content):
                    raise ValueError(
                        f"Duplicate note detected: content similar to {note_file.name}"
                    )
            except ValueError:
                raise
            except Exception as e:
                print(f"[warn] Error checking {note_file.name}: {e}")

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
