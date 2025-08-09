"""
news.py — unified news service

Combines:
- news_services.py (GNews search / listing)
- news_crawler.py (fetch + extract article text)
- summary_services.py (generate compact summaries)
- sentiment_store.py (sentiment + optional caching)

Design goals:
- Single facade for all news needs used by the dashboard
- Pluggable persistence: in‑memory by default; optional SQLite via backend/api/db/database.py if present
- Headline impact scoring + sentiment in one place

Public functions:
- search_news(query: str | None = None, symbol: str | None = None, *, max_items: int = 20) -> list[dict]
- fetch_and_cache_article_text(url: str) -> dict
- sentiment(text: str) -> dict
- score_headline_impact(item: dict) -> float
- summarize(text: str, *, max_sentences: int = 3) -> str

Returned news item shape (normalized minimal contract):
{
  "title": str,
  "source": str | None,
  "published_at": int,          # epoch seconds
  "url": str,
  "description": str | None,
  "tickers": list[str] | None,
}
"""
from __future__ import annotations

import os
import re
import time
import html
import json
import math
import typing as t
from dataclasses import dataclass

import requests

try:
    # Optional: wire to your SQLite helper if it exposes a simple interface
    # We'll detect and use functions if available without importing-heavy coupling.
    from backend.api.db import database as db  # type: ignore
except Exception:  # pragma: no cover - optional
    db = None  # fallback to in-memory

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY") or os.getenv("GNEWS_KEY")
GNEWS_BASE = "https://gnews.io/api/v4/search"

# ---------------------------
# In-memory caches (lightweight)
# ---------------------------
@dataclass
class _CacheItem:
    data: t.Any
    ts: float

_CACHE_TTL_ARTICLE = int(os.getenv("NEWS_ARTICLE_CACHE_TTL", "86400"))  # 24h
_CACHE_TTL_SEARCH = int(os.getenv("NEWS_SEARCH_CACHE_TTL", "900"))      # 15m

_search_cache: dict[tuple, _CacheItem] = {}
_article_cache: dict[str, _CacheItem] = {}


def _cache_get(buf: dict, key: t.Hashable, ttl: int):
    it = buf.get(key)
    if not it:
        return None
    if time.time() - it.ts > ttl:
        buf.pop(key, None)
        return None
    return it.data


def _cache_set(buf: dict, key: t.Hashable, data: t.Any):
    buf[key] = _CacheItem(data=data, ts=time.time())


# ---------------------------
# GNews Search
# ---------------------------

def search_news(query: str | None = None, symbol: str | None = None, *, max_items: int = 20) -> list[dict]:
    """Search news via GNews for a query or symbol, normalized to a compact shape.

    If both query and symbol are None, raises ValueError.
    """
    if not GNEWS_API_KEY:
        raise RuntimeError("Missing GNEWS_API_KEY")

    if not query and not symbol:
        raise ValueError("Provide query or symbol")

    q = query or symbol
    key = (q, max_items)
    cached = _cache_get(_search_cache, key, _CACHE_TTL_SEARCH)
    if cached:
        return cached

    params = {
        "q": q,
        "token": GNEWS_API_KEY,
        "lang": "en",
        "max": min(max_items, 100),
    }

    r = requests.get(GNEWS_BASE, params=params, timeout=20)
    r.raise_for_status()
    payload = r.json()

    items: list[dict] = []
    for art in payload.get("articles", [])[:max_items]:
        items.append({
            "title": art.get("title"),
            "source": (art.get("source") or {}).get("name"),
            "published_at": _iso8601_to_epoch(art.get("publishedAt")),
            "url": art.get("url"),
            "description": art.get("description"),
            "tickers": _extract_tickers(art.get("title") or "") or None,
        })

    _cache_set(_search_cache, key, items)
    return items


# ---------------------------
# Article fetch + text extract
# ---------------------------

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def fetch_and_cache_article_text(url: str) -> dict:
    """Fetch an article and return { 'url', 'title', 'text' }.

    Uses local cache; attempts very light extraction heuristics to avoid heavy deps.
    If the site blocks scraping or returns non-HTML, returns best-effort content.
    """
    if not url:
        raise ValueError("url required")

    # First check in-memory cache
    cached = _cache_get(_article_cache, url, _CACHE_TTL_ARTICLE)
    if cached:
        return cached

    headers = {"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        html_text = r.text
    except Exception as e:  # pragma: no cover - network errors
        data = {"url": url, "title": None, "text": f"<fetch-error: {e}>"}
        _cache_set(_article_cache, url, data)
        return data

    title = _extract_title(html_text)
    body = _extract_readable_text(html_text)

    data = {"url": url, "title": title, "text": body}

    # Optional: persist to SQLite if helper is available
    try:
        if db and hasattr(db, "save_article_text"):
            db.save_article_text(url=url, title=title or "", text=body or "", fetched_at=int(time.time()))
    except Exception:
        # Non-fatal
        pass

    _cache_set(_article_cache, url, data)
    return data


# ---------------------------
# Sentiment + headline impact
# ---------------------------
_NEG_WORDS = {
    "lawsuit", "charges", "fraud", "decline", "selloff", "sell-off", "probe", "investigation",
    "misses", "downgrade", "cut guidance", "regulatory", "ban", "penalty", "fine", "layoffs", "recall",
}
_POS_WORDS = {
    "beats", "record", "upgrade", "innovation", "launch", "surge", "growth", "profit", "guidance raise",
    "acquisition", "partnership", "contract", "approval", "milestone", "breakthrough",
}


def sentiment(text: str) -> dict:
    """Ultra-light sentiment heuristic (free, no external models).

    Returns {score: -1..1, pos: int, neg: int, words: int}
    """
    if not text:
        return {"score": 0.0, "pos": 0, "neg": 0, "words": 0}

    tokens = re.findall(r"[A-Za-z']+", text.lower())
    words = len(tokens)
    pos = sum(1 for t in tokens if t in _POS_WORDS)
    neg = sum(1 for t in tokens if t in _NEG_WORDS)
    # Simple normalized score
    score = 0.0
    if words:
        score = (pos - neg) / math.sqrt(words)
        score = max(-1.0, min(1.0, score))
    return {"score": round(score, 4), "pos": pos, "neg": neg, "words": words}


def score_headline_impact(item: dict) -> float:
    """Headline impact score blends recency, source presence, and sentiment of title/desc.

    0..1 where higher is more impactful.
    """
    title = (item or {}).get("title") or ""
    desc = (item or {}).get("description") or ""
    ts = (item or {}).get("published_at") or 0

    # Sentiment from title + description
    s = sentiment(f"{title}. {desc}")

    # Recency decay: within 24h ≈ 1.0, then decays
    age = max(0, time.time() - ts)
    # 24h half-life
    decay = 0.5 ** (age / 86400)

    # Source weight if present
    src_weight = 1.0 if item.get("source") else 0.9

    # Combine (bounded)
    raw = (0.6 * ((s["score"] + 1) / 2)) + (0.3 * decay) + (0.1 * src_weight)
    return max(0.0, min(1.0, raw))


# ---------------------------
# Summarization (extractive)
# ---------------------------

def summarize(text: str, *, max_sentences: int = 3) -> str:
    """Very small extractive summarizer: pick top-N sentences by keyword hit.
    Keeps it dependency-free; you can swap with an LLM later.
    """
    if not text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) <= max_sentences:
        return text.strip()

    # Keyword scoring
    tokens = re.findall(r"[A-Za-z']+", text.lower())
    freq: dict[str, int] = {}
    for tkn in tokens:
        freq[tkn] = freq.get(tkn, 0) + 1

    def score_sentence(s: str) -> float:
        toks = re.findall(r"[A-Za-z']+", s.lower())
        return sum(freq.get(t, 0) for t in toks) / (len(toks) + 1)

    ranked = sorted(((score_sentence(s), i, s) for i, s in enumerate(sentences)), reverse=True)
    picked = sorted(ranked[:max_sentences], key=lambda x: x[1])
    return " ".join(s for _, __, s in picked).strip()


# ---------------------------
# Helpers
# ---------------------------

def _iso8601_to_epoch(s: str | None) -> int:
    if not s:
        return 0
    # 2024-01-01T12:34:56Z
    from datetime import datetime, timezone

    try:
        if s.endswith("Z"):
            dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        else:
            # Best effort; ignore timezone offset specifics
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return 0


def _extract_title(html_text: str) -> str | None:
    # Try <title> first
    m = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if m:
        return html.unescape(m.group(1)).strip()
    # Then og:title
    m = re.search(r"property=[\"']og:title[\"'][^>]*content=[\"'](.*?)[\"']", html_text, re.IGNORECASE)
    if m:
        return html.unescape(m.group(1)).strip()
    return None


def _extract_readable_text(html_text: str) -> str:
    # Remove scripts/styles
    html_no_code = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html_text, flags=re.IGNORECASE)
    # Strip tags
    text = re.sub(r"<[^>]+>", " ", html_no_code)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return html.unescape(text).strip()


def _extract_tickers(text: str) -> list[str]:
    # Very light $TSLA / (NASDAQ:AAPL) patterns
    tickers: set[str] = set()
    for m in re.finditer(r"\$([A-Z]{1,5})\b", text):
        tickers.add(m.group(1))
    for m in re.finditer(r"\((?:NASDAQ|NYSE|AMEX):([A-Z]{1,5})\)", text):
        tickers.add(m.group(1))
    return sorted(tickers)