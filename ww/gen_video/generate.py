#!/usr/bin/env python3
"""ww gen-video generate — Read markdown from pasteboard, send to the gen-video API server.

Reads content from the system clipboard, POSTs it to the GEN_VIDEO_SERVER_URL
endpoint, and downloads the generated video.

Usage:
    ww gen-video generate [options]

Environment:
    GEN_VIDEO_SERVER_URL   The gen-video API server URL (e.g. http://localhost:8000)
                           The /api/generate-video path is appended automatically.

Options:
    --output PATH   Where to save the generated video (default: gen_video_<timestamp>.mp4)
    --model MODEL   LLM model override to send to the server
    --image-model   Image generation model override
    --server URL    Override GEN_VIDEO_SERVER_URL for this call
"""

import os
import sys
import time

import requests


def main():
    try:
        from ww.env import load_env as _le
        _le()
    except ImportError:
        pass

    # ── Parse args ──────────────────────────────────────────────────────
    args = list(sys.argv[1:])

    output_path = None
    model = None
    image_model = None
    server_url = None

    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif args[i] == "--image-model" and i + 1 < len(args):
            image_model = args[i + 1]
            i += 2
        elif args[i] == "--server" and i + 1 < len(args):
            server_url = args[i + 1]
            i += 2
        elif args[i] in ("--help", "-h"):
            print(__doc__)
            return
        else:
            print(f"Unknown option: {args[i]}")
            print(__doc__)
            sys.exit(1)

    # ── Get server URL ──────────────────────────────────────────────────
    if server_url is None:
        server_url = os.getenv("GEN_VIDEO_SERVER_URL", "")
    if not server_url:
        print(
            "Error: GEN_VIDEO_SERVER_URL not set. "
            "Set it in .env or pass --server URL."
        )
        sys.exit(1)

    # Strip trailing slash and append the API path
    api_url = server_url.rstrip("/")
    if not api_url.endswith("/api/generate-video"):
        api_url += "/api/generate-video"

    # ── Read pasteboard ─────────────────────────────────────────────────
    try:
        import pyperclip
        content = pyperclip.paste()
    except Exception:
        # Fallback: try pbpaste on macOS
        import subprocess
        try:
            result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
            content = result.stdout
        except Exception:
            print("Error: Could not read from pasteboard. Is pyperclip or pbpaste available?")
            sys.exit(1)

    if not content or not content.strip():
        print("Error: Pasteboard is empty.")
        sys.exit(1)

    print(f"Read {len(content)} chars from pasteboard.")

    # ── Determine output path ───────────────────────────────────────────
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f"gen_video_{timestamp}.mp4"

    # ── Build request ───────────────────────────────────────────────────
    payload = {"content": content}
    if model:
        payload["model"] = model
    if image_model:
        payload["image_model"] = image_model

    print(f"Sending to {api_url} ...")
    print(f"  Model: {model or 'default'}")
    print(f"  Image model: {image_model or 'default'}")
    print()

    try:
        resp = requests.post(
            api_url,
            json=payload,
            timeout=(10, 600),  # 10s connect, 600s read (video generation takes time)
            stream=True,
        )
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {api_url}")
        print("  Is the gen-video server running? Try: ww gen-video server")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Error: Request timed out connecting to server.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text[:500])
        except Exception:
            detail = resp.text[:500]
        print(f"Error: Server returned HTTP {resp.status_code}")
        print(f"  {detail}")
        sys.exit(1)

    # ── Save the response as a video file ───────────────────────────────
    content_type = resp.headers.get("content-type", "")
    if "video" not in content_type and "octet-stream" not in content_type:
        print(f"Warning: Unexpected content type: {content_type}")

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    size = os.path.getsize(output_path)
    print(f"\n✓ Video saved: {output_path}")
    print(f"  Size: {size / 1024 / 1024:.1f} MB")
