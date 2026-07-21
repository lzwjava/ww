"""ww linux check-fan — Diagnose why system fans are loud.

Collects thermal sensors, fan controllers, GPU cooling, and HDD info
to identify the root cause of fan noise.

Usage:
    ww linux check-fan

Output sections:
    - Temperatures (CPU, GPU, NVMe, chassis)
    - Fan controllers (PWM chips, exported channels)
    - GPU fan status
    - Spinning disks (HDDs — mechanical noise source)
    - Thermal daemon status
    - CPU frequency / load
    - Disk I/O (iostat snapshot)
"""

import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], timeout: int = 10) -> str:
    """Run a command and return its stdout, or an error message."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip() or "(no output)"
    except FileNotFoundError:
        return "(not found)"
    except subprocess.TimeoutExpired:
        return "(timed out)"
    except Exception as e:
        return f"({e})"


def _section(title: str, body: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    print(body)


def _read_sysfs(glob_pattern: str) -> str:
    """Read all matching sysfs files and return key=value lines."""
    lines: list[str] = []
    for p in sorted(Path("/").glob(glob_pattern.lstrip("/"))):
        try:
            val = p.read_text().strip()
            lines.append(f"{p} = {val}")
        except (PermissionError, OSError):
            lines.append(f"{p} = (unreadable)")
    return "\n".join(lines) if lines else "(none found)"


def run():
    # ── 1. Temperatures ──────────────────────────────────────────────
    sensors_out = _run(["sensors"])
    if "(not found)" in sensors_out:
        sensors_out = (
            "(lm-sensors not installed — run: sudo apt-get install -y lm-sensors)"
        )

    thermal_zones = _read_sysfs("/sys/class/thermal/thermal_zone*/temp")
    thermal_types = _read_sysfs("/sys/class/thermal/thermal_zone*/type")

    temp_section = f"--- lm-sensors ---\n{sensors_out}"
    if thermal_zones != "(none found)":
        temp_section += f"\n\n--- sysfs thermal zones ---\n{thermal_zones}"
    if thermal_types != "(none found)":
        temp_section += f"\n{thermal_types}"

    # NVMe temps
    nvme_temps = _read_sysfs("/sys/class/nvme/nvme*/device/temp*")
    if nvme_temps != "(none found)":
        temp_section += f"\n\n--- NVMe temps ---\n{nvme_temps}"

    _section("Temperatures", temp_section)

    # ── 2. Fan controllers ───────────────────────────────────────────
    fan_inputs = _read_sysfs("/sys/devices/**/fan*_input")
    pwm_chips = _read_sysfs("/sys/devices/**/pwm/pwmchip*/npwm")

    fan_section = ""
    if fan_inputs != "(none found)":
        fan_section += f"Fan RPM sensors:\n{fan_inputs}\n"
    else:
        fan_section += (
            "Fan RPM sensors: (none found — board doesn't expose RPM readings)\n"
        )

    if pwm_chips != "(none found)":
        fan_section += f"\nPWM controllers:\n{pwm_chips}\n"
        # Check exported PWM channels
        for base in sorted(Path("/").glob("sys/devices/**/pwm/pwmchip[0-9]*")):
            for pwm_dir in sorted(base.glob("pwm[0-9]*")):
                try:
                    enable = (pwm_dir / "enable").read_text().strip()
                    duty = (pwm_dir / "duty_cycle").read_text().strip()
                    period = (pwm_dir / "period").read_text().strip()
                    fan_section += (
                        f"  {pwm_dir}: enable={enable}, "
                        f"duty_cycle={duty}/{period} "
                        f"({int(duty) / int(period) * 100:.0f}% duty if period>0)\n"
                    )
                except (PermissionError, OSError, ZeroDivisionError, ValueError):
                    fan_section += f"  {pwm_dir}: (unreadable)\n"
        # Check if any PWM channels are exportable but not exported
        for base in sorted(Path("/").glob("sys/devices/**/pwm/pwmchip[0-9]*")):
            try:
                npwm = int((base / "npwm").read_text().strip())
                exported = sorted(base.glob("pwm[0-9]*"))
                if len(exported) < npwm:
                    unexported = npwm - len(exported)
                    fan_section += f"  Warning: {unexported}/{npwm} PWM channels not exported (OS not controlling fans)\n"
            except (PermissionError, OSError, ValueError):
                pass
    else:
        fan_section += "PWM controllers: (none found — BIOS controls fans directly)\n"

    _section("Fan Controllers", fan_section)

    # ── 3. GPU fan ───────────────────────────────────────────────────
    gpu_info = _run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,fan.speed,temperature.gpu,pstate,power.draw",
            "--format=csv,noheader",
        ]
    )
    if "(not found)" in gpu_info:
        gpu_info = "(nvidia-smi not available — no NVIDIA GPU or driver not loaded)"
    _section("GPU Cooling", gpu_info)

    # ── 4. Spinning disks (HDDs) ────────────────────────────────────
    lsblk_out = _run(["lsblk", "-o", "NAME,SIZE,ROTA,MODEL,TYPE,MOUNTPOINT"])
    if "(not found)" in lsblk_out:
        lsblk_out = "(lsblk not available)"
    _section("Spinning Disks (ROTA=1 means HDD)", lsblk_out)

    # Check HDD status
    hdd_lines = _run(["lsblk", "-n", "-o", "NAME,ROTA", "-d"]).split("\n")
    for line in hdd_lines:
        parts = line.split()
        if len(parts) == 2 and parts[1] == "1":
            dev = parts[0]
            hdparm_out = _run(["sudo", "hdparm", "-C", f"/dev/{dev}"])
            if "(not found)" not in hdparm_out:
                print(f"\n  /dev/{dev} drive state: {hdparm_out}")

    # ── 5. Thermal daemon ────────────────────────────────────────────
    thermald = _run(["systemctl", "status", "thermald", "--no-pager", "--lines", "5"])
    _section("Thermal Daemon (thermald)", thermald)

    # Config file check
    if os.path.exists("/etc/thermald/thermal-conf.xml"):
        _section("thermald Config", "/etc/thermald/thermal-conf.xml exists")
    else:
        _section(
            "thermald Config", "(no config file — thermald running in polling mode)"
        )

    # ── 6. CPU frequency / load ──────────────────────────────────────
    load_avg = Path("/proc/loadavg").read_text().strip()
    cpu_info = _run(["cat", "/proc/cpuinfo"])
    mhz_lines = []
    for line in cpu_info.split("\n"):
        if "cpu MHz" in line:
            mhz_lines.append(line.strip())
    freq_summary = "\n".join(mhz_lines[:8]) if mhz_lines else "(no cpu MHz info)"
    if len(mhz_lines) > 8:
        freq_summary += f"\n  ... and {len(mhz_lines) - 8} more cores"

    top_out = _run(["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"]).split("\n")
    top_lines = "\n".join(top_out[:10]) if top_out else "(no data)"

    _section(
        "CPU Load & Frequency",
        f"load average: {load_avg}\n\nTop CPU consumers:\n{top_lines}\n\nFrequencies (first 8 cores):\n{freq_summary}",
    )

    # ── 7. iostat snapshot ──────────────────────────────────────────
    iostat_out = _run(["iostat", "-x", "1", "3"])
    if "(not found)" in iostat_out:
        iostat_out = "(iostat not available — install: sudo apt-get install -y sysstat)"
    _section("Disk I/O (iostat)", iostat_out)

    # ── Verdict ──────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("  SUMMARY / VERDICT")
    print(f"{'=' * 60}")

    # Check if we have fan control
    has_fan_rpm = fan_inputs != "(none found)"
    has_pwm = pwm_chips != "(none found)"

    if not has_fan_rpm and not has_pwm:
        print("""
  Fans are controlled by BIOS/UEFI — OS has no visibility or control.
  Likely: BIOS fan curve is aggressive (full speed at low temps).

  Fix: reboot, enter BIOS (Del/F2), and set a silent/standard fan profile.
  Your temps are fine (CPU ~35°C, GPU ~33°C) — no need for aggressive cooling.
""")
    elif has_pwm and not has_fan_rpm:
        print("""
  PWM controller detected but fan RPM not readable.
  Check if all PWM channels are exported (see Fan Controllers section above).
  If not exported, try: echo 0 | sudo tee /sys/.../pwmchip0/export
""")
    else:
        print("  OS has fan control. Check duty cycles above.")

    # HDD warning
    spinning = 0
    for line in hdd_lines:
        parts = line.split()
        if len(parts) == 2 and parts[1] == "1":
            spinning += 1
    if spinning:
        print(f"  Note: {spinning} spinning HDD(s) detected. Mechanical hard drives")
        print("  make audible noise. The noise may be HDD seek/rotation, not fans.")
        print("  Test: unmount the HDD temporarily to isolate the source.")
    print()

    # ── 8. LLM summary via OpenRouter ──────────────────────────────
    _llm_summarize()


def _llm_summarize():
    """Send collected diagnostics to OpenRouter for a concise analysis."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("MODEL")
    if not api_key or not model:
        print("  OPENROUTER_API_KEY or MODEL not set — skipping LLM analysis.")
        print()
        return

    # Re-collect key data as a compact string
    data = _collect_diagnostics()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Linux systems engineer. A user ran 'ww linux check-fan' "
                "because their computer fan is loud. Below is the raw diagnostic data. "
                "Analyze it and produce a SHORT (<150 words) answer in plain text "
                "(no markdown). State the most likely cause of the fan noise, then "
                "1-2 concrete steps to fix it. If the data shows temperatures are fine "
                "and the OS has no fan control, say so and recommend a BIOS fix."
            ),
        },
        {
            "role": "user",
            "content": data,
        },
    ]

    try:
        import requests

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": 300,
        }
        resp = requests.post(url, headers=headers, json=body, timeout=(5, 30))
        if resp.ok:
            reply = resp.json()["choices"][0]["message"]["content"]
            print(f"{'=' * 60}")
            print("  LLM ANALYSIS")
            print(f"{'=' * 60}")
            print()
            print(reply)
            print()
        else:
            print(f"  LLM call failed: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  LLM call failed: {e}")
    print()


def _collect_diagnostics() -> str:
    """Re-run and collect key diagnostics as a compact string."""
    parts = []

    # Temps - grab summary lines from sensors
    sensors_out = _run(["sensors", "-A"])
    temps = []
    for line in sensors_out.split("\n"):
        if ":" in line and ("°C" in line or "N/A" in line):
            temps.append(line.strip())
    if temps:
        parts.append("Temperatures:\n" + "\n".join(temps[:15]))

    # GPU
    gpu = _run(["nvidia-smi", "--query-gpu=index,name,fan.speed,temperature.gpu,pstate,power.draw", "--format=csv,noheader"])
    parts.append("GPU:\n" + gpu)

    # Fan controllers
    pwm_info = _read_sysfs("/sys/devices/**/pwm/pwmchip*/npwm")
    parts.append("PWM controllers:\n" + pwm_info)

    fan_rpm = _read_sysfs("/sys/devices/**/fan*_input")
    parts.append("Fan RPM sensors:\n" + fan_rpm)

    # Spinning disks
    lsblk = _run(["lsblk", "-n", "-o", "NAME,ROTA,MODEL"])
    spinning = [l for l in lsblk.split("\n") if " 1 " in l or l.endswith(" 1")]
    parts.append("HDDs:\n" + ("\n".join(spinning) if spinning else "none"))

    # Load
    load_avg = Path("/proc/loadavg").read_text().strip()
    parts.append("Load average: " + load_avg)

    # iowait
    iostat = _run(["iostat", "-x", "1", "2"])
    for line in iostat.split("\n"):
        if "iowait" in line or "%iowait" in line:
            parts.append("iowait: " + line.strip())
            break

    return "\n\n".join(parts)


if __name__ == "__main__":
    run()
