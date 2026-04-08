import argparse
import json
import os
import warnings
from urllib.parse import urlparse, parse_qs, quote_plus

import requests
from bs4 import BeautifulSoup

from .common import (
    HEADERS,
    PROXY,
    run_search_main,
    fetch_results_parallel,
    format_llm_output,
)

warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
warnings.filterwarnings(
    "ignore", message=".*urllib3.*doesn't match a supported version.*"
)


def search_bing(query, num_results=20):
    url = f"https://www.bing.com/search?q={quote_plus(query)}&setmkt=en-US&setlang=en-US&cc=US"
    try:
        session = requests.Session()
        session.cookies.set("SRCHHPGUSR", "SRCHLANG=EN&WLS=2", domain=".bing.com")
        session.cookies.set("_EDGE_S", "mkt=en-us", domain=".bing.com")
        res = session.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"Error searching Bing: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for item in soup.select("li.b_algo"):
        link = item.select_one("h2 a")
        if not link:
            continue
        href = str(link["href"])
        if href.startswith("//"):
            href = "https:" + href
        results.append({"title": link.text.strip(), "url": href})
    return results[:num_results]


def search_ddg(query, num_results=20):
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        res = requests.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"Error searching DDG: {e}")
        return []

    if res.status_code == 202 or "anomaly-modal" in res.text:
        print(
            "DDG blocked the request (CAPTCHA/bot detection). Try another engine with --type bing or --type tavily."
        )
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for item in soup.select(".result__title .result__a"):
        href = str(item["href"])
        if href.startswith("//"):
            href = "https:" + href
        if "duckduckgo.com/l/?uddg=" in href:
            params = parse_qs(urlparse(href).query)
            if "uddg" in params:
                href = params["uddg"][0]
        results.append({"title": item.text.strip(), "url": href})
    return results[:num_results]


def search_startpage(query, num_results=20):
    url = "https://www.startpage.com/sp/search"
    params = {"query": query, "cat": "web", "language": "english"}
    try:
        res = requests.get(
            url, params=params, headers=HEADERS, proxies=PROXY, timeout=10
        )
        res.raise_for_status()
    except Exception as e:
        print(f"Error searching Startpage: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for item in soup.select(".result"):
        link = item.select_one("a.result-link")
        title_tag = item.select_one(".wgl-title")
        if not (link and link.has_attr("href") and title_tag):
            continue
        href = link["href"]
        if isinstance(href, str) and href.startswith("http"):
            results.append({"title": title_tag.get_text(strip=True), "url": href})
    return results[:num_results]


def search_tavily(query, num_results=5):
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY not set.")
        return []

    from tavily import TavilyClient  # type: ignore[import-untyped]

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query, search_depth="advanced", max_results=num_results
        )
        results = []
        for res in response.get("results", []):
            results.append(
                {
                    "title": res.get("title", "No Title"),
                    "url": res.get("url"),
                    "content": res.get("content", "No content available."),
                }
            )
        return results
    except Exception as e:
        print(f"Error searching Tavily: {e}")
        return []


def _deduplicate(results):
    seen = set()
    deduped = []
    for r in results:
        domain = urlparse(r["url"]).netloc
        key = (domain, r["title"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


ENGINES = {
    "bing": search_bing,
    "ddg": search_ddg,
    "startpage": search_startpage,
    "tavily": search_tavily,
}


def web_search(query, num_results=5, provider="ddg"):
    """Callable function for LLM/Copilot tool use.

    Returns structured Markdown (default) or list of dicts.
    """
    if provider == "tavily":
        results = search_tavily(query, num_results=num_results)
        if not results:
            return "No results found."
        return format_llm_output(_deduplicate(results))

    search_fn = ENGINES.get(provider, search_ddg)
    search_results = search_fn(query, num_results=num_results)
    if not search_results:
        return "No results found."

    search_results = _deduplicate(search_results)
    processed = fetch_results_parallel(search_results)
    return format_llm_output(processed)


def main():
    parser = argparse.ArgumentParser(description="Web Search & Extract for LLMs.")
    parser.add_argument("query", help="The search query")
    parser.add_argument(
        "--type",
        choices=["bing", "ddg", "startpage", "tavily"],
        default="ddg",
        help="Search engine (default: ddg)",
    )
    parser.add_argument(
        "-n", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument("-o", "--output", help="Save output to file")
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output as JSON (for LLM tool use)",
    )
    args = parser.parse_args()

    if args.json_output:
        search_fn = ENGINES.get(args.type, search_ddg)
        if args.type == "tavily":
            results = search_fn(args.query, num_results=args.n)
        else:
            search_results = search_fn(args.query, num_results=args.n)
            search_results = _deduplicate(search_results)
            results = fetch_results_parallel(search_results)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if args.type == "tavily":
            results = search_tavily(args.query, num_results=args.n)
            if not results:
                print("No results found.")
                return
            output = format_llm_output(_deduplicate(results))
            from .common import write_output

            write_output(output, args.output)
        else:
            run_search_main(ENGINES[args.type], args)


if __name__ == "__main__":
    main()
