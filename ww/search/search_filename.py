import subprocess
import argparse
import os

from .common import check_ack


def search_filenames(query, ignore_case=False, delete=False):
    try:
        ack = check_ack()
        cmd = [ack]
        if ignore_case:
            cmd.append("-i")
        cmd.extend(["-g", "--type-add=md=.md,.markdown", "--md", query, "notes"])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode not in [0, 1]:
            print("Error executing search command")
            print(result.stderr)
            return

        matches = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not matches:
            print("No matching filenames found")
            return

        if delete:
            _delete_matches(matches)
        else:
            print("\n".join(matches))

    except subprocess.CalledProcessError as e:
        print(f"Error executing search: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


def _delete_matches(matches):
    deleted, missing = [], []
    for match in matches:
        path = match if os.path.isabs(match) else os.path.join(os.getcwd(), match)
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted.append(match)
            except OSError as exc:
                print(f"Failed to delete {match}: {exc}")
        else:
            missing.append(match)
    if deleted:
        print("Deleted files:")
        print("\n".join(deleted))
    if missing:
        print("Files not found (skipped):")
        print("\n".join(missing))


def main():
    parser = argparse.ArgumentParser(
        description="Search markdown filenames in the repository"
    )
    parser.add_argument("query", help="Search pattern to look for in filenames")
    parser.add_argument(
        "-i", "--ignore-case", action="store_true", help="Case insensitive search"
    )
    parser.add_argument(
        "--del", dest="delete", action="store_true", help="Delete all files that match"
    )
    args = parser.parse_args()
    search_filenames(args.query, args.ignore_case, args.delete)
