import os
import time
import argparse
import tempfile
import datetime
from PIL import Image


def images_to_gif(image_folder, output_gif, duration):
    images = []
    file_list = sorted(os.listdir(image_folder))

    for filename in file_list:
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(image_folder, filename)
            img = Image.open(path).convert("RGB")
            images.append(img)

    if not images:
        print("No images found in the folder.")
        return

    images[0].save(
        output_gif, save_all=True, append_images=images[1:], duration=duration, loop=0
    )
    print(f"GIF saved as {output_gif}")


def capture_window_screenshot(window_name, output_path):
    import Quartz  # type: ignore
    from PIL import ImageGrab

    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID
    )

    target_window = None
    for window in windows:
        owner = window.get(Quartz.kCGWindowOwnerName, "")
        if owner == window_name:
            target_window = window
            title = window.get(Quartz.kCGWindowName, "")
            print(f"Found window: {owner} - {title}")
            break

    if not target_window:
        print(f"Window '{window_name}' not found")
        return False

    bounds = target_window.get("kCGWindowBounds")
    if not bounds:
        print("Could not get window bounds")
        return False

    x = int(bounds.get("X", 0))
    y = int(bounds.get("Y", 0))
    w = int(bounds.get("Width", 0))
    h = int(bounds.get("Height", 0))
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(output_path)
    print(f"Saved {output_path} size={img.size}")
    return True


def interactive_gif(output_gif, duration, window_name, countdown):
    tmpdir = tempfile.mkdtemp(prefix="ww_gif_")
    frame_index = 0
    print(f"Interactive GIF capture. Window: '{window_name}'")
    print("Press Enter to capture a frame, or type 'end' and press Enter to finish.")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            break

        if user_input.lower() == "end":
            if frame_index == 0:
                print("No frames captured. Exiting.")
            else:
                images_to_gif(tmpdir, output_gif, duration)
            break

        print(f"Capturing in {countdown} seconds...")
        time.sleep(countdown)

        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        frame_path = os.path.join(tmpdir, f"frame-{frame_index:04d}-{ts}.png")
        success = capture_window_screenshot(window_name, frame_path)
        if success:
            frame_index += 1
            print(
                f"Frame {frame_index} captured. Press Enter for next, or type 'end' to finish."
            )
        else:
            print("Screenshot failed. Try again.")


def main():
    parser = argparse.ArgumentParser(description="Convert images in a folder to a GIF.")
    parser.add_argument(
        "image_folder", nargs="?", help="Path to the folder containing images"
    )
    parser.add_argument("output_gif", nargs="?", help="Output GIF file path")
    parser.add_argument(
        "--duration", type=int, default=300, help="Frame duration in ms (default: 300)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactively capture screenshots and assemble into a GIF",
    )
    parser.add_argument(
        "--window",
        default="Safari",
        help="Window owner name to capture in interactive mode (default: Safari)",
    )
    parser.add_argument(
        "--countdown",
        type=int,
        default=3,
        help="Seconds to wait before each capture in interactive mode (default: 3)",
    )

    args = parser.parse_args()

    if args.interactive:
        out = args.output_gif or "output.gif"
        interactive_gif(out, args.duration, args.window, args.countdown)
    elif args.image_folder and args.output_gif:
        images_to_gif(args.image_folder, args.output_gif, args.duration)
    else:
        parser.print_help()
