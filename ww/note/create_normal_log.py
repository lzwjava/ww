import os
import re

from ww.llm.openrouter_client import call_openrouter_api
from ww.note.create_note_utils import (
    get_base_path,
    get_clipboard_content,
    get_first_n_words,
)
from ww.github.gitmessageai import gitmessageai


def generate_filename(content):
    snippet = get_first_n_words(content)
    prompt = f"Generate a short filename with extension (maximum 4 words before the extension, all lowercase, use ONLY letters a-z, numbers 0-9, and hyphens - for separation, then a dot and appropriate file extension based on the content type). Extension rules: if content has markdown formatting (headers, bold, lists, links) use .md, shell scripts use .sh, Python use .py, JavaScript use .js, TypeScript use .ts, JSON use .json, YAML use .yaml, HTML use .html, CSS use .css, SQL use .sql, XML use .xml, plain logs use .log, config files use their native extension, otherwise use .txt. Examples: my-config.yaml, server-error.log, build-script.sh, api-notes.md. NO underscores, single quotes, backticks, or markdown syntax in your response. Respond with only the filename in the format filename.ext: {snippet}"
    result = call_openrouter_api(prompt)
    if not result:
        raise RuntimeError("Failed to generate filename from LLM.")
    return (
        result.strip()
        .lower()
        .replace("_", "-")
        .replace("`", "")
        .replace("*", "")
        .strip()
    )


def create_normal_log(content=None):
    logs_dir = os.path.join(get_base_path(), "logs")
    if content is None:
        content = get_clipboard_content()

    ai_filename = generate_filename(content)

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
