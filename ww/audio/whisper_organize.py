import argparse
import os
import sys
import time

from ww.llm.openrouter_client import stream_openrouter_api


ORGANIZE_RULE = """You are given a raw Whisper transcription of a conversation. Your job is to lightly clean it up while preserving the original conversation as faithfully as possible.

Rules:

1. **No speaker labels.** Whisper transcription has no speaker labels, and you cannot reliably reconstruct who said what. Do NOT use labels like "Speaker A / Speaker B," "Person 1 / Person 2," or invent speaker names. Narrate the discussion in third person using a variety of phrases to avoid repetition. Use patterns like:
   - "They discussed …"
   - "One participant noted …"
   - "It was raised that …"
   - "Another argued …"
   - "Someone brought up …"
   - "The conversation turned to …"
   - "A point was made that …"
   - "There was agreement that …"
   - "One person pushed back, saying …"
   - "It was suggested that …"
   - "A counterpoint was raised: …"
   For clear question-and-answer dynamics, render as "one participant asked whether …; another responded that …" rather than guessing identities. For back-and-forth exchanges, you can group them: "A brief back-and-forth followed: one side argued X; the other countered that Y; the discussion settled on Z." Do NOT consistently associate a "voice" with a position — vary your phrasing.

2. **Fix grammar and fluency.** Fix obvious grammar mistakes, broken sentences, and awkward phrasing — but keep the original meaning, tone, and word choice intact. Do NOT rewrite or rephrase what someone said. Do NOT make it sound more formal or polished than the original.

3. **Keep everything.** Do not summarize, condense, or drop any content. Every substantive statement must appear in the output. The output should be roughly the same length as the input.

4. **Remove only true noise.** Remove filler words (um, uh, er, ah, mm), false starts where the speaker restarts mid-sentence, and repeated stutters. Keep all substantive content including hedging ("I think", "maybe"), back-and-forth ("right", "exactly", "yeah" when used as real agreement), and casual language.

5. **Preserve specifics.** Keep all names, numbers, dates, technical terms, product names, URLs, file paths, code references, and concrete details exactly as spoken. Convert spoken numbers to digits when clear ("fifty" → "50").

6. **No reorganization.** Keep the chronological order of the conversation. Do not group topics or restructure.

7. **Output format.** Write as flowing third-person prose. Each turn or exchange should be a paragraph. Use standard Markdown. Do NOT include a title, summary, headers, or any preamble — just the narrated conversation. Example:

They discussed the new deployment pipeline and whether to use GitHub Actions or Jenkins. One participant argued that GitHub Actions was simpler to maintain; another pushed back, noting that Jenkins offered more flexibility for complex build matrices. It was suggested that they could start with GitHub Actions for new repos and migrate existing ones later.

The conversation then turned to database scaling. There was agreement that read replicas would help, but no consensus on whether to use PgBouncer or built-in connection pooling. One person brought up a recent blog post comparing the two approaches.

8. **Code-switching.** If the conversation mixes languages (e.g. Chinese and English), keep technical terms and proper nouns in their original form. Translate the rest to fluent English.

9. **Unclear segments.** If a segment is truly unintelligible, mark it with (unclear). Use this sparingly — only when meaning cannot be reasonably inferred.

10. **Direct quotation.** When a speaker said something in a particularly striking, precise, or colorful way, you may use a short direct quote: "As one participant put it, 'the current pipeline is held together with duct tape and hope.'" Use direct quotes sparingly — no more than 2–3 per output.
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
        description="Lightly organize a Whisper transcription: fix grammar, remove noise, narrate in third person."
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
