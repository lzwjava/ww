"""OpenRouter Management API client.

Uses OPENROUTER_MANAGEMENT_API_KEY to query account info, credits, models, activity.
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta

import requests

BASE_URL = "https://openrouter.ai/api/v1"


def _get_mgmt_key():
    key = os.getenv("OPENROUTER_MANAGEMENT_API_KEY")
    if not key:
        raise Exception("OPENROUTER_MANAGEMENT_API_KEY not set")
    return key


def _get(key_path=None):
    """GET with management key auth. Returns parsed JSON."""
    headers = {"Authorization": f"Bearer {_get_mgmt_key()}"}
    url = f"{BASE_URL}/{key_path}" if key_path else BASE_URL
    resp = requests.get(url, headers=headers, timeout=15)
    if not resp.ok:
        raise Exception(f"OpenRouter API error: {resp.status_code} {resp.text[:500]}")
    return resp.json()


def get_key_info():
    """Return key metadata: usage, limits, rate limits."""
    return _get("auth/key").get("data", {})


def get_credits():
    """Return credits balance: total_credits, total_usage."""
    return _get("credits").get("data", {})


def get_models():
    """Return list of available models."""
    return _get("models").get("data", [])


def get_activity():
    """Return activity entries (all time)."""
    return _get("activity").get("data", [])


def _fmt_tokens(n):
    """Format token count with K/M suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def cmd_activity(days=7):
    """Show activity for the past N days, aggregated by model."""
    entries = get_activity()

    cutoff = datetime.now() - timedelta(days=days)
    filtered = []
    for e in entries:
        try:
            dt = datetime.strptime(e["date"], "%Y-%m-%d %H:%M:%S")
        except (ValueError, KeyError):
            continue
        if dt >= cutoff:
            filtered.append(e)

    if not filtered:
        print(f"No activity in the past {days} days.")
        return

    # Aggregate by model
    by_model = defaultdict(
        lambda: {
            "usage": 0.0,
            "byok_usage": 0.0,
            "requests": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "reasoning_tokens": 0,
        }
    )
    # Also track daily totals
    by_day = defaultdict(lambda: {"usage": 0.0, "requests": 0, "tokens": 0})

    for e in filtered:
        model = e.get("model", "unknown")
        m = by_model[model]
        m["usage"] += e.get("usage", 0)
        m["byok_usage"] += e.get("byok_usage_inference", 0)
        m["requests"] += e.get("requests", 0)
        m["prompt_tokens"] += e.get("prompt_tokens", 0)
        m["completion_tokens"] += e.get("completion_tokens", 0)
        m["reasoning_tokens"] += e.get("reasoning_tokens", 0)

        day_str = e["date"][:10]
        d = by_day[day_str]
        d["usage"] += e.get("usage", 0) + e.get("byok_usage_inference", 0)
        d["requests"] += e.get("requests", 0)
        d["tokens"] += e.get("prompt_tokens", 0) + e.get("completion_tokens", 0)

    # Print daily summary
    total_spend = sum(d["usage"] for d in by_day.values())
    total_reqs = sum(d["requests"] for d in by_day.values())
    total_tok = sum(d["tokens"] for d in by_day.values())

    print(f"OpenRouter Activity - Past {days} Days")
    print("=" * 58)
    print()
    print("  Daily Summary")
    print("  " + "-" * 54)
    for day in sorted(by_day.keys()):
        d = by_day[day]
        print(
            f"  {day}   ${d['usage']:>8.4f}   "
            f"{d['requests']:>5} reqs   "
            f"{_fmt_tokens(d['tokens']):>8} tokens"
        )
    print("  " + "-" * 54)
    print(
        f"  {'TOTAL':<10}  ${total_spend:>8.4f}   "
        f"{total_reqs:>5} reqs   "
        f"{_fmt_tokens(total_tok):>8} tokens"
    )

    # Print per-model breakdown
    print()
    print("  By Model")
    print("  " + "-" * 54)

    # Sort by spend descending
    sorted_models = sorted(by_model.items(), key=lambda x: x[1]["usage"], reverse=True)
    for model, m in sorted_models:
        total_model_tokens = m["prompt_tokens"] + m["completion_tokens"]
        spend = m["usage"] + m["byok_usage"]
        print(f"  {model}")
        print(
            f"    ${spend:.4f}   "
            f"{m['requests']} reqs   "
            f"{_fmt_tokens(m['prompt_tokens'])} prompt + "
            f"{_fmt_tokens(m['completion_tokens'])} completion"
        )
        if m["reasoning_tokens"] > 0:
            print(f"    reasoning: {_fmt_tokens(m['reasoning_tokens'])} tokens")


def cmd_info():
    key_data = get_key_info()
    credits = get_credits()

    total = credits.get("total_credits", 0)
    used = credits.get("total_usage", 0)
    remaining = total - used

    print("OpenRouter Account")
    print("=" * 40)
    print(f"  Credits total:     ${total:.2f}")
    print(f"  Credits used:      ${used:.2f}")
    print(f"  Credits remaining: ${remaining:.2f}")
    print()
    print(f"  Usage (all time):  ${key_data.get('usage', 0):.4f}")
    print(f"  Usage (daily):     ${key_data.get('usage_daily', 0):.4f}")
    print(f"  Usage (weekly):    ${key_data.get('usage_weekly', 0):.4f}")
    print(f"  Usage (monthly):   ${key_data.get('usage_monthly', 0):.4f}")
    print()
    print(f"  Free tier:         {key_data.get('is_free_tier', False)}")
    print(f"  Management key:    {key_data.get('is_management_key', False)}")
    limit = key_data.get("limit")
    if limit:
        print(f"  Limit:             ${limit}")
        print(f"  Limit remaining:   ${key_data.get('limit_remaining')}")
    else:
        print("  Limit:             None")


def cmd_credits():
    credits = get_credits()
    total = credits.get("total_credits", 0)
    used = credits.get("total_usage", 0)
    print(f"Total: ${total:.2f}  Used: ${used:.2f}  Remaining: ${total - used:.2f}")


def cmd_models(as_json=False):
    models = get_models()
    if as_json:
        import json

        print(json.dumps(models, indent=2))
    else:
        print(f"Available models: {len(models)}")
        print()
        for m in models:
            mid = m.get("id", "?")
            pricing = m.get("pricing", {})
            prompt_price = pricing.get("prompt", "0")
            completion_price = pricing.get("completion", "0")
            print(f"  {mid}")
            print(
                f"    prompt: ${prompt_price}/tok  completion: ${completion_price}/tok"
            )
    print()
    print(f"Total: {len(models)} models")


def main():
    import sys

    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww openrouter <command>")
        print()
        print("Commands:")
        print("  info      Account summary: credits, usage, key details")
        print("  credits   Show credits balance")
        print("  activity  Show past week spend, requests, tokens (--days N)")
        print("  models    List available models (--json for raw)")
        return

    subcmd = args[0]

    if subcmd == "info":
        cmd_info()
    elif subcmd == "credits":
        cmd_credits()
    elif subcmd == "activity":
        days = 7
        for i, a in enumerate(args):
            if a == "--days" and i + 1 < len(args):
                days = int(args[i + 1])
        cmd_activity(days=days)
    elif subcmd == "models":
        cmd_models(as_json="--json" in args)
    else:
        print(f"Unknown openrouter command: {subcmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
