"""Trigger a GitHub Actions workflow via gh CLI.

Usage:
    ww action [workflow.yml] [--repo owner/repo] [--ref branch]
"""

import argparse
import subprocess
import sys

DEFAULT_REPO = "lzwjava/jekyll-ai-blog"
DEFAULT_WORKFLOW = "gh-pages.yml"


def trigger_workflow(workflow, repo, ref=None):
    """Trigger a workflow_dispatch event."""
    cmd = ["gh", "workflow", "run", workflow, "--repo", repo]
    if ref:
        cmd.extend(["--ref", ref])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
    print(result.stdout.strip() or f"Triggered {workflow} on {repo}")


def main():
    parser = argparse.ArgumentParser(description="Trigger a GitHub Actions workflow")
    parser.add_argument(
        "workflow",
        nargs="?",
        default=DEFAULT_WORKFLOW,
        help=f"Workflow file name (default: {DEFAULT_WORKFLOW})",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=DEFAULT_REPO,
        help=f"GitHub repo (default: {DEFAULT_REPO})",
    )
    parser.add_argument(
        "--ref",
        type=str,
        default=None,
        help="Branch or tag name (default: repo's default branch)",
    )
    args = parser.parse_args()
    trigger_workflow(args.workflow, args.repo, args.ref)
