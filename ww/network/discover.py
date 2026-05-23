import subprocess
import socket
import re


# Common MAC OUI prefixes -> vendor
OUI_DB = {
    # Apple
    "3C:6A:48": "Apple",
    "68:C6:AC": "Apple",
    "88:E9:FE": "Apple",
    "A4:83:E7": "Apple",
    "DC:A6:32": "Apple",
    "F0:18:98": "Apple",
    "AC:DE:48": "Apple",
    "38:F9:D3": "Apple",
    "C8:69:CD": "Apple",
    "14:7D:DA": "Apple",
    "78:7B:8A": "Apple",
    "E0:B9:BA": "Apple",
    "8C:85:90": "Apple",
    "F8:FF:C2": "Apple",
    "A8:5C:2C": "Apple",
    "64:A5:C3": "Apple",
    "70:56:81": "Apple",
    "04:0C:CE": "Apple",
    "B8:E8:56": "Apple",
    "C4:B3:01": "Apple",
    "FC:E9:98": "Apple",
    "84:89:AD": "Apple",
    "5C:F7:E6": "Apple",
    "D0:81:7A": "Apple",
    "A0:D7:95": "Apple",
    "18:E7:F4": "Apple",
    "6C:96:CF": "Apple",
    "80:BE:05": "Apple",
    "A4:B1:C1": "Apple",
    "FC:FC:48": "Apple",
    "F0:72:EA": "Apple",
    "3C:2E:FF": "Apple",
    "C8:89:F3": "Apple",
    "00:1B:63": "Apple",
    "98:01:A7": "Apple",
    "B0:BE:76": "Apple",
    # TP-Link
    "50:C7:BF": "TP-Link",
    "C0:06:C3": "TP-Link",
    "68:AB:BC": "TP-Link",
    "E8:48:B8": "TP-Link",
    "C0:25:E9": "TP-Link",
    # Xiaomi
    "78:11:DC": "Xiaomi",
    "28:6C:07": "Xiaomi",
    "64:B4:73": "Xiaomi",
    "F8:A4:5F": "Xiaomi",
    "58:41:20": "Xiaomi",
    # Huawei
    "48:46:C1": "Huawei",
    "00:E0:FC": "Huawei",
    "88:28:B3": "Huawei",
    "CC:A2:23": "Huawei",
    "E4:68:A3": "Huawei",
    # Samsung
    "00:21:19": "Samsung",
    "8C:71:F8": "Samsung",
    "C0:97:27": "Samsung",
    "E4:7C:F9": "Samsung",
    # Intel
    "00:1E:65": "Intel",
    "A4:4C:C8": "Intel",
    "F8:63:3F": "Intel",
    # Raspberry Pi
    "B8:27:EB": "Raspberry Pi",
    "E4:5F:01": "Raspberry Pi",
    # Amazon (Echo, Fire TV, etc.)
    "68:54:FD": "Amazon",
    "F0:F0:A4": "Amazon",
    "74:C2:46": "Amazon",
    "A0:02:DC": "Amazon",
    # Sonos
    "48:0E:EC": "Sonos",
    "5C:AA:FD": "Sonos",
    # Google (Nest, Chromecast)
    "54:60:09": "Google",
    "F4:F5:D8": "Google",
    "30:FD:38": "Google",
    # Dell
    "F8:DB:88": "Dell",
    "18:03:73": "Dell",
    "B0:83:FE": "Dell",
    # Lenovo
    "68:F7:28": "Lenovo",
    "90:78:41": "Lenovo",
    # ESP32 / Espressif (IoT)
    "24:6F:28": "Espressif",
    "30:AE:A4": "Espressif",
    "A4:CF:12": "Espressif",
    "C4:5B:BE": "Espressif",
}

# Common ports to fingerprint device type
PROBE_PORTS = [22, 80, 443, 5353, 5900, 7000, 8080, 62078]


def get_local_ip():
    """Get the local IP address by connecting to a public DNS (no actual traffic sent)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def get_subnet(ip):
    """Derive /24 subnet from an IP address."""
    parts = ip.split(".")
    return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"


def parse_arp_table():
    """Parse the system ARP table. Returns list of (ip, hostname, mac)."""
    entries = []
    try:
        # -n = numeric (skip DNS), avoids timeouts on unresolvable hostnames
        output = subprocess.check_output(
            ["arp", "-an"], text=True, timeout=15, stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return entries

    for line in output.splitlines():
        # macOS format: hostname (ip) at mac [ether] on en0
        # Linux format: hostname (ip) at mac [ether] on iface
        m = re.search(r"\(([\d.]+)\)\s+at\s+([\w:]+)", line)
        if m:
            ip = m.group(1)
            mac = m.group(2).upper()
            if mac == "(INCOMPLETE)" or mac == "FF:FF:FF:FF:FF:FF":
                continue
            # Skip multicast addresses (224.0.0.0/4)
            first_octet = int(ip.split(".")[0])
            if first_octet >= 224:
                continue
            # Extract hostname from line
            hostname = line.split("(")[0].strip().rstrip('"').lstrip('"')
            if hostname == "?":
                hostname = ""
            entries.append((ip, hostname, mac))
    return entries


def lookup_vendor(mac):
    """Look up vendor from MAC OUI prefix."""
    prefix = mac[:8].upper()
    return OUI_DB.get(prefix, "")


def resolve_hostname(ip):
    """Try reverse DNS resolution."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return ""


def probe_ports(ip, ports=None, timeout=0.5):
    """Check which ports are open on a host. Returns list of open port numbers."""
    if ports is None:
        ports = PROBE_PORTS
    open_ports = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except OSError:
            pass
    return open_ports


def guess_device_type(vendor, hostname, open_ports):
    """Guess device type from vendor, hostname, and open ports."""
    hostname_lower = hostname.lower()

    # Check hostname hints
    if any(k in hostname_lower for k in ("iphone", "ipad", "phone")):
        return "iPhone/iPad"
    if "macbook" in hostname_lower or "imac" in hostname_lower:
        return "Mac"
    if "router" in hostname_lower or "gateway" in hostname_lower:
        return "Router"
    if "printer" in hostname_lower:
        return "Printer"

    # Check vendor + port combinations
    if vendor == "Apple":
        if 7000 in open_ports:
            return "Apple TV/HomePod"
        if 62078 in open_ports:
            return "iPhone/iPad"
        if 5900 in open_ports:
            return "Mac (Screen Sharing)"
        if 22 in open_ports:
            return "Mac (SSH)"
        if 5353 in open_ports:
            return "Apple device"
        return "Apple device"

    if vendor in ("Xiaomi", "Huawei"):
        if 80 in open_ports or 443 in open_ports:
            return "IoT/Phone"
        return "Phone/IoT"

    if vendor in ("TP-Link",):
        return "Router/Switch"

    if vendor in ("Espressif",):
        return "ESP32/IoT"

    if vendor == "Raspberry Pi":
        if 22 in open_ports:
            return "Raspberry Pi (SSH)"
        return "Raspberry Pi"

    if vendor in ("Amazon",):
        return "Echo/Fire TV"

    if vendor in ("Sonos",):
        return "Sonos Speaker"

    if vendor in ("Google",):
        return "Nest/Chromecast"

    if vendor in ("Samsung",):
        return "Samsung device"

    if vendor in ("Dell", "Lenovo"):
        return "PC/Laptop"

    if vendor == "Intel":
        return "PC (Intel NIC)"

    # No vendor match — try ports alone
    if 5353 in open_ports:
        return "mDNS device"
    if 22 in open_ports and 80 not in open_ports:
        return "Linux/Server"
    if 80 in open_ports or 443 in open_ports:
        return "Web device"

    return ""


def port_label(port):
    """Map well-known port numbers to labels."""
    labels = {
        22: "SSH",
        80: "HTTP",
        443: "HTTPS",
        5353: "mDNS",
        5900: "VNC",
        7000: "AirPlay",
        8080: "HTTP-Alt",
        62078: "iPhoneSync",
    }
    return labels.get(port, str(port))


def discover_network(subnet=None, resolve=False, probe=False):
    """
    Discover devices on the local network.

    Returns list of dicts with keys: ip, hostname, mac, vendor, device_type, ports
    """
    local_ip = get_local_ip()
    if not local_ip:
        print("[error] Could not determine local IP address")
        return []

    if not subnet:
        subnet = get_subnet(local_ip)

    print(f"Local IP: {local_ip}")
    print(f"Scanning: {subnet}")
    print("")

    # Phase 1: ARP table
    entries = parse_arp_table()
    if not entries:
        print("[warn] ARP table empty — try pinging some hosts first:")
        print(f"  ping -c 1 -W 100 {local_ip.rsplit('.', 1)[0]}.1")
        return []

    # Phase 2: Enrich with vendor, hostname, ports
    devices = []
    for ip, arp_hostname, mac in entries:
        vendor = lookup_vendor(mac)

        hostname = arp_hostname
        if resolve and not hostname:
            hostname = resolve_hostname(ip)

        open_ports = []
        device_type = ""
        if probe:
            open_ports = probe_ports(ip)
            device_type = guess_device_type(vendor, hostname, open_ports)
        elif vendor:
            device_type = guess_device_type(vendor, hostname, [])

        devices.append(
            {
                "ip": ip,
                "hostname": hostname,
                "mac": mac,
                "vendor": vendor,
                "device_type": device_type,
                "ports": open_ports,
            }
        )

    # Sort by IP
    devices.sort(key=lambda d: tuple(int(p) for p in d["ip"].split(".")))
    return devices


def print_table(devices, probe=False):
    """Print devices in a formatted table."""
    if not devices:
        print("No devices found.")
        return

    # Compute column widths
    ip_w = max(len(d["ip"]) for d in devices)
    ip_w = max(ip_w, 2)  # "IP"

    mac_w = 17  # XX:XX:XX:XX:XX:XX

    host_w = max((len(d["hostname"]) for d in devices), default=0)
    host_w = max(host_w, 8)  # "Hostname"

    vendor_w = max((len(d["vendor"]) for d in devices), default=0)
    vendor_w = max(vendor_w, 6)  # "Vendor"

    type_w = max((len(d["device_type"]) for d in devices), default=0)
    type_w = max(type_w, 4)  # "Type"

    # Header
    header = f"  {'IP':<{ip_w}}  {'MAC':<{mac_w}}  {'Hostname':<{host_w}}  {'Vendor':<{vendor_w}}"
    if probe:
        header += f"  {'Type':<{type_w}}  Ports"
    print(header)

    sep = (
        "  "
        + "─" * ip_w
        + "  "
        + "─" * mac_w
        + "  "
        + "─" * host_w
        + "  "
        + "─" * vendor_w
    )
    if probe:
        sep += "  " + "─" * type_w + "  " + "─" * 20
    print(sep)

    # Rows
    for d in devices:
        row = f"  {d['ip']:<{ip_w}}  {d['mac']:<{mac_w}}  {d['hostname']:<{host_w}}  {d['vendor']:<{vendor_w}}"
        if probe:
            ports_str = (
                ", ".join(port_label(p) for p in d["ports"]) if d["ports"] else "--"
            )
            row += f"  {d['device_type']:<{type_w}}  {ports_str}"
        print(row)

    print("")
    print(f"{len(devices)} device(s) found.")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Discover devices on the local network via ARP table."
    )
    parser.add_argument(
        "-s",
        "--subnet",
        help="Subnet to scan (default: auto-detect /24 from local IP)",
    )
    parser.add_argument(
        "-r",
        "--resolve",
        action="store_true",
        help="Resolve hostnames via reverse DNS (slower)",
    )
    parser.add_argument(
        "-p",
        "--probe",
        action="store_true",
        help="Probe common ports and guess device types (slower)",
    )
    args = parser.parse_args()

    devices = discover_network(
        subnet=args.subnet,
        resolve=args.resolve,
        probe=args.probe,
    )
    print_table(devices, probe=args.probe)


if __name__ == "__main__":
    main()
