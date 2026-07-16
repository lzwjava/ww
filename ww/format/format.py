"""Format a JSON file with pretty-printing (in-place)."""

import json
import sys


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww format <file.json>")
        print()
        print("Pretty-print a JSON file in-place.")
        print()
        print("Examples:")
        print("  ww format data.json")
        print("  ww format ~/config.json")
        return

    file_path = args[0]

    try:
        with open(file_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {file_path}: {e}")
        sys.exit(1)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Formatted: {file_path}")
