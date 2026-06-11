"""Fetch, summarize, and translate NYTimes Chinese articles."""

import sys
import requests
from bs4 import BeautifulSoup


def _fetch_html(url, timeout=30):
    """Fetch HTML content from a URL, skipping SSL verification."""
    try:
        response = requests.get(url, verify=False, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"  [skip] {url} — {e}")
        return None


def _extract_links(html):
    """Extract article links from the cn.nytimes.com main page."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        url = a["href"]
        text = a.get_text(strip=True)
        if (
            url.startswith("https://cn.nytimes.com/")
            and "/dual/" not in url
            and text
            and len(text) > 4
            and url not in seen
        ):
            seen.add(url)
            links.append({"url": url, "text": text})
    return links


def _dual_url(url):
    """Convert an article URL to its dual (bilingual) version."""
    url = url.rstrip("/")
    return url + "/dual/"


def _extract_article(html):
    """Extract title and article text from a dual article page."""
    soup = BeautifulSoup(html, "html.parser")

    # Try multiple selectors for title
    title = ""
    for sel in [
        ".article-area .article-content .article-header header h1",
        "h1",
        ".article-header h1",
        "title",
    ]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break

    # Extract body text
    article_area = soup.find("div", class_="article-area")
    if article_area:
        text = article_area.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Trim to reasonable size
    if len(text) > 30000:
        text = text[:30000]

    return title, text


def _summarize(text, call_llm):
    """Summarize article text in English using the LLM."""
    prompt = (
        "Summarize the following article in English in 2-4 sentences. "
        "Focus on the main points. Do not include any preamble.\n\n" + text
    )
    return call_llm(prompt)


def _translate_title(title, call_llm):
    """Translate a Chinese title to English using the LLM."""
    prompt = (
        "Translate the following Chinese title to English. "
        "Provide only the translated title, nothing else.\n\n" + title
    )
    return call_llm(prompt)


def main():
    """ww news nytimes — fetch and summarize NYTimes Chinese articles."""
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Parse args: --count N (default 10)
    count = 10
    args = sys.argv[1:]
    if "--count" in args:
        idx = args.index("--count")
        if idx + 1 < len(args):
            count = int(args[idx + 1])
    if "--help" in args or "-h" in args:
        print("Usage: ww news nytimes [--count N]")
        print("")
        print("Fetch top stories from NYTimes Chinese edition,")
        print("summarize and translate titles to English.")
        print("")
        print("Options:")
        print("  --count N   Number of articles to process (default: 10)")
        return

    # Lazy import to avoid circular deps and speed up dispatch
    from ww.llm.openrouter_client import call_openrouter_api

    def call_llm(prompt):
        return call_openrouter_api(prompt, max_tokens=500)

    # Suppress only InsecureRequestWarning
    import warnings

    warnings.filterwarnings(
        "ignore", category=urllib3.exceptions.InsecureRequestWarning
    )

    print("Fetching NYTimes Chinese edition...")
    html = _fetch_html("https://m.cn.nytimes.com")
    if not html:
        print("Failed to fetch main page.")
        sys.exit(1)

    links = _extract_links(html)
    print(f"Found {len(links)} article links.\n")

    if not links:
        print("No articles found.")
        sys.exit(1)

    # Limit to requested count
    links = links[:count]

    results = []
    for i, link in enumerate(links):
        url = link["url"]
        dual = _dual_url(url)
        print(f"[{i + 1}/{len(links)}] {link['text'][:60]}")

        article_html = _fetch_html(dual)
        if not article_html:
            continue

        title, text = _extract_article(article_html)
        if not text or len(text) < 100:
            print("  [skip] article too short")
            continue

        # Translate title
        en_title = _translate_title(title, call_llm)
        if not en_title:
            en_title = title  # fallback to original

        # Summarize
        summary = _summarize(text, call_llm)
        if not summary:
            print("  [skip] summarization failed")
            continue

        results.append(
            {"title_zh": title, "title_en": en_title, "summary": summary, "url": url}
        )
        print(f"  ✓ {en_title}\n")

    # Output final results
    print("=" * 70)
    print(f"NYTimes Chinese — Top {len(results)} Stories (English Summary)")
    print("=" * 70)
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title_en']}")
        print(f"   {r['title_zh']}")
        print(f"   {r['summary']}")
        print(f"   {r['url']}")

    print(f"\n--- {len(results)} articles processed ---")
