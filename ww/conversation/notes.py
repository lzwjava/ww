import argparse
import json
import os
from datetime import date

DEFAULT_CONVERSATION_DIR = os.path.join("scripts", "conversation")
DEFAULT_NOTES_DIR = "notes"


def convert_conversation_to_notes(conversation_dir, notes_dir):
    print("Starting conversation to notes conversion...")
    os.makedirs(notes_dir, exist_ok=True)
    print(f"Created or verified notes directory: {notes_dir}")
    converted = 0
    for filename in os.listdir(conversation_dir):
        if filename.endswith(".json") and not filename.endswith("-zh.json"):
            print(f"Processing file: {filename}")
            filepath = os.path.join(conversation_dir, filename)
            with open(filepath, "r") as f:
                try:
                    conversation = json.load(f)
                    print(f"Successfully loaded JSON from {filename}")
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in {filename}. Skipping.")
                    continue

            today = date.today()
            date_str = today.strftime("%Y-%m-%d")
            base_filename = os.path.splitext(filename)[0]
            notes_filename = f"{date_str}-{base_filename}-conv-en.md"
            notes_filepath = os.path.join(notes_dir, notes_filename)
            title = base_filename.replace("-", " ").title() + " - Conversation"
            print(f"Creating notes file: {notes_filepath} with title: {title}")

            existing_files = [
                f
                for f in os.listdir(notes_dir)
                if f.endswith("-conv-en.md") and base_filename in f
            ]
            if existing_files:
                print(
                    f"Notes file with base filename {base_filename} already exists. Skipping."
                )
                continue

            with open(notes_filepath, "w") as outfile:
                outfile.write(f"""---
audio: false
generated: true
image: false
lang: en
layout: post
model: none
title: {title}
translated: false
type: note
---

""")
                for item in conversation:
                    speaker = item.get("speaker")
                    line = item.get("line")
                    if speaker and line:
                        outfile.write(f"{speaker}: {line}\n\n")
                    else:
                        print(
                            f"Skipping item with missing speaker or line in {filename}: {item}"
                        )
            print(f"Successfully wrote notes to {notes_filepath}")
            converted += 1
    print(f"Finished. Converted {converted} conversations to notes.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert conversation JSON files to markdown notes."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=DEFAULT_CONVERSATION_DIR,
        help=f"Input directory for conversation JSON files (default: {DEFAULT_CONVERSATION_DIR})",
    )
    parser.add_argument(
        "--notes-dir",
        type=str,
        default=DEFAULT_NOTES_DIR,
        help=f"Output directory for markdown notes (default: {DEFAULT_NOTES_DIR})",
    )
    args = parser.parse_args()

    convert_conversation_to_notes(args.input_dir, args.notes_dir)


if __name__ == "__main__":
    main()
