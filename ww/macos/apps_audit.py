"""
Audit /Applications: list apps with size and last-modified timestamp,
classify into KEEP / CONSIDER / SAFE DELETE / HOLD via LLM.

Usage: ww macos apps [--no-llm] [--json] [--path DIR]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from ww.llm.openrouter_client import call_openrouter_api


AUDIT_PROMPT = """You are auditing macOS applications installed in /Applications to help the user reclaim disk space and remove dead apps.

For each app, you receive: name, size, and last-modified date (which correlates with last install/update).

Classification rules:
- KEEP = last touched in last 3 months, clearly active dev/production tool
- CONSIDER = duplicates of tools already present, or niche utility the user may have replaced
- SAFE DELETE = last touched 1+ year ago AND (redundant OR one-time-use OR irrelevant to AI engineering)
- HOLD = large app where you need user input on whether the use case still exists

Output format — use EXACTLY this layout with aligned columns. Use ─ for separator lines.
Group KEEP items by category (Core work, Comms, AI/Dev, System, Proxy) on a single line each.
For CONSIDER show "Replaces" column. For SAFE DELETE show "Why remove". For HOLD show "Question".

  {{category}} — {{subtitle}} (save ~{{size}})

  App                           Last Touch   Size      Why remove
  ─────────────────────────────────────────────────────────────────
  iTerm.app                     2023-01      72MB      Replaced by Ghostty
  ...

  Potential savings: ~{{total}}

Be concise. No preamble. No markdown fences. Plain text only.

App data:
---
{app_data}
---"""


def _format_size(size_kb):
    if size_kb >= 1024 * 1024:
        return f"{size_kb / (1024 * 1024):.1f}GB"
    if size_kb >= 1024:
        return f"{size_kb / 1024:.0f}MB"
    if size_kb > 0:
        return f"{size_kb}KB"
    return "--"


def _format_size_short(size_kb):
    """Compact size for table cells."""
    if size_kb >= 1024 * 1024:
        return f"{size_kb / (1024 * 1024):.1f}GB"
    if size_kb >= 1024:
        return f"{size_kb / 1024:.0f}MB"
    return "--"


def _month_str(date_str):
    """Convert 2025-03-12 to 2025-03."""
    if not date_str:
        return "--"
    return date_str[:7]


def collect_apps(app_dir):
    """Collect app bundles with size and last-modified timestamp."""
    app_path = Path(app_dir)
    if not app_path.exists():
        print(f"Error: {app_dir} does not exist.")
        sys.exit(1)

    apps = []
    app_bundles = sorted(app_path.glob("*.app"))
    total = len(app_bundles)

    if total == 0:
        print(f"No .app bundles found in {app_dir}")
        return apps

    for i, bundle in enumerate(app_bundles, 1):
        name = bundle.stem
        if i % 10 == 0 or i == total:
            print(f"  {i}/{total}", end="\r", flush=True)

        try:
            result = subprocess.run(
                ["du", "-sk", str(bundle)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            size_kb = int(result.stdout.split()[0]) if result.returncode == 0 else 0
        except (subprocess.TimeoutExpired, ValueError, IndexError):
            size_kb = 0

        try:
            result = subprocess.run(
                ["stat", "-f", "%Sm", "-t", "%Y-%m-%d", str(bundle)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            modified_str = result.stdout.strip() if result.returncode == 0 else ""
        except subprocess.TimeoutExpired:
            modified_str = ""

        modified_date = None
        if modified_str:
            try:
                modified_date = datetime.strptime(modified_str, "%Y-%m-%d")
            except ValueError:
                pass

        age_days = None
        if modified_date:
            age_days = (datetime.now() - modified_date).days

        apps.append(
            {
                "name": name,
                "size_kb": size_kb,
                "size_human": _format_size(size_kb),
                "modified": modified_str,
                "age_days": age_days,
            }
        )

    print(" " * 50, end="\r")
    return apps


def _classify_by_age(app):
    age = app.get("age_days")
    if age is None:
        return "UNKNOWN"
    if age <= 90:
        return "KEEP"
    if age <= 365:
        return "CONSIDER"
    return "SAFE DELETE"


def _group_apps(apps):
    groups = {"KEEP": [], "CONSIDER": [], "SAFE DELETE": [], "UNKNOWN": []}
    for app in apps:
        groups[_classify_by_age(app)].append(app)
    for bucket in groups.values():
        bucket.sort(key=lambda a: a["size_kb"], reverse=True)
    return groups


def _trunc(s, width):
    """Truncate string to width, adding .. if needed."""
    if len(s) <= width:
        return s
    return s[: width - 2] + ".."


def print_report(apps):
    """Print the full audit report with aligned tables."""
    groups = _group_apps(apps)
    total_size = sum(a["size_kb"] for a in apps)
    safe_size = sum(a["size_kb"] for a in groups["SAFE DELETE"])
    consider_size = sum(a["size_kb"] for a in groups["CONSIDER"])

    n = len(apps)
    print()
    print(f"  {n} apps, {_format_size(total_size)} total. Organized by what to do:")

    # SAFE DELETE
    bucket = groups["SAFE DELETE"]
    if bucket:
        save_str = _format_size(safe_size + consider_size)
        print()
        print(f"  SAFE DELETE — clearly unused/stale (save ~{save_str})")
        print()
        print(f"  {'App':<30} {'Last Touch':<12} {'Size':>8}  {'Why remove'}")
        print(f"  {'─' * 30} {'─' * 12} {'─' * 8}  {'─' * 20}")
        for app in bucket:
            name = _trunc(app["name"] + ".app", 30)
            print(
                f"  {name:<30} {_month_str(app['modified']):<12} "
                f"{_format_size_short(app['size_kb']):>8}  "
                f">{365}d stale"
            )

    # CONSIDER
    bucket = groups["CONSIDER"]
    if bucket:
        print()
        print("  CONSIDER DELETING — 3mo-1yr stale, review case by case")
        print()
        print(f"  {'App':<30} {'Last Touch':<12} {'Size':>8}  {'Age'}")
        print(f"  {'─' * 30} {'─' * 12} {'─' * 8}  {'─' * 8}")
        for app in bucket:
            name = _trunc(app["name"] + ".app", 30)
            age = app["age_days"]
            age_str = f"{age // 30}mo" if age else "--"
            print(
                f"  {name:<30} {_month_str(app['modified']):<12} "
                f"{_format_size_short(app['size_kb']):>8}  {age_str}"
            )

    # KEEP
    bucket = groups["KEEP"]
    if bucket:
        keep_size = sum(a["size_kb"] for a in bucket)
        print()
        print(
            f"  KEEP — active use, touched in last 3 months ({_format_size(keep_size)})"
        )
        print()
        for app in bucket:
            name = app["name"]
            size = _format_size_short(app["size_kb"])
            print(f"    {name:<28} {size:>8}")

    # UNKNOWN
    bucket = groups["UNKNOWN"]
    if bucket:
        print()
        print("  UNKNOWN — no date available")
        print()
        for app in bucket:
            name = app["name"]
            size = _format_size_short(app["size_kb"])
            print(f"    {name:<28} {size:>8}")

    # Summary
    n_safe = len(groups["SAFE DELETE"])
    n_cons = len(groups["CONSIDER"])
    n_keep = len(groups["KEEP"])
    print()
    print(
        f"  Potential savings if you delete safe + consider: ~{_format_size(safe_size + consider_size)}"
    )
    print(f"  Summary: {n_keep} keep | {n_cons} consider | {n_safe} safe delete")
    print()


def llm_audit(apps):
    """Send app data to LLM for smart classification."""
    lines = []
    for app in sorted(apps, key=lambda a: a["size_kb"], reverse=True):
        age = f"{app['age_days']}d" if app["age_days"] is not None else "unknown"
        lines.append(
            f"{app['name']} | {app['size_human']} | {app['modified']} | age={age}"
        )
    app_data = "\n".join(lines)

    prompt = AUDIT_PROMPT.format(app_data=app_data)
    result = call_openrouter_api(prompt)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Audit macOS applications: size, age, and cleanup recommendations"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM analysis, show raw data with age-based classification",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    parser.add_argument(
        "--path",
        default="/Applications",
        help="Path to scan (default: /Applications)",
    )
    args = parser.parse_args(sys.argv[1:])

    apps = collect_apps(args.path)
    if not apps:
        return

    if args.json_output:
        print(json.dumps(apps, indent=2))
        return

    if args.no_llm:
        print_report(apps)
        return

    print(f"  Analyzing {len(apps)} apps with LLM...\n")
    result = llm_audit(apps)

    if not result:
        print("Error: LLM call failed. Use --no-llm for raw data.")
        sys.exit(1)

    print(result)
