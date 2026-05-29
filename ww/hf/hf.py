"""HuggingFace user profile lookup via public API."""

import sys

import requests

BASE_URL = "https://huggingface.co/api/users"


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


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else None
    cmd_info(username)


if __name__ == "__main__":
    main()
