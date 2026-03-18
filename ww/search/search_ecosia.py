import warnings

warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
warnings.filterwarnings(
    "ignore", message=".*urllib3.*doesn't match a supported version.*"
)

import argparse

import requests
from bs4 import BeautifulSoup

from .common import HEADERS, PROXY, run_search_main


def search_ecosia(query, num_results=10):
    url = f"https://www.ecosia.org/search?q={query}"
    try:
        res = requests.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"Ecosia search failed: {e}")
        raise

    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for result in soup.select(".result"):
        title_elem = result.select_one(".result-title")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        href = title_elem.get("href")
        if href and isinstance(href, str) and href.startswith("http"):
            if not any(r["url"] == href for r in results):
                results.append({"title": title, "url": href})
        if len(results) >= num_results:
            break

    if not results:
        print("No Ecosia results found in HTML.")
    return results


def main():
    parser = argparse.ArgumentParser(description="Ecosia Search & Extract for LLMs.")
    parser.add_argument("query", help="The search query")
    parser.add_argument(
        "-n", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument("-o", "--output", help="Save output to file")
    run_search_main(search_ecosia, parser.parse_args())
