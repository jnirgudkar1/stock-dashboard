"""
news.py — unified news service with sentiment + impact scoring (no DB)

Exports:
- search_news(query=None, symbol=None, *, max_items=20) -> list[dict]
- fetch_and_cache_article_text(url) -> dict

Each news item:
{
  "title": str,
  "url": str,
  "source": str,
  "published_at": int,   # epoch seconds
  "description": str | None,
  "sentiment": { "score": float[-1..1], "label": "positive|neutral|negative", "color": "green|yellow|red" },
  "impact": "low|medium|high",
  "impact_score": float, # 0..100
}
"""

from __future__ import annotations

import os
import re
import time
from typing import Dict, Tuple

import requests

# ---------------------------
# Config
# ---------------------------

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY") or os.getenv("GNEWS_KEY") or ""
GNEWS_ENDPOINT = "https://gnews.io/api/v4/search"  # free tier supports search

_CACHE_TTL_SEARCH = int(os.getenv("NEWS_CACHE_TTL", "1800"))   # 30m
_CACHE_TTL_ARTICLE = int(os.getenv("ARTICLE_CACHE_TTL", "86400"))  # 24h

_search_cache: Dict[Tuple[str, int], Tuple[float, list[dict]]] = {}
_article_cache: Dict[str, Tuple[float, dict]] = {}

# ---------------------------
# Utilities
# ---------------------------

def _label_color_from_score(score: float) -> tuple[str, str]:
    """Map sentiment score [-1..1] to (label, color)."""
    if score >= 0.15:
        return ("positive", "green")
    if score <= -0.15:
        return ("negative", "red")
    return ("neutral", "yellow")


def _cache_get(cache: dict, key, ttl: int):
    ent = cache.get(key)
    if not ent:
        return None
    ts, val = ent
    return val if (time.time() - ts) <= ttl else None


def _cache_set(cache: dict, key, val):
    cache[key] = (time.time(), val)


def _extract_tickers(text: str) -> list[str]:
    return re.findall(r"\b[A-Z]{2,5}\b", text or "")


# ---------------------------
# Sentiment (heuristic, no ML)
# ---------------------------

_POS = set("""beat beats beating surge surges bullish upgrade record rally rebound surge strong growth profit profits profitable upside raised raises
outperform buy buys optimistic optimisticly optimism expand expanding expansion accelerate accelerating""".split())
_NEG = set("""miss misses missed plunge plunges bearish downgrade lawsuit probe investigation fraud cut cuts cutting cutting cut guidance warning warns
layoff layoffs decline declines declining weak weakness loss losses downside fear fears pessimistic slowdown slowing slump""".split())

def sentiment(text: str) -> dict:
    """
    Very lightweight keyword-based sentiment -> score in [-1..1].
    """
    if not text:
        return {"score": 0.0, "label": "neutral", "color": "yellow"}
    toks = re.findall(r"[A-Za-z']+", text.lower())
    pos = sum(1 for t in toks if t in _POS)
    neg = sum(1 for t in toks if t in _NEG)
    total = pos + neg
    score = 0.0 if total == 0 else (pos - neg) / total
    label, color = _label_color_from_score(score)
    return {"score": round(score, 4), "label": label, "color": color}


# ---------------------------
# Impact score 0..1 (display as 0..100 on frontend)
# ---------------------------

_SRC_WEIGHTS = {
    "reuters": 1.0, "bloomberg": 1.0, "wsj": 0.95, "financial times": 0.95,
    "cnbc": 0.85, "marketwatch": 0.8, "seeking alpha": 0.7, "yahoo": 0.7
}
_KEYWORDS = [
    "earnings","guidance","downgrade","upgrade","lawsuit",
    "acquires","acquisition","merger","sec","cfo","partnership","bankruptcy"
]

def impact_score(item: dict) -> float:
    """Blend recency, source weight, and sentiment into a single score in [0,1]."""
    title = (item or {}).get("title") or ""
    desc = (item or {}).get("description") or ""
    ts = float((item or {}).get("published_at") or 0)

    # Sentiment strength |score| (0..1)
    s = sentiment(f"{title}. {desc}")
    s_term = 0.5 * abs(s["score"])  # weight 0.5

    # Recency decay (half-life 24h)
    age = max(0.0, time.time() - ts)
    decay = 0.5 ** (age / (24 * 3600.0))  # 1.0 at now, 0.5 after 24h ...
    r_term = 0.35 * decay  # weight 0.35

    # Source weight (0.6..1.0)
    src = ((item or {}).get("source") or "").lower()
    src_weight = max(0.6, _SRC_WEIGHTS.get(src, 0.7))
    src_term = 0.10 * src_weight  # weight 0.10

    # Keyword boost (0..0.05)
    kw_lower = f"{title} {desc}".lower()
    k = sum(1 for w in _KEYWORDS if w in kw_lower)
    kw_term = 0.05 * min(1.0, k / 3.0)

    score = s_term + r_term + src_term + kw_term
    return max(0.0, min(1.0, score))


# ---------------------------
# Search news
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
    key = (q, int(max_items))
    cached = _cache_get(_search_cache, key, _CACHE_TTL_SEARCH)
    if cached is not None:
        return cached

    params = {
        "q": q,
        "lang": "en",
        "max": int(max_items),
        "token": GNEWS_API_KEY,
        "sortby": "publishedAt",
    }
    r = requests.get(GNEWS_ENDPOINT, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    articles = (data or {}).get("articles", []) or []
    items: list[dict] = []
    for a in articles[: int(max_items)]:
        # Normalize
        title = a.get("title") or ""
        url = a.get("url") or ""
        source = ((a.get("source") or {}).get("name") or "").strip()
        desc = a.get("description") or ""
        # gnews uses RFC3339 in 'publishedAt'
        published_at = a.get("publishedAt") or a.get("published_at") or ""
        # parse to epoch
        ts = _parse_iso_to_epoch(published_at)

        base = {
            "title": title,
            "url": url,
            "source": source,
            "published_at": ts,
            "description": desc,
        }
        # sentiment + impact
        s = sentiment(f"{title}. {desc}")
        base["sentiment"] = s
        imp = impact_score(base)  # 0..1
        base["impact_score"] = round(imp * 100.0, 1)
        base["impact"] = ("high" if imp >= 0.66 else "medium" if imp >= 0.4 else "low")
        items.append(base)

    _cache_set(_search_cache, key, items)
    return items


def _parse_iso_to_epoch(s: str) -> int:
    # Try several formats quickly without bringing heavy deps
    if not s:
        return 0
    try:
        # 2023-10-05T14:30:00Z or with offset
        import datetime as _dt
        try:
            dt = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            # Fallback RFC2822 style
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(s)
        return int(dt.timestamp())
    except Exception:
        return 0


# ---------------------------
# Article fetch + text extract
# ---------------------------

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120 Safari/537.36"
)

def fetch_and_cache_article_text(url: str) -> dict:
    if not url:
        raise ValueError("url required")
    cached = _cache_get(_article_cache, url, _CACHE_TTL_ARTICLE)
    if cached is not None:
        return cached

    try:
        r = requests.get(url, headers={"User-Agent": _USER_AGENT, "Accept": "text/html"}, timeout=10)
        r.raise_for_status()
        html = r.text
        text = _html_to_text(html)
        out = {"url": url, "text": text[:20000]}
        _cache_set(_article_cache, url, out)
        return out
    except Exception as e:
        raise RuntimeError(f"failed to fetch article: {e}")


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

def _html_to_text(html: str) -> str:
    txt = _TAG_RE.sub(" ", html or "")
    txt = _WS_RE.sub(" ", txt)
    return txt.strip()


# ---------------------------
# Summarization (extractive, optional)
# ---------------------------

def summarize_text(text: str, max_sentences: int = 5) -> str:
    """
    Very light extractive summarization:
    - sentence split
    - keyword frequency scoring
    - take top-N sentences
    """
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) <= max_sentences:
        return text.strip()

    tokens = re.findall(r"[A-Za-z']+", text.lower())
    freq: dict[str, int] = {}
    for tkn in tokens:
        freq[tkn] = freq.get(tkn, 0) + 1

    def score_sentence(s: str) -> float:
        toks = re.findall(r"[A-Za-z']+", s.lower())
        return sum(freq.get(t, 0) for t in toks) / (len(toks) + 1e-6)

    # pick top sentences, keep original order
    ranked = sorted([(i, score_sentence(s)) for i, s in enumerate(sentences)], key=lambda x: x[1], reverse=True)
    keep_idx = set(i for i, _ in ranked[:max_sentences])
    kept = [s for i, s in enumerate(sentences) if i in keep_idx]
    return " ".join(kept)
    return " ".join(kept)