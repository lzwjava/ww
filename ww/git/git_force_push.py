import subprocess
import sys


def check_git_status():
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True
    )
    if result.stdout.strip():
        raise RuntimeError(
            "Cannot force push: You have unstaged changes. Please commit or stash them first."
        )


def get_current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
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
        ["git", "push", "--force-with-lease", "origin", current_branch], check=True
    )
