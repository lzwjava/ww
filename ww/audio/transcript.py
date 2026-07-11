"""
ww transcript — extract transcript text from Google Cloud Speech-to-Text JSON to markdown
"""

import json
import argparse


def extract_transcript(json_path):
    """Load Google Cloud STT JSON and extract transcript + optional word timestamps."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    parts = []
    word_parts = []

    for result in results:
        alternatives = result.get("alternatives", [])
        for alt in alternatives:
            transcript = alt.get("transcript", "")
            confidence = alt.get("confidence")
            words = alt.get("words", [])

            if transcript:
                parts.append(transcript)

            if words:
                for w in words:
                    word = w.get("word", "")
                    start = w.get("startOffset", "")
                    end = w.get("endOffset", "")
                    c = w.get("confidence")
                    ts = ""
                    if start and end:
                        ts = f"[{start} → {end}]"
                    elif start:
                        ts = f"[{start}]"
                    conf = f" (c={c:.2f})" if c is not None else ""
                    word_parts.append(f"- {word} {ts}{conf}")

    full_transcript = " ".join(parts)

    # Output markdown
    lines = []
    lines.append("# Transcript")
    lines.append("")
    lines.append(f"**Source:** `{json_path}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Full Transcript")
    lines.append("")
    lines.append(full_transcript)
    lines.append("")

    if word_parts:
        lines.append("---")
        lines.append("")
        lines.append("## Word Timestamps")
        lines.append("")
        lines.extend(word_parts)
        lines.append("")

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
