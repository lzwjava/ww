import json
import os
import sys
import urllib.parse
import urllib.request


def _get_key():
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        print("Error: GOOGLE_MAPS_API_KEY not set in environment", file=sys.stderr)
        sys.exit(1)
    return key


def _api_get(url, timeout=15):
    """Make a GET request to a Google Maps API endpoint."""
    req = urllib.request.Request(url, headers={"User-Agent": "ww/1.0"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    with resp:
        return json.loads(resp.read().decode("utf-8"))


def _fmt_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    mins = seconds // 60
    if mins < 60:
        return f"{mins}min"
    h, m = divmod(mins, 60)
    return f"{h}h{m}min" if m else f"{h}h"


def _fmt_distance(meters):
    """Format meters into human-readable distance."""
    if meters < 1000:
        return f"{meters}m"
    return f"{meters / 1000:.1f}km"


def _print_json(data):
    """Pretty-print JSON output."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_geocode(args):
    """Geocode an address to coordinates."""
    if not args:
        print("Usage: ww maps geocode <address>")
        print("Example: ww maps geocode '1600 Amphitheatre Parkway, Mountain View, CA'")
        return
    address = " ".join(args)
    key = _get_key()
    url = "https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(
        {"address": address, "key": key}
    )
    data = _api_get(url)
    if data.get("status") != "OK":
        print(f"Error: {data.get('status')} — {data.get('error_message', '')}")
        return
    for i, result in enumerate(data["results"]):
        loc = result["geometry"]["location"]
        print(f"[{i + 1}] {result['formatted_address']}")
        print(f"    Lat: {loc['lat']}, Lng: {loc['lng']}")
        print(f"    Place ID: {result.get('place_id', 'N/A')}")
        types = result.get("types", [])
        if types:
            print(f"    Types: {', '.join(types)}")
        if i < len(data["results"]) - 1:
            print()


def cmd_reverse(args):
    """Reverse geocode coordinates to an address."""
    if not args:
        print("Usage: ww maps reverse <lat,lng>")
        print("Example: ww maps reverse 37.4220,-122.0841")
        return
    key = _get_key()
    latlng = args[0]
    url = "https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(
        {"latlng": latlng, "key": key}
    )
    data = _api_get(url)
    if data.get("status") != "OK":
        print(f"Error: {data.get('status')} — {data.get('error_message', '')}")
        return
    for i, result in enumerate(data["results"]):
        print(f"[{i + 1}] {result['formatted_address']}")
        types = result.get("types", [])
        if types:
            print(f"    Types: {', '.join(types)}")


def cmd_search(args):
    """Text search for places."""
    if not args:
        print("Usage: ww maps search <query> [--near lat,lng] [--radius M]")
        print("Example: ww maps search 'coffee shop near Times Square'")
        return
    key = _get_key()
    query_parts = []
    near = None
    radius = None
    i = 0
    while i < len(args):
        if args[i] == "--near" and i + 1 < len(args):
            near = args[i + 1]
            i += 2
        elif args[i] == "--radius" and i + 1 < len(args):
            radius = args[i + 1]
            i += 2
        else:
            query_parts.append(args[i])
            i += 1

    params = {"query": " ".join(query_parts), "key": key}
    if near:
        params["location"] = near
        params["radius"] = radius or "5000"

    url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        + urllib.parse.urlencode(params)
    )
    data = _api_get(url)
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        print(f"Error: {data.get('status')} — {data.get('error_message', '')}")
        return
    results = data.get("results", [])
    if not results:
        print("No results found.")
        return
    for i, place in enumerate(results):
        loc = place["geometry"]["location"]
        rating = place.get("rating", "N/A")
        reviews = place.get("user_ratings_total", 0)
        status = place.get("business_status", "")
        addr = place.get("formatted_address", "")
        print(f"[{i + 1}] {place['name']}")
        print(f"    Address: {addr}")
        print(f"    Location: {loc['lat']}, {loc['lng']}")
        print(f"    Rating: {rating} ({reviews} reviews)")
        if status:
            print(f"    Status: {status}")
        price = place.get("price_level")
        if price is not None:
            print(f"    Price: {'$' * price}")
        print(f"    Place ID: {place.get('place_id', 'N/A')}")
        if i < len(results) - 1:
            print()


def cmd_nearby(args):
    """Find nearby places by type."""
    if not args:
        print("Usage: ww maps nearby <lat,lng> [radius_m] [type]")
        print("Example: ww maps nearby 37.4220,-122.0841 1000 restaurant")
        print("Common types: restaurant, cafe, hospital, gas_station, bank, pharmacy")
        return
    key = _get_key()
    location = args[0]
    radius = args[1] if len(args) > 1 else "1000"
    place_type = args[2] if len(args) > 2 else ""

    params = {"location": location, "radius": radius, "key": key}
    if place_type:
        params["type"] = place_type

    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        + urllib.parse.urlencode(params)
    )
    data = _api_get(url)
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        print(f"Error: {data.get('status')} — {data.get('error_message', '')}")
        return
    results = data.get("results", [])
    if not results:
        print("No nearby places found.")
        return
    for i, place in enumerate(results):
        loc = place["geometry"]["location"]
        rating = place.get("rating", "N/A")
        reviews = place.get("user_ratings_total", 0)
        print(f"[{i + 1}] {place['name']}")
        print(f"    Vicinity: {place.get('vicinity', 'N/A')}")
        print(f"    Location: {loc['lat']}, {loc['lng']}")
        print(f"    Rating: {rating} ({reviews} reviews)")
        types = place.get("types", [])
        if types:
            print(f"    Types: {', '.join(types[:3])}")
        print(f"    Place ID: {place.get('place_id', 'N/A')}")
        if i < len(results) - 1:
            print()


def cmd_directions(args):
    """Get directions between two points."""
    if len(args) < 2:
        print(
            "Usage: ww maps directions <origin> <dest> [--mode driving|walking|transit|bicycling]"
        )
        print("Example: ww maps directions 'Guangzhou' 'Shenzhen' --mode driving")
        return
    key = _get_key()
    mode = "driving"
    # Parse: everything before --mode is origin/dest splitting
    clean = []
    i = 0
    while i < len(args):
        if args[i] == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
            i += 2
        else:
            clean.append(args[i])
            i += 1

    if len(clean) < 2:
        print("Error: need both origin and destination")
        return

    origin = clean[0]
    destination = clean[1]

    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "key": key,
    }
    url = (
        "https://maps.googleapis.com/maps/api/directions/json?"
        + urllib.parse.urlencode(params)
    )
    data = _api_get(url)
    if data.get("status") != "OK":
        print(f"Error: {data.get('status')} — {data.get('error_message', '')}")
        return
    routes = data.get("routes", [])
    if not routes:
        print("No routes found.")
        return
    for ri, route in enumerate(routes):
        leg = route["legs"][0]
        dist = leg["distance"]
        dur = leg["duration"]
        print(
            f"Route {ri + 1}: {_fmt_distance(dist['value'])}, {_fmt_duration(dur['value'])}"
        )
        print(f"  From: {leg['start_address']}")
        print(f"  To:   {leg['end_address']}")
        print()
        for si, step in enumerate(leg["steps"]):
            instr = step["html_instructions"]
            # Strip HTML tags for terminal
            import re

            instr = re.sub(r"<[^>]+>", " ", instr).strip()
            instr = re.sub(r"\s+", " ", instr)
            s_dist = step["distance"]["value"]
            print(f"  {si + 1}. {instr} ({_fmt_distance(s_dist)})")
        if ri < len(routes) - 1:
            print()


def cmd_place(args):
    """Get details for a place by ID or name."""
    if not args:
        print("Usage: ww maps place <place_id>")
        print("Example: ww maps place ChIJN1t_tDeuEmsRUsoyG83frY4")
        return
    key = _get_key()
    place_id = args[0]
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,price_level,types,url",
        "key": key,
    }
    url = (
        "https://maps.googleapis.com/maps/api/place/details/json?"
        + urllib.parse.urlencode(params)
    )
    data = _api_get(url)
    if data.get("status") != "OK":
        print(f"Error: {data.get('status')} — {data.get('error_message', '')}")
        return
    p = data["result"]
    print(f"Name: {p.get('name', 'N/A')}")
    print(f"Address: {p.get('formatted_address', 'N/A')}")
    phone = p.get("formatted_phone_number")
    if phone:
        print(f"Phone: {phone}")
    website = p.get("website")
    if website:
        print(f"Website: {website}")
    rating = p.get("rating")
    if rating:
        print(f"Rating: {rating} ({p.get('user_ratings_total', 0)} reviews)")
    price = p.get("price_level")
    if price is not None:
        print(f"Price: {'$' * price}")
    types = p.get("types", [])
    if types:
        print(f"Types: {', '.join(types)}")
    hours = p.get("opening_hours")
    if hours:
        print(f"Open now: {'Yes' if hours.get('open_now') else 'No'}")
        for line in hours.get("weekday_text", []):
            print(f"  {line}")
    maps_url = p.get("url")
    if maps_url:
        print(f"Maps: {maps_url}")


def cmd_timezone(args):
    """Get timezone for a location."""
    if not args:
        print("Usage: ww maps timezone <lat,lng>")
        print("Example: ww maps timezone 23.1291,113.2644")
        return
    key = _get_key()
    import time

    parts = args[0].split(",")
    if len(parts) != 2:
        print("Error: format must be lat,lng (e.g. 23.1291,113.2644)")
        return
    params = {
        "location": args[0],
        "timestamp": str(int(time.time())),
        "key": key,
    }
    url = (
        "https://maps.googleapis.com/maps/api/timezone/json?"
        + urllib.parse.urlencode(params)
    )
    data = _api_get(url)
    if data.get("status") != "OK":
        print(f"Error: {data.get('status')} — {data.get('error_message', '')}")
        return
    print(f"Timezone ID: {data['timeZoneId']}")
    print(f"Name: {data['timeZoneName']}")
    offset = data["rawOffset"]
    sign = "+" if offset >= 0 else "-"
    h, m = divmod(abs(offset) // 60, 60)
    print(f"UTC Offset: UTC{sign}{h}:{m:02d}")


def cmd_elevation(args):
    """Get elevation for a location."""
    if not args:
        print("Usage: ww maps elevation <lat,lng>")
        print("Example: ww maps elevation 27.9881,86.9250")
        return
    key = _get_key()
    params = {"locations": args[0], "key": key}
    url = (
        "https://maps.googleapis.com/maps/api/elevation/json?"
        + urllib.parse.urlencode(params)
    )
    data = _api_get(url)
    if data.get("status") != "OK":
        print(f"Error: {data.get('status')} — {data.get('error_message', '')}")
        return
    for r in data["results"]:
        loc = r["location"]
        print(f"Location: {loc['lat']}, {loc['lng']}")
        print(f"Elevation: {r['elevation']:.1f}m")
        print(f"Resolution: {r['resolution']:.1f}m")


def cmd_ip(args):
    """Geocode an IP address's location."""
    if not args:
        print("Usage: ww maps ip <ip_address>")
        print("Example: ww maps ip 8.8.8.8")
        return
    key = _get_key()
    params = {"ip": args[0], "key": key}
    url = (
        "https://www.googleapis.com/geolocation/v1/geolocate?"
        + urllib.parse.urlencode({"key": key})
    )
    # Use the IP-based geolocation is actually a different API,
    # but let's use geocode with ip address lookup via a simpler approach
    # Actually Google doesn't have a direct IP geocode. Use ip-api.com + then geocode
    import urllib.request as ureq

    try:
        ip_url = f"http://ip-api.com/json/{args[0]}"
        req = ureq.Request(ip_url, headers={"User-Agent": "ww/1.0"})
        opener = ureq.build_opener(ureq.ProxyHandler({}))
        resp = opener.open(req, timeout=10)
        ip_data = json.loads(resp.read().decode())
        if ip_data.get("status") != "success":
            print(f"Error: {ip_data.get('message', 'lookup failed')}")
            return
        print(f"IP: {args[0]}")
        print(
            f"Location: {ip_data.get('city', '')}, {ip_data.get('regionName', '')}, {ip_data.get('country', '')}"
        )
        print(f"Coords: {ip_data.get('lat')}, {ip_data.get('lon')}")
        print(f"ISP: {ip_data.get('isp', 'N/A')}")
        print(f"Timezone: {ip_data.get('timezone', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")


def _haversine_km(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance in km between two coordinates."""
    import math

    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _cmd_trip_report(dest_name, dest_addr, dest_lat, dest_lng, origin_label, args):
    """Shared logic for office/home trip reports."""
    key = _get_key()
    origin = args[0] if args else os.environ.get(origin_label, "").strip()
    if not origin:
        print(f"Usage: ww maps <office|home> [lat,lng]")
        print(f"Or set {origin_label} in .env to use without arguments.")
        return

    origin_parts = origin.split(",")
    if len(origin_parts) != 2:
        print("Error: format must be lat,lng (e.g. 22.838889,114.498969)")
        return
    try:
        olat, olng = float(origin_parts[0]), float(origin_parts[1])
    except ValueError:
        print("Error: invalid coordinates")
        return

    # 1. Reverse geocode origin
    rev_url = "https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(
        {"latlng": origin, "key": key}
    )
    rev_data = _api_get(rev_url)
    origin_addr = origin
    if rev_data.get("status") == "OK" and rev_data.get("results"):
        origin_addr = rev_data["results"][0].get("formatted_address", origin)

    # 2. Get driving directions
    dest = f"{dest_lat},{dest_lng}"
    dir_url = "https://maps.googleapis.com/maps/api/directions/json?" + urllib.parse.urlencode(
        {"origin": origin, "destination": dest, "mode": "driving", "key": key}
    )
    dir_data = _api_get(dir_url)
    if dir_data.get("status") != "OK":
        print(f"Error: {dir_data.get('status')} — {dir_data.get('error_message', '')}")
        return
    routes = dir_data.get("routes", [])
    if not routes:
        print("No routes found.")
        return

    leg = routes[0]["legs"][0]
    route_dist = leg["distance"]["value"]
    route_dur = leg["duration"]["value"]

    # 3. Transit
    transit_url = "https://maps.googleapis.com/maps/api/directions/json?" + urllib.parse.urlencode(
        {"origin": origin, "destination": dest, "mode": "transit", "key": key}
    )
    transit_data = _api_get(transit_url)
    transit_dur = transit_dist = None
    if transit_data.get("status") == "OK" and transit_data.get("routes"):
        tleg = transit_data["routes"][0]["legs"][0]
        transit_dur = tleg["duration"]["value"]
        transit_dist = tleg["distance"]["value"]

    # 4. Straight-line distance
    straight_km = _haversine_km(olat, olng, dest_lat, dest_lng)

    # 5. Print report
    import re

    label = dest_name.split("(")[0].strip()
    print("=" * 56)
    print(f"  YOUR LOCATION -> {label.upper()}")
    print("=" * 56)
    print()
    print(f"FROM: {origin_addr}")
    print(f"TO:   {dest_name}")
    if dest_addr:
        print(f"      {dest_addr}")
    print()

    print("-" * 56)
    print("  STRAIGHT-LINE (direct) DISTANCE")
    print("-" * 56)
    print(f"  {straight_km:.1f} km ({straight_km * 1000:.0f} m)")
    print()

    print("-" * 56)
    print("  DRIVING ROUTE")
    print("-" * 56)
    print(f"  Distance:  {_fmt_distance(route_dist)}")
    print(f"  Est. time: {_fmt_duration(route_dur)}  (without traffic)")
    print()

    if transit_dur is not None:
        print("-" * 56)
        print("  TRANSIT (public transport)")
        print("-" * 56)
        print(f"  Distance:  {_fmt_distance(transit_dist)}")
        print(f"  Est. time: {_fmt_duration(transit_dur)}")
        print()

    # Route overview
    highways = []
    for step in leg.get("steps", []):
        instr = re.sub(r"<[^>]+>", " ", step.get("html_instructions", ""))
        instr = re.sub(r"\s+", " ", instr).strip()
        for m in re.findall(r"[A-Z]\d+[/\w]*|[\u4e00-\u9fff]+(?:高速|快速|大道)", instr):
            if m not in highways:
                highways.append(m)

    print("-" * 56)
    print("  ROUTE OVERVIEW")
    print("-" * 56)
    if highways:
        print(f"  {' -> '.join(highways)}")
    steps = leg.get("steps", [])
    print()
    for si, step in enumerate(steps):
        instr = re.sub(r"<[^>]+>", " ", step.get("html_instructions", ""))
        instr = re.sub(r"\s+", " ", instr).strip()
        sd = step["distance"]["value"]
        if si < 5 or si >= len(steps) - 3:
            print(f"  {si + 1}. {instr} ({_fmt_distance(sd)})")
        elif si == 5:
            print(f"  ... ({len(steps) - 6} more steps) ...")
    print()

    ratio = route_dist / (straight_km * 1000) if straight_km > 0 else 0
    print("-" * 56)
    print("  SUMMARY")
    print("-" * 56)
    print(f"  Driving distance / straight-line = {ratio:.2f}x")
    print("=" * 56)


def cmd_office(args):
    """Show distance and driving time to OneLink office (万菱汇).

    Usage: ww maps office [lat,lng]
    Example: ww maps office 22.838889,114.498969
             ww maps office          # uses OFFICE_LAT_LNG from .env
    """
    _cmd_trip_report(
        "Wan Ling International Center (万菱国际中心)",
        "Tianhe Rd 230-232, Tianhe, Guangzhou",
        23.1327559, 113.3290462,
        "OFFICE_LAT_LNG", args,
    )


def cmd_home(args):
    """Show distance and driving time to home (侨建御溪谷).

    Usage: ww maps home [lat,lng]
    Example: ww maps home 22.838889,114.498969
             ww maps home            # uses HOME_LAT_LNG from .env
    """
    _cmd_trip_report(
        "Qiaojian Yu Xigu Phase 1 (侨建御溪谷一期)",
        "Zhongxinzhen Fengguang Rd 399, Zengcheng, Guangzhou",
        23.283489, 113.607298,
        "HOME_LAT_LNG", args,
    )


def _parse_maps_url(url):
    """Parse a maps URL and return (lat, lng, name, address) or None."""
    import re
    from urllib.parse import urlparse, parse_qs, unquote

    url = url.strip()

    # Apple Maps: https://maps.apple.com/place?coordinate=23.28,113.60&name=...
    if "maps.apple.com" in url:
        qs = parse_qs(urlparse(url).query)
        coord = qs.get("coordinate", [""])[0]
        name = unquote(qs.get("name", [""])[0])
        address = unquote(qs.get("address", [""])[0])
        if coord:
            parts = coord.split(",")
            if len(parts) == 2:
                return float(parts[0]), float(parts[1]), name, address

    # Google Maps: https://maps.google.com/?q=23.28,113.60 or @23.28,113.60
    if "google.com/maps" in url or "goo.gl" in url:
        # Try @lat,lng
        m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if m:
            return float(m.group(1)), float(m.group(2)), "", ""
        # Try q=lat,lng
        qs = parse_qs(urlparse(url).query)
        q = qs.get("q", [""])[0]
        if q:
            parts = q.split(",")
            if len(parts) >= 2:
                try:
                    return float(parts[0]), float(parts[1]), "", ""
                except ValueError:
                    pass

    # Generic URL with lat/lng query params
    qs = parse_qs(urlparse(url).query)
    for key in ("coordinate", "ll", "sll"):
        val = qs.get(key, [""])[0]
        if val:
            parts = val.split(",")
            if len(parts) >= 2:
                try:
                    return float(parts[0]), float(parts[1]), "", ""
                except ValueError:
                    pass

    return None


def cmd_location(args):
    """Show distance/time to a maps URL from clipboard or argument.

    Usage: ww maps location --paste [origin_lat,lng]
           ww maps location <maps_url> [origin_lat,lng]

    Reads destination from clipboard (--paste) or a maps URL argument.
    Parses Apple Maps / Google Maps URLs for coordinates.
    Origin defaults to OFFICE_LAT_LNG from .env.
    """
    import subprocess

    if not args:
        print("Usage: ww maps location --paste [origin_lat,lng]")
        print("       ww maps location <maps_url> [origin_lat,lng]")
        print()
        print("Reads a maps URL (Apple Maps, Google Maps) and shows trip report.")
        print("Use --paste to read from clipboard, or pass the URL directly.")
        return

    origin = None
    maps_url = None

    if args[0] == "--paste":
        # Read clipboard
        try:
            result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
            maps_url = result.stdout.strip()
        except Exception:
            # Linux fallback
            try:
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    capture_output=True, text=True, timeout=5,
                )
                maps_url = result.stdout.strip()
            except Exception:
                print("Error: could not read clipboard (pbpaste/xclip not available)")
                return
        if not maps_url:
            print("Error: clipboard is empty")
            return
        origin = args[1] if len(args) > 1 else None
    else:
        maps_url = args[0]
        origin = args[1] if len(args) > 1 else None

    parsed = _parse_maps_url(maps_url)
    if not parsed:
        print(f"Error: could not parse coordinates from URL:")
        print(f"  {maps_url[:120]}")
        print()
        print("Supported: Apple Maps, Google Maps URLs with coordinates.")
        return

    dest_lat, dest_lng, name, address = parsed
    dest_name = name or f"Location ({dest_lat}, {dest_lng})"
    dest_addr = address or ""

    # Build args for _cmd_trip_report: [origin] or []
    trip_args = [origin] if origin else []
    _cmd_trip_report(dest_name, dest_addr, dest_lat, dest_lng, "OFFICE_LAT_LNG", trip_args)


def cmd_test(_args):
    """Test the Google Maps API key with a simple geocode."""
    key = _get_key()
    print(f"API Key: {key[:8]}...{key[-4:]}")
    print()

    # Test geocoding
    print("--- Geocoding API ---")
    url = "https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(
        {"address": "Guangzhou", "key": key}
    )
    data = _api_get(url)
    if data.get("status") == "OK":
        result = data["results"][0]
        loc = result["geometry"]["location"]
        print(f"  OK: {result['formatted_address']}")
        print(f"  Coords: {loc['lat']}, {loc['lng']}")
    else:
        print(f"  FAIL: {data.get('status')} — {data.get('error_message', '')}")

    # Test timezone
    print()
    print("--- Time Zone API ---")
    import time

    tz_url = (
        "https://maps.googleapis.com/maps/api/timezone/json?"
        + urllib.parse.urlencode(
            {
                "location": "23.1291,113.2644",
                "timestamp": str(int(time.time())),
                "key": key,
            }
        )
    )
    data = _api_get(tz_url)
    if data.get("status") == "OK":
        print(f"  OK: {data['timeZoneId']} ({data['timeZoneName']})")
    else:
        print(f"  FAIL: {data.get('status')} — {data.get('error_message', '')}")

    # Test places text search
    print()
    print("--- Places API (Text Search) ---")
    ps_url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        + urllib.parse.urlencode(
            {
                "query": "coffee shop",
                "location": "23.1291,113.2644",
                "radius": "1000",
                "key": key,
            }
        )
    )
    data = _api_get(ps_url)
    if data.get("status") in ("OK", "ZERO_RESULTS"):
        count = len(data.get("results", []))
        print(f"  OK: {count} results for 'coffee shop' near Guangzhou")
    else:
        print(f"  FAIL: {data.get('status')} — {data.get('error_message', '')}")

    # Test elevation
    print()
    print("--- Elevation API ---")
    elev_url = (
        "https://maps.googleapis.com/maps/api/elevation/json?"
        + urllib.parse.urlencode({"locations": "23.1291,113.2644", "key": key})
    )
    data = _api_get(elev_url)
    if data.get("status") == "OK":
        elev = data["results"][0]["elevation"]
        print(f"  OK: Guangzhou elevation = {elev:.1f}m")
    else:
        print(f"  FAIL: {data.get('status')} — {data.get('error_message', '')}")

    # Test directions
    print()
    print("--- Directions API ---")
    dir_url = (
        "https://maps.googleapis.com/maps/api/directions/json?"
        + urllib.parse.urlencode(
            {
                "origin": "Guangzhou",
                "destination": "Shenzhen",
                "mode": "driving",
                "key": key,
            }
        )
    )
    data = _api_get(dir_url)
    if data.get("status") == "OK":
        leg = data["routes"][0]["legs"][0]
        print(
            f"  OK: Guangzhou → Shenzhen: {_fmt_distance(leg['distance']['value'])}, {_fmt_duration(leg['duration']['value'])}"
        )
    else:
        print(f"  FAIL: {data.get('status')} — {data.get('error_message', '')}")

    print()
    print("All tests complete.")


COMMANDS = {
    "geocode": cmd_geocode,
    "reverse": cmd_reverse,
    "search": cmd_search,
    "nearby": cmd_nearby,
    "directions": cmd_directions,
    "home": cmd_home,
    "location": cmd_location,
    "office": cmd_office,
    "place": cmd_place,
    "timezone": cmd_timezone,
    "elevation": cmd_elevation,
    "ip": cmd_ip,
    "test": cmd_test,
}


def _print_help():
    print("Usage: ww maps <command> [args]")
    print()
    print("Commands:")
    print("  directions <from> <to> [--mode M]       Route directions")
    print("  elevation <lat,lng>            Elevation for location")
    print("  geocode <address>              Address to lat/lng")
    print("  home [lat,lng]                 Distance/time to home")
    print("  ip <address>                   Geolocate an IP address")
    print("  location --paste [origin]      Trip report from clipboard URL")
    print("  nearby <lat,lng> [radius] [type]        Nearby places")
    print("  office [lat,lng]               Distance/time to OneLink office")
    print("  place <place_id>               Place details")
    print("  reverse <lat,lng>              Lat/lng to address")
    print("  search <query> [--near L] [--radius M]  Places text search")
    print("  test                           Test all Google Maps APIs")
    print("  timezone <lat,lng>             Timezone for location")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        _print_help()
        return
    cmd = args[0]
    rest = args[1:]
    fn = COMMANDS.get(cmd)
    if fn is None:
        print(f"Unknown command: {cmd}")
        _print_help()
        return
    fn(rest)
