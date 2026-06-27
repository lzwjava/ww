import os
import re
import datetime
import pyperclip

from ww.llm.openrouter_client import call_openrouter_api


def get_base_path():
    base = os.environ.get("BASE_PATH", "").strip()
    return base if base and base != "." else "."


def get_first_n_words(text, n=500):
    words = text.split()
    return " ".join(words[:n])


def process_title_for_filename(title):
    title = title.strip()
    title = re.sub(r"\s+", "-", title)
    title = re.sub(r"[^a-zA-Z0-9-]", "", title)
    title = title.lower()
    return title


def clean_grok_tags(content):
    if "<grok:render" in content:
        prompt = f"""Remove all <grok:render> tags and their contents from the following text, and format the text cleanly by removing extra spaces and ensuring proper sentence spacing. Respond with only the cleaned text:

{content}"""
        cleaned_content = call_openrouter_api(prompt)
        if not cleaned_content:
            print("Failed to clean grok tags. Using original content.")
            return content
        return cleaned_content.strip()
    return content


def get_clipboard_content():
    return pyperclip.paste()


def _call_llm_or_exit(prompt, error_msg, max_tokens=None):
    model = os.getenv("MODEL", "(not set)")
    try:
        result = call_openrouter_api(prompt, max_tokens=max_tokens)
    except Exception as e:
        raise RuntimeError(
            f"LLM call failed. Model: {model}, max_tokens: {max_tokens}\n"
            f"Prompt (first 300 chars): {prompt[:300]}\n"
            f"Exception: {e}"
        ) from e

    if not result:
        raise RuntimeError(
            f"LLM returned empty result. Model: {model}, max_tokens: {max_tokens}\n"
            f"Prompt (first 300 chars): {prompt[:300]}\n{error_msg}"
        )
    return result


TITLE_MAX_CHARS = 100
TITLE_MAX_RETRIES = 3


def generate_title(content, max_words, format_prompt):
    prompt = format_prompt(get_first_n_words(content))
    for attempt in range(1, TITLE_MAX_RETRIES + 1):
        raw = _call_llm_or_exit(
            prompt,
            f"Failed to generate title with max {max_words} words. Exit.",
            max_tokens=1024,
        )
        title = re.sub(r"\*", " ", raw).strip()
        if len(title) < TITLE_MAX_CHARS:
            return title
        if attempt < TITLE_MAX_RETRIES:
            print(
                f"[warn] Title too long ({len(title)} chars), retrying ({attempt}/{TITLE_MAX_RETRIES})..."
            )
    raise ValueError(
        f"Generated title still >= {TITLE_MAX_CHARS} chars after {TITLE_MAX_RETRIES} retries: {title!r}."
    )


def generate_short_title(prompt):
    return _call_llm_or_exit(prompt, "Failed to generate short title. Exit.")


def create_filename(short_title, notes_dir=None, date=None):
    if notes_dir is None:
        notes_dir = os.path.join(get_base_path(), "notes")
    if date is None:
        date_str = datetime.date.today().strftime("%Y-%m-%d")
    else:
        date_str = date
    if not os.path.exists(notes_dir):
        os.makedirs(notes_dir)
    base_file_name = f"{date_str}-{short_title}-en.md"
    file_path = os.path.join(notes_dir, base_file_name)
    if os.path.exists(file_path):
        raise FileExistsError(
            f"Note already exists: {file_path}. Refusing to create a duplicate "
            f"with a counter suffix. Remove the existing note or pick a different title."
        )
    return file_path


def format_front_matter(full_title, date=None):
    if ":" in full_title and '"' not in full_title:
        full_title = f'"{full_title}"'
    if date is None:
        date = datetime.date.today().strftime("%Y-%m-%d")
    return f"""---
audio: false
generated: true
image: false
lang: en
layout: post
title: {full_title}
translated: false
type: note
---"""


def fix_liquid_raw_tags(content):
    """Wrap fenced code blocks containing {{ or {% with {% raw %}...{% endraw %}
    to prevent Jekyll Liquid parsing errors during the CI build.

    Jekyll's Liquid parser runs before Markdown rendering, so any {{ }} or
    {% %} patterns in code blocks — even fenced ``` blocks — get parsed as
    Liquid expressions and can crash the build. This function wraps affected
    blocks so Liquid leaves them untouched.
    """
    lines = content.split("\n")
    result = []
    i = 0
    fixed_count = 0
    while i < len(lines):
        stripped = lines[i].strip()
        fence_match = re.match(r"^(```|~~~)", stripped)
        if fence_match:
            fence_char = fence_match.group(1)
            block_lines = [lines[i]]
            i += 1
            while i < len(lines):
                block_lines.append(lines[i])
                if lines[i].strip().startswith(fence_char):
                    i += 1
                    break
                i += 1

            full_block = "\n".join(block_lines)
            if re.search(r"\{\{|\{\%", full_block):
                already = False
                if result:
                    last = result[-1].strip()
                    if re.match(r"\{%-?\s*raw\s*-?%\}", last):
                        already = True
                if not already:
                    result.append("{% raw %}")
                    result.extend(block_lines)
                    result.append("{% endraw %}")
                    fixed_count += 1
                else:
                    result.extend(block_lines)
            else:
                result.extend(block_lines)
        else:
            result.append(lines[i])
            i += 1

    if fixed_count > 0:
        print(
            f"[fix] Wrapped {fixed_count} code block(s) with "
            f"{{% raw %}} tags for Liquid safety"
        )

    return "\n".join(result)


def clean_content(content):
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        content = "\n".join(lines[1:])
    content = content.strip()
    lines = content.splitlines()
    while lines and lines[0].strip() == "---":
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def write_note(file_path, front_matter, content):
    content = fix_liquid_raw_tags(content)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(front_matter + "\n\n" + content)
    print(f"Created note: {file_path}")
