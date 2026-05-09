#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys


def _resolve_input(path):
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        print(f"Error: file not found: {abs_path}")
        sys.exit(1)
    return abs_path


def _build_cmd(filename, model, device, language, output_dir):
    return [
        "whisper",
        filename,
        "--model",
        model,
        "--device",
        device,
        "--language",
        language,
        "--output_dir",
        output_dir,
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Run OpenAI whisper on an mp4 (Chinese, large model, CUDA by default)."
    )
    parser.add_argument("input_file", help="Path to the mp4 file (any directory)")
    parser.add_argument(
        "--model", default="large", help="Whisper model (default: large)"
    )
    parser.add_argument(
        "--device", default="cuda", help="Compute device (default: cuda)"
    )
    parser.add_argument(
        "--language", default="Chinese", help="Source language (default: Chinese)"
    )
    args = parser.parse_args()

    if shutil.which("whisper") is None:
        print(
            "Error: 'whisper' CLI not found. Install via: pip install -U openai-whisper"
        )
        sys.exit(1)

    input_path = _resolve_input(args.input_file)
    parent_dir = os.path.dirname(input_path)
    filename = os.path.basename(input_path)
    output_dir = os.getcwd()

    cmd = _build_cmd(filename, args.model, args.device, args.language, output_dir)
    print(f"[whisper] cwd={parent_dir}")
    print(f"[whisper] output_dir={output_dir}")
    print(f"[whisper] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=parent_dir)
    sys.exit(result.returncode)
