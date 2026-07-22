"""Process the note queue — drain pending entries through the full pipeline."""

import os
import sys

from ww.content.fix_mathjax import fix_mathjax_in_file
from ww.content.fix_table import process_tables_in_file
from ww.note.create_note_from_clipboard import create_note_from_content
from ww.note.create_note_utils import get_base_path
from ww.note.create_normal_log import create_normal_log
from ww.note.note_queue import get_pending, mark_done, mark_failed


def _git_toplevel() -> str:
    from ww.note.note_workflow import _git_toplevel

    return _git_toplevel()


def _git_pull_rebase() -> None:
    from ww.note.note_workflow import git_pull_rebase

    git_pull_rebase()


def _check_uncommitted() -> None:
    from ww.note.note_workflow import check_uncommitted_changes

    check_uncommitted_changes()


def _git_commit_push(files=None) -> None:
    """AI-powered commit + push via gitmessageai."""
    import subprocess

    from ww.github.gitmessageai import gitmessageai

    base = get_base_path()
    directory = None if base == "." else base
    git = ["git", "-C", directory] if directory else ["git"]
    try:
        gitmessageai(allow_pull_push=True, directory=directory, files=files)
    except subprocess.CalledProcessError:
        # Pre-commit hooks may have modified files (e.g. end-of-file-fixer).
        # Re-stage them so the index matches the working tree, then retry once.
        if files:
            subprocess.run([*git, "add", *files], check=True)
        else:
            subprocess.run([*git, "add", "-A"], check=True)
        gitmessageai(allow_pull_push=True, directory=directory, files=files)


def _print_note_links(files: list[str], directory: str | None) -> None:
    """Print GitHub links for each pushed note file."""
    import subprocess

    git = ["git", "-C", directory] if directory else ["git"]

    # Get remote URL
    try:
        remote = subprocess.run(
            [*git, "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return  # no remote configured, skip

    # Parse owner/repo from git@github.com:owner/repo.git or https://github.com/owner/repo
    for prefix in ("git@github.com:", "https://github.com/"):
        if remote.startswith(prefix):
            repo_path = remote[len(prefix) :]
            break
    else:
        return  # not a GitHub remote
    repo_path = repo_path.removesuffix(".git")

    # Get git root to relativize file paths
    try:
        toplevel = subprocess.run(
            [*git, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return

    for f in files:
        rel = os.path.relpath(f, toplevel) if os.path.isabs(f) else f
        url = f"https://github.com/{repo_path}/blob/main/{rel}"
        print(f"  {url}")


def process_queue(dry_run: bool = False) -> None:
    """Drain all pending queue entries through the full note pipeline."""
    pending = get_pending()
    if not pending:
        print("[ok] Queue is empty, nothing to process")
        return

    print(f"[info] Processing {len(pending)} pending note(s)...")

    # Pre-flight: git state
    try:
        _check_uncommitted()
    except RuntimeError:
        print("[error] Fix uncommitted changes first, then run 'ww note process' again")
        sys.exit(1)

    try:
        _git_pull_rebase()
    except Exception as e:
        print(f"[warn] git pull failed: {e} — continuing anyway")

    created_paths = []
    for i, entry in enumerate(pending, 1):
        entry_id = entry["id"]
        content = entry["content"]
        entry_type = entry.get("type", "note")
        preview = content[:60].replace("\n", " ")
        print(
            f"\n[{i}/{len(pending)}] Processing {entry_id} ({entry_type}): {preview}..."
        )

        if dry_run:
            print(f"  [dry-run] Would create {entry_type} from {len(content)} chars")
            continue

        try:
            if entry_type == "log":
                file_path = create_normal_log(
                    content,
                    ext=entry.get("ext"),
                    friendly_name=entry.get("friendly_name", False),
                    detect_ext=entry.get("detect_ext", False),
                    skip_git=True,
                )
                print(f"  [ok] Created: {file_path}")
            elif entry_type == "html":
                from ww.note.create_note_html import create_note_html as create_html

                file_path = create_html(content)
                print(f"  [ok] Created: {file_path}")
            else:
                file_path = create_note_from_content(content)
                print(f"  [ok] Created: {file_path}")
        except Exception as e:
            print(f"  [error] Failed to create {entry_type}: {e}")
            mark_failed(entry_id, str(e))
            continue

        # Post-processing: MathJax + table fix (notes only)
        if entry_type != "note":
            if file_path and os.path.exists(file_path):
                created_paths.append(file_path)
                mark_done(entry_id, file_path)
                print(f"  [done] {entry_id}")
            else:
                mark_failed(entry_id, f"Log file not created: {file_path}")
            continue

        if file_path and os.path.exists(file_path):
            try:
                fix_mathjax_in_file(file_path, gemini=False)
                process_tables_in_file(file_path, fix_tables=True)
            except Exception as e:
                print(f"  [warn] Post-processing failed: {e}")

            created_paths.append(file_path)
            mark_done(entry_id, file_path)
            print(f"  [done] {entry_id}")
        else:
            mark_failed(entry_id, f"Note file not created: {file_path}")

    if dry_run:
        print(f"\n[dry-run] Would commit and push {len(pending)} note(s)")
        return

    # Single git commit + push for all created notes
    if created_paths:
        print(f"\n[info] Committing and pushing {len(created_paths)} note(s)...")
        try:
            _git_commit_push(files=created_paths)
            print("[ok] All notes committed and pushed")
            base = get_base_path()
            _print_note_links(created_paths, None if base == "." else base)
        except Exception as e:
            print(f"[error] Git commit/push failed: {e}")
            print(f"  Created files: {created_paths}")
            print("  Run 'ww note process' again to retry the push")
    else:
        print("\n[warn] No notes were created successfully")

    # Auto-clean: remove done/failed entries from queue
    from ww.note.note_queue import clear_done

    removed = clear_done()
    if removed:
        print(f"[ok] Cleaned {removed} processed entry/entries from queue")


def main():
    """CLI entry point for 'ww note process'."""
    dry_run = "--dry-run" in sys.argv
    process_queue(dry_run=dry_run)
