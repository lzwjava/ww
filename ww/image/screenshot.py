import Quartz  # type: ignore
from PIL import ImageGrab
import datetime


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = f"screenshot-{ts}.png"

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
