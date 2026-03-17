#!/usr/bin/env python3
"""
Script to find directories larger than specified size in MB (default 1MB) in a given path (one subdirectory level)
Usage: ww find-large-dirs [--mb SIZE_MB] [directory_path]
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None


def get_directory_size_kb(directory_path):
    try:
        cmd = f'du -sk "{directory_path}"'
        result = run_command(cmd)
        if result:
            size_kb = int(result.split()[0])
            return size_kb
        return 0
    except (ValueError, AttributeError):
        return 0


def format_size(size_kb):
    if size_kb >= 1024 * 1024:
        gb = size_kb / (1024 * 1024)
        return f"{gb:.1f} GB"
    elif size_kb >= 1024:
        mb = size_kb / 1024
        return f"{mb:.0f} MB"
    else:
        return f"{size_kb} KB"


def find_large_directories(base_path, min_size_kb=1024):
    large_dirs = []

    try:
        base = Path(base_path).resolve()

        total_dirs = sum(1 for item in base.iterdir() if item.is_dir())
        if total_dirs == 0:
            return large_dirs

        print(f"Scanning {total_dirs} directories...")
        processed = 0

        for item in base.iterdir():
            if item.is_dir():
                processed += 1
                if processed % 10 == 0 or processed == total_dirs:
                    print(
                        f"   Scanned {processed}/{total_dirs} directories... ({processed * 100 // total_dirs}%)",
                        end="\r",
                        flush=True,
                    )

                size_kb = get_directory_size_kb(str(item))
                if size_kb >= min_size_kb:
                    large_dirs.append((item.name, size_kb))

        print("   " * 50, end="\r")

    except (OSError, PermissionError) as e:
        print(f"Error accessing directory {base_path}: {e}")
        return []

    large_dirs.sort(key=lambda x: x[1], reverse=True)
    return large_dirs


def main():
    parser = argparse.ArgumentParser(
        description="Find directories larger than specified size in MB (default 1MB)",
    )
    parser.add_argument(
        "--mb", type=int, default=1, help="Minimum directory size in MB (default: 1)"
    )
    parser.add_argument(
        "directory_path",
        nargs="?",
        default=".",
        help="Directory path to scan (default: current directory)",
    )

    args = parser.parse_args()

    min_size_kb = args.mb * 1024

    try:
        resolved_path = Path(args.directory_path).resolve()
        if not resolved_path.exists():
            print(f"Error: Path '{args.directory_path}' does not exist.")
            sys.exit(1)
        if not resolved_path.is_dir():
            print(f"Error: Path '{args.directory_path}' is not a directory.")
            sys.exit(1)
    except Exception as e:
        print(f"Error resolving path '{args.directory_path}': {e}")
        sys.exit(1)

    print(f"Finding directories larger than {args.mb} MB in: {resolved_path}")
    print("=" * 70)
    print()

    large_dirs = find_large_directories(resolved_path, min_size_kb)

    if not large_dirs:
        print(
            f"No directories larger than {args.mb} MB found in the immediate subdirectory level."
        )
        return

    print("Large directories found:")
    print()

    for name, size_kb in large_dirs:
        size_formatted = format_size(size_kb)
        print(f"   {name:<30} {size_formatted:>10}")

    print()
    print(f"Total: {len(large_dirs)} directory(ies) larger than {args.mb} MB")
