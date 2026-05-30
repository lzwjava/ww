#!/usr/bin/env python3
"""List snapshots from AMD Dev Cloud (DigitalOcean API v2)."""

import os
import sys
import requests


API_BASE = "https://api.digitalocean.com/v2"


def main():
    token = os.environ.get("AMD_DEV_CLOUD_API_KEY")
    if not token:
        print("Error: AMD_DEV_CLOUD_API_KEY not set.", file=sys.stderr)
        print("  source ~/.zprofile to load it.", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Handle pagination
    url = f"{API_BASE}/snapshots?per_page=200"
    all_snapshots = []

    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)
            sys.exit(1)

        data = resp.json()
        all_snapshots.extend(data.get("snapshots", []))

        # Follow pagination
        links = data.get("links", {})
        pages = links.get("pages", {})
        url = pages.get("next", None)

    if not all_snapshots:
        print("No snapshots found.")
        return

    print(f"Snapshots ({len(all_snapshots)}):\n")
    print(
        f"  {'ID':<20} {'Name':<45} {'Region':<12} {'Min Disk':<10} {'Size (GB)':<10} {'Created'}"
    )
    print(f"  {'-' * 20} {'-' * 45} {'-' * 12} {'-' * 10} {'-' * 10} {'-' * 25}")

    for snap in all_snapshots:
        snap_id = str(snap.get("id", ""))
        name = snap.get("name", "")
        regions = snap.get("regions", [])
        region = regions[0] if regions else ""
        min_disk = snap.get("min_disk_size", 0)
        size_gb = snap.get("size_gigabytes", 0)
        created = snap.get("created_at", "")

        # Truncate long names
        if len(name) > 43:
            name = name[:40] + "..."

        # Format timestamp to just date+time
        if created:
            created = created[:19].replace("T", " ")

        print(
            f"  {snap_id:<20} {name:<45} {region:<12} {min_disk:<10} {size_gb:<10} {created}"
        )

    print(f"\nTotal: {len(all_snapshots)} snapshots")


if __name__ == "__main__":
    main()
