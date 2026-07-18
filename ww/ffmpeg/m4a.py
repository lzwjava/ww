#!/usr/bin/env python3
"""Convert .m4a file(s) to MP3, combining multiple files into one."""

import os
import subprocess
import sys
import tempfile


def _print_help():
    print("Usage: ww ffmpeg m4a <file1.m4a> [file2.m4a ...]")
    print()
    print("Convert .m4a file(s) to MP3. If multiple files are given,")
    print("they are combined into a single MP3 file.")
    print()
    print("Examples:")
    print("  ww ffmpeg m4a recording.m4a")
    print("  ww ffmpeg m4a part1.m4a part2.m4a part3.m4a")


def _convert_m4a_to_mp3(m4a_path, mp3_path):
    """Convert a single .m4a file to .mp3 using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        m4a_path,
        "-c:a",
        "libmp3lame",
        "-q:a",
        "2",
        mp3_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error converting {m4a_path}: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        _print_help()
        return

    input_files = sys.argv[1:]

    # Check all files exist and are .m4a
    for f in input_files:
        if not os.path.isfile(f):
            print(f"Error: File not found: {f}", file=sys.stderr)
            sys.exit(1)
        ext = os.path.splitext(f)[1].lower()
        if ext != ".m4a":
            print(f"Error: Not a .m4a file: {f}", file=sys.stderr)
            sys.exit(1)

    if len(input_files) == 1:
        # Single file: just convert to MP3
        base = os.path.splitext(input_files[0])[0]
        output = f"{base}.mp3"
        print(f"Converting {input_files[0]} -> {output} ...")
        _convert_m4a_to_mp3(input_files[0], output)
        print(f"Done: {output}")
        return

    # Multiple files: convert each to temp MP3, then combine
    temp_files = []
    for i, f in enumerate(input_files):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        print(f"Converting {f} -> temp#{i + 1}.mp3 ...")
        _convert_m4a_to_mp3(f, tmp.name)
        temp_files.append(tmp.name)

    # Combine all temp MP3s
    base = os.path.splitext(input_files[0])[0]
    output = f"{base}_combined.mp3"

    # Use concat demuxer for combining
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as flist:
        for tf in temp_files:
            flist.write(f"file '{os.path.abspath(tf)}'\n")
        filelist = flist.name

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
            output,
        ]
        print(f"Combining {len(temp_files)} converted files into {output} ...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("Direct copy failed, trying re-encode merge ...")
            inputs = []
            for tf in temp_files:
                inputs.extend(["-i", tf])
            n = len(temp_files)
            filter_parts = "".join(f"[{i}:a]" for i in range(n))
            cmd2 = [
                "ffmpeg",
                "-y",
                *inputs,
                "-filter_complex",
                f"{filter_parts}concat=n={n}:v=0:a=1[outa]",
                "-map",
                "[outa]",
                output,
            ]
            result2 = subprocess.run(cmd2, capture_output=True, text=True)
            if result2.returncode != 0:
                print(f"Error combining files: {result2.stderr}", file=sys.stderr)
                sys.exit(1)

        print(f"Done: {output}")
    finally:
        os.unlink(filelist)
        for tf in temp_files:
            os.unlink(tf)


if __name__ == "__main__":
    main()
