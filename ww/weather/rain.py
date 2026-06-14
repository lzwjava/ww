"""ww rain — Record a short video from the webcam and analyze rain intensity.

Usage:
    ww rain              # 3-second video, analyze rain
    ww rain --seconds 5  # 5-second video
    ww rain --keep       # Keep the captured video file
    ww rain --debug      # Show request details

Designed for in-car use: laptop webcam faces the windshield, window may be
closed. The vision model receives multiple frames and rates rain intensity.
"""

import base64
import os
import shutil
import subprocess
import sys
import tempfile
import glob as globmod


def _find_ffmpeg():
    for p in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if os.path.isfile(p):
            return p
    found = shutil.which("ffmpeg")
    if found:
        return found
    print("Error: ffmpeg not found. Install with: brew install ffmpeg")
    sys.exit(1)


def _record_video(ffmpeg_path, duration=3):
    """Record a short video from the default webcam via avfoundation."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    cmd = [
        ffmpeg_path,
        "-f",
        "avfoundation",
        "-framerate",
        "15",
        "-video_size",
        "640x480",
        "-i",
        "0",
        "-t",
        str(duration),
        "-pix_fmt",
        "yuv420p",
        "-y",
        tmp,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 10)
    if result.returncode != 0:
        err = result.stderr.strip().split("\n")[-1] if result.stderr else "unknown"
        print(f"Error recording video: {err}")
        if os.path.exists(tmp):
            os.remove(tmp)
        sys.exit(1)
    return tmp


def _extract_frames(video_path, num_frames=5):
    """Extract evenly-spaced frames from a video, return list of base64 JPEG strings."""
    out_dir = tempfile.mkdtemp()
    pattern = os.path.join(out_dir, "frame_%03d.jpg")
    # Extract 1 frame per second — simple and reliable
    subprocess.run(
        [
            _find_ffmpeg(),
            "-i",
            video_path,
            "-vf",
            "fps=1",
            "-frames:v",
            str(num_frames),
            "-y",
            pattern,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )

    frames = []
    for fpath in sorted(globmod.glob(os.path.join(out_dir, "frame_*.jpg"))):
        with open(fpath, "rb") as f:
            frames.append(base64.b64encode(f.read()).decode("utf-8"))
        os.remove(fpath)
    os.rmdir(out_dir)
    return frames


def _analyze_rain(frames, debug=False):
    """Send frames to vision model via OpenRouter and get rain intensity analysis."""
    from ww.env import load_env

    load_env()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    model = os.getenv("VISION_MODEL") or os.getenv("MODEL")
    if not model:
        print("Error: VISION_MODEL or MODEL env var required")
        sys.exit(1)

    # Build multimodal message with all frames
    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "You are a rain intensity analyzer. These are consecutive frames from a "
                "short video captured by a laptop webcam in a car. The webcam is pointed "
                "at the windshield (main driving wheel side). The window may be closed "
                "with a curtain, or open.\n\n"
                "Analyze the frames and determine the current rain intensity. Consider:\n"
                "- Water droplets on the glass\n"
                "- Visibility through the windshield\n"
                "- Streaks of rain visible\n"
                "- How much the view is obscured\n"
                "- Any wiper marks or water flow\n\n"
                "Rate the rain on this scale:\n"
                "  0 — No rain (clear, dry glass)\n"
                "  1 — Light drizzle (few scattered drops)\n"
                "  2 — Light rain (visible drops, mild streaking)\n"
                "  3 — Moderate rain (steady rain, reduced visibility)\n"
                "  4 — Heavy rain (intense, significant visibility reduction)\n"
                "  5 — Torrential (extremely heavy, near-zero visibility)\n\n"
                "Reply in this exact format:\n"
                "  Rain: [0-5] — [one-word label]\n"
                "  Detail: [1-2 sentence description of what you see]\n"
                "  Advice: [open/close window, drive carefully, etc.]"
            ),
        }
    ]

    for i, frame_b64 in enumerate(frames):
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"},
            }
        )

    import requests

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 200,
    }

    if debug:
        print(f"Model: {model}")
        print(f"Frames: {len(frames)}")
        print(f"Request size: ~{len(str(data)) // 1024}KB")

    response = requests.post(url, headers=headers, json=data, timeout=30)
    if not response.ok:
        print(f"API error: HTTP {response.status_code}")
        print(response.text[:500])
        sys.exit(1)

    body = response.json()
    result = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    return result


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if "--help" in argv or "-h" in argv:
        print("Usage: ww rain [--seconds N] [--keep] [--debug]")
        print("")
        print("Record a short video from the webcam and analyze rain intensity.")
        print("Designed for in-car use: webcam faces the windshield.")
        print("")
        print("Options:")
        print("  --seconds N   Video duration in seconds (default: 3)")
        print("  --keep        Keep the captured video file")
        print("  --debug       Show debug info")
        return

    duration = 3
    keep = False
    debug = False

    i = 0
    while i < len(argv):
        if argv[i] == "--seconds" and i + 1 < len(argv):
            try:
                duration = int(argv[i + 1])
            except ValueError:
                print(f"Invalid seconds: {argv[i + 1]}")
                sys.exit(1)
            i += 2
        elif argv[i] == "--keep":
            keep = True
            i += 1
        elif argv[i] == "--debug":
            debug = True
            i += 1
        else:
            i += 1

    duration = max(1, min(duration, 10))

    ffmpeg = _find_ffmpeg()
    print(f"Recording {duration}s video from webcam...")
    video_path = _record_video(ffmpeg, duration)

    try:
        size_kb = os.path.getsize(video_path) / 1024
        print(f"Video captured ({size_kb:.0f} KB). Extracting frames...")

        frames = _extract_frames(video_path, num_frames=5)
        if not frames:
            print("Error: no frames extracted from video")
            sys.exit(1)

        print(f"Extracted {len(frames)} frames. Analyzing rain...")

        result = _analyze_rain(frames, debug=debug)
        print()
        print(result)

    finally:
        if keep:
            print(f"\nVideo saved: {video_path}")
        elif os.path.exists(video_path):
            os.remove(video_path)


if __name__ == "__main__":
    main()
