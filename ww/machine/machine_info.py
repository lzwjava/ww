import subprocess
import sys


def run(cmd, remote=None, ssh_args=""):
    """Run command locally or via SSH. Returns stdout or None."""
    try:
        if remote:
            cmd = f"ssh -o ConnectTimeout=5 -o ProxyCommand=none {ssh_args} {remote} {cmd}"
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip()
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass
    return None


def get_machine_info(remote=None, ssh_args=""):
    """Collect basic machine info: hostname, cpu, load, memory, disk."""
    info = {}

    # Hostname
    info["hostname"] = run("hostname", remote, ssh_args) or "unknown"

    # CPU cores
    cpu_cores = run("nproc", remote, ssh_args)
    if not cpu_cores:
        cpu_cores = run("sysctl -n hw.ncpu", remote, ssh_args)
    info["cpu_cores"] = cpu_cores or "?"

    # CPU model (first line)
    cpu_model = run(
        "lscpu | grep '^Model name' | sed 's/Model name:\\s*//'", remote, ssh_args
    )
    if not cpu_model:
        cpu_model = run("sysctl -n machdep.cpu.brand_string", remote, ssh_args)
    info["cpu_model"] = cpu_model or "unknown"

    # Load average
    load = run("cat /proc/loadavg | awk '{print $1, $2, $3}'", remote, ssh_args)
    if not load:
        load = run("sysctl -n vm.loadavg | awk '{print $2, $3, $4}'", remote, ssh_args)
    info["load"] = load or "?"

    # Memory
    mem = run('free -h | awk \'/^Mem:/{print $3"/"$2" used"}\'', remote, ssh_args)
    if not mem:
        # macOS: use sysctl for total, vm_stat for usage
        page_size = run(
            "vm_stat | head -1 | grep -o '[0-9]*' | tail -1", remote, ssh_args
        )
        ps = int(page_size) if page_size and page_size.isdigit() else 16384
        total_bytes = run("sysctl -n hw.memsize", remote, ssh_args)
        if total_bytes and total_bytes.isdigit():
            total_gb = int(total_bytes) / 1073741824
            used = run(
                f"vm_stat | awk -v ps={ps} "
                "'/Pages active/{{act=$3}} /Pages wired/{{wired=$3}} "
                'END{printf "%.1f", (act+wired)*ps/1073741824}\'',
                remote,
                ssh_args,
            )
            if used:
                mem = f"{used}G/{total_gb:.0f}G used"
    info["memory"] = mem or "?"

    # Disk
    disk = run('df -h / | awk \'NR==2{print $3"/"$2" used ("$5")"}\'', remote, ssh_args)
    info["disk"] = disk or "?"

    # Uptime
    uptime = run("uptime -p", remote, ssh_args)
    if not uptime:
        uptime = run("uptime | sed 's/.*up /up /' | sed 's/,.*//'", remote, ssh_args)
    info["uptime"] = uptime or "?"

    # GPU (NVIDIA only, skip if not present)
    gpu = run(
        "nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null",
        remote,
        ssh_args,
    )
    if gpu and "failed" not in gpu.lower():
        # Format: name, used, total
        parts = [p.strip() for p in gpu.split(",")]
        if len(parts) >= 3:
            info["gpu"] = f"{parts[0]} ({parts[1]}MB/{parts[2]}MB)"
        else:
            info["gpu"] = gpu
    else:
        info["gpu"] = None

    return info


def print_info(info, label):
    """Print machine info in a compact format."""
    print(f"--- {label} ({info['hostname']}) ---")
    print(f"  CPU:    {info['cpu_model']} ({info['cpu_cores']} cores)")
    print(f"  Load:   {info['load']}")
    print(f"  Memory: {info['memory']}")
    print(f"  Disk:   {info['disk']}")
    print(f"  Uptime: {info['uptime']}")
    if info.get("gpu"):
        print(f"  GPU:    {info['gpu']}")


MACHINES = {
    "local": {"label": "Local", "remote": None},
    "workstation": {"label": "Workstation", "remote": "lzw@192.168.1.36"},
    "dmit": {
        "label": "DMIT",
        "remote": "root@69.63.219.52",
        "ssh_args": "-i ~/projects/DMIT-KiXdN3dnsQ-id_rsa/id_rsa.pem",
    },
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage: ww machine <name> [name...]")
        print()
        print("Machines:")
        print("  local        Current machine")
        print("  workstation   lzw@192.168.1.36")
        print("  dmit          DMIT server (root@69.63.219.52)")
        print()
        print("Examples:")
        print("  ww machine local")
        print("  ww machine workstation")
        print("  ww machine local workstation")
        return

    targets = sys.argv[1:]
    first = True
    for target in targets:
        if target not in MACHINES:
            print(f"Unknown machine: {target}")
            print(f"Available: {', '.join(MACHINES.keys())}")
            sys.exit(1)
        if not first:
            print()
        first = False
        cfg = MACHINES[target]
        info = get_machine_info(remote=cfg["remote"], ssh_args=cfg.get("ssh_args", ""))
        print_info(info, cfg["label"])
