"""List all open Ghostty windows with ID, title, position, and size.

For windows titled "hermes", also queries running hermes processes
to show which project directory each instance is working in.
"""

import subprocess
import sys

SWIFT_CODE = r"""
import Cocoa
import CoreGraphics

struct WinInfo {
    let id: Int
    let name: String
    let x: Int
    let y: Int
    let w: Int
    let h: Int
}

func listGhosttyWindows() -> [WinInfo] {
    let options = CGWindowListOption(arrayLiteral: .optionOnScreenOnly, .excludeDesktopElements)
    guard let windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else {
        return []
    }
    var results: [WinInfo] = []
    for win in windowList {
        guard let owner = win["kCGWindowOwnerName"] as? String else { continue }
        guard owner.lowercased().contains("ghostty") else { continue }
        let name = win["kCGWindowName"] as? String ?? "(no title)"
        let wid = win["kCGWindowNumber"] as? Int ?? 0
        let bounds = win["kCGWindowBounds"] as? [String: Any]
        let x = bounds?["X"] as? Int ?? 0
        let y = bounds?["Y"] as? Int ?? 0
        let w = bounds?["Width"] as? Int ?? 0
        let h = bounds?["Height"] as? Int ?? 0
        results.append(WinInfo(id: wid, name: name, x: x, y: y, w: w, h: h))
    }
    return results
}

let windows = listGhosttyWindows()
for (i, win) in windows.enumerated() {
    print("\(i + 1)\t\(win.id)\t\(win.name)\t\(win.x),\(win.y)\t\(win.w)x\(win.h)")
}
"""


def get_ghostty_windows():
    """Return list of dicts: [{index, id, title, x, y, w, h}, ...]"""
    result = subprocess.run(
        ["swift", "-e", SWIFT_CODE],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        err = result.stderr.strip()
        if "not allowed assistive access" in err:
            print(
                "Error: Accessibility permissions required. Grant in System Settings > Privacy & Security > Accessibility."
            )
        else:
            print(f"Error: {err or 'Swift script failed'}")
        sys.exit(1)

    windows = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        idx_str, wid_str, title, pos, size = parts
        x_str, y_str = pos.split(",")
        w_str, h_str = size.split("x")
        windows.append(
            {
                "index": int(idx_str),
                "id": int(wid_str),
                "title": title,
                "x": int(x_str),
                "y": int(y_str),
                "w": int(w_str),
                "h": int(h_str),
            }
        )
    return windows


def get_hermes_cwds():
    """Get CWDs of all running hermes processes.

    Returns list of dicts: [{pid, cwd}, ...]
    """
    try:
        result = subprocess.run(
            ["pgrep", "-f", "Python.*hermes"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []

        pids = [p.strip() for p in result.stdout.strip().splitlines() if p.strip()]
        cwds = []
        for pid in pids:
            proc = subprocess.run(
                ["lsof", "-p", pid, "-a", "-d", "cwd"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in proc.stdout.splitlines():
                if "cwd" in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        cwds.append({"pid": pid, "cwd": parts[8]})
                        break
        return cwds
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def main():
    windows = get_ghostty_windows()

    if not windows:
        print("No Ghostty windows found.")
        return

    # Column widths
    idx_w = max(len(str(len(windows))), 5)
    id_w = max(len(str(max(w["id"] for w in windows))), 2) + 2  # brackets
    title_w = max(len(w["title"]) for w in windows)
    title_w = max(title_w, 5)
    pos_w = 15  # (x, y)

    print(
        f" {'#':<{idx_w}}  {'Window ID':<{id_w}}  {'Title':<{title_w}}  {'Position':<{pos_w}}  {'Size'}"
    )
    for w in windows:
        wid_str = f"[{w['id']}]"
        pos_str = f"({w['x']},{w['y']})"
        size_str = f"{w['w']}x{w['h']}"
        print(
            f"{w['index']:>{idx_w}}. {wid_str:<{id_w}}  {w['title']:<{title_w}}  {pos_str:<{pos_w}}  {size_str}"
        )

    # Show hermes CWD info for windows titled "hermes"
    hermes_wins = [w for w in windows if w["title"].strip() == "hermes"]
    if hermes_wins:
        hermes_cwds = get_hermes_cwds()
        if hermes_cwds:
            # Extract unique project names
            seen = set()
            unique_projects = []
            for h in hermes_cwds:
                cwd = h["cwd"]
                proj = cwd.split("/projects/")[-1] if "/projects/" in cwd else cwd
                if proj not in seen:
                    seen.add(proj)
                    unique_projects.append(proj)

            if unique_projects:
                print(f"\nHermes instances: {', '.join(unique_projects)}")
