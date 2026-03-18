import os
import subprocess
import sys

WW_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_ww(*args, input_text=None, timeout=30, env=None):
    """Run ww CLI command and return (returncode, stdout, stderr)."""
    base_env = os.environ.copy()
    if env is not None:
        base_env.update(env)
    base_env["PYTHONPATH"] = WW_PROJECT + ":" + base_env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", "from ww.main import main; main()"] + list(args),
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=WW_PROJECT,
        env=base_env,
    )
    return result.returncode, result.stdout, result.stderr
