import subprocess
import argparse
import sys
import os
import shutil


def check_ack():
    if not shutil.which("ack"):
        print("Error: ack is not installed.")
        print("Please install it first:")
        print("  macOS: brew install ack")
        print("  Ubuntu/Debian: sudo apt-get install ack")
        print("  Windows: scoop install ack")
        sys.exit(1)


def search_posts(query, ignore_case=False, dirs=None):
    try:
        check_ack()

        cmd = [shutil.which("ack")]
        if ignore_case:
            cmd.append("-i")
        cmd.append("--type-add=md=.md,.markdown")
        cmd.append("--md")
        cmd.append("--color")
        cmd.append("--color-match=red")
        cmd.append(query)

        if dirs:
            cmd.extend(dirs)
        else:
            cmd.extend(["_posts/en", "original", "notes"])

        env = os.environ.copy()
        env["CLICOLOR_FORCE"] = "1"
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode not in [0, 1]:
            print("Error executing search command")
            print(result.stderr)
            return

        if result.stdout:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                print()
                if line.startswith("--"):
                    print()
                    continue
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) >= 2:
                        file_part = parts[0]
                        content = parts[1]
                        if "-" in file_part and file_part.split("-")[-1].isdigit():
                            file_name = "-".join(file_part.split("-")[:-1])
                            line_num = file_part.split("-")[-1]
                            print(f"{file_name}:{line_num}:{content}")
                        else:
                            print(line)
                    else:
                        print(line)
                elif "-" in line and not line.startswith("-"):
                    parts = line.split("-")
                    if len(parts) >= 3 and parts[-2].isdigit():
                        file_name = "-".join(parts[:-2])
                        line_num = parts[-2]
                        content = parts[-1]
                        print(f"{file_name}:{line_num}:{content}")
                    else:
                        print(line)
                else:
                    print(line)
            print()
        else:
            print("No matches found")

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
