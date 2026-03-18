import subprocess
import argparse
import os

from .common import check_ack, print_ack_output


def search_posts(query, ignore_case=False, dirs=None):
    try:
        ack = check_ack()
        cmd = [ack]
        if ignore_case:
            cmd.append("-i")
        cmd.extend(
            [
                "--type-add=md=.md,.markdown",
                "--md",
                "--color",
                "--color-match=red",
                query,
            ]
        )
        cmd.extend(dirs if dirs else ["_posts/en", "original", "notes"])

        env = {**os.environ, "CLICOLOR_FORCE": "1"}
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode not in [0, 1]:
            print("Error executing search command")
            print(result.stderr)
            return

        print_ack_output(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Error executing search: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    parser = argparse.ArgumentParser(description="Search posts in the repository")
    parser.add_argument("query", help="Search pattern to look for")
    parser.add_argument(
        "-i", "--ignore-case", action="store_true", help="Case insensitive search"
    )
    parser.add_argument(
        "--dir",
        nargs="*",
        choices=["notes", "original", "_posts/en"],
        default=[],
        help="Directories to search in (default: all)",
    )
    args = parser.parse_args()
    search_posts(args.query, args.ignore_case, args.dir)
