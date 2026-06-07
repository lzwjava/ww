"""ww network physical-speed — Estimate vehicle speed using EM Doppler shift.

Measures car speed by observing the Doppler effect on wireless signals
(FM radio, WiFi, cellular). Works in theory on any RF source; best with
FM radio + RTL-SDR dongle. On macOS without SDR hardware, provides
WiFi-based relative-motion estimation and a Doppler-shift calculator.

Usage:
    ww network physical-speed                  # Show overview
    ww network physical-speed --doppler        # Scan FM stations + calculate Doppler
    ww network physical-speed --estimate       # Estimate speed from WiFi RSSI changes
    ww network physical-speed --fm <freq_mhz>  # FM radio Doppler calculator
    ww network physical-speed --simulate       # Simulate and explain the physics
    ww network physical-speed --scan           # Scan FM band with RTL-SDR

Options:
    --doppler           Doppler shift calculator (auto-scans FM stations)
    --estimate          WiFi RSSI-based speed estimation
    --fm <freq_mhz>    FM frequency for Doppler calculation
    --simulate          Simulate Doppler shift for various signals
    --scan              Scan FM band with RTL-SDR dongle
    --speed <kmh>       Speed in km/h (for --doppler/--fm mode)
    --duration <sec>    Observation duration in seconds (default: 10)
"""

import json
import shutil
import subprocess
import sys
import time
import urllib.request

SPEED_OF_LIGHT = 3e8  # m/s

# Popular FM stations by city. Each entry: (freq_mhz, name, power_description)
# Sources: Wikipedia, SARFT public filings, radio-tuning.com
FM_STATIONS = {
    "guangzhou": [
        (87.4, "CNR-2 经济之声", "10 kW"),
        (88.8, "广东新闻广播", "10 kW"),
        (89.3, "CNR-1 中国之声", "10 kW"),
        (91.4, "广东珠江经济台", "10 kW"),
        (93.6, "广东音乐之声", "10 kW"),
        (95.2, "广州新闻资讯", "3 kW"),
        (96.2, "广州交通电台", "3 kW"),
        (97.4, "广东文体广播", "10 kW"),
        (99.3, "CNR-3 音乐之声", "10 kW"),
        (100.2, "广州金曲音乐", "3 kW"),
        (101.7, "广东南方生活", "10 kW"),
        (102.7, "广州汽车音乐", "3 kW"),
        (103.6, "广东城市之声", "10 kW"),
        (105.2, "广东股市广播", "10 kW"),
        (106.1, "广州新闻电台", "3 kW"),
        (107.6, "广东新闻广播", "10 kW"),
    ],
    "shenzhen": [
        (87.8, "深圳新闻频率", "3 kW"),
        (89.8, "深圳生活频率", "3 kW"),
        (91.8, "深圳音乐频率", "3 kW"),
        (94.2, "CNR-1 中国之声", "1 kW"),
        (95.8, "深圳交通频率", "3 kW"),
        (97.1, "CNR-2 经济之声", "1 kW"),
        (99.1, "深圳先锋频率", "3 kW"),
        (102.0, "CNR-3 音乐之声", "1 kW"),
        (104.3, "深圳私家车", "3 kW"),
        (105.7, "深圳快乐1057", "3 kW"),
    ],
    "beijing": [
        (87.6, "北京文艺广播", "10 kW"),
        (88.1, "CNR-2 经济之声", "10 kW"),
        (89.1, "CNR-1 中国之声", "10 kW"),
        (90.0, "北京新闻广播", "10 kW"),
        (91.5, "CNR-9 中华之声", "10 kW"),
        (93.0, "北京音乐广播", "10 kW"),
        (95.4, "北京交通广播", "10 kW"),
        (96.6, "北京城市管理", "10 kW"),
        (97.4, "北京音乐台", "10 kW"),
        (99.6, "北京故事广播", "10 kW"),
        (100.6, "北京体育广播", "10 kW"),
        (101.8, "北京外语广播", "10 kW"),
        (103.9, "北京交通广播", "10 kW"),
        (105.2, "CNR-3 音乐之声", "10 kW"),
        (106.1, "CNR-11 藏语广播", "10 kW"),
        (107.3, "北京青年广播", "10 kW"),
    ],
    "shanghai": [
        (87.9, "动感101", "10 kW"),
        (89.9, "都市792", "10 kW"),
        (91.4, "第一财经广播", "10 kW"),
        (93.4, "上海新闻广播", "10 kW"),
        (94.7, "经典947", "10 kW"),
        (97.2, "上海故事广播", "10 kW"),
        (99.0, "上海交通广播", "10 kW"),
        (101.7, "上海交通台", "10 kW"),
        (103.7, "Love Radio", "10 kW"),
        (105.7, "上海体育广播", "10 kW"),
        (107.2, "上海老年广播", "10 kW"),
    ],
    "chengdu": [
        (88.1, "CNR-2 经济之声", "10 kW"),
        (89.4, "CNR-1 中国之声", "10 kW"),
        (91.4, "四川新闻广播", "10 kW"),
        (94.0, "成都交通广播", "3 kW"),
        (95.5, "四川交通广播", "10 kW"),
        (98.1, "四川岷江音乐", "10 kW"),
        (100.3, "成都新闻广播", "3 kW"),
        (101.7, "CNR-3 音乐之声", "10 kW"),
        (102.6, "成都文化休闲", "3 kW"),
        (105.1, "四川经济广播", "10 kW"),
        (106.5, "成都故事广播", "3 kW"),
    ],
    "hangzhou": [
        (88.0, "浙江之声", "10 kW"),
        (89.0, "浙江经济广播", "10 kW"),
        (91.8, "杭州交通经济", "3 kW"),
        (93.0, "浙江音乐调频", "10 kW"),
        (95.0, "浙江城市之声", "10 kW"),
        (96.8, "杭州新闻广播", "3 kW"),
        (99.6, "杭州西湖之声", "3 kW"),
        (101.6, "浙江文艺广播", "10 kW"),
        (103.2, "杭州私家车", "3 kW"),
        (104.5, "浙江旅游之声", "10 kW"),
        (105.4, "杭州交通广播", "3 kW"),
        (107.0, "浙江老年广播", "10 kW"),
    ],
    "wuhan": [
        (88.4, "CNR-2 经济之声", "10 kW"),
        (89.6, "CNR-1 中国之声", "10 kW"),
        (91.2, "湖北之声", "10 kW"),
        (92.7, "楚天交通广播", "10 kW"),
        (93.6, "湖北经济广播", "10 kW"),
        (95.6, "楚天音乐广播", "10 kW"),
        (97.8, "湖北音乐广播", "10 kW"),
        (99.8, "武汉新闻广播", "3 kW"),
        (101.8, "湖北文艺广播", "10 kW"),
        (103.8, "CNR-3 音乐之声", "10 kW"),
        (105.8, "湖北生活广播", "10 kW"),
        (107.8, "湖北私家车", "10 kW"),
    ],
    "international": [
        (88.0, "BBC Radio 1 (UK)", "—"),
        (89.9, "NPR (US)", "—"),
        (91.1, "WNYC (New York)", "—"),
        (93.9, "WQXR (New York Classical)", "—"),
        (96.3, "KQED (San Francisco)", "—"),
        (99.5, "Classical KUSC (LA)", "—"),
        (101.1, "KIIS FM (LA)", "—"),
        (103.5, "KTU (New York)", "—"),
        (106.7, "Lite FM (New York)", "—"),
    ],
}

# City name aliases for fuzzy matching
_CITY_ALIASES = {
    "guangzhou": ["guangzhou", "gz", "广州", "canton"],
    "shenzhen": ["shenzhen", "sz", "深圳"],
    "beijing": ["beijing", "bj", "北京"],
    "shanghai": ["shanghai", "sh", "上海"],
    "chengdu": ["chengdu", "cd", "成都"],
    "hangzhou": ["hangzhou", "hz", "杭州"],
    "wuhan": ["wuhan", "wh", "武汉"],
}


def _help():
    print("Usage: ww network physical-speed [options]")
    print("")
    print("Estimate vehicle speed using EM Doppler shift on wireless signals.")
    print("")
    print("Options:")
    print("  --doppler             Doppler shift calculator (scans FM stations)")
    print("  --estimate            WiFi RSSI-based speed estimation (macOS)")
    print("  --fm <freq_mhz>      FM radio Doppler calculator")
    print("  --simulate            Simulate Doppler shifts for various signals")
    print("  --scan                Scan FM band with RTL-SDR dongle")
    print("  --speed <kmh>         Speed in km/h (for --doppler/--fm mode)")
    print("  --duration <sec>      Observation duration (default: 10s)")
    print("  --help, -h            Show this help")


def doppler_shift(source_freq_hz, velocity_ms):
    """Calculate Doppler frequency shift for non-relativistic speeds.

    Args:
        source_freq_hz: Source frequency in Hz
        velocity_ms: Velocity toward source in m/s (negative = away)

    Returns:
        Frequency shift in Hz (positive = blue-shift, negative = red-shift)
    """
    return source_freq_hz * velocity_ms / SPEED_OF_LIGHT


def speed_from_shift(source_freq_hz, shift_hz):
    """Derive velocity from observed frequency shift.

    Args:
        source_freq_hz: Source frequency in Hz
        shift_hz: Observed frequency shift in Hz

    Returns:
        Velocity in m/s
    """
    return shift_hz * SPEED_OF_LIGHT / source_freq_hz


def _detect_city():
    """Detect city via IP geolocation (bypasses proxy)."""
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/",
            headers={"Accept": "application/json", "User-Agent": "ww/1.0"},
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        resp = opener.open(req, timeout=5)
        data = json.loads(resp.read().decode())
        if data.get("status") == "success":
            city = data.get("city", "").lower()
            return city
    except Exception:
        pass

    try:
        req = urllib.request.Request(
            "https://ipinfo.io/json",
            headers={"Accept": "application/json", "User-Agent": "ww/1.0"},
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        resp = opener.open(req, timeout=5)
        data = json.loads(resp.read().decode())
        city = data.get("city", "").lower()
        return city
    except Exception:
        pass

    return None


def _match_city(detected_city):
    """Match detected city name to FM_STATIONS key."""
    if not detected_city:
        return None
    detected = detected_city.lower().strip()
    for key, aliases in _CITY_ALIASES.items():
        for alias in aliases:
            if alias in detected or detected in alias:
                return key
    return None


def _has_rtl_sdr():
    """Check if rtl_power is available (RTL-SDR dongle connected)."""
    return shutil.which("rtl_power") is not None


def _scan_fm_band():
    """Scan FM band (88-108 MHz) with RTL-SDR dongle.

    Returns list of (freq_mhz, power_db) sorted by signal strength.
    """
    if not _has_rtl_sdr():
        return None

    print("  Scanning FM band (88-108 MHz) with RTL-SDR...")
    print("  This takes ~30 seconds...")
    print("")

    try:
        # rtl_power: scan 88-108 MHz, 1 MHz steps, 1 second per step
        out = subprocess.check_output(
            [
                "rtl_power",
                "-f",
                "88e6:108e6:1e6",
                "-g",
                "40",
                "-i",
                "1",
                "-e",
                "30s",
                "-",
            ],
            text=True,
            timeout=60,
        )
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return None

    # Parse output: date, time, Hz_low, Hz_high, Hz_step, samples, dB, dB, ...
    stations = []
    for line in out.strip().splitlines():
        parts = line.split(",")
        if len(parts) < 7:
            continue
        try:
            freq_low = float(parts[2])
            freq_high = float(parts[3])
            freq_center = (freq_low + freq_high) / 2 / 1e6  # MHz
            # Get max power from samples
            powers = [float(p) for p in parts[6:] if p.strip()]
            if powers:
                max_power = max(powers)
                stations.append((freq_center, max_power))
        except (ValueError, IndexError):
            continue

    # Deduplicate by rounding to 0.1 MHz
    seen = {}
    for freq, power in stations:
        key = round(freq, 1)
        if key not in seen or power > seen[key]:
            seen[key] = power
    stations = [(f, p) for f, p in seen.items()]
    stations.sort(key=lambda x: -x[1])

    return stations[:20]  # Top 20


def _get_fm_stations(city=None):
    """Get FM stations for a city. Returns list of (freq_mhz, name, power)."""
    if city:
        matched = _match_city(city)
        if matched and matched in FM_STATIONS:
            return FM_STATIONS[matched]

    # Try auto-detection
    detected = _detect_city()
    if detected:
        matched = _match_city(detected)
        if matched and matched in FM_STATIONS:
            return FM_STATIONS[matched]

    # Fallback: return a mix of popular stations
    return FM_STATIONS["international"]


def _prompt_choice(stations, prompt_text="Select station"):
    """Show numbered station list, return selected (freq_mhz, name)."""
    print(f"  {prompt_text}:")
    print(f"  {'─' * 50}")
    for i, (freq, name, *_) in enumerate(stations, 1):
        print(f"  [{i}]  {freq:>6.1f} MHz  {name}")
    print("")

    try:
        raw = input("  Enter number (or frequency in MHz): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("")
        return None

    if not raw:
        return None

    # Try as number
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(stations):
            return stations[idx][0], stations[idx][1]
    except ValueError:
        pass

    # Try as frequency
    try:
        freq = float(raw)
        # Find closest station
        closest = min(stations, key=lambda s: abs(s[0] - freq))
        return closest[0], closest[1]
    except ValueError:
        pass

    print(f"  Invalid selection: {raw}")
    return None


def _fm_doppler_calculator(freq_mhz=None, speed_kmh=None):
    """FM radio Doppler shift calculator with station scanning."""
    print(f"  {'=' * 50}")
    print("  FM Radio Doppler Shift Calculator")
    print(f"  {'=' * 50}")
    print("")

    # If no frequency given, scan or suggest stations
    if freq_mhz is None:
        station_name = None

        # Try RTL-SDR scan first
        if _has_rtl_sdr():
            print("  [RTL-SDR detected — scanning FM band]")
            scanned = _scan_fm_band()
            if scanned:
                print("")
                print("  Top FM signals detected:")
                print(f"  {'─' * 45}")
                for i, (freq, power) in enumerate(scanned[:5], 1):
                    print(f"  [{i}]  {freq:>6.1f} MHz  ({power:+.1f} dB)")
                print("")
                try:
                    raw = input("  Select station (1-5) or enter freq: ").strip()
                    idx = int(raw) - 1
                    if 0 <= idx < len(scanned):
                        freq_mhz = scanned[idx][0]
                except (ValueError, EOFError, KeyboardInterrupt):
                    pass

        # Fallback to curated station list
        if freq_mhz is None:
            city = _detect_city()
            stations = _get_fm_stations(city)
            if city:
                matched = _match_city(city)
                label = matched if matched else city
                print(f"  Detected location: {label}")
                print("")
            else:
                print("  [Could not detect location — showing international stations]")
                print("")

            result = _prompt_choice(stations[:5], "Top 5 FM stations near you")
            if result is None:
                print("  No station selected.")
                return
            freq_mhz, station_name = result

        if station_name:
            print(f"\n  Selected: {station_name} ({freq_mhz:.1f} MHz)")
        else:
            print(f"\n  Selected: {freq_mhz:.1f} MHz")

    # If no speed given, show a menu of typical speeds
    if speed_kmh is None:
        print("")
        print("  Select typical highway speed:")
        print(f"  {'─' * 35}")
        speeds = [60, 80, 100, 120, 140]
        for i, s in enumerate(speeds, 1):
            shift = doppler_shift(freq_mhz * 1e6, s / 3.6)
            print(f"  [{i}]  {s:>3} km/h  (Δf = {shift:.1f} Hz)")
        print("")
        try:
            raw = input("  Select speed (1-5) or enter km/h: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            return

        if not raw:
            return

        try:
            idx = int(raw) - 1
            if 0 <= idx < len(speeds):
                speed_kmh = speeds[idx]
            else:
                speed_kmh = float(raw)
        except ValueError:
            try:
                speed_kmh = float(raw)
            except ValueError:
                print(f"  Invalid speed: {raw}")
                return

    freq_hz = freq_mhz * 1e6
    v_ms = speed_kmh / 3.6
    shift_hz = doppler_shift(freq_hz, v_ms)

    print(f"\n  {'=' * 50}")
    print("  FM Radio Doppler Analysis")
    print(f"  {'=' * 50}")
    print(f"  Station frequency:  {freq_mhz:.1f} MHz")
    print(f"  Vehicle speed:      {speed_kmh:.0f} km/h ({v_ms:.1f} m/s)")
    print(f"  Doppler shift:      {shift_hz:+.1f} Hz")
    print(f"  Relative shift:     {shift_hz / freq_hz * 1e6:+.3f} ppm")
    print("")

    # Measurement feasibility
    print("  Measurement Feasibility:")
    if abs(shift_hz) > 5000:
        print("  ✓ Shift > 5 kHz — easily measurable with RTL-SDR")
    elif abs(shift_hz) > 1000:
        print("  ✓ Shift > 1 kHz — measurable with good SDR")
    elif abs(shift_hz) > 100:
        print("  ~ Shift > 100 Hz — challenging, need narrow-band filter")
    else:
        print("  ✗ Shift < 100 Hz — very difficult to isolate")

    print("")
    print("  Required SDR setup:")
    print("    1. RTL-SDR V4 dongle (~$25)")
    print(f"    2. Center frequency: {freq_mhz:.1f} MHz")
    print("    3. Sample rate: 2.4 MSPS")
    print(f"    4. FFT size: 65536 -> resolution: {2.4e6 / 65536:.1f} Hz/bin")
    print("    5. Observe carrier peak shift over time")

    # Estimate accuracy
    fft_resolution = 2.4e6 / 65536
    speed_resolution = speed_from_shift(freq_hz, fft_resolution) * 3.6
    print(f"\n  With 65536-pt FFT: freq resolution = {fft_resolution:.1f} Hz")
    print(f"  -> minimum detectable speed: ~{speed_resolution:.1f} km/h")

    return shift_hz


def _get_wifi_rssi():
    """Get current WiFi RSSI on macOS using airport utility."""
    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    try:
        out = subprocess.check_output([airport, "-I"], text=True)
        for line in out.splitlines():
            if "agrCtlRSSI" in line:
                return int(line.split(":")[-1].strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def _get_wifi_bssid():
    """Get current WiFi BSSID (access point MAC) on macOS."""
    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    try:
        out = subprocess.check_output([airport, "-I"], text=True)
        for line in out.splitlines():
            if "BSSID" in line:
                return line.split(":")[-1].strip().lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def _estimate_speed_from_rssi(duration=10):
    """Estimate speed by observing WiFi RSSI changes over time."""
    print(f"{'=' * 55}")
    print("  WiFi RSSI-Based Motion Estimation")
    print(f"{'=' * 55}")
    print(f"  Observing for {duration} seconds...")
    print("  (Move toward/away from a WiFi AP for best results)")
    print("")

    bssid = _get_wifi_bssid()
    if not bssid:
        print("  ERROR: Not connected to a WiFi network.")
        print("  Connect to a WiFi AP first, then retry.")
        return

    print(f"  Connected AP BSSID: {bssid}")

    samples = []
    start = time.time()
    while time.time() - start < duration:
        rssi = _get_wifi_rssi()
        if rssi is not None:
            samples.append((time.time(), rssi))
        time.sleep(0.5)

    if len(samples) < 4:
        print("  ERROR: Not enough RSSI samples collected.")
        return

    rssis = [s[1] for s in samples]
    times_s = [s[0] - samples[0][0] for s in samples]

    n = len(rssis)
    sum_t = sum(times_s)
    sum_r = sum(rssis)
    sum_tr = sum(t * r for t, r in zip(times_s, rssis))
    sum_tt = sum(t * t for t in times_s)

    denom = n * sum_tt - sum_t * sum_t
    if denom == 0:
        slope = 0
    else:
        slope = (n * sum_tr - sum_t * sum_r) / denom

    speed_estimate = abs(slope) * 60

    print("\n  Results:")
    print(f"  {'─' * 45}")
    print(f"  Samples collected:  {n}")
    print(f"  RSSI range:         {min(rssis)} to {max(rssis)} dBm")
    print(f"  RSSI slope:         {slope:+.2f} dB/s")
    print(
        f"  Direction:          {'moving toward AP' if slope > 0 else 'moving away from AP' if slope < 0 else 'stationary'}"
    )
    print(f"  Estimated speed:    ~{speed_estimate:.0f} km/h (relative to AP)")
    print("")
    print("  NOTE: This is a rough estimate. WiFi RSSI-based speed")
    print("  measurement is imprecise due to multipath, obstacles,")
    print("  and antenna patterns. For accurate Doppler measurement,")
    print("  use an RTL-SDR dongle with FM radio: $25 on Amazon.")
    print("")
    print("  For true Doppler: ww network physical-speed --doppler")


def _simulate_doppler():
    """Simulate and display Doppler shifts for various signal sources."""
    speeds = [30, 60, 100, 120, 150]
    sources = [
        ("FM Radio (low)", 88e6),
        ("FM Radio (mid)", 98e6),
        ("FM Radio (high)", 108e6),
        ("Cellular 900", 900e6),
        ("WiFi 2.4 GHz", 2.4e9),
        ("WiFi 5 GHz", 5.0e9),
        ("5G mmWave 28 GHz", 28e9),
    ]

    print(f"{'=' * 70}")
    print("  Doppler Shift Simulation for Various Signal Sources")
    print(f"{'=' * 70}")
    print("")
    print("  Physics: df = f_source x v / c")
    print(f"  c = {SPEED_OF_LIGHT:.0e} m/s")
    print("")

    header = f"  {'Source':<22}"
    for s in speeds:
        header += f" {s:>8} km/h"
    print(header)
    print(f"  {'─' * 22}" + "─" * (11 * len(speeds)))

    for name, freq in sources:
        row = f"  {name:<22}"
        for s in speeds:
            v_ms = s / 3.6
            shift = doppler_shift(freq, v_ms)
            if shift >= 1e6:
                row += f" {shift / 1e6:>7.2f} MHz"
            elif shift >= 1e3:
                row += f" {shift / 1e3:>7.2f} kHz"
            else:
                row += f" {shift:>7.2f} Hz"
        print(row)

    print("")
    print("  KEY INSIGHTS:")
    print("  - FM radio shift is ~8 Hz at 100 km/h — very small!")
    print("    -> needs long observation time + narrow-band FFT")
    print("  - WiFi 5 GHz shift is ~463 Hz at 100 km/h")
    print("    -> still hard due to OFDM spread spectrum noise")
    print("  - 5G mmWave has ~2.6 kHz shift at 100 km/h")
    print("    -> already used in automotive radar (77 GHz)")
    print("")
    print("  PRACTICAL: 5G mmWave or automotive radar for real Doppler speed.")


def _scan_and_show():
    """Scan FM band and show results."""
    if not _has_rtl_sdr():
        print("  RTL-SDR not found. Install rtl-sdr to scan FM band:")
        print("    brew install librtlsdr    # macOS")
        print("    apt install rtl-sdr       # Linux")
        print("")
        print("  Also need an RTL-SDR V4 dongle (~$25 on Amazon).")
        print("")
        # Show curated stations instead
        city = _detect_city()
        stations = _get_fm_stations(city)
        if city:
            matched = _match_city(city)
            label = matched if matched else city
            print(f"  Detected location: {label}")
        else:
            print("  [Could not detect location — showing international stations]")
        print("")
        print(f"  {'Freq':>8}  {'Station':<30}  {'Power'}")
        print(f"  {'─' * 8}  {'─' * 30}  {'─' * 10}")
        for freq, name, power in stations:
            print(f"  {freq:>7.1f}  {name:<30}  {power}")
        return

    scanned = _scan_fm_band()
    if not scanned:
        print("  Scan failed or no signals detected.")
        return

    print("\n  FM Band Scan Results (top 10)")
    print(f"  {'─' * 45}")
    print(f"  {'Freq':>8}  {'Power':>10}")
    print(f"  {'─' * 8}  {'─' * 10}")
    for freq, power in scanned[:10]:
        print(f"  {freq:>7.1f}  {power:>+9.1f} dB")


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        _help()
        return

    if "--simulate" in args:
        _simulate_doppler()
        return

    if "--scan" in args:
        _scan_and_show()
        return

    if "--doppler" in args:
        speed = None
        for i, a in enumerate(args):
            if a == "--speed" and i + 1 < len(args):
                try:
                    speed = float(args[i + 1])
                except ValueError:
                    pass
        _fm_doppler_calculator(speed_kmh=speed)
        return

    if "--fm" in args:
        freq = None
        speed = None
        for i, a in enumerate(args):
            if a == "--fm" and i + 1 < len(args):
                try:
                    freq = float(args[i + 1])
                except ValueError:
                    pass
            if a == "--speed" and i + 1 < len(args):
                try:
                    speed = float(args[i + 1])
                except ValueError:
                    pass
        _fm_doppler_calculator(freq_mhz=freq, speed_kmh=speed)
        return

    if "--estimate" in args:
        duration = 10
        for i, a in enumerate(args):
            if a == "--duration" and i + 1 < len(args):
                try:
                    duration = int(args[i + 1])
                except ValueError:
                    pass
        _estimate_speed_from_rssi(duration)
        return

    # Default: show overview
    print(f"{'=' * 55}")
    print("  Physical Speed Estimation — Doppler Effect")
    print(f"{'=' * 55}")
    print("")
    print("  Measure vehicle speed using wireless signal Doppler shift.")
    print("")
    print("  Modes:")
    print("    --doppler      FM station scanner + Doppler calculator")
    print("    --estimate     WiFi RSSI-based speed estimation (macOS)")
    print("    --simulate     Simulate Doppler shifts for various signals")
    print("    --fm <freq>    FM radio Doppler calculator")
    print("    --scan         Scan FM band (RTL-SDR) or list local stations")
    print("")
    print("  Quick start:")
    print("    ww network physical-speed --doppler")
    print("    ww network physical-speed --simulate")
    print("    ww network physical-speed --fm 101.1 --speed 100")
    print("")
    print("  Best method: 5G mmWave (28 GHz) or automotive radar (77 GHz)")
    print("  FM shift at 100 km/h ~ 8 Hz — too small for practical SDR.")
    print("  5G mmWave at 100 km/h ~ 2.6 kHz — measurable with SDR.")


if __name__ == "__main__":
    main()
