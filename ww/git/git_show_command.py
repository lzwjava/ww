import subprocess
import os

try:
    import pyperclip

    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


def get_last_commit_info():
    try:
        commit_info = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%H %s"], text=True
        ).strip()
        commit_hash, commit_message = commit_info.split(" ", 1)

        all_files = (
            subprocess.check_output(
                ["git", "show", "--name-only", "--format=%n", commit_hash], text=True
            )
            .strip()
            .split("\n")
        )
        all_files = [f.strip() for f in all_files if f.strip()]
        python_files = [f for f in all_files if f.endswith(".py")]

        return {
            "hash": commit_hash[:8],
            "message": commit_message,
            "python_files": python_files,
            "all_files": all_files,
        }
    except subprocess.CalledProcessError as e:
        print(f"Error getting git info: {e}")
        return None


def format_file_list(files, title):
    if not files:
        return f"  {title}: None"
    items = "\n".join(f"    {i}. {f}" for i, f in enumerate(files, 1))
    return f"  {title}:\n{items}"


def main():
    print("=== Git Commit Python Command Helper ===\n")

    commit_info = get_last_commit_info()
    if not commit_info:
        print(
            "Could not retrieve git commit information. Make sure you're in a git repository."
        )
        return 1

    print(f"Last commit: {commit_info['hash']}")
    print(f"Message: {commit_info['message']}")
    print()
    print(format_file_list(commit_info["all_files"], "All changed files"))
    print()
    print(format_file_list(commit_info["python_files"], "Python files"))
    print()

    if commit_info["python_files"]:
        first_py = commit_info["python_files"][0]
        python_cmd = f"python {first_py}"
        print(f"First Python file: {first_py}")

        if not CLIPBOARD_AVAILABLE:
            print("Note: pyperclip not found. To install: pip3 install pyperclip")
        else:
            try:
                pyperclip.copy(python_cmd)
                print("Command copied to clipboard!")
            except OSError as e:
                print(f"Could not copy to clipboard: {e}")

        print(f"Command to try: {python_cmd}")

        if os.path.exists(first_py):
            print("File exists and ready to run!")
        else:
            print("File path might be relative. Check the file location.")

        print(f"\nTo try this script, run: {python_cmd}")
    else:
        print("No Python files found in the last commit.")

    return 0
