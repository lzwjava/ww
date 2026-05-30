#!/usr/bin/env python3
"""Create a GPU droplet from an existing snapshot for training."""

import os
import sys
import time
import requests

API_BASE = "https://api.digitalocean.com/v2"

# GPU droplet sizes available for AMD Dev Cloud (MI300X)
GPU_SIZES = [
    {"slug": "gpu-mi300x1-192gb-devcloud", "description": "MI300X 192GB (single GPU)"},
    {"slug": "gpu-mi300x8-1536gb-devcloud", "description": "MI300X 8x192GB (8 GPUs)"},
]


def fetch_ssh_keys(token):
    """Fetch SSH keys from the account."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    resp = requests.get(f"{API_BASE}/account/keys", headers=headers)
    if resp.status_code != 200:
        return []

    return resp.json().get("ssh_keys", [])


def select_ssh_keys(token):
    """Let user select SSH keys for the droplet."""
    keys = fetch_ssh_keys(token)
    if not keys:
        print("No SSH keys found in account.")
        return []

    print("\nSSH Keys available:")
    for i, key in enumerate(keys, 1):
        print(f"  [{i}] {key.get('name', 'Unknown')} (ID: {key.get('id')})")

    print("  [a] All keys")

    while True:
        choice = input(
            "\nSelect SSH key(s) (comma-separated numbers, 'a' for all, or Enter for none): "
        ).strip()
        if not choice:
            return []
        if choice.lower() == "a":
            return [k["id"] for k in keys]

        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected = []
            for idx in indices:
                if 0 <= idx < len(keys):
                    selected.append(keys[idx]["id"])
                else:
                    print(f"Invalid index: {idx + 1}")
                    continue
            return selected
        except ValueError:
            print("Enter numbers separated by commas, 'a', or press Enter.")


def fetch_snapshots(token):
    """Fetch all snapshots from the API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{API_BASE}/snapshots?per_page=200"
    all_snapshots = []

    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)
            sys.exit(1)

        data = resp.json()
        all_snapshots.extend(data.get("snapshots", []))

        links = data.get("links", {})
        pages = links.get("pages", {})
        url = pages.get("next", None)

    return all_snapshots


def create_droplet(token, name, region, size, snapshot_id, ssh_keys=None):
    """Create a droplet from a snapshot."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "name": name,
        "region": region,
        "size": size,
        "image": snapshot_id,
        "ssh_keys": ssh_keys or [],
        "tags": ["training", "gpu"],
    }

    print(f"\nCreating droplet '{name}'...")
    print(f"  Region: {region}")
    print(f"  Size: {size}")
    print(f"  Snapshot ID: {snapshot_id}")

    resp = requests.post(f"{API_BASE}/droplets", headers=headers, json=payload)

    if resp.status_code != 202:
        print(
            f"Error creating droplet: {resp.status_code} {resp.text}", file=sys.stderr
        )
        sys.exit(1)

    droplet = resp.json().get("droplet", {})
    droplet_id = droplet.get("id")
    print(f"\nDroplet created! ID: {droplet_id}")
    return droplet


def wait_for_droplet(token, droplet_id, timeout=300):
    """Wait for droplet to become active."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    print("Waiting for droplet to become active...", end="", flush=True)
    start = time.time()

    while time.time() - start < timeout:
        resp = requests.get(f"{API_BASE}/droplets/{droplet_id}", headers=headers)
        if resp.status_code == 200:
            droplet = resp.json().get("droplet", {})
            status = droplet.get("status")
            networks = droplet.get("networks", {})
            v4 = networks.get("v4", [])
            ip_address = None
            for net in v4:
                if net.get("type") == "public":
                    ip_address = net.get("ip_address")
                    break

            if status == "active" and ip_address:
                print(" Active!")
                return droplet
            elif status == "errored":
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
        print("  source ~/.zprofile to load it.", file=sys.stderr)
        sys.exit(1)

    # Fetch snapshots
    snapshots = fetch_snapshots(token)
    if not snapshots:
        print("No snapshots found.")
        return

    # Filter to GPU-related snapshots (those with mi300x in name)
    gpu_snapshots = [s for s in snapshots if "mi300x" in s.get("name", "").lower()]

    if not gpu_snapshots:
        print("No GPU snapshots found.")
        print("Available snapshots:")
        for s in snapshots:
            print(f"  - {s.get('name', 'Unknown')}")
        return

    # Display GPU snapshots
    print("GPU Snapshots:\n")
    for i, snap in enumerate(gpu_snapshots, 1):
        snap_id = snap.get("id")
        name = snap.get("name", "")
        size_gb = snap.get("size_gigabytes", 0)
        created = snap.get("created_at", "")[:19].replace("T", " ")
        print(f"  [{i}] {name}")
        print(f"      ID: {snap_id} | Size: {size_gb} GB | Created: {created}")

    # Prompt user to select snapshot
    print()
    while True:
        try:
            choice = input("Select snapshot number (or 'q' to quit): ").strip()
            if choice.lower() == "q":
                print("Aborted.")
                return
            idx = int(choice) - 1
            if 0 <= idx < len(gpu_snapshots):
                selected = gpu_snapshots[idx]
                break
            print(f"Invalid choice. Enter 1-{len(gpu_snapshots)}.")
        except ValueError:
            print("Enter a number or 'q'.")

    # Select GPU size
    print("\nGPU Sizes:")
    for i, size in enumerate(GPU_SIZES, 1):
        print(f"  [{i}] {size['slug']} - {size['description']}")

    while True:
        try:
            choice = input("\nSelect GPU size (default 1): ").strip()
            if choice == "":
                choice = "1"
            idx = int(choice) - 1
            if 0 <= idx < len(GPU_SIZES):
                size_slug = GPU_SIZES[idx]["slug"]
                break
            print(f"Invalid choice. Enter 1-{len(GPU_SIZES)}.")
        except ValueError:
            print("Enter a number.")

    # Prompt for droplet name
    default_name = f"train-{selected.get('name', 'gpu')[:20]}"
    name = input(f"\nDroplet name (default: {default_name}): ").strip()
    if not name:
        name = default_name

    # Get region from snapshot
    regions = selected.get("regions", [])
    region = regions[0] if regions else "atl1"

    # Select SSH keys
    ssh_keys = select_ssh_keys(token)

    # Confirm
    print("\n--- Summary ---")
    print(f"Snapshot: {selected.get('name')}")
    print(f"Region: {region}")
    print(f"Size: {size_slug}")
    print(f"Name: {name}")
    print(f"SSH Keys: {len(ssh_keys)} selected")
    confirm = input("\nCreate droplet? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    # Create droplet
    droplet = create_droplet(token, name, region, size_slug, selected["id"], ssh_keys)

    # Wait for it to become active
    droplet_id = droplet.get("id")
    droplet = wait_for_droplet(token, droplet_id)

    if droplet:
        networks = droplet.get("networks", {})
        v4 = networks.get("v4", [])
        ip_address = None
        for net in v4:
            if net.get("type") == "public":
                ip_address = net.get("ip_address")
                break

        print("\nDroplet ready!")
        print(f"  ID: {droplet.get('id')}")
        print(f"  IP: {ip_address}")
        print("\nConnect with:")
        print(f"  ssh root@{ip_address}")
    else:
        print("\nDroplet creation may have failed or timed out.")
        print(f"  Check droplet ID {droplet_id} in the AMD Dev Cloud console.")


if __name__ == "__main__":
    main()
