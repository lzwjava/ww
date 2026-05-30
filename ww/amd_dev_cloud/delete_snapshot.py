#!/usr/bin/env python3
"""Delete a snapshot from AMD Dev Cloud."""

import os
import sys

import requests

API_BASE = "https://api.digitalocean.com/v2"


def fetch_snapshots(token):
    """Fetch all snapshots from the API."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE}/snapshots?per_page=200"
    all_snapshots = []

    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        all_snapshots.extend(data.get("snapshots", []))
        url = data.get("links", {}).get("pages", {}).get("next", None)

    return all_snapshots


def delete_snapshot(token, snap_id):
    """Delete a snapshot by ID."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.delete(f"{API_BASE}/snapshots/{snap_id}", headers=headers)
    return resp.status_code == 204


def main():
    token = os.environ.get("AMD_DEV_CLOUD_API_KEY")
    if not token:
        print("Error: AMD_DEV_CLOUD_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    snapshots = fetch_snapshots(token)
    if not snapshots:
        print("No snapshots found.")
        return

    # Show snapshots
    print(f"Snapshots ({len(snapshots)}):\n")
    for i, snap in enumerate(snapshots, 1):
        name = snap.get("name", "")
        size_gb = snap.get("size_gigabytes", 0)
        created = snap.get("created_at", "")[:19].replace("T", " ")
        print(f"  [{i}] {name}")
        print(f"      ID: {snap['id']} | Size: {size_gb} GB | Created: {created}")

    # Select snapshot
    print()
    while True:
        try:
            choice = input("Select snapshot to delete (or 'q'): ").strip()
            if choice.lower() == "q":
                return
            idx = int(choice) - 1
            if 0 <= idx < len(snapshots):
                selected = snapshots[idx]
                break
        except ValueError:
            pass
        print(f"Enter 1-{len(snapshots)} or 'q'.")

    # Confirm
    print(f"\n  Name: {selected.get('name', '')}")
    print(f"  ID:   {selected['id']}")
    if input("\nDelete this snapshot? [y/N]: ").strip().lower() != "y":
        print("Aborted.")
        return

    if delete_snapshot(token, selected["id"]):
        print("Deleted.")
    else:
        print("Failed to delete.", file=sys.stderr)


if __name__ == "__main__":
    main()
