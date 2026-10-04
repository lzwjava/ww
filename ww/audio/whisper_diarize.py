#!/usr/bin/env python3
"""
whisper_diarize.py — Whisper transcription with optional speaker diarization via whisperx.

Uses faster-whisper backend + pyannote for speaker labels.
Outputs a .txt file with [START → END] [SPEAKER:] text per segment.

Diarization requires a valid HuggingFace token with accepted pyannote access
(one-time, browser):
  https://huggingface.co/pyannote/speaker-diarization-community-1  (whisperx default)
  https://huggingface.co/pyannote/speaker-diarization-3.1          (--diarize-model)
  https://huggingface.co/pyannote/segmentation-3.0                 (underlying model)

The token is taken from --hf-token, the HF_TOKEN env var, or the token file
cached by `huggingface-cli login` (~/.cache/huggingface/token). Without any of
those, runs transcription-only (no speaker labels).
"""

import argparse
import glob
import importlib.util
import os
import sys


def _prepend_libpython_dir():
    """Make torchcodec loadable when the interpreter lacks libpython3.11.so.1.0.

    pyannote.audio >= 4 imports torchcodec for file-based audio decoding.
    torchcodec ships one .so set per FFmpeg major (4-7); on this machine the
    FFmpeg-6 variant matches the system libav* libraries, but its custom-ops
    library also links libpython3.11.so.1.0.  /usr/bin/python3.11 is Ubuntu's
    static ESM build (no -dev package), so that file is absent and torchcodec
    refuses to load -- pyannote then prints a long "torchcodec is not installed
    correctly" warning at every run.

    We locate an ABI-compatible shared libpython under uv-managed / pyenv
    Pythons and put its directory on LD_LIBRARY_PATH.  Only the re-exec'd venv
    interpreter benefits (ld.so reads the variable at process start), and the
    running interpreter's already-exported Python symbols win over the freshly
    dlopen'd library, so this is safe.  If none is found, behavior is unchanged
    (pyannote merely warns again).
    """
    if "libpython3.11.so.1.0" in os.environ.get("LD_LIBRARY_PATH", ""):
        return
    bases = [
        os.path.expanduser("~/.local/share/uv/python"),
        os.path.expanduser("~/.pyenv/versions"),
    ]
    lib_dirs = []
    for base in bases:
        for pattern in ("cpython-3.11*/lib", "3.11*/lib"):
            lib_dirs.extend(sorted(glob.glob(os.path.join(base, pattern))))
    for d in lib_dirs:
        if os.path.isfile(os.path.join(d, "libpython3.11.so.1.0")):
            current = os.environ.get("LD_LIBRARY_PATH", "")
            parts = current.split(":") if current else []
            if d not in parts:
                os.environ["LD_LIBRARY_PATH"] = d + ((":" + current) if current else "")
            return


def _ensure_deps(*module_names):
    """Re-exec this script with the project venv python.

    `ww` is installed as a global console script (system python), while
    whisperx/torch live in the project .venv.  The system python can also
    carry stale copies of these deps, so always prefer the venv unless we
    are already running inside it.
    """
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    venv_py = os.path.join(root, ".venv", "bin", "python")
    in_venv = os.path.realpath(sys.prefix) == os.path.realpath(
        os.path.dirname(os.path.dirname(venv_py))
    )
    if in_venv:
        return  # pinned venv deps are already active
    if not os.path.isfile(venv_py):
        missing = [m for m in module_names if importlib.util.find_spec(m) is None]
        print(
            f"Error: missing modules {missing} and no project venv at {venv_py}. "
            "Run `uv sync` in the ww project first.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    # torchcodec (imported by pyannote.audio via whisperx) fails to dlopen under
    # the static system python3.11 unless libpython3.11.so.1.0 is reachable.
    _prepend_libpython_dir()
    print(f"[ww] Re-running with project venv python: {venv_py}", file=sys.stderr)
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


def main():
    _ensure_deps("whisperx", "torch")
    import torch  # type: ignore[reportMissingImports]
    import whisperx  # type: ignore[reportMissingImports]

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
        help="HuggingFace token for pyannote diarization. Falls back to HF_TOKEN env var "
        "and then to the token cached by `huggingface-cli login`. Without any token, "
        "runs transcription-only (no speaker labels).",
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=None,
        help="Hint: exact number of speakers (improves diarization accuracy)",
    )
    parser.add_argument(
        "--diarize-model",
        default=None,
        help="pyannote pipeline repo for diarization (default: whisperx's "
        "pyannote/speaker-diarization-community-1). Use pyannote/speaker-diarization-3.1 "
        "or the community pipeline after accepting access on huggingface.co.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Batch size for transcription (default: 4)",
    )
    parser.add_argument(
        "--no-align",
        action="store_true",
        help="Skip wav2vec2 alignment step (faster, less accurate timestamps)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: <input>_diarized.txt or <input>_transcribed.txt)",
    )
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="Unset proxy env vars for model downloads (for machines with a direct "
        "route to huggingface.co; otherwise the default proxy env is kept)",
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_file)
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    hf_token = args.hf_token or os.environ.get("HF_TOKEN")
    if not hf_token:
        # Fall back to the token cached by `huggingface-cli login`.
        try:
            with open(
                os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "token"),
                encoding="utf-8",
            ) as f:
                hf_token = f.read().strip()
        except OSError:
            hf_token = None
    do_diarize = bool(hf_token)
    if not do_diarize:
        print(
            "      No HuggingFace token found — running transcription-only (no speaker "
            "labels). Pass --hf-token or set HF_TOKEN."
        )

    # Diarization needs to download pyannote models from the Hub.  Proxy env is
    # kept by default (some machines have no direct route to huggingface.co);
    # --no-proxy opts into the old behavior for boxes with a direct connection.
    if args.no_proxy:
        _disable_proxy()

    output_path = args.output
    if not output_path:
        base, _ = os.path.splitext(input_path)
        suffix = "_diarized.txt" if do_diarize else "_transcribed.txt"
        output_path = base + suffix

    # Step 1: Transcribe
    print(
        f"[1/{'3' if do_diarize else '2'}] Loading whisperx model '{args.model}' on {args.device} ({args.compute_type})..."
    )
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
                result["segments"],
                model_a,
                metadata,
                audio,
                args.device,
                return_char_alignments=False,
            )
        except Exception as e:
            print(f"      Alignment failed ({e}), using unaligned timestamps")

    # Step 3: Diarize (optional — needs pyannote token)
    if do_diarize:
        print("[3/3] Running speaker diarization...")
        try:
            from whisperx.diarize import DiarizationPipeline  # type: ignore[reportMissingImports]

            diarize_model = DiarizationPipeline(
                model_name=args.diarize_model, token=hf_token, device=args.device
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
