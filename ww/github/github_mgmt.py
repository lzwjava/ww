"""GitHub Management API client.

Uses GITHUB_PAT_TOKEN to query account info, repos, starred repos, rate limits.
Also supports public user lookups and interest comparison.
"""

import os
import sys
from collections import Counter

import requests

BASE_URL = "https://api.github.com"


def _get_token():
    token = os.getenv("GITHUB_PAT_TOKEN")
    if not token:
        raise Exception("GITHUB_PAT_TOKEN not set")
    return token


def _get(path, params=None, auth=True):
    """GET with optional PAT auth. Returns parsed JSON."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if auth:
        headers["Authorization"] = f"Bearer {_get_token()}"
    url = f"{BASE_URL}/{path}"
    resp = requests.get(url, headers=headers, params=params, timeout=15)
    if not resp.ok:
        raise Exception(f"GitHub API error: {resp.status_code} {resp.text[:500]}")
    return resp.json(), resp.headers


def _get_user():
    """Get authenticated user info."""
    data, _ = _get("user")
    return data


def _get_all_pages(path, params=None, auth=True, max_pages=10):
    """Fetch all pages for a paginated endpoint."""
    results = []
    params = params or {}
    params.setdefault("per_page", 100)
    for page in range(1, max_pages + 1):
        params["page"] = page
        data, headers = _get(path, params=params, auth=auth)
        if not data:
            break
        results.extend(data)
        if len(data) < params["per_page"]:
            break
    return results


def _fetch_user_profile(username):
    """Fetch public profile + repos + starred for any user."""
    # Use auth if available to avoid 60 req/hr unauthenticated rate limit
    use_auth = bool(os.getenv("GITHUB_PAT_TOKEN"))
    user, _ = _get(f"users/{username}", auth=use_auth)
    repos = _get_all_pages(f"users/{username}/repos", {"sort": "pushed"}, auth=use_auth)
    try:
        starred = _get_all_pages(f"users/{username}/starred", auth=use_auth)
    except Exception:
        starred = []
    return user, repos, starred


def _analyze_user(username):
    """Analyze a single user: profile, languages, interests."""
    user, repos, starred = _fetch_user_profile(username)

    # Language breakdown from repos
    lang_counts = Counter()
    for r in repos:
        lang = r.get("language")
        if lang:
            lang_counts[lang] += 1

    # Top topics/description keywords from repos
    topics = []
    for r in repos:
        topics.extend(r.get("topics", []))

    return {
        "username": user.get("login", username),
        "name": user.get("name", ""),
        "bio": user.get("bio", "") or "",
        "location": user.get("location", "") or "",
        "created": user.get("created_at", "?")[:10],
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "company": user.get("company", "") or "",
        "blog": user.get("blog", "") or "",
        "twitter": user.get("twitter_username", "") or "",
        "repos": repos,
        "starred": starred,
        "lang_counts": lang_counts,
        "topics": Counter(topics),
    }


def _print_user_report(profile):
    """Print a detailed profile report."""
    p = profile
    print(f"\n{'=' * 55}")
    print(f"  GitHub Profile: {p['username']}")
    print(f"{'=' * 55}")
    if p["name"]:
        print(f"  Name:         {p['name']}")
    if p["bio"]:
        print(f"  Bio:          {p['bio']}")
    if p["location"]:
        print(f"  Location:     {p['location']}")
    if p["company"]:
        print(f"  Company:      {p['company']}")
    if p["blog"]:
        print(f"  Blog:         {p['blog']}")
    if p["twitter"]:
        print(f"  Twitter:      @{p['twitter']}")
    print(f"  Registered:   {p['created']}")
    print(f"  Public repos: {p['public_repos']}")
    print(f"  Followers:    {p['followers']}  |  Following: {p['following']}")

    # Languages
    if p["lang_counts"]:
        print(f"\n  Languages ({len(p['lang_counts'])} seen):")
        for lang, count in p["lang_counts"].most_common(15):
            print(f"    {lang:<15} {count} repos")

    # Topics
    if p["topics"]:
        print(f"\n  Repo Topics:")
        for topic, count in p["topics"].most_common(20):
            print(f"    {topic:<25} {count} repos")

    # Top repos by stars
    top_repos = sorted(p["repos"], key=lambda r: r.get("stargazers_count", 0), reverse=True)[:10]
    if top_repos:
        print(f"\n  Top Repos (by stars):")
        for r in top_repos:
            stars = r.get("stargazers_count", 0)
            lang = r.get("language") or "?"
            desc = (r.get("description") or "")[:55]
            print(f"    ★{stars:>5}  {r['name']:<30} [{lang}]")
            if desc:
                print(f"           {desc}")

    # Recent repos
    recent = p["repos"][:5]
    if recent:
        print(f"\n  Recently Active:")
        for r in recent:
            pushed = (r.get("pushed_at") or "?")[:10]
            lang = r.get("language") or "?"
            print(f"    {r['name']:<30} [{lang}]  pushed: {pushed}")

    # Starred repos count
    if p["starred"]:
        print(f"\n  Starred repos: {len(p['starred'])}")
        # Top starred interests by language
        star_langs = Counter()
        for r in p["starred"]:
            lang = r.get("language")
            if lang:
                star_langs[lang] += 1
        if star_langs:
            print(f"  Starred languages:")
            for lang, count in star_langs.most_common(10):
                print(f"    {lang:<15} {count} repos")


def cmd_profile(username):
    """Show detailed profile report for any GitHub user."""
    profile = _analyze_user(username)
    _print_user_report(profile)


def cmd_interests(user1, user2):
    """Compare interests between two GitHub users."""
    print(f"Fetching {user1}...")
    p1 = _analyze_user(user1)
    print(f"Fetching {user2}...")
    p2 = _analyze_user(user2)

    # Print both profiles
    _print_user_report(p1)
    _print_user_report(p2)

    # Comparison
    print(f"\n{'=' * 55}")
    print(f"  COMPARISON: {user1} vs {user2}")
    print(f"{'=' * 55}")

    # Mutual starred repos
    starred1 = {r["full_name"] for r in p1["starred"]}
    starred2 = {r["full_name"] for r in p2["starred"]}
    mutual_starred = starred1 & starred2

    # Mutual topics
    topics1 = set(p1["topics"].keys())
    topics2 = set(p2["topics"].keys())
    mutual_topics = topics1 & topics2

    # Mutual languages
    langs1 = set(p1["lang_counts"].keys())
    langs2 = set(p2["lang_counts"].keys())
    mutual_langs = langs1 & langs2

    # Mutual followers/following
    use_auth = bool(os.getenv("GITHUB_PAT_TOKEN"))
    try:
        followers1 = {u["login"] for u in _get(f"users/{user1}/followers", auth=use_auth)[0]}
        following1 = {u["login"] for u in _get(f"users/{user1}/following", auth=use_auth)[0]}
        followers2 = {u["login"] for u in _get(f"users/{user2}/followers", auth=use_auth)[0]}
        following2 = {u["login"] for u in _get(f"users/{user2}/following", auth=use_auth)[0]}
        mutual_followers = (followers1 | following1) & (followers2 | following2)
    except Exception:
        mutual_followers = set()

    # Categorize mutual starred repos by domain
    if mutual_starred:
        print(f"\n  MUTUAL STARRED REPOS ({len(mutual_starred)}):")
        for repo in sorted(mutual_starred):
            # Try to find description from either user's starred list
            desc = ""
            for r in p1["starred"] + p2["starred"]:
                if r["full_name"] == repo:
                    desc = (r.get("description") or "")[:60]
                    break
            print(f"    {repo}")
            if desc:
                print(f"      {desc}")

    if mutual_langs:
        print(f"\n  SHARED LANGUAGES: {', '.join(sorted(mutual_langs))}")

    if mutual_topics:
        print(f"\n  SHARED TOPICS: {', '.join(sorted(mutual_topics))}")

    if mutual_followers:
        print(f"\n  MUTUAL CONNECTIONS: {', '.join(sorted(mutual_followers)[:20])}")

    # Unique interests
    only1_starred = starred1 - starred2
    only2_starred = starred2 - starred1

    if only1_starred:
        print(f"\n  Only {user1} stars ({len(only1_starred)}):")
        for repo in sorted(only1_starred)[:15]:
            print(f"    {repo}")
        if len(only1_starred) > 15:
            print(f"    ... and {len(only1_starred) - 15} more")

    if only2_starred:
        print(f"\n  Only {user2} stars ({len(only2_starred)}):")
        for repo in sorted(only2_starred)[:15]:
            print(f"    {repo}")
        if len(only2_starred) > 15:
            print(f"    ... and {len(only2_starred) - 15} more")

    # Language comparison
    all_langs = sorted(langs1 | langs2)
    if all_langs:
        print(f"\n  LANGUAGE COMPARISON:")
        print(f"    {'Language':<15} {user1:>12}  {user2:>12}")
        print(f"    {'-' * 42}")
        for lang in all_langs:
            c1 = p1["lang_counts"].get(lang, 0)
            c2 = p2["lang_counts"].get(lang, 0)
            bar1 = "█" * min(c1, 20)
            bar2 = "█" * min(c2, 20)
            print(f"    {lang:<15} {c1:>3} {bar1:<8}  {c2:>3} {bar2:<8}")

    # Summary
    print(f"\n  SUMMARY:")
    overlap = len(mutual_starred)
    total = len(starred1 | starred2)
    if total > 0:
        pct = overlap / total * 100
        print(f"    Star overlap: {overlap}/{total} repos ({pct:.1f}%)")
    print(f"    Language overlap: {len(mutual_langs)}/{len(all_langs)} languages")
    if mutual_topics:
        print(f"    Topic overlap: {len(mutual_topics)} shared topics")


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
