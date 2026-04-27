import subprocess
import sys


def trigger_workflow(yaml_path):
    result = subprocess.run(
        ["gh", "workflow", "run", yaml_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
    print(result.stdout.strip() or f"Triggered {yaml_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: ww action <path/to/workflow.yml>")
        sys.exit(1)
    trigger_workflow(sys.argv[1])
