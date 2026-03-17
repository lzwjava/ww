#!/usr/bin/env python3
"""
Script to open multiple Ghostty terminal windows
"""

import argparse
import subprocess
import sys
import os


def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def open_ghostty_at_path(path, number):
    if not path:
        print("Error: Path is required")
        return False

    if number <= 0:
        print("Error: Number must be greater than 0")
        return False

    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print(f"Error: Path '{path}' does not exist")
        return False

    opened = 0
    for i in range(number):
        cmd = f'open -na ghostty.app --args --working-directory="{path}"'
        result = run_command(cmd)

        if result and result.returncode == 0:
            opened += 1
            print(f"Opened Ghostty window {i + 1}/{number} in {path}")
        else:
            print(f"Failed to open Ghostty window {i + 1}/{number}")
            if result and result.stderr:
                print(f"Error: {result.stderr}")

    print(f"\nSuccessfully opened {opened}/{number} Ghostty terminal window(s)")
    return opened == number


def main():
    parser = argparse.ArgumentParser(
        description="Open multiple Ghostty terminal windows"
    )
    parser.add_argument(
        "--path", required=True, help="The directory path to open in each terminal"
    )
    parser.add_argument(
        "--number", type=int, required=True, help="The number of terminals to open"
    )

    args = parser.parse_args()

    success = open_ghostty_at_path(args.path, args.number)
    sys.exit(0 if success else 1)
