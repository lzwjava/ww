"""GitHub Management API client.

Uses GITHUB_PAT_TOKEN to query account info, repos, starred repos, rate limits.
"""

import os
import requests

BASE_URL = "https://api.github.com"


def _get_token():
    token = os.getenv("GITHUB_PAT_TOKEN")
    if not token:
        raise Exception("GITHUB_PAT_TOKEN not set")
    return token


def _get(path, params=None):
    """GET with PAT auth. Returns parsed JSON."""
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"{BASE_URL}/{path}"
    resp = requests.get(url, headers=headers, params=params, timeout=15)
    if not resp.ok:
        raise Exception(f"GitHub API error: {resp.status_code} {resp.text[:500]}")
    return resp.json(), resp.headers


def _get_user():
    """Get authenticated user info."""
    data, _ = _get("user")
    return data


def _fmt_count(n):
    """Format count with K/M suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def cmd_info():
    """Show authenticated user info and token scopes."""
    user = _get_user()
    _, headers = _get("user")

    print("GitHub Account")
    print("=" * 40)
    print(f"  Username:      {user.get('login', '?')}")
    print(f"  Name:          {user.get('name', '?')}")
    print(f"  Email:         {user.get('email', '?')}")
    print(f"  Public repos:  {user.get('public_repos', 0)}")
    print(f"  Followers:     {user.get('followers', 0)}")
    print(f"  Following:     {user.get('following', 0)}")
    print(f"  Created:       {user.get('created_at', '?')[:10]}")
    print()
    print(f"  Plan:          {user.get('plan', {}).get('name', '?')}")
    print(f"  Private repos: {user.get('plan', {}).get('private_repos', 0)}")
    print()

    # Rate limit
    rl_data, _ = _get("rate_limit")
    core = rl_data.get("resources", {}).get("core", {})
    search = rl_data.get("resources", {}).get("search", {})
    print(
        f"  Rate Limit (core):   {core.get('remaining', '?')}/{core.get('limit', '?')}"
    )
    print(
        f"  Rate Limit (search): {search.get('remaining', '?')}/{search.get('limit', '?')}"
    )


def cmd_repos():
    """List user's repos (most recently pushed)."""
    repos, _ = _get("user/repos", {"sort": "pushed", "per_page": 30})

    print(f"GitHub Repos (recent, {len(repos)} shown)")
    print("=" * 55)
    for r in repos:
        stars = r.get("stargazers_count", 0)
        lang = r.get("language") or "?"
        private = " [private]" if r.get("private") else ""
        print(f"  {r['full_name']}{private}")
        print(f"    ★ {stars}  lang: {lang}  pushed: {r.get('pushed_at', '?')[:10]}")


def cmd_starred():
    """List starred repos."""
    repos, _ = _get("user/starred", {"per_page": 30})

    print(f"Starred Repos ({len(repos)} shown)")
    print("=" * 55)
    for r in repos:
        stars = r.get("stargazers_count", 0)
        lang = r.get("language") or "?"
        desc = (r.get("description") or "")[:60]
        print(f"  {r['full_name']}")
        print(f"    ★ {stars}  lang: {lang}")
        if desc:
            print(f"    {desc}")


def cmd_followers():
    """List followers."""
    users, _ = _get("user/followers", {"per_page": 30})

    print(f"Followers ({len(users)} shown)")
    print("=" * 40)
    for u in users:
        print(f"  {u['login']}")


def cmd_following():
    """List following."""
    users, _ = _get("user/following", {"per_page": 30})

    print(f"Following ({len(users)} shown)")
    print("=" * 40)
    for u in users:
        print(f"  {u['login']}")


def cmd_notifications():
    """List unread notifications."""
    notifs, _ = _get("notifications", {"per_page": 20})

    if not notifs:
        print("No unread notifications.")
        return

    print(f"Notifications ({len(notifs)} shown)")
    print("=" * 55)
    for n in notifs:
        repo = n.get("repository", {}).get("full_name", "?")
        reason = n.get("reason", "?")
        subject = n.get("subject", {}).get("title", "?")[:50]
        print(f"  [{reason}] {repo}")
        print(f"    {subject}")


def cmd_rate():
    """Show rate limit details."""
    data, _ = _get("rate_limit")
    resources = data.get("resources", {})

    print("GitHub Rate Limits")
    print("=" * 45)
    for name, info in resources.items():
        used = info.get("limit", 0) - info.get("remaining", 0)
        print(
            f"  {name:<12}  {info.get('remaining', '?'):>5}/{info.get('limit', '?'):>5}  used: {used}"
        )


def main():
    import sys

    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww github <command>")
        print()
        print("Commands:")
        print("  info           Account info, plan, rate limits")
        print("  repos          List your repos (recently pushed)")
        print("  starred        List starred repos")
        print("  followers      List followers")
        print("  following      List following")
        print("  notifications  List unread notifications")
        print("  rate           Show rate limit details")
        return

    subcmd = args[0]

    if subcmd == "info":
        cmd_info()
    elif subcmd == "repos":
        cmd_repos()
    elif subcmd == "starred":
        cmd_starred()
    elif subcmd == "followers":
        cmd_followers()
    elif subcmd == "following":
        cmd_following()
    elif subcmd == "notifications":
        cmd_notifications()
    elif subcmd == "rate":
        cmd_rate()
    else:
        print(f"Unknown github command: {subcmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
