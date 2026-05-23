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
- CONSIDER = duplicates of tools already present, or niche utility the user may have replaced (e.g. multiple browsers, FTP clients, etc.)
- SAFE DELETE = last touched 1+ year ago AND (redundant with another app OR one-time-use tool OR clearly irrelevant to the user's work as an AI engineer)
- HOLD = large app where you need user input on whether the use case still exists

Output format (be concise, no preamble):

SUMMARY
  Total: N apps, X GB
  KEEP: N | CONSIDER: N | SAFE DELETE: N | HOLD: N

KEEP
  AppName — Size — reason

CONSIDER
  AppName — Size — reason

SAFE DELETE
  AppName — Size — reason

HOLD
  AppName — Size — question for user

App data:
---
{app_data}
---"""


def _format_size(size_kb):
    if size_kb >= 1024 * 1024:
        return f"{size_kb / (1024 * 1024):.1f} GB"
    if size_kb >= 1024:
        return f"{size_kb / 1024:.0f} MB"
    return f"{size_kb} KB"


def _parse_du_size(raw):
    """Parse 'du -sh' output like '4.7G' or '123M' into KB."""
    raw = raw.strip()
    if not raw:
        return 0
    unit = raw[-1].upper()
    try:
        value = float(raw[:-1])
    except ValueError:
        return 0
    if unit == "G":
        return int(value * 1024 * 1024)
    if unit == "M":
        return int(value * 1024)
    if unit == "K":
        return int(value)
    return int(value)


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

    print(f"Scanning {total} apps in {app_dir}...")

    for i, bundle in enumerate(app_bundles, 1):
        name = bundle.stem
        if i % 10 == 0 or i == total:
            print(f"   {i}/{total}", end="\r", flush=True)

        # Size
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

        # Last modified (macOS stat format)
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

        # Parse date
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

    # Clear progress line
    print(" " * 50, end="\r")
    return apps


def _classify_by_age(app):
    """Simple age-based pre-classification (no LLM)."""
    age = app.get("age_days")
    if age is None:
        return "UNKNOWN"
    if age <= 90:
        return "KEEP"
    if age <= 365:
        return "CONSIDER"
    return "SAFE DELETE"


def print_table(apps, show_class=False):
    """Print apps as a formatted table."""
    # Sort by size descending
    apps = sorted(apps, key=lambda a: a["size_kb"], reverse=True)

    total_size = sum(a["size_kb"] for a in apps)
    print(f"\n  {len(apps)} apps, {_format_size(total_size)} total\n")

    if show_class:
        header = f"  {'App':<40} {'Size':>10} {'Modified':>12} {'Age':>8}  {'Class'}"
    else:
        header = f"  {'App':<40} {'Size':>10} {'Modified':>12} {'Age':>8}"
    print(header)
    print("  " + "-" * len(header.strip()))

    for app in apps:
        age_str = f"{app['age_days']}d" if app["age_days"] is not None else "?"
        if app["age_days"] is not None and app["age_days"] > 365:
            age_str = f"{app['age_days'] // 365}y"
        line = (
            f"  {app['name']:<40} {app['size_human']:>10} "
            f"{app['modified']:>12} {age_str:>8}"
        )
        if show_class:
            cls = _classify_by_age(app)
            line += f"  {cls}"
        print(line)

    print()


def print_classified(apps):
    """Print apps grouped by age-based classification."""
    groups = {"KEEP": [], "CONSIDER": [], "SAFE DELETE": [], "UNKNOWN": []}
    for app in apps:
        groups[_classify_by_age(app)].append(app)

    for label in ("KEEP", "CONSIDER", "SAFE DELETE", "UNKNOWN"):
        bucket = groups[label]
        if not bucket:
            continue
        bucket.sort(key=lambda a: a["size_kb"], reverse=True)
        total = sum(a["size_kb"] for a in bucket)
        print(f"\n  {label} ({len(bucket)} apps, {_format_size(total)})")
        print("  " + "-" * 60)
        for app in bucket:
            age_str = f"{app['age_days']}d" if app["age_days"] is not None else "?"
            print(
                f"    {app['name']:<38} {app['size_human']:>10}  {app['modified']:>12}  {age_str:>6}"
            )


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
        print_classified(apps)
        return

    # LLM-powered analysis
    print(f"Analyzing {len(apps)} apps with LLM...\n")
    result = llm_audit(apps)

    if not result:
        print("Error: LLM call failed. Use --no-llm for raw data.")
        sys.exit(1)

    print(result)
