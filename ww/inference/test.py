#!/usr/bin/env python3
"""ww inference test — Detect whether an OpenRouter model endpoint is SGLang or vLLM.

Sends a streaming chat completion request and inspects:
  - id field format (chatcmpl- prefix → vLLM; bare hex → SGLang)
  - delta fields for reasoning_content vs reasoning
  - Server header
  - TTFT / latency comparison on second request (prefix cache check)
"""

import json
import os
import sys
import time

import requests


def _detect_backend_from_id(chunk):
    """Examine the id field of the first response chunk."""
    cid = chunk.get("id", "") or ""
    if cid.startswith("chatcmpl-"):
        return "vLLM"
    # SGLang often uses a bare 32-char hex string (no prefix)
    if len(cid) == 32 and all(c in "0123456789abcdef" for c in cid):
        return "SGLang"
    return f"unknown (id={cid!r})"


def _detect_backend_from_delta(delta):
    """Examine delta fields for reasoning markers."""
    keys = list(delta.keys())
    if "reasoning_content" in keys:
        return "vLLM (reasoning_content delta field)"
    if "reasoning" in keys:
        return "SGLang (reasoning delta field — deep thinking models)"
    return f"unknown (delta keys: {keys})"


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


def _ttft_stream(model, messages, max_tokens=64):
    """Measure Time-To-First-Token via streaming. Returns (ttft_seconds, first_delta, response_id, full_text)."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise Exception("OPENROUTER_API_KEY not set")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    data = {
        "model": model,
        "messages": messages,
        "stream": True,
        "max_tokens": max_tokens,
    }

    t0 = time.perf_counter()
    resp = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
    if not resp.ok:
        raise Exception(f"HTTP {resp.status_code}: {resp.text[:500]}")

    first_delta = None
    first_id = None
    total_text = ""

    for raw in resp.iter_lines():
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace")
        if not line.startswith("data: "):
            continue
        payload = line[len("data: ") :].strip()
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue

        choices = chunk.get("choices") or []
        if choices:
            delta = choices[0].get("delta") or {}
            content = delta.get("content") or ""
            if content:
                if first_delta is None:
                    first_delta = delta
                total_text += content

        if first_id is None:
            first_id = chunk.get("id")

    elapsed = time.perf_counter() - t0
    return elapsed, first_delta, first_id, total_text


def main():
    load_env = None
    try:
        from ww.env import load_env as _le

        load_env = _le
    except ImportError:
        pass

    # main.py already popped "test" from sys.argv[1] before calling us
    args = list(sys.argv[1:])

    if "--help" in args or "-h" in args:
        print("Usage: ww inference test [--model MODEL] [--no-prefix-cache]")
        print()
        print("Send a request to an OpenRouter model and detect whether the backend")
        print("is SGLang or vLLM by inspecting the streaming response format.")
        print()
        print("Options:")
        print("  --model MODEL       Model slug (default: tencent/hy3-preview)")
        print("  --no-prefix-cache   Skip the prefix-cache TTFT comparison")
        print()
        print("Examples:")
        print("  ww inference test")
        print("  ww inference test --model openai/gpt-4o-mini")
        return

    if load_env:
        load_env()

    # Parse args
    model = "tencent/hy3-preview"
    do_prefix_test = True
    for i, arg in enumerate(args):
        if arg == "--model" and i + 1 < len(args):
            model = args[i + 1]
        elif arg == "--no-prefix-cache":
            do_prefix_test = False

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        print("Run 'ww env update' to set it, or export it manually.")
        sys.exit(1)

    print("Backend Detection Test")
    print(f"  Model: {model}")
    print(f"  Proxy: {_check_proxy()}")
    print()

    # --- Request 1: simple query ---
    print("[1/3] Sending streaming request to detect backend...")
    try:
        ttft_1, first_delta, response_id, full_text = _ttft_stream(
            model, [{"role": "user", "content": "Say hello in one sentence."}]
        )
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    id_detect = _detect_backend_from_id({"id": response_id})
    delta_detect = _detect_backend_from_delta(first_delta or {})

    print()
    print(f"  Response id:  {response_id}")
    print(f"  id detection: {id_detect}")
    print(f"  delta keys:   {list((first_delta or {}).keys())}")
    print(f"  delta detect: {delta_detect}")
    print(f"  TTFT:         {ttft_1:.3f}s")
    print(f"  Total time:   {ttft_1:.3f}s")
    print(f"  Full text:    {full_text[:120]!r}{'...' if len(full_text) > 120 else ''}")
    print()

    # --- Detect server header ---
    print("[2/3] Checking server header...")
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 1,
            },
            timeout=15,
        )
        server = resp.headers.get("Server", "not reported")
        power = resp.headers.get("X-Powered-By", "not reported")
        print(f"  Server:        {server}")
        print(f"  X-Powered-By:  {power}")
    except Exception as e:
        print(f"  Error: {e}")
        server = "error"
    print()

    # --- Prefix cache test ---
    if do_prefix_test:
        print("[3/3] Prefix cache test (two requests with shared prefix)...")
        SHARED_PREFIX = (
            "You are a senior Python engineer. Answer strictly as requested.\n\n" * 200
        )
        suffix_a = "Question A: print 1 to 10."
        suffix_b = "Question B: print the first 10 Fibonacci numbers."

        print(
            f"  Shared prefix: {len(SHARED_PREFIX)} chars, ~{len(SHARED_PREFIX.split())} tokens"
        )
        print()

        print("  Request A (cold)...", end=" ", flush=True)
        try:
            ttft_a, _, _, _ = _ttft_stream(
                model,
                [{"role": "user", "content": SHARED_PREFIX + suffix_a}],
                max_tokens=32,
            )
            print(f"TTFT={ttft_a:.3f}s, total={ttft_a:.3f}s")
        except Exception as e:
            print(f"Error: {e}")
            ttft_a = 0

        print("  Request B (same prefix, different suffix)...", end=" ", flush=True)
        try:
            ttft_b, _, _, _ = _ttft_stream(
                model,
                [{"role": "user", "content": SHARED_PREFIX + suffix_b}],
                max_tokens=32,
            )
            print(f"TTFT={ttft_b:.3f}s, total={ttft_b:.3f}s")
        except Exception as e:
            print(f"Error: {e}")
            ttft_b = 0

        if ttft_a > 0 and ttft_b > 0:
            ratio = ttft_b / ttft_a
            if ratio < 0.7:
                print(f"  -> Likely cache HIT (TTFT dropped to {ratio:.1%} of cold)")
            elif ratio < 1.0:
                print(f"  -> Possible partial cache hit (TTFT {ratio:.1%} of cold)")
            else:
                print(
                    f"  -> Likely cache MISS (TTFT {ratio:.1%} of cold — no improvement)"
                )

    print()
    print("Summary:")
    print(f"  Backend:       {id_detect} / {delta_detect}")
    print(f"  Server:        {server}")
    print(f"  TTFT (cold):   {ttft_1:.3f}s")
