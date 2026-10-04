"""Set the default startup model of the pi coding agent.

Pi reads user settings from <agent-dir>/settings.json (agent dir defaults to
~/.pi/agent, override with PI_CODING_AGENT_DIR). The startup model is defined
by the `defaultProvider` and `defaultModel` keys.
"""

import json
import os
import sys


def agent_dir():
    d = os.environ.get("PI_CODING_AGENT_DIR", "").strip()
    if d:
        return os.path.expanduser(d)
    return os.path.join(os.path.expanduser("~"), ".pi", "agent")


def settings_path():
    return os.path.join(agent_dir(), "settings.json")


def load_settings():
    path = settings_path()
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings):
    path = settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def _usage():
    print("Usage: ww pi set-model <provider>/<model> [--provider <provider>]")
    print("")
    print("Set the default startup model of the pi coding agent.")
    print("")
    print("The provider is the segment before the first '/'. Models that already")
    print("contain '/' (e.g. xiaomi/mimo-v2.6-flash) can be passed with an")
    print("explicit --provider to keep the full model id intact:")
    print("")
    print("  ww pi set-model openrouter/xiaomi/mimo-v2.6-flash")
    print("  ww pi set-model xiaomi/mimo-v2.6-flash --provider openrouter")


def main():
    args = sys.argv[1:]
    provider = None
    spec = None

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--help", "-h"):
            _usage()
            return
        if a == "--provider":
            if i + 1 >= len(args):
                print("Error: --provider requires a value")
                sys.exit(1)
            provider = args[i + 1]
            i += 2
            continue
        if a.startswith("--provider="):
            provider = a.split("=", 1)[1]
            i += 1
            continue
        if spec is None:
            spec = a
            i += 1
            continue
        print(f"Error: unexpected argument: {a}")
        sys.exit(1)

    if spec is None:
        _usage()
        sys.exit(1)

    # Split "provider/model" at the first '/' unless --provider was given.
    if provider is None and "/" in spec:
        provider, _, spec = spec.partition("/")

    if not provider or not spec:
        print(
            "Error: specify provider and model, e.g. openrouter/xiaomi/mimo-v2.6-flash"
        )
        sys.exit(1)

    settings = load_settings()
    old_provider = settings.get("defaultProvider", "")
    old_model = settings.get("defaultModel", "")

    settings["defaultProvider"] = provider
    settings["defaultModel"] = spec
    save_settings(settings)

    if old_provider or old_model:
        print(f"Previous: {old_provider}/{old_model}")
    print(f"Set:      {provider}/{spec}")
    print(f"Saved to: {settings_path()}")


if __name__ == "__main__":
    main()
