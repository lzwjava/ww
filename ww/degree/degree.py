import argparse
import re
import sys

import requests

from ww.llm.openrouter_client import call_openrouter_api


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
    for p in range(1, pages + 1):
        url = _page_url(p)
        for entry in _parse_entries(_fetch_html(url)):
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
        "You are helping a self-study (自学考试 / zikao) student at Guangdong "
        "University of Foreign Studies. The student cares specifically about "
        "**practical exam (实践考核) registration, seat numbers, schedules, "
        "syllabi, and results/scores (成绩)** — NOT about thesis defense "
        "(论文答辩), bachelor's degree application (学士学位申请), graduation "
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
    return call_openrouter_api(prompt, model=model)


def _analyze_overview(entries, model=None):
    catalog = _format_catalog(entries)
    prompt = (
        "You are helping a self-study (自学考试 / zikao) student at Guangdong "
        "University of Foreign Studies understand recent official notices.\n\n"
        "Group the articles below into these categories, in this order:\n"
        "1. 实践考核 (Practical exam: registration, seat numbers, scores, syllabi)\n"
        "2. 笔试 / 报考 (Written-exam registration & schedules)\n"
        "3. 学位 / 论文 (Bachelor's degree & thesis)\n"
        "4. 毕业 / 证书 (Graduation & certificates)\n"
        "5. 其他 (Other)\n\n"
        "Under each non-empty category, list articles as Markdown bullets:\n"
        "- [YYYY-MM-DD] [Title](URL)\n\n"
        "Then end with a `### Top picks` section: up to 5 articles the student "
        "should read first, with a one-line reason each.\n\n"
        f"Articles:\n{catalog}\n"
    )
    return call_openrouter_api(prompt, model=model)


def _print_list(entries):
    for e in entries:
        print(f"- [{e['date']}] {e['title']}")
        print(f"  {e['url']}")


def main():
    parser = argparse.ArgumentParser(
        prog="ww degree",
        description="Scrape GDUFS self-study (自考) notice page and let an LLM "
        "surface practical-exam-related articles.",
    )
    parser.add_argument(
        "subcmd",
        nargs="?",
        default="overview",
        choices=["overview", "practical", "list"],
        help="overview (default): AI-categorize. practical: filter for 实践考核. "
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
    args = parser.parse_args()

    if args.pages < 1 or args.pages > 11:
        print("--pages must be between 1 and 11", file=sys.stderr)
        sys.exit(1)

    entries = fetch_entries(pages=args.pages)
    print(
        f"Fetched {len(entries)} entries across {args.pages} page(s).\n",
        file=sys.stderr,
    )

    if args.subcmd == "list":
        _print_list(entries)
        return

    if args.subcmd == "practical":
        result = _analyze_practical(entries, model=args.model)
    else:
        result = _analyze_overview(entries, model=args.model)
    print(result)
