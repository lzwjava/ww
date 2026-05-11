import argparse
import subprocess


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7890
BYPASS_DOMAINS = [
    "127.0.0.1",
    "localhost",
    "lzwjava.local",
    "192.168.1.1",
    "192.168.1.*",
    "192.168.0.*",
    "192.168.0.1",
    "192.168.2.*",
    "192.168.2.1",
    "192.168.88.*",
]


def _run(cmd):
    subprocess.run(cmd, check=True)


def _list_services():
    result = subprocess.run(
        ["networksetup", "-listallnetworkservices"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        line.strip()
        for line in result.stdout.splitlines()[1:]
        if line.strip() and not line.startswith("*")
    ]


def _service_ip(service):
    result = subprocess.run(
        ["networksetup", "-getinfo", service],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("IP address:"):
            return line.split(":", 1)[1].strip().lower()
    return None


def _is_active(service):
    ip = _service_ip(service)
    if ip is None:
        return False
    else:
        return ip not in ("", "none", "0.0.0.0")


def _active_services():
    wanted = ("Wi-Fi", "USB 10/100 LAN")
    return [
        s for s in _list_services() if any(w in s for w in wanted) and _is_active(s)
    ]


def _apply(service, host, http_port, socks_port):
    _run(["networksetup", "-setwebproxy", service, host, str(http_port)])
    _run(["networksetup", "-setsecurewebproxy", service, host, str(http_port)])
    _run(["networksetup", "-setsocksfirewallproxy", service, host, str(socks_port)])
    _run(["networksetup", "-setproxybypassdomains", service, *BYPASS_DOMAINS])
    print(
        f"{service}: HTTP/HTTPS {host}:{http_port}, "
        f"SOCKS {host}:{socks_port}, bypass {len(BYPASS_DOMAINS)} entries"
    )


def _clean(service):
    _run(["networksetup", "-setwebproxystate", service, "off"])
    _run(["networksetup", "-setsecurewebproxystate", service, "off"])
    _run(["networksetup", "-setsocksfirewallproxystate", service, "off"])
    _run(["networksetup", "-setproxybypassdomains", service, "Empty"])
    print(f"{service}: HTTP/HTTPS/SOCKS proxies disabled, bypass cleared")


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ww macos settings-proxy",
        description="Set macOS system proxy (HTTP/HTTPS + SOCKS) with bypass list",
    )
    parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"Proxy host (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"HTTP/HTTPS proxy port; SOCKS uses port+1 (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove proxy values from networksetup instead of setting them",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    services = _active_services()
    if not services:
        print("No active Wi-Fi or USB Ethernet interface found.")
        return
    else:
        for service in services:
            try:
                if args.clean:
                    _clean(service)
                else:
                    _apply(service, args.host, args.port, args.port + 1)
            except subprocess.CalledProcessError as e:
                verb = "clearing" if args.clean else "setting"
                print(f"Error {verb} proxy for {service}: {e}")


if __name__ == "__main__":
    main()
