import os

import requests


def call_openrouter_api_with_messages(
    messages, model=None, max_tokens=None, debug=False
):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise Exception("OPENROUTER_API_KEY environment variable is not set")

    if model is None:
        model = os.getenv("MODEL")
    if not model:
        raise Exception("MODEL not specified and MODEL env var is not set")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = {"model": model, "messages": messages}
    if max_tokens is not None:
        data["max_tokens"] = max_tokens

    if debug:
        print(f"Request URL: {url}")
        print(f"Request Data: {data}")

    response = requests.post(url, headers=headers, json=data)
    if debug:
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")

    if not response.ok:
        raise Exception(f"Error: {response.status_code} - {response.text}")
    return response.json()["choices"][0]["message"]["content"]


def call_openrouter_api(prompt, model=None, max_tokens=None, debug=False):
    messages = [{"role": "user", "content": prompt}]
    return call_openrouter_api_with_messages(messages, model, max_tokens, debug)
