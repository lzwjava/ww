import argparse
import subprocess
from pathlib import Path


def list_files_excluding_ext(repo, commit, exclude_ext):
    cmd = ["git", "-C", str(repo), "diff-tree", "--no-commit-id", "--name-only", "-r", commit]
    try:
        output = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git diff-tree failed: {e}") from e

    files = output.strip().splitlines()
    if exclude_ext.startswith("."):
        exclude_ext = exclude_ext[1:]
    exclude_ext = exclude_ext.lower()
    return [f for f in files if not f.lower().endswith(f".{exclude_ext}")]


def main():
    parser = argparse.ArgumentParser(
        description="List files changed by a specific git commit, excluding a given extension.",
        usage="%(prog)s repo_path commit_hash [--exclude-ext EXT]",
    )
    parser.add_argument("repo", type=Path, help="Path to the git repository.")
    parser.add_argument("commit", help="Commit hash to inspect.")
    parser.add_argument("--exclude-ext", default="py", help="File extension to exclude (default: py).")
    args = parser.parse_args()

    try:
        files = list_files_excluding_ext(args.repo, args.commit, args.exclude_ext)
    except RuntimeError as e:
        print(e)
        return

    if files:
        print(f"Files changed (excluding .{args.exclude_ext}):")
        for f in files:
            print(f)
    else:
        print(f"No files changed (excluding .{args.exclude_ext}) in this commit.")
