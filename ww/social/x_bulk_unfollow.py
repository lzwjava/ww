"""
Bulk unfollow script for X/Twitter using Playwright + normal Chrome via CDP.
Uses LLM (via OpenRouter) to decide who to unfollow based on their profile.

Strategy: gather profiles in batches of 10, ask LLM to pick exactly 1 to
unfollow from each batch. This distributes unfollows conservatively — recent
follows may align with current interests, old follows have long-term value.

Usage:
    1. Close all Chrome windows first
    2. ww x unfollow --count 500
    3. ww x unfollow --count 500 --delay 3

Prerequisites:
    pip install playwright python-dotenv
    export OPENROUTER_API_KEY=your_key

Note: Launches your real Chrome via remote debugging (no automation flags),
      then connects Playwright via CDP. This avoids bot detection.
"""

import argparse
import json
import os
import re
import subprocess
import time
import random
from datetime import datetime

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright  # type: ignore[reportMissingImports]

load_dotenv()

from ww.llm.openrouter_client import call_openrouter_api_with_messages

FOLLOWING_URL_TEMPLATE = "https://x.com/{username}/following"
DEFAULT_DELAY = 2
DEFAULT_SCROLL_PAUSE = 1.5
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEBUG_PORT = 9222
BATCH_SIZE = 10
REPORT_FILE = os.path.join(os.path.dirname(__file__), "unfollowed_report.json")

LLM_SYSTEM_PROMPT = """You are helping decide who to unfollow on X/Twitter.
The user is a software engineer interested in AI, engineering, and tech.

You are given a batch of 10 profiles. Pick exactly ONE to unfollow.

Use OBJECTIVE signals only — no bias based on language, nationality, or geography.
A Chinese bio is perfectly fine; do not penalize accounts for being Chinese.

Unfollow priority (higher = more likely to pick):
1. Follower count is very low (< 100) — suggests low influence or credibility
2. Bio is empty or spam-like (crypto spam, giveaway spam, link farming)
3. No clear professional identity — no role, no project, no affiliation
4. Account looks inactive or low-quality (generic avatar, no real activity)

Keep priority (don't pick these):
1. High follower count (10K+) — indicates established credibility and influence
2. Clear professional role in AI, engineering, programming, tech, science, startups, VC
3. Has Premium/verified status — indicates serious account
4. Well-known figure, company, or organization in tech or science

When in doubt, prefer keeping the account with more followers and clearer professional identity.

You MUST pick exactly one. Respond with ONLY valid JSON (no markdown, no fences):
{"index": <1-based index of the profile to unfollow>, "reason": "<brief reason in 10 words or less>"}"""


def launch_chrome():
    import socket

    profile_dir = os.path.expanduser("~/.chrome-playwright-debug-profile")
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Wait until the debug port is actually accepting connections
    for _ in range(30):
        try:
            sock = socket.create_connection(("127.0.0.1", DEBUG_PORT), timeout=1)
            sock.close()
            return proc
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    print("Warning: Chrome debug port not responding after 15s")
    return proc


def login_manually(page):
    page.goto("https://x.com/login")
    print("Please log in to your X account in the browser window.")
    print("Press Enter here once you are logged in and see your home feed...")
    input()


def get_username(page):
    page.goto("https://x.com/home")
    page.wait_for_timeout(3000)
    nav_link = page.locator('a[data-testid="AppTabBar_Profile_Link"]')
    href = nav_link.get_attribute("href")
    username = href.strip("/")
    print(f"Detected username: @{username}")
    return username


def extract_profile_info(cell):
    """Extract profile info from a UserCell element."""
    info = {}

    # Username / handle
    try:
        link = cell.locator('a[role="link"]').first
        href = link.get_attribute("href") or ""
        info["handle"] = href.strip("/")
    except Exception:
        info["handle"] = "unknown"

    # Display name
    try:
        name_el = cell.locator('a[role="link"] span').first
        info["name"] = name_el.inner_text()
    except Exception:
        info["name"] = ""

    # Bio
    try:
        bio_el = cell.locator('[data-testid="UserDescription"]')
        if bio_el.count() > 0:
            info["bio"] = bio_el.first.inner_text()
        else:
            info["bio"] = ""
    except Exception:
        info["bio"] = ""

    # Premium / verified badge
    try:
        verified = cell.locator('[data-testid="icon-verified"]')
        info["premium"] = verified.count() > 0
    except Exception:
        info["premium"] = False

    # Follower count — shown in the UserCell, e.g. "1,234 Followers"
    try:
        text = cell.inner_text()
        match = re.search(r"([\d,\.]+[KMB]?)\s*Followers?", text)
        if match:
            raw = match.group(1).replace(",", "")
            mult = 1
            if raw.endswith("K"):
                raw, mult = raw[:-1], 1_000
            elif raw.endswith("M"):
                raw, mult = raw[:-1], 1_000_000
            elif raw.endswith("B"):
                raw, mult = raw[:-1], 1_000_000_000
            info["followers"] = int(float(raw) * mult)
        else:
            info["followers"] = 0
    except Exception:
        info["followers"] = 0

    return info


def ask_llm_pick_unfollow(profiles):
    """Ask LLM to pick one profile from a batch to unfollow.

    Args:
        profiles: list of dicts with handle, name, bio, premium.

    Returns:
        (index_to_unfollow, reason) — index is 0-based, or -1 on error.
    """
    lines = []
    for i, p in enumerate(profiles):
        lines.append(
            f"[{i + 1}] @{p.get('handle', 'unknown')} | "
            f"Name: {p.get('name', '')} | "
            f"Bio: {p.get('bio', '(empty)')} | "
            f"Followers: {p.get('followers', 0):,} | "
            f"Premium: {'Yes' if p.get('premium') else 'No'}"
        )
    profile_text = "\n".join(lines)

    messages = [
        {"role": "system", "content": LLM_SYSTEM_PROMPT},
        {"role": "user", "content": profile_text},
    ]

    try:
        response = call_openrouter_api_with_messages(
            messages, model=None, max_tokens=2000
        )
        text = response.strip()
        match = re.search(r"\{[^}]+\}", text)
        if match:
            text = match.group(0)
        result = json.loads(text)
        idx = int(result.get("index", 0)) - 1  # convert to 0-based
        reason = result.get("reason", "")
        if 0 <= idx < len(profiles):
            return idx, reason
        print(f"  LLM returned invalid index {idx + 1}, skipping batch")
        return -1, "invalid_index"
    except Exception as e:
        print(f"  LLM error: {e}, skipping batch")
        return -1, "llm_error"


def load_report():
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "r") as f:
            return json.load(f)
    return {"unfollowed": [], "kept": [], "run_date": ""}


def save_report(report):
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def collect_batch(page, already_seen, batch_size):
    """Collect a batch of profile cells that haven't been seen yet.

    Returns list of (cell_index, profile_info) tuples.
    """
    batch = []
    cells = page.locator('[data-testid="UserCell"]')
    cell_count = cells.count()

    for i in range(cell_count):
        if len(batch) >= batch_size:
            break
        try:
            cell = cells.nth(i)
            if not cell.is_visible():
                continue
            profile = extract_profile_info(cell)
            handle = profile.get("handle", "unknown")
            if handle in already_seen:
                continue
            already_seen.add(handle)
            batch.append((i, profile))
        except Exception:
            pass
    return batch


def do_unfollow(page, cell_index, profile, report, count, delay, unfollowed):
    """Click unfollow on the cell at cell_index. Returns True if unfollowed."""
    cells = page.locator('[data-testid="UserCell"]')
    cell = cells.nth(cell_index)
    unfollow_btn = cell.locator('button[data-testid$="-unfollow"]')
    if unfollow_btn.count() == 0:
        print(f"  No unfollow button for @{profile['handle']}, skipping")
        return False

    unfollow_btn.first.click()
    page.wait_for_timeout(500)
    confirm = page.locator('button[data-testid="confirmationSheetConfirm"]')
    if confirm.is_visible(timeout=3000):
        confirm.click()

    entry = {
        "handle": profile["handle"],
        "name": profile.get("name", ""),
        "bio": profile.get("bio", ""),
        "premium": profile.get("premium", False),
        "reason": profile.get("reason", ""),
    }
    report["unfollowed"].append(entry)
    unfollowed[0] += 1
    print(f"  Unfollowed @{profile['handle']} ({unfollowed[0]}/{count})")
    jitter = random.uniform(0.5, 1.5)
    time.sleep(delay * jitter)
    return True


def unfollow_with_llm(page, username, count, delay):
    """Scroll through following list, batch profiles, ask LLM to pick 1 per batch."""
    page.goto(FOLLOWING_URL_TEMPLATE.format(username=username))
    page.wait_for_timeout(3000)

    report = load_report()
    report["run_date"] = datetime.now().isoformat()
    already_seen = set()
    unfollowed = [0]  # mutable counter for nested function
    evaluated = 0

    while unfollowed[0] < count:
        # Scroll to load content if needed
        cells = page.locator('[data-testid="UserCell"]')
        if cells.count() == 0:
            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(int(DEFAULT_SCROLL_PAUSE * 1000))
            cells = page.locator('[data-testid="UserCell"]')
            if cells.count() == 0:
                print("No more user cells found. Stopping.")
                break

        # Collect a batch of unseen profiles
        batch = collect_batch(page, already_seen, BATCH_SIZE)

        if len(batch) < BATCH_SIZE:
            # Not enough in view — scroll to load more and retry
            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(int(DEFAULT_SCROLL_PAUSE * 1000))
            batch = collect_batch(page, already_seen, BATCH_SIZE - len(batch))
            batch = batch[:BATCH_SIZE]
            if not batch:
                print("No more new profiles found. Stopping.")
                break

        evaluated += len(batch)
        print(
            f"\nBatch of {len(batch)} profiles gathered (evaluated {evaluated} total):"
        )
        for _, p in batch:
            print(
                f"  @{p['handle']} — {p.get('followers', 0):,} followers"
                f" | bio: {p.get('bio', '')[:50]}"
            )

        # Ask LLM to pick one
        profiles = [p for _, p in batch]
        pick_idx, reason = ask_llm_pick_unfollow(profiles)
        if pick_idx >= 0:
            cell_idx, picked = batch[pick_idx]
            picked["reason"] = reason
            print(f"  LLM picked: @{picked['handle']} — {reason}")
            do_unfollow(page, cell_idx, picked, report, count, delay, unfollowed)
        else:
            print("  No one picked from this batch")

        # Record kept profiles
        for i, (_, p) in enumerate(batch):
            if i != pick_idx:
                report["kept"].append(
                    {"handle": p["handle"], "reason": "kept_in_batch"}
                )

        # Rate limit pause every 50 unfollows
        if unfollowed[0] > 0 and unfollowed[0] % 50 == 0:
            pause = random.uniform(15, 30)
            save_report(report)
            print(f"Pausing for {pause:.0f}s to avoid rate limits...")
            time.sleep(pause)

        # Scroll to load more for next batch
        page.evaluate("window.scrollBy(0, 800)")
        page.wait_for_timeout(int(DEFAULT_SCROLL_PAUSE * 1000))
        save_report(report)

    save_report(report)
    return unfollowed[0], evaluated


def main():
    parser = argparse.ArgumentParser(
        description="Smart bulk unfollow on X/Twitter using LLM decisions."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help="Target number of accounts to unfollow (default: 500).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Base delay in seconds between unfollows (default: {DEFAULT_DELAY}).",
    )
    args = parser.parse_args()

    print("Launching Chrome with remote debugging...")
    print("(Close all other Chrome windows first!)\\n")
    chrome_proc = launch_chrome()

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
            context = browser.contexts[0]
            page = context.new_page()

            login_manually(page)
            username = get_username(page)

            print(f"\nStarting smart unfollow (target: {args.count})...")
            print(f"Batch size: {BATCH_SIZE} (1 unfollow per batch)")
            print(f"Base delay: {args.delay}s | Report: {REPORT_FILE}\n")

            total, evaluated = unfollow_with_llm(page, username, args.count, args.delay)

            print(f"\nDone! Evaluated {evaluated} profiles, unfollowed {total}.")
            print(f"Report saved to: {REPORT_FILE}")
            browser.close()
    finally:
        chrome_proc.terminate()


if __name__ == "__main__":
    main()
