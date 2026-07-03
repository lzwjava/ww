"""ww qwen vl — vision-language inference via local Qwen2-VL server."""

import argparse
import base64
import json
import os
import sys
import urllib.request


def main():
    parser = argparse.ArgumentParser(
        prog="ww qwen vl", description="Query local Qwen2-VL vision model"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Describe this image in detail.",
        help="Text prompt for the image",
    )
    parser.add_argument(
        "--image",
        "-i",
        default=None,
        help="Path to image file (default: clipboard if on macOS, else required)",
    )
    parser.add_argument(
        "--server", default=None, help="Server URL (default: http://192.168.1.36:8088)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=500, help="Max tokens (default: 500)"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.3, help="Temperature (default: 0.3)"
    )

    args = parser.parse_args()

    server = args.server or os.getenv("QWEN_VL_SERVER", "http://192.168.1.36:8088")

    # Resolve image path
    image_path = args.image
    if not image_path:
        # Try macOS clipboard for image data
        try:
            import subprocess

            result = subprocess.run(
                ["osascript", "-e", "get the clipboard as «class PNGf»"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Have clipboard image data (Mac)
                raw_hex = result.stdout.strip()
                image_bytes = bytes.fromhex(raw_hex.replace(" ", ""))
                b64 = base64.b64encode(image_bytes).decode()
                print(
                    f"[info] Using image from clipboard ({len(image_bytes)} bytes)",
                    file=sys.stderr,
                )
            else:
                print(
                    "Error: no image provided and clipboard has no image",
                    file=sys.stderr,
                )
                sys.exit(1)
        except Exception:
            print(
                "Error: --image is required (or use on macOS for clipboard)",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        if not os.path.exists(image_path):
            print(f"Error: image not found: {image_path}", file=sys.stderr)
            sys.exit(1)
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

    payload = {
        "model": "qwen2-vl",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                    {"type": "text", "text": args.prompt},
                ],
            }
        ],
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
    }

    url = f"{server.rstrip('/')}/v1/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )

    try:
        resp = urllib.request.urlopen(req, timeout=300)
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        print(content)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"Server error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection failed: {e.reason}", file=sys.stderr)
        print(f"  Is the server running at {server}?", file=sys.stderr)
        sys.exit(1)
