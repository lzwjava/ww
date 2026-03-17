import subprocess
import sys
from pathlib import Path


def run_command(command, check=True, repo_path=None):
    cwd = repo_path if repo_path is not None else Path.cwd()
    print(f"Running command: {' '.join(command)} (cwd={cwd})")
    result = subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=True,
        cwd=str(cwd),
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result


def stage_changes(repo_path):
    run_command(["git", "add", "-A"], repo_path=repo_path)


def amend_commit(repo_path):
    run_command(["git", "commit", "--amend", "--no-edit"], repo_path=repo_path)


def push_changes(repo_path):
    run_command(["git", "push", "--force-with-lease"], repo_path=repo_path)


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    if args:
        repo_path = Path(args[0]).expanduser().resolve()
    else:
        repo_path = Path.cwd()

    if not repo_path.is_dir():
        print(f"Error: '{repo_path}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    stage_changes(repo_path)
    amend_commit(repo_path)
    push_changes(repo_path)
