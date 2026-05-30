#!/usr/bin/env python3
"""End a training session: snapshot the GPU droplet then destroy it."""

import os
import sys
import time
import webbrowser
from datetime import datetime

import requests

API_BASE = "https://api.digitalocean.com/v2"


def fetch_droplets(token):
    """Fetch all droplets."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE}/droplets?per_page=200"
    all_droplets = []

    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        all_droplets.extend(data.get("droplets", []))
        url = data.get("links", {}).get("pages", {}).get("next", None)

    return all_droplets


def snapshot_and_destroy(token, droplet_id, droplet_name):
    """Create a snapshot of the droplet via browser, then destroy it."""
    # Snapshotting GPU droplets also requires the web UI
    ts = datetime.now().strftime("%m%d-%H%M")
    snap_name = f"{droplet_name}-{ts}"

    snap_url = f"https://cloud.digitalocean.com/droplets/{droplet_id}/snapshots"

    print(f"\nGPU droplet snapshots must be created via web dashboard.")
    print(f"Opening browser to snapshot page...\n")
    print(f"  Suggested snapshot name: {snap_name}\n")
    print(f"  URL: {snap_url}\n")

    webbrowser.open(snap_url)
    input("Press Enter after creating the snapshot in the browser...")

    # Verify snapshot exists
    print("Verifying snapshot...", end="", flush=True)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for _ in range(12):  # 60 seconds
        resp = requests.get(f"{API_BASE}/snapshots?per_page=200", headers=headers)
        if resp.status_code == 200:
            for s in resp.json().get("snapshots", []):
                if droplet_name in s.get("name", "") or snap_name in s.get("name", ""):
                    print(f" Found: {s.get('name', '')}")
                    break
            else:
                print(".", end="", flush=True)
                time.sleep(5)
                continue
            break
        print(".", end="", flush=True)
        time.sleep(5)
    else:
        print(" Snapshot not found yet, continuing anyway.")

    # Destroy the droplet
    print(f"\nDestroying droplet '{droplet_name}' (ID: {droplet_id})...")
    confirm = input("Confirm destroy? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted. Droplet still running!")
        return

    resp = requests.delete(f"{API_BASE}/droplets/{droplet_id}", headers=headers)
    if resp.status_code == 204:
        print("Droplet destroyed.")
    else:
        print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)


def main():
    token = os.environ.get("AMD_DEV_CLOUD_API_KEY")
    if not token:
        print("Error: AMD_DEV_CLOUD_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    # Fetch droplets
    droplets = fetch_droplets(token)

    # Filter to GPU droplets (those with gpu in size slug or tags)
    gpu_droplets = []
    for d in droplets:
        size_slug = d.get("size", {}).get("slug", "")
        tags = d.get("tags", [])
        if "gpu" in size_slug.lower() or "gpu" in tags or "training" in tags:
            gpu_droplets.append(d)

    if not gpu_droplets:
        print("No GPU droplets found.")
        return

    # Show droplets
    print("GPU Droplets:\n")
    for i, d in enumerate(gpu_droplets, 1):
        droplet_id = d.get("id")
        name = d.get("name", "")
        status = d.get("status", "")
        size = d.get("size", {}).get("slug", "")
        ip = "no-ip"
        for net in d.get("networks", {}).get("v4", []):
            if net.get("type") == "public" and net.get("ip_address"):
                ip = net["ip_address"]
                break
        created = d.get("created_at", "")[:19].replace("T", " ")
        print(f"  [{i}] {name}")
        print(f"      ID: {droplet_id} | Status: {status} | Size: {size} | IP: {ip} | Created: {created}")

    # Select droplet
    print()
    while True:
        try:
            choice = input("Select droplet to end (or 'q'): ").strip()
            if choice.lower() == "q":
                return
            idx = int(choice) - 1
            if 0 <= idx < len(gpu_droplets):
                selected = gpu_droplets[idx]
                break
        except ValueError:
            pass
        print(f"Enter 1-{len(gpu_droplets)} or 'q'.")

    snapshot_and_destroy(token, selected["id"], selected.get("name", "gpu"))


if __name__ == "__main__":
    main()
