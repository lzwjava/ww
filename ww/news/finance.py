"""Fetch and summarize finance news via OpenRouter web search."""

import sys
import json
import os

import requests


def _call_with_web_search(messages, model=None, max_tokens=4000):
    """Call OpenRouter API with web search plugin enabled."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise Exception("OPENROUTER_API_KEY environment variable is not set")

    if model is None:
        model = os.getenv("MODEL", "google/gemini-2.5-flash")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "plugins": [{"id": "web"}],
    }

    response = requests.post(url, headers=headers, json=data, timeout=60)
    if not response.ok:
        raise Exception(
            f"OpenRouter API error: HTTP {response.status_code}\n"
            f"  Response: {response.text[:500]}"
        )

    body = response.json()
    return body["choices"][0]["message"]["content"]


def main():
    """ww news finance — search and summarize finance news via LLM web search."""
    query = "latest finance news today"
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print("Usage: ww news finance [query]")
        print("")
        print("Search and summarize finance news via LLM web search.")
        print("")
        print("Options:")
        print("  query  Custom search query (default: 'latest finance news today')")
        print("")
        print("Examples:")
        print("  ww news finance")
        print('  ww news finance "fed interest rate"')
        return

    positional = [a for a in args if not a.startswith("-")]
    if positional:
        query = " ".join(positional)

    messages = [
        {
            "role": "user",
            "content": (
                f"Search the web for the latest news about: {query}\n\n"
                "For each of the top 10 results, provide:\n"
                "1. A short English title\n"
                "2. A 2-3 sentence summary\n"
                "3. The source URL\n\n"
                "Return ONLY valid JSON — a JSON array of objects with keys: "
                "title, summary, url. Example:\n"
                '[{"title": "...", "summary": "...", "url": "..."}]\n\n'
                "No markdown, no code fences, no explanation — just the JSON array."
            ),
        }
    ]

    model = os.getenv("MODEL", "google/gemini-2.5-flash")
    print(f"Searching via {model} with web search...")

    try:
        content = _call_with_web_search(messages, model=model)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Strip code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        articles = json.loads(content)
    except json.JSONDecodeError:
        print("Failed to parse LLM response as JSON:")
        print(content)
        sys.exit(1)

    if not articles:
        print("No articles found.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print(f"Finance News — Top {len(articles)} Stories")
    print("=" * 70)
    for i, r in enumerate(articles, 1):
        print(f"\n{i}. {r.get('title', 'Untitled')}")
        print(f"   {r.get('summary', 'No summary.')}")
        print(f"   {r.get('url', '')}")

    print(f"\n--- {len(articles)} articles processed ---")
