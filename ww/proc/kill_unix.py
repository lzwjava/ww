#!/usr/bin/env python3

import subprocess
import re


def find_process_on_port(port):
    """Find the process ID using the specified port on Unix systems (macOS/Linux)."""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 2:
                    return parts[1], f"{parts[0]} ({parts[1]})"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return None, None


def find_processes_by_pattern(pattern):
    """Find all process IDs matching the specified pattern on Unix systems (macOS/Linux)."""
    processes = []
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:
                if pattern.lower() in line.lower():
                    parts = line.split()
                    if len(parts) >= 11:
                        pid = parts[1]
                        command = " ".join(parts[10:])
                        processes.append((pid, f"{command} ({pid})"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return processes


def get_process_details(pid):
    """Get detailed information about a process on Unix systems (macOS/Linux)."""
    try:
        ps_result = subprocess.run(
            ["ps", "-p", pid, "-o", "pid,ppid,lstart,etime,command"],
            capture_output=True,
            text=True,
        )
        if ps_result.returncode == 0:
            lines = ps_result.stdout.strip().split("\n")
            if len(lines) > 1:
                data_line = next(
                    (
                        line.strip()
                        for line in lines[1:]
                        if line.strip().startswith(pid)
                    ),
                    None,
                )
                if data_line:
                    match = re.match(
                        r"(\d+)\s+(\d+)\s+(.*?)\s+([0-9-]+:[0-9:]+)\s+(.+)", data_line
                    )
                    if match:
                        pid_val, ppid_val, lstart_val, etime_val, command_val = (
                            match.groups()
                        )
                        return {
                            "name": command_val.split()[0],
                            "pid": pid_val,
                            "ppid": ppid_val,
                            "started": lstart_val,
                            "elapsed": etime_val,
                            "command": command_val,
                            "app_info": None,
                        }
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        pass

    return None


def print_process_details(process_info, details):
    """Print process information from a get_process_details result."""
    print(f"  Name: {process_info}")
    if not details:
        print("  (Unable to retrieve detailed process information)")
        return
    for key, label in [
        ("app_info", "Application"),
        ("started", "Started"),
        ("elapsed", "Running for"),
        ("ppid", "Parent PID"),
    ]:
        if details.get(key):
            print(f"  {label}: {details[key]}")
    if details.get("name") == "java" and details.get("command"):
        print(f"  Command: {details['command']}")


def kill_process(pid):
    """Kill the process with the specified PID on Unix systems (macOS/Linux)."""
    try:
        check = subprocess.run(["ps", "-p", pid], capture_output=True, text=True)
        if check.returncode != 0:
            return True
        subprocess.run(["kill", "-9", pid], capture_output=True, text=True, check=False)
        verify = subprocess.run(["ps", "-p", pid], capture_output=True, text=True)
        return verify.returncode != 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
