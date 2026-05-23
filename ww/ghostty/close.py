import subprocess
import sys


def main():
    """Close all Ghostty windows on macOS."""
    script = """
    tell application "System Events"
        set ghosttyProcesses to every process whose name is "ghostty"
        repeat with proc in ghosttyProcesses
            set procName to name of proc
            if procName is "ghostty" then
                tell application "ghostty" to quit
            end if
        end repeat
    end tell
    """

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0:
        error = result.stderr.strip()
        if "Application isn't running" in error:
            print("No Ghostty windows are running.")
        else:
            print(f"Error: {error}")
            sys.exit(1)
    else:
        print("Closed all Ghostty windows.")
