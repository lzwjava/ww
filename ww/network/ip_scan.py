import subprocess
import ipaddress
import threading
import socket
import argparse

MAX_THREADS = 50  # Maximum number of threads to use


def is_host_up_by_port(host, port):
    """Check if host is reachable by attempting a TCP connection to port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0
    except socket.error:
        return False
    finally:
        sock.close()


def is_host_up_by_ping(host):
    """Check if host is reachable via ICMP ping."""
    try:
        subprocess.check_output(["ping", "-c", "1", "-W", "1", host], timeout=1)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def get_ping_delay(host, count=10):
    """Get avg ping delay in ms over multiple pings. Returns None on failure."""
    import sys

    # macOS -W is in ms, Linux -W is in seconds
    timeout_val = "1000" if sys.platform == "darwin" else "1"
    try:
        output = subprocess.check_output(
            ["ping", "-c", str(count), "-W", timeout_val, host],
            timeout=count + 2,
            text=True,
        )
        for line in output.splitlines():
            if "round-trip" in line:
                # format: "round-trip min/avg/max/stddev = 1.234/5.678/9.012/3.456 ms"
                parts = line.split("=")[-1].strip().split("/")
                return float(parts[1])  # avg
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


def is_host_up(host, port=None):
    """Check if a host is up using TCP (if port given) or ping."""
    if port:
        return is_host_up_by_port(host, port)
    else:
        return is_host_up_by_ping(host)


def test_ssh_access(ip, hostname, port=22):
    """Test if we can SSH into ip as `hostname` using key-based auth (no password prompt)."""
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=3",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-p",
        str(port),
        f"{hostname}@{ip}",
        "true",
    ]
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, timeout=8)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def test_ssh_on_host(ip, hostname, port, results):
    """Test SSH port and login on a single IP, storing (ip, port_open, ssh_ok) in results."""
    port_open = is_host_up_by_port(ip, port)
    ssh_ok = False
    if port_open:
        ssh_ok = test_ssh_access(ip, hostname, port)
    results.append((ip, port_open, ssh_ok))


def test_ssh_network(up_ips, hostname, port=22):
    """Test SSH access to all live IPs in parallel. Returns list of (ip, port_open, ssh_ok)."""
    print(f"\nTesting SSH access as '{hostname}' on port {port}...")
    results = []
    threads = []
    semaphore = threading.Semaphore(MAX_THREADS)

    def test_with_semaphore(ip_str):
        with semaphore:
            test_ssh_on_host(ip_str, hostname, port, results)

    for ip in up_ips:
        thread = threading.Thread(target=test_with_semaphore, args=(ip,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results


def scan_ip(ip_str, up_ips, port=None, show_delay=False, delays=None):
    """
    Scans a single IP address and prints its status.
    """
    if is_host_up(ip_str, port):
        if show_delay:
            delay = get_ping_delay(ip_str)
            if delay is not None:
                print(f"{ip_str} is up  avg {delay:.1f} ms")
                if delays is not None:
                    delays[ip_str] = delay
            else:
                print(f"{ip_str} is up  (no delay)")
        else:
            print(f"{ip_str} is up")
        up_ips.append(ip_str)
    else:
        print(f"{ip_str} is down")


def scan_network(network, port=None, show_delay=False):
    """
    Scans a network for live hosts using threads, limiting the number of concurrent threads.
    """
    print(f"Scanning network: {network}")
    threads = []
    semaphore = threading.Semaphore(
        MAX_THREADS
    )  # Limit the number of concurrent threads
    up_ips = []
    delays = {}

    def scan_ip_with_semaphore(ip_str):
        with semaphore:
            scan_ip(ip_str, up_ips, port, show_delay, delays)

    for ip in ipaddress.IPv4Network(network):
        ip_str = str(ip)
        thread = threading.Thread(target=scan_ip_with_semaphore, args=(ip_str,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return up_ips, delays


def main():
    parser = argparse.ArgumentParser(description="Scan a network for live hosts.")
    parser.add_argument(
        "network",
        nargs="?",
        default="192.168.1.0/24",
        help="The network to scan (e.g., 192.168.1.0/24)",
    )
    parser.add_argument("-p", "--port", type=int, help="The port to check (optional)")
    parser.add_argument(
        "--delay",
        action="store_true",
        help="Show ping delay (ms) for hosts that are up",
    )
    parser.add_argument(
        "--hostname",
        help="SSH username to test on live hosts (e.g. --hostname lzw)",
    )
    parser.add_argument(
        "--ssh-port",
        type=int,
        default=22,
        help="SSH port to test (default: 22)",
    )
    args = parser.parse_args()

    network_to_scan = args.network
    port_to_scan = args.port
    show_delay = args.delay

    up_ips, delays = scan_network(network_to_scan, port_to_scan, show_delay)
    print("\nLive IPs:")
    for ip in up_ips:
        if show_delay and ip in delays:
            print(f"  {ip}  avg {delays[ip]:.1f} ms")
        else:
            print(f"  {ip}")

    if args.hostname and up_ips:
        results = test_ssh_network(up_ips, args.hostname, args.ssh_port)
        print(f"\nSSH test results (as {args.hostname}, port {args.ssh_port}):")
        accessible = []
        for ip, port_open, ssh_ok in results:
            if ssh_ok:
                print(f"  {ip}  port open  SSH OK")
                accessible.append(ip)
            elif port_open:
                print(f"  {ip}  port open  SSH failed (auth or permission denied)")
            else:
                print(f"  {ip}  port closed")

        if accessible:
            print(f"\nAccessible via {args.hostname}@:")
            for ip in accessible:
                print(f"  {ip}")
        else:
            print(f"\nNo hosts allow SSH access as {args.hostname}")


if __name__ == "__main__":
    main()
