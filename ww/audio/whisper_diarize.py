#!/usr/bin/env python3
"""
whisper_diarize.py — Whisper transcription with optional speaker diarization via whisperx.

Uses faster-whisper backend + pyannote for speaker labels.
Outputs a .txt file with [START → END] [SPEAKER:] text per segment.

Diarization requires a valid HuggingFace token with accepted pyannote license:
  https://huggingface.co/pyannote/speaker-diarization-3.1
  https://huggingface.co/pyannote/segmentation-3.0

Without --hf-token, runs transcription-only (no speaker labels).
"""

import argparse
import os
import sys

import whisperx
import torch


def _disable_proxy():
    """Unset proxy env vars — HuggingFace downloads stall through local proxy."""
    for var in (
        "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
        "all_proxy", "ALL_PROXY",
    ):
        os.environ.pop(var, None)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio with optional speaker diarization (whisperx)."
    )
    parser.add_argument("input_file", help="Path to audio/video file")
    parser.add_argument(
        "--model", default="large-v3", help="Whisper model (default: large-v3)"
    )
    parser.add_argument(
        "--language", default="zh", help="Language code (default: zh for Chinese)"
    )
    parser.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Compute device (default: cuda)",
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        help="Compute type for faster-whisper (default: int8, use float16 for best quality)",
    )
    parser.add_argument(
        "--hf-token",
        default=None,
        help="HuggingFace token for pyannote diarization. Falls back to HF_TOKEN env var. "
             "Without this, runs transcription-only (no speaker labels).",
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=None,
        help="Hint: exact number of speakers (improves diarization accuracy)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=4, help="Batch size for transcription (default: 4)"
    )
    parser.add_argument(
        "--no-align", action="store_true",
        help="Skip wav2vec2 alignment step (faster, less accurate timestamps)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: <input>_diarized.txt or <input>_transcribed.txt)",
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_file)
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    hf_token = args.hf_token or os.environ.get("HF_TOKEN")
    do_diarize = bool(hf_token)

    # Disable proxy to avoid HuggingFace download stalls
    _disable_proxy()

    output_path = args.output
    if not output_path:
        base, _ = os.path.splitext(input_path)
        suffix = "_diarized.txt" if do_diarize else "_transcribed.txt"
        output_path = base + suffix

    # Step 1: Transcribe
    print(f"[1/{'3' if do_diarize else '2'}] Loading whisperx model '{args.model}' on {args.device} ({args.compute_type})...")
    model = whisperx.load_model(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        language=args.language,
    )

    print("[2/{}] Transcribing...".format("3" if do_diarize else "2"))
    audio = whisperx.load_audio(input_path)
    result = model.transcribe(audio, batch_size=args.batch_size, language=args.language)
    print(f"      Got {len(result['segments'])} segments")

    # Step 2: Align (optional — needs wav2vec2 download)
    if not args.no_align:
        try:
            print("[2.5] Aligning timestamps (wav2vec2)...")
            model_a, metadata = whisperx.load_align_model(
                language_code=args.language, device=args.device
            )
            result = whisperx.align(
                result["segments"], model_a, metadata, audio, args.device,
                return_char_alignments=False,
            )
        except Exception as e:
            print(f"      Alignment failed ({e}), using unaligned timestamps")

    # Step 3: Diarize (optional — needs pyannote token)
    if do_diarize:
        print("[3/3] Running speaker diarization...")
        try:
            from whisperx.diarize import DiarizationPipeline
            diarize_model = DiarizationPipeline(
                token=hf_token, device=args.device
            )
            diarize_kwargs = {}
            if args.num_speakers:
                diarize_kwargs["num_speakers"] = args.num_speakers
            diarize_segments = diarize_model(audio, **diarize_kwargs)
            result = whisperx.assign_word_speakers(diarize_segments, result)
        except Exception as e:
            print(f"      Diarization failed ({e}), outputting without speaker labels")
            do_diarize = False

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in result["segments"]:
            speaker = seg.get("speaker", "")
            start = seg["start"]
            end = seg["end"]
            text = seg["text"].strip()
            if do_diarize and speaker:
                line = f"[{start:.1f}s → {end:.1f}s] {speaker}: {text}"
            else:
                line = f"[{start:.1f}s → {end:.1f}s] {text}"
            print(line)
            f.write(line + "\n")

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
