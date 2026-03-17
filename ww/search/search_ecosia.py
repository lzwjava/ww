import warnings

warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
warnings.filterwarnings(
    "ignore", message=".*urllib3.*doesn't match a supported version.*"
)

import requests
import sys
import argparse
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from readability import Document

DEFAULT_PROXY = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
PROXY = {
    "http": os.environ.get("HTTP_PROXY", DEFAULT_PROXY["http"]),
    "https": os.environ.get("HTTPS_PROXY", DEFAULT_PROXY["https"]),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def search_ecosia(query, num_results=10):
    url = f"https://www.ecosia.org/search?q={query}"
    try:
        response = requests.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for result in soup.select(".result"):
            title_elem = result.select_one(".result-title")
            link_elem = result.select_one(".result-title")
            if not title_elem or not link_elem:
                continue
            title = title_elem.get_text(strip=True)
            href = link_elem.get("href")
            if href and title and href.startswith("http"):
                if not any(res["url"] == href for res in results):
                    results.append({"title": title, "url": href})
            if len(results) >= num_results:
                break
        if results:
            return results
        print("No Ecosia results found in HTML.")
        return []
    except Exception as e:
        print(f"Ecosia search failed: {e}")
        raise


def extract_text_from_url(url):
    try:
        session = requests.Session()
        res = session.get(url, headers=HEADERS, proxies=PROXY, timeout=15)
        res.encoding = res.apparent_encoding

        if res.status_code != 200:
            return f"Error: Received status code {res.status_code}"

        soup = BeautifulSoup(res.text, "html.parser")
        for element in soup(
            ["script", "style", "header", "footer", "nav", "aside", "form"]
        ):
            element.decompose()

        content_blocks = []
        if "zhihu.com" in url:
            targets = soup.select(
                ".QuestionHeader-title, .RichContent-inner, .Post-RichTextContainer"
            )
        elif "zhidao.baidu.com" in url:
            targets = soup.select(
                ".wgt-best-mask, .wgt-best-content, .wgt-answers, .line.content, .best-text"
            )
        elif "wikipedia.org" in url:
            targets = soup.select("#firstHeading, .mw-parser-output p")
        elif "github.com" in url:
            targets = soup.select(".repository-content, article.markdown-body")
        else:
            try:
                doc = Document(res.text)
                summary_html = doc.summary()
                if summary_html:
                    text = BeautifulSoup(summary_html, "html.parser").get_text(
                        separator=" ", strip=True
                    )
                    if len(text) > 100:
                        return text
            except Exception as e:
                print(f"Readability failed for {url}: {e}")
            targets = soup.select("article, main, .main-content, #content, .content")
            if not targets:
                targets = [soup.find("body")]

        for t in targets:
            if t:
                text = t.get_text(separator=" ", strip=True)
                if text:
                    content_blocks.append(text)

        return (
            "\n\n".join(content_blocks)
            if content_blocks
            else soup.get_text(separator=" ", strip=True)
        )
    except Exception as e:
        return f"Error fetching {url}: {e}"


def format_llm_output(results):
    blocks = []
    for i, res in enumerate(results):
        blocks.append(
            f"### Source {i + 1}\n"
            f"**Title:** {res['title']}\n"
            f"**URL:** {res['url']}\n\n"
            f"**Content:**\n{res.get('content', 'No content extracted.')}\n"
            f"{'-' * 40}"
        )
    return "\n\n".join(blocks)


def copy_to_clipboard(text):
    try:
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(text.encode("utf-8"))
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Ecosia Search & Extract for LLMs.")
    parser.add_argument("query", help="The search query")
    parser.add_argument(
        "-n", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument("-o", "--output", help="Save output to file")
    args = parser.parse_args()

    print(f"Searching Ecosia for: {args.query}")
    search_results = search_ecosia(args.query, num_results=args.n)
    if not search_results:
        print("No results found.")
        sys.exit(0)

    print(f"Fetching {len(search_results)} results in parallel...")

    processed_results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_info = {
            executor.submit(extract_text_from_url, r["url"]): r for r in search_results
        }
        for future in as_completed(future_to_info):
            info = future_to_info[future]
            try:
                processed_results.append({**info, "content": future.result()})
                print(f"Done: {info['url']}")
            except Exception as e:
                print(f"Failed: {info['url']} ({e})")

    url_to_order = {res["url"]: i for i, res in enumerate(search_results)}
    processed_results.sort(key=lambda x: url_to_order.get(x["url"], 999))
    final_content = format_llm_output(processed_results)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(final_content)
        print(f"\nSaved to: {args.output}")
    else:
        print("\n--- LLM Structured Output ---\n")
        print(final_content)

    if copy_to_clipboard(final_content):
        print("\nCopied to clipboard.")
