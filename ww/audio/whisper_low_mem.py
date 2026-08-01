#!/usr/bin/env python3
"""Memory-safe Whisper transcription for large-v3 on a 12GB GPU.

Standard whisper.load_model() loads the fp16 checkpoint onto the GPU and
simultaneously builds an fp32 model, spiking ~10 GB of VRAM. This loader
keeps the checkpoint on CPU and moves the model to the GPU only in fp16
(~3.2 GB for large-v3).

Usage: ww whisper <audio> --low-memory [--model large-v3] [--language zh]
"""

import argparse
import os

import torch
import torch.nn as nn
import torch.nn.functional as F

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


class LayerNormFP16(nn.LayerNorm):
    """Whisper's LayerNorm runs in fp32 but uses weights as-is; with a half
    model the weights are half, so cast them to fp32 too."""

    def forward(self, x):
        w = self.weight.float() if self.weight is not None else None
        b = self.bias.float() if self.bias is not None else None
        return F.layer_norm(x.float(), self.normalized_shape, w, b).type(x.dtype)


def load_model_mem_safe(name: str, device: str = "cuda"):
    """Load a cached whisper checkpoint straight to GPU in fp16 only."""
    import whisper.model as wm
    from whisper import ModelDimensions, Whisper, _ALIGNMENT_HEADS

    cache = os.path.expanduser("~/.cache/whisper")
    checkpoint_path = os.path.join(cache, f"{name}.pt")
    if not os.path.isfile(checkpoint_path):
        raise FileNotFoundError(
            f"Model not cached: {checkpoint_path} (download first with: whisper {name})"
        )
    print(f"[load] checkpoint on CPU: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)

    dims = ModelDimensions(**checkpoint["dims"])
    # Patch before instantiating so the half model is fully fp16-capable
    wm.LayerNorm = LayerNormFP16
    model = Whisper(dims)
    model.load_state_dict(checkpoint["model_state_dict"])
    if name in _ALIGNMENT_HEADS:
        model.set_alignment_heads(_ALIGNMENT_HEADS[name])
    del checkpoint

    # Move to GPU as fp16 only (avoids the fp32 -> fp16 peak of the stock loader)
    model = model.half().to(device)
    return model


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Memory-safe Whisper transcription: loads the model to GPU as fp16 "
            "only (~3.2 GB for large-v3, fits a 12 GB card)."
        )
    )
    parser.add_argument(
        "audio", help="Path to the audio/video file (mp4, mp3, wav, ...)"
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model (default: large-v3; must be cached in ~/.cache/whisper)",
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
        "--device", default="cuda", help="Compute device (default: cuda)"
    )
    args = parser.parse_args()

    try:
        import whisper
    except ImportError:
        print(
            "Error: 'whisper' module not found. Install via: pip install -U openai-whisper"
        )
        raise SystemExit(1)

    audio = os.path.abspath(args.audio)
    if not os.path.isfile(audio):
        print(f"Error: file not found: {audio}")
        raise SystemExit(1)

    model = load_model_mem_safe(args.model, args.device)
    if args.device.startswith("cuda") and torch.cuda.is_available():
        vram = torch.cuda.memory_allocated() / 2**30
        print(f"[load] model {args.model} on {args.device}, VRAM used: {vram:.2f} GiB")
    else:
        print(f"[load] model {args.model} on {args.device}")

    result = whisper.transcribe(
        model,
        audio,
        language=args.language,
        task=args.task,
        fp16=True,
        verbose=False,
    )

    # Write outputs as <audio_stem>.txt / .srt / .json / .vtt / .tsv
    out_dir = os.path.dirname(audio)
    stem = os.path.splitext(os.path.basename(audio))[0]
    writer = whisper.utils.get_writer("all", out_dir)
    writer(result, audio)
    print(f"[done] outputs written to {out_dir}/{stem}.*")
    print(f"[done] segments: {len(result['segments'])}")


if __name__ == "__main__":
    main()
