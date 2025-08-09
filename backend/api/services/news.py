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
- summarize_text(text: str, max_sentences: int = 5) -> str
- impact_score(item: dict) -> float
- sentiment(text: str) -> dict
"""
from __future__ import annotations

import os
import re
import time
import html
import json
import math
import typing as t
import requests
from urllib.parse import urlparse

# Configuration (env)
GNEWS_API_KEY = os.getenv("GNEWS_KEY") or os.getenv("GNEWS_API_KEY")
GNEWS_BASE = "https://gnews.io/api/v4/search"

# Local in‑memory caches
_search_cache: dict[tuple[str, int], tuple[float, list[dict]]] = {}
_article_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL_SEARCH = 60  # seconds
_CACHE_TTL_ARTICLE = 3600  # seconds

# --- Sentiment label/color mapping for UI ---
def _label_color_from_score(score: float | None):
    if score is None:
        return ("unknown", "grey")
    if score >= 0.2:
        return ("positive", "green")
    if score <= -0.2:
        return ("negative", "red")
    return ("neutral", "yellow")


# ---------------------------
# Helpers: cache
# ---------------------------

def _cache_get(store: dict, key, ttl: int):
    item = store.get(key)
    if not item:
        return None
    ts, value = item
    if time.time() - ts > ttl:
        return None
    return value

def _cache_set(store: dict, key, value):
    store[key] = (time.time(), value)


# ---------------------------
# Helpers: parse/convert
# ---------------------------

def _iso8601_to_epoch(s: str | None) -> int:
    if not s:
        return 0
    # gnews example: "2025-08-08T19:35:00Z"
    try:
        import datetime as dt
        return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())
    except Exception:
        return 0


# ---------------------------
# News search (GNews)
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
        base = {
            "title": art.get("title"),
            "source": (art.get("source") or {}).get("name"),
            "published_at": _iso8601_to_epoch(art.get("publishedAt")),
            "url": art.get("url"),
            "description": art.get("description"),
            "tickers": _extract_tickers(art.get("title") or "") or None,
        }
        # Enrich with sentiment + impact (server-side)
        text_for_sent = f"{base['title'] or ''}. {base['description'] or ''}"
        s = sentiment(text_for_sent)
        label, color = _label_color_from_score(s.get("score"))
        base["sentiment"] = {
            "score": float(s.get("score", 0.0)),
            "label": label,
            "color": color,
        }
        # impact_score -> 0..1 (higher = more impactful)
        imp = impact_score(base)
        base["impact"] = ("high" if imp >= 0.66 else "medium" if imp >= 0.4 else "low")
        items.append(base)

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
    If the site blocks scraping or returns non-HTML, the text may be blank.
    """
    cached = _cache_get(_article_cache, url, _CACHE_TTL_ARTICLE)
    if cached:
        return cached

    try:
        headers = {"User-Agent": _USER_AGENT, "Accept": "text/html,*/*"}
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        html_text = resp.text
    except Exception:
        html_text = ""

    title = _extract_title(html_text) or _domain_from_url(url)
    text = _extract_main_text(html_text)

    result = {"url": url, "title": title, "text": text}
    _cache_set(_article_cache, url, result)
    return result


def _domain_from_url(u: str) -> str:
    try:
        return urlparse(u).netloc
    except Exception:
        return ""


# ---------------------------
# Lightweight HTML extraction
# ---------------------------

def _extract_title(html_text: str) -> str:
    if not html_text:
        return ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return html.unescape(m.group(1)).strip()


def _extract_main_text(html_text: str) -> str:
    if not html_text:
        return ""
    # Remove scripts/styles
    html_no_code = re.sub(r"<(script|style)[^>]*>.*?</\\1>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
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


# ---------------------------
# Sentiment (heuristic, free)
# ---------------------------

_POS_WORDS = {
    "beat", "beats", "beating", "surge", "surged", "record", "growth", "rally",
    "upgrade", "upgrades", "outperform", "raise", "raises", "profit", "profits",
    "strong", "bullish", "optimism", "optimistic", "win", "wins", "winning",
    "expand", "expansion", "contract win", "innovation", "breakthrough",
    "guidance raise", "forecast beat", "revenue beat", "eps beat",
    "approval", "milestone", "partnership", "contract",
}

_NEG_WORDS = {
    "miss", "misses", "missing", "fall", "falls", "fell", "drop", "dropped", "decline",
    "downgrade", "downgrades", "underperform", "cut", "cuts", "cutting",
    "loss", "losses", "lawsuit", "probe", "investigation", "fraud",
    "weak", "bearish", "warning", "recall", "delay", "delays",
    "guidance cut", "profit warning",
}

_NEUTRAL_BOOST = {
    "ai", "iphone", "merger", "acquisition", "deal", "agreement", "launch", "product",
    "expansion", "partnership", "contract", "approval", "milestone", "breakthrough",
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
    neutral = sum(1 for t in tokens if t in _NEUTRAL_BOOST)

    raw = pos - neg
    # Mildly dampen negatives that include neutral/business-y words
    raw += 0.25 * neutral

    # Squash to [-1, 1] with tanh
    score = math.tanh(raw / 3.0)
    return {"score": score, "pos": pos, "neg": neg, "words": words}


# ---------------------------
# Impact scoring (0..1)
# ---------------------------

def impact_score(item: dict) -> float:
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

def summarize_text(text: str, max_sentences: int = 5) -> str:
    """
    Very light extractive summarization:
    - sentence split
    - keyword frequency scoring
    - pick top N sentences (order preserved)
    This is intentionally simple to avoid heavy dependencies.
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
        return sum(freq.get(t, 0) for t in toks)

    ranked = sorted(((i, s, score_sentence(s)) for i, s in enumerate(sentences)), key=lambda x: x[2], reverse=True)
    top = sorted(ranked[:max_sentences], key=lambda x: x[0])
    return " ".join(s for _, s, _ in top)