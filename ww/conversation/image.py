"""Resize and crop an image to 854x480 (480p) maintaining aspect ratio."""

import sys
import os
from PIL import Image

DPI = 72


def get_image_dimensions(image_path):
    """Gets image dimensions in pixels and points."""
    try:
        image = Image.open(image_path)
        width, height = image.size
        dpi = image.info.get("dpi", (DPI, DPI))
        print(f"  Image dimensions: width={width}, height={height}, dpi={dpi}")
        return width, height, dpi
    except Exception as e:
        print(f"Error opening or processing image: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Error: Please provide a file path (without .jpg extension).")
        print("Usage: ww conversation to-image <file_path>")
        print("  Processes <file_path>.jpg — resizes to 854x480 and overwrites.")
        sys.exit(1)

    file_path = sys.argv[1]
    # Strip .jpg extension if provided — the script appends it
    if file_path.endswith(".jpg"):
        file_path = file_path[:-4]
    jpg_path = f"{file_path}.jpg"
    print(f"Processing image: {jpg_path}")

    # Check if the file exists
    if not os.path.exists(jpg_path):
        print(f"Error: File {jpg_path} not found.")
        sys.exit(1)

    # Get image dimensions using PIL
    width, height, dpi = get_image_dimensions(jpg_path)

    # Calculate scale factor based on desired height of 480, maintaining aspect ratio
    scale_factor = 480 / height
    print(f"  Calculated scale factor: {scale_factor}")

    # Calculate new width based on scale factor
    new_width = int(width * scale_factor)
    print(f"  New width: {new_width}")

    try:
        # Open the image
        image = Image.open(jpg_path)
        print("  Image opened successfully.")

        # Resize the image
        resized_image = image.resize((new_width, 480), Image.Resampling.LANCZOS)
        print("  Image resized successfully.")

        # Calculate the cropping box
        left = (resized_image.width - 854) / 2
        top = 0
        right = (resized_image.width + 854) / 2
        bottom = 480
        print(f"  Cropping box: left={left}, top={top}, right={right}, bottom={bottom}")

        # Crop the image
        cropped_image = resized_image.crop((left, top, right, bottom))
        print("  Image cropped successfully.")

        # Save the processed image, overwriting the original
        cropped_image.save(jpg_path)
        print(f"  Image saved to {jpg_path}")

    except Exception as e:
        print(f"Error processing image: {e}")
        sys.exit(1)
