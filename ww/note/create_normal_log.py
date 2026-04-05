import os
import re

from ww.note.create_note_utils import (
    get_base_path,
    get_clipboard_content,
    generate_title,
)
from ww.github.gitmessageai import gitmessageai


def create_normal_log(content=None):
    logs_dir = os.path.join(get_base_path(), "logs")
    if content is None:
        content = get_clipboard_content()

    filename_prompt = lambda c: (
        f"Generate a short filename with extension (maximum 4 words before the extension, all lowercase, use ONLY letters a-z, numbers 0-9, and hyphens - for separation, then a dot and appropriate file extension based on the content type, e.g. my-config.yaml, server-error.log, build-script.sh). NO underscores, single quotes, backticks, or markdown syntax. Respond with only the filename in the format filename.ext: {c}"
    )
    ai_filename = (
        generate_title(content, 4, filename_prompt)
        .lower()
        .replace("_", "-")
        .replace("`", "")
        .strip()
    )

    match = re.match(r"^([a-z0-9-]+)\.([a-z0-9]+)$", ai_filename)
    if not match:
        raise ValueError(
            f"Invalid filename '{ai_filename}': expected format like 'name.ext' with lowercase letters, numbers, and hyphens"
        )

    os.makedirs(logs_dir, exist_ok=True)
    file_path = os.path.join(logs_dir, ai_filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Log created: {file_path}")

    gitmessageai(allow_pull_push=True, directory=logs_dir)
    print(f"Git operations ran in: {logs_dir}")
