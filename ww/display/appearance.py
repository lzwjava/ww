import os
import shutil
import subprocess
import sys
import tempfile


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


def smart_auto(threshold=80):
    """Capture a webcam photo, analyze ambient brightness, and set dark/light mode.

    Uses average luminance of the webcam frame:
      - Luminance < threshold -> dark mode  (dim environment)
      - Luminance >= threshold -> light mode (bright environment)

    Default threshold=80 (on 0-255 scale). Typical indoor with lights: ~80-120.
    Skips webcam capture if a video conferencing app is running.
    """
    # Skip if a video conferencing app is using the webcam
    video_apps = ["zoom.us", "Google Meet", "Microsoft Teams", "FaceTime", "Webex"]
    for app in video_apps:
        result = subprocess.run(["pgrep", "-x", app], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Skipping — {app} is running")
            return

    import numpy as np
    from PIL import Image

    # Find imagesnap (preferred) or ffmpeg
    capture_cmd = None
    if os.path.isfile("/opt/homebrew/bin/imagesnap") or shutil.which("imagesnap"):
        capture_cmd = "imagesnap"
    elif os.path.isfile("/opt/homebrew/bin/ffmpeg") or shutil.which("ffmpeg"):
        capture_cmd = "ffmpeg"

    if not capture_cmd:
        print(
            "Error: imagesnap or ffmpeg required. Install with: brew install imagesnap"
        )
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        tmp = tmp_file.name
    try:
        if capture_cmd == "imagesnap":
            result = subprocess.run(
                ["imagesnap", "-q", tmp],
                capture_output=True,
                text=True,
                timeout=10,
            )
        else:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "avfoundation",
                    "-framerate",
                    "15",
                    "-video_size",
                    "640x480",
                    "-i",
                    "0:",
                    "-frames:v",
                    "1",
                    "-y",
                    tmp,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        if result.returncode != 0:
            err = (
                result.stderr.strip().split("\n")[-1]
                if result.stderr
                else "unknown error"
            )
            print(f"Error capturing webcam: {err}")
            print("Make sure a webcam is connected and not in use by another app.")
            sys.exit(1)

        # Analyze brightness via numpy
        img = Image.open(tmp).convert("L")  # grayscale
        avg_brightness = float(np.array(img).mean())

        print(f"Webcam brightness: {avg_brightness:.1f} / 255 (threshold: {threshold})")

        if avg_brightness < threshold:
            print(
                f"Environment appears dim ({avg_brightness:.1f} < {threshold}) -> dark mode"
            )
            set_dark()
        else:
            print(
                f"Environment appears bright ({avg_brightness:.1f} >= {threshold}) -> light mode"
            )
            set_light()

    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("--help", "-h"):
        print("Usage: ww appearance <dark|light|auto|smart-auto|show>")
        print("")
        print("  dark        Switch to dark mode")
        print("  light       Switch to light mode")
        print("  auto        Switch to auto mode (follows sunrise/sunset)")
        print("  smart-auto  Detect ambient light via webcam, then set dark/light")
        print("  show        Show current appearance mode")
        print("")
        print("Options (smart-auto):")
        print("  --threshold N   Brightness threshold 0-255 (default: 80)")
        return

    subcmd = argv[0]

    # Parse --threshold for smart-auto
    threshold = 80
    for i, arg in enumerate(argv):
        if arg == "--threshold" and i + 1 < len(argv):
            try:
                threshold = int(argv[i + 1])
            except ValueError:
                print(f"Invalid threshold: {argv[i + 1]}")
                sys.exit(1)

    if subcmd == "dark":
        set_dark()
    elif subcmd == "light":
        set_light()
    elif subcmd == "auto":
        set_auto()
    elif subcmd == "smart-auto":
        smart_auto(threshold=threshold)
    elif subcmd == "show":
        show()
    else:
        print(f"Unknown appearance command: {subcmd}")
        print("Usage: ww appearance <dark|light|auto|smart-auto|show>")
        sys.exit(1)


if __name__ == "__main__":
    main()
