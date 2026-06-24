"""Hacker News agent built with LangGraph.

Reads top HN stories, fetches article content, and produces an AI-curated briefing.
"""

import json
import os
import sys
import textwrap

import requests
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph


# ── HN API helpers ──────────────────────────────────────────────────────────

HN_API = "https://hacker-news.firebaseio.com/v0"


def _fetch_json(url: str, timeout: int = 10):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ── Tools ───────────────────────────────────────────────────────────────────


@tool
def fetch_top_stories(count: int = 10) -> str:
    """Fetch top Hacker News stories with title, score, author, URL, and comment count.

    Args:
        count: Number of stories to fetch (1-30, default 10).
    """
    count = max(1, min(count, 30))
    ids = _fetch_json(f"{HN_API}/topstories.json")
    if not ids:
        return "Error: could not fetch top story IDs"

    stories = []
    for sid in ids[:count]:
        item = _fetch_json(f"{HN_API}/item/{sid}.json")
        if not item:
            continue
        stories.append(
            {
                "id": sid,
                "title": item.get("title", ""),
                "score": item.get("score", 0),
                "by": item.get("by", ""),
                "url": item.get("url", ""),
                "descendants": item.get("descendants", 0),
                "type": item.get("type", ""),
            }
        )
    return json.dumps(stories, indent=2)


@tool
def fetch_story_comments(story_id: int, max_comments: int = 5) -> str:
    """Fetch top comments for a Hacker News story.

    Args:
        story_id: The HN item ID of the story.
        max_comments: Number of top-level comments to fetch (1-20, default 5).
    """
    max_comments = max(1, min(max_comments, 20))
    item = _fetch_json(f"{HN_API}/item/{story_id}.json")
    if not item:
        return f"Error: could not fetch story {story_id}"

    kid_ids = item.get("kid", [])[:max_comments]
    comments = []
    for cid in kid_ids:
        c = _fetch_json(f"{HN_API}/item/{cid}.json")
        if not c:
            continue
        text = c.get("text", "")
        # Strip HTML tags simply
        import re

        text = re.sub(r"<[^>]+>", "", text)
        comments.append(
            {"by": c.get("by", ""), "text": text[:500], "score": c.get("score", 0)}
        )
    return json.dumps(comments, indent=2)


@tool
def fetch_article_content(url: str) -> str:
    """Fetch and extract the text content of an article URL.

    Args:
        url: The article URL to fetch.
    """
    try:
        from bs4 import BeautifulSoup
        from readability import Document

        headers = {"User-Agent": "Mozilla/5.0 (compatible; ww-hackernews/1.0)"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        doc = Document(r.text)
        soup = BeautifulSoup(doc.summary(), "lxml")
        text = soup.get_text(separator="\n", strip=True)
        # Truncate to avoid flooding the context
        return text[:5000] if len(text) > 5000 else text
    except Exception as e:
        return f"Error fetching article: {e}"


TOOLS = [fetch_top_stories, fetch_story_comments, fetch_article_content]

# ── System prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""\
    You are a Hacker News reading agent. Your job is to read today's top HN stories,
    identify the most interesting ones, and produce a concise briefing.

    Workflow:
    1. Use fetch_top_stories to get the current top stories (default 10).
    2. Scan the list and pick 3-5 stories that look most interesting or significant.
       Prioritize: high scores, interesting topics (AI/ML, systems, security, startups),
       and stories with active discussion.
    3. For each interesting story, optionally fetch_article_content to read the linked
       article, or fetch_story_comments to see the discussion.
    4. Produce a final briefing with this format:

    📰 Hacker News Briefing
    ═══════════════════════

    For each story:
    • **Title** (score) — by author
      URL: ...
      [1-2 sentence summary of the article or key discussion points]

    End with a quick "Also notable:" list of remaining stories (title + score only).

    Keep the briefing concise and opinionated — highlight what's genuinely interesting.
""")


# ── LangGraph agent ─────────────────────────────────────────────────────────


def _build_graph():
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),  # type: ignore[arg-type]
        model=os.environ.get("MODEL", "deepseek/deepseek-v3.2"),
        temperature=0.3,
    )
    llm_with_tools = llm.bind_tools(TOOLS)

    tool_map = {t.name: t for t in TOOLS}

    def agent_node(state: MessagesState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def tool_node(state: MessagesState):
        last = state["messages"][-1]
        results = []
        for tc in last.tool_calls:
            fn = tool_map.get(tc["name"])
            if fn:
                output = fn.invoke(tc["args"])
            else:
                output = f"Unknown tool: {tc['name']}"
            results.append(ToolMessage(content=str(output), tool_call_id=tc["id"]))
        return {"messages": results}

    def should_continue(state: MessagesState):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# ── CLI entry point ─────────────────────────────────────────────────────────


def main():
    count = 10
    topic = ""

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--count" and i + 1 < len(args):
            count = int(args[i + 1])
            i += 2
        elif args[i] in ("--help", "-h"):
            print("Usage: ww hackernews [--count N] [topic]")
            print()
            print("Read Hacker News with an AI agent powered by LangGraph.")
            print()
            print("Options:")
            print("  --count N   Number of stories to fetch (default: 10, max: 30)")
            print("  topic       Optional focus area (e.g. 'AI', 'Rust', 'startups')")
            return
        elif not args[i].startswith("-"):
            topic = args[i]
            i += 1
        else:
            i += 1

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set in environment")
        sys.exit(1)

    prompt = f"Fetch the top {count} HN stories and give me a briefing."
    if topic:
        prompt += f" Focus especially on stories about {topic}."

    graph = _build_graph()

    print(f"Fetching top {count} Hacker News stories...")
    print()

    result = graph.invoke(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        }
    )

    # Print the final AI message
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            print(msg.content)
            break
