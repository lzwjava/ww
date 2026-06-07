"""ww network physical-speed — Estimate vehicle speed using EM Doppler shift.

Measures car speed by observing the Doppler effect on wireless signals
(FM radio, WiFi, cellular). Works in theory on any RF source; best with
FM radio + RTL-SDR dongle. On macOS without SDR hardware, provides
WiFi-based relative-motion estimation and a Doppler-shift calculator.

Usage:
    ww network physical-speed                  # WiFi-based motion estimation (macOS)
    ww network physical-speed --doppler        # Calculate Doppler shift for given speed
    ww network physical-speed --estimate       # Estimate speed from WiFi RSSI changes
    ww network physical-speed --fm <freq_mhz>  # FM radio Doppler calculator
    ww network physical-speed --simulate       # Simulate and explain the physics

Options:
    --doppler           Doppler shift calculator
    --estimate          WiFi RSSI-based speed estimation
    --fm <freq_mhz>    FM frequency for Doppler calculation
    --simulate          Simulate Doppler shift for various signals
    --speed <kmh>       Speed in km/h (for --doppler mode)
    --duration <sec>    Observation duration in seconds (default: 10)
"""

import sys
import time

SPEED_OF_LIGHT = 3e8  # m/s


def _help():
    print("Usage: ww network physical-speed [options]")
    print("")
    print("Estimate vehicle speed using EM Doppler shift on wireless signals.")
    print("")
    print("Options:")
    print("  --doppler             Doppler shift calculator (interactive)")
    print("  --estimate            WiFi RSSI-based speed estimation (macOS)")
    print("  --fm <freq_mhz>      FM radio Doppler calculator")
    print("  --simulate            Simulate Doppler shifts for various signals")
    print("  --speed <kmh>         Speed in km/h (for --doppler mode)")
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


def _get_wifi_rssi():
    """Get current WiFi RSSI on macOS using airport utility."""
    import subprocess

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
    import subprocess

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
    """Estimate speed by observing WiFi RSSI changes over time.

    Moving toward/away from a WiFi AP causes RSSI to change.
    This is a rough proxy — not a true Doppler measurement,
    but demonstrates the principle and gives order-of-magnitude estimates.

    Typical RSSI change: ~1-3 dB per 10 km/h of relative motion
    (highly environment-dependent).
    """
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

    # Analyze RSSI trend
    rssis = [s[1] for s in samples]
    times_s = [s[0] - samples[0][0] for s in samples]

    # Linear regression on RSSI vs time
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

    # RSSI slope (dB/s) → rough speed estimate
    # Empirical: ~0.5 dB/s ≈ ~30 km/h relative motion
    # (varies hugely with environment — this is order-of-magnitude only)
    speed_estimate = abs(slope) * 60  # rough: 0.5 dB/s ≈ 30 km/h → 60x factor

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
    print("  For true Doppler: ww network physical-speed --fm 101.1 --speed 100")


def _simulate_doppler():
    """Simulate and display Doppler shifts for various signal sources."""
    speeds = [30, 60, 100, 120, 150]  # km/h
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
    print("  Physics: Δf = f_source × v / c")
    print(f"  c = {SPEED_OF_LIGHT:.0e} m/s")
    print("")

    # Header
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
    print("  • FM radio shift is ~8 Hz at 100 km/h — very small!")
    print("    → needs long observation time + narrow-band FFT")
    print("  • WiFi 5 GHz shift is ~463 Hz at 100 km/h")
    print("    → still hard due to OFDM spread spectrum noise")
    print("  • 5G mmWave has ~2.6 kHz shift at 100 km/h")
    print("    → already used in automotive radar (77 GHz)")
    print("")
    print("  PRACTICAL: 5G mmWave or automotive radar for real Doppler speed.")


def _fm_doppler_calculator(freq_mhz=None, speed_kmh=None):
    """FM radio Doppler shift calculator."""
    if freq_mhz is None:
        print("  FM Radio Doppler Shift Calculator")
        print(f"  {'─' * 40}")
        try:
            freq_mhz = float(input("  Enter FM frequency (MHz, e.g. 101.1): "))
        except (ValueError, EOFError):
            print("  Invalid frequency.")
            return

    if speed_kmh is None:
        try:
            speed_kmh = float(input("  Enter vehicle speed (km/h): "))
        except (ValueError, EOFError):
            print("  Invalid speed.")
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
    print(f"    4. FFT size: 65536 → resolution: {2.4e6 / 65536:.1f} Hz/bin")
    print("    5. Observe carrier peak shift over time")

    # Estimate accuracy
    fft_resolution = 2.4e6 / 65536
    speed_resolution = speed_from_shift(freq_hz, fft_resolution) * 3.6
    print(f"\n  With 65536-pt FFT: freq resolution = {fft_resolution:.1f} Hz")
    print(f"  → minimum detectable speed: ~{speed_resolution:.1f} km/h")

    return shift_hz


def _wifi_doppler_estimate():
    """Estimate speed from WiFi signal characteristics."""
    print(f"{'=' * 55}")
    print("  WiFi Doppler-Based Speed Estimation")
    print(f"{'=' * 55}")
    print("")
    print("  WiFi 2.4 GHz Doppler shifts at highway speeds:")
    print(f"  {'─' * 45}")

    wifi_freq = 2.4e9
    for speed in [60, 80, 100, 120, 140]:
        v = speed / 3.6
        shift = doppler_shift(wifi_freq, v)
        print(f"  {speed:>3} km/h  →  Δf = {shift:.1f} Hz")

    print("")
    print("  Challenges with WiFi Doppler:")
    print("  • Very small shifts (~200-400 Hz) buried in OFDM noise")
    print("  • Multiple APs → can't isolate single carrier")
    print("  • Multipath (buildings, cars) smears the signal")
    print("  • WiFi uses spread spectrum — no clean carrier to track")
    print("")
    print("  WiFi is better used for RSSI-based relative motion")
    print("  (see --estimate mode). For true Doppler, use FM radio.")
    print("")
    print("  Advanced: WiFi CSI (Channel State Information) can measure")
    print("  sub-carrier phase shifts → much more sensitive than RSSI.")
    print("  Requires Intel 5300 NIC + Linux CSI tool, or ESP32 CSI.")


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        _help()
        return

    if "--simulate" in args:
        _simulate_doppler()
        return

    if "--doppler" in args:
        # Interactive Doppler calculator
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

    # Default: show WiFi-based estimation summary + guidance
    print(f"{'=' * 55}")
    print("  Physical Speed Estimation — Doppler Effect")
    print(f"{'=' * 55}")
    print("")
    print("  Measure vehicle speed using wireless signal Doppler shift.")
    print("")
    print("  Modes:")
    print("    --estimate     WiFi RSSI-based speed estimation (macOS)")
    print("    --simulate     Simulate Doppler shifts for various signals")
    print("    --fm <freq>    FM radio Doppler calculator")
    print("    --doppler      General Doppler shift calculator")
    print("")
    print("  Quick start:")
    print("    ww network physical-speed --simulate")
    print("    ww network physical-speed --fm 101.1 --speed 100")
    print("    ww network physical-speed --estimate --duration 15")
    print("")
    print("  Best method: 5G mmWave (28 GHz) or automotive radar (77 GHz)")
    print("  FM shift at 100 km/h ≈ 8 Hz — too small for practical SDR.")
    print("  WiFi shift at 100 km/h ≈ 463 Hz — hard without CSI.")
    print("  5G mmWave at 100 km/h ≈ 2.6 kHz — measurable with SDR.")


if __name__ == "__main__":
    main()
