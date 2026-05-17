import sys
import time

from dotenv import load_dotenv

from ww.image.screenshot import capture_screenshot
from ww.note.screenshot_log import (
    _create_note_file,
    _generate_title_from_content,
    _get_screenshot_dir,
    _print_note_url,
    _summarize_with_extra_prompt,
    _vision_describe,
)


def main():
    load_dotenv()

    # Ask how many screenshots
    n_input = input("How many screenshots? ").strip()
    n = int(n_input) if n_input else 1

    # Ask delay
    delay_input = input("Delay before each screenshot (seconds)? ").strip()
    delay = int(delay_input) if delay_input else 3

    # Determine screenshot directory
    screenshot_dir = _get_screenshot_dir()

    # Capture screenshots
    screenshot_paths = []
    for i in range(n):
        print(f"Screenshot {i + 1}/{n} — taking in {delay} seconds...")
        time.sleep(delay)
        path = capture_screenshot(screenshot_dir)
        if path:
            screenshot_paths.append(path)
        else:
            print(f"Warning: failed to capture screenshot {i + 1}/{n}")

    if not screenshot_paths:
        print("No screenshots captured. Exiting.")
        sys.exit(1)

    print(f"Captured {len(screenshot_paths)} screenshot(s).")

    # Ask for additional context
    extra_prompt = input("Additional context (or Enter to skip)? ").strip() or None

    # Describe screenshots with vision model
    print(f"Analyzing {len(screenshot_paths)} screenshot(s) with LLM vision...")
    description = _vision_describe(screenshot_paths, extra_prompt)

    # Summarize
    print("Summarizing content...")
    summary = _summarize_with_extra_prompt(description, extra_prompt)

    # Generate title
    print("Generating title...")
    full_title = _generate_title_from_content(summary, extra_prompt)

    # Create note file
    note_path = _create_note_file(summary, full_title, screenshot_paths)
    _print_note_url(note_path)
