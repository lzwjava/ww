import os
import re
from datetime import datetime

from ww.llm.openrouter_client import call_openrouter_api
from ww.note.create_note_utils import (
    get_base_path,
    get_clipboard_content,
    get_first_n_words,
)
from ww.github.gitmessageai import gitmessageai


def generate_filename_with_ext(content, ext):
    snippet = get_first_n_words(content)
    prompt = f"Generate a short filename WITHOUT extension (maximum 4 words, all lowercase, use ONLY letters a-z, numbers 0-9, and hyphens - for separation). NO underscores, single quotes, backticks, or markdown syntax. Respond with only the name: {snippet}"
    result = call_openrouter_api(prompt)
    if not result:
        raise RuntimeError("Failed to generate filename from LLM.")
    name = (
        result.strip()
        .lower()
        .replace("_", "-")
        .replace("`", "")
        .replace("*", "")
        .strip()
        .rstrip(".")
    )
    name = re.sub(r"\.[a-z0-9]+$", "", name)
    return f"{name}.{ext}"


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


def detect_extension(content):
    snippet = get_first_n_words(content)
    prompt = f"Detect the file extension for the following content. Extension rules: if content has markdown formatting (headers, bold, lists, links) use md, shell scripts use sh, Python use py, JavaScript use js, TypeScript use ts, JSON use json, YAML use yaml, HTML use html, CSS use css, SQL use sql, XML use xml, plain logs use log, config files use their native extension, otherwise use txt. Respond with ONLY the extension (no dot), e.g. md or txt: {snippet}"
    result = call_openrouter_api(prompt)
    if not result:
        return "txt"
    ext = result.strip().lower().replace(".", "").replace("`", "")
    if re.match(r"^[a-z0-9]+$", ext):
        return ext
    return "txt"


def generate_timestamp_filename(ext):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}.{ext}"


def create_normal_log(content=None, ext=None, friendly_name=False, detect_ext=False):
    logs_dir = os.path.join(get_base_path(), "logs")
    if content is None:
        content = get_clipboard_content()

    if friendly_name:
        if ext:
            ai_filename = generate_filename_with_ext(content, ext)
        else:
            ai_filename = generate_filename(content)
    else:
        resolved_ext = ext or (detect_extension(content) if detect_ext else "log")
        ai_filename = generate_timestamp_filename(resolved_ext)

    match = re.match(r"^[a-z0-9_-]+\.[a-z0-9]+$", ai_filename)
    if not match:
        raise ValueError(
            f"Invalid filename '{ai_filename}': expected format like 'name.ext' with lowercase letters, numbers, hyphens, and underscores"
        )

    os.makedirs(logs_dir, exist_ok=True)
    file_path = os.path.join(logs_dir, ai_filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Log created: {file_path}")

    gitmessageai(allow_pull_push=True, directory=logs_dir)
    print(f"Git operations ran in: {logs_dir}")
