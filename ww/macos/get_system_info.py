#!/usr/bin/env python3
"""
System Information Script for macOS
"""

import platform
import subprocess
import os
import sys


def run_command(cmd, fallback=None):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return fallback
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        return fallback


def get_os_info():
    try:
        result = subprocess.run(["sw_vers"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            os_info = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    os_info[key.strip()] = value.strip()

            product_name = os_info.get("ProductName", "macOS")
            product_version = os_info.get("ProductVersion", "Unknown")
            build_version = os_info.get("BuildVersion", "Unknown")

            return f"{product_name} {product_version} (Build {build_version})"
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass

    return run_command("uname -srm")


def get_architecture():
    machine = platform.machine().lower()
    if machine == "x86_64":
        return "Intel 64-bit"
    elif machine == "arm64":
        return "Apple Silicon 64-bit"
    else:
        return f"{machine} ({'64-bit' if sys.maxsize > 2**32 else '32-bit'})"


def get_python_version():
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_java_version():
    for java_cmd in ["java", "java8", "java11", "java17", "java21"]:
        version = run_command(f"{java_cmd} -version 2>&1 | head -n 1")
        if version and ("java" in version.lower() or "openjdk" in version.lower()):
            if '"' in version:
                return version.split('"')[1]
            return version.split()[2] if len(version.split()) > 2 else version
    return "Java not found"


def get_macos_ui_info():
    desktop_info = []

    appearance = run_command("defaults read -g AppleInterfaceStyle 2>/dev/null")
    if appearance:
        desktop_info.append(f"Appearance: Dark Mode ({appearance})")
    else:
        desktop_info.append("Appearance: Light Mode")

    if os.environ.get("DISPLAY") or os.environ.get("TERM_PROGRAM") != "Apple_Terminal":
        desktop_info.append("Desktop: GUI Session")
    else:
        desktop_info.append("Desktop: Console Session")

    return "; ".join(desktop_info)


def get_kernel_info():
    return run_command("uname -r")


def get_disk_info():
    try:
        result = subprocess.run(
            "df -h /", shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                root_line = lines[1]
                parts = root_line.split()
                if len(parts) >= 6:
                    total = parts[1]
                    used = parts[2]
                    available = parts[3]
                    use_percent = parts[4]
                    mount = parts[5]
                    return f"Total: {total}, Used: {used} ({use_percent}), Available: {available} (mounted on {mount})"
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass
    return "Unable to retrieve disk information"


def get_memory_info():
    try:
        total_cmd = run_command("sysctl -n hw.memsize")
        if total_cmd:
            total_bytes = int(total_cmd)
            total_gb = total_bytes / (1024**3)

            pressure = run_command("sysctl -n kern.memorystatus_vm_pressure_level")
            pressure_text = ""
            if pressure:
                pressure_levels = {"0": "Normal", "1": "Warning", "2": "Critical"}
                pressure_text = f" (Pressure: {pressure_levels.get(pressure, pressure)})"

            vm_stat = run_command("vm_stat")
            if vm_stat:
                lines = vm_stat.split("\n")
                pages_free = 0
                pages_active = 0
                pages_wired = 0
                page_size = 4096

                for line in lines:
                    if "Pages free:" in line:
                        pages_free = int(line.split(":")[1].strip().replace(".", ""))
                    elif "Pages active:" in line:
                        pages_active = int(line.split(":")[1].strip().replace(".", ""))
                    elif "Pages wired down:" in line or "Pages wired:" in line:
                        pages_wired = int(line.split(":")[1].strip().replace(".", ""))

                used_pages = pages_active + pages_wired
                used_gb = (used_pages * page_size) / (1024**3)
                available_gb = (pages_free * page_size) / (1024**3)
                used_percent = (used_gb / total_gb) * 100

                return f"Total: {total_gb:.1f} GB, Used: {used_gb:.1f} GB ({used_percent:.1f}%), Available: {available_gb:.1f} GB{pressure_text}"
    except (ValueError, subprocess.SubprocessError):
        pass
    return "Unable to retrieve memory information"


def get_gpu_info():
    gpu_info = []

    for vendor, label in [("Intel", "Intel Integrated Graphics"), ("AMD", "AMD GPU"), ("NVIDIA", "NVIDIA GPU"), ("Apple", "Apple Silicon GPU")]:
        info = run_command(f"system_profiler SPDisplaysDataType | grep -A 5 '{vendor}'")
        if info:
            gpu_info.append(f"{label}: {info.strip()}")

    if not gpu_info:
        display_info = run_command("system_profiler SPDisplaysDataType | grep -A 10 'Graphics'")
        if display_info:
            gpu_info.append(f"Display: {display_info.strip()}")

    return "\n".join(gpu_info) if gpu_info else "Unable to detect GPU information"


def get_macos_hardware_info():
    hardware_info = []

    model = run_command("sysctl -n hw.model")
    if model:
        hardware_info.append(f"Model: {model}")

    cpu_brand = run_command("sysctl -n machdep.cpu.brand_string")
    if cpu_brand:
        hardware_info.append(f"CPU: {cpu_brand}")

    cpu_cores = run_command("sysctl -n hw.ncpu")
    if cpu_cores:
        hardware_info.append(f"Cores: {cpu_cores}")

    serial = run_command("system_profiler SPHardwareDataType | grep 'Serial Number' | awk -F': ' '{print $2}'")
    if serial:
        hardware_info.append(f"Serial: {serial}")

    return "; ".join(hardware_info) if hardware_info else "Unable to retrieve hardware info"


def main():
    print("=== macOS System Information ===")
    print()

    print("macOS Information:")
    print(f"  Version: {get_os_info()}")
    print(f"  Architecture: {get_architecture()}")

    kernel = get_kernel_info()
    if kernel:
        print(f"  Kernel: {kernel}")
    print()

    hardware = get_macos_hardware_info()
    if hardware != "Unable to retrieve hardware info":
        print("Hardware Details:")
        print(f"  {hardware}")
        print()

    print("Programming Languages:")
    print(f"  Python: {get_python_version()}")
    print(f"  Java: {get_java_version()}")
    print()

    print("User Interface:")
    print(f"  {get_macos_ui_info()}")
    print()

    print("System Resources:")
    print(f"  Disk: {get_disk_info()}")
    print(f"  Memory: {get_memory_info()}")
    print(f"  GPU: {get_gpu_info()}")
    print()
