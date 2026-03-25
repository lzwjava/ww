# Design Spec: 2026-03-26-linux-script-migration.md

## Overview
Migrate Linux-specific utility and setup scripts from `blog-source/scripts/linux` into the `ww` toolkit. This migration centralizes personal infrastructure management, provides a cleaner CLI interface via `ww linux`, and makes environment-specific values configurable.

## Goals
- Decentralize logic from `blog-source` and centralize in `ww`.
- Provide a unified `ww linux` command group for system-level tasks.
- Replace hardcoded values with `.env` variables (e.g., `MAG_MAC_ADDRESS`).
- Clean up the source repository post-migration.

## Architecture
### 1. New Module Structure
- `ww/linux/`: Implementation logic for Linux-related scripts.
    - `gpu.py`: GPU and CUDA information.
    - `system.py`: Overview of OS and system specs.
    - `disk.py`: Disk usage reporting (including charts).
    - `battery.py`: Battery status (using `psutil` and `sysfs`).
    - `setup.py`: APT proxy and environment setup.
    - `net.py`: Network utilities like Wake-On-LAN.
    - `terminal.py`: Fullscreen terminal launcher.
    - `main.py`: Command dispatcher for the `linux` group.

### 2. Configuration (`.env`)
- `MAG_MAC_ADDRESS`: Target MAC address for Wake-On-LAN (`ww linux wol`).

### 3. Command Dispatch (`ww/main.py` and `ww/linux/main.py`)
Add a `linux` group with subcommands:
- `ww linux gpu`: Shows GPU and CUDA details.
- `ww linux system`: Comprehensive system overview.
- `ww linux disk`: Shows disk usage (and chart if interactive).
- `ww linux battery`: Shows battery level and charging status.
- `ww linux proxy-setup`: Interactively configures APT proxy.
- `ww linux wol`: Sends a WoL packet.
- `ww linux terminal`: Opens a fullscreen terminal.

## Implementation Plan
1.  **Preparation**: Add `MAG_MAC_ADDRESS` to `.env` (if not already present).
2.  **Porting**:
    - `blog-source/scripts/linux/get_gpu_info.py` -> `ww/linux/gpu.py`.
    - `blog-source/scripts/linux/get_system_info.py` -> `ww/linux/system.py`.
    - `blog-source/scripts/linux/df.py` -> `ww/linux/disk.py`.
    - `blog-source/scripts/linux/system_battery_status.py` -> `ww/linux/battery.py`.
    - `blog-source/scripts/linux/setup_apt_proxy.py` and `blog-source/scripts/linux/setup.py` -> `ww/linux/setup.py` (renamed functions).
    - `blog-source/scripts/linux/wakeonlan.py` -> `ww/linux/net.py` (renamed functions).
    - `blog-source/scripts/linux/random_terminal.py` -> `ww/linux/terminal.py` (renamed functions).
3.  **CLI Integration**: Register commands in `ww/main.py` and implement `ww/linux/main.py`.
4.  **Verification**: Test commands on a Linux environment (where possible).
5.  **Cleanup**: Delete `blog-source/scripts/linux/`.

## Success Criteria
- `ww linux gpu` correctly displays GPU information.
- `ww linux system` provides a full system overview.
- `ww linux wol` sends packets using the configured MAC address.
- All original files in `blog-source/scripts/linux/` are removed.
