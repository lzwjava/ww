import os
import sys

from ww.image.image_utils import crop_center


def process_crop(input_path, top_percent: float = 0):
    cropped = crop_center(input_path, top_percent)

    dir_path = os.path.dirname(input_path)
    filename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(dir_path, f"{filename}_crop.jpg")

    cropped.save(output_path)
    print(f"Saved: {output_path}")


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: ww crop <input_jpg_path> [top_percent]")
        sys.exit(1)

    input_path = sys.argv[1]
    top_percent = float(sys.argv[2]) if len(sys.argv) == 3 else 0
    process_crop(input_path, top_percent)
