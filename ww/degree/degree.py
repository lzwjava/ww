import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests

from ww.llm.openrouter_client import stream_openrouter_api


BASE_HOST = "https://jxjy.gdufs.edu.cn"
LIST_URL = f"{BASE_HOST}/zkfw/zkbtz.htm"
INFO_PREFIX = f"{BASE_HOST}/info/1178/"
PAGE_TPL = f"{BASE_HOST}/zkfw/zkbtz/{{n}}.htm"

ENTRY_RE = re.compile(
    r'href="\.\.(?:/\.\.)?/info/1178/(\d+)\.htm"[^>]*title="([^"]+)"'
    r".*?<span>(\d{4}-\d{2}-\d{2})</span>",
    re.DOTALL,
)


def _fetch_html(url):
    resp = requests.get(url, timeout=20)
    resp.encoding = resp.apparent_encoding or "utf-8"
    if not resp.ok:
        raise Exception(f"HTTP {resp.status_code} fetching {url}")
    return resp.text


def _parse_entries(html):
    out = []
    for m in ENTRY_RE.finditer(html):
        article_id = m.group(1)
        out.append(
            {
                "id": article_id,
                "title": m.group(2),
                "date": m.group(3),
                "url": f"{INFO_PREFIX}{article_id}.htm",
            }
        )
    return out


def _page_url(page):
    if page == 1:
        return LIST_URL
    return PAGE_TPL.format(n=12 - page)


def fetch_entries(pages=1):
    seen = set()
    out = []

    def _fetch_page(p):
        url = _page_url(p)
        return _parse_entries(_fetch_html(url))

    with ThreadPoolExecutor(max_workers=min(pages, 5)) as pool:
        futures = {pool.submit(_fetch_page, p): p for p in range(1, pages + 1)}
        for future in as_completed(futures):
            for entry in future.result():
                if entry["id"] in seen:
                    continue
                seen.add(entry["id"])
                out.append(entry)
    return out


def _format_catalog(entries):
    return "\n".join(f"- [{e['date']}] {e['title']} -> {e['url']}" for e in entries)


def _analyze_practical(entries, model=None):
    catalog = _format_catalog(entries)
    prompt = (
        "You are helping a self-study exam (zikao) student at Guangdong "
        "University of Foreign Studies. The student cares specifically about "
        "**practical exam registration, seat numbers, schedules, "
        "syllabi, and results/scores** — NOT about thesis defense, "
        "bachelor's degree application, graduation "
        "certificate pickup, or general non-practical-exam topics.\n\n"
        "From the article list below, pick only entries that are relevant to "
        "the practical exam or its scores. For each relevant article output a "
        "single Markdown bullet on its own line:\n"
        "- [YYYY-MM-DD] [Title in original Chinese](URL) — one short sentence "
        "in English explaining why it matters.\n\n"
        "Sort newest first. If nothing is relevant, output exactly: "
        "`No practical-exam articles found.`\n\n"
        f"Articles:\n{catalog}\n"
    )
    for chunk in stream_openrouter_api(prompt, model=model):
        print(chunk, end="", flush=True)
    print()


def _analyze_overview(entries, model=None):
    catalog = _format_catalog(entries)
    prompt = (
        "You are helping a self-study exam (zikao) student at Guangdong "
        "University of Foreign Studies understand recent official notices.\n\n"
        "Group the articles below into these categories, in this order:\n"
        "1. Practical exams (registration, seat numbers, scores, syllabi)\n"
        "2. Written exams (registration & schedules)\n"
        "3. Degree & thesis (bachelor's degree & thesis defense)\n"
        "4. Graduation & certificates\n"
        "5. Other\n\n"
        "Under each non-empty category, list articles as Markdown bullets:\n"
        "- [YYYY-MM-DD] [Title](URL)\n\n"
        "Then end with a `### Top picks` section: up to 5 articles the student "
        "should read first, with a one-line reason each.\n\n"
        f"Articles:\n{catalog}\n"
    )
    for chunk in stream_openrouter_api(prompt, model=model):
        print(chunk, end="", flush=True)
    print()


def _print_list(entries):
    for e in entries:
        print(f"- [{e['date']}] {e['title']}")
        print(f"  {e['url']}")


def main():
    parser = argparse.ArgumentParser(
        prog="ww degree",
        description="Scrape GDUFS self-study exam notice page and let an LLM "
        "surface practical-exam-related articles.",
    )
    parser.add_argument(
        "subcmd",
        nargs="?",
        default="overview",
        choices=["overview", "practical", "list"],
        help="overview (default): AI-categorize. practical: filter for practical exams. "
        "list: raw scraped list with no AI.",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="How many list pages to fetch, 1 (newest 20 entries) to 11 (all). "
        "Default 1.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override OpenRouter model (else uses MODEL env var).",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Only show articles from the last N months (default 3). Use 0 to disable.",
    )
    args = parser.parse_args()

    if args.pages < 1 or args.pages > 11:
        print("--pages must be between 1 and 11", file=sys.stderr)
        sys.exit(1)

    entries = fetch_entries(pages=args.pages)

    if args.months > 0:
        cutoff = (datetime.now() - timedelta(days=args.months * 30)).strftime(
            "%Y-%m-%d"
        )
        entries = [e for e in entries if e["date"] >= cutoff]

    print(
        f"Fetched {len(entries)} entries across {args.pages} page(s).\n",
        file=sys.stderr,
    )

    if args.subcmd == "list":
        _print_list(entries)
        return

    if args.subcmd == "practical":
        _analyze_practical(entries, model=args.model)
    else:
        _analyze_overview(entries, model=args.model)
