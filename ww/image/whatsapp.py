#!/usr/bin/env python3
"""Download images from WhatsApp Web messages via Safari's JavaScript context.

Uses Canvas.toDataURL to extract both data: URIs and blob: URLs
from the last message container in WhatsApp Web — works synchronously
with Safari's do JavaScript AppleScript bridge.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time


def run_applescript(script):
    """Run an AppleScript snippet and return stdout."""
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        print(f"AppleScript error: {proc.stderr.strip()}", file=sys.stderr)
        return None
    return proc.stdout.strip()


def safari_execute_js(js_code):
    """Execute JavaScript in Safari's front document, return the result."""
    escaped = js_code.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    script = f'''
    tell application "Safari"
        if not (exists front document) then
            return "ERROR: No Safari document open"
        end if
        tell front document
            do JavaScript "{escaped}"
        end tell
    end tell
    '''
    return run_applescript(script)


def safari_get_url():
    """Return the URL of Safari's front document."""
    script = """
    tell application "Safari"
        if not (exists front document) then
            return ""
        end if
        return URL of front document
    end tell
    """
    return run_applescript(script)


def safari_navigate(url):
    """Open or navigate Safari to a URL."""
    escaped_url = url.replace('"', '\\"')
    script = f'''
    tell application "Safari"
        activate
        if not (exists front document) then
            make new document with properties {{URL:"{escaped_url}"}}
        else
            set URL of front document to "{escaped_url}"
        end if
    end tell
    '''
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        print(f"Failed to navigate Safari: {proc.stderr.strip()}", file=sys.stderr)
        return False
    return True


def diagnose_page():
    """Run diagnostic JS to understand what page Safari is showing."""
    diag_js = """
    (function() {
        var info = {
            url: window.location.href,
            title: document.title,
            readyState: document.readyState,
        };

        /* WhatsApp-specific selectors */
        info.msgContainers = document.querySelectorAll("[data-testid='msg-container']").length;
        info.chatList = document.querySelector("[data-testid='chat-list']") ? 'present' : 'absent';
        info.conversationPanel = document.querySelector("[data-testid='conversation-panel-wrapper']") ? 'present' : 'absent';
        info.qrCode = document.querySelector("[data-testid='qrcode']") ? 'present' : 'absent';
        info.introPanel = document.querySelector("[data-testid='intro-panel']") ? 'present' : 'absent';
        info.allImages = document.querySelectorAll('img').length;
        info.allDivs = document.querySelectorAll('div').length;

        /* Alternative selectors */
        info.msgIn = document.querySelectorAll("[data-testid='msg-in']").length;
        info.msgOut = document.querySelectorAll("[data-testid='msg-out']").length;
        info.selectableText = document.querySelectorAll("[data-testid='selectable-text']").length;

        /* Check if we are on whatsapp */
        info.whatsapp = window.location.hostname.includes('whatsapp');

        return JSON.stringify(info);
    })();
    """
    raw = safari_execute_js(diag_js)
    if not raw or raw.startswith("ERROR:"):
        print(f"  Diagnostic JS failed: {raw}", file=sys.stderr)
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"  Could not parse diagnostic output: {raw[:200]}")
        return None


def extract_images_from_last_message(output_dir, verbose=False):
    """Extract images from the last message container on WhatsApp Web."""
    os.makedirs(output_dir, exist_ok=True)

    # STEP 1: diagnostic
    print("─" * 50)
    print("Step 1: Checking Safari page state...")
    url = safari_get_url()
    print(f"  Safari front tab URL: {url or '(none)'}")

    diag = diagnose_page()
    if diag:
        print(f"  Page title:        {diag.get('title', '?')}")
        print(f"  URL host:          {diag.get('url', '?')[:80]}")
        print(f"  Ready state:       {diag.get('readyState', '?')}")
        print(f"  Is WhatsApp:       {diag.get('whatsapp', False)}")
        print(f"  Message containers:{diag.get('msgContainers', 0)}")
        print(f"  Chat list:         {diag.get('chatList', '?')}")
        print(f"  Conversation panel:{diag.get('conversationPanel', '?')}")
        print(f"  QR code:           {diag.get('qrCode', '?')}")
        print(f"  Intro panel:       {diag.get('introPanel', '?')}")
        print(f"  msg-in / msg-out:  {diag.get('msgIn', 0)} / {diag.get('msgOut', 0)}")
        print(f"  Total <img> tags:  {diag.get('allImages', 0)}")
        if verbose:
            print(f"  Total <div> tags:  {diag.get('allDivs', 0)}")

        # Diagnose common issues
        issues = []
        if not diag.get("whatsapp"):
            issues.append("NOT on WhatsApp Web — open web.whatsapp.com in Safari")
        elif diag.get("qrCode") == "present":
            issues.append("WhatsApp is showing QR code — scan it to log in first")
        elif diag.get("introPanel") == "present":
            issues.append("WhatsApp intro panel showing — click a chat to open it")
        elif (
            diag.get("conversationPanel") == "absent"
            and diag.get("chatList") == "absent"
        ):
            issues.append(
                "WhatsApp not fully loaded — wait for the page to finish loading"
            )
        elif (
            diag.get("msgContainers") == 0
            and diag.get("conversationPanel") == "present"
        ):
            issues.append("Chat is open but no messages loaded yet — scroll up or wait")
        elif diag.get("msgContainers") == 0:
            issues.append("No messages visible — try opening a specific chat")

        if issues:
            print("\n  ⚠️  Issues detected:")
            for issue in issues:
                print(f"    → {issue}")
            if not diag.get("whatsapp"):
                return []

    # STEP 2: extract
    print("\nStep 2: Extracting images from last message...")

    js_code = """
    (function() {
        var containers = document.querySelectorAll("[data-testid='msg-container']");
        if (containers.length === 0) {
            return JSON.stringify({error: 'No message containers found'});
        }

        var lastContainer = containers[containers.length - 1];
        var imgs = lastContainer.querySelectorAll('img');
        if (imgs.length === 0) {
            return JSON.stringify({images: [], total: 0, note: 'Last message has no images'});
        }

        var results = [];
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');

        imgs.forEach(function(img, idx) {
            var w = img.naturalWidth || img.width || 300;
            var h = img.naturalHeight || img.height || 300;

            if (w === 0 || h === 0) {
                results.push({index: idx, error: 'zero-size image', skip: true});
                return;
            }

            canvas.width = w;
            canvas.height = h;

            try {
                ctx.clearRect(0, 0, w, h);
                ctx.drawImage(img, 0, 0, w, h);
            } catch (e) {
                results.push({index: idx, error: 'drawImage failed: ' + e.message, skip: true});
                return;
            }

            try {
                var dataUrl = canvas.toDataURL('image/jpeg', 0.92);
                var b64 = dataUrl.split(',')[1];
                results.push({index: idx, data: b64, width: w, height: h});
            } catch (e) {
                results.push({index: idx, error: 'toDataURL failed (tainted canvas?)', skip: true});
            }
        });

        return JSON.stringify({images: results, total: imgs.length});
    })();
    """

    raw = safari_execute_js(js_code)

    if raw is None:
        print("  JS execution returned nothing (AppleScript error?)")
        return []
    if raw.startswith("ERROR:"):
        print(f"  {raw}", file=sys.stderr)
        return []

    if verbose:
        print(f"  Raw response (first 200 chars): {raw[:200]}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  JSON parse failed. Raw (first 300 chars): {raw[:300]}")
        return []

    if "error" in data:
        print(f"  Error: {data['error']}")
        if "note" in data:
            print(f"  Note: {data['note']}")
        return []

    images = data.get("images", [])
    total = data.get("total", 0)
    valid = [img for img in images if not img.get("skip")]
    skipped = [img for img in images if img.get("skip")]

    print(f"  Found {total} image(s), {len(valid)} extractable, {len(skipped)} skipped")
    for s in skipped:
        print(f"    Skipped image {s['index']}: {s.get('error', 'unknown')}")

    if not valid:
        if total > 0:
            print(
                "  All images were skipped (possibly tainted canvas from cross-origin)"
            )
        else:
            print("  No images in the last message. Make sure the message has images.")
        return []

    # STEP 3: save
    print(f"\nStep 3: Saving to {output_dir}/")
    saved_paths = []
    for img in valid:
        idx = img["index"]
        filename = f"whatsapp-{idx + 1}.jpg"
        path = os.path.join(output_dir, filename)

        img_bytes = base64.b64decode(img["data"])
        with open(path, "wb") as f:
            f.write(img_bytes)

        size_kb = len(img_bytes) / 1024
        w, h = img.get("width", "?"), img.get("height", "?")
        print(f"    {filename}  {w}x{h}  {size_kb:.1f} KB")
        saved_paths.append(path)

    print(f"\n  ✓ Saved {len(saved_paths)} image(s) to {output_dir}/")
    print("─" * 50)
    return saved_paths


def main():
    parser = argparse.ArgumentParser(
        description="Download images from the latest WhatsApp Web message via Safari",
        usage="%(prog)s [--dir DIR] [--open] [--verbose]",
    )
    parser.add_argument(
        "--dir",
        default="assets/images/cooking",
        help="Output directory (default: assets/images/cooking)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Navigate Safari to web.whatsapp.com first",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show extra debug output",
    )
    args = parser.parse_args(sys.argv[1:])

    if args.open:
        print("Navigating Safari to web.whatsapp.com...")
        if not safari_navigate("https://web.whatsapp.com/"):
            sys.exit(1)
        print("Waiting for WhatsApp Web to load...")
        time.sleep(8)
        url = safari_get_url()
        if not url or "whatsapp.com" not in url:
            print(f"Warning: Safari is at '{url}', not WhatsApp Web.", file=sys.stderr)

    extract_images_from_last_message(args.dir, verbose=args.verbose)


if __name__ == "__main__":
    main()
