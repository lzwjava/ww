"""Fetch and summarize finance news via web search."""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup


def _fetch_text(url, timeout=15):
    """Fetch page and extract readable text."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script/style/nav/footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Trim
        return text[:20000] if text else ""
    except Exception:
        return ""


def _process_item(i, item, total, call_llm):
    """Fetch, extract, and summarize one search result."""
    title = item["title"]
    url = item["url"]

    text = _fetch_text(url)
    if not text or len(text) < 200:
        return None

    prompt = (
        "Summarize the following news article in English in 2-4 sentences. "
        "Focus on the main financial points. Do not include any preamble.\n\n" + text
    )
    summary = call_llm(prompt)
    if not summary:
        return None

    return {"idx": i, "title": title, "summary": summary, "url": url}


def main():
    """ww news finance — search and summarize finance news."""
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Parse args
    count = 10
    threads = 8
    query = "latest finance news today"
    args = sys.argv[1:]

    if "--count" in args:
        idx = args.index("--count")
        if idx + 1 < len(args):
            count = int(args[idx + 1])
    if "--threads" in args:
        idx = args.index("--threads")
        if idx + 1 < len(args):
            threads = int(args[idx + 1])
    # Treat remaining positional args as custom query
    positional = [a for a in args if not a.startswith("-")]
    # Skip 'finance' if it came from the subcmd dispatch
    positional = [a for a in positional if a != "finance"]
    if positional:
        query = " ".join(positional)

    if "--help" in args or "-h" in args:
        print("Usage: ww news finance [query] [--count N] [--threads N]")
        print("")
        print("Search and summarize finance news via web search.")
        print("")
        print("Options:")
        print("  --count N    Number of articles (default: 10)")
        print("  --threads N  Parallel threads (default: 8)")
        print(
            "  query        Custom search query (default: 'latest finance news today')"
        )
        print("")
        print("Examples:")
        print("  ww news finance")
        print('  ww news finance "fed interest rate"')
        print("  ww news finance --count 5")
        return

    # Lazy imports
    from ww.llm.openrouter_client import call_openrouter_api
    from ww.search.search_web import search_bing, _deduplicate

    def call_llm(prompt):
        return call_openrouter_api(prompt, max_tokens=500)

    import warnings

    warnings.filterwarnings(
        "ignore", category=urllib3.exceptions.InsecureRequestWarning
    )

    print(f"Searching: {query}")
    results_raw = search_bing(query, num_results=count + 5)
    results_raw = _deduplicate(results_raw)[:count]
    print(f"Found {len(results_raw)} results.\n")

    if not results_raw:
        print("No results found.")
        sys.exit(1)

    total = len(results_raw)
    print(f"Processing {total} articles with {threads} threads...\n")

    results: list = [None] * total
    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = {
            pool.submit(_process_item, i, item, total, call_llm): i
            for i, item in enumerate(results_raw)
        }
        done = 0
        for future in as_completed(futures):
            done += 1
            i = futures[future]
            item = results_raw[i]
            try:
                result = future.result()
                if result:
                    results[i] = result
                    print(f"[{done}/{total}] ✓ {result['title'][:70]}")
                else:
                    print(f"[{done}/{total}] ✗ {item['title'][:70]}")
            except Exception as e:
                print(f"[{done}/{total}] ✗ {item['title'][:70]} — {e}")

    results = [r for r in results if r is not None]

    print("\n" + "=" * 70)
    print(f"Finance News — Top {len(results)} Stories")
    print("=" * 70)
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title']}")
        print(f"   {r['summary']}")
        print(f"   {r['url']}")

    print(f"\n--- {len(results)} articles processed ---")
