import os
import re
import subprocess
import argparse

from ww.env import load_env
from ww.llm.llm_client import call_llm

load_env()


def _parse_file_changes(diff_output):
    changes = []
    lines = diff_output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 4:
                file_a = parts[2][2:]
                file_b = parts[3][2:]
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                if file_a == file_b:
                    if "deleted file mode" in next_line:
                        changes.append(f"Deleted file {file_a}")
                    elif "new file mode" in next_line:
                        changes.append(f"Added file {file_a}")
                    else:
                        changes.append(f"Updated file {file_a}")
                else:
                    if "similarity index" in next_line:
                        changes.append(f"Renamed file {file_a} to {file_b}")
        i += 1
    return changes


def _build_prompt(type, diff_output):
    header = (
        "Generate a concise commit message in Conventional Commits format for the following code changes.\n"
        "Use one of the following types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, or revert.\n"
        "If applicable, include a scope in parentheses to describe the part of the codebase affected.\n"
        "The commit message should not exceed 70 characters. Just give the commit message, without any leading or trailing notes.\n"
    )
    if type == "file":
        file_changes = _parse_file_changes(diff_output)
        for change in file_changes:
            print(change)
        if not file_changes:
            return None, None
        return (
            f"{header}\nChanged files:\n{', '.join(file_changes[:20])}\n",
            file_changes,
        )
    else:
        return f"{header}\nCode changes:\n{diff_output[:2000]}\n", None


def _clean_commit_message(msg):
    msg = msg.replace("```", "")
    return msg.strip()


def _get_github_repo_url(git):
    try:
        remote_url = subprocess.check_output(
            [*git, "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return ""
    if remote_url.startswith("git@github.com:"):
        remote_url = remote_url.replace("git@github.com:", "https://github.com/")
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    return remote_url


def _print_note_urls(git, file_changes):
    if not file_changes:
        return
    repo_url = _get_github_repo_url(git)
    if not repo_url:
        return
    note_files = [f for f in file_changes if re.search(r"Added file .*\.md$", f)]
    if not note_files:
        return
    try:
        repo_root = subprocess.check_output(
            [*git, "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return
    for note in note_files:
        filename = note.replace("Added file ", "")
        abs_path = os.path.join(repo_root, filename)
        if os.path.exists(abs_path):
            rel_path = os.path.relpath(abs_path, repo_root).replace(os.sep, "/")
            github_url = repo_url + "/blob/main/" + rel_path
            print(f"[info] Note created at {github_url}")


def _push_with_fallback(git, allow_pull_push):
    try:
        subprocess.run([*git, "push"], check=True)
    except subprocess.CalledProcessError as e:
        if allow_pull_push:
            print("Push failed, attempting pull and push...")
            subprocess.run([*git, "pull", "--rebase"], check=True)
            subprocess.run([*git, "push"], check=True)
        else:
            print("Push failed.")
            raise e


def gitmessageai(
    push=True,
    only_message=False,
    allow_pull_push=False,
    type="file",
    directory=None,
    model=None,
):
    git = ["git", "-C", directory] if directory else ["git"]

    subprocess.run([*git, "add", "-A"], check=True)

    diff_process = subprocess.run(
        [*git, "diff", "--staged", "--unified=0"],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
        errors="replace",
    )
    diff_output = diff_process.stdout

    if not diff_output:
        print("No changes to commit.")
        return

    if type == "content":
        diff_process = subprocess.run(
            [*git, "diff", "--staged"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        diff_output = diff_process.stdout
        if not diff_output:
            print("No changes to commit.")
            return
    elif type != "file":
        print(f"Error: Invalid type specified: {type}")
        return

    prompt, file_changes = _build_prompt(type, diff_output)
    if prompt is None:
        print("No changes to commit.")
        return

    commit_message = call_llm(prompt, model=model)
    if not commit_message:
        print("Error: No response from LLM.")
        return

    commit_message = _clean_commit_message(commit_message)
    if not commit_message:
        print("Error: Empty commit message generated. Aborting commit.")
        return

    if only_message:
        print(f"Suggested commit message: {commit_message}")
        return

    subprocess.run([*git, "commit", "-m", commit_message], check=True)

    if push:
        _push_with_fallback(git, allow_pull_push)
        if type == "file" and file_changes:
            _print_note_urls(git, file_changes)
    else:
        print("Changes committed locally, but not pushed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate commit message with AI and commit changes."
    )
    parser.add_argument("--no-push", dest="push", action="store_false")
    parser.add_argument("--only-message", dest="only_message", action="store_true")
    parser.add_argument(
        "--allow-pull-push", dest="allow_pull_push", action="store_true"
    )
    parser.add_argument(
        "--type", type=str, default="content", choices=["file", "content"]
    )
    args = parser.parse_args()
    gitmessageai(
        push=args.push,
        only_message=args.only_message,
        allow_pull_push=args.allow_pull_push,
        type=args.type,
    )
