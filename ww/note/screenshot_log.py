import argparse
import base64
import os
import subprocess
import sys
from datetime import datetime

from dotenv import load_dotenv

from ww.llm.openrouter_client import (
    call_openrouter_api,
    call_openrouter_api_with_messages,
)
from ww.note.create_note_utils import (
    get_base_path,
    process_title_for_filename,
)


def _encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_screenshot_dir():
    env_dir = os.environ.get("SCREENSHOT_DIR", "").strip()
    return env_dir if env_dir else "."


def _get_latest_screenshots(screenshot_dir, n=1):
    if not os.path.isdir(screenshot_dir):
        print(f"Screenshot directory not found: {screenshot_dir}")
        sys.exit(1)
    files = [
        os.path.join(screenshot_dir, f)
        for f in os.listdir(screenshot_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if not files:
        print(f"No screenshots found in {screenshot_dir}")
        sys.exit(1)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    selected = files[:n]
    for p in selected:
        print(f"Using screenshot: {p}")
    return selected


DEFAULT_VISION_MODEL = "google/gemini-2.5-flash-image"


def _get_vision_model():
    return os.environ.get("VISION_MODEL", "").strip() or DEFAULT_VISION_MODEL


def _vision_describe(image_paths, prompt_text=None):
    content_parts = []
    for path in image_paths:
        b64 = _encode_image_to_base64(path)
        ext = os.path.splitext(path)[1].lstrip(".").lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
        content_parts.append(
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
        )
    instruction = "Describe what you see in this screenshot in detail."
    if prompt_text:
        instruction = prompt_text
    content_parts.insert(0, {"type": "text", "text": instruction})

    vision_model = _get_vision_model()
    print(f"Using vision model: {vision_model}")
    messages = [{"role": "user", "content": content_parts}]
    result = call_openrouter_api_with_messages(messages, model=vision_model)
    if not result:
        print("Failed to describe screenshot with LLM.")
        sys.exit(1)
    return result


def _summarize_with_extra_prompt(description, extra_prompt=None):
    if not extra_prompt:
        return description
    prompt = (
        f"Here is a description of a screenshot:\n\n{description}\n\n"
        f"Additional context from user:\n{extra_prompt}\n\n"
        f"Based on both the screenshot description and the user's context, "
        f"write a concise, informative note summarizing the key points."
    )
    result = call_openrouter_api(prompt)
    if not result:
        print("Failed to summarize with LLM. Using raw description.")
        return description
    return result


def _generate_title_from_content(content, extra_prompt=None):
    snippet = content[:800]
    prompt = "Give a short English title (at most 6 words, no quotes, no explanation) for the following content"
    if extra_prompt:
        prompt += f", considering this context: {extra_prompt}"
    prompt += f":\n{snippet}\n\nTitle:"
    result = call_openrouter_api(prompt, max_tokens=300)
    if not result:
        print("Failed to generate title. Using fallback.")
        return "screenshot-note"
    title = result.strip().strip('"').strip("'")
    return title


def _build_image_section(image_paths, notes_dir):
    lines = ["\n\n---\n\n**Screenshots:**\n"]
    for path in image_paths:
        rel = os.path.relpath(path, notes_dir)
        lines.append(f"![screenshot]({rel})")
    return "\n".join(lines)


def _format_front_matter_with_image(full_title, has_image, date=None):
    if ":" in full_title and '"' not in full_title:
        full_title = f'"{full_title}"'
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return f"""---
audio: false
generated: true
image: {"true" if has_image else "false"}
lang: en
layout: post
title: {full_title}
translated: false
type: note
---"""


def _get_github_repo_url():
    try:
        remote_url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    if remote_url.startswith("git@github.com:"):
        remote_url = remote_url.replace("git@github.com:", "https://github.com/")
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    return remote_url


def _print_note_url(file_path):
    if not file_path or not os.path.exists(file_path):
        return
    repo_url = _get_github_repo_url()
    if not repo_url:
        return
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return
    rel_path = os.path.relpath(os.path.abspath(file_path), repo_root).replace(
        os.sep, "/"
    )
    github_url = repo_url + "/blob/main/" + rel_path
    print(f"[info] Note created at {github_url}")


def _create_note_file(content, full_title, image_paths=None, date=None):
    notes_dir = os.path.join(get_base_path(), "notes")
    os.makedirs(notes_dir, exist_ok=True)
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    slug = process_title_for_filename(full_title)
    filename = f"{date}-{slug}-en.md"
    file_path = os.path.join(notes_dir, filename)
    if os.path.exists(file_path):
        print(f"Note already exists: {file_path}")
        sys.exit(1)
    has_image = bool(image_paths)
    front_matter = _format_front_matter_with_image(full_title, has_image, date)
    body = content
    if image_paths:
        body += _build_image_section(image_paths, notes_dir)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(front_matter + "\n\n" + body)
    print(f"Created note: {file_path}")
    return file_path


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Create a note from the latest screenshot(s) using LLM vision"
    )
    parser.add_argument(
        "-n",
        type=int,
        default=1,
        help="Number of latest screenshots to use (default: 1)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Extra prompt to guide LLM analysis and title generation",
    )
    args = parser.parse_args(sys.argv[1:])

    screenshot_dir = _get_screenshot_dir()
    image_paths = _get_latest_screenshots(screenshot_dir, args.n)

    print(f"Analyzing {len(image_paths)} screenshot(s) with LLM vision...")
    description = _vision_describe(image_paths, args.prompt)

    print("Summarizing content...")
    summary = _summarize_with_extra_prompt(description, args.prompt)

    print("Generating title...")
    full_title = _generate_title_from_content(summary, args.prompt)

    note_path = _create_note_file(summary, full_title, image_paths)
    _print_note_url(note_path)
