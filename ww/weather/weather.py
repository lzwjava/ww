import os
import sys
import urllib.request
import urllib.parse
import json
import subprocess


def _fetch(url, accept="text/plain", no_proxy=False, timeout=10):
    req = urllib.request.Request(
        url, headers={"Accept": accept, "User-Agent": "curl/8.0"}
    )
    if no_proxy:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        resp = opener.open(req, timeout=timeout)
    else:
        resp = urllib.request.urlopen(req, timeout=timeout)
    with resp:
        return resp.read().decode("utf-8")


def _detect_location():
    """Get real location bypassing proxy. Returns (coords, city, isp, source)."""
    try:
        raw = _fetch(
            "http://ip-api.com/json/", accept="application/json", no_proxy=True
        )
        data = json.loads(raw)
        if data.get("status") == "success":
            city = data.get("city", "")
            coords = f"{data['lat']},{data['lon']}" if data.get("lat") else ""
            isp = f"{data.get('isp', '')} ({data.get('org', '')})"
            return coords, city, isp, "ip-api.com"
    except Exception:
        pass

    try:
        raw = _fetch("https://ipinfo.io/json", accept="application/json", no_proxy=True)
        data = json.loads(raw)
        return (
            data.get("loc", ""),
            data.get("city", ""),
            data.get("org", ""),
            "ipinfo.io",
        )
    except Exception:
        pass

    return "", "", "", ""


def _get_network_info():
    """Collect local network details."""
    info = {}
    try:
        out = (
            subprocess.check_output(
                ["ipconfig", "getifaddr", "en0"], stderr=subprocess.DEVNULL, timeout=3
            )
            .decode()
            .strip()
        )
        info["local_ip"] = out
    except Exception:
        info["local_ip"] = "N/A"

    try:
        out = subprocess.check_output(
            ["netstat", "-rn"], stderr=subprocess.DEVNULL, timeout=3
        ).decode()
        for line in out.splitlines():
            if line.startswith("default"):
                parts = line.split()
                if len(parts) >= 2:
                    info["gateway"] = parts[1]
                    break
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["system_profiler", "SPAirPortDataType"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode()
        for line in out.splitlines():
            s = line.strip()
            if s.startswith("Channel:"):
                info["wifi_channel"] = s.split(":", 1)[1].strip()
            elif s.startswith("Signal / Noise:"):
                info["wifi_signal"] = s.split(":", 1)[1].strip()
            elif s.startswith("PHY Mode:"):
                info["wifi_phy"] = s.split(":", 1)[1].strip()
    except Exception:
        pass

    return info


def _is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _weather_icon(desc):
    d = desc.lower()
    if "sun" in d or "clear" in d:
        return "☀️"
    if "partly" in d:
        return "⛅"
    if "cloud" in d or "overcast" in d:
        return "☁️"
    if "rain" in d or "drizzle" in d or "shower" in d:
        return "🌧️"
    if "thunder" in d:
        return "⛈️"
    if "snow" in d:
        return "❄️"
    if "fog" in d or "mist" in d:
        return "🌫️"
    return "🌤️"


def _format_hour(time_str):
    """Convert '0' -> '00:00', '1200' -> '12:00'."""
    t = time_str.zfill(4)
    return f"{t[:2]}:{t[2:]}"


def _print_compact(data, days):
    """Print compact weather from JSON data."""
    area = data.get("nearest_area", [{}])[0]
    city = ", ".join(a.get("value", "") for a in area.get("areaName", []))

    cc = data.get("current_condition", [{}])[0]
    desc = cc.get("weatherDesc", [{}])[0].get("value", "")
    icon = _weather_icon(desc)
    temp_c = cc.get("temp_C", "?")
    feels = cc.get("FeelsLikeC", "?")
    humidity = cc.get("humidity", "?")
    wind = cc.get("windspeedKmph", "?")
    wind_dir = cc.get("winddir16Point", "")

    print(f"Weather: {city}")
    print(
        f"Now: {icon} {desc}, {temp_c}°C (feels {feels}°C), humidity {humidity}%, wind {wind}km/h {wind_dir}"
    )

    for i, day in enumerate(data.get("weather", [])[:days]):
        date = day.get("date", "")
        max_t = day.get("maxtempC", "?")
        min_t = day.get("mintempC", "?")

        if i == 0:
            print(f"\nToday ({date}): {min_t}°C ~ {max_t}°C")
        else:
            weekday = _weekday(date)
            print(f"\n{weekday} ({date}): {min_t}°C ~ {max_t}°C")

        # Show key hours: 06, 09, 12, 15, 18, 21
        key_hours = ["0600", "0900", "1200", "1500", "1800", "2100"]
        parts = []
        for h in day.get("hourly", []):
            t = h.get("time", "").zfill(4)
            if t in key_hours:
                hr = _format_hour(t)
                t_c = h.get("tempC", "?")
                h_desc = h.get("weatherDesc", [{}])[0].get("value", "")
                h_icon = _weather_icon(h_desc)
                parts.append(f"{hr} {h_icon}{t_c}°")
        print("  " + "  ".join(parts))


def _weekday(date_str):
    """Return weekday name from YYYY-MM-DD."""
    from datetime import datetime

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%A")
    except Exception:
        return ""


def main():
    args = sys.argv[1:]
    flags = [a for a in args if a.startswith("-")]
    positional = [a for a in args if not a.startswith("-")]

    oneline = "--oneline" in flags
    as_json = "--json" in flags
    show_detail = "--detail" in flags

    # Parse: ww weather [N] [city] or ww weather [city] [N]
    days = 1
    city_arg = ""
    for p in positional:
        if _is_int(p):
            days = max(1, min(int(p), 3))
        else:
            city_arg = p

    # Auto-detect location if no city given
    if city_arg:
        location = city_arg
    else:
        coords, city, isp, source = _detect_location()
        location = city or coords or os.environ.get("WW_WEATHER_CITY", "")

        if show_detail:
            net = _get_network_info()
            print(f"=== Location ({source}) ===")
            print(f"  City     : {city or 'N/A'}")
            print(f"  ISP      : {isp or 'N/A'}")
            print(f"  Local IP : {net.get('local_ip', 'N/A')}")
            print(f"  Gateway  : {net.get('gateway', 'N/A')}")
            if net.get("wifi_channel"):
                print(
                    f"  WiFi     : {net.get('wifi_phy', '')}, Ch {net.get('wifi_channel', '')}"
                )
            if net.get("wifi_signal"):
                print(f"  Signal   : {net.get('wifi_signal', '')}")
            print()

    loc = urllib.parse.quote(location)

    if as_json:
        url = f"https://wttr.in/{loc}?format=j1"
        raw = _fetch(url, accept="application/json")
        data = json.loads(raw)
        current = data.get("current_condition", [{}])[0]
        area = data.get("nearest_area", [{}])[0]
        result = {
            "location": ", ".join(a.get("value", "") for a in area.get("areaName", [])),
            "temp_c": current.get("temp_C"),
            "feels_like_c": current.get("FeelsLikeC"),
            "humidity": current.get("humidity"),
            "wind_kmph": current.get("windspeedKmph"),
            "description": current.get("weatherDesc", [{}])[0].get("value", ""),
        }
        print(json.dumps(result, indent=2))
        return

    if oneline:
        url = f"https://wttr.in/{loc}?format=%l:+%c+%t"
        print(_fetch(url).strip())
        return

    # Compact formatted view
    url = f"https://wttr.in/{loc}?format=j1"
    raw = _fetch(url, accept="application/json")
    data = json.loads(raw)
    _print_compact(data, days)
