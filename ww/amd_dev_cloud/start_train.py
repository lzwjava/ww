#!/usr/bin/env python3
"""Create a GPU droplet from an existing snapshot for training.

GPU droplets on AMD Dev Cloud can only be created via the web dashboard
(not the DigitalOcean API — GPU sizes have regions=[] in the API).
"""

import os
import sys
import time
import webbrowser
from datetime import datetime

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


def wait_for_droplet(token, name, timeout=300):
    """Poll for a new droplet matching the given name."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print(f"Waiting for droplet '{name}'...", end="", flush=True)
    start = time.time()

    while time.time() - start < timeout:
        resp = requests.get(f"{API_BASE}/droplets?per_page=200", headers=headers)
        if resp.status_code == 200:
            for d in resp.json().get("droplets", []):
                if d.get("name") == name:
                    status = d.get("status")
                    for net in d.get("networks", {}).get("v4", []):
                        if net.get("type") == "public" and net.get("ip_address"):
                            if status == "active":
                                print(" Active!")
                                return net["ip_address"]
                    if status == "errored":
                        print(" Errored!")
                        return None
        print(".", end="", flush=True)
        time.sleep(5)

    print(" Timeout! Check the dashboard.")
    return None


def main():
    token = os.environ.get("AMD_DEV_CLOUD_API_KEY")
    if not token:
        print("Error: AMD_DEV_CLOUD_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    # Fetch and filter GPU snapshots
    snapshots = fetch_snapshots(token)
    gpu_snapshots = [s for s in snapshots if "mi300x" in s.get("name", "").lower()]
    if not gpu_snapshots:
        print("No GPU snapshots found.")
        return

    # Show snapshots
    print("GPU Snapshots:\n")
    for i, snap in enumerate(gpu_snapshots, 1):
        created = snap.get("created_at", "")[:19].replace("T", " ")
        print(f"  [{i}] {snap.get('name', '')}")
        print(f"      ID: {snap['id']} | Size: {snap.get('size_gigabytes', 0)} GB | Created: {created}")

    # Select snapshot
    print()
    while True:
        try:
            choice = input("Select snapshot (or 'q'): ").strip()
            if choice.lower() == "q":
                return
            idx = int(choice) - 1
            if 0 <= idx < len(gpu_snapshots):
                selected = gpu_snapshots[idx]
                break
        except ValueError:
            pass
        print(f"Enter 1-{len(gpu_snapshots)} or 'q'.")

    # Build name with timestamp
    ts = datetime.now().strftime("%m%d-%H%M")
    snap_short = selected.get("name", "gpu")[:20]
    default_name = f"train-{snap_short}-{ts}"

    # Open browser to create droplet from snapshot
    snap_id = selected["id"]
    region = selected.get("regions", ["atl1"])[0]
    create_url = f"https://cloud.digitalocean.com/droplets/new?region={region}&size=gpu-mi300x1-192gb&snapshot={snap_id}"

    print(f"\nGPU droplets can't be created via API (size not available in any region).")
    print(f"Opening browser to create droplet from snapshot...\n")
    print(f"  Name:     {default_name}")
    print(f"  Snapshot: {selected.get('name')}")
    print(f"  Region:   {region}")
    print(f"  Size:     gpu-mi300x1-192gb\n")
    print(f"  URL: {create_url}\n")

    webbrowser.open(create_url)

    # Wait for user to create, then poll for the droplet
    input("Press Enter after creating the droplet in the browser...")

    ip = wait_for_droplet(token, default_name)
    if ip:
        print(f"\nDroplet ready! IP: {ip}")
        print(f"  ssh root@{ip}")
    else:
        print(f"\nDroplet not found. Check the dashboard.")


if __name__ == "__main__":
    main()
