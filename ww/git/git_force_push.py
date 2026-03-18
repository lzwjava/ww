import subprocess
import sys

from ww.note.create_note_utils import get_base_path


def check_git_status():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=get_base_path(),
    )
    if result.stdout.strip():
        raise RuntimeError(
            "Cannot force push: You have unstaged changes. Please commit or stash them first."
        )


def get_current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
        cwd=get_base_path(),
    )
    return result.stdout.strip()


def main():
    try:
        check_git_status()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    current_branch = get_current_branch()
    subprocess.run(
        ["git", "push", "--force-with-lease", "origin", current_branch],
        check=True,
        cwd=get_base_path(),
    )
