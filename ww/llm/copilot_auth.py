#!/usr/bin/env python3
"""GitHub OAuth device flow to obtain a personal access token for Copilot API."""

import json
import os
import time

import requests

GITHUB_CLIENT_ID = "01ab8ac9400c4e429b23"  # VSCode's client ID


def _get_device_code():
    resp = requests.post(
        "https://github.com/login/device/code",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json={"client_id": GITHUB_CLIENT_ID, "scope": "read:user repo"},
    )
    resp.raise_for_status()
    return resp.json()


def _poll_for_access_token(device_code, interval=5):
    while True:
        time.sleep(interval)
        resp = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={
                "client_id": GITHUB_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if "access_token" in data:
            return data["access_token"]
        elif data.get("error") == "authorization_pending":
            print("Waiting for authorization...", end="\r")
        elif data.get("error") == "slow_down":
            interval += 5
        elif data.get("error") == "expired_token":
            raise RuntimeError("Device code expired. Please run auth again.")
        else:
            raise RuntimeError(f"OAuth error: {json.dumps(data)}")


def _save_token_to_env(token, env_path=".env"):
    existing = open(env_path).readlines() if os.path.exists(env_path) else []
    token_line = f"GITHUB_TOKEN={token}\n"
    updated = [
        token_line if line.startswith("GITHUB_TOKEN=") else line for line in existing
    ]
    if token_line not in updated:
        updated.append(token_line)
    with open(env_path, "w") as f:
        f.writelines(updated)


def main():
    print("Starting GitHub OAuth device flow...")
    data = _get_device_code()
    print(f"\nVisit: {data['verification_uri']}")
    print(f"Enter code: {data['user_code']}\n")

    token = _poll_for_access_token(data["device_code"], data.get("interval", 5))
    print(f"\nGitHub token obtained: {token[:8]}...")

    _save_token_to_env(token)
    print("Saved GITHUB_TOKEN to .env")
