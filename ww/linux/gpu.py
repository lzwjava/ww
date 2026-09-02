#!/usr/bin/env python3
"""
GPU Information Script for Linux Systems
Collects and displays GPU information including NVIDIA (proprietary & Nouveau),
AMD, Intel GPUs and memory usage where available.
"""

import glob
import os
import subprocess


def run_command(cmd, fallback=None):
    """Run a command and return its output, or fallback if it fails."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return fallback
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        return fallback


def detect_gpus():
    """Detect GPUs by scanning /sys/class/drm and lspci."""
    gpus = []
    cards = sorted(glob.glob("/sys/class/drm/card[0-9]*"))
    for card in cards:
        uevent_path = os.path.join(card, "device", "uevent")
        if not os.path.exists(uevent_path):
            continue
        uevent = open(uevent_path).read()
        if "PCI_CLASS=30000" not in uevent:
            continue
        driver = "unknown"
        for line in uevent.splitlines():
            if line.startswith("DRIVER="):
                driver = line.split("=", 1)[1]
                break
        pci_id = None
        for line in uevent.splitlines():
            if line.startswith("PCI_SLOT_NAME="):
                pci_id = line.split("=", 1)[1]
                break
        name = "Unknown GPU"
        if pci_id:
            name_line = run_command(f"lspci -s {pci_id} 2>/dev/null | head -1")
            if name_line:
                name = name_line.split(":", 2)[-1].strip()
        gpus.append({
            "card": os.path.basename(card),
            "pci_id": pci_id,
            "driver": driver,
            "name": name,
        })
    return gpus


def get_nvidia_proprietary_info(gpu):
    """Get memory info via nvidia-smi for proprietary driver."""
    out = run_command(
        "nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free "
        "--format=csv,noheader,nounits"
    )
    if not out or "failed" in out.lower():
        return None
    lines = []
    for i, line in enumerate(out.strip().split("\n")):
        parts = [p.strip().strip('"') for p in line.split(",")]
        if len(parts) >= 4:
            lines.append(
                f"  NVIDIA {parts[0]}: {parts[1]} MiB total, {parts[2]} MiB used, {parts[3]} MiB free"
            )
    return "\n".join(lines)


def get_nouveau_memory_info():
    """Get Nouveau VRAM info from eglinfo/glxinfo using GL_NVX_gpu_memory_info."""
    info = {}
    # Try eglinfo first (more detailed for NVX extension)
    egl_out = run_command("eglinfo 2>/dev/null")
    glx_out = run_command("glxinfo 2>/dev/null")
    combined = (egl_out or "") + "\n" + (glx_out or "")
    for line in combined.splitlines():
        if "Dedicated video memory:" in line:
            try:
                info["total_mb"] = int(line.split(":")[-1].strip().split()[0])
            except ValueError:
                pass
        if "Currently available dedicated video memory:" in line:
            try:
                info["free_mb"] = int(line.split(":")[-1].strip().split()[0])
            except ValueError:
                pass
        if "Video memory:" in line and "total_mb" not in info:
            try:
                info["total_mb"] = int(line.split(":")[-1].strip().split()[0])
            except ValueError:
                pass
    if "total_mb" in info and "free_mb" in info:
        used = info["total_mb"] - info["free_mb"]
        return f"  {info['total_mb']} MiB total, {used} MiB used, {info['free_mb']} MiB free"
    if "total_mb" in info:
        return f"  {info['total_mb']} MiB total (free/used unavailable)"
    return None


def get_amd_memory_info(card):
    """Get AMDGPU VRAM info from sysfs."""
    base = f"/sys/class/drm/{card}/device"
    try:
        with open(os.path.join(base, "mem_info_vram_total")) as f:
            total = int(f.read().strip()) // (1024 * 1024)
        with open(os.path.join(base, "mem_info_vram_used")) as f:
            used = int(f.read().strip()) // (1024 * 1024)
        free = total - used
        return f"  {total} MiB total, {used} MiB used, {free} MiB free"
    except FileNotFoundError:
        return None


def get_gpu_temperature(card):
    """Read GPU temperature from hwmon if available."""
    hwmon_dirs = glob.glob(f"/sys/class/drm/{card}/device/hwmon/hwmon*")
    for h in hwmon_dirs:
        temp_path = os.path.join(h, "temp1_input")
        if os.path.exists(temp_path):
            try:
                with open(temp_path) as f:
                    temp = int(f.read().strip())
                return f"{temp / 1000:.1f}°C"
            except ValueError:
                continue
    return None


def get_renderer_info():
    """Get OpenGL renderer string."""
    glx = run_command("glxinfo 2>/dev/null | grep 'OpenGL renderer string'")
    if glx:
        return glx.split(":", 1)[-1].strip()
    egl = run_command("eglinfo 2>/dev/null | grep 'OpenGL.*renderer:' | head -1")
    if egl:
        return egl.split(":", 1)[-1].strip()
    return None


def get_cuda_info():
    """Get CUDA and NVIDIA driver information."""
    cuda_versions = []
    driver_version = run_command(
        "nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits"
    )
    if driver_version and "failed" not in driver_version.lower():
        cuda_versions.append(f"NVIDIA Driver: {driver_version}")
    cuda_version = run_command(
        "nvidia-smi --query-gpu=cuda_runtime_version --format=csv,noheader,nounits"
    )
    if cuda_version and "failed" not in cuda_version.lower():
        cuda_versions.append(f"CUDA Runtime: {cuda_version}")
    nvcc_version = run_command(
        "nvcc --version | grep -i 'release' | awk '{print $6}' | cut -d',' -f1"
    )
    if nvcc_version and nvcc_version != "":
        cuda_versions.append(f"NVCC Compiler: {nvcc_version}")
    cudnn_major = run_command(
        "cat /usr/include/cudnn_version.h 2>/dev/null | grep -w CUDNN_MAJOR | awk '{print $3}' | tr -d ';' | xargs"
    )
    if cudnn_major:
        cudnn_minor = run_command(
            "cat /usr/include/cudnn_version.h 2>/dev/null | grep -w CUDNN_MINOR | awk '{print $3}' | tr -d ';'"
        )
        cudnn_patch = run_command(
            "cat /usr/include/cudnn_version.h 2>/dev/null | grep -w CUDNN_PATCHLEVEL | awk '{print $3}' | tr -d ';'"
        )
        cuda_versions.append(f"cuDNN: {cudnn_major}.{cudnn_minor or '0'}.{cudnn_patch or '0'}")
    if cuda_versions:
        return "\n".join(cuda_versions)
    return None


def get_vulkan_info():
    """Get Vulkan information if available."""
    vulkan_info = []
    vulkan_icd = run_command(
        "vulkaninfo --summary 2>/dev/null | grep -i 'device name' | head -3"
    )
    if vulkan_icd:
        vulkan_info.append(f"Devices: {vulkan_icd}")
    vulkan_sdk = run_command(
        "vulkaninfo --summary 2>/dev/null | grep -i 'vulkan' | head -1"
    )
    if vulkan_sdk:
        vulkan_info.append(f"Runtime: {vulkan_sdk}")
    if vulkan_info:
        return "\n".join(vulkan_info)
    return None


def tool_available(name):
    """Check if a CLI tool is available."""
    return run_command(f"which {name} 2>/dev/null") is not None


def run():
    """Main function to collect and display GPU information."""
    gpus = detect_gpus()
    if not gpus:
        print("No GPU detected via DRM subsystem.")
        pci_gpus = run_command("lspci | grep -i vga")
        if pci_gpus:
            print("PCI VGA devices:")
            for line in pci_gpus.strip().split("\n"):
                print(f"  {line}")
        print()
    else:
        for gpu in gpus:
            print(f"GPU: {gpu['name']}")
            print(f"  Driver: {gpu['driver']}")
            temp = get_gpu_temperature(gpu["card"])
            if temp:
                print(f"  Temperature: {temp}")
            if gpu["driver"] == "nvidia":
                info = get_nvidia_proprietary_info(gpu)
                if info:
                    print("  Memory:")
                    print(info)
                else:
                    print("  nvidia-smi unavailable.")
            elif gpu["driver"] == "nouveau":
                mem = get_nouveau_memory_info()
                if mem:
                    print("  Memory:")
                    print(mem)
                else:
                    print("  VRAM usage not available via standard interfaces.")
                renderer = get_renderer_info()
                if renderer:
                    print(f"  Renderer: {renderer}")
            elif gpu["driver"] == "amdgpu":
                mem = get_amd_memory_info(gpu["card"])
                if mem:
                    print("  Memory:")
                    print(mem)
                else:
                    print("  VRAM sysfs read failed.")
            elif gpu["driver"] == "i915":
                print("  Intel GPU detected.")
            else:
                print(f"  Unknown driver '{gpu['driver']}' — limited info available.")
            print()

    # CUDA info (only if nvidia proprietary tools exist)
    cuda = get_cuda_info()
    if cuda:
        print("CUDA / NVIDIA Driver:")
        for line in cuda.split("\n"):
            print(f"  {line}")
        print()

    # Vulkan info
    vulkan = get_vulkan_info()
    if vulkan:
        print("Vulkan:")
        for line in vulkan.split("\n"):
            print(f"  {line}")
        print()

    # Recommendations
    print("Tools:")
    if tool_available("nvtop"):
        print("  nvtop: installed (run `nvtop` for live monitoring)")
    else:
        print("  nvtop: not installed — `sudo apt install nvtop` for live GPU monitoring")
    if any(g["driver"] == "amdgpu" for g in gpus):
        if tool_available("radeontop"):
            print("  radeontop: installed")
        else:
            print("  radeontop: not installed — `sudo apt install radeontop` for AMD live monitoring")
    if any(g["driver"] == "i915" for g in gpus):
        if tool_available("intel_gpu_top"):
            print("  intel_gpu_top: installed")
        else:
            print("  intel_gpu_top: not installed — `sudo apt install intel-gpu-tools` for Intel live monitoring")
    if any(g["driver"] == "nouveau" for g in gpus):
        print("  GALLIUM_HUD: set env GALLIUM_HUD=GPU-load+VRAM-usage to see overlay in Mesa apps")
    print()
