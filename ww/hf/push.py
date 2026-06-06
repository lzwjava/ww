"""Push/pull model repos to/from HuggingFace Hub (like git push/pull)."""

import os
import sys


def _get_token():
    """Get HF token from env or huggingface-cli login cache."""
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token
    # Fall back to cached token from `huggingface-cli login`
    try:
        from huggingface_hub import get_token
        return get_token()
    except Exception:
        return None


def cmd_push():
    """Push current directory (or specified path) to a HuggingFace model repo.

    Usage: ww hf push [local_path] [--repo user/repo] [--message msg] [--private]
    """
    from huggingface_hub import HfApi

    args = sys.argv[1:]  # already popped 'push'
    local_path = "."
    repo_id = None
    message = None
    private = False

    i = 0
    while i < len(args):
        if args[i] == "--repo" and i + 1 < len(args):
            repo_id = args[i + 1]
            i += 2
        elif args[i] == "--message" and i + 1 < len(args):
            message = args[i + 1]
            i += 2
        elif args[i] == "--private":
            private = True
            i += 1
        elif args[i] in ("--help", "-h"):
            print("Usage: ww hf push [local_path] [--repo user/repo] [--message msg] [--private]")
            print()
            print("Push a local directory to a HuggingFace model repository.")
            print("Defaults to current directory and infers repo from directory name.")
            print()
            print("Options:")
            print("  local_path          Local directory to push (default: .)")
            print("  --repo user/repo    HuggingFace repo ID (default: <username>/<dirname>)")
            print("  --message msg       Commit message (default: 'Upload model')")
            print("  --private           Create repo as private if it doesn't exist")
            return
        elif not args[i].startswith("-") and local_path == ".":
            local_path = args[i]
            i += 1
        else:
            i += 1

    token = _get_token()
    if not token:
        print("Error: No HF token found. Run 'huggingface-cli login' or set HF_TOKEN.")
        sys.exit(1)

    api = HfApi(token=token)

    # Resolve repo_id
    if not repo_id:
        whoami = api.whoami()
        username = whoami.get("name", "unknown")
        dirname = os.path.basename(os.path.abspath(local_path))
        repo_id = f"{username}/{dirname}"

    if not message:
        message = "Upload model"

    local_path = os.path.abspath(local_path)
    if not os.path.isdir(local_path):
        print(f"Error: '{local_path}' is not a directory.")
        sys.exit(1)

    # Create repo if it doesn't exist
    print(f"Repo:   {repo_id}")
    print(f"Path:   {local_path}")
    print("Type:   model")
    print()

    try:
        api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True, private=private)
        print(f"Repo ensured: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"Error creating repo: {e}")
        sys.exit(1)

    # Upload entire folder
    print(f"Uploading... ({message})")
    try:
        result = api.upload_folder(
            repo_id=repo_id,
            repo_type="model",
            folder_path=local_path,
            commit_message=message,
        )
        print(f"Done! {result}")
        print(f"https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"Error uploading: {e}")
        sys.exit(1)


def cmd_pull():
    """Pull (download) a HuggingFace model repo to a local directory.

    Usage: ww hf pull <user/repo> [local_path] [--revision branch]
    """
    from huggingface_hub import snapshot_download

    args = sys.argv[1:]  # already popped 'pull'
    repo_id = None
    local_path = None
    revision = None

    i = 0
    while i < len(args):
        if args[i] == "--revision" and i + 1 < len(args):
            revision = args[i + 1]
            i += 2
        elif args[i] in ("--help", "-h"):
            print("Usage: ww hf pull [user/repo] [local_path] [--revision branch]")
            print()
            print("Download a HuggingFace model repo to a local directory.")
            print("Defaults to <username>/<dirname> inferred from HF token + cwd.")
            print()
            print("Options:")
            print("  user/repo           HuggingFace repo ID (default: inferred)")
            print("  local_path          Local directory (default: current directory)")
            print("  --revision branch   Branch, tag, or commit to pull (default: main)")
            return
        elif not args[i].startswith("-"):
            if repo_id is None:
                repo_id = args[i]
            elif local_path is None:
                local_path = args[i]
            i += 1
        else:
            i += 1

    if not repo_id:
        token = _get_token()
        if not token:
            print("Error: No HF token found. Run 'huggingface-cli login' or set HF_TOKEN.")
            sys.exit(1)
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        whoami = api.whoami()
        username = whoami.get("name", "unknown")
        dirname = os.path.basename(os.getcwd())
        repo_id = f"{username}/{dirname}"

    token = _get_token()

    # Default local_path to current directory (like push)
    if not local_path:
        local_path = os.getcwd()

    local_path = os.path.abspath(local_path)

    print(f"Repo:   {repo_id}")
    print(f"Path:   {local_path}")
    print("Type:   model")
    if revision:
        print(f"Branch: {revision}")
    print()
    print("Downloading...")

    try:
        kwargs = {
            "repo_id": repo_id,
            "repo_type": "model",
            "local_dir": local_path,
        }
        if token:
            kwargs["token"] = token
        if revision:
            kwargs["revision"] = revision

        result = snapshot_download(**kwargs)
        print(f"Done! Downloaded to: {result}")
    except Exception as e:
        print(f"Error downloading: {e}")
        sys.exit(1)
