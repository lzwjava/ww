#!/usr/bin/env python3
"""Shared utilities for md2jpg and md2png."""

import os
import sys
import tempfile

_CSS = """
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 40px;
  color: #24292e;
}
h1, h2, h3, h4, h5, h6 {
  margin-top: 1.4em;
  margin-bottom: 0.4em;
  font-weight: 600;
  line-height: 1.25;
}
h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
code {
  background-color: rgba(27,31,35,0.07);
  border-radius: 3px;
  font-size: 85%;
  padding: 0.2em 0.4em;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}
pre {
  background-color: #f6f8fa;
  border-radius: 3px;
  font-size: 85%;
  line-height: 1.45;
  overflow: auto;
  padding: 16px;
}
pre code {
  background-color: transparent;
  padding: 0;
  font-size: inherit;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1em;
}
table th, table td {
  border: 1px solid #dfe2e5;
  padding: 6px 13px;
}
table tr:nth-child(even) { background-color: #f6f8fa; }
table th { background-color: #f0f0f0; font-weight: 600; }
blockquote {
  border-left: 4px solid #dfe2e5;
  color: #6a737d;
  margin: 0 0 1em 0;
  padding: 0 1em;
}
img { max-width: 100%; }
hr { border: none; border-top: 1px solid #eaecef; margin: 1.5em 0; }
"""


def md_to_html(md_path, html_path, title):
    import shutil
    import subprocess

    tmpdir = tempfile.mkdtemp()
    try:
        header_file = os.path.join(tmpdir, "header.html")
        with open(header_file, "w") as f:
            f.write(f"<style>\n{_CSS}\n</style>\n")

        cmd = [
            "pandoc",
            md_path,
            "-o",
            html_path,
            "--standalone",
            "--metadata",
            f"title={title}",
            "--include-in-header",
            header_file,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"pandoc error: {result.stderr}")
            return False
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


_QUALITY_PRESETS = {
    "low": {"width": 600, "quality": 60},
    "medium": {"width": 900, "quality": 80},
    "high": {"width": 1200, "quality": 95},
}


def html_to_image(
    html_path, output_path, width, img_type="jpeg", quality=None, preset=None
):
    from pathlib import Path

    from playwright.sync_api import sync_playwright  # pyright: ignore[reportMissingImports]

    # Apply preset if provided
    if preset and preset in _QUALITY_PRESETS:
        p = _QUALITY_PRESETS[preset]
        width = p["width"]
        if img_type == "jpeg":
            quality = p["quality"]
    elif preset:
        print(f"Unknown preset '{preset}'. Use: low, medium, high")
        return

    kwargs = {"path": output_path, "full_page": True, "type": img_type}
    if quality is not None:
        kwargs["quality"] = quality

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 100})
        page.goto(f"file://{Path(html_path).resolve()}")
        page.wait_for_load_state("networkidle")

        height = page.evaluate("document.body.scrollHeight")
        page.set_viewport_size({"width": width, "height": height})

        page.screenshot(**kwargs)
        browser.close()


def frontmatter_title(md_path):
    """Return the title from YAML frontmatter, or None if not found."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() in ("---", "..."):
            break
        if line.lower().startswith("title:"):
            value = line[len("title:") :].strip().strip('"').strip("'")
            return value or None
    return None


def resolve_path(input_str):
    """Resolve partial filename to a .md file in CWD. Returns full path or None."""
    if os.path.isfile(input_str):
        return input_str

    cwd = os.getcwd()
    candidates = []
    for f in os.listdir(cwd):
        if not f.endswith(".md"):
            continue
        if input_str.lower() in f.lower():
            candidates.append(f)

    if len(candidates) == 1:
        return os.path.join(cwd, candidates[0])
    elif len(candidates) > 1:
        print(f"Multiple matches for '{input_str}':")
        for c in candidates:
            print(f"  {c}")
        sys.exit(1)
    else:
        print(f"No .md file matching '{input_str}' in {cwd}")
        sys.exit(1)


def resolve_output(md_path, arg_output, arg_output_dir, ext):
    """Determine output file path."""
    base = md_path[:-3] if md_path.lower().endswith(".md") else md_path
    if arg_output:
        return arg_output
    if arg_output_dir:
        os.makedirs(arg_output_dir, exist_ok=True)
        return os.path.join(arg_output_dir, os.path.basename(base) + ext)
    return base + ext
