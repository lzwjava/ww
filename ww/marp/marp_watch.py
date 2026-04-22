#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import time


def _run_marp_once(md_path, format_flag, ext):
    cmd = ["marp", md_path, format_flag, "--allow-local-files"]
    print(f"[marp] {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode == 0:
        out_path = os.path.splitext(md_path)[0] + ext
        print(f"[marp] generated: {out_path}")
    else:
        print(f"[marp] failed with exit code {result.returncode}")


def _run_marp(md_path, formats):
    for format_flag, ext in formats:
        _run_marp_once(md_path, format_flag, ext)


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Watch a markdown file and regenerate via marp on change."
    )
    parser.add_argument("markdown_file", help="Path to the markdown file to watch")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds (default: 1.0)",
    )
    parser.add_argument("--pdf", action="store_true", help="Generate PDF output")
    parser.add_argument("--html", action="store_true", help="Generate HTML output")
    args = parser.parse_args()

    formats = []
    if args.pdf:
        formats.append(("--pdf", ".pdf"))
    if args.html:
        formats.append(("--html", ".html"))
    if not formats:
        formats = [("--pdf", ".pdf")]

    md_path = os.path.abspath(args.markdown_file)

    if not os.path.isfile(md_path):
        print(f"Error: file not found: {md_path}")
        sys.exit(1)

    if shutil.which("marp") is None:
        print("Error: 'marp' CLI not found. Install via: npm i -g @marp-team/marp-cli")
        sys.exit(1)

    print(f"[marp] watching {md_path} (interval={args.interval}s). Ctrl-C to stop.")
    _run_marp(md_path, formats)
    last = _mtime(md_path)

    try:
        while True:
            time.sleep(args.interval)
            current = _mtime(md_path)
            if current is None:
                print(f"[marp] file disappeared: {md_path}")
                continue
            if current != last:
                last = current
                _run_marp(md_path, formats)
    except KeyboardInterrupt:
        print("\n[marp] stopped.")
