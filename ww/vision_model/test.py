#!/usr/bin/env python3
"""ww vision-model test — Test whether the configured VISION_MODEL supports image inputs via OpenRouter.

Sends a small test image (a 1x1 blue pixel, generated on the fly) with a
text prompt and reports whether the model responds successfully.
"""

import base64
import io
import os
import sys
import time

import requests
from PIL import Image


DEFAULT_VISION_MODEL = "google/gemini-2.5-flash-image"


def _check_proxy():
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        val = os.environ.get(var, "")
        if val:
            try:
                from urllib.parse import urlparse

                parsed = urlparse(val)
                host = parsed.hostname
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
                import socket

                sock = socket.create_connection((host, port), timeout=3)
                sock.close()
                return f"{var}={val} (port {port} reachable)"
            except Exception as e:
                return f"{var}={val} (UNREACHABLE: {e})"
    return "No proxy configured"


def _generate_test_image():
    """Generate a tiny blue test image as base64 JPG."""
    img = Image.new("RGB", (64, 64), (30, 80, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/jpeg"


def _test_vision_model(model, max_tokens=1024, timeout=30):
    """Send a test request to the vision model via OpenRouter.

    Returns (success: bool, response_text: str, elapsed: float).
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise Exception("OPENROUTER_API_KEY environment variable is not set")

    b64, mime = _generate_test_image()

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in one sentence."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                },
            ],
        }
    ]

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {"model": model, "messages": messages, "max_tokens": max_tokens}

    t0 = time.perf_counter()
    resp = requests.post(url, headers=headers, json=data, timeout=timeout)
    elapsed = time.perf_counter() - t0

    if not resp.ok:
        return False, f"HTTP {resp.status_code}: {resp.text[:1000]}", elapsed

    body = resp.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content") or ""
    finish_reason = body.get("choices", [{}])[0].get("finish_reason")

    if not content:
        return (
            False,
            f"Empty response (finish_reason={finish_reason})",
            elapsed,
        )

    return True, content, elapsed


def main():
    try:
        from ww.env import load_env as _le

        _le()
    except ImportError:
        pass

    # main.py already popped "test" from sys.argv[1]
    args = list(sys.argv[1:])

    if "--help" in args or "-h" in args:
        print(
            "Usage: ww vision-model test [--model MODEL] [--image PATH] [--max-tokens N]"
        )
        print()
        print(
            "Test whether the configured VISION_MODEL supports image inputs via OpenRouter."
        )
        print()
        print("Options:")
        print(
            "  --model MODEL        Vision model slug (default: $VISION_MODEL or google/gemini-2.5-flash-image)"
        )
        print(
            "  --image PATH         Optional: send a real image file instead of the auto-generated test image"
        )
        print("  --max-tokens N       Max output tokens (default: 1024)")
        print()
        print("Examples:")
        print("  ww vision-model test")
        print("  ww vision-model test --model openai/gpt-4o-mini")
        print("  ww vision-model test --image ~/photo.jpg")
        print("  ww vision-model test --max-tokens 4096")
        return

    # Parse args
    model = None
    image_path = None
    max_tokens = 1024
    for i, arg in enumerate(args):
        if arg == "--model" and i + 1 < len(args):
            model = args[i + 1]
        elif arg == "--image" and i + 1 < len(args):
            image_path = args[i + 1]
        elif arg == "--max-tokens" and i + 1 < len(args):
            try:
                max_tokens = int(args[i + 1])
            except ValueError:
                print(f"Error: invalid --max-tokens value: {args[i + 1]}")
                sys.exit(1)

    if model is None:
        model = os.environ.get("VISION_MODEL", "").strip() or DEFAULT_VISION_MODEL

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        print("Run 'ww env update' to set it, or export it manually.")
        sys.exit(1)

    print("Vision Model Test")
    print(f"  Model: {model}")
    print(f"  Max tokens: {max_tokens}")
    print(f"  Proxy: {_check_proxy()}")
    print()

    if image_path:
        image_path = os.path.expanduser(image_path)
        if not os.path.isfile(image_path):
            print(f"Error: image file not found: {image_path}")
            sys.exit(1)
        print(f"  Using real image: {image_path}")
    else:
        print("  Using auto-generated test image (64x64 blue square)")
    print()

    print("Sending test request (image + text prompt)...")
    try:
        success, response_text, elapsed = _test_vision_model(
            model, max_tokens=max_tokens, timeout=30
        )
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    print()
    print(f"  Response time: {elapsed:.3f}s")
    print()

    if success:
        print("  Status: VISION MODEL IS WORKING")
        print()
        print(f"  Response: {response_text}")
    else:
        print("  Status: VISION MODEL TEST FAILED")
        print()
        print(f"  Error: {response_text}")
        print()
        print("  Tips:")
        print("    - Ensure VISION_MODEL supports image inputs")
        print("    - Try a different model like google/gemini-2.5-flash-image")
        print(
            "    - Use --skip-analysis with screenshot commands if vision is not needed"
        )
        sys.exit(1)
