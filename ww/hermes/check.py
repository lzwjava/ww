"""ww hermes check — verify Hermes note plugin works correctly on any platform."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def _check(cond, msg):
    icon = "✅" if cond else "❌"
    print(f"  {icon}  {msg}")
    return cond


def _check_plugin_files():
    """Check the Hermes note plugin files exist and compile."""
    plugin_dir = Path.home() / ".hermes" / "plugins" / "note"

    init_py = plugin_dir / "__init__.py"
    yaml = plugin_dir / "plugin.yaml"

    ok = True
    ok &= _check(init_py.exists(), f"Plugin exists at {init_py}")
    ok &= _check(yaml.exists(), f"Plugin yaml at {yaml}")

    if not ok:
        return False

    # Check plugin code compiles and has all required functions
    try:
        spec = importlib.util.spec_from_file_location("note_plugin", str(init_py))
        if spec is None or spec.loader is None:
            _check(False, "Could not create module spec from plugin file")
            return False
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _check(True, "Plugin code compiles without errors")

        for fn in [
            "_strip_reasoning_tags",
            "_content_as_text",
            "_get_assistant_messages",
            "_handle_note",
            "register",
        ]:
            _check(hasattr(mod, fn), f"Function `{fn}()` defined")
    except Exception as e:
        _check(False, f"Plugin code failed to compile: {e}")
        return False

    return True


def _check_ww_package():
    """Check the ww package can be imported from the plugin."""
    ww_path = Path.home() / "projects" / "ww"

    ok = True
    ok &= _check(ww_path.exists(), f"ww project found at {ww_path}")

    if not ok:
        return False

    # Ensure ww is on sys.path (mirrors what the plugin does at runtime)
    ww_str = str(ww_path)
    if ww_str not in sys.path:
        sys.path.insert(0, ww_str)

    try:
        from ww.note.create_note_from_clipboard import create_note_from_content  # noqa: F401

        _check(True, "ww.note.create_note_from_clipboard imports OK")
    except ImportError as e:
        _check(False, f"ww.note.create_note_from_clipboard import failed: {e}")
        ok = False

    try:
        from ww.github.gitmessageai import gitmessageai  # noqa: F401

        _check(True, "ww.github.gitmessageai imports OK")
    except ImportError as e:
        _check(False, f"ww.github.gitmessageai import failed: {e}")
        ok = False

    return ok


def _check_dependencies():
    """Check Python dependencies the plugin needs at runtime."""
    deps = [
        ("pyperclip", "clipboard operations"),
        ("dotenv", ".env file loading"),
        ("requests", "HTTP/API calls"),
    ]

    ok = True
    for mod_name, description in deps:
        try:
            __import__(mod_name)
            _check(True, f"{mod_name} — {description}")
        except ImportError:
            _check(False, f"{mod_name} — {description} (missing)")
            ok = False

    return ok


def _check_env():
    """Check environment variables the plugin needs."""
    ok = True

    # Mirror ww.env.load_env search order
    env_file_path = _find_env()
    ok &= _check(
        env_file_path is not None,
        ".env found" if env_file_path else ".env not found in any expected location",
    )

    model = os.environ.get("MODEL", "")
    if not model:
        model = _read_from_env("MODEL", env_file_path)

    ok &= _check(bool(model), f"MODEL = {model or '(not set)'}")

    base_path = os.environ.get("BASE_PATH", "").strip()
    if not base_path or base_path == ".":
        base_path = _read_from_env("BASE_PATH", env_file_path)
    if not base_path or base_path == ".":
        _check(True, "BASE_PATH not set (notes go to current directory)")
    else:
        expanded = os.path.expanduser(base_path)
        ok &= _check(
            Path(expanded).exists(), f"BASE_PATH = {base_path} (resolves to {expanded})"
        )

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        api_key = _read_from_env("OPENROUTER_API_KEY", env_file_path)
    if api_key:
        _check(True, f"OPENROUTER_API_KEY is set ({len(api_key)} chars)")
    else:
        print(
            "  ⚠️   OPENROUTER_API_KEY not found — LLM title gen will fail if not set in shell"
        )
        # Not fatal: user may have it in shell profile

    return ok


def _find_env():
    """Search for ww .env in standard locations."""
    candidates = [
        Path.home() / ".config" / "ww" / ".env",
        Path.home() / "projects" / "ww" / ".env",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _read_from_env(key: str, env_file_path, default=""):
    """Read a key from a .env file."""
    if not env_file_path:
        return default
    try:
        for line in env_file_path.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key}=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip()
    except (OSError, PermissionError):
        pass
    return default


def _check_git():
    """Check git repo state for auto-commit."""
    base_path = os.environ.get("BASE_PATH", "").strip()
    if not base_path or base_path == ".":
        env_f = _find_env()
        if env_f:
            base_path = _read_from_env("BASE_PATH", env_f)

    if not base_path or base_path == ".":
        print("  ℹ️   BASE_PATH not set — skipping git check")
        return True

    repo = os.path.expanduser(base_path)
    if not Path(repo).exists():
        _check(False, f"BASE_PATH directory does not exist: {repo}")
        return False

    try:
        result = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            _check(False, f"Not a git repository: {repo}")
            return False

        git_root = result.stdout.strip()
        _check(True, f"Git repo root: {git_root}")

        status = subprocess.run(
            ["git", "-C", repo, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        uncommitted = status.stdout.strip()
        if uncommitted:
            count = len(uncommitted.splitlines())
            _check(False, f"Git repo has {count} uncommitted file(s)")
        else:
            _check(True, "Git repo is clean (ready for auto-commit)")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        _check(False, f"Git check failed: {e}")
        return False

    return True


def main():
    """Run all checks and report status."""
    print("🔍 Hermes Note Plugin — Health Check")
    print("━" * 42)
    print()

    print("📁  Plugin Files:")
    plugin_ok = _check_plugin_files()
    print()

    print("📦  ww Package:")
    ww_ok = _check_ww_package()
    print()

    print("🔧  Python Dependencies:")
    deps_ok = _check_dependencies()
    print()

    print("⚙️   Environment:")
    env_ok = _check_env()
    print()

    print("🔗  Git Repo:")
    git_ok = _check_git()
    print()

    print("━" * 42)
    all_ok = plugin_ok and ww_ok and deps_ok and env_ok and git_ok
    if all_ok:
        print("✅  All checks passed — /note plugin is ready")
        sys.exit(0)
    else:
        print("❌  Some checks failed — review issues above")
        sys.exit(1)


if __name__ == "__main__":
    main()
