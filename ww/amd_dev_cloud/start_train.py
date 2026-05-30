#!/usr/bin/env python3
"""Create a GPU droplet from an existing snapshot for training."""

import os
import sys
import time
from datetime import datetime

import requests

API_BASE = "https://api.digitalocean.com/v2"
GPU_SIZE = "gpu-mi300x1-192gb"


def fetch_ssh_keys(token):
    """Fetch all SSH keys from the account."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.get(f"{API_BASE}/account/keys", headers=headers)
    if resp.status_code != 200:
        return []
    return resp.json().get("ssh_keys", [])


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


def create_droplet(token, name, region, snapshot_id, ssh_keys):
    """Create a droplet from a snapshot."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "name": name,
        "region": region,
        "size": GPU_SIZE,
        "image": snapshot_id,
        "ssh_keys": ssh_keys,
        "tags": ["training", "gpu"],
    }

    print(f"\nCreating droplet '{name}'...")
    print(f"  Region: {region} | Size: {GPU_SIZE}")

    resp = requests.post(f"{API_BASE}/droplets", headers=headers, json=payload)
    if resp.status_code != 202:
        print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    droplet = resp.json().get("droplet", {})
    print(f"Droplet created! ID: {droplet.get('id')}")
    return droplet


def wait_for_droplet(token, droplet_id, timeout=300):
    """Wait for droplet to become active and return its IP."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("Waiting for droplet...", end="", flush=True)
    start = time.time()

    while time.time() - start < timeout:
        resp = requests.get(f"{API_BASE}/droplets/{droplet_id}", headers=headers)
        if resp.status_code == 200:
            droplet = resp.json().get("droplet", {})
            status = droplet.get("status")
            for net in droplet.get("networks", {}).get("v4", []):
                if net.get("type") == "public" and net.get("ip_address"):
                    if status == "active":
                        print(" Active!")
                        return net["ip_address"]
            if status == "errored":
                print(" Errored!")
                return None
        print(".", end="", flush=True)
        time.sleep(5)

    print(" Timeout!")
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

    # Auto-select all SSH keys
    ssh_keys = [k["id"] for k in fetch_ssh_keys(token)]
    print(f"SSH keys: {len(ssh_keys)} attached")

    # Build name with timestamp
    ts = datetime.now().strftime("%m%d-%H%M")
    snap_short = selected.get("name", "gpu")[:20]
    default_name = f"train-{snap_short}-{ts}"
    name = input(f"\nDroplet name [{default_name}]: ").strip() or default_name

    # Region from snapshot
    region = selected.get("regions", ["atl1"])[0]

    # Confirm
    print(f"\n--- Creating ---")
    print(f"Snapshot: {selected.get('name')}")
    print(f"Name: {name} | Region: {region} | Size: {GPU_SIZE}")
    if input("Proceed? [y/N]: ").strip().lower() != "y":
        print("Aborted.")
        return

    # Create and wait
    droplet = create_droplet(token, name, region, selected["id"], ssh_keys)
    ip = wait_for_droplet(token, droplet["id"])

    if ip:
        print(f"\nDroplet ready! IP: {ip}")
        print(f"  ssh root@{ip}")
    else:
        print(f"\nCheck droplet ID {droplet['id']} in console.")


if __name__ == "__main__":
    main()
