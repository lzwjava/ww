import subprocess
import datetime
import os
import sys
import time
import tempfile
from PIL import Image
from dotenv import load_dotenv


def main():
    load_dotenv()

    no_save = "--no-save" in sys.argv or "-n" in sys.argv

    if not no_save:
        screenshot_dir = (
            os.environ.get("SCREENSHOT_DIR", "").strip() or "assets/screenshots"
        )
        os.makedirs(screenshot_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        path = os.path.join(screenshot_dir, f"{ts}.png")
    else:
        # Use a temp file when saving is disabled
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        path = tmp.name
        tmp.close()

    # Prompt user to prepare for screenshot
    print("Screenshot will be taken in 5 seconds...")
    print("Please switch to the window you want to capture")
    print("Countdown: 5...", end="", flush=True)

    time.sleep(1)
    print(" 4...", end="", flush=True)
    time.sleep(1)
    print(" 3...", end="", flush=True)
    time.sleep(1)
    print(" 2...", end="", flush=True)
    time.sleep(1)
    print(" 1...")
    time.sleep(1)
    print("Taking screenshot now!")

    # Method 1: Use scrot (if available)
    try:
        subprocess.run(["scrot", path], check=True)
        method = "scrot"
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Method 2: Use ImageMagick's import command
        try:
            subprocess.run(["import", "-window", "root", path], check=True)
            method = "ImageMagick"
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Method 3: Use gnome-screenshot (GNOME environments)
            try:
                subprocess.run(["gnome-screenshot", "-f", path], check=True)
                method = "gnome-screenshot"
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Method 4: Use spectacle (KDE environments)
                try:
                    subprocess.run(["spectacle", "-b", "-n", "-o", path], check=True)
                    method = "spectacle"
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Method 5: Use xwd (X11 fallback)
                    try:
                        xwd_path = path.replace(".png", ".xwd")
                        subprocess.run(["xwd", "-root", "-out", xwd_path], check=True)
                        subprocess.run(["convert", xwd_path, path], check=True)
                        if os.path.exists(xwd_path):
                            os.remove(xwd_path)
                        method = "xwd + convert"
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        # Method 6: Use ffmpeg (last resort)
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
                            )
                            method = "ffmpeg"
                        except (
                            subprocess.CalledProcessError,
                            FileNotFoundError,
                        ):
                            print(
                                "No suitable screenshot tool found. Please install one of: scrot, ImageMagick, gnome-screenshot, spectacle, or ffmpeg."
                            )
                            if no_save:
                                os.unlink(path)
                            return

    if no_save:
        # Copy to clipboard instead of saving to file
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", path],
                check=True,
                capture_output=True,
            )
            print(f"Screenshot copied to clipboard using {method}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to xsel if xclip is not available
            try:
                with open(path, "rb") as f:
                    subprocess.run(
                        ["xsel", "--clipboard", "--input"],
                        stdin=f,
                        check=True,
                    )
                print(f"Screenshot copied to clipboard via xsel using {method}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(
                    "Failed to copy to clipboard. Install xclip or xsel:\n"
                    "  sudo apt install xclip   # or xsel"
                )
        finally:
            os.unlink(path)
        return

    # If screenshot was taken, show basic info and compress
    if os.path.exists(path):
        try:
            with Image.open(path) as img:
                original_size = os.path.getsize(path)
                print(f"Screenshot saved: {path}")
                print(
                    f"Size: {img.size[0]}x{img.size[1]} ({original_size / 1024:.1f} KB)"
                )

                new_width = int(img.size[0] * 0.5)
                new_height = int(img.size[1] * 0.5)
                resized_img = img.resize((new_width, new_height), Image.LANCZOS)

                compressed_path = path.replace(".png", "_compressed.jpg")
                resized_img.save(compressed_path, "JPEG", quality=85, optimize=True)

                compressed_size = os.path.getsize(compressed_path)
                print(
                    f"Compressed size: {new_width}x{new_height} ({compressed_size / 1024:.1f} KB)"
                )
                print(f"Compression ratio: {(original_size / compressed_size):.1f}x")

                os.replace(compressed_path, path)
                print(f"Compressed screenshot saved: {path}")

        except Exception as e:
            print(f"Could not process image: {e}")
