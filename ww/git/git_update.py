from __future__ import annotations

import argparse
import json
import os
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


def update_repo(repo_path):
    print(f"[pulling] {repo_path} ...", flush=True)
    result = subprocess.run(
        ["git", "pull", "--verbose"],
        cwd=repo_path,
    )
    if result.returncode == 0:
        print(f"[updated] {repo_path}")
        return True
    else:
        print(f"[failed]  {repo_path}")
        return False


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
    updated, failed = 0, 0

    # Validate paths first
    valid_paths = []
    for path in paths:
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            print(f"[skip] {path} is not a directory")
            failed += 1
        else:
            valid_paths.append(path)

    # Parallel git pulls
    if valid_paths:
        max_workers = min(args.jobs, len(valid_paths))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(update_repo, p): p for p in valid_paths}
            for future in as_completed(futures):
                if future.result():
                    updated += 1
                else:
                    failed += 1

    elapsed = time.monotonic() - start
    print(f"\nUpdated {updated}, failed {failed} ({elapsed:.1f}s)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
