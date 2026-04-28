import os
import re

import requests

ARENA_PREFIXES = [
    "anthropic/claude-opus",
    "anthropic/claude-sonnet",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "openai/gpt-4.1",
    "openai/gpt-4o",
    "x-ai/grok-3",
    "deepseek/deepseek-r1",
    "meta-llama/llama-4-maverick",
    "mistralai/mistral-large",
]


def fetch_models(api_key):
    resp = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    if not resp.ok:
        raise Exception(f"OpenRouter error: {resp.status_code} {resp.text}")
    return resp.json().get("data", [])


def pick_top(models):
    priority = {}
    for rank, prefix in enumerate(ARENA_PREFIXES):
        for m in models:
            mid = m["id"]
            if mid.startswith(prefix) and mid not in priority:
                priority[mid] = (rank, m)
                break

    ranked = sorted(
        priority.values(), key=lambda x: (x[0], -x[1].get("context_length", 0))
    )
    selected_ids = {m["id"] for _, m in ranked}

    extras = sorted(
        [m for m in models if m["id"] not in selected_ids],
        key=lambda m: -m.get("context_length", 0),
    )

    return [m for _, m in ranked] + extras[: max(0, 10 - len(ranked))]


def find_env_path():
    if os.path.isfile(".env"):
        return ".env"
    base = os.environ.get("BASE_PATH", "").strip()
    if base and base != ".":
        alt = os.path.join(base, ".env")
        if os.path.isfile(alt):
            return alt
    return ".env"


def set_model(env_path, model_id):
    try:
        with open(env_path) as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    if re.search(r"^MODEL=", content, re.MULTILINE):
        content = re.sub(
            r"^MODEL=.*$", f"MODEL={model_id}", content, flags=re.MULTILINE
        )
    else:
        content += f"\nMODEL={model_id}\n"

    with open(env_path, "w") as f:
        f.write(content)


def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        return

    print("Fetching models from OpenRouter...")
    models = fetch_models(api_key)
    top = pick_top(models)

    current = os.getenv("MODEL", "(not set)")
    print(f"\nCurrent MODEL: {current}\n")
    print("Top models (Arena-ranked):\n")

    for i, m in enumerate(top, 1):
        ctx = m.get("context_length", 0)
        ctx_str = f"{ctx // 1000}K" if ctx >= 1000 else str(ctx)
        name = m.get("name", m["id"])
        print(f"  {i:2}. {name:<42} {m['id']:<52} ctx:{ctx_str}")

    print()
    choice = input("Pick a number (1-10) or Enter to cancel: ").strip()
    if not choice:
        print("Cancelled.")
        return

    try:
        idx = int(choice) - 1
        if not 0 <= idx < len(top):
            raise ValueError()
    except ValueError:
        print("Invalid choice.")
        return

    selected = top[idx]["id"]
    env_path = find_env_path()
    set_model(env_path, selected)
    print(f"\nUpdated {env_path}: MODEL={selected}")
