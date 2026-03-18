import subprocess
import sys
import re

from ww.note.create_note_utils import get_base_path


def get_commits_with_deletions(n):
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-n", str(n), "--format=%H"],
            capture_output=True,
            text=True,
            cwd=get_base_path(),
        )
        if result.returncode != 0:
            print(f"Error getting commits: {result.stderr}", file=sys.stderr)
            return []
        commits = result.stdout.strip().split("\n")
        return [c for c in commits if c]
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return []


def get_changed_files_count(commit_hash):
    try:
        result = subprocess.run(
            ["git", "show", "--stat", commit_hash],
            capture_output=True,
            text=True,
            cwd=get_base_path(),
        )
        if result.returncode != 0:
            return 0
        for line in result.stdout.split("\n"):
            if "files changed" in line:
                match = re.search(r"(\d+)\s+files? changed", line)
                if match:
                    return int(match.group(1))
        return 0
    except OSError as e:
        print(f"Error getting deletion count for {commit_hash}: {e}", file=sys.stderr)
        return 0


def main():
    if len(sys.argv) != 3:
        print("Usage: ww git-delete-commit <n> <m>", file=sys.stderr)
        print("  n: number of recent commits to check", file=sys.stderr)
        print("  m: minimum number of files with deletions required", file=sys.stderr)
        sys.exit(1)

    try:
        n = int(sys.argv[1])
        m = int(sys.argv[2])
    except ValueError:
        print("Error: n and m must be integers", file=sys.stderr)
        sys.exit(1)

    if n <= 0 or m < 0:
        print("Error: n must be > 0 and m must be >= 0", file=sys.stderr)
        sys.exit(1)

    commits = get_commits_with_deletions(n)
    for commit_hash in commits:
        changed_files_count = get_changed_files_count(commit_hash)
        if changed_files_count > m:
            print(f"{commit_hash}: {changed_files_count}")
            sys.exit(0)

    print("none")
