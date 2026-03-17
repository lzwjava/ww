import os

import requests

GITHUB_API_BASE = os.environ.get("ICLAW_GITHUB_API_BASE", "https://api.github.com")
COPILOT_API_BASE = os.environ.get(
    "ICLAW_COPILOT_API_BASE", "https://api.githubcopilot.com"
)

_COPILOT_HEADERS = {
    "Content-Type": "application/json",
    "Editor-Version": "vscode/1.85.0",
    "Editor-Plugin-Version": "copilot/1.155.0",
    "User-Agent": "GithubCopilot/1.155.0",
    "Copilot-Integration-Id": "vscode-chat",
}


def _get_copilot_token(github_token):
    resp = requests.get(
        f"{GITHUB_API_BASE}/copilot_internal/v2/token",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Editor-Version": "vscode/1.85.0",
            "Editor-Plugin-Version": "copilot/1.155.0",
            "User-Agent": "GithubCopilot/1.155.0",
        },
    )
    if not resp.ok:
        raise RuntimeError(
            f"Failed to get Copilot token: {resp.status_code} {resp.reason}"
        )
    return resp.json()["token"]


def get_models(github_token):
    copilot_token = _get_copilot_token(github_token)
    resp = requests.get(
        f"{COPILOT_API_BASE}/models",
        headers={"Authorization": f"Bearer {copilot_token}", **_COPILOT_HEADERS},
    )
    if not resp.ok:
        raise RuntimeError(f"Failed to get models: {resp.status_code} {resp.reason}")
    return resp.json().get("data", [])


def call_copilot_api_with_messages(messages, model=None, debug=False):
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")

    if model is None:
        model = os.getenv("MODEL")
    if not model:
        raise RuntimeError("MODEL not specified and MODEL env var is not set")

    copilot_token = _get_copilot_token(github_token)
    payload = {"model": model, "messages": messages, "stream": False}

    if debug:
        print(f"Request URL: {COPILOT_API_BASE}/chat/completions")
        print(f"Model: {model}")

    resp = requests.post(
        f"{COPILOT_API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {copilot_token}", **_COPILOT_HEADERS},
        json=payload,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Copilot API error: {resp.status_code} {resp.reason}\n{resp.text}"
        )

    if debug:
        print(f"Response: {resp.text}")

    return resp.json()["choices"][0]["message"]["content"]


def call_copilot_api(prompt, model=None, debug=False):
    messages = [{"role": "user", "content": prompt}]
    return call_copilot_api_with_messages(messages, model, debug)
