import os
import sys
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
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

SITE_SELECTORS = {
    "zhihu.com": ".QuestionHeader-title, .RichContent-inner, .Post-RichTextContainer",
    "zhidao.baidu.com": ".wgt-best-mask, .wgt-best-content, .wgt-answers, .line.content, .best-text",
    "wikipedia.org": "#firstHeading, .mw-parser-output p",
    "github.com": ".repository-content, article.markdown-body",
}


def _site_targets(soup, url):
    selector = next(
        (sel for domain, sel in SITE_SELECTORS.items() if domain in url), None
    )
    if selector:
        return soup.select(selector)
    return None


def _fallback_targets(soup, html):
    try:
        doc = Document(html)
        summary_html = doc.summary()
        if summary_html:
            text = BeautifulSoup(summary_html, "html.parser").get_text(
                separator=" ", strip=True
            )
            if len(text) > 100:
                return text
    except Exception as e:
        print(f"Readability failed: {e}")
    targets = soup.select("article, main, .main-content, #content, .content")
    return targets if targets else [soup.find("body")]


def extract_text_from_url(url):
    try:
        res = requests.Session().get(url, headers=HEADERS, proxies=PROXY, timeout=15)
        res.encoding = res.apparent_encoding

        if res.status_code != 200:
            return f"Error: Received status code {res.status_code}"

        soup = BeautifulSoup(res.text, "html.parser")
        for el in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            el.decompose()

        targets = _site_targets(soup, url)
        if targets is None:
            fallback = _fallback_targets(soup, res.text)
            if isinstance(fallback, str):
                return fallback
            targets = fallback

        blocks = [t.get_text(separator=" ", strip=True) for t in targets if t]
        blocks = [b for b in blocks if b]
        return (
            "\n\n".join(blocks) if blocks else soup.get_text(separator=" ", strip=True)
        )
    except Exception as e:
        return f"Error fetching {url}: {e}"


def format_llm_output(results):
    blocks = [
        f"### Source {i + 1}\n"
        f"**Title:** {res['title']}\n"
        f"**URL:** {res['url']}\n\n"
        f"**Content:**\n{res.get('content', 'No content extracted.')}\n"
        f"{'-' * 40}"
        for i, res in enumerate(results)
    ]
    return "\n\n".join(blocks)


def copy_to_clipboard(text):
    try:
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(text.encode("utf-8"))
        return True
    except Exception:
        return False


def fetch_results_parallel(search_results):
    processed = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_info = {
            executor.submit(extract_text_from_url, r["url"]): r for r in search_results
        }
        for future in as_completed(future_to_info):
            info = future_to_info[future]
            try:
                processed.append({**info, "content": future.result()})
                print(f"Done: {info['url']}")
            except Exception as e:
                print(f"Failed: {info['url']} ({e})")
    url_to_order = {res["url"]: i for i, res in enumerate(search_results)}
    processed.sort(key=lambda x: url_to_order.get(x["url"], 999))
    return processed


def write_output(content, output_path):
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\nSaved to: {output_path}")
    else:
        print("\n--- LLM Structured Output ---\n")
        print(content)
    if copy_to_clipboard(content):
        print("\nCopied to clipboard.")


def run_search_main(search_fn, args):
    search_results = search_fn(args.query, num_results=args.n)
    if not search_results:
        print("No results found.")
        sys.exit(0)
    print(f"Searching for: {args.query}")
    print(f"Fetching {len(search_results)} results in parallel...")
    processed = fetch_results_parallel(search_results)
    write_output(format_llm_output(processed), args.output)


# --- ack utilities ---


def check_ack() -> str:
    path = shutil.which("ack")
    if not path:
        print("Error: ack is not installed.")
        print("Please install it first:")
        print("  macOS: brew install ack")
        print("  Ubuntu/Debian: sudo apt-get install ack")
        print("  Windows: scoop install ack")
        sys.exit(1)
    return path


def _format_ack_line(line):
    if line.startswith("--"):
        print()
        return
    if ":" in line:
        parts = line.split(":", 1)
        file_part, content = parts[0], parts[1]
        if "-" in file_part and file_part.split("-")[-1].isdigit():
            segs = file_part.split("-")
            print(f"{'-'.join(segs[:-1])}:{segs[-1]}:{content}")
        else:
            print(line)
    elif "-" in line and not line.startswith("-"):
        parts = line.split("-")
        if len(parts) >= 3 and parts[-2].isdigit():
            print(f"{'-'.join(parts[:-2])}:{parts[-2]}:{parts[-1]}")
        else:
            print(line)
    else:
        print(line)


def print_ack_output(stdout):
    if not stdout:
        print("No matches found")
        return
    for line in stdout.strip().split("\n"):
        print()
        _format_ack_line(line)
    print()
