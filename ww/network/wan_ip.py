"""Check real WAN IP (bypasses proxy) and track changes across router restarts."""

import json
import os
import sys
import urllib.request
from datetime import datetime

LOGFILE = os.path.expanduser("~/.ww/wan_ip.log")


def _fetch_ip_unproxied():
    """Fetch real WAN IP by bypassing any proxy env vars."""
    # Save and remove proxy env vars
    proxy_keys = [
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "all_proxy",
        "FTP_PROXY",
        "ftp_proxy",
        "GLOBAL_PROXY",
    ]
    saved = {}
    for k in proxy_keys:
        if k in os.environ:
            saved[k] = os.environ.pop(k)

    try:
        # ip.sb returns plain text IP
        req = urllib.request.Request("http://ip.sb", headers={"User-Agent": "curl/8.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            ip = resp.read().decode().strip()
    except Exception:
        ip = None
    finally:
        # Restore proxy env vars
        os.environ.update(saved)

    return ip


def _fetch_ipinfo(ip):
    """Fetch IP geolocation info from ipinfo.io."""
    proxy_keys = [
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "all_proxy",
        "FTP_PROXY",
        "ftp_proxy",
        "GLOBAL_PROXY",
    ]
    saved = {}
    for k in proxy_keys:
        if k in os.environ:
            saved[k] = os.environ.pop(k)

    try:
        req = urllib.request.Request(
            f"https://ipinfo.io/{ip}/json",
            headers={"User-Agent": "curl/8.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        data = {}
    finally:
        os.environ.update(saved)

    return data


def _fetch_isp_cn(ip):
    """Fetch Chinese ISP name from myip.ipip.net."""
    proxy_keys = [
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "all_proxy",
        "FTP_PROXY",
        "ftp_proxy",
        "GLOBAL_PROXY",
    ]
    saved = {}
    for k in proxy_keys:
        if k in os.environ:
            saved[k] = os.environ.pop(k)

    try:
        req = urllib.request.Request(
            "http://myip.ipip.net",
            headers={"User-Agent": "curl/8.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode()
        # Format: "当前 IP：x.x.x.x  来自于：中国 广东 广州  电信"
        if "来自于：" in text:
            return text.split("来自于：")[1].strip()
    except Exception:
        pass
    finally:
        os.environ.update(saved)

    return None


def _read_last_ip():
    """Read the last logged IP from the log file."""
    if not os.path.exists(LOGFILE):
        return None
    try:
        with open(LOGFILE) as f:
            lines = f.readlines()
        if lines:
            # Format: [2026-06-10 15:30:00] 14.19.55.197
            return lines[-1].strip().split()[-1]
    except Exception:
        pass
    return None


def _log_ip(ip):
    """Append IP with timestamp to log file."""
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGFILE, "a") as f:
        f.write(f"[{ts}] {ip}\n")


def main():
    show_log = "--log" in sys.argv

    ip = _fetch_ip_unproxied()
    if not ip:
        print("ERROR: Could not retrieve WAN IP (direct connection failed)")
        sys.exit(1)

    info = _fetch_ipinfo(ip)
    org = info.get("org", "")
    city = info.get("city", "")
    region = info.get("region", "")
    country = info.get("country", "")

    # Try Chinese ISP source for better labels (e.g. "中国 广东 广州  电信")
    cn_info = _fetch_isp_cn(ip)

    if cn_info:
        # Parse: "中国 广东 广州  电信" → location="中国 广东 广州", isp="电信"
        parts = cn_info.split()
        if len(parts) >= 2:
            isp = parts[-1]  # Last token is ISP (电信/联通/移动)
            location = " ".join(parts[:-1])
        else:
            isp = cn_info
            location = ""
    else:
        # Fallback to ipinfo.io English data
        isp = org
        location_parts = [p for p in [country, region, city] if p]
        location = " ".join(location_parts) if location_parts else "Unknown"

    # Check for IP change
    last_ip = _read_last_ip()
    changed = last_ip is not None and last_ip != ip

    # Display
    print()
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"    IP:       {ip}")
    print(f"    ISP:      {isp}")
    print(f"    Location: {location}")
    if last_ip:
        if changed:
            print(f"    Changed:  {last_ip} → {ip}")
        else:
            print("    Status:   Same as last check")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # Log
    _log_ip(ip)

    # Show full log if requested
    if show_log:
        print(f"  Log: {LOGFILE}")
        print()
        if os.path.exists(LOGFILE):
            with open(LOGFILE) as f:
                for line in f:
                    print(f"    {line.rstrip()}")
            print()
