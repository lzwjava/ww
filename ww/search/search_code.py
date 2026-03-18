import subprocess
import argparse
import os

from .common import check_ack, print_ack_output

CODE_TYPES = (
    ".py,.js,.ts,.rs,.c,.cpp,.cc,.h,.hpp,.java,.go,.rb,.php,.sh,.kt,.swift,.scala"
)


def search_code(query, ignore_case=False):
    try:
        ack = check_ack()
        cmd = [ack]
        if ignore_case:
            cmd.append("-i")
        cmd.extend(
            [
                f"--type-add=code={CODE_TYPES}",
                "--code",
                "--color",
                "--color-match=red",
                query,
                ".",
            ]
        )

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
    parser = argparse.ArgumentParser(description="Search code files in the repository")
    parser.add_argument("query", help="Search pattern to look for")
    parser.add_argument(
        "-i", "--ignore-case", action="store_true", help="Case insensitive search"
    )
    args = parser.parse_args()
    search_code(args.query, args.ignore_case)
