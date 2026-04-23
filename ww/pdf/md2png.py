#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
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


def _chrome_path():
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome",
        "chromium",
        "chromium-browser",
    ]
    for c in candidates:
        if os.path.isabs(c):
            if os.path.isfile(c):
                return c
        elif shutil.which(c):
            return c
    return None


def _md_to_html(md_path, html_path, title):
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


def _html_to_pdf(html_path, pdf_path, chrome):
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        f"--print-to-pdf={os.path.abspath(pdf_path)}",
        "--no-pdf-header-footer",
        f"file://{os.path.abspath(html_path)}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Chrome error: {result.stderr}")
        return False
    if not os.path.isfile(pdf_path):
        print("Chrome did not produce a PDF.")
        return False
    return True


def _pdf_to_png(pdf_path, output_png, density):
    tmpdir = tempfile.mkdtemp()
    try:
        pages_pattern = os.path.join(tmpdir, "page-%02d.png")
        cmd = [
            "magick",
            "-density",
            str(density),
            pdf_path,
            "-quality",
            "95",
            pages_pattern,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ImageMagick error: {result.stderr}")
            return False

        pages = sorted(
            f
            for f in os.listdir(tmpdir)
            if f.startswith("page-") and f.endswith(".png")
        )
        if not pages:
            print("No pages generated from PDF.")
            return False

        page_paths = [os.path.join(tmpdir, p) for p in pages]

        if len(page_paths) == 1:
            shutil.copyfile(page_paths[0], output_png)
        else:
            cmd = ["magick"] + page_paths + ["-append", output_png]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"ImageMagick append error: {result.stderr}")
                return False

        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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


def main():
    parser = argparse.ArgumentParser(
        description="Convert a markdown file to a single PNG image via HTML → PDF → PNG"
    )
    parser.add_argument("markdown_file", help="Path to the markdown file")
    parser.add_argument("--output", "-o", help="Output PNG path (default: <input>.png)")
    parser.add_argument(
        "--output-dir", "-d", help="Output directory (default: same as input)"
    )
    parser.add_argument(
        "--density",
        type=int,
        default=150,
        help="DPI for PDF→PNG conversion (default: 150)",
    )
    args = parser.parse_args()

    md_path = args.markdown_file
    if not os.path.isfile(md_path):
        print(f"Error: File not found: {md_path}")
        sys.exit(1)

    base = md_path[:-3] if md_path.lower().endswith(".md") else md_path
    if args.output:
        output_png = args.output
    elif args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_png = os.path.join(args.output_dir, os.path.basename(base) + ".png")
    else:
        output_png = base + ".png"
    title = _frontmatter_title(md_path) or os.path.basename(base)

    chrome = _chrome_path()
    if not chrome:
        print(
            "Error: Chrome or Chromium not found. Install Google Chrome and try again."
        )
        sys.exit(1)

    tmpdir = tempfile.mkdtemp(prefix="md2png-")
    try:
        html_path = os.path.join(tmpdir, "output.html")
        pdf_path = os.path.join(tmpdir, "output.pdf")

        print("[1/3] markdown → HTML")
        if not _md_to_html(md_path, html_path, title):
            sys.exit(1)

        print("[2/3] HTML → PDF")
        if not _html_to_pdf(html_path, pdf_path, chrome):
            sys.exit(1)

        print("[3/3] PDF → PNG")
        if not _pdf_to_png(pdf_path, output_png, args.density):
            sys.exit(1)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"Done: {output_png}")


if __name__ == "__main__":
    main()
