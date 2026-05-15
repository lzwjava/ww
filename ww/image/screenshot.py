import argparse
import Quartz  # type: ignore
from PIL import ImageGrab
import datetime
import os
import sys
import time

from dotenv import load_dotenv


def capture_screenshot(directory):
    """Capture a Safari window screenshot and save to directory.

    Returns the saved file path on success, or None if Safari window not found.
    """
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"screenshot-{ts}.png"

    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)

    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID
    )

    safari_window = None
    for window in windows:
        owner = window.get(Quartz.kCGWindowOwnerName, "")
        if owner == "Safari":
            safari_window = window
            title = window.get(Quartz.kCGWindowName, "")
            print(f"Found Safari window: {title}")
            break

    if safari_window:
        bounds = safari_window.get("kCGWindowBounds")
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
        print("Safari window not found")
    return None


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Take a screenshot (macOS)",
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
    directory = env_dir or args.dir or "."

    capture_screenshot(directory)
