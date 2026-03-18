import subprocess
import argparse

from ww.env import load_env
from ww.llm.llm_client import call_llm

load_env()


def gitmessageai(
    push=True, only_message=False, allow_pull_push=False, type="file", directory=None
):
    git = ["git", "-C", directory] if directory else ["git"]

    # Stage all changes
    subprocess.run([*git, "add", "-A"], check=True)

    # Get a detailed summary of the changes
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

    if type == "file":
        file_changes = []
        lines = diff_output.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("diff --git"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    file_a = parts[2][2:]
                    file_b = parts[3][2:]
                    if file_a == file_b:
                        if i + 1 < len(lines) and "deleted file mode" in lines[i + 1]:
                            file_changes.append(f"Deleted file {file_a}")
                            i += 1
                        elif i + 1 < len(lines) and "new file mode" in lines[i + 1]:
                            file_changes.append(f"Added file {file_a}")
                            i += 1
                        elif i + 1 < len(lines):
                            file_changes.append(f"Updated file {file_a}")
                            i += 1
                    else:
                        if i + 1 < len(lines) and "similarity index" in lines[i + 1]:
                            file_changes.append(f"Renamed file {file_a} to {file_b}")
                            i += 1
            i += 1

        for change in file_changes:
            print(change)

        if not file_changes:
            print("No changes to commit.")
            return

        prompt = f"""
Generate a concise commit message in Conventional Commits format for the following code changes.
Use one of the following types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, or revert.
If applicable, include a scope in parentheses to describe the part of the codebase affected.
The commit message should not exceed 70 characters. Just give the commit message, without any leading or trailing notes.

Changed files:
{", ".join(file_changes[:20])}

"""
    elif type == "content":
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

        diff_output = diff_output[:2000]

        prompt = f"""
Generate a concise commit message in Conventional Commits format for the following code changes.
Use one of the following types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, or revert.
If applicable, include a scope in parentheses to describe the part of the codebase affected.
The commit message should not exceed 70 characters. Just give the commit message, without any leading or trailing notes.

Code changes:
{diff_output}

"""
    else:
        print(f"Error: Invalid type specified: {type}")
        return

    commit_message = call_llm(prompt)
    if not commit_message:
        print("Error: No response from LLM.")
        return

    if "```" in commit_message:
        commit_message = commit_message.replace("```", "")

    commit_message = commit_message.strip()
    if not commit_message:
        print("Error: Empty commit message generated. Aborting commit.")
        return

    if only_message:
        print(f"Suggested commit message: {commit_message}")
        return

    subprocess.run([*git, "commit", "-m", commit_message], check=True)

    if push:
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
