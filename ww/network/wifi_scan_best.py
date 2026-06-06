#!/usr/bin/env python3
"""
WiFi Signal Scanner — scan available networks, compare signal strength,
and recommend the best network. macOS uses CoreWLAN (PyObjC), Linux uses nmcli.

Does NOT disconnect from current WiFi.

On macOS, SSIDs are hidden by Location Services privacy. To reveal them:
  System Settings > Privacy & Security > Location Services > enable for Terminal/iTerm
Or use --identify to scan known preferred networks and match by signal.
"""

import platform
import sys


def _get_preferred_ssids():
    """Get saved preferred WiFi network names (macOS)."""
    import subprocess

    try:
        result = subprocess.run(
            ["networksetup", "-listpreferredwirelessnetworks", "en0"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        ssids = []
        for line in result.stdout.strip().split("\n"):
            s = line.strip()
            if s and not s.startswith("Preferred"):
                ssids.append(s)
        return ssids
    except Exception:
        return []


def _get_current_ssid_scd():
    """Try to get current SSID from SystemConfiguration CachedScanRecord."""
    try:
        import SystemConfiguration  # type: ignore[reportMissingImports]
        import re

        store = SystemConfiguration.SCDynamicStoreCreate(None, "wifi", None, None)
        val = SystemConfiguration.SCDynamicStoreCopyValue(
            store, "State:/Network/Interface/en0/AirPort"
        )
        if not val:
            return None
        cached = val.get("CachedScanRecord")
        if not cached:
            return None
        raw = bytes(cached)
        # Extract readable strings and look for known SSIDs
        ssids_found = []
        for m in re.finditer(rb"[\x20-\x7e]{3,32}", raw):
            s = m.group().decode("ascii", errors="ignore")
            if len(s) >= 3:
                noise_patterns = (
                    "NSKeyed",
                    "archiver",
                    "NSMutableArray",
                    "NSMutableDictionary",
                    "NSDictionary",
                    "NSArray",
                    "NSObject",
                    "NSString",
                    "NSNumber",
                    "NSData",
                    "SCAN_RESULT",
                    "IE_KEY",
                    "CHANNEL_FLAGS",
                    "BSS_TRANS",
                    "PRIVATE_MAC",
                    "HT_",
                    "WPA_",
                    "RSN_",
                    "WEPOPEN",
                    "MCS_SET",
                    "AMPDU",
                    "TXBF",
                    "ASEL",
                    "CAPABILITIES",
                    "BEACON",
                    "RSSI_",
                    "NOISE_",
                    "SNR",
                    "TIMESTAMP",
                    "SSID_STR",
                    "Smart",
                    "Bluetooth",
                    "Auto",
                    "Busy",
                    "Power",
                    "Profile",
                    "UserMode",
                    "Cached",
                    "WEP40",
                    "PHY_MODE",
                    "QBSS_",
                    "RATES",
                    "TRANS_DISABLED",
                    "Assoc",
                    "BC^",
                    "b2/",
                    "ray",
                    "Troot",
                    "EACON_",
                    "EP40_",
                    "HAN_UTIL",
                    "375DE_",
                    "AGS_",
                    "COLOCATED",
                    "AMPDU_PARAM",
                    "TXBF_CAPS",
                    "ASEL_CAPS",
                    "HT_STA",
                    "HT_PRIMARY",
                    "HT_NON",
                    "HT_SECONDARY",
                    "HT_OP",
                    "HT_TX",
                    "HT_PSMP",
                    "HT_OBSS",
                    "HT_PCO",
                    "HT_DUAL",
                    "HT_LSIG",
                    "HT_BASIC",
                    "HT_RIFS",
                    "HT_SERVICE",
                    "BEACON_INT",
                    "HT_CAPS",
                    "EXT_CAP",
                    "BSSID",
                    "CHANNEL",
                    "UAGE",
                    "bplist",
                )
                if not any(p in s for p in noise_patterns):
                    ssids_found.append(s)
        # Return the first plausible SSID
        for s in ssids_found:
            if not s.startswith("#") and not s.startswith(")") and ":" not in s[:3]:
                return s
    except Exception:
        pass
    return None


def _scan_preferred_to_match(iface, scan_entries, max_scan=50):
    """Scan preferred networks and match to scan entries by (rssi, ch, bw)."""
    preferred = _get_preferred_ssids()
    if not preferred:
        return {}

    # Build lookup: (rssi, ch, bw) -> list of scan indices
    sig_map = {}
    for i, entry in enumerate(scan_entries):
        key = (entry[1], entry[3], entry[4])  # rssi, ch, bw
        sig_map.setdefault(key, []).append(i)

    matched = {}
    scanned = 0
    for ssid_name in preferred:
        if scanned >= max_scan:
            break
        try:
            nets, _ = iface.scanForNetworksWithName_error_(ssid_name, None)
            scanned += 1
            if nets:
                for n in nets:
                    rssi = n.rssiValue()
                    ch = n.wlanChannel()
                    ch_num = ch.channelNumber() if ch else 0
                    bw = int(ch.channelWidth()) if ch else 0
                    key = (rssi, ch_num, bw)
                    if key in sig_map:
                        for idx in sig_map[key]:
                            if idx not in matched:
                                matched[idx] = ssid_name
        except Exception:
            pass

    return matched


def _macos_scan(identify=False):
    """Scan WiFi using CoreWLAN framework (macOS)."""
    try:
        from CoreWLAN import CWWiFiClient  # type: ignore[reportMissingImports]
    except ImportError:
        print("ERROR: pyobjc-framework-CoreWLAN not installed.")
        print("  pip3 install pyobjc-framework-CoreWLAN")
        return

    client = CWWiFiClient.sharedWiFiClient()
    names = client.interfaceNames()
    if not names:
        print("No WiFi interface found.")
        return

    iface = client.interfaceWithName_(names[0])
    cur_ssid = iface.ssid() or _get_current_ssid_scd()
    cur_rssi = iface.rssiValue()
    cur_noise = iface.noiseMeasurement()
    cur_ch = iface.wlanChannel()
    cur_ch_num = cur_ch.channelNumber() if cur_ch else 0

    print(
        f"Current: {cur_ssid or '(hidden)'}  RSSI: {cur_rssi} dBm  "
        f"Noise: {cur_noise} dBm  SNR: {cur_rssi - cur_noise} dB  Ch: {cur_ch_num}"
    )
    if not iface.ssid():
        print(
            "  (SSID hidden by macOS — enable Location Services for Terminal to reveal)"
        )
    print()

    networks, err = iface.scanForNetworksWithName_error_(None, None)
    if err:
        print(f"Scan error: {err}")
        return

    if not networks:
        print("No networks found.")
        return

    # Build scan entries: (ssid, rssi, noise, ch, bw)
    scan_entries = []
    for n in networks:
        ssid = n.ssid() or "(hidden)"
        rssi = n.rssiValue()
        noise = n.noiseMeasurement()
        ch = n.wlanChannel()
        ch_num = ch.channelNumber() if ch else 0
        bw = int(ch.channelWidth()) if ch else 0
        scan_entries.append((ssid, rssi, noise, ch_num, bw))

    scan_entries.sort(key=lambda x: x[1], reverse=True)

    # Try to identify hidden SSIDs by scanning preferred networks
    if identify:
        print("Identifying networks by scanning preferred list...")
        matched = _scan_preferred_to_match(iface, scan_entries)
        if matched:
            entries_list = list(scan_entries)
            for idx, ssid_name in matched.items():
                old = entries_list[idx]
                entries_list[idx] = (ssid_name, old[1], old[2], old[3], old[4])
            scan_entries = tuple(entries_list)
            print(f"  Identified {len(matched)} networks.")
        else:
            print("  No matches found.")
        print()

    five_ghz = [e for e in scan_entries if e[3] > 14]
    two_4_ghz = [e for e in scan_entries if e[3] <= 14]

    BW_LABELS = {0: "?", 1: "20MHz", 2: "40MHz", 3: "80MHz", 4: "160MHz"}

    def _is_current(entry):
        if cur_ssid and entry[0] == cur_ssid:
            return True
        if not cur_ssid and entry[1] == cur_rssi:
            return True
        return False

    def _print_table(title, rows):
        print(f"=== {title} ===")
        print(
            f"  {'SSID':<35} {'RSSI':>6} {'Noise':>6} {'SNR':>5} {'Ch':>4} {'BW':<8}  Note"
        )
        print("  " + "-" * 85)
        for ssid, rssi, noise, ch_num, bw in rows:
            snr = rssi - (noise if noise else -90)
            bw_label = BW_LABELS.get(bw, f"{bw}")
            marker = " <-- YOU" if _is_current((ssid, rssi, noise, ch_num, bw)) else ""
            print(
                f"  {ssid:<35} {rssi:>5}  {noise:>5}  {snr:>4}  {ch_num:>3}  {bw_label:<8}{marker}"
            )
        print()

    if five_ghz:
        _print_table("5 GHz (faster, less range)", five_ghz)
    if two_4_ghz:
        _print_table("2.4 GHz (better range, slower)", two_4_ghz)

    # Recommendation
    print("=== RECOMMENDATION ===")
    best_5 = five_ghz[0] if five_ghz else None
    best_24 = two_4_ghz[0] if two_4_ghz else None

    if best_5:
        snr5 = best_5[1] - (best_5[2] if best_5[2] else -90)
        print(
            f"  Best 5GHz:  {best_5[0]:<35} RSSI {best_5[1]} dBm, Ch {best_5[3]}, SNR ~{snr5} dB"
        )
    if best_24:
        snr24 = best_24[1] - (best_24[2] if best_24[2] else -90)
        print(
            f"  Best 2.4G:  {best_24[0]:<35} RSSI {best_24[1]} dBm, Ch {best_24[3]}, SNR ~{snr24} dB"
        )

    print()
    if _is_current((cur_ssid or "", cur_rssi, cur_noise, cur_ch_num, 0)):
        if best_5 and best_5[1] > cur_rssi + 5 and not _is_current(best_5):
            delta = best_5[1] - cur_rssi
            print(f"  >>> STRONGER 5GHz available: {best_5[0]} ({delta} dB better)")
            print(
                f"      Switch with: networksetup -setairportnetwork en0 '{best_5[0]}' <password>"
            )
        elif best_24 and best_24[1] > cur_rssi + 5 and not _is_current(best_24):
            delta = best_24[1] - cur_rssi
            print(f"  >>> A 2.4GHz network is {delta} dB stronger: {best_24[0]}")
            if best_5:
                print("      Stick with 5GHz for speed unless you need range.")
        else:
            print("  >>> Your current signal is among the best available.")


def _linux_scan():
    """Scan WiFi using nmcli (Linux)."""
    import subprocess

    try:
        subprocess.run(
            ["nmcli", "device", "wifi", "rescan"], capture_output=True, timeout=5
        )
    except Exception:
        pass

    try:
        result = subprocess.run(
            [
                "nmcli",
                "-t",
                "-f",
                "SSID,SIGNAL,FREQ,CHAN,SECURITY,ACTIVE,IN-USE",
                "device",
                "wifi",
                "list",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        print("ERROR: nmcli not found. Install NetworkManager.")
        return

    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        return

    lines = [line for line in result.stdout.strip().splitlines() if line]
    if not lines:
        print("No WiFi networks found.")
        return

    networks = []
    for line in lines:
        parts = line.split(":")
        if len(parts) < 5:
            continue
        ssid = parts[0] or "(hidden)"
        try:
            signal = int(parts[1])
        except ValueError:
            continue
        freq = parts[2]
        chan = parts[3]
        security = parts[4]
        active = len(parts) > 5 and parts[5] == "yes"
        in_use = len(parts) > 6 and parts[6] == "*"
        is_5g = "5" in freq
        networks.append((ssid, signal, freq, chan, security, active or in_use, is_5g))

    networks.sort(key=lambda x: x[1], reverse=True)

    five_ghz = [n for n in networks if n[6]]
    two_4_ghz = [n for n in networks if not n[6]]

    def _print_table(title, rows):
        print(f"=== {title} ===")
        print(
            f"  {'SSID':<35} {'Signal':>6} {'Freq':<10} {'Ch':>4} {'Security':<15} Note"
        )
        print("  " + "-" * 85)
        for ssid, signal, freq, chan, sec, active, _ in rows:
            marker = " <-- YOU" if active else ""
            print(f"  {ssid:<35} {signal:>4}%  {freq:<10} {chan:>3} {sec:<15}{marker}")
        print()

    if five_ghz:
        _print_table("5 GHz (faster, less range)", five_ghz)
    if two_4_ghz:
        _print_table("2.4 GHz (better range, slower)", two_4_ghz)

    cur = [n for n in networks if n[5]]
    best = networks[0] if networks else None
    if cur and best and cur[0][1] < best[1] - 10:
        print(
            f"  >>> STRONGER network available: {best[0]} ({best[1]}% vs {cur[0][1]}%)"
        )
    elif cur:
        print("  >>> Your current signal is among the best available.")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan WiFi networks and recommend the best signal"
    )
    parser.add_argument(
        "--identify",
        action="store_true",
        help="Identify hidden SSIDs by scanning saved preferred networks (slower)",
    )
    args = parser.parse_args()

    system = platform.system()
    if system == "Darwin":
        _macos_scan(identify=args.identify)
    elif system == "Linux":
        _linux_scan()
    else:
        print(f"Unsupported platform: {system}")
        sys.exit(1)


if __name__ == "__main__":
    main()
