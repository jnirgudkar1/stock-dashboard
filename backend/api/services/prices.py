"""
prices.py — unified price service with in‑memory caching (no SQLite)

Cascade: Alpha Vantage → Twelve Data → Finnhub
Normalize output to Alpha-style `prices` list for frontend charts.
"""

from __future__ import annotations

import os
import time
import typing as t
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
TWELVE_DATA_BASE = "https://api.twelvedata.com/time_series"
FINNHUB_BASE = "https://finnhub.io/api/v1/stock/candle"

CACHE_TTL = int(os.getenv("PRICE_CACHE_TTL", "60"))

PROVIDER_ORDER = ["alpha_vantage", "twelve_data", "finnhub"]

_INTERVAL_MAP = {
    "1min": {"alpha": "1min", "twelve": "1min", "finnhub": "1"},
    "5min": {"alpha": "5min", "twelve": "5min", "finnhub": "5"},
    "15min": {"alpha": "15min", "twelve": "15min", "finnhub": "15"},
    "30min": {"alpha": "30min", "twelve": "30min", "finnhub": "30"},
    "60min": {"alpha": "60min", "twelve": "1h", "finnhub": "60"},
    "1day": {"alpha": "Daily", "twelve": "1day", "finnhub": "D"},
}

@dataclass
class _CacheItem:
    data: dict
    ts: float

_cache: dict[tuple, _CacheItem] = {}

def _mem_get(key: tuple) -> t.Optional[dict]:
    item = _cache.get(key)
    if not item:
        return None
    if time.time() - item.ts > CACHE_TTL:
        _cache.pop(key, None)
        return None
    return item.data

def _mem_set(key: tuple, data: dict) -> None:
    _cache[key] = _CacheItem(data=data, ts=time.time())


# ---------------- Public API ----------------
class PriceServiceError(Exception):
    pass

def get_prices(symbol: str, *, interval: str = "1day", limit: int = 100) -> dict:
    """
    Returns:
    {
      "symbol": "AAPL",
      "interval": "1day",
      "provider": "alpha_vantage|twelve_data|finnhub|cache",
      "prices": [ ... ascending bars ... ]
    }
    """
    symbol = symbol.upper()
    key = (symbol, interval, limit)

    # 1) in-memory cache
    mem_hit = _mem_get(key)
    if mem_hit:
        return mem_hit

    # 2) provider cascade
    last_err = None
    for provider in PROVIDER_ORDER:
        try:
            if provider == "alpha_vantage":
                data = _from_alpha_vantage(symbol, interval, limit)
            elif provider == "twelve_data":
                data = _from_twelve_data(symbol, interval, limit)
            elif provider == "finnhub":
                data = _from_finnhub(symbol, interval, limit)
            else:
                continue

            if data and data.get("prices"):
                _mem_set(key, data)
                return data
        except Exception as e:
            last_err = e
            continue

    raise PriceServiceError(f"All providers failed for {symbol} ({interval}). Last error: {last_err}")


# ------------- Provider adapters -------------
def _from_alpha_vantage(symbol: str, interval: str, limit: int) -> dict:
    if not ALPHA_VANTAGE_KEY:
        raise PriceServiceError("Missing ALPHA_VANTAGE_KEY")

    alpha_interval = _INTERVAL_MAP.get(interval, {}).get("alpha")
    if alpha_interval in {"1min", "5min", "15min", "30min", "60min"}:
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": alpha_interval,
            "outputsize": "compact" if limit <= 100 else "full",
            "apikey": ALPHA_VANTAGE_KEY,
        }
    elif alpha_interval == "Daily":
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "compact" if limit <= 100 else "full",
            "apikey": ALPHA_VANTAGE_KEY,
        }
    else:
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "compact" if limit <= 100 else "full",
            "apikey": ALPHA_VANTAGE_KEY,
        }

    r = requests.get(ALPHA_VANTAGE_BASE, params=params, timeout=20)
    r.raise_for_status()
    payload = r.json()

    ts = None
    for k in (
        "Time Series (1min)", "Time Series (5min)", "Time Series (15min)",
        "Time Series (30min)", "Time Series (60min)",
        "Time Series (Daily)", "Time Series (Daily Adjusted)",
        "Weekly Adjusted Time Series", "Monthly Adjusted Time Series",
    ):
        if k in payload:
            ts = payload[k]
            break

    if not ts:
        note = payload.get("Note") or payload.get("Error Message") or str(payload)[:200]
        raise PriceServiceError(f"Alpha Vantage error: {note}")

    items = []
    for iso, row in ts.items():
        try:
            o = float(row.get("1. open") or row.get("1. Open"))
            h = float(row.get("2. high") or row.get("2. High"))
            l = float(row.get("3. low") or row.get("3. Low"))
            c = float(row.get("4. close") or row.get("4. Close"))
            v = float(row.get("6. volume") or row.get("5. volume") or row.get("5. Volume") or 0)
        except Exception:
            continue

        try:
            if len(iso) == 10:
                dt = datetime.strptime(iso, "%Y-%m-%d")
            else:
                dt = datetime.strptime(iso, "%Y-%m-%d %H:%M:%S")
            ts_sec = int(dt.timestamp())
        except Exception:
            continue

        items.append({"timestamp": ts_sec, "open": o, "high": h, "low": l, "close": c, "volume": v})

    items.sort(key=lambda x: x["timestamp"])
    return {"symbol": symbol.upper(), "interval": interval, "provider": "alpha_vantage",
            "prices": items[-limit:] if limit else items}


def _from_twelve_data(symbol: str, interval: str, limit: int) -> dict:
    if not TWELVE_DATA_KEY:
        raise PriceServiceError("Missing TWELVE_DATA_KEY")

    twelve_interval = _INTERVAL_MAP.get(interval, {}).get("twelve", "1day")
    params = {
        "symbol": symbol,
        "interval": twelve_interval,
        "apikey": TWELVE_DATA_KEY,
        "outputsize": limit,
        "order": "ASC",
        "format": "JSON",
    }

    r = requests.get(TWELVE_DATA_BASE, params=params, timeout=20)
    r.raise_for_status()
    payload = r.json()

    if "values" not in payload:
        message = payload.get("message") or str(payload)[:200]
        raise PriceServiceError(f"Twelve Data error: {message}")

    items = []
    for row in payload.get("values", []):
        try:
            dt = datetime.strptime(row["datetime"], "%Y-%m-%d" if len(row["datetime"]) == 10 else "%Y-%m-%d %H:%M:%S")
            ts_sec = int(dt.timestamp())
            items.append({
                "timestamp": ts_sec,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0) or 0),
            })
        except Exception:
            continue

    items.sort(key=lambda x: x["timestamp"])
    return {"symbol": symbol.upper(), "interval": interval, "provider": "twelve_data",
            "prices": items[-limit:] if limit else items}


def _from_finnhub(symbol: str, interval: str, limit: int) -> dict:
    if not FINNHUB_KEY:
        raise PriceServiceError("Missing FINNHUB_KEY")

    res = _INTERVAL_MAP.get(interval, {}).get("finnhub", "D")

    now = int(time.time())
    if res == "D":
        span = limit * 86400
    else:
        minutes = int(res)
        span = limit * minutes * 60
    _from = now - span - 60

    params = {"symbol": symbol.upper(), "resolution": res, "from": _from, "to": now, "token": FINNHUB_KEY}

    r = requests.get(FINNHUB_BASE, params=params, timeout=20)
    r.raise_for_status()
    payload = r.json()

    if payload.get("s") != "ok":
        raise PriceServiceError(f"Finnhub error: {payload}")

    items = []
    for i in range(len(payload.get("t", []))):
        items.append({
            "timestamp": int(payload["t"][i]),
            "open": float(payload["o"][i]),
            "high": float(payload["h"][i]),
            "low": float(payload["l"][i]),
            "close": float(payload["c"][i]),
            "volume": float(payload.get("v", [0] * len(payload["t"]))[i]),
        })

    items.sort(key=lambda x: x["timestamp"])
    return {"symbol": symbol.upper(), "interval": interval, "provider": "finnhub",
            "prices": items[-limit:] if limit else items}