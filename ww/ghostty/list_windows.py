"""List all open Ghostty windows with ID, title, position, size, and hermes project info.

Uses CGWindowList for window enumeration and AXUIElement for hermes project
directory matching (via AXDocument attribute).
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

// Get AXDocument for each hermes window (working directory)
func getHermesDocs() -> [String: String] {
    // posKey -> project name
    var result: [String: String] = [:]
    // Find the main Ghostty process (the one with the most windows)
    let ghosttyApps = NSWorkspace.shared.runningApplications.filter {
        $0.localizedName?.lowercased().contains("ghostty") == true
    }
    var bestApp: NSRunningApplication?
    var bestCount = 0
    for app in ghosttyApps {
        let el = AXUIElementCreateApplication(app.processIdentifier)
        var ref: CFTypeRef?
        AXUIElementCopyAttributeValue(el, kAXWindowsAttribute as CFString, &ref)
        let count = (ref as? [AXUIElement])?.count ?? 0
        if count > bestCount {
            bestCount = count
            bestApp = app
        }
    }
    guard let ghostty = bestApp else { return result }

    let appEl = AXUIElementCreateApplication(ghostty.processIdentifier)
    var winsRef: CFTypeRef?
    AXUIElementCopyAttributeValue(appEl, kAXWindowsAttribute as CFString, &winsRef)
    guard let windows = winsRef as? [AXUIElement] else { return result }

    for win in windows {
        var titleRef: CFTypeRef?
        AXUIElementCopyAttributeValue(win, kAXTitleAttribute as CFString, &titleRef)
        let title = (titleRef as? String ?? "").trimmingCharacters(in: .whitespaces)
        guard title == "hermes" else { continue }

        var docRef: CFTypeRef?
        AXUIElementCopyAttributeValue(win, kAXDocumentAttribute as CFString, &docRef)
        if let doc = docRef as? String {
            let path = doc.replacingOccurrences(of: "file://", with: "")
            let proj = path.split(separator: "/").last.map { String($0) } ?? path
            // Use position as key
            var posRef: CFTypeRef?
            AXUIElementCopyAttributeValue(win, kAXPositionAttribute as CFString, &posRef)
            var pos = CGPoint.zero
            if let pv = posRef { AXValueGetValue(pv as! AXValue, .cgPoint, &pos) }
            let key = "\(Int(pos.x)),\(Int(pos.y))"
            result[key] = proj
        }
    }
    return result
}

let windows = listGhosttyWindows()
let hermesDocs = getHermesDocs()

for (i, win) in windows.enumerated() {
    var extra = ""
    if win.name == "hermes" || win.name == "hermes " {
        let key = "\(win.x),\(win.y)"
        if let proj = hermesDocs[key] {
            extra = proj
        }
    }
    print("\(i + 1)\t\(win.id)\t\(win.name)\t\(win.x),\(win.y)\t\(win.w)x\(win.h)\t\(extra)")
}
"""


def get_ghostty_windows():
    """Return list of dicts: [{index, id, title, x, y, w, h, project}, ...]"""
    result = subprocess.run(
        ["swift", "-e", SWIFT_CODE],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        err = result.stderr.strip()
        print(f"Error: {err or 'Swift script failed'}")
        sys.exit(1)

    windows = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        idx_str, wid_str, title, pos, size, project = (
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            parts[4],
            parts[5].strip(),
        )
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
                "project": project,
            }
        )
    return windows


def main():
    windows = get_ghostty_windows()

    if not windows:
        print("No Ghostty windows found.")
        return

    # Column widths
    idx_w = max(len(str(len(windows))), 5)
    id_w = max(len(str(max(w["id"] for w in windows))), 2) + 2
    title_w = max(len(w["title"]) for w in windows)
    title_w = max(title_w, 5)
    pos_w = 15

    print(
        f" {'#':<{idx_w}}  {'Window ID':<{id_w}}  {'Title':<{title_w}}  {'Position':<{pos_w}}  {'Size'}"
    )
    for w in windows:
        wid_str = f"[{w['id']}]"
        pos_str = f"({w['x']},{w['y']})"
        size_str = f"{w['w']}x{w['h']}"
        title = w["title"]
        if w["project"]:
            title = f"{title} [{w['project']}]"
        print(
            f"{w['index']:>{idx_w}}. {wid_str:<{id_w}}  {title:<{title_w}}  {pos_str:<{pos_w}}  {size_str}"
        )
