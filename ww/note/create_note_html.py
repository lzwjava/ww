"""
Create an HTML note from clipboard content — Jekyll-style with visual formatting.

Reads clipboard → LLM-converts to styled HTML → writes to {BASE_PATH}/notes/ with
Jekyll frontmatter. Works both standalone and through the note queue pipeline.
"""

import os
import re
from datetime import datetime

from ww.note.create_note_utils import (
    get_base_path,
    get_clipboard_content,
    clean_grok_tags,
    clean_content,
)
from ww.llm.openrouter_client import call_openrouter_api


def _generate_slug(content: str) -> str:
    """Generate a URL-friendly slug from content using LLM."""
    snippet = " ".join(content.split()[:300])
    prompt = (
        f"Generate a short URL slug (max 6 words, lowercase, hyphens only, "
        f"no punctuation, no extension) for this content:\n{snippet}\n\nSlug:"
    )
    result = call_openrouter_api(prompt, max_tokens=100)
    if not result:
        raise RuntimeError("Failed to generate slug from LLM.")
    slug = result.strip().lower().replace("'", "").replace("_", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = datetime.now().strftime("%Y%m%d-%H%M%S")
    parts = slug.split("-")
    if len(parts) > 8:
        slug = "-".join(parts[:8])
    return slug[:80].rstrip("-")


def _generate_title(content: str) -> str:
    """Generate an English title (at most 6 words)."""
    snippet = " ".join(content.split()[:500])
    prompt = (
        "Generate an English title (at most 6 words) for the given content."
        " Return ONLY the title, no explanation, no quotes, no markdown.\n\n"
        f"Content:\n{snippet}\n\nTitle:"
    )
    result = call_openrouter_api(prompt, max_tokens=50)
    if not result:
        raise RuntimeError("Failed to generate title from LLM.")
    title = re.sub(r"\*", "", result).strip().strip('"').strip("'")
    # If longer than 60 chars, truncate at word boundary
    if len(title) > 60:
        title = " ".join(title.split()[:6])
    return title


def _content_to_html(content: str) -> str:
    """Convert raw clipboard content to styled HTML suitable for a Jekyll post body.

    The LLM wraps the content in semantic HTML: headings, paragraphs, code blocks
    with syntax highlighting classes, lists, blockquotes, links, and images.
    Returns the inner HTML body content (no <html>/<body> wrapper — Jekyll layout
    provides that).
    """
    snippet = " ".join(content.split()[:2000])
    prompt = (
        "Convert the following content into clean, well-formatted HTML. Rules:\n"
        "- Use semantic HTML5 tags: <h2>, <h3>, <p>, <pre><code>, <ul>/<ol>, "
        "<blockquote>, <a>, <img>, <table>, <hr>\n"
        '- For code blocks: <pre><code class="language-xxx">...</code></pre> '
        "with appropriate language class\n"
        "- Escape all HTML entities (&, <, >, quotes) inside code blocks\n"
        "- Wrap inline code in <code> tags\n"
        '- Add class="centered" to wrapper divs around images if appropriate\n'
        "- Keep all original content — do not summarize or omit anything\n"
        "- Do NOT add <html>, <body>, or <head> tags (this goes inside a Jekyll post)\n"
        "- Do NOT wrap in backticks or markdown fences\n"
        "- Respond with ONLY the HTML, nothing else\n\n"
        f"Content:\n{snippet}"
    )
    result = call_openrouter_api(prompt, max_tokens=8192)
    if not result:
        # Fallback: basic HTML wrapping
        escaped = (
            content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        result = f"<p>{escaped.replace(chr(10), '<br>')}</p>"
    return result.strip()


def _format_front_matter(title: str, date: str | None = None) -> str:
    """Jekyll frontmatter for an HTML note post."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    quoted = f'"{title}"' if ":" in title and '"' not in title else title
    return f"""---
audio: false
generated: true
image: false
lang: en
layout: post
title: {quoted}
translated: false
type: note
---"""


def create_note_html(content=None, directory=None) -> str:
    """Create a Jekyll-compatible HTML note from clipboard content.

    Args:
        content: Text content (default: read from clipboard)
        directory: Output directory (default: {BASE_PATH}/notes/)

    Returns:
        Path to the created file
    """
    if directory is None:
        directory = os.path.join(get_base_path(), "notes")

    if content is None:
        content = get_clipboard_content()

    if not content or not content.strip():
        raise ValueError("Content is empty or invalid.")

    content = clean_grok_tags(content)
    content = clean_content(content)

    # Generate title and slug
    print("[html] Generating title...")
    full_title = _generate_title(content)
    print(f"[html] Title: {full_title}")

    slug = _generate_slug(content)

    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date}-{slug}-en.html"
    file_path = os.path.join(directory, filename)

    if os.path.exists(file_path):
        raise FileExistsError(f"HTML note already exists: {file_path}")

    print("[html] Converting content to HTML...")
    html_body = _content_to_html(content)

    front_matter = _format_front_matter(full_title, date)
    full_content = front_matter + "\n\n" + html_body

    os.makedirs(directory, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"[html] Created HTML note: {file_path}")
    return file_path


def main():
    """CLI entry point for 'ww note html'."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="ww note html", description="Create a Jekyll HTML note from clipboard"
    )
    parser.add_argument(
        "--dir",
        help="Output directory (default: {BASE_PATH}/notes/)",
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Enqueue for deferred processing via 'ww note process'",
    )
    args = parser.parse_args()

    if args.queue:
        from ww.note.note_queue import enqueue_html

        enqueue_html()
    else:
        file_path = create_note_html(directory=args.dir)
        print(f"[ok] HTML note ready at: {file_path}")


if __name__ == "__main__":
    main()
