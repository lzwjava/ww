import os
import random
import subprocess
import argparse
from datetime import datetime, timedelta
from typing import Optional

from ww.create.gpa import gpa
from ww.create.create_note_from_clipboard import create_note
from ww.content.fix_mathjax import fix_mathjax_in_file
from ww.content.fix_table import process_tables_in_file


def check_uncommitted_changes() -> None:
    try:
        toplevel = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        result = subprocess.run(
            ["git", "-C", toplevel, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            print(
                "[error] Uncommitted changes detected. Please commit or stash your changes before running this script."
            )
            raise RuntimeError("Uncommitted changes found")
    except subprocess.CalledProcessError as e:
        print(f"[error] Failed to check git status: {e}")
        raise


def git_pull_rebase() -> None:
    try:
        toplevel = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        print(f"[info] Running 'git pull --rebase' in {toplevel}...")
        subprocess.run(["git", "-C", toplevel, "pull", "--rebase"], check=True)
    except Exception as e:
        print(f"[error] git pull --rebase failed: {e}")
        raise


def open_note_in_browser(note_path: Optional[str], repo_url: str) -> None:
    if not note_path:
        return

    abs_note_path = os.path.abspath(note_path)

    try:
        import subprocess as sp
        repo_root = sp.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        rel_path = os.path.relpath(abs_note_path, repo_root)
    except Exception as exc:
        print(f"[warn] Unable to compute relative path for {abs_note_path}: {exc}")
        return

    github_url = repo_url.rstrip("/") + "/blob/main/" + rel_path.replace(os.sep, "/")

    import sys
    if sys.platform.startswith("darwin"):
        command = ["open", github_url]
    elif sys.platform.startswith("linux"):
        command = ["env", "NO_AT_BRIDGE=1", "xdg-open", github_url]
    else:
        try:
            import webbrowser
            if not webbrowser.open(github_url):
                print(f"[warn] webbrowser module could not launch {github_url}")
        except Exception as exc:
            print(f"[warn] Unable to launch browser for {github_url}: {exc}")
        return

    try:
        subprocess.run(command, check=False)
    except FileNotFoundError:
        print(f"[warn] Launch command not found when opening {github_url}")
    except Exception as exc:
        print(f"[warn] Failed to open browser for {github_url}: {exc}")


def generate_random_date():
    random.seed(datetime.now().timestamp())
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    random_days = random.randint(0, 180)
    return (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")


def parse_args():
    parser = argparse.ArgumentParser(description="Create a note.")
    parser.add_argument("--random", action="store_true", help="Use a random date within last 180 days")
    parser.add_argument("--without-math", action="store_true", help="Skip fixing MathJax delimiters")
    parser.add_argument("--gemini", action="store_true", help="Enable Gemini-specific MathJax fixing")
    parser.add_argument("--open", action="store_true", help="Open the note in browser after creating")
    parser.add_argument("--no-push", action="store_true", help="Skip the gpa git push step")
    parser.add_argument("--repo-url", default="https://github.com/lzwjava/blog-source", help="GitHub repo URL for --open")
    return parser.parse_args()


def main():
    check_uncommitted_changes()
    git_pull_rebase()

    args = parse_args()
    random_date = generate_random_date() if args.random else None
    print(f"[debug] random_date: {random_date}")

    created_path = create_note(date=random_date)

    if not args.without_math and created_path and os.path.exists(created_path):
        try:
            fix_mathjax_in_file(created_path, gemini=args.gemini)
            process_tables_in_file(created_path, fix_tables=True)
        except Exception as e:
            print(f"[warn] MathJax fix failed for {created_path}: {e}")

    if not args.no_push:
        gpa()

    if args.open:
        try:
            open_note_in_browser(created_path, args.repo_url)
        except Exception as e:
            print(f"[warn] Failed to open browser: {e}")

    print(f"[info] Note created at {created_path}")
