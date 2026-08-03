#!/usr/bin/env python3
"""Transcribe audio via faster-whisper (CTranslate2 backend).

Replaces the old openai-whisper CLI wrapper.  Uses the same underlying
engine as whisperx and --low-memory, but provides a simpler interface
that mirrors the original openai-whisper CLI defaults (large model, CUDA).

Usage:
    ww whisper <audio-file>
    ww whisper <audio-file> --model large-v3 --device cuda --language zh
"""

import argparse
import importlib.util
import os
import sys


def _ensure_deps(*module_names):
    """Re-exec this script with the project venv python if a required module
    is missing in the current interpreter (the `ww` console script runs under
    the system python, while faster-whisper/torch live in the project .venv)."""
    missing = [m for m in module_names if importlib.util.find_spec(m) is None]
    if not missing:
        return
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    venv_py = os.path.join(root, ".venv", "Scripts", "python.exe")
    if not os.path.isfile(venv_py):
        venv_py = os.path.join(root, ".venv", "bin", "python")
    if not os.path.isfile(venv_py):
        print(
            "Error: project venv python not found. "
            "Run `uv sync` and try again.",
            file=sys.stderr,
        )
        sys.exit(1)
    os.execv(venv_py, [venv_py] + sys.argv)


def _resolve_input(path):
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        print(f"Error: file not found: {abs_path}", file=sys.stderr)
        sys.exit(1)
    return abs_path


def _format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    return f"{minutes:02d}:{secs:06.3f}"


def main():
    _ensure_deps("faster_whisper", "ctranslate2")
    from faster_whisper import WhisperModel  # type: ignore[reportMissingImports]

    parser = argparse.ArgumentParser(
        description="Transcribe audio via faster-whisper (CTranslate2 backend)."
    )
    parser.add_argument("input_file", help="Path to the audio file")
    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model name (default: large-v3, supports: tiny, base, small, medium, large-v3, etc.)",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Compute device (default: cuda, use 'cpu' for CPU inference)",
    )
    parser.add_argument(
        "--compute-type",
        default="float16",
        help="Compute type for GPU (default: float16, use 'int8_float16' for lower VRAM)",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Source language code (e.g. 'zh', 'ja', 'en'). Auto-detect if not set.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: current working directory)",
    )
    parser.add_argument(
        "--output-format",
        choices=["txt", "srt", "vtt", "tsv", "json", "all"],
        default="txt",
        help="Output format (default: txt, use 'all' for all formats)",
    )
    args = parser.parse_args()

    input_path = _resolve_input(args.input_file)
    output_dir = args.output_dir or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    basename = os.path.splitext(os.path.basename(input_path))[0]

    print(f"[whisper] Loading model '{args.model}' on {args.device} ({args.compute_type})...")
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
    )

    print(f"[whisper] Transcribing: {input_path}")
    if args.language:
        print(f"[whisper] Language: {args.language}")
    else:
        print("[whisper] Language: auto-detect")

    segments, info = model.transcribe(input_path, language=args.language, beam_size=5)

    detected_language = info.language
    print(f"\n[whisper] Detected language: {detected_language} ({info.language_probability * 100:.1f}%)")
    print(f"[whisper] Duration: {info.duration:.1f}s\n")

    segments = list(segments)

    # --- TXT output ---
    if args.output_format in ("txt", "all"):
        txt_path = os.path.join(output_dir, f"{basename}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for seg in segments:
                line = f"[{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}] {seg.text.strip()}"
                f.write(line + "\n")
        print(f"[whisper] Saved: {txt_path}")

    # --- SRT output ---
    if args.output_format in ("srt", "all"):
        srt_path = os.path.join(output_dir, f"{basename}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = _format_timestamp(seg.start).replace(".", ",")
                end = _format_timestamp(seg.end).replace(".", ",")
                f.write(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n\n")
        print(f"[whisper] Saved: {srt_path}")

    # --- VTT output ---
    if args.output_format in ("vtt", "all"):
        vtt_path = os.path.join(output_dir, f"{basename}.vtt")
        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for seg in segments:
                start = _format_timestamp(seg.start)
                end = _format_timestamp(seg.end)
                f.write(f"{start} --> {end}\n{seg.text.strip()}\n\n")
        print(f"[whisper] Saved: {vtt_path}")

    # --- TSV output ---
    if args.output_format in ("tsv", "all"):
        tsv_path = os.path.join(output_dir, f"{basename}.tsv")
        with open(tsv_path, "w", encoding="utf-8") as f:
            f.write("start\tend\ttext\n")
            for seg in segments:
                f.write(f"{seg.start}\t{seg.end}\t{seg.text.strip()}\n")
        print(f"[whisper] Saved: {tsv_path}")

    # --- JSON output ---
    if args.output_format in ("json", "all"):
        import json

        json_path = os.path.join(output_dir, f"{basename}.json")
        data = {
            "language": detected_language,
            "duration": info.duration,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                    "avg_logprob": getattr(seg, "avg_logprob", None),
                    "no_speech_prob": getattr(seg, "no_speech_prob", None),
                }
                for seg in segments
            ],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[whisper] Saved: {json_path}")

    # Also print to stdout
    print("\n--- Transcription ---")
    for seg in segments:
        print(f"[{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}] {seg.text.strip()}")