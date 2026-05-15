import Quartz  # type: ignore
from PIL import ImageGrab
import datetime
import os
import sys

from dotenv import load_dotenv


def main():
    load_dotenv()
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"screenshot-{ts}.png"

    args = sys.argv[3:]
    cli_dir = args[0] if args else None
    env_dir = os.environ.get("SCREENSHOT_DIR", "").strip()
    directory = env_dir or cli_dir or "."
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
    else:
        print("Safari window not found")
