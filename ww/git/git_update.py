from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPOS_BASE = Path.home() / "projects"
CONFIG_PATH = Path(__file__).parent.parent / "projects" / "repos.json"

# Legacy fallback — used only if repos.json is missing
FALLBACK_REPOS = [
    "pytorch",
    "llama.cpp",
    "nanoGPT",
    "modded-nanogpt",
    "llm.c",
    "open-webui",
    "dify",
    "ComfyUI",
    "stable-diffusion-webui",
    "clash-core",
]


def load_config_repos():
    """Load repo list from repos.json config file."""
    if not CONFIG_PATH.exists():
        return FALLBACK_REPOS, {}
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    repos = []
    categories = {}
    for cat, entries in data.get("repos", {}).items():
        categories[cat] = entries
        repos.extend(entries)
    return repos, categories


def _get_current_branch(repo_path):
    """Get the current branch name, or None if detached."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        branch = result.stdout.strip()
        if branch != "HEAD":
            return branch
    return None


def _has_upstream(repo_path, branch):
    """Check if the branch has an upstream tracking ref."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{u}}"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def fetch_repo(repo_path):
    """Fetch remote refs. Returns (repo_path, needs_pull, fetch_ok)."""
    branch = _get_current_branch(repo_path)
    if branch and not _has_upstream(repo_path, branch):
        # No upstream — skip entirely (local-only branch)
        return repo_path, False, True

    result = subprocess.run(
        ["git", "fetch"],
        cwd=repo_path,
        capture_output=True,
    )
    if result.returncode != 0:
        return repo_path, False, False

    # Check if local is behind remote
    if branch:
        count_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..@{u}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if count_result.returncode == 0:
            behind = int(count_result.stdout.strip())
            return repo_path, behind > 0, True

    return repo_path, False, True


def _get_short_stats(repo_path, old_head, new_head):
    """Get short diff stats between two commits. Returns (commits, files, ins, dels) or None."""
    # Commit count
    r = subprocess.run(
        ["git", "rev-list", "--count", f"{old_head}..{new_head}"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return None
    commits = int(r.stdout.strip())
    # Shortstat
    r = subprocess.run(
        ["git", "diff", "--shortstat", old_head, new_head],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    files, ins, dels = 0, 0, 0
    if r.returncode == 0 and r.stdout.strip():
        s = r.stdout.strip()
        m = re.search(r"(\d+) files? changed", s)
        if m:
            files = int(m.group(1))
        m = re.search(r"(\d+) insertions?", s)
        if m:
            ins = int(m.group(1))
        m = re.search(r"(\d+) deletions?", s)
        if m:
            dels = int(m.group(1))
    return commits, files, ins, dels


def pull_repo(repo_path):
    """Pull (fetch + merge) a repo that needs updating.
    Returns (repo_path, success, stats_dict_or_None).
    """
    # Record HEAD before pull
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    old_head = r.stdout.strip() if r.returncode == 0 else None

    result = subprocess.run(
        ["git", "pull", "--verbose"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    ok = result.returncode == 0
    stats = None
    if ok and old_head:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        new_head = r.stdout.strip()
        if r.returncode == 0 and new_head != old_head:
            stats = _get_short_stats(repo_path, old_head, new_head)
    return repo_path, ok, stats


def resolve_repos(names_or_paths):
    repos = []
    for name_or_path in names_or_paths:
        if os.path.isabs(name_or_path) or name_or_path.startswith("."):
            repos.append(name_or_path)
        elif os.path.isdir(name_or_path):
            repos.append(name_or_path)
        else:
            repo_path = REPOS_BASE / name_or_path
            if repo_path.exists():
                repos.append(str(repo_path))
            else:
                print(f"[skip] {name_or_path} not found in {REPOS_BASE}")
    return repos


def resolve_category(category):
    """Resolve repos in a specific category from config."""
    _, categories = load_config_repos()
    if category not in categories:
        print(f"Unknown category: {category}")
        print(f"Available: {', '.join(categories.keys())}")
        return []
    return resolve_repos(categories[category])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Update git repos")
    parser.add_argument(
        "targets",
        nargs="*",
        help="Repo names (from ~/projects), paths, or @category",
    )
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=8,
        help="Number of parallel git pull workers (default: 8)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List configured repos and categories",
    )
    parser.add_argument(
        "--category",
        "-c",
        help="Update only repos in a specific category",
    )
    args = parser.parse_args(argv)

    config_repos, categories = load_config_repos()

    if args.list:
        print("Configured repos by category:\n")
        for cat, entries in categories.items():
            print(f"  [{cat}] ({len(entries)} repos)")
            for r in entries:
                print(f"    {r}")
            print()
        print(f"Total: {len(config_repos)} repos")
        return 0

    if args.category:
        paths = resolve_category(args.category)
    elif not args.targets:
        paths = resolve_repos(config_repos)
    else:
        # Support @category syntax inline
        expanded = []
        for t in args.targets:
            if t.startswith("@"):
                cat = t[1:]
                _, cats = load_config_repos()
                if cat in cats:
                    expanded.extend(cats[cat])
                else:
                    print(f"Unknown category: {cat}")
                    print(f"Available: {', '.join(cats.keys())}")
                    return 1
            else:
                expanded.append(t)
        paths = resolve_repos(expanded)

    if not paths:
        print("No repos to update.")
        return 1

    print(f"Updating {len(paths)} repos (jobs={args.jobs})...\n")
    start = time.monotonic()

    # Validate paths first
    valid_paths = []
    for path in paths:
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            print(f"[skip] {path} is not a directory")
        else:
            valid_paths.append(path)

    if not valid_paths:
        print("No valid repos.")
        return 1

    # Phase 1: Fetch all repos in parallel (lightweight — just check for changes)
    needs_pull = []
    fetch_failed = []
    up_to_date = 0
    max_workers = min(args.jobs, len(valid_paths))

    print(f"[phase 1] Fetching {len(valid_paths)} repos...")
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_repo, p): p for p in valid_paths}
        for future in as_completed(futures):
            repo_path, should_pull, ok = future.result()
            if not ok:
                fetch_failed.append(repo_path)
            elif should_pull:
                needs_pull.append(repo_path)
            else:
                up_to_date += 1

    print(
        f"  {up_to_date} up-to-date, {len(needs_pull)} need update, {len(fetch_failed)} failed\n"
    )

    # Phase 2: Pull only repos that need updating
    updated, pull_failed = 0, 0
    pull_stats = []  # (repo_name, (commits, files, ins, dels))
    if needs_pull:
        print(f"[phase 2] Pulling {len(needs_pull)} repos...")
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(pull_repo, p): p for p in needs_pull}
            for future in as_completed(futures):
                repo_path, ok, stats = future.result()
                if ok:
                    updated += 1
                    if stats:
                        name = os.path.basename(repo_path)
                        pull_stats.append((name, stats))
                else:
                    pull_failed += 1

    total_failed = len(fetch_failed) + pull_failed
    elapsed = time.monotonic() - start

    for p in fetch_failed:
        print(f"[failed]  {p}")

    print(
        f"\nDone: {up_to_date} current, {updated} updated, {total_failed} failed ({elapsed:.1f}s)"
    )

    # Summary table
    if pull_stats:
        pull_stats.sort(key=lambda x: x[0])
        total_c = sum(s[0] for _, s in pull_stats)
        total_f = sum(s[1] for _, s in pull_stats)
        total_i = sum(s[2] for _, s in pull_stats)
        total_d = sum(s[3] for _, s in pull_stats)
        # Column widths
        nw = max(len(n) for n, _ in pull_stats)
        nw = max(nw, 6)  # min "Repo" width
        print(f"\n{'Repo':<{nw}}  commits  files changed  insertions(+)  deletions(-)")
        print(f"{'─' * nw}  ───────  ─────────────  ─────────────  ───────────")
        for name, (c, f, i, d) in pull_stats:
            print(f"{name:<{nw}}  {c:>7}  {f:>13}  {i:>13}  {d:>11}")
        print(f"{'─' * nw}  ───────  ─────────────  ─────────────  ───────────")
        print(
            f"{'TOTAL':<{nw}}  {total_c:>7}  {total_f:>13}  {total_i:>13}  {total_d:>11}"
        )

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
