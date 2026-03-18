import argparse
import warnings
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .common import HEADERS, PROXY, run_search_main

warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
warnings.filterwarnings(
    "ignore", message=".*urllib3.*doesn't match a supported version.*"
)


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


ENGINES = {
    "bing": search_bing,
    "ddg": search_ddg,
    "startpage": search_startpage,
}


def main():
    parser = argparse.ArgumentParser(description="Web Search & Extract for LLMs.")
    parser.add_argument("query", help="The search query")
    parser.add_argument(
        "--type",
        choices=["bing", "ddg", "startpage"],
        default="ddg",
        help="Search engine (default: ddg)",
    )
    parser.add_argument(
        "-n", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument("-o", "--output", help="Save output to file")
    args = parser.parse_args()
    run_search_main(ENGINES[args.type], args)
