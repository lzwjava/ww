import os
import subprocess
import sys


def run_wol():
    """Send a Wake-on-LAN packet to the configured MAC address."""
    mac_address = os.environ.get("MAG_MAC_ADDRESS")
    if not mac_address:
        print(
            "Error: MAG_MAC_ADDRESS environment variable is not set in .env.",
            file=sys.stderr,
        )
        return

    try:
        subprocess.run(["wakeonlan", mac_address], check=True)
        print(f"Wake-on-LAN packet sent to {mac_address}")
    except subprocess.CalledProcessError as e:
        print(f"Error running wakeonlan: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(
            "Error: 'wakeonlan' command not found. Install it first (e.g., sudo apt install wakeonlan).",
            file=sys.stderr,
        )
