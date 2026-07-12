"""
ww transcript — extract transcript text from Google Cloud Speech-to-Text JSON to markdown
"""

import json
import argparse


def extract_transcript(json_path):
    """Load Google Cloud STT JSON and extract transcript to markdown."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    parts = []

    for result in results:
        for alt in result.get("alternatives", []):
            transcript = alt.get("transcript", "")
            if transcript:
                parts.append(transcript)

    full_transcript = " ".join(parts)

    lines = [
        "# Transcript",
        "",
        f"**Source:** `{json_path}`",
        "",
        "---",
        "",
        "## Full Transcript",
        "",
        full_transcript,
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract transcript from Google Cloud STT JSON to markdown"
    )
    parser.add_argument("json_path", help="Path to Google Cloud STT JSON file")
    parser.add_argument("-o", "--output", help="Output markdown file (default: stdout)")
    args = parser.parse_args()

    md = extract_transcript(args.json_path)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Transcript written to {args.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
