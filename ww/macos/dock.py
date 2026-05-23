"""
List applications currently pinned to the macOS Dock.

Reads ~/Library/Preferences/com.apple.dock.plist via Python's plistlib.

Usage: ww dock [--json]
"""

import argparse
import json
import plistlib
import subprocess
import sys
from pathlib import Path


DOCK_PLIST = Path.home() / "Library" / "Preferences" / "com.apple.dock.plist"


def _read_dock_apps():
    """Read persistent-apps from the Dock plist. Returns list of dicts."""
    if not DOCK_PLIST.exists():
        print(f"Dock plist not found: {DOCK_PLIST}", file=sys.stderr)
        sys.exit(1)

    with open(DOCK_PLIST, "rb") as f:
        data = plistlib.load(f)

    apps = []
    for item in data.get("persistent-apps", []):
        tile = item.get("tile-data", {})
        label = tile.get("file-label", "?")
        bundle_id = tile.get("bundle-identifier", "")
        file_url = tile.get("file-data", {}).get("_CFURLString", "")
        apps.append(
            {
                "name": label,
                "bundle_id": bundle_id,
                "path": file_url.replace("file://", "").rstrip("/"),
            }
        )

    return apps


def _running_pids():
    """Return set of bundle ids that are currently running."""
    try:
        out = subprocess.check_output(
            [
                "osascript",
                "-e",
                'tell application "System Events" to get bundle identifier of every process whose background only is false',
            ],
            text=True,
            timeout=5,
        ).strip()
        if out:
            return {b.strip() for b in out.split(",") if b.strip()}
    except Exception:
        pass
    return set()


def main():
    parser = argparse.ArgumentParser(description="List macOS Dock applications")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    apps = _read_dock_apps()

    if args.json:
        print(json.dumps(apps, indent=2))
        return

    if not apps:
        print("No applications found in Dock.")
        return

    running = _running_pids()
    max_name = max(len(a["name"]) for a in apps)

    print(f"Dock ({len(apps)} apps)")
    print(f"{'#':>3}  {'App':<{max_name}}  {'Bundle ID'}")
    print(f"{'':>3}  {'─' * max_name}  {'─' * 40}")

    for i, app in enumerate(apps, 1):
        marker = "●" if app["bundle_id"] in running else " "
        print(f"{i:>3}{marker} {app['name']:<{max_name}}  {app['bundle_id']}")

    if running:
        print(
            f"\n● = currently running ({sum(1 for a in apps if a['bundle_id'] in running)}/{len(apps)})"
        )


if __name__ == "__main__":
    main()
