"""ww network speed — Internet speed test with optional proxy comparison.

Usage:
    ww network speed              # Direct connection speed test
    ww network speed --proxy      # Also test through local proxy (mihomo/clash)
    ww network speed --ping-only  # Quick ping/jitter only (no bandwidth)
"""

import sys
import time
import socket
import statistics
import urllib.request
import ssl
from datetime import datetime


def _detect_proxy():
    """Detect if a local SOCKS/HTTP proxy is running (mihomo/clash default ports)."""
    for port in [7890, 7891, 7892, 7897]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
            s.close()
            return port
        except (ConnectionRefusedError, OSError):
            continue
    return None


def _ping_host(host, port=443, timeout=3):
    """TCP ping to host:port, return latency in ms or None."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        start = time.perf_counter()
        s.connect((host, port))
        elapsed = (time.perf_counter() - start) * 1000
        s.close()
        return elapsed
    except (OSError, socket.timeout):
        return None


def _ping_jitter(host, port=443, count=10, timeout=2):
    """Ping host multiple times, return (avg_ms, jitter_ms, min_ms, max_ms)."""
    results = []
    for _ in range(count):
        lat = _ping_host(host, port, timeout=timeout)
        if lat is not None:
            results.append(lat)
        else:
            # If first ping fails, skip rest — host likely unreachable
            if not results:
                return None, None, None, None
        time.sleep(0.05)
    if not results:
        return None, None, None, None
    avg = statistics.mean(results)
    jitter = statistics.stdev(results) if len(results) > 1 else 0.0
    return avg, jitter, min(results), max(results)


def _http_latency(url, timeout=10):
    """GET url, return (status, latency_ms, bytes_downloaded) or (None, None, None)."""
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "ww-network-speed/1.0"}
        )
        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = resp.read()
            elapsed = (time.perf_counter() - start) * 1000
            return resp.status, elapsed, len(data)
    except Exception:
        return None, None, None


def _fmt_latency(ms):
    if ms is None:
        return "timeout"
    return f"{ms:.1f} ms"


def _speedtest_run(label="Direct"):
    """Run speedtest-cli and print results."""
    import speedtest

    print(f"\n{'=' * 50}")
    print(f"  Speed Test ({label})")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}")

    st = speedtest.Speedtest()
    print("  Finding best server...", end=" ", flush=True)
    st.get_best_server()
    server = st.results.server
    print("done")
    print(
        f"  Server: {server.get('sponsor', '?')} ({server.get('name', '?')}, "
        f"{server.get('country', '?')})"
    )
    print(f"  Distance: {float(server.get('d', 0)):.1f} km")

    print("  Testing download...", end=" ", flush=True)
    dl = st.download()
    dl_mbps = dl / 1_000_000
    print(f"{dl_mbps:.2f} Mbps")

    print("  Testing upload...", end=" ", flush=True)
    ul = st.upload()
    ul_mbps = ul / 1_000_000
    print(f"{ul_mbps:.2f} Mbps")

    ping = st.results.ping
    print(f"  Ping: {ping:.2f} ms")
    print(f"  Download: {dl_mbps:.2f} Mbps")
    print(f"  Upload:   {ul_mbps:.2f} Mbps")
    print(f"  Ping:     {ping:.2f} ms")
    return dl_mbps, ul_mbps, ping


def _ping_only():
    """Quick ping/jitter test to multiple endpoints — no bandwidth test."""
    targets = [
        ("Baidu", "baidu.com", 443),
        ("Alibaba", "alibaba.com", 443),
        ("Tencent", "qq.com", 443),
        ("Cloudflare", "1.1.1.1", 443),
        ("Google DNS", "8.8.8.8", 443),
    ]

    print(f"\n{'=' * 50}")
    print("  Ping & Jitter Test")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}\n")

    for name, host, port in targets:
        avg, jitter, mn, mx = _ping_jitter(host, port, count=10)
        if avg is not None:
            print(
                f"  {name:15s}  avg={avg:6.1f} ms  jitter={jitter:5.1f} ms  "
                f"min={mn:6.1f} ms  max={mx:6.1f} ms"
            )
        else:
            print(f"  {name:15s}  unreachable")

    # HTTP latency
    print("\n  HTTP Latency:")
    http_targets = [
        ("https://www.baidu.com", "Baidu"),
        ("https://www.taobao.com", "Taobao"),
        ("https://www.google.com", "Google"),
        ("https://httpbin.org/get", "HTTPBin"),
    ]
    for url, name in http_targets:
        status, lat, size = _http_latency(url)
        if status:
            print(f"  {name:15s}  status={status}  {_fmt_latency(lat)}  {size} bytes")
        else:
            print(f"  {name:15s}  failed/timeout")


def _full_test(with_proxy=False):
    """Full speed test: ping + bandwidth."""
    # Ping first
    _ping_only()

    # Bandwidth via speedtest-cli
    _speedtest_run("Direct")

    proxy_port = _detect_proxy()
    if with_proxy and proxy_port:
        print(f"\n  [Proxy detected on 127.0.0.1:{proxy_port}]")
        # Set proxy env for speedtest
        import os

        old_http = os.environ.get("HTTP_PROXY")
        old_https = os.environ.get("HTTPS_PROXY")
        proxy_url = f"socks5://127.0.0.1:{proxy_port}"
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        try:
            _speedtest_run(f"via Proxy :{proxy_port}")
        except Exception as e:
            print(f"  Proxy speed test failed: {e}")
        finally:
            if old_http:
                os.environ["HTTP_PROXY"] = old_http
            else:
                os.environ.pop("HTTP_PROXY", None)
            if old_https:
                os.environ["HTTPS_PROXY"] = old_https
            else:
                os.environ.pop("HTTPS_PROXY", None)
    elif with_proxy and not proxy_port:
        print("\n  [No local proxy detected (tried ports 7890-7897)]")
        print("  [Skipping proxy speed test]")

    print(f"\n{'=' * 50}")
    print("  Test complete.")


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print("Usage: ww network speed [--proxy] [--ping-only]")
        print("")
        print("Internet speed test: ping, jitter, download, upload.")
        print("")
        print("Options:")
        print("  --proxy       Also test through local proxy (mihomo/clash)")
        print("  --ping-only   Quick ping/jitter test only (no bandwidth)")
        return

    ping_only = "--ping-only" in args
    with_proxy = "--proxy" in args

    if ping_only:
        _ping_only()
    else:
        _full_test(with_proxy=with_proxy)


if __name__ == "__main__":
    main()
