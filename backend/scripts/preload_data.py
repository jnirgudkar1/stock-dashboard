# backend/scripts/preload_data.py
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Iterable, Optional, Dict, Any, List

# Ensure repo root on path
HERE = os.path.abspath(os.path.dirname(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

# DB helpers
from api.db.database import (
    create_all_tables,
    db_upsert_metadata,
    db_get_metadata,
    db_upsert_prices,
    db_get_prices_last_updated,
    db_upsert_stock_features,
)

# Try to use your existing services (graceful fallback if not present)
try:
    from api.services.metadata_services import fetch_metadata  # expected: fetch_metadata(symbol) -> dict
except Exception:
    fetch_metadata = None

try:
    from api.services.price_services import fetch_daily_prices  # expected: fetch_daily_prices(symbol, outputsize="compact"|"full") -> list[{date,open,high,low,close,volume}]
except Exception:
    fetch_daily_prices = None

try:
    from api.services.news_services import search_company_news  # expected: search_company_news(symbol, limit=20) -> list[dict]
    from api.services.sentiment_analyzer import analyze_sentiment_text  # optional if you split analyzer
except Exception:
    search_company_news = None
    analyze_sentiment_text = None

# Valuation + prediction (optional if wired)
try:
    from api.services.valuation_scorer import score_valuation_from_inputs  # (metadata, news_items)-> dict scores
except Exception:
    score_valuation_from_inputs = None

try:
    from api.services.valuation_predictor import predict_direction_for_symbol  # returns {"prob_up":..,"prob_down":..,"label":..}
except Exception:
    predict_direction_for_symbol = None

# News cache upserts (simple)
from api.db.database import get_connection


def upsert_news_rows(symbol: str, items: List[Dict[str, Any]]) -> None:
    """
    Insert/Update into news_cache. If your project already has a helper, swap this with it.
    items entries may contain: url, title, content, sentiment_score, impact_score, published_at
    """
    if not items:
        return
    with get_connection() as conn:
        cur = conn.cursor()
        sql = """
          INSERT INTO news_cache(url, symbol, title, content, sentiment_score, impact_score, published_at)
          VALUES(?,?,?,?,?,?,?)
          ON CONFLICT(url) DO UPDATE SET
            symbol=excluded.symbol,
            title=excluded.title,
            content=excluded.content,
            sentiment_score=excluded.sentiment_score,
            impact_score=excluded.impact_score,
            published_at=excluded.published_at,
            last_updated=CURRENT_TIMESTAMP
        """
        rows = []
        for it in items:
            rows.append((
                it.get("url"),
                symbol,
                it.get("title"),
                it.get("content"),
                it.get("sentiment_score"),
                it.get("impact_score"),
                it.get("published_at"),
            ))
        cur.executemany(sql, rows)
        conn.commit()


def ttl_expired(last_dt: Optional[datetime], ttl_seconds: int) -> bool:
    if last_dt is None:
        return True
    return (datetime.utcnow() - last_dt) > timedelta(seconds=ttl_seconds)


def preload_metadata(symbol: str, force: bool = False, ttl_seconds: int = 7200) -> Optional[Dict[str, Any]]:
    row = db_get_metadata(symbol)
    # metadata table has its own last_updated; quick TTL check
    stale = True
    if row and row.get("last_updated"):
        try:
            lu = str(row["last_updated"])
            last = datetime.fromisoformat(lu) if "T" in lu else datetime.strptime(lu.split(".")[0], "%Y-%m-%d %H:%M:%S")
            stale = ttl_expired(last, ttl_seconds)
        except Exception:
            stale = True

    if not force and not stale:
        return row

    if not fetch_metadata:
        print(f"[metadata] No fetcher wired for {symbol}; skipping.")
        return row

    data = fetch_metadata(symbol) or {}
    if data.get("symbol"):
        db_upsert_metadata(data)
        print(f"[metadata] Upserted {symbol}")
        return data
    else:
        print(f"[metadata] Empty for {symbol}; leaving existing.")
        return row


def preload_prices(symbol: str, force: bool = False, ttl_seconds: int = 3600, full_history: bool = False) -> int:
    last = db_get_prices_last_updated(symbol)
    if not force and not ttl_expired(last, ttl_seconds):
        print(f"[prices] Fresh enough for {symbol}; skipping.")
        return 0

    if not fetch_daily_prices:
        print(f"[prices] No price fetcher wired for {symbol}; skipping.")
        return 0

    outputsize = "full" if full_history else "compact"
    rows = fetch_daily_prices(symbol, outputsize=outputsize) or []
    if rows:
        # Expect rows: [{symbol,date,open,high,low,close,volume}, ...]
        db_upsert_prices(rows)
        print(f"[prices] Upserted {len(rows)} rows for {symbol}")
        return len(rows)
    print(f"[prices] No rows for {symbol}")
    return 0


def preload_news(symbol: str, limit: int = 25, force: bool = False, ttl_seconds: int = 10800) -> int:
    if not search_company_news:
        print(f"[news] No news fetcher wired for {symbol}; skipping.")
        return 0

    # Simple strategy: always fetch top N recent; rely on ON CONFLICT(url) for idempotence
    items = search_company_news(symbol, limit=limit) or []

    # sentiment enrichment if available and missing
    for it in items:
        if it.get("content") and analyze_sentiment_text and "sentiment_score" not in it:
            try:
                score = analyze_sentiment_text(it["content"])
                it["sentiment_score"] = score
            except Exception:
                pass
        it.setdefault("impact_score", None)

    upsert_news_rows(symbol, items)
    print(f"[news] Upserted {len(items)} items for {symbol}")
    return len(items)


def derive_and_store_features(symbol: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Stores a single row in stock_features for quick model inputs.
    You can expand this to add rolling features later.
    """
    # Latest close
    from api.db.database import db_get_prices
    prices = db_get_prices(symbol, limit=1)
    close_price = prices[0]["close"] if prices else None

    # Metadata-derived features
    if metadata is None:
        metadata = db_get_metadata(symbol) or {}

    pe_ratio = metadata.get("peRatio")
    eps = None
    # If you’ve added EPS to metadata later, pull it here; else leave None
    # eps = metadata.get("eps")  # optional
    revenue_growth = None  # populate when available in your pipeline

    db_upsert_stock_features({
        "symbol": symbol,
        "close_price": close_price,
        "pe_ratio": pe_ratio,
        "eps": eps,
        "revenue_growth": revenue_growth,
    })
    print(f"[features] Upserted basic features for {symbol}")


def preload_valuation(symbol: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    if not score_valuation_from_inputs:
        print(f"[valuation] Scorer not wired; skipping {symbol}.")
        return

    # Pull recent news from DB
    with get_connection() as conn:
        rows = conn.execute("""
          SELECT title, content, sentiment_score, impact_score, published_at, url
          FROM news_cache WHERE symbol=? ORDER BY published_at DESC LIMIT 50
        """, (symbol,)).fetchall()
        news_items = [dict(r) for r in rows]

    if metadata is None:
        metadata = db_get_metadata(symbol) or {}

    result = score_valuation_from_inputs(metadata, news_items)  # should match your scorer’s signature
    if not result:
        print(f"[valuation] No result for {symbol}")
        return

    # Upsert into valuation_data
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
          INSERT INTO valuation_data(symbol, sentiment_score, financial_score, growth_score, total_score,
                                     verdict, eps_growth, revenue_growth, confidence, contradiction, valuation_label)
          VALUES(?,?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(symbol) DO UPDATE SET
            sentiment_score=excluded.sentiment_score,
            financial_score=excluded.financial_score,
            growth_score=excluded.growth_score,
            total_score=excluded.total_score,
            verdict=excluded.verdict,
            eps_growth=excluded.eps_growth,
            revenue_growth=excluded.revenue_growth,
            confidence=excluded.confidence,
            contradiction=excluded.contradiction,
            valuation_label=excluded.valuation_label,
            last_updated=CURRENT_TIMESTAMP
        """, (
            result.get("sentiment_score"),
            result.get("financial_score"),
            result.get("growth_score"),
            result.get("total_score"),
            result.get("verdict"),
            result.get("eps_growth"),
            result.get("revenue_growth"),
            result.get("confidence"),
            result.get("contradiction"),
            result.get("valuation_label"),
            # symbol last to match columns? No: symbol is first in columns list above
        ))
        # OOPS: The VALUES order must match the columns; fix by moving symbol first:
        conn.rollback()
        cur.execute("""
          INSERT INTO valuation_data(symbol, sentiment_score, financial_score, growth_score, total_score,
                                     verdict, eps_growth, revenue_growth, confidence, contradiction, valuation_label)
          VALUES(?,?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(symbol) DO UPDATE SET
            sentiment_score=excluded.sentiment_score,
            financial_score=excluded.financial_score,
            growth_score=excluded.growth_score,
            total_score=excluded.total_score,
            verdict=excluded.verdict,
            eps_growth=excluded.eps_growth,
            revenue_growth=excluded.revenue_growth,
            confidence=excluded.confidence,
            contradiction=excluded.contradiction,
            valuation_label=excluded.valuation_label,
            last_updated=CURRENT_TIMESTAMP
        """, (
            symbol,
            result.get("sentiment_score"),
            result.get("financial_score"),
            result.get("growth_score"),
            result.get("total_score"),
            result.get("verdict"),
            result.get("eps_growth"),
            result.get("revenue_growth"),
            result.get("confidence"),
            result.get("contradiction"),
            result.get("valuation_label"),
        ))
        conn.commit()
    print(f"[valuation] Upserted for {symbol}")


def preload_prediction(symbol: str) -> None:
    if not predict_direction_for_symbol:
        print(f"[predict] Predictor not wired; skipping {symbol}.")
        return
    res = predict_direction_for_symbol(symbol) or {}
    if not res:
        print(f"[predict] No prediction for {symbol}")
        return

    with get_connection() as conn:
        conn.execute("""
          INSERT INTO price_predictions(symbol, prob_up, prob_down, label, model_loaded_at)
          VALUES(?,?,?,?,?)
          ON CONFLICT(symbol) DO UPDATE SET
            prob_up=excluded.prob_up,
            prob_down=excluded.prob_down,
            label=excluded.label,
            model_loaded_at=excluded.model_loaded_at,
            last_updated=CURRENT_TIMESTAMP
        """, (symbol, res.get("prob_up"), res.get("prob_down"), res.get("label"), res.get("model_loaded_at")))
        conn.commit()
    print(f"[predict] Upserted for {symbol}")


def preload_symbol(
    symbol: str,
    force: bool = False,
    prices_ttl: int = 3600,
    metadata_ttl: int = 7200,
    full_history: bool = False,
    news_limit: int = 25
) -> None:
    print(f"\n=== {symbol} ===")
    md = preload_metadata(symbol, force=force, ttl_seconds=metadata_ttl)
    preload_prices(symbol, force=force, ttl_seconds=prices_ttl, full_history=full_history)
    preload_news(symbol, limit=news_limit, force=force)
    derive_and_store_features(symbol, metadata=md)
    preload_valuation(symbol, metadata=md)
    preload_prediction(symbol)


def parse_args():
    p = argparse.ArgumentParser(description="Preload/cache stock data into SQLite for faster dashboard & better history.")
    p.add_argument("--symbols", type=str, required=True,
                   help="Comma-separated list: e.g., AAPL,MSFT,GOOGL")
    p.add_argument("--force", action="store_true", help="Ignore TTLs; refetch everything.")
    p.add_argument("--full-history", action="store_true", help="Pull full price history (slower).")
    p.add_argument("--prices-ttl", type=int, default=3600)
    p.add_argument("--metadata-ttl", type=int, default=7200)
    p.add_argument("--news-limit", type=int, default=25)
    return p.parse_args()


def main():
    create_all_tables()
    args = parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    for sym in symbols:
        try:
            preload_symbol(
                sym,
                force=args.force,
                prices_ttl=args.prices_ttl,
                metadata_ttl=args.metadata_ttl,
                full_history=args.full_history,
                news_limit=args.news_limit,
            )
        except Exception as e:
            print(f"[ERROR] {sym}: {e}")
            continue


if __name__ == "__main__":
    main()