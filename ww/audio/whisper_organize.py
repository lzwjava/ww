import argparse
import os
import sys
import time

from ww.llm.openrouter_client import stream_openrouter_api


ORGANIZE_RULE = """You are given a raw Whisper transcription of a conversation. Your job is to lightly clean it up while preserving the original conversation as faithfully as possible.

Rules:

1. **Speaker labels.** Identify distinct speakers and label them consistently (A:, B:, C:, etc.). Use context clues — greetings, topic changes, turn-taking patterns, references to each other — to distinguish speakers. If only one speaker is detectable, use a single label.

2. **Fix grammar and fluency.** Fix obvious grammar mistakes, broken sentences, and awkward phrasing — but keep the original meaning, tone, and word choice intact. Do NOT rewrite or rephrase what someone said. Do NOT make it sound more formal or polished than the original.

3. **Keep everything.** Do not summarize, condense, or drop any content. Every substantive statement must appear in the output. The output should be roughly the same length as the input.

4. **Remove only true noise.** Remove filler words (um, uh, er, ah, mm), false starts where the speaker restarts mid-sentence, and repeated stutters. Keep all substantive content including hedging ("I think", "maybe"), back-and-forth ("right", "exactly", "yeah" when used as real agreement), and casual language.

5. **Preserve specifics.** Keep all names, numbers, dates, technical terms, product names, URLs, file paths, code references, and concrete details exactly as spoken. Convert spoken numbers to digits when clear ("fifty" → "50").

6. **No reorganization.** Keep the chronological order of the conversation. Do not group topics or restructure.

7. **Output format.** Use this format:

```
A: [what speaker A said]

B: [what speaker B said]

A: [next thing speaker A said]
```

Blank line between each turn. Each speaker's turn should be one paragraph (or multiple paragraphs if they spoke at length on different sub-points). Use standard Markdown. Do NOT include a title, summary, headers, or any preamble — just the labeled conversation.

8. **Code-switching.** If the conversation mixes languages (e.g. Chinese and English), keep technical terms and proper nouns in their original form. Translate the rest to fluent English.

9. **Unclear segments.** If a segment is truly unintelligible, mark it with (unclear). Use this sparingly — only when meaning cannot be reasonably inferred.

10. **Merge rapid-fire turns.** If two speakers exchange several short back-and-forth turns that form a single coherent exchange (e.g. quick confirmations, brief Q&A, rapid agreement/disagreement), combine them into one turn per speaker. Use a line break within the turn for each distinct utterance. Do NOT merge turns that are separated by topic changes or that belong to different conversational threads.
"""


def _read_input(path):
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        print(f"Error: file not found: {abs_path}")
        sys.exit(1)
    with open(abs_path, "r", encoding="utf-8") as f:
        return abs_path, f.read()


def _output_path(input_path):
    root, _ = os.path.splitext(input_path)
    return root + ".organized.md"


def _build_prompt(transcript):
    return f"{ORGANIZE_RULE}\n\n---\n\nTranscription:\n\n{transcript}"


def _stream_to_stdout(prompt, model, debug):
    chunks = []
    started = time.monotonic()
    first_chunk_at = None
    for text in stream_openrouter_api(prompt, model=model, debug=debug):
        if first_chunk_at is None:
            first_chunk_at = time.monotonic()
            print(
                f"[organize] first token in {first_chunk_at - started:.1f}s, streaming...\n"
            )
            print("---")
        sys.stdout.write(text)
        sys.stdout.flush()
        chunks.append(text)
    elapsed = time.monotonic() - started
    if first_chunk_at is None:
        print("[organize] warning: stream ended with no content")
    else:
        print("\n---")
    return "".join(chunks), elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Lightly organize a Whisper transcription: label speakers, fix grammar, keep original content."
    )
    parser.add_argument("input_file", help="Path to the .txt transcription file")
    parser.add_argument(
        "--model",
        default="deepseek/deepseek-v4-flash",
        help="OpenRouter model (default: deepseek/deepseek-v4-flash)",
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    input_path, transcript = _read_input(args.input_file)
    output_path = _output_path(input_path)
    prompt = _build_prompt(transcript)

    print(f"[organize] input={input_path} ({len(transcript)} chars)")
    print(f"[organize] output={output_path}")
    print(f"[organize] model={args.model}")
    print("[organize] connecting to OpenRouter...")

    organized, elapsed = _stream_to_stdout(prompt, args.model, args.debug)

    if not organized:
        print("[organize] no content received; not writing output file")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(organized)

    print(f"[organize] wrote {len(organized)} chars to {output_path} in {elapsed:.1f}s")
