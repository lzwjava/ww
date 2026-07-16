#!/usr/bin/env python3
"""Merge two or more audio/video files using ffmpeg."""

import os
import subprocess
import sys
import tempfile


def _is_audio_ext(ext):
    return ext.lower() in (".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma")


def _print_help():
    print("Usage: ww ffmpeg merge <file1> <file2> [... <fileN>]")
    print()
    print("Merge two or more audio/video files (mp3, mp4, wav, etc.) into one.")
    print("Output file is saved as <first_file>_merged.<ext>")
    print()
    print("Examples:")
    print("  ww ffmpeg merge intro.mp3 main.mp3 outro.mp3")
    print("  ww ffmpeg merge part1.mp4 part2.mp4 part3.mp4")
    print("  ww ffmpeg merge track1.wav track2.wav track3.wav")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        _print_help()
        return

    input_files = sys.argv[1:]

    if len(input_files) < 2:
        print("Error: At least two input files are required.")
        sys.exit(1)

    # Check all files exist
    for f in input_files:
        if not os.path.isfile(f):
            print(f"Error: File not found: {f}")
            sys.exit(1)

    first = input_files[0]
    base, ext = os.path.splitext(first)
    output_file = f"{base}_merged{ext}"

    # -- Fast path: concat demuxer with stream copy (no re-encode) --
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for inp in input_files:
            f.write(f"file '{os.path.abspath(inp)}'\n")
        filelist = f.name

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            filelist,
            "-c",
            "copy",
            output_file,
        ]

        print(f"Merging {len(input_files)} files into {output_file} ...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Done: {output_file}")
            return

        # -- Fallback: concat filter with re-encode --
        if _is_audio_ext(ext):
            print("Direct copy failed, trying re-encode merge (audio)...")
            n = len(input_files)
            inputs = []
            for inp in input_files:
                inputs.extend(["-i", inp])
            filter_parts = "".join(f"[{i}:a]" for i in range(n))
            filter_complex = f"{filter_parts}concat=n={n}:v=0:a=1[outa]"
            cmd2 = [
                "ffmpeg",
                "-y",
                *inputs,
                "-filter_complex",
                filter_complex,
                "-map",
                "[outa]",
                output_file,
            ]
        else:
            print("Direct copy failed, trying re-encode merge (video)...")
            n = len(input_files)
            inputs = []
            for inp in input_files:
                inputs.extend(["-i", inp])
            filter_complex = "".join(f"[{i}:v][{i}:a]" for i in range(n))
            filter_complex += f"concat=n={n}:v=1:a=1[outv][outa]"
            cmd2 = [
                "ffmpeg",
                "-y",
                *inputs,
                "-filter_complex",
                filter_complex,
                "-map",
                "[outv]",
                "-map",
                "[outa]",
                output_file,
            ]

        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        if result2.returncode != 0:
            print(f"Error merging files: {result2.stderr}")
            sys.exit(1)

        print(f"Done: {output_file}")
    finally:
        os.unlink(filelist)


if __name__ == "__main__":
    main()
