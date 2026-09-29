"""
Monitor HuggingFace trending models and alert on changes.

Usage:
  ww monitor huggingface            Check now, show current trending, compare with cache
  ww monitor huggingface --now      Force alert even if no change
  ww monitor huggingface --hours 1  Look back N hours (default: check current top 10)

# ───────────────────────────────────────────────────────
# Cron job config (run every 10 minutes):
#   * * * * * cd /Users/lzwjava/projects/ww && uv run ww monitor huggingface >> /tmp/ww-monitor-hf.log 2>&1
# ───────────────────────────────────────────────────────
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
HF_API_MODELS = "https://huggingface.co/api/models"
CACHE_DIR = Path.home() / ".ww" / "monitor"
CACHE_FILE = CACHE_DIR / "hf_trending.json"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get(
    "TELEGRAM_HABIT_BOT_API_KEY"
)
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_MAX_LENGTH = 4096


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _fetch_top_trending(limit=10):
    """Fetch top N trending models from HuggingFace API."""
    params = {"sort": "trendingScore", "direction": "-1", "limit": limit}
    resp = requests.get(HF_API_MODELS, params=params, timeout=20)
    if not resp.ok:
        print(f"  HF API error: {resp.status_code} {resp.text[:300]}")
        return []
    return resp.json()


def _model_key(item):
    """Return a stable unique key for a model."""
    return item.get("id", "?")


def _model_summary(item):
    """Format a model entry for display and alert."""
    model_id = item.get("id", "?")
    score = item.get("trendingScore", 0)
    likes = item.get("likes", 0)
    downloads = item.get("downloads", 0)
    pipeline = item.get("pipeline_tag", "")
    created = (item.get("createdAt") or "")[:10]
    return {
        "id": model_id,
        "score": score,
        "likes": likes,
        "downloads": downloads,
        "pipeline": pipeline,
        "created": created,
    }


def _load_cache():
    """Load the cached trending models snapshot."""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _save_cache(models):
    """Save a snapshot of trending models."""
    _ensure_cache_dir()
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models": [_model_summary(m) for m in models],
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(snapshot, f, indent=2)
    return snapshot


def _send_telegram(message):
    """Send a message via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  [Telegram] Skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # Strip markdown asterisks for safe delivery
    safe_msg = message.replace("*", "")
    # Split if exceeds length limit
    parts = []
    msg = safe_msg
    while len(msg) > TELEGRAM_MAX_LENGTH:
        split_idx = msg.rfind("\n", 0, TELEGRAM_MAX_LENGTH)
        if split_idx == -1 or split_idx < TELEGRAM_MAX_LENGTH // 2:
            split_idx = TELEGRAM_MAX_LENGTH
        parts.append(msg[:split_idx])
        msg = msg[split_idx:]
    parts.append(msg)

    success = True
    for part in parts:
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": part, "parse_mode": "Markdown"}
        try:
            resp = requests.post(url, params=params, timeout=10)
            resp.raise_for_status()
            print(f"  [Telegram] Sent ({len(part)} chars)")
        except requests.exceptions.RequestException as e:
            print(f"  [Telegram] Error: {e}")
            success = False
    return success


def _fmt_downloads(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def cmd_monitor(force_alert=False, lookback_hours=0):
    """
    Fetch top 10 trending HF models, compare with last cached snapshot,
    and send Telegram alert if the top 10 changed.
    """
    print("  [HF Monitor] Fetching top 10 trending models...")
    print(f"  Time: {datetime.now(timezone.utc).isoformat()}")
    print()

    current = _fetch_top_trending(limit=10)
    if not current:
        print("  [HF Monitor] No models returned from API.")
        return

    current_ids = [_model_key(m) for m in current]

    # Display current trending
    print(f"  {'=' * 60}")
    print("  Current Top 10 Trending Models")
    print(f"  {'=' * 60}")
    for i, item in enumerate(current, 1):
        summary = _model_summary(item)
        downloads = _fmt_downloads(summary["downloads"])
        pipeline = summary["pipeline"]
        tag = f"[{pipeline}] " if pipeline else ""
        print(f"  {i:>2}. {summary['id']}")
        print(
            f"       Score: {summary['score']}  Likes: {summary['likes']}  {tag}{downloads} dl"
        )
    print()

    # Compare with cache
    cached = _load_cache()
    changed = False
    changes = []

    if cached is None:
        print("  [HF Monitor] No cached snapshot found. Saving current as baseline.")
        changed = True
        changes.append("Initial baseline recorded.")
    else:
        cached_ids = [m["id"] for m in cached.get("models", [])]
        cached_time = cached.get("timestamp", "?")
        print(f"  Last snapshot: {cached_time}")
        print()

        if current_ids != cached_ids:
            changed = True
            old_set = set(cached_ids)
            new_set = set(current_ids)
            entered = new_set - old_set
            dropped = old_set - new_set

            if entered:
                changes.append(f"New entries: {', '.join(sorted(entered))}")
            if dropped:
                changes.append(f"Dropped: {', '.join(sorted(dropped))}")

            # Show positional changes
            for pos, model_id in enumerate(current_ids, 1):
                old_pos = (
                    (cached_ids.index(model_id) + 1) if model_id in cached_ids else None
                )
                if old_pos and old_pos != pos:
                    changes.append(f"  {model_id}: #{old_pos} → #{pos}")

    # Save new snapshot
    snapshot = _save_cache(current)

    if force_alert or changed:
        if not changed:
            print("  [HF Monitor] Top 10 unchanged. --now: forcing alert anyway.")
            print()

        # Build Telegram message
        lines = [
            "🤗 *HF Trending Monitor*",
            f"Checked: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        ]
        if changes:
            lines.append("")
            lines.append("*Changes:*")
            for c in changes:
                lines.append(f"  • {c}")
        else:
            lines.append("  Top 10 trending models unchanged")

        lines.append("")
        lines.append("*Current Top 10:*")
        for i, item in enumerate(current, 1):
            summary = _model_summary(item)
            downloads = _fmt_downloads(summary["downloads"])
            lines.append(f"  {i}. {summary['id']} ({summary['score']:.0f})")
        lines.append("")
        lines.append("https://huggingface.co/models?sort=trending")

        message = "\n".join(lines)
        print("  [HF Monitor] Sending Telegram alert...")
        _send_telegram(message)
    else:
        print("  [HF Monitor] Top 10 unchanged. No alert sent.")
        print("  Use --now to force a notification anyway.")

    print()
    print("  Done.")


def main():
    """Entry point for `ww monitor huggingface`."""
    args = sys.argv[1:]
    force_alert = "--now" in args
    lookback_hours = 0

    if "--hours" in args:
        try:
            idx = args.index("--hours")
            lookback_hours = int(args[idx + 1])
        except (IndexError, ValueError):
            pass

    cmd_monitor(force_alert=force_alert, lookback_hours=lookback_hours)


if __name__ == "__main__":
    main()
