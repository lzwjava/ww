#!/usr/bin/env python3

import argparse
import platform

from .kill_unix import print_process_details

if platform.system().lower() == "windows":
    from . import kill_windows as platform_module
else:
    from . import kill_unix as platform_module


def ask_confirm(count):
    print(
        f"Do you want to kill all {count} process(es)? (Press Enter to kill, or 'no' to exit)"
    )
    try:
        response = input().strip().lower()
        return response not in ("no", "n")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return False


def kill_all(processes):
    killed, failed = [], []
    for pid, _ in processes:
        if platform_module.kill_process(pid):
            print(f"Successfully killed process {pid}")
            killed.append(pid)
        else:
            print(f"Failed to kill process {pid}")
            failed.append(pid)
    if failed:
        print(f"\nFailed to kill {len(failed)} process(es): {', '.join(failed)}")
        print(
            "You may need administrator privileges or the processes may have already terminated."
        )
    else:
        print(f"\nSuccessfully killed all {len(killed)} process(es)")


def main():
    parser = argparse.ArgumentParser(description="Kill processes matching a pattern")
    parser.add_argument(
        "pattern",
        type=str,
        help='Pattern to match process names/commands (e.g., "clash")',
    )
    args = parser.parse_args()

    pattern = args.pattern
    processes = platform_module.find_processes_by_pattern(pattern)

    if not processes:
        print(f"No processes found matching pattern '{pattern}'")
        return

    print(f"Found {len(processes)} process(es) matching pattern '{pattern}':\n")

    for i, (pid, process_info) in enumerate(processes, 1):
        print(f"[{i}] Process:")
        details = platform_module.get_process_details(pid)
        print_process_details(process_info, details)
        print()

    if ask_confirm(len(processes)):
        kill_all(processes)


if __name__ == "__main__":
    main()
