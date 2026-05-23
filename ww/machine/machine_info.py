import subprocess
import sys


def run(cmd, remote=None, ssh_args=""):
    """Run command locally or via SSH. Returns stdout or None."""
    try:
        if remote:
            cmd = f"ssh -o ConnectTimeout=5 -o ProxyCommand=none {ssh_args} {remote} {cmd}"
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            return r.stdout.strip()
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass
    return None


def run_script(script, remote=None, ssh_args=""):
    """Run a multi-line shell script locally or pipe via stdin to SSH."""
    try:
        if remote:
            cmd = (
                f"ssh -o ConnectTimeout=5 -o ProxyCommand=none {ssh_args} {remote} bash"
            )
            r = subprocess.run(
                cmd,
                shell=True,
                input=script,
                capture_output=True,
                text=True,
                timeout=15,
            )
        else:
            r = subprocess.run(
                "bash",
                shell=True,
                input=script,
                capture_output=True,
                text=True,
                timeout=15,
            )
        if r.returncode == 0:
            return r.stdout.strip()
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass
    return None


# Shell script that collects all info in one shot, outputting one value per line.
# Section markers like ---HOSTNAME--- delimit output. Empty = not available.
BATCH_SCRIPT = r"""
echo "---HOSTNAME---"
hostname
echo "---CPU_MODEL---"
if command -v lscpu >/dev/null 2>&1; then
  lscpu | grep '^Model name' | sed 's/Model name:\s*//'
else
  sysctl -n machdep.cpu.brand_string 2>/dev/null
fi
echo "---CPU_CORES---"
nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null
echo "---LOAD---"
if [ -f /proc/loadavg ]; then
  awk '{print $1, $2, $3}' /proc/loadavg
else
  sysctl -n vm.loadavg 2>/dev/null | awk '{print $2, $3, $4}'
fi
echo "---MEMORY---"
if command -v free >/dev/null 2>&1; then
  free -h | awk '/^Mem:/{print $3"/"$2" used"}'
else
  echo "macos_mem"
fi
echo "---DISK---"
df -h / | awk 'NR==2{print $3"/"$2" used ("$5")"}'
echo "---UPTIME---"
uptime -p 2>/dev/null || uptime | sed 's/.*up /up /' | sed 's/,.*//'
echo "---GPU---"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null
echo "---SERVICES---"
"""


def build_batch_script(services=None):
    """Append service checks to the batch script."""
    script = BATCH_SCRIPT
    if services:
        for svc in services:
            script += f"pgrep -x {svc} >/dev/null 2>&1 && echo '{svc}=UP' || echo '{svc}=DOWN'\n"
    script += 'echo "---END---"\n'
    return script


def get_machine_info(remote=None, ssh_args="", services=None):
    """Collect basic machine info in a single SSH call."""
    script = build_batch_script(services)
    raw = run_script(script, remote, ssh_args)
    if not raw:
        return None

    lines = raw.split("\n")
    sections = {}
    current = None
    for line in lines:
        if line.startswith("---") and line.endswith("---"):
            tag = line.strip("-")
            if tag == "END":
                break
            current = tag
            sections[current] = []
        elif current is not None:
            sections[current].append(line)

    def get(section):
        vals = [v for v in sections.get(section, []) if v.strip()]
        return vals[0].strip() if vals else None

    info = {}
    info["hostname"] = get("HOSTNAME") or "unknown"
    info["cpu_model"] = get("CPU_MODEL") or "unknown"
    info["cpu_cores"] = get("CPU_CORES") or "?"
    info["load"] = get("LOAD") or "?"

    # Memory
    mem = get("MEMORY")
    if mem == "macos_mem" or not mem:
        # macOS fallback — run separately (local only, so fast)
        page_size = run(
            "vm_stat | head -1 | grep -o '[0-9]*' | tail -1", remote, ssh_args
        )
        ps = int(page_size) if page_size and page_size.isdigit() else 16384
        total_bytes = run("sysctl -n hw.memsize", remote, ssh_args)
        if total_bytes and total_bytes.isdigit():
            total_gb = int(total_bytes) / 1073741824
            used = run(
                f"vm_stat | awk -v ps={ps} "
                "'/Pages active/{act=$3} /Pages wired/{wired=$3} "
                'END{printf "%.1f", (act+wired)*ps/1073741824}\'',
                remote,
                ssh_args,
            )
            if used:
                mem = f"{used}G/{total_gb:.0f}G used"
    info["memory"] = mem or "?"

    info["disk"] = get("DISK") or "?"
    info["uptime"] = get("UPTIME") or "?"

    # GPU
    gpu = get("GPU")
    if gpu and "failed" not in gpu.lower():
        parts = [p.strip() for p in gpu.split(",")]
        if len(parts) >= 3:
            info["gpu"] = f"{parts[0]} ({parts[1]}MB/{parts[2]}MB)"
        else:
            info["gpu"] = gpu
    else:
        info["gpu"] = None

    # Services
    svc_lines = sections.get("SERVICES", [])
    svc_results = []
    if services:
        for svc in services:
            found = any(line.strip() == f"{svc}=UP" for line in svc_lines)
            svc_results.append((svc, found))
    info["services"] = svc_results

    return info


def print_info(info, label, services=None):
    """Print machine info in a compact format."""
    print(f"--- {label} ({info['hostname']}) ---")
    print(f"  CPU:    {info['cpu_model']} ({info['cpu_cores']} cores)")
    print(f"  Load:   {info['load']}")
    print(f"  Memory: {info['memory']}")
    print(f"  Disk:   {info['disk']}")
    print(f"  Uptime: {info['uptime']}")
    if info.get("gpu"):
        print(f"  GPU:    {info['gpu']}")
    if services:
        for name, up in services:
            icon = "✓" if up else "✗"
            status = "running" if up else "NOT running"
            print(f"  {icon} {name}: {status}")


MACHINES = {
    "local": {"label": "Local", "remote": None},
    "workstation": {"label": "Workstation", "remote": "lzw@192.168.1.36"},
    "dmit": {
        "label": "DMIT",
        "remote": "root@69.63.219.52",
        "ssh_args": "-i ~/projects/DMIT-KiXdN3dnsQ-id_rsa/id_rsa.pem",
        "services": ["hysteria"],
    },
}


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target in ("--help", "-h"):
        print("Usage: ww host [local|workstation|dmit|all]")
        print()
        print("  local        Current machine")
        print("  workstation  lzw@192.168.1.36 (RTX 4070)")
        print("  dmit         DMIT server (root@69.63.219.52)")
        print("  all          All hosts (default)")
        return

    if target == "all":
        targets = list(MACHINES.keys())
    elif target in MACHINES:
        targets = [target]
    else:
        print(f"Unknown host: {target}")
        print("Available: local, workstation, dmit, all")
        sys.exit(1)

    first = True
    for t in targets:
        if not first:
            print()
        first = False
        cfg = MACHINES[t]
        info = get_machine_info(
            remote=cfg["remote"],
            ssh_args=cfg.get("ssh_args", ""),
            services=cfg.get("services", []),
        )
        if not info:
            print(f"--- {cfg['label']} ---")
            print("  Failed to connect")
        else:
            print_info(info, cfg["label"], services=info.get("services", []))
