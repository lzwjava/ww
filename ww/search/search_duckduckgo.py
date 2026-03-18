import warnings

warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
warnings.filterwarnings(
    "ignore", message=".*urllib3.*doesn't match a supported version.*"
)

import argparse
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .common import HEADERS, PROXY, run_search_main


def search_ddg(query, num_results=20):
    url = f"https://html.duckduckgo.com/html/?q={query}"
    try:
        res = requests.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"Error searching DDG: {e}")
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


def main():
    parser = argparse.ArgumentParser(
        description="DuckDuckGo Search & Extract for LLMs."
    )
    parser.add_argument("query", help="The search query")
    parser.add_argument(
        "-n", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument("-o", "--output", help="Save output to file")
    run_search_main(search_ddg, parser.parse_args())
