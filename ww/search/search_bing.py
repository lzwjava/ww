import argparse

import requests
from bs4 import BeautifulSoup

from .common import HEADERS, PROXY, run_search_main


def search_bing(query, num_results=20):
    url = f"https://www.bing.com/search?q={query}&setmkt=en-US&setlang=en-US&cc=US"
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


def main():
    parser = argparse.ArgumentParser(description="Bing Search & Extract for LLMs.")
    parser.add_argument("query", help="The search query")
    parser.add_argument(
        "-n", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument("-o", "--output", help="Save output to file")
    run_search_main(search_bing, parser.parse_args())
