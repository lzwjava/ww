"""Open Beyond Compare to compare two files."""

import os
import subprocess
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: ww compare <file1> <file2>")
        print("")
        print("Open Beyond Compare to diff two files.")
        print("")
        print("Options:")
        print("  --tool <path>   Use a custom diff tool instead of Beyond Compare")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    # Allow custom tool via --tool flag
    tool = "Beyond Compare"
    if "--tool" in sys.argv:
        idx = sys.argv.index("--tool")
        if idx + 1 < len(sys.argv):
            tool = sys.argv[idx + 1]

    for f in (file1, file2):
        if not os.path.exists(f):
            print(f"Error: file not found: {f}")
            sys.exit(1)

    try:
        subprocess.run(["open", "-a", tool, file1, file2], check=True)
        print(f"Opened {tool}: {file1} vs {file2}")
    except subprocess.CalledProcessError as e:
        print(f"Error launching {tool}: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"Error: {tool} not found. Install it or use --tool to specify a different diff tool."
        )
        sys.exit(1)
