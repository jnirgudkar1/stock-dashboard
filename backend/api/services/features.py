"""
features.py — technical + news sentiment features (no DB, in-memory cached)

Depends on existing services:
- prices.get_prices(symbol, interval, limit)
- news.search_news(symbol, max_items)

Outputs a compact feature vector for use by /predict and the UI.
"""

from __future__ import annotations

import math
import os
import time
from typing import Dict, List, Tuple

from .prices import get_prices
from .news import search_news

# -------------------------
# Config (env overrides)
# -------------------------
FEATURES_CACHE_TTL = int(os.getenv("FEATURES_CACHE_TTL", "600"))  # 10 minutes
DEFAULT_INTERVAL = os.getenv("FEATURES_INTERVAL", "1day")
DEFAULT_LIMIT = int(os.getenv("FEATURES_PRICE_LIMIT", "240"))     # enough for 26/20/21-day windows
DEFAULT_MAX_NEWS = int(os.getenv("FEATURES_MAX_NEWS", "50"))

# -------------------------
# In-memory cache
# -------------------------
_cache: Dict[Tuple[str, str, int, int], Tuple[float, dict]] = {}

def _cache_get(key: Tuple[str, str, int, int]):
    ent = _cache.get(key)
    if not ent:
        return None
    ts, val = ent
    if time.time() - ts <= FEATURES_CACHE_TTL:
        return val
    return None

def _cache_set(key: Tuple[str, str, int, int], val: dict):
    _cache[key] = (time.time(), val)

# -------------------------
# Math helpers
# -------------------------
def _sma(values: List[float], n: int) -> float | None:
    if len(values) < n:
        return None
    return sum(values[-n:]) / n

def _stddev(values: List[float], n: int) -> float | None:
    if len(values) < n:
        return None
    m = _sma(values, n)
    if m is None:
        return None
    var = sum((v - m) ** 2 for v in values[-n:]) / n
    return math.sqrt(var)

def _ema(values: List[float], n: int) -> float | None:
    if len(values) < n:
        return None
    k = 2 / (n + 1)
    ema = sum(values[:n]) / n  # seed with SMA
    for v in values[n:]:
        ema = v * k + ema * (1 - k)
    return ema

def _rsi(values: List[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains = []
    losses = []
    for i in range(1, len(values)):
        chg = values[i] - values[i - 1]
        gains.append(max(chg, 0.0))
        losses.append(max(-chg, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    # Wilder's smoothing
    for i in range(period, len(values) - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def _macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float | None, float | None, float | None]:
    if len(values) < slow + signal:
        return (None, None, None)
    ema_fast = _ema(values, fast)
    ema_slow = _ema(values, slow)
    if ema_fast is None or ema_slow is None:
        return (None, None, None)
    macd_val = ema_fast - ema_slow
    # Build MACD series to compute signal (approximate with last 'signal' points)
    macd_series: List[float] = []
    for i in range(len(values)):
        ef = _ema(values[: i + 1], fast)
        es = _ema(values[: i + 1], slow)
        if ef is not None and es is not None:
            macd_series.append(ef - es)
    if len(macd_series) < signal:
        return (macd_val, None, None)
    sig = _ema(macd_series, signal)
    if sig is None:
        return (macd_val, None, None)
    hist = macd_val - sig
    return (macd_val, sig, hist)

def _pct(a: float, b: float) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return (a / b) - 1.0

# -------------------------
# Public: get_features
# -------------------------
def get_features(symbol: str, interval: str = DEFAULT_INTERVAL, limit: int = DEFAULT_LIMIT, max_news: int = DEFAULT_MAX_NEWS) -> dict:
    """
    Build a compact features dict from prices + news.

    Returns:
    {
      "symbol": "AAPL",
      "asof": 1723600000,
      "window": {"prices": 240, "news": 50},
      "features": {...}
    }
    """
    symbol = symbol.upper()
    key = (symbol, interval, int(limit), int(max_news))
    cached = _cache_get(key)
    if cached:
        return cached

    # ---- Prices
    price_payload = get_prices(symbol, interval=interval, limit=limit)
    items = (price_payload or {}).get("prices", [])
    if not items:
        raise RuntimeError("No price data available")

    closes = [float(x["close"]) for x in items]
    highs  = [float(x["high"])  for x in items]
    lows   = [float(x["low"])   for x in items]
    vols   = [float(x.get("volume", 0.0)) for x in items]

    last = closes[-1]
    prev = closes[-2] if len(closes) > 1 else None

    ret_1d  = _pct(last, prev) if prev is not None else None
    ret_5d  = _pct(closes[-1], closes[-6])  if len(closes) >= 6  else None
    ret_21d = _pct(closes[-1], closes[-22]) if len(closes) >= 22 else None

    # Volatility (21d std of daily returns)
    rets = []
    for i in range(1, len(closes)):
        if closes[i - 1] != 0:
            rets.append((closes[i] / closes[i - 1]) - 1.0)
    vol_21d = _stddev(rets, 21) if len(rets) >= 21 else None

    # RSI(14), MACD(12,26,9), Bollinger %B(20, 2)
    rsi_14 = _rsi(closes, 14)
    macd_val, macd_signal, macd_hist = _macd(closes, 12, 26, 9)

    sma_20 = _sma(closes, 20)
    sd_20  = _stddev(closes, 20)
    bb_upper = sma_20 + 2 * sd_20 if sma_20 is not None and sd_20 is not None else None
    bb_lower = sma_20 - 2 * sd_20 if sma_20 is not None and sd_20 is not None else None
    bb_percent_b = None
    if bb_upper is not None and bb_lower is not None and bb_upper != bb_lower:
        bb_percent_b = (last - bb_lower) / (bb_upper - bb_lower)

    # Volume z-score (20)
    vol_mean_20 = _sma(vols, 20)
    vol_sd_20 = _stddev(vols, 20)
    vol_zscore = (vols[-1] - vol_mean_20) / vol_sd_20 if vol_mean_20 and vol_sd_20 else None

    # ---- News aggregates
    now = time.time()
    items_news = search_news(symbol=symbol, max_items=max_news) if max_news > 0 else []
    scores = [(n.get("sentiment") or {}).get("score") for n in items_news if isinstance((n.get("sentiment") or {}).get("score"), (int, float))]
    times  = [float(n.get("published_at") or 0) for n in items_news]

    def mean(arr: List[float]) -> float | None:
        arr2 = [float(x) for x in arr if isinstance(x, (int, float))]
        return sum(arr2) / len(arr2) if arr2 else None

    def window_mask(seconds: int) -> List[int]:
        cutoff = now - seconds
        return [i for i, tts in enumerate(times) if tts >= cutoff]

    idx_24h = window_mask(24 * 3600)
    idx_7d  = window_mask(7 * 24 * 3600)

    sent_24h = mean([scores[i] for i in idx_24h]) if idx_24h else None
    sent_7d  = mean([scores[i] for i in idx_7d])  if idx_7d  else None

    # Assemble features
    feats = {
        # Price-based
        "close": last,
        "return_1d": ret_1d,
        "return_5d": ret_5d,
        "return_21d": ret_21d,
        "volatility_21d": vol_21d,
        "rsi_14": rsi_14,
        "macd": macd_val,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "bb_percent_b": bb_percent_b,
        "volume_zscore_20": vol_zscore,
        # News-based
        "news_sent_mean_24h": sent_24h,
        "news_sent_mean_7d": sent_7d,
        "news_count_24h": len(idx_24h),
        "news_count_7d": len(idx_7d),
        "news_count_total": len(items_news),
    }

    # Round gently for readability
    out_feats = {}
    for k, v in feats.items():
        if isinstance(v, float):
            out_feats[k] = round(v, 6)
        else:
            out_feats[k] = v

    payload = {
        "symbol": symbol,
        "asof": int(now),
        "window": {"prices": limit, "news": max_news},
        "features": out_feats,
        "interval": interval,
    }
    _cache_set(key, payload)
    return payload