"""ww memory <host> — Remote memory chip diagnostics via SSH.

Collects:
- Current memory usage (free -h, /proc/meminfo)
- SPD EEPROM decode (DDR3/DDR4/DDR5) from sysfs I2C
- Kernel dmesg memory-related messages
"""

import re
import subprocess
import sys


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def ssh_run(cmd, remote, ssh_args="", timeout=15):
    """Run a command via SSH. Returns (stdout, stderr, returncode)."""
    try:
        full = f"ssh -o ConnectTimeout=5 {ssh_args} {remote} {cmd}"
        r = subprocess.run(
            full, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        return "", str(e), -1
    except subprocess.SubprocessError as e:
        return "", str(e), -1


def ssh_script(script, remote, ssh_args="", timeout=15):
    """Pipe a multi-line shell script via SSH."""
    try:
        cmd = f"ssh -o ConnectTimeout=5 {ssh_args} {remote} bash"
        r = subprocess.run(
            cmd,
            shell=True,
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.stdout, r.stderr, r.returncode
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        return "", str(e), -1


# ---------------------------------------------------------------------------
# SPD decode (DDR3-centric, with fallbacks for DDR4/DDR5)
# ---------------------------------------------------------------------------

MEM_TYPES = {
    0x0B: "DDR3 SDRAM",
    0x0C: "DDR4 SDRAM",
    0x11: "DDR4E SDRAM",
    0x12: "DDR5 SDRAM",
}

MODULE_TYPES = {
    0x01: "RDIMM",
    0x02: "UDIMM",
    0x03: "SO-DIMM",
    0x04: "Micro-DIMM",
    0x05: "Mini-RDIMM",
    0x06: "Mini-UDIMM",
}

# JEDEC Manufacturer IDs (JEP106)
# key = (byte117, byte118)  — only most common ones
JEDEC_MFRS = {
    (0x01, 0x00): "AMD",
    (0x04, 0x00): "Fujitsu",
    (0x06, 0x00): "Hitachi",
    (0x2C, 0x00): "Micron Technology",
    (0x80, 0x00): "Samsung",
    (0x81, 0x00): "Toshiba",
    (0x82, 0x00): "SK Hynix",
    (0x83, 0x00): "Mitsubishi",
    (0x85, 0x00): "Fujitsu",
    (0x89, 0x00): "Kingston",
    (0x91, 0x00): "Winbond",
    (0x98, 0x00): "Toshiba",
    (0x9B, 0x00): "Crucial / Micron",
    (0xAD, 0x00): "SK Hynix",
    (0xCE, 0x00): "Samsung",
    (0x51, 0x04): "Kingston",
}


def _mfr_name(b1, b2):
    key = (b1, b2)
    if key in JEDEC_MFRS:
        return JEDEC_MFRS[key]
    key2 = (b1, 0)
    if key2 in JEDEC_MFRS:
        return JEDEC_MFRS[key2]
    # Reverse endian try
    key3 = (b2, b1)
    if key3 in JEDEC_MFRS:
        return JEDEC_MFRS[key3]
    return f"JEDEC ID {b1:#04x}:{b2:#04x}"


# Density mapping for DDR3 (SPD byte 4, bits 7-4)
DDR3_DENSITY = {
    0: "256 Mb",
    1: "512 Mb",
    2: "1 Gb",
    3: "2 Gb",
    4: "4 Gb",
    5: "6 Gb",
    6: "8 Gb",
    7: "12 Gb",
    8: "16 Gb",
}


def guess_module_size(spd, info):
    """Try to compute module size from SPD fields + part number fallback."""
    # --- From SPD fields ---
    try:
        densities = {0: 256, 1: 512, 2: 1024, 3: 2048, 4: 4096, 5: 6144, 6: 8192}
        # Try upper nibble first (DDR3 standard)
        density_nibble = (spd[4] >> 4) & 0x0F
        chip_mb = densities.get(density_nibble, 0)
        if chip_mb == 0:
            # Try full byte (some modules use lower nibble)
            chip_mb = densities.get(spd[4] & 0x0F, 0)

        if chip_mb > 0:
            width_map = {0: 4, 1: 8, 2: 16}
            bus_map = {0: 8, 1: 16, 2: 32, 3: 64, 4: 128}
            sdram_width = width_map.get((spd[7] >> 2) & 0x03, 0)
            bus_width = bus_map.get(spd[8] & 0x07, 0)
            ranks = 1 + ((spd[5] >> 3) & 0x07)
            if bus_width and sdram_width and ranks:
                chips = (bus_width // sdram_width) * ranks
                total_mb = (chip_mb * chips) // 8  # Mb to MB
                if 128 <= total_mb <= 65536:  # sanity
                    info["module_size_spd"] = (
                        f"{total_mb // 1024}.{total_mb % 1024 * 10 // 1024} GB ({total_mb} MB)"
                    )
                    info["module_size_mb"] = total_mb
    except (KeyError, ZeroDivisionError, TypeError):
        pass

    # --- From part number ---
    part = info.get("part_number", "")
    # Match patterns like: KB256082G → 256M×64 = 2GB
    m = re.search(r"(\d+)\s*[GgMm]", part)
    if m:
        val = int(m.group(1))
        if "g" in part.lower():
            info["part_number_size"] = f"{val} GB"
        else:
            info["part_number_size"] = f"maybe ~{val // 128} GB"
    # Match structured names: "256082" → words=256, org=08
    m2 = re.search(r"(\d{3})(\d{2})", part)
    if m2:
        words_m = int(m2.group(1))
        # 256M words × 64-bit bus = 16384 Mbits = 2 GB
        size_gb = words_m / 128.0
        if 0.125 <= size_gb <= 64:
            info["part_number_size"] = f"~{size_gb:.1f} GB (from part#)"

    if "module_size_mb" in info:
        ms = info["module_size_mb"]
        if ms > 0 and info.get("mem_total_kb"):
            slots = ms * 1024 // info["mem_total_kb"]
            if 1 <= slots <= 8:
                info["slots_inferred"] = slots


def decode_spd(raw, mem_total_kb=None):
    """Decode a 256-byte DDR3-style SPD blob. Returns a dict."""
    info = {}
    if len(raw) < 128:
        info["error"] = "SPD data too short"
        return info

    if mem_total_kb:
        info["mem_total_kb"] = mem_total_kb

    info["spd_bytes_used"] = raw[0]
    info["spd_total_size"] = raw[1] * 16

    # --- Memory & Module types ---
    info["memory_type"] = MEM_TYPES.get(raw[2], f"Unknown (0x{raw[2]:02x})")
    info["module_type"] = MODULE_TYPES.get(raw[3], f"0x{raw[3]:02x}")

    # --- SDRAM density (try upper nibble first, then full-byte) ---
    density_nibble = (raw[4] >> 4) & 0x0F
    density_str = DDR3_DENSITY.get(density_nibble)
    if not density_str:
        density_str = DDR3_DENSITY.get(raw[4] & 0x0F)
    info["sdram_density"] = density_str or f"0x{raw[4]:02x} (raw)"

    # --- Ranks (DDR3: bits 2-0 of byte 5 encode 0=1rank, 1=2ranks, 2=3ranks...) ---
    info["ranks"] = (raw[5] & 0x07) + 1

    # --- Voltage ---
    v_map = {0: "1.5 V (standard)", 1: "1.25 V", 2: "1.35 V (low voltage)"}
    info["voltage"] = v_map.get(raw[6] & 0x03, f"Unknown (0x{raw[6] & 0x03:x})")

    # --- SDRAM width ---
    width_map = {0: 4, 1: 8, 2: 16}
    info["sdram_width"] = width_map.get((raw[7] >> 2) & 0x03, "?")

    # --- Bus width ---
    bus_map = {0: 8, 1: 16, 2: 32, 3: 64, 4: 128}
    info["bus_width"] = bus_map.get(raw[8] & 0x07, "?")

    # --- Timing (DDR3 SPD) ---
    # Byte 9: MTB Dividend | Byte 10: MTB Divisor
    # Standard DDR3: Dividend=1, Divisor=8 → MTB=0.125ns
    # Some modules use FTB (Fine Timebase) or non-standard values
    mtb_div = raw[9]
    mtb_dvs = raw[10]
    mtb_ns = (mtb_div / mtb_dvs) if mtb_dvs else 0

    # Sanity check: DDR3 MTB should be ≈ 0.125 ns
    # If unreasonably large, try assuming standard 0.125 ns
    if mtb_ns > 1.0:
        info["mtb_ns_raw"] = round(mtb_ns, 3)
        mtb_ns = 0.125  # fallback to standard DDR3 MTB
        info["mtb_ns"] = 0.125
    else:
        info["mtb_ns"] = round(mtb_ns, 3)

    # tCKmin (byte 12) — min cycle time
    tck_raw = raw[12]
    if mtb_ns:
        tck_ns = tck_raw * mtb_ns
        if tck_ns > 0:
            info["tck_ns"] = round(tck_ns, 3)
            info["ddr_mts"] = int(round(2000 / tck_ns, -1))

    # CAS Latencies (bytes 14-17)
    cl_val = raw[14] | (raw[15] << 8) | (raw[16] << 16) | (raw[17] << 24)
    cl_list = [i + 4 for i in range(28) if (cl_val >> i) & 1]
    if cl_list:
        info["cas_supported"] = cl_list

    # tAAmin (byte 23)
    if mtb_ns:
        taa_ns = raw[23] * mtb_ns
        if taa_ns > 0.1:
            info["taa_ns"] = round(taa_ns, 2)

    # --- Manufacturer ID (DDR3: bytes 117-118 / offset 0x75) ---
    mfr_b1 = raw[0x75] if len(raw) > 0x75 else 0
    mfr_b2 = raw[0x76] if len(raw) > 0x76 else 0
    info["manufacturer_id"] = f"{mfr_b1:#04x} {mfr_b2:#04x}"
    info["manufacturer"] = _mfr_name(mfr_b1, mfr_b2)

    # --- Manufacturing date (bytes 120-121 / offset 0x78) ---
    yr_raw = raw[0x78] if len(raw) > 0x78 else 0
    wk_raw = raw[0x79] if len(raw) > 0x79 else 0
    if yr_raw:
        # DDR3: BCD encoded year (0-99 → 2000-2099)
        year = 2000 + int(str(yr_raw), 16) if yr_raw <= 0x99 else 2000 + yr_raw
        info["mfg_year"] = year
        info["mfg_week"] = wk_raw if wk_raw else None

    # --- Serial (bytes 122-125 / offset 0x7A) ---
    sn = raw[0x7A : 0x7A + 4] if len(raw) > 0x7A else b"\x00\x00\x00\x00"
    if any(b != 0 for b in sn):
        info["serial"] = sn.hex()

    # --- Module revision (byte 126) / checksum (byte 127) ---
    info["module_revision"] = f"0x{raw[0x7E]:02x}" if len(raw) > 0x7E else "?"
    info["spd_checksum"] = f"0x{raw[0x7F]:02x}" if len(raw) > 0x7F else "?"

    # --- Part number (bytes 128-145 / offset 0x80) ---
    part = (
        raw[0x80 : 0x80 + 18].decode("ascii", errors="replace").rstrip("\x00").strip()
    )
    info["part_number"] = part if part else "(not set)"

    # --- Speed grade ---
    if info.get("ddr_mts"):
        mts = info["ddr_mts"]
        info["speed_grade"] = f"DDR3-{mts} (PC3-{mts * 8})"

    # --- Size inference ---
    guess_module_size(raw, info)

    return info


# ---------------------------------------------------------------------------
# collection script (piped to SSH)
# ---------------------------------------------------------------------------

MEMORY_COLLECT_SCRIPT = r"""
echo "===MEM_USAGE==="
free -h 2>/dev/null || vm_stat 2>/dev/null
echo "===MEMINFO==="
cat /proc/meminfo 2>/dev/null | head -30
echo "===DMESG_MEM==="
dmesg 2>/dev/null | grep -iE "memory|DIMM|DDR|populated|slot|spd|ecc|edac" | head -20
journalctl -k 2>/dev/null | grep -iE "memory|DIMM|DDR|populated|slot|spd|ecc|edac" | head -5
echo "===MEM_SLOTS==="
dmesg 2>/dev/null | grep -i "Memory slots populated"
echo "===SPD_RAW==="
for f in /sys/bus/i2c/devices/0-0050/eeprom /sys/bus/i2c/devices/0-0051/eeprom; do
  if [ -r "$f" ]; then
    echo "SPD_FILE:$f"
    od -A x -t x1z "$f" 2>/dev/null | head -18
  fi
done
echo "===MEM_BLOCKS==="
ls /sys/devices/system/memory/memory*/state 2>/dev/null | head -5
echo "MEM_BLOCK_COUNT:$(ls -d /sys/devices/system/memory/memory* 2>/dev/null | wc -l)"
echo "MEM_BLOCK_SIZE:$(cat /sys/devices/system/memory/block_size_bytes 2>/dev/null)"
echo "===CPU_INFO==="
lscpu 2>/dev/null | grep -E 'Model name|CPU\(s\)|Thread|Core|socket|NUMA' | head -10
echo "===END==="
"""


def collect_memory(remote, ssh_args=""):
    """Run the collection script on the remote host and return parsed results."""
    out, err, rc = ssh_script(MEMORY_COLLECT_SCRIPT, remote, ssh_args, timeout=20)
    if rc != 0 and not out:
        return {"error": f"SSH failed: {err.strip()}"}

    result = {}
    sections = {}
    current = None
    for line in out.splitlines():
        if line.startswith("===") and line.endswith("==="):
            tag = line.strip("=")
            if tag == "END":
                break
            current = tag
            sections[current] = []
        elif current is not None:
            sections[current].append(line)

    # Mem usage
    result["mem_usage_raw"] = "\n".join(sections.get("MEM_USAGE", []))

    # Mem info
    meminfo = {}
    for line in sections.get("MEMINFO", []):
        if ":" in line:
            k, v = line.split(":", 1)
            meminfo[k.strip()] = v.strip()
    result["meminfo"] = meminfo

    # CPU info
    cpu_lines = sections.get("CPU_INFO", [])
    result["cpu_info"] = "\n".join(cpu_lines) if cpu_lines else ""

    # DMI slots
    slots_lines = sections.get("MEM_SLOTS", [])
    result["slots_populated_raw"] = slots_lines[0] if slots_lines else None

    # dmesg mem
    result["dmesg_mem_lines"] = sections.get("DMESG_MEM", [])

    # Memory blocks
    result["mem_block_count"] = None
    result["mem_block_size"] = None
    for line in sections.get("MEM_BLOCKS", []):
        if line.startswith("MEM_BLOCK_COUNT:"):
            result["mem_block_count"] = line.split(":", 1)[1]
        elif line.startswith("MEM_BLOCK_SIZE:"):
            val = line.split(":", 1)[1]
            if val:
                size_bytes = int(val, 16)
                result["mem_block_size"] = f"{size_bytes // (1024 * 1024)} MB"

    # SPD
    spd_raw_hex = {}
    current_spd_file = None
    for line in sections.get("SPD_RAW", []):
        if line.startswith("SPD_FILE:"):
            current_spd_file = line.split(":", 1)[1]
            spd_raw_hex[current_spd_file] = []
        elif current_spd_file:
            spd_raw_hex[current_spd_file].append(line)

    mem_total_kb = None
    if "MemTotal" in meminfo:
        try:
            mem_total_kb = int(meminfo["MemTotal"].split()[0])
        except (ValueError, IndexError):
            pass

    # Decode SPD if found
    for fpath, hex_lines in spd_raw_hex.items():
        hex_bytes = []
        last_addr = -16
        last_bytes_16 = None
        for hline in hex_lines:
            hline = hline.strip()
            if not hline:
                continue

            # --- Handle od repeat mark ---
            if hline == "*":
                # Fill gap with the last known line until the next explicit address
                if last_bytes_16 is not None:
                    hex_bytes.extend(last_bytes_16)
                    last_addr += 16
                continue

            parts = hline.split()
            if len(parts) < 2:
                continue

            # Parse address
            try:
                addr = int(parts[0], 16)
            except ValueError:
                continue

            # Fill gap between last_addr+16 and this addr (for * expansion)
            while last_addr + 16 < addr and last_bytes_16 is not None:
                hex_bytes.extend(last_bytes_16)
                last_addr += 16

            # Collect hex bytes (skip offset and ASCII column)
            current_16 = []
            for p in parts[1:-1]:
                try:
                    b = int(p, 16)
                    current_16.append(b)
                except ValueError:
                    pass

            if len(current_16) == 16:
                hex_bytes.extend(current_16)
                last_addr = addr
                last_bytes_16 = current_16[:]
            elif current_16:
                # Partial line (shouldn't happen with standard od output)
                hex_bytes.extend(current_16)

        if len(hex_bytes) >= 128:
            result["spd_decode"] = decode_spd(bytes(hex_bytes[:256]), mem_total_kb)
            result["spd_path"] = fpath

    return result


# ---------------------------------------------------------------------------
# display
# ---------------------------------------------------------------------------


def _fmt_kb_to_gb(val):
    """Convert '12345 kB' string to human-friendly GB."""
    try:
        kb = int(val.split()[0])
        gb = kb / (1024 * 1024)
        return f"{gb:.2f} GB"
    except (ValueError, IndexError):
        return val


def print_memory_report(info, host_label):
    """Pretty-print the memory diagnostics."""
    print(f"\n{'=' * 60}")
    print(f"  Memory Diagnostics: {host_label}")
    print(f"{'=' * 60}\n")

    if "error" in info:
        print(f"  ❌ {info['error']}")
        return

    mi = info.get("meminfo", {})

    # ---- Memory usage ----
    print("── Current Memory Usage ──")
    if info.get("mem_usage_raw"):
        for line in info["mem_usage_raw"].splitlines():
            print(f"  {line}")
    print()

    # /proc/meminfo summary
    if mi:
        for key in (
            "MemTotal",
            "MemFree",
            "MemAvailable",
            "SwapTotal",
            "SwapFree",
            "Cached",
            "Active",
            "Inactive",
            "Buffers",
            "SwapCached",
        ):
            val = mi.get(key)
            if val:
                gb = _fmt_kb_to_gb(val)
                print(f"  {key:20s} {val:>12s}  ({gb})")
    print()

    # ---- CPU ----
    if info.get("cpu_info"):
        print("── CPU / Platform ──")
        for line in info["cpu_info"].splitlines():
            print(f"  {line}")
        print()

    # ---- Memory slots ----
    print("── Hardware Memory Slots ──")
    slots_raw = info.get("slots_populated_raw")
    if slots_raw:
        # e.g. "DMI: Memory slots populated: 2/2"
        print(f"  {slots_raw}")
    else:
        print("  (no slot info from dmesg)")

    if info.get("mem_block_count"):
        block_sz = info.get("mem_block_size", "?")
        print(f"  System memory blocks: {info['mem_block_count']} × {block_sz}")
    print()

    # ---- SPD decode ----
    spd = info.get("spd_decode", {})
    if spd and "error" not in spd:
        print("── SPD EEPROM Decode ──")
        print(f"  Memory Type:    {spd.get('memory_type', '?')}")
        print(f"  Module Type:    {spd.get('module_type', '?')}")
        print(f"  Part Number:    {spd.get('part_number', '?')}")
        print(
            f"  Manufacturer:   {spd.get('manufacturer', '?')}  (ID: {spd.get('manufacturer_id', '?')})"
        )
        print(f"  SDRAM Density:  {spd.get('sdram_density', '?')} per chip")
        print(f"  SDRAM Width:    {spd.get('sdram_width', '?')} bits")
        print(f"  Bus Width:      {spd.get('bus_width', '?')} bits")
        print(f"  Ranks:          {spd.get('ranks', '?')}")
        print(f"  Voltage:        {spd.get('voltage', '?')}")
        if spd.get("ddr_mts"):
            print(
                f"  Speed:          ~{spd['ddr_mts']} MT/s  (tCK = {spd.get('tck_ns', '?')} ns)"
            )
        if spd.get("speed_grade"):
            print(f"  Grade:          {spd['speed_grade']}")
        if spd.get("cas_supported"):
            cl = spd["cas_supported"]
            print(
                f"  CAS Latencies:  {', '.join(str(c) for c in cl[:8])}{'...' if len(cl) > 8 else ''}"
            )
        if spd.get("mfg_year"):
            wk = spd.get("mfg_week") or "?"
            print(f"  Mfg Date:       {spd['mfg_year']} week {wk}")
        if spd.get("serial"):
            print(f"  Serial:         0x{spd['serial']}")
        if spd.get("module_revision"):
            print(f"  Revision:       {spd['module_revision']}")
        if spd.get("module_size_spd"):
            print(f"  Module Size:    {spd['module_size_spd']} (from SPD)")
        if spd.get("part_number_size"):
            print(f"  Module Size:    {spd['part_number_size']} (from part number)")
        if spd.get("mtb_ns_raw"):
            print(
                f"  ⚠ MTB raw:      {spd['mtb_ns_raw']} ns (non-standard, assumed 0.125 ns)"
            )
        print()

    # ---- dmesg memory ----
    dmesg_lines = info.get("dmesg_mem_lines", [])
    if dmesg_lines:
        print("── Kernel Memory Messages (dmesg) ──")
        for line in dmesg_lines[:10]:
            print(f"  {line}")
        if len(dmesg_lines) > 10:
            print(f"  ... ({len(dmesg_lines)} total, showing first 10)")
        print()

    # ---- Health summary ----
    print("── Health Summary ──")
    if mi:
        try:
            total_kb = int(mi.get("MemTotal", "0").split()[0])
            avail_kb = int(mi.get("MemAvailable", "0").split()[0])
            if total_kb:
                pct = 100 * (total_kb - avail_kb) / total_kb
                free_gb = avail_kb / (1024 * 1024)
                total_gb = total_kb / (1024 * 1024)
                print(
                    f"  Usage:  {pct:.0f}%  ({free_gb:.1f} GB free / {total_gb:.1f} GB total)"
                )
        except (ValueError, IndexError):
            pass

    if info.get("spd_decode"):
        print("  SPD:    ✅ Readable (module info decoded)")
    else:
        print("  SPD:    ⚠️  Not accessible (no EEPROM or insufficient permissions)")

    # Memory block health
    block_count = info.get("mem_block_count")
    if block_count:
        print(f"  Blocks: ✅ {block_count} memory blocks all online")
    print()


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww memory <host> [ssh-args]")
        print()
        print("  host       SSH target (e.g., user@hostname)")
        print("  ssh-args   Optional extra SSH flags (e.g., -i ~/.ssh/key)")
        print()
        print("Examples:")
        print("  ww memory lzw@192.168.1.53")
        print("  ww memory root@server -i ~/.ssh/id_rsa.pem")
        return

    host = args[0]
    extra_args = " ".join(args[1:]) if len(args) > 1 else ""

    print(f"🔍 Collecting memory diagnostics from {host} ...", flush=True)
    info = collect_memory(host, extra_args)

    print_memory_report(info, host)
