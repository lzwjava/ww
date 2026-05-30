#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
import tempfile

from ww.md._shared import (
    frontmatter_title,
    html_to_image,
    md_to_html,
    resolve_output,
    resolve_path,
)


def main():
    parser = argparse.ArgumentParser(
        description="Convert a markdown file to JPG/PNG via HTML screenshot (Playwright)"
    )
    parser.add_argument("markdown_file", help="Path to the markdown file")
    parser.add_argument(
        "--format",
        "-f",
        choices=["jpg", "png"],
        default="png",
        help="Output format: jpg or png (default: png)",
    )
    parser.add_argument(
        "--output", "-o", help="Output path (default: <input>.<format>)"
    )
    parser.add_argument(
        "--output-dir", "-d", help="Output directory (default: same as input)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        help="JPG compression quality 1-100 (overrides preset, JPG only)",
    )
    parser.add_argument(
        "--preset",
        choices=["low", "medium", "high"],
        default="medium",
        help="Quality preset: low (600px), medium (900px), high (1200px). Default: medium",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Viewport width in pixels (overrides preset)",
    )
    args = parser.parse_args()

    fmt = args.format
    ext = f".{fmt}"
    img_type = "jpeg" if fmt == "jpg" else "png"

    md_path = resolve_path(args.markdown_file)
    output = resolve_output(md_path, args.output, args.output_dir, ext)
    title = frontmatter_title(md_path) or os.path.basename(
        md_path[:-3] if md_path.lower().endswith(".md") else md_path
    )

    width = args.width
    quality = args.quality

    tmpdir = tempfile.mkdtemp(prefix="md2img-")
    try:
        html_path = os.path.join(tmpdir, "output.html")

        print("[1/2] markdown -> HTML")
        if not md_to_html(md_path, html_path, title):
            sys.exit(1)

        print(f"[2/2] HTML -> {fmt.upper()} (preset: {args.preset})")
        html_to_image(
            html_path,
            output,
            width=width or 900,
            img_type=img_type,
            quality=quality,
            preset=args.preset if not width and not quality else None,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"Done: {output}")


if __name__ == "__main__":
    main()
