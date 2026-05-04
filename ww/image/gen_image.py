import os
import sys
from datetime import datetime

import pyperclip
from google import genai  # type: ignore[import]
from google.genai import types  # type: ignore[import]


def read_clipboard():
    text = pyperclip.paste().strip()
    if not text:
        print("Error: clipboard is empty")
        sys.exit(1)
    return text


def generate_image(prompt, model="imagen-3.0-generate-002"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set in .env")
        sys.exit(1)
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1),
        )
    except Exception as e:
        print(f"Error: image generation failed — {e}")
        sys.exit(1)
    return response.generated_images[0].image.image_bytes


def save_image(data, path):
    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError as e:
        print(f"Error: could not save image — {e}")
        sys.exit(1)
    print(f"Saved: {path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate an image from clipboard text"
    )
    parser.add_argument("--output", type=str, default=None, help="Output PNG path")
    parser.add_argument(
        "--model", type=str, default="imagen-3.0-generate-002", help="Imagen model"
    )
    args = parser.parse_args()

    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        args.output = f"gen-image-{timestamp}.png"

    prompt = read_clipboard()
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"Generating image with {args.model}...")
    data = generate_image(prompt, model=args.model)
    save_image(data, args.output)
