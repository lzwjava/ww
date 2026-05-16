import os
import sys
import random
import subprocess
import webbrowser
import argparse
from datetime import datetime, timedelta
from typing import Optional

from ww.github.gitmessageai import gitmessageai
from ww.note.create_note_from_clipboard import create_note
from ww.note.create_note_utils import get_base_path
from ww.content.fix_mathjax import fix_mathjax_in_file
from ww.content.fix_table import process_tables_in_file


def _git_toplevel() -> str:
    base = get_base_path()
    cmd = ["git", "rev-parse", "--show-toplevel"]
    if base != ".":
        cmd = ["git", "-C", base, "rev-parse", "--show-toplevel"]
    return subprocess.check_output(cmd, text=True).strip()


def check_uncommitted_changes() -> None:
    try:
        toplevel = _git_toplevel()
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
        toplevel = _git_toplevel()
        print(f"[info] Running 'git pull --rebase' in {toplevel}...")
        subprocess.run(["git", "-C", toplevel, "pull", "--rebase"], check=True)
    except Exception as e:
        print(f"[error] git pull --rebase failed: {e}")
        raise


def _open_url(github_url: str) -> None:
    browser = os.getenv("NOTE_BROWSER", "").strip()
    if sys.platform.startswith("darwin"):
        if browser:
            script = f'tell application "{browser}" to open location "{github_url}"'
            try:
                subprocess.run(
                    ["osascript", "-e", script], check=False, capture_output=True
                )
                return
            except Exception:
                pass
        command = ["open", "-g", github_url]
    elif sys.platform.startswith("linux"):
        command = ["env", "NO_AT_BRIDGE=1", "xdg-open", github_url]
    else:
        if not webbrowser.open(github_url):
            print(f"[warn] webbrowser module could not launch {github_url}")
        return
    try:
        subprocess.run(command, check=False)
    except FileNotFoundError:
        print(f"[warn] Launch command not found when opening {github_url}")
    except Exception as exc:
        print(f"[warn] Failed to open browser for {github_url}: {exc}")


def open_note_in_browser(note_path: Optional[str], repo_url: str) -> None:
    if not note_path:
        return
    abs_note_path = os.path.abspath(note_path)
    try:
        repo_root = _git_toplevel()
        rel_path = os.path.relpath(abs_note_path, repo_root)
    except Exception as exc:
        print(f"[warn] Unable to compute relative path for {abs_note_path}: {exc}")
        return
    github_url = repo_url.rstrip("/") + "/blob/main/" + rel_path.replace(os.sep, "/")
    _open_url(github_url)


def generate_random_date():
    random.seed(datetime.now().timestamp())
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    random_days = random.randint(0, 180)
    return (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")


def parse_args():
    parser = argparse.ArgumentParser(description="Create a note.")
    parser.add_argument(
        "--random", action="store_true", help="Use a random date within last 180 days"
    )
    parser.add_argument(
        "--without-math", action="store_true", help="Skip fixing MathJax delimiters"
    )
    parser.add_argument(
        "--gemini", action="store_true", help="Enable Gemini-specific MathJax fixing"
    )
    parser.add_argument(
        "--open",
        action=argparse.BooleanOptionalAction,
        default=os.getenv("NOTE_BROWSER_OPEN", "true").lower()
        not in ("false", "0", "no"),
        help="Open the note in browser after creating (default: NOTE_BROWSER_OPEN env, true; use --no-open to skip)",
    )
    parser.add_argument(
        "--no-push", action="store_true", help="Skip the gpa git push step"
    )
    parser.add_argument(
        "--repo-url",
        default="https://github.com/lzwjava/blog-source",
        help="GitHub repo URL for --open",
    )
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
        base = get_base_path()
        gitmessageai(allow_pull_push=True, directory=None if base == "." else base)

    if args.open:
        try:
            open_note_in_browser(created_path, args.repo_url)
        except Exception as e:
            print(f"[warn] Failed to open browser: {e}")

    print(f"[info] Note created at {created_path}")
