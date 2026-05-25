"""Check GitHub Actions workflow run status.

Usage:
    ww actions check [workflow.yml] [--repo owner/repo] [--count N]
"""

import argparse
from datetime import datetime, timezone

from ww.github.github_mgmt import _get


def _parse_time(ts_str):
    """Parse ISO timestamp to datetime."""
    if not ts_str:
        return None
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))


def _time_ago(dt):
    """Human-readable time ago string."""
    if dt is None:
        return "?"
    now = datetime.now(timezone.utc)
    delta = now - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{secs}s ago"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


STATUS_ICONS = {
    "success": "\033[32m✓\033[0m",
    "failure": "\033[31m✗\033[0m",
    "cancelled": "\033[33m○\033[0m",
    "in_progress": "\033[34m⟳\033[0m",
    "queued": "\033[37m◌\033[0m",
    "skipped": "\033[90m-\033[0m",
}


def _status_icon(conclusion):
    """Color-coded status icon."""
    if conclusion is None:
        return STATUS_ICONS.get("in_progress", "?")
    return STATUS_ICONS.get(conclusion, f"?({conclusion})")


def check_runs(repo, workflow_file=None, count=10):
    """Fetch and display recent workflow runs."""
    path = f"repos/{repo}/actions/runs"
    params = {"per_page": count}
    if workflow_file:
        path = f"repos/{repo}/actions/workflows/{workflow_file}/runs"
    data, _ = _get(path, params)
    runs = data.get("workflow_runs", [])
    if not runs:
        print(f"No workflow runs found for {repo}")
        return

    failures = [r for r in runs if r.get("conclusion") == "failure"]
    successes = [r for r in runs if r.get("conclusion") == "success"]

    wf_name = workflow_file or "all workflows"
    print(f"GitHub Actions: {repo} ({wf_name})")
    print("=" * 70)
    print(
        f"  Total: {len(runs)}  |  "
        f"\033[32m✓ {len(successes)}\033[0m  |  "
        f"\033[31m✗ {len(failures)}\033[0m"
    )
    print()

    for r in runs:
        icon = _status_icon(r.get("conclusion"))
        num = r.get("run_number", "?")
        title = (r.get("head_commit", {}) or {}).get("message", "")
        title = title.split("\n")[0][:55]
        branch = r.get("head_branch", "?")
        created = _parse_time(r.get("created_at"))
        ago = _time_ago(created)
        run_id = r.get("id", "")

        print(f"  {icon} #{num:<5} {branch:<16} {ago:<8} {title}")
        if r.get("conclusion") == "failure":
            print(f"        → https://github.com/{repo}/actions/runs/{run_id}")

    if failures:
        print()
        print(f"  ⚠  {len(failures)} failed build(s) in last {len(runs)} runs:")
        for r in failures:
            num = r.get("run_number", "?")
            created = _parse_time(r.get("created_at"))
            ago = _time_ago(created)
            title = (r.get("head_commit", {}) or {}).get("message", "")
            title = title.split("\n")[0][:50]
            print(f"     #{num}  {ago}  {title}")


def main():
    parser = argparse.ArgumentParser(description="Check GitHub Actions workflow status")
    parser.add_argument(
        "workflow",
        nargs="?",
        default=None,
        help="Workflow file name (e.g. gh-pages.yml). Omit for all workflows.",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="lzwjava/jekyll-ai-blog",
        help="GitHub repo (default: lzwjava/jekyll-ai-blog)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of recent runs to show (default: 10)",
    )
    args = parser.parse_args()
    check_runs(args.repo, args.workflow, args.count)
