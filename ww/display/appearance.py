import subprocess
import sys


def _run_osascript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def _current_appearance():
    result = subprocess.run(
        ["defaults", "read", "-g", "AppleInterfaceStyleSwitchesAutomatically"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip() == "1":
        return "auto"
    dark = _run_osascript(
        'tell application "System Events" to tell appearance preferences to get dark mode'
    )
    return "dark" if dark == "true" else "light"


def set_dark():
    subprocess.run(
        [
            "defaults",
            "write",
            "-g",
            "AppleInterfaceStyleSwitchesAutomatically",
            "-bool",
            "false",
        ],
        check=True,
    )
    _run_osascript(
        'tell application "System Events" to tell appearance preferences to set dark mode to true'
    )
    print("Appearance set to dark")


def set_light():
    subprocess.run(
        [
            "defaults",
            "write",
            "-g",
            "AppleInterfaceStyleSwitchesAutomatically",
            "-bool",
            "false",
        ],
        check=True,
    )
    _run_osascript(
        'tell application "System Events" to tell appearance preferences to set dark mode to false'
    )
    print("Appearance set to light")


def set_auto():
    _run_osascript(
        'tell application "System Events" to tell appearance preferences to set dark mode to false'
    )
    subprocess.run(
        [
            "defaults",
            "write",
            "-g",
            "AppleInterfaceStyleSwitchesAutomatically",
            "-bool",
            "true",
        ],
        check=True,
    )
    subprocess.run(
        ["killall", "SystemUIServer", "ControlCenter"], capture_output=True, text=True
    )
    print("Appearance set to auto (follow sunrise/sunset)")


def show():
    mode = _current_appearance()
    print(mode)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("--help", "-h"):
        print("Usage: ww display <dark|light|auto|show>")
        print("")
        print("  dark     Switch to dark mode")
        print("  light    Switch to light mode")
        print("  auto     Switch to auto mode (follows sunrise/sunset)")
        print("  show     Show current appearance mode")
        return

    subcmd = argv[0]
    if subcmd == "dark":
        set_dark()
    elif subcmd == "light":
        set_light()
    elif subcmd == "auto":
        set_auto()
    elif subcmd == "show":
        show()
    else:
        print(f"Unknown display command: {subcmd}")
        print("Usage: ww display <dark|light|auto|show>")
        sys.exit(1)


if __name__ == "__main__":
    main()
