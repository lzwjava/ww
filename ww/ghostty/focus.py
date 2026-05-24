"""Scale a Ghostty window to near-full-screen size by list index or title substring.

Uses CGSSetWindowTransform (SkyLight private API) to scale and reposition
the window to fill the screen. No focus stealing, no Accessibility needed.

The window content scales proportionally (text gets larger).
"""

import subprocess
import sys

SWIFT_CODE = r"""
import Cocoa
import CoreGraphics

typealias CGSConnection = Int32
typealias CGSWindow = UInt32

struct WinInfo {
    let id: Int
    let name: String
    let x: CGFloat
    let y: CGFloat
    let w: CGFloat
    let h: CGFloat
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
        let x = bounds?["X"] as? CGFloat ?? 0
        let y = bounds?["Y"] as? CGFloat ?? 0
        let w = bounds?["Width"] as? CGFloat ?? 0
        let h = bounds?["Height"] as? CGFloat ?? 0
        results.append(WinInfo(id: wid, name: name, x: x, y: y, w: w, h: h))
    }
    return results
}

func scaleWindowToScreen(_ win: WinInfo) -> Bool {
    guard let lib = dlopen("/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight", RTLD_NOW) else {
        return false
    }
    guard let connFn = dlsym(lib, "CGSMainConnectionID") else { return false }
    let conn: CGSConnection = unsafeBitCast(connFn, to: (@convention(c) () -> CGSConnection).self)()

    guard let setTransformFn = dlsym(lib, "CGSSetWindowTransform") else { return false }
    typealias SetTransformFunc = @convention(c) (CGSConnection, CGSWindow, CGAffineTransform) -> Int32
    let CGSSetWindowTransform = unsafeBitCast(setTransformFn, to: SetTransformFunc.self)

    guard let screen = NSScreen.screens.first else { return false }
    let screenW = screen.frame.width
    let screenH = screen.frame.height
    let menuBar: CGFloat = 25
    let padding: CGFloat = 4

    let targetW = screenW - padding * 2
    let targetH = screenH - menuBar - padding * 2
    let targetX = padding
    let targetY = menuBar + padding

    let scaleX = targetW / win.w
    let scaleY = targetH / win.h

    // CGSSetWindowTransform applies: new_point = transform * old_point
    // Scale the window, then translate so top-left maps to target position
    let tx = targetX - win.x * scaleX
    let ty = targetY - win.y * scaleY

    let transform = CGAffineTransform(a: scaleX, b: 0, c: 0, d: scaleY, tx: tx, ty: ty)
    let err = CGSSetWindowTransform(conn, CGSWindow(win.id), transform)
    return err == 0
}

func resetTransform(_ winID: Int) {
    guard let lib = dlopen("/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight", RTLD_NOW) else { return }
    guard let connFn = dlsym(lib, "CGSMainConnectionID") else { return }
    let conn: CGSConnection = unsafeBitCast(connFn, to: (@convention(c) () -> CGSConnection).self)()
    guard let setTransformFn = dlsym(lib, "CGSSetWindowTransform") else { return }
    typealias SetTransformFunc = @convention(c) (CGSConnection, CGSWindow, CGAffineTransform) -> Int32
    let CGSSetWindowTransform = unsafeBitCast(setTransformFn, to: SetTransformFunc.self)
    let _ = CGSSetWindowTransform(conn, CGSWindow(winID), .identity)
}

let target = "__TARGET__"
let windows = listGhosttyWindows()

if target.isEmpty {
    for (i, w) in windows.enumerated() {
        print("\(i + 1). [\(w.id)] \(w.name)")
    }
    exit(0)
}

// Handle "reset" subcommand
if target == "reset" {
    for w in windows {
        resetTransform(w.id)
    }
    print("Reset all Ghostty window transforms.")
    exit(0)
}

// Resolve target
var targetWin: WinInfo?
if let idx = Int(target), idx >= 1, idx <= windows.count {
    targetWin = windows[idx - 1]
} else {
    let query = target.lowercased()
    for win in windows {
        if win.name.lowercased().contains(query) {
            targetWin = win
            break
        }
    }
}

guard let tw = targetWin else {
    print("No Ghostty window matching '\(target)'")
    print("Available windows:")
    for (i, w) in windows.enumerated() {
        print("  \(i + 1). [\(w.id)] \(w.name)")
    }
    exit(1)
}

if scaleWindowToScreen(tw) {
    print("Scaled: [\(tw.id)] \(tw.name) to full screen")
} else {
    print("Error: Could not scale window")
    exit(1)
}
"""


def main():
    if len(sys.argv) < 2 or not sys.argv[1:]:
        from ww.ghostty.list_windows import main as list_main

        list_main()
        print("\nUsage: ww ghostty focus <index|title>")
        print("       ww ghostty focus reset    (reset all transforms)")
        return

    target = sys.argv[1]
    swift_code = SWIFT_CODE.replace("__TARGET__", target)
    result = subprocess.run(
        ["swift", "-e", swift_code],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
