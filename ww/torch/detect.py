"""Discover all Python installations and check which have PyTorch installed."""

import os
import subprocess


def _find_python_binaries():
    """Find all python3/python binaries on the system."""
    candidates = set()

    # which -a finds all entries on PATH
    for name in ("python3", "python"):
        try:
            result = subprocess.run(
                ["which", "-a", name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.strip().splitlines():
                path = line.strip()
                if path and os.path.isfile(path):
                    candidates.add(path)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Common locations to probe even if not on PATH
    home = os.path.expanduser("~")
    bin_dirs = [
        "/usr/bin",
        "/usr/local/bin",
        "/opt/homebrew/bin",
        f"{home}/.pyenv/shims",
        f"{home}/.local/bin",
        f"{home}/miniconda3/bin",
        f"{home}/anaconda3/bin",
        f"{home}/miniforge3/bin",
        "/opt/conda/bin",
    ]
    # Also scan any conda envs
    for conda_base in (f"{home}/miniconda3", f"{home}/anaconda3", f"{home}/miniforge3"):
        envs_dir = os.path.join(conda_base, "envs")
        if os.path.isdir(envs_dir):
            for env_name in os.listdir(envs_dir):
                bin_dirs.append(os.path.join(envs_dir, env_name, "bin"))

    # Scan venvs in common project directories
    for proj_dir in (f"{home}/projects", f"{home}/repos"):
        if os.path.isdir(proj_dir):
            for root, dirs, _files in os.walk(proj_dir):
                depth = root[len(proj_dir) :].count(os.sep)
                if depth > 3:
                    dirs[:] = []
                    continue
                if ".venv" in dirs:
                    bin_dirs.append(os.path.join(root, ".venv", "bin"))
                    dirs.remove(".venv")
                if "venv" in dirs:
                    bin_dirs.append(os.path.join(root, "venv", "bin"))
                    dirs.remove("venv")

    # Scan bin dirs for python3, python, and versioned variants (python3.11, etc.)
    import glob as _glob

    for d in bin_dirs:
        if not os.path.isdir(d):
            continue
        for pattern in ("python3", "python", "python3.*"):
            for path in _glob.glob(os.path.join(d, pattern)):
                # Skip symlinks to python3-config, python3-X-config, etc.
                basename = os.path.basename(path)
                if "-config" in basename:
                    continue
                # Skip things like python3-intel64
                if "intel64" in basename:
                    continue
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    candidates.add(path)

    return sorted(candidates)


def _probe_torch(python_path):
    """Run a quick torch probe in the given Python. Returns dict or None."""
    script = r"""
import sys, json
info = {}
try:
    import torch
    info["torch_version"] = torch.__version__
    info["cuda_available"] = torch.cuda.is_available()
    info["cuda_version"] = torch.version.cuda if torch.version.cuda else None
    info["cudnn_version"] = str(torch.backends.cudnn.version()) if torch.backends.cudnn.is_available() else None
    info["device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
    if torch.cuda.is_available() and torch.cuda.device_count() > 0:
        info["gpu_name"] = torch.cuda.get_device_name(0)
    # MPS (Apple Silicon)
    info["mps_available"] = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    print(json.dumps(info))
except ImportError:
    print(json.dumps({"error": "not installed"}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
"""
    try:
        result = subprocess.run(
            [python_path, "-c", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout.strip()
        if output:
            import json

            return json.loads(output)
    except (
        subprocess.SubprocessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
        Exception,
    ):
        pass
    return None


def _python_version(python_path):
    """Get the --version string of a python binary."""
    try:
        result = subprocess.run(
            [python_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception:
        return "unknown"


def _is_same_python(a, b):
    """Check if two python paths resolve to the same binary."""
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def run():
    """Main entry: find all Pythons, report which have torch."""
    binaries = _find_python_binaries()

    if not binaries:
        print("No Python installations found on this system.")
        return

    # Deduplicate by real path, prefer shorter (more descriptive) paths as representative
    seen_real = {}  # real_path -> index in unique
    unique = []
    for b in binaries:
        try:
            real = os.path.realpath(b)
        except OSError:
            real = b
        if real not in seen_real:
            seen_real[real] = len(unique)
            unique.append(b)
        else:
            # Prefer the shorter / more descriptive path
            existing = unique[seen_real[real]]
            # Prefer non-venv paths (they describe the actual install better)
            in_venv = "/.venv/" in b or "/venv/" in b
            existing_in_venv = "/.venv/" in existing or "/venv/" in existing
            if existing_in_venv and not in_venv:
                unique[seen_real[real]] = b
            elif len(b) < len(existing) and in_venv == existing_in_venv:
                unique[seen_real[real]] = b

    results = []
    for path in unique:
        info = _probe_torch(path)
        ver = _python_version(path)
        results.append((path, ver, info))

    # Separate torch vs non-torch
    with_torch = [(p, v, i) for p, v, i in results if i and "torch_version" in i]
    without_torch = [
        (p, v, i) for p, v, i in results if not i or "torch_version" not in i
    ]

    # Filter out errors (broken installs)
    broken = [
        (p, v, i)
        for p, v, i in results
        if i and "error" in i and i["error"] != "not installed"
    ]
    without_torch = [
        (p, v, i)
        for p, v, i in results
        if (i is None or (i.get("error") == "not installed"))
    ]

    # Print header
    print(f"Scanned {len(unique)} Python installation(s)")
    print(f"  {len(with_torch)} with PyTorch, {len(without_torch)} without")
    if broken:
        print(f"  {len(broken)} errored (skipped)")
    print()

    if with_torch:
        print("=== PyTorch Found ===")
        for path, ver, info in with_torch:
            print(f"\n  {path}")
            print(f"    Python:   {ver}")
            print(f"    PyTorch:  {info['torch_version']}")
            cuda = info.get("cuda_available", False)
            mps = info.get("mps_available", False)
            print(f"    CUDA:     {'yes' if cuda else 'no'}", end="")
            if cuda and info.get("cuda_version"):
                print(f" (CUDA {info['cuda_version']})", end="")
            print()
            if cuda and info.get("cudnn_version"):
                print(f"    cuDNN:    {info['cudnn_version']}")
            if cuda and info.get("device_count", 0) > 0:
                print(f"    GPUs:     {info['device_count']}")
                if info.get("gpu_name"):
                    print(f"    GPU 0:    {info['gpu_name']}")
            print(f"    MPS:      {'yes' if mps else 'no'}")
        print()

    if without_torch:
        print("=== No PyTorch ===")
        for path, ver, _info in without_torch:
            print(f"  {path:50s}  ({ver})")
        print()
