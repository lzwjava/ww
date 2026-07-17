#!/usr/bin/env python3
"""RunPod CLI wrapper — manage pods via runpodctl.

Subcommands:
  start <gpu> [pod_name]   Create and start a pod with the given GPU type
  stop <pod_id>             Stop a running pod
  list                      List all pods
  ssh <pod_id>              SSH into a pod
  delete <pod_id>           Delete a pod
  gpus                      List available GPU types
  send <file>               Send a file (generates one-time receive code)
  receive <code>            Receive a file via one-time code
  user                      Show account info
  billing                   Show billing history
  raw <args...>             Pass raw arguments directly to runpodctl

GPU type shortcuts (mapped to runpodctl --gpu-id values):
  rtx4000ada  → NVIDIA RTX 4000 Ada (24GB)
  rtx4090     → NVIDIA RTX 4070 Ti 48GB (RTX 4090 24GB)
  a100        → NVIDIA A100 80GB
  h100        → NVIDIA H100 80GB
  h200        → NVIDIA H200 140GB
  l40s        → NVIDIA L40S 48GB
  mi300x      → AMD MI300X 192GB (if available)
"""

import shutil
import subprocess
import sys

GPU_ALIASES = {
    "rtx4000ada": "NVIDIA-RTX-4000-Ada",
    "rtx4070ti": "NVIDIA-RTX-4070-Ti-48GB",
    "rtx4090": "NVIDIA-RTX-4090",
    "a100": "NVIDIA-A100-80GB",
    "a100-80gb": "NVIDIA-A100-80GB",
    "h100": "NVIDIA-H100-80GB",
    "h100-80gb": "NVIDIA-H100-80GB",
    "h200": "NVIDIA-H200-140GB",
    "l40s": "NVIDIA-L40S",
    "mi300x": "AMD-MI300X-192GB",
}

DEFAULT_IMAGE = "runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04"


def _check_runpodctl():
    if not shutil.which("runpodctl"):
        print("Error: runpodctl not found. Install it first:")
        print("  wget -qO- cli.runpod.net | sudo bash")
        print("  # or")
        print("  brew install runpod/runpodctl/runpodctl")
        sys.exit(1)


def _run(args, check=True):
    """Run runpodctl with given args, streaming output."""
    _check_runpodctl()
    cmd = ["runpodctl"] + args
    try:
        result = subprocess.run(cmd, check=check)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


def cmd_start():
    """Create and start a pod: ww runpod start <gpu> [pod_name] [--image IMG]"""
    args = sys.argv[1:]  # remaining args after "start"
    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww runpod start <gpu> [pod_name] [--image IMAGE]")
        print("")
        print("GPU types:")
        for alias, gpu_id in sorted(GPU_ALIASES.items()):
            print(f"  {alias:16s}  {gpu_id}")
        print("")
        print("Options:")
        print("  --image IMAGE   Container image (default: pytorch 2.8.0 + CUDA 12.8)")
        print("")
        print("Examples:")
        print("  ww runpod start rtx4000ada")
        print("  ww runpod start h200 my-training-pod")
        print("  ww runpod start a100 --image runpod/pytorch:2.4.0-py3.11-cuda12.4")
        return

    gpu_input = args[0]
    gpu_id = GPU_ALIASES.get(gpu_input.lower(), gpu_input)

    pod_name = None
    image = DEFAULT_IMAGE
    i = 1
    while i < len(args):
        if args[i] == "--image" and i + 1 < len(args):
            image = args[i + 1]
            i += 2
        elif not args[i].startswith("-"):
            pod_name = args[i]
            i += 1
        else:
            i += 1

    runpod_args = [
        "pod",
        "create",
        "--gpu-id",
        gpu_id,
        "--image",
        image,
    ]
    if pod_name:
        runpod_args += ["--name", pod_name]

    print(
        f"Creating pod: GPU={gpu_id}, image={image}"
        + (f", name={pod_name}" if pod_name else "")
    )
    _run(runpod_args)


def cmd_stop():
    """Stop a running pod: ww runpod stop <pod_id>"""
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww runpod stop <pod_id>")
        return
    _run(["pod", "stop", args[0]])


def cmd_list():
    """List all pods: ww runpod list"""
    _run(["pod", "list"])


def cmd_ssh():
    """SSH into a pod: ww runpod ssh <pod_id>"""
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww runpod ssh <pod_id>")
        return
    # runpodctl has no direct ssh subcommand; use pod get to find IP+port, then ssh
    # But runpodctl older versions have: runpodctl ssh <pod_id>
    # Try the direct approach first
    _run(["ssh", args[0]])


def cmd_delete():
    """Delete a pod: ww runpod delete <pod_id>"""
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww runpod delete <pod_id>")
        return
    _run(["pod", "delete", args[0]])


def cmd_gpus():
    """List available GPU types: ww runpod gpus"""
    _run(["gpu", "list"])


def cmd_send():
    """Send a file: ww runpod send <file>"""
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww runpod send <file>")
        return
    _run(["send", args[0]])


def cmd_receive():
    """Receive a file: ww runpod receive <code>"""
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww runpod receive <code>")
        print("  code format: NNNN-word-word-word")
        return
    _run(["receive", args[0]])


def cmd_user():
    """Show account info: ww runpod user"""
    _run(["user"])


def cmd_billing():
    """Show billing history: ww runpod billing"""
    _run(["billing"])


def cmd_raw():
    """Pass raw args to runpodctl: ww runpod raw <args...>"""
    args = sys.argv[1:]
    if not args:
        print("Usage: ww runpod raw <runpodctl args...>")
        print("Example: ww runpod raw pod get abc123")
        return
    _run(args)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage: ww runpod <command> [options]")
        print("")
        print("Commands:")
        print("  start <gpu> [name]   Create and start a pod with a GPU type")
        print("  stop <pod_id>         Stop a running pod")
        print("  list                  List all pods")
        print("  ssh <pod_id>          SSH into a pod")
        print("  delete <pod_id>       Delete a pod")
        print("  gpus                  List available GPU types")
        print("  send <file>           Send a file (generates receive code)")
        print("  receive <code>        Receive a file via code")
        print("  user                  Show account info")
        print("  billing               Show billing history")
        print("  raw <args...>         Pass raw args to runpodctl")
        print("")
        print("GPU shortcuts:")
        for alias, gpu_id in sorted(GPU_ALIASES.items()):
            print(f"  {alias:16s}  {gpu_id}")
        print("")
        print("Examples:")
        print("  ww runpod start rtx4000ada")
        print("  ww runpod start h200 my-training --image runpod/pytorch:2.4.0")
        print("  ww runpod list")
        print("  ww runpod ssh abc123")
        print("  ww runpod stop abc123")
        return

    subcmd = sys.argv.pop(1)
    if subcmd == "start":
        cmd_start()
    elif subcmd == "stop":
        cmd_stop()
    elif subcmd == "list":
        cmd_list()
    elif subcmd == "ssh":
        cmd_ssh()
    elif subcmd == "delete":
        cmd_delete()
    elif subcmd == "gpus":
        cmd_gpus()
    elif subcmd == "send":
        cmd_send()
    elif subcmd == "receive":
        cmd_receive()
    elif subcmd == "user":
        cmd_user()
    elif subcmd == "billing":
        cmd_billing()
    elif subcmd == "raw":
        cmd_raw()
    else:
        print(f"Unknown runpod command: {subcmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
