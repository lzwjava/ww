import os
import subprocess
import sys

WW_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_ww(*args, input_text=None, timeout=30):
    """Run ww CLI command and return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env["PYTHONPATH"] = WW_PROJECT + ":" + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", "from ww.main import main; main()"] + list(args),
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=WW_PROJECT,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr
