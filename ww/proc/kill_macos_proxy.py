#!/usr/bin/env python3

import argparse
import subprocess

from .kill_unix import get_process_details, kill_process


def find_clash_processes():
    """Find all Clash-related processes on macOS."""
    clash_patterns = ["clash-darwin-amd64", "clash.py", "clash"]
    processes = []

    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:
                line_lower = line.lower()
                if not any(p in line_lower for p in clash_patterns):
                    continue
                parts = line.split()
                if len(parts) < 11:
                    continue
                pid = parts[1]
                user = parts[0]
                command = " ".join(parts[10:])
                if "grep" in command or user == "root":
                    continue
                if (
                    "clash-darwin-amd64" in command
                    or "clash.py" in command
                    or ("/python" in command and "clash" in command)
                ):
                    processes.append((pid, f"{command} ({pid})"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return processes


def main():
    parser = argparse.ArgumentParser(description="Kill Clash processes on macOS")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Kill processes without asking for confirmation",
    )
    args = parser.parse_args()

    processes = find_clash_processes()

    if not processes:
        print("No Clash processes found")
        return

    print(f"Found {len(processes)} Clash process(es):\n")

    for i, (pid, process_info) in enumerate(processes, 1):
        print(f"[{i}] Process:")
        print(f"  PID: {pid}")
        print(f"  Command: {process_info}")
        details = get_process_details(pid)
        if details:
            if details.get("started"):
                print(f"  Started: {details['started']}")
            if details.get("elapsed"):
                print(f"  Running for: {details['elapsed']}")
            if details.get("ppid"):
                print(f"  Parent PID: {details['ppid']}")
        print()

    if not args.force:
        print(
            f"Do you want to kill all {len(processes)} Clash process(es)? (Press Enter to kill, or 'no' to exit)"
        )
        try:
            response = input().strip().lower()
            if response in ("no", "n"):
                print("Clash processes not killed. Exiting.")
                return
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return
    else:
        print("Force mode enabled - proceeding to kill all Clash processes")

    killed, failed = [], []
    for pid, _ in processes:
        if kill_process(pid):
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
        print(f"\nSuccessfully killed all {len(killed)} Clash process(es)")


if __name__ == "__main__":
    main()
