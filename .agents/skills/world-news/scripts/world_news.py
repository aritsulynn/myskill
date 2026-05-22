#!/usr/bin/env python3
"""
World News — Fetch global headlines via NewsAPI

Usage:
    python world_news.py --api-key KEY
    python world_news.py --topic business --max 15
    python world_news.py --topic world --json

Requires free API key from https://newsapi.org/register
Set as env var NEWSAPI_KEY or pass via --api-key

Dependencies: pip install requests
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Error: 'requests' library required. Run: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

NEWSAPI_BASE = "https://newsapi.org/v2"

PRESTIGE_SOURCES = (
    "reuters,associated-press,bbc-news,cnn,"
    "the-washington-post,the-wall-street-journal,"
    "bloomberg,financial-times,bbc-sport"
)

TOPIC_CONFIG = {
    "all": {
        "endpoint": "top-headlines",
        "params": {"country": "us", "category": "general"},
        "label": "All Topics",
    },
    "business": {
        "endpoint": "top-headlines",
        "params": {"category": "business"},
        "label": "Business & Markets",
    },
    "tech": {
        "endpoint": "top-headlines",
        "params": {"category": "technology"},
        "label": "Technology & Science",
    },
    "politics": {
        "endpoint": "everything",
        "params": {
            "q": "politics OR government OR election OR policy OR diplomacy",
            "language": "en",
            "sortBy": "publishedAt",
        },
        "label": "Politics & Policy",
    },
    "world": {
        "endpoint": "everything",
        "params": {
            "q": "world",
            "language": "en",
            "sortBy": "publishedAt",
        },
        "label": "World Affairs",
    },
}


def _make_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=2, backoff_factor=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session


def fetch_articles(api_key: str, topic: str, max_records: int,
                   prestige: bool = False) -> list[dict]:
    cfg = TOPIC_CONFIG[topic]
    params = dict(cfg["params"])
    params["apiKey"] = api_key
    params["pageSize"] = min(max_records, 100)

    if prestige:
        params["sources"] = PRESTIGE_SOURCES
        params.pop("country", None)
        params.pop("category", None)
        params.pop("q", None)
        params.pop("language", None)
        params.pop("sortBy", None)
        if cfg["endpoint"] == "everything":
            params["sortBy"] = "relevancy"

    session = _make_session()
    url = f"{NEWSAPI_BASE}/{cfg['endpoint']}"
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "ok":
        print(f"API error: {data.get('message', 'unknown')}", file=sys.stderr)
        return []

    articles = []
    for a in data.get("articles", []):
        raw_date = a.get("publishedAt", "")
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d %H:%M UTC")
        except (ValueError, TypeError):
            date_str = raw_date

        source_name = (a.get("source") or {}).get("name", "")

        articles.append({
            "title":   (a.get("title") or "").strip(),
            "url":     a.get("url") or "",
            "snippet": (a.get("description") or "").strip(),
            "date":    date_str,
            "source":  source_name,
        })
    return articles


def main():
    parser = argparse.ArgumentParser(description="Fetch world headlines via NewsAPI")
    parser.add_argument("--api-key",
                        help="NewsAPI key (or set NEWSAPI_KEY env var)")
    parser.add_argument("--max", type=int, default=15,
                        help="Max articles (default: 15, max: 100)")
    parser.add_argument("--topic",
                        choices=list(TOPIC_CONFIG.keys()), default="all",
                        help="News category")
    parser.add_argument("--prestige", action="store_true",
                        help="Prestige sources only (Reuters, BBC, AP, WSJ, etc.)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON (for AI consumption)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("NEWSAPI_KEY")
    if not api_key:
        print("Error: NewsAPI key required.")
        print("  Option 1: Set env var: $env:NEWSAPI_KEY=\"your-key\"")
        print("  Option 2: Pass --api-key KEY")
        print("  Get a free key at: https://newsapi.org/register")
        sys.exit(1)

    article_limit = min(args.max, 100)
    articles = fetch_articles(api_key, args.topic, article_limit, args.prestige)

    if args.json:
        print(json.dumps(articles, indent=2, ensure_ascii=False))
        return

    label = TOPIC_CONFIG[args.topic]["label"]
    quality = " [prestige]" if args.prestige else ""

    if not articles:
        print(f"[{label}{quality}] No articles found.")
        return

    print(f"--- {label}{quality} ---")
    print(f"Found {len(articles)} articles\n")

    for i, a in enumerate(articles, 1):
        print(f"{i}. {a['title']}")
        print(f"   {a['source']} | {a['date']}")
        if a['snippet']:
            print(f"   {a['snippet'][:200]}")
        print()


if __name__ == "__main__":
    main()
