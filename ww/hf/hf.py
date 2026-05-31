"""HuggingFace user profile lookup and trending feed via public API."""

import sys

import requests

BASE_URL = "https://huggingface.co/api/users"
API_BASE = "https://huggingface.co/api"


def _fmt_date(iso_str):
    """Format ISO timestamp to YYYY-MM-DD."""
    if not iso_str:
        return "?"
    return iso_str[:10]


def cmd_info(username=None):
    """Show HuggingFace user profile info."""
    if not username:
        username = "lzwjava"

    url = f"{BASE_URL}/{username}/overview"
    resp = requests.get(url, timeout=15)
    if not resp.ok:
        if resp.status_code == 404:
            print(f"User '{username}' not found on HuggingFace.")
        else:
            print(f"HF API error: {resp.status_code} {resp.text[:300]}")
        sys.exit(1)

    user = resp.json()

    print(f"HuggingFace Profile: {username}")
    print("=" * 45)
    print(f"  Name:          {user.get('fullname', '?')}")
    print(f"  Username:      {user.get('user', '?')}")
    print(f"  Created:       {_fmt_date(user.get('createdAt'))}")
    print(f"  Pro:           {'Yes' if user.get('isPro') else 'No'}")
    print()

    # Details/bio
    details = user.get("details", "")
    if details:
        print(f"  Bio:           {details}")
        print()

    # Count user artifacts
    models = user.get("numModels", 0)
    datasets = user.get("numDatasets", 0)
    spaces = user.get("numSpaces", 0)

    print("  Contributions:")
    print(f"    Models:      {models}")
    print(f"    Datasets:    {datasets}")
    print(f"    Spaces:      {spaces}")
    print()

    # Social stats
    likes = user.get("numLikes", 0)
    followers = user.get("numFollowers", 0)
    following = user.get("numFollowing", 0)

    print("  Social:")
    print(f"    Likes:       {likes}")
    print(f"    Followers:   {followers}")
    print(f"    Following:   {following}")
    print()

    # Profile link
    print(f"  Profile:       https://huggingface.co/{username}")


def _fetch_trending(kind, limit=10):
    """Fetch trending items from HuggingFace API. kind: models|datasets|spaces."""
    url = f"{API_BASE}/{kind}"
    params = {"sort": "trendingScore", "direction": "-1", "limit": limit}
    resp = requests.get(url, params=params, timeout=15)
    if not resp.ok:
        print(f"  HF API error for {kind}: {resp.status_code}")
        return []
    return resp.json()


def _fmt_downloads(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def cmd_news(limit=10):
    """Show trending models, datasets, and spaces on HuggingFace."""
    as_json = "--json" in sys.argv
    if "--limit" in sys.argv:
        try:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    items = {
        "models": _fetch_trending("models", limit),
        "datasets": _fetch_trending("datasets", limit),
        "spaces": _fetch_trending("spaces", limit),
    }

    if as_json:
        import json

        print(json.dumps(items, indent=2))
        return

    sections = [
        ("models", "Trending Models"),
        ("datasets", "Trending Datasets"),
        ("spaces", "Trending Spaces"),
    ]

    for key, title in sections:
        entries = items[key]
        print(f"{'=' * 60}")
        print(f"  {title}  ({len(entries)} items)")
        print(f"{'=' * 60}")
        if not entries:
            print("  (none)")
            print()
            continue
        for i, item in enumerate(entries, 1):
            item_id = item.get("id", "?")
            likes = item.get("likes", 0)
            score = item.get("trendingScore", 0)
            created = (item.get("createdAt") or "")[:10]

            # Extra info per kind
            extra = ""
            if key == "models":
                downloads = _fmt_downloads(item.get("downloads", 0))
                pipeline = item.get("pipeline_tag", "")
                extra = f"  [{pipeline}] {downloads} dl"
            elif key == "datasets":
                downloads = _fmt_downloads(item.get("downloads", 0))
                extra = f"  {downloads} dl"
            elif key == "spaces":
                sdk = item.get("sdk", "")
                extra = f"  [{sdk}]"

            print(f"  {i:>2}. {item_id}")
            print(f"      Score: {score}  Likes: {likes}  Created: {created}{extra}")

        # Link to browse more
        kind = key if key != "spaces" else "spaces"
        print(f"\n  https://huggingface.co/{kind}?sort=trending")
        print()


def cmd_top30():
    """Show top 30 most-followed HuggingFace users from Weyaxi leaderboard dataset."""
    import csv
    import io
    from datetime import datetime, timedelta

    # Find latest dataset directory name (format: "DD-MM-YYYY HH-MM")
    # Try recent dates — dataset updates daily around 04:00 UTC
    now = datetime.utcnow()
    dataset_base = (
        "https://huggingface.co/datasets/Weyaxi/followers-leaderboard/resolve/main"
    )

    csv_url = None
    for days_back in range(3):
        dt = now - timedelta(days=days_back)
        for hour in [4, 3, 5, 2]:
            for minute in [0, 8, 3, 5, 10, 15, 20, 30, 40, 50]:
                dirname = f"{dt.strftime('%d-%m-%Y')} {hour:02d}-{minute:02d}"
                url = f"{dataset_base}/{dirname}/data.csv?download=true"
                try:
                    resp = requests.head(url, timeout=5)
                    if resp.ok:
                        csv_url = url
                        break
                except Exception:
                    continue
            if csv_url:
                break
        if csv_url:
            break

    if not csv_url:
        print("Error: Could not find latest leaderboard data. Try again later.")
        sys.exit(1)

    # Download CSV
    resp = requests.get(csv_url, timeout=30)
    if not resp.ok:
        print(f"Error downloading leaderboard: {resp.status_code}")
        sys.exit(1)

    # Parse and sort
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = []
    for row in reader:
        try:
            followers = int(row["Number of Followers"])
            following = int(row["Number of Following"])
            rows.append((row["Author"], followers, following))
        except (ValueError, KeyError):
            continue

    rows.sort(key=lambda x: x[1], reverse=True)
    top = rows[:30]

    # Parse date from URL for display
    date_str = (
        csv_url.split("/resolve/main/")[1].split("/")[0]
        if "/resolve/main/" in csv_url
        else "unknown"
    )

    print("Top 30 HuggingFace Users by Followers")
    print(f"Source: Weyaxi/followers-leaderboard ({date_str})")
    print("=" * 60)
    print(f"{'#':>3}  {'Username':<25} {'Followers':>10}  {'Following':>9}")
    print("-" * 60)
    for i, (author, followers, following) in enumerate(top, 1):
        print(f"{i:>3}. {author:<25} {followers:>10,}  {following:>9,}")
    print("-" * 60)
    print(f"Total users in dataset: {len(rows):,}")
    print("\nhttps://huggingface.co/spaces/Weyaxi/followers-leaderboard")


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else None
    cmd_info(username)


if __name__ == "__main__":
    main()
