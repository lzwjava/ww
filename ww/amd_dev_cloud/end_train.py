#!/usr/bin/env python3
"""End a training session: snapshot the GPU droplet then destroy it."""

import os
import sys
import time
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


def create_snapshot(token, droplet_id, name):
    """Create a snapshot of a droplet via API."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"type": "snapshot", "name": name}
    resp = requests.post(
        f"{API_BASE}/droplets/{droplet_id}/actions", headers=headers, json=payload
    )
    if resp.status_code != 201:
        print(
            f"Error creating snapshot: {resp.status_code} {resp.text}", file=sys.stderr
        )
        return None
    return resp.json().get("action", {})


def wait_for_snapshot(token, droplet_id, timeout=600):
    """Wait for the snapshot action to complete."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("Snapshotting", end="", flush=True)
    start = time.time()

    while time.time() - start < timeout:
        resp = requests.get(
            f"{API_BASE}/droplets/{droplet_id}/actions?per_page=5", headers=headers
        )
        if resp.status_code == 200:
            actions = resp.json().get("actions", [])
            for a in actions:
                if a.get("type") == "snapshot":
                    status = a.get("status")
                    if status == "completed":
                        print(" Done!")
                        return True
                    elif status == "errored":
                        print(" Errored!")
                        return False
        print(".", end="", flush=True)
        time.sleep(10)

    print(" Timeout!")
    return False


def destroy_droplet(token, droplet_id, name):
    """Destroy a droplet."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.delete(f"{API_BASE}/droplets/{droplet_id}", headers=headers)
    if resp.status_code == 204:
        print(f"Droplet '{name}' destroyed.")
    else:
        print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)


def main():
    token = os.environ.get("AMD_DEV_CLOUD_API_KEY")
    if not token:
        print("Error: AMD_DEV_CLOUD_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    # Fetch droplets
    droplets = fetch_droplets(token)

    # Filter to GPU droplets
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
        print(
            f"      ID: {d['id']} | Status: {status} | Size: {size} | IP: {ip} | Created: {created}"
        )

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

    droplet_id = selected["id"]
    droplet_name = selected.get("name", "gpu")

    # Snapshot
    ts = datetime.now().strftime("%m%d-%H%M")
    snap_name = f"snap-{droplet_name}-{ts}"

    print(f"\nCreating snapshot: {snap_name}")
    action = create_snapshot(token, droplet_id, snap_name)
    if not action:
        print("Failed to create snapshot. Aborting.")
        return

    if not wait_for_snapshot(token, droplet_id):
        print("Snapshot failed. Droplet NOT destroyed.")
        return

    # Destroy
    confirm = input(f"\nDestroy droplet '{droplet_name}'? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted. Droplet still running!")
        return

    destroy_droplet(token, droplet_id, droplet_name)


if __name__ == "__main__":
    main()
