import random
import subprocess
import sys


def get_screen_size():
    swift = """
    import Cocoa
    if let screen = NSScreen.main {
        let f = screen.frame
        print("\\(Int(f.size.width)),\\(Int(f.size.height))")
    }
    """
    result = subprocess.run(
        ["swift", "-e", swift], capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None, None
    w, h = result.stdout.strip().split(",")
    return int(w), int(h)


def pixels_to_cells(px, font_size=13, is_height=False):
    if is_height:
        return max(4, int(px / (font_size * 1.23)))
    return max(10, int(px / (font_size * 0.6)))


def main():
    screen_w, screen_h = get_screen_size()
    if screen_w is None or screen_h is None:
        print("Error: Could not get screen resolution")
        sys.exit(1)

    win_w = int(screen_w * 0.75)
    win_h = int(screen_h * 0.75)

    max_x = screen_w - win_w
    max_y = screen_h - win_h
    x = random.randint(0, max_x)
    y = random.randint(0, max_y)

    cols = pixels_to_cells(win_w)
    rows = pixels_to_cells(win_h, is_height=True)

    cmd = [
        "open",
        "-na",
        "ghostty.app",
        "--args",
        f"--window-position-x={x}",
        f"--window-position-y={y}",
        f"--window-width={cols}",
        f"--window-height={rows}",
        "--window-save-state=never",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        print(f"Error: {proc.stderr.strip()}")
        sys.exit(1)

    print(f"Opened Ghostty at ({x}, {y}) size {cols}x{rows} cells ({win_w}x{win_h}px)")
