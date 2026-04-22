from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

updated_repos = ["jdk", "pytorch"]

REPOS_BASE = Path.home() / "projects"


def update_repo(repo_path):
    print(f"[pulling] {repo_path} ...", flush=True)
    result = subprocess.run(
        ["git", "pull"],
        capture_output=True,
        text=True,
        cwd=repo_path,
    )
    if result.returncode == 0:
        out = result.stdout.strip()
        print(f"[updated] {repo_path}" + (f"\n          {out}" if out else ""))
        return True
    else:
        print(f"[failed]  {repo_path}")
        for line in (result.stderr.strip() + "\n" + result.stdout.strip()).splitlines():
            if line.strip():
                print(f"          {line}")
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Update git repos")
    parser.add_argument(
        "targets",
        nargs="*",
        help="Repo names (from ~/repos) or paths",
    )
    args = parser.parse_args(argv)

    if not args.targets:
        targets = updated_repos
    else:
        targets = args.targets

    paths = resolve_repos(targets)

    updated, failed = 0, 0
    for path in paths:
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            print(f"[skip] {path} is not a directory")
            failed += 1
            continue
        if not update_repo(path):
            failed += 1
        else:
            updated += 1

    print(f"\nUpdated {updated}, failed {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
