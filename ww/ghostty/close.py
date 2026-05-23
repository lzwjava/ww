import subprocess
import sys


def main():
    """Close all Ghostty windows on macOS."""
    # First, try graceful quit via osascript
    script = """
    tell application "System Events"
        set ghosttyProcesses to every process whose name is "ghostty"
        repeat with proc in ghosttyProcesses
            tell application "ghostty" to quit
        end repeat
    end tell
    """

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0 and "Application isn't running" not in result.stderr:
        print(f"osascript error: {result.stderr.strip()}")

    # Wait a moment for graceful quit
    import time

    time.sleep(0.5)

    # Force kill any remaining ghostty processes
    kill_result = subprocess.run(
        ["pkill", "-f", "ghostty"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    if kill_result.returncode == 0:
        print("Closed all Ghostty windows.")
    elif kill_result.returncode == 1:
        print("No Ghostty windows are running.")
    else:
        print(f"Error: {kill_result.stderr.strip()}")
        sys.exit(1)
