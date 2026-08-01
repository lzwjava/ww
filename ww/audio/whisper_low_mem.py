#!/usr/bin/env python3
"""Low-VRAM Whisper transcription via faster-whisper (CTranslate2 backend).

Why faster-whisper and not openai-whisper for --low-memory?

- openai-whisper's load_model() builds an fp32 copy of the weights while
  loading the fp16 checkpoint, spiking ~10 GB VRAM for large-v3.  The old
  loader here patched around that (fp16-only load), but it relied on private
  APIs (_ALIGNMENT_HEADS, a monkeypatched LayerNorm) and on the 'whisper'
  module being importable in the running interpreter.
- faster-whisper is the transcription engine inside whisperx.  It loads
  CTranslate2 models directly in the requested compute type — float16
  (~3.2 GB) or int8 (~1.1 GB) for large-v3 — with no fp32 spike, and is
  typically several times faster than openai-whisper.
- We deliberately do NOT pull in full whisperx here: whisperx layers wav2vec2
  word-level alignment (~+1.2 GB VRAM, extra download) and optional pyannote
  diarization (HF token + model downloads) on top of faster-whisper, none of
  which plain transcription needs.  For speaker labels use `ww whisper diarize`.

Notes:
- Models are downloaded from HuggingFace (Systran/faster-whisper-*) on first
  use, cached under ~/.cache/huggingface/hub — separate from the openai-whisper
  ~/.cache/whisper/*.pt files.
- The `ww` console script usually runs under the system python, while the heavy
  deps live in the project venv.  _ensure_deps() re-execs this script with the
  venv python if faster-whisper is missing in the current interpreter.

Usage: ww whisper <audio> --low-memory [--model large-v3] [--language zh]
"""

import argparse
import importlib.util
import json
import os
import sys


def _ensure_deps(*module_names):
    """Re-exec this script with the project venv python if a required module
    is missing in the current interpreter.

    `ww` is installed as a global console script (system python), while the
    ML deps (faster-whisper, whisperx, ...) live in the project .venv.
    Without this, `ww whisper --low-memory` dies with ModuleNotFoundError
    even though the venv has everything.
    """
    missing = [m for m in module_names if importlib.util.find_spec(m) is None]
    if not missing:
        return
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    venv_py = os.path.join(root, ".venv", "bin", "python")
    if not os.path.isfile(venv_py):
        print(
            f"Error: missing modules {missing} and no project venv at {venv_py}. "
            "Run `uv sync` in the ww project first.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(
        f"[ww] {', '.join(missing)} not importable here; re-running with {venv_py}",
        file=sys.stderr,
    )
    os.execv(venv_py, [venv_py, os.path.abspath(__file__), *sys.argv[1:]])  # nosec B606 — fixed interpreter path, no shell


def _disable_proxy():
    """Unset proxy env vars — HuggingFace downloads stall through local proxy."""
    for var in (
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "all_proxy",
        "ALL_PROXY",
    ):
        os.environ.pop(var, None)


def _fmt_srt(seconds):
    ms = round((seconds - int(seconds)) * 1000)
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_vtt(seconds):
    return _fmt_srt(seconds).replace(",", ".")


def _write_outputs(audio_path, segments, info, task):
    """Write <stem>.txt/.srt/.vtt/.tsv/.json next to the audio file
    (mirrors openai-whisper's --output_format all)."""
    out_dir = os.path.dirname(audio_path)
    stem = os.path.splitext(os.path.basename(audio_path))[0]
    segs = list(segments)

    with open(os.path.join(out_dir, stem + ".txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(seg.text.strip() for seg in segs) + "\n")

    with open(os.path.join(out_dir, stem + ".srt"), "w", encoding="utf-8") as f:
        f.write(
            "".join(
                f"{i}\n{_fmt_srt(seg.start)} --> {_fmt_srt(seg.end)}\n{seg.text.strip()}\n\n"
                for i, seg in enumerate(segs, 1)
            )
        )

    with open(os.path.join(out_dir, stem + ".vtt"), "w", encoding="utf-8") as f:
        f.write(
            "WEBVTT\n\n"
            + "".join(
                f"{_fmt_vtt(seg.start)} --> {_fmt_vtt(seg.end)}\n{seg.text.strip()}\n\n"
                for seg in segs
            )
        )

    with open(os.path.join(out_dir, stem + ".tsv"), "w", encoding="utf-8") as f:
        f.write(
            "start\tend\ttext\n"
            + "".join(
                f"{seg.start:.6f}\t{seg.end:.6f}\t{seg.text.strip()}\n" for seg in segs
            )
        )

    data = {
        "task": task,
        "language": info.language,
        "duration": info.duration,
        "text": "\n".join(seg.text.strip() for seg in segs),
        "segments": [
            {
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "avg_logprob": seg.avg_logprob,
                "no_speech_prob": seg.no_speech_prob,
                "compression_ratio": seg.compression_ratio,
            }
            for seg in segs
        ],
    }
    with open(os.path.join(out_dir, stem + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return stem, len(segs)


def main():
    _ensure_deps("faster_whisper", "ctranslate2")
    from faster_whisper import WhisperModel  # type: ignore[reportMissingImports]

    parser = argparse.ArgumentParser(
        description=(
            "Low-VRAM Whisper transcription via faster-whisper: CTranslate2 "
            "models load directly in fp16 (~3.2 GB) or int8 (~1.1 GB) for "
            "large-v3, no fp32 spike."
        )
    )
    parser.add_argument(
        "audio", help="Path to the audio/video file (mp4, mp3, wav, ...)"
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model size or HF repo (default: large-v3; downloaded "
        "from HuggingFace on first use)",
    )
    parser.add_argument(
        "--language", default="zh", help="Source language (default: zh)"
    )
    parser.add_argument(
        "--task",
        default="transcribe",
        choices=["transcribe", "translate"],
        help="Transcribe or translate to English (default: transcribe)",
    )
    parser.add_argument(
        "--device", default="cuda", help="Compute device: cuda or cpu (default: cuda)"
    )
    parser.add_argument(
        "--compute-type",
        default="auto",
        choices=["auto", "float16", "int8", "float32"],
        help="Model precision (default: auto = float16 on cuda, int8 on cpu)",
    )
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="Unset proxy env vars for model downloads (HF downloads can stall "
        "through a local proxy)",
    )
    args = parser.parse_args()

    audio = os.path.abspath(args.audio)
    if not os.path.isfile(audio):
        print(f"Error: file not found: {audio}")
        raise SystemExit(1)

    if args.no_proxy:
        _disable_proxy()

    device = args.device
    compute = args.compute_type
    if device == "cuda":
        import ctranslate2  # type: ignore[reportMissingImports]

        if ctranslate2.get_cuda_device_count() == 0:
            print("[load] no CUDA device found, falling back to int8 on CPU")
            device, compute = "cpu", "int8"
        elif compute == "auto":
            compute = "float16"
    elif compute == "auto":
        compute = "int8"

    print(f"[load] loading '{args.model}' on {device} ({compute}) ...")
    model = WhisperModel(args.model, device=device, compute_type=compute)

    print(f"[transcribe] {audio} ...")
    segments, info = model.transcribe(
        audio,
        language=args.language,
        task=args.task,
        beam_size=5,
    )

    stem, n_segs = _write_outputs(audio, segments, info, args.task)
    out_dir = os.path.dirname(audio)
    print(f"[done] outputs written to {out_dir}/{stem}.*")
    print(
        f"[done] language={info.language} duration={info.duration:.1f}s segments={n_segs}"
    )


if __name__ == "__main__":
    main()
