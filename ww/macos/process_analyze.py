import argparse
import subprocess
import sys

from ww.llm.openrouter_client import call_openrouter_api


ANALYZE_PROMPT = """You are analyzing the running processes on a macOS machine to suggest which ones can be safely killed to free up CPU and memory.

For each process you recommend killing, provide:
- The PID and process name
- Approximate CPU% / MEM% being used
- A short reason it's safe to kill (e.g. user-launched app, known background helper, runaway process)
- The exact `kill` command to run

Skip system-critical processes (kernel_task, launchd, WindowServer, coreaudiod, loginwindow, hidd, mds, mds_stores, etc.) - flag them as "do not kill".

Group your output as:
1. SAFE TO KILL (user apps, dev servers, browser tabs, runaway helpers)
2. PROBABLY OK (background helpers — kill if you don't need that feature right now)
3. DO NOT KILL (system processes)

Be concise. No preamble.

Process list (from `ps aux` sorted by CPU then memory):
---
{processes}
---"""


def collect_processes(limit):
    result = subprocess.run(
        ["ps", "-Ao", "pid,user,%cpu,%mem,rss,command", "-r"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ps failed: {result.stderr}")
    lines = result.stdout.strip().split("\n")
    header = lines[0]
    body = lines[1 : 1 + limit]
    return "\n".join([header] + body)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze running macOS processes and suggest what to kill"
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=40,
        help="Number of top processes to analyze (default: 40)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the LLM model (defaults to MODEL env var)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the raw process list instead of calling the LLM",
    )
    args = parser.parse_args(sys.argv[1:])

    processes = collect_processes(args.limit)

    if args.raw:
        print(processes)
        return

    prompt = ANALYZE_PROMPT.format(processes=processes)
    suggestion = call_openrouter_api(prompt, model=args.model)

    if not suggestion:
        print("Error: LLM call failed.")
        sys.exit(1)

    print(suggestion)
