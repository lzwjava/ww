#!/usr/bin/env python3

import argparse
import platform

from .kill_unix import print_process_details

if platform.system().lower() == "windows":
    from . import kill_windows as platform_module
else:
    from . import kill_unix as platform_module


def main():
    parser = argparse.ArgumentParser(
        description="Kill process running on a specific port"
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8080,
        help="Port number to kill process on (default: 8080)",
    )
    args = parser.parse_args()

    port = args.port
    pid, process_info = platform_module.find_process_on_port(port)

    if not pid:
        print(f"No process found running on port {port}")
        return

    print(f"Found process running on port {port}:")
    details = platform_module.get_process_details(pid)
    print_process_details(process_info, details)

    print("")
    print("Do you want to kill this process? (Press Enter to kill, or 'no' to exit)")

    try:
        response = input().strip().lower()
        if response in ("no", "n"):
            print("Process not killed. Exiting.")
            return
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return

    if platform_module.kill_process(pid):
        print(f"Successfully killed process {pid}")
    else:
        print(f"Failed to kill process {pid}")
        print(
            "You may need administrator privileges or the process may have already terminated."
        )


if __name__ == "__main__":
    main()
