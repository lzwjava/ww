import json
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


def _resolve_model(model):
    if model is None:
        model = os.getenv("MODEL")
    if not model:
        raise Exception("MODEL not specified and MODEL env var is not set")
    return model


def _extract_delta_text(payload):
    try:
        chunk = json.loads(payload)
    except json.JSONDecodeError:
        return None
    choices = chunk.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    return delta.get("content")


def stream_openrouter_api_with_messages(
    messages, model=None, max_tokens=None, debug=False
):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise Exception("OPENROUTER_API_KEY environment variable is not set")

    model = _resolve_model(model)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    data = {"model": model, "messages": messages, "stream": True}
    if max_tokens is not None:
        data["max_tokens"] = max_tokens

    if debug:
        print(f"Request URL: {url}")
        print(f"Request Data: {data}")

    response = requests.post(url, headers=headers, json=data, stream=True)
    if not response.ok:
        raise Exception(f"Error: {response.status_code} - {response.text}")

    for raw in response.iter_lines():
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace")
        if not line.startswith("data: "):
            continue
        payload = line[len("data: ") :].strip()
        if payload == "[DONE]":
            break
        text = _extract_delta_text(payload)
        if text:
            yield text


def stream_openrouter_api(prompt, model=None, max_tokens=None, debug=False):
    messages = [{"role": "user", "content": prompt}]
    yield from stream_openrouter_api_with_messages(messages, model, max_tokens, debug)
