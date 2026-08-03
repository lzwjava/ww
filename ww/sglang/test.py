#!/usr/bin/env python3
"""ww sglang test — Exercise a local SGLang server with different input lengths.

Sends streaming chat completion requests to a running SGLang server (OpenAI
compatible API) and reports, for each input size:
  - TTFT (time to first token)
  - Total latency
  - Output tokens and throughput (tok/s)
  - Finish reason and a snippet of the generated text

Typical use (server on the default port 30010):
    ww sglang test
    ww sglang test --port 30011 --max-tokens 256
    ww sglang test --url http://my-host:30010
"""

import argparse
import json
import sys
import time

import requests


# (name, target_char_count, instruction)
# Instruction is appended after filler paragraphs so the model has a real task.
PROFILES = [
    ("tiny", 30, "Say hi."),
    ("short", 300, "In one sentence, what did the text above talk about?"),
    ("medium", 1500, "Summarize the text above in two sentences."),
    ("long", 6000, "List the three most important points from the text above."),
    ("huge", 24000, "Give a one-line summary of the text above."),
]

# Deterministic filler paragraphs (varied so prompt processing is real work).
_FILLER = [
    "The quick brown fox jumps over the lazy dog while the moon watches silently. "
    "Rivers carry stories from mountain springs to the open sea, and every drop "
    "remembers the path it traveled. Mathematics is the poetry of logic, weaving "
    "patterns out of pure thought.",
    "In the garden of ideas, curiosity is the gardener and patience the soil. "
    "Old libraries smell of paper and possibility, each spine a door to another "
    "mind. Weather systems dance across the planet, driven by the sun's patient hand.",
    "A well-tuned system hums like a satisfied machine, every component knowing "
    "its role. Data flows through networks the way water finds cracks in stone, "
    "always seeking the path of least resistance. History is written by those "
    "who remember, and rewritten by those who question.",
]


def _build_prompt(target_chars, instruction):
    """Build a prompt of roughly target_chars characters + instruction."""
    parts = []
    total = 0
    while total < target_chars:
        for para in _FILLER:
            parts.append(para)
            total += len(para) + 2
            if total >= target_chars:
                break
    body = " ".join(parts)
    # Trim to target length at a word boundary.
    if len(body) > target_chars:
        body = body[:target_chars].rsplit(" ", 1)[0]
    return f"{body}\n\nTask: {instruction}"


def _stream_chat(base_url, model, messages, max_tokens, timeout=300):
    """Stream a chat completion.

    Returns (ttft_s, total_s, output_text, usage, finish_reason).
    usage is the dict from the trailing usage chunk if present, else {}.
    """
    url = f"{base_url}/v1/chat/completions"
    data = {
        "model": model,
        "messages": messages,
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    t0 = time.perf_counter()
    resp = requests.post(
        url,
        json=data,
        stream=True,
        timeout=timeout,
        headers={"Accept": "text/event-stream"},
    )
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:400]}")

    first_token_at = None
    output = []
    usage = {}
    finish_reason = None

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

        if chunk.get("usage"):
            usage = chunk["usage"]

        choices = chunk.get("choices") or []
        if choices:
            delta = choices[0].get("delta") or {}
            content = delta.get("content") or ""
            if content:
                if first_token_at is None:
                    first_token_at = time.perf_counter() - t0
                output.append(content)
            if choices[0].get("finish_reason"):
                finish_reason = choices[0]["finish_reason"]

    total_s = time.perf_counter() - t0
    ttft_s = first_token_at if first_token_at is not None else total_s
    return ttft_s, total_s, "".join(output), usage, finish_reason


def _count_tokens(base_url, model, text):
    """Exact token count via SGLang's /v1/tokenize extension. Returns count or None."""
    try:
        r = requests.post(
            f"{base_url}/v1/tokenize",
            json={"model": model, "prompt": text},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("count")
    except Exception:
        return None


def _fmt_tok(n):
    return f"{n:,}"


def main():
    parser = argparse.ArgumentParser(
        prog="ww sglang test",
        description="Test a local SGLang server with different input lengths.",
    )
    parser.add_argument(
        "--url", default="http://localhost:30010", help="Server base URL"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Shorthand for --url http://localhost:PORT",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=128, help="Max output tokens per request"
    )
    parser.add_argument(
        "--model", default=None, help="Model id (default: first model from /v1/models)"
    )
    parser.add_argument(
        "--no-stream", action="store_true", help="Use non-streaming requests (no TTFT)"
    )
    parser.add_argument(
        "--timeout", type=float, default=300, help="Per-request timeout in seconds"
    )
    args = parser.parse_args()

    if args.port:
        args.url = f"http://localhost:{args.port}"

    # --- Server info ---
    try:
        r = requests.get(f"{args.url}/v1/models", timeout=10)
        r.raise_for_status()
        models = [m["id"] for m in r.json().get("data", [])]
    except Exception as e:
        print(f"Error: cannot reach SGLang server at {args.url}: {e}")
        sys.exit(1)

    model = args.model or (models[0] if models else None)
    if not model:
        print("Error: no model id advertised by server; pass --model")
        sys.exit(1)

    print("SGLang Test")
    print(f"  URL:      {args.url}")
    print(f"  Model:    {model}")
    print(
        f"  Max ctx:  {_fmt_tok(r.json().get('data', [{}])[0].get('max_model_len', '?') if r.json().get('data') else '?')} tokens (advertised)"
    )
    print(f"  Max out:  {args.max_tokens} tokens per request")
    print()

    # --- Probe non-streaming once for sanity ---
    try:
        t0 = time.perf_counter()
        probe = requests.post(
            f"{args.url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with OK."}],
                "max_tokens": 8,
            },
            timeout=30,
        )
        probe.raise_for_status()
        probe_s = time.perf_counter() - t0
        probe_usage = probe.json().get("usage", {})
        print(
            f"Probe (non-stream): {probe_s * 1000:.0f}ms, "
            f"{probe_usage.get('prompt_tokens', '?')} in / {probe_usage.get('completion_tokens', '?')} out "
            f"-> {probe.json()['choices'][0]['message']['content'].strip()!r}"
        )
    except Exception as e:
        print(f"Error: probe request failed: {e}")
        sys.exit(1)
    print()

    # --- Length sweep ---
    print(
        f"{'case':<8}{'input':>12}{'TTFT':>9}{'total':>9}{'out':>7}{'tok/s':>9}  finish  response"
    )
    print("-" * 92)

    results = []
    for name, chars, instruction in PROFILES:
        prompt = _build_prompt(chars, instruction)
        prompt_tokens = _count_tokens(args.url, model, prompt)
        prompt_tokens_est = prompt_tokens or max(1, len(prompt) // 4)

        try:
            if args.no_stream:
                t0 = time.perf_counter()
                resp = requests.post(
                    f"{args.url}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": args.max_tokens,
                    },
                    timeout=args.timeout,
                )
                resp.raise_for_status()
                body = resp.json()
                elapsed = time.perf_counter() - t0
                ttft = elapsed  # no TTFT available without streaming
                text = body["choices"][0]["message"]["content"] or ""
                usage = body.get("usage", {})
                finish = body["choices"][0].get("finish_reason")
                out_tokens = usage.get("completion_tokens", 0)
                if not out_tokens:
                    out_tokens = _count_tokens(args.url, model, text) or 0
            else:
                ttft, elapsed, text, usage, finish = _stream_chat(
                    args.url,
                    model,
                    [{"role": "user", "content": prompt}],
                    args.max_tokens,
                    args.timeout,
                )
                out_tokens = usage.get("completion_tokens", 0)
                # Streaming chunks may omit usage; tokenize the output for an exact count.
                if not out_tokens and text:
                    out_tokens = _count_tokens(args.url, model, text) or 0
            tok_s = out_tokens / elapsed if elapsed > 0 else 0
            snippet = " ".join(text.split())[:48] if text else "(empty!)"
            print(
                f"{name:<8}{prompt_tokens:>10,}t{ttft * 1000:>8.0f}ms{elapsed * 1000:>8.0f}ms"
                f"{out_tokens:>6,}{tok_s:>9.1f}  {str(finish):<8}  {snippet!r}"
            )
            results.append(
                {
                    "name": name,
                    "prompt_tokens": prompt_tokens,
                    "ttft": ttft,
                    "total": elapsed,
                    "out_tokens": out_tokens,
                    "finish": finish,
                    "text": text,
                }
            )
        except Exception as e:
            print(f"{name:<8}{prompt_tokens_est:>10,}t   ERROR: {e}")
            results.append({"name": name, "error": str(e)})

    print("-" * 92)
    print()

    # --- Checks & summary ---
    print("Checks:")
    ok = True
    for res in results:
        if "error" in res:
            print(f"  [FAIL] {res['name']:<8} request error: {res['error']}")
            ok = False
            continue
        text = res.get("text", "")
        if not text:
            print(f"  [FAIL] {res['name']:<8} empty response")
            ok = False
        elif res["out_tokens"] == 0:
            print(f"  [WARN] {res['name']:<8} 0 output tokens reported")
        else:
            print(
                f"  [ OK ] {res['name']:<8} {res['prompt_tokens']:,} in -> {res['out_tokens']:,} out, "
                f"finish={res['finish']}"
            )

    valid = [r for r in results if "error" not in r and r.get("out_tokens", 0) > 0]
    if valid:
        max_ttft = max(valid, key=lambda r: r["ttft"])
        print()
        print(
            f"Worst TTFT:   {max_ttft['name']} ({max_ttft['prompt_tokens']:,} input tokens) = "
            f"{max_ttft['ttft'] * 1000:.0f}ms"
        )

    print()
    if ok:
        print("Summary: all input lengths responded successfully.")
    else:
        print("Summary: some tests failed (see above).")
        sys.exit(1)


if __name__ == "__main__":
    main()
