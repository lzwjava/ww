#!/usr/bin/env python3
import argparse
import os
import sys
import tempfile
from pathlib import Path

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


def _md_to_html(md_path, html_path, title):
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


def _html_to_jpg(html_path, output_jpg, quality, width):
    from playwright.sync_api import sync_playwright  # pyright: ignore[reportMissingImports]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 100})
        page.goto(f"file://{Path(html_path).resolve()}")
        page.wait_for_load_state("networkidle")

        # Get exact content height, resize to fit
        height = page.evaluate("document.body.scrollHeight")
        page.set_viewport_size({"width": width, "height": height})

        page.screenshot(
            path=output_jpg,
            full_page=True,
            type="jpeg",
            quality=quality,
        )
        browser.close()


def _frontmatter_title(md_path):
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


def _resolve_path(input_str):
    """Resolve partial filename to a .md file in CWD. Returns full path or None."""
    # Exact match
    if os.path.isfile(input_str):
        return input_str

    # Search .md files in CWD for substring match
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


def main():
    parser = argparse.ArgumentParser(
        description="Convert a markdown file to a JPG image via HTML screenshot (Playwright)"
    )
    parser.add_argument("markdown_file", help="Path to the markdown file")
    parser.add_argument("--output", "-o", help="Output JPG path (default: <input>.jpg)")
    parser.add_argument(
        "--output-dir", "-d", help="Output directory (default: same as input)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=90,
        help="JPG compression quality 1-100 (default: 90)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=900,
        help="Viewport width in pixels (default: 900)",
    )
    args = parser.parse_args()

    md_path = _resolve_path(args.markdown_file)
    if not md_path:
        print(f"Error: File not found: {md_path}")
        sys.exit(1)

    base = md_path[:-3] if md_path.lower().endswith(".md") else md_path
    if args.output:
        output_jpg = args.output
    elif args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_jpg = os.path.join(args.output_dir, os.path.basename(base) + ".jpg")
    else:
        output_jpg = base + ".jpg"
    title = _frontmatter_title(md_path) or os.path.basename(base)

    tmpdir = tempfile.mkdtemp(prefix="md2jpg-")
    try:
        html_path = os.path.join(tmpdir, "output.html")

        print("[1/2] markdown -> HTML")
        if not _md_to_html(md_path, html_path, title):
            sys.exit(1)

        print("[2/2] HTML -> JPG (Playwright screenshot)")
        _html_to_jpg(html_path, output_jpg, args.quality, args.width)
    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"Done: {output_jpg}")


if __name__ == "__main__":
    main()
