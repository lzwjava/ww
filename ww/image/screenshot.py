import argparse
import datetime
import os
import subprocess
import sys
import time

from PIL import ImageGrab
from dotenv import load_dotenv


def capture_screenshot(directory, window_name=None):
    """Capture a screenshot and save to directory.

    On macOS: captures the specified window (default: Safari) using Quartz.
    On Linux: captures the full screen using available system tools
              (scrot, ImageMagick, gnome-screenshot, spectacle, ffmpeg).

    Returns the saved file path on success, or None if failed.
    """
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"screenshot-{ts}.png"

    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)

    if sys.platform == "darwin":
        import Quartz  # type: ignore

        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID
        )

        target_owner = window_name or "Safari"
        target_window = None
        for window in windows:
            owner = window.get(Quartz.kCGWindowOwnerName, "")
            if owner == target_owner:
                target_window = window
                title = window.get(Quartz.kCGWindowName, "")
                print(f"Found window: {title}")
                break

        if target_window:
            bounds = target_window.get("kCGWindowBounds")
            if bounds:
                x = int(bounds.get("X", 0))
                y = int(bounds.get("Y", 0))
                w = int(bounds.get("Width", 0))
                h = int(bounds.get("Height", 0))
                img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                img.save(path)
                print(f"Saved {path} size={img.size}")
                return path
        else:
            print(f"{target_owner} window not found")
        return None
    else:
        # Linux: try available tools in order
        return _capture_linux(path)


def _capture_linux(path):
    """Try Linux screenshot tools in order of preference. Returns path or None."""
    # scrot
    try:
        subprocess.run(["scrot", path], check=True, capture_output=True, timeout=10)
        print(f"Saved {path}")
        return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # ImageMagick import
    try:
        subprocess.run(
            ["import", "-window", "root", path],
            check=True,
            capture_output=True,
            timeout=10,
        )
        print(f"Saved {path}")
        return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # gnome-screenshot
    try:
        subprocess.run(
            ["gnome-screenshot", "-f", path],
            check=True,
            capture_output=True,
            timeout=10,
        )
        print(f"Saved {path}")
        return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # spectacle (KDE)
    try:
        subprocess.run(
            ["spectacle", "-b", "-n", "-o", path],
            check=True,
            capture_output=True,
            timeout=10,
        )
        print(f"Saved {path}")
        return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # ffmpeg x11grab (last resort)
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-f",
                "x11grab",
                "-s",
                "1920x1080",
                "-i",
                ":0.0",
                "-frames:v",
                "1",
                path,
            ],
            check=True,
            capture_output=True,
            timeout=10,
        )
        print(f"Saved {path}")
        return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    print(
        "No suitable screenshot tool found. "
        "Please install one of: scrot, ImageMagick, gnome-screenshot, spectacle, ffmpeg."
    )
    return None


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Take a screenshot (macOS / Linux)",
        usage="%(prog)s [DELAY] [--dir DIR]",
    )
    parser.add_argument(
        "delay",
        nargs="?",
        type=int,
        default=0,
        help="Delay in seconds before capture (default: 0)",
    )
    parser.add_argument(
        "--dir", default=None, help="Output directory (default: SCREENSHOT_DIR or .)"
    )
    args = parser.parse_args(sys.argv[1:])

    if args.delay > 0:
        print(f"Taking screenshot in {args.delay} second(s)...")
        time.sleep(args.delay)

    env_dir = os.environ.get("SCREENSHOT_DIR", "").strip()
    directory = os.path.expanduser(env_dir) or args.dir or "."

    capture_screenshot(directory)
