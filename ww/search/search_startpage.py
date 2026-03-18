import argparse

import requests
from bs4 import BeautifulSoup

from .common import HEADERS, PROXY, run_search_main


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


def main():
    parser = argparse.ArgumentParser(description="Startpage Search & Extract for LLMs.")
    parser.add_argument("query", help="The search query")
    parser.add_argument(
        "-n", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument("-o", "--output", help="Save output to file")
    run_search_main(search_startpage, parser.parse_args())
