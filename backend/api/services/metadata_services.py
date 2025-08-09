# backend/api/services/metadata_services.py
from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any
import requests

# Optional fallback (already installed in this project)
try:
    import finnhub  # type: ignore
except Exception:
    finnhub = None  # degrade gracefully if not present

# -------------------------
# Config
# -------------------------
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

FINNHUB_API_KEY = os.getenv("FINNHUB_KEY")
ENABLE_FINNHUB_FALLBACK = os.getenv("METADATA_ENABLE_FINNHUB_FALLBACK", "false").lower() == "true"

# In-memory cache TTL (seconds)
CACHE_TTL = int(os.getenv("METADATA_CACHE_TTL", "7200"))  # default 2 hours

# In-memory cache (symbol -> (ts, data))
_metadata_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}

# Only fields guaranteed across our code paths (EPS is optional)
RESPONSE_FIELDS = [
    "symbol", "name", "description", "sector", "industry",
    "marketCap", "peRatio", "dividendYield", "website", "eps"
]


# -------------------------
# Helpers
# -------------------------
def _now() -> float:
    return time.time()

def _is_mem_fresh(ts: float) -> bool:
    return (_now() - ts) < CACHE_TTL

def _to_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0

def _normalize_alpha_overview(data: dict) -> dict:
    # Map Alpha fields → our normalized keys
    return {
        "symbol": data.get("Symbol"),
        "name": data.get("Name"),
        "description": data.get("Description"),
        "sector": data.get("Sector"),
        "industry": data.get("Industry"),
        "marketCap": _to_float(data.get("MarketCapitalization")),
        "peRatio": _to_float(data.get("PERatio")),
        "dividendYield": _to_float(data.get("DividendYield")),
        "eps": _to_float(data.get("EPS")),
        "website": data.get("Website"),
    }

def _normalize_finnhub(profile: dict, metrics: dict, symbol: str) -> dict:
    # Finnhub units: marketCapitalization is in millions USD
    mc = profile.get("marketCapitalization")
    market_cap = float(mc) * 1e6 if mc is not None else 0.0
    metric = metrics.get("metric", {}) if isinstance(metrics, dict) else {}

    return {
        "symbol": symbol,
        "name": profile.get("name"),
        "description": profile.get("finnhubIndustry"),
        "sector": profile.get("finnhubIndustry"),
        "industry": profile.get("finnhubIndustry"),
        "marketCap": market_cap,
        "peRatio": _to_float(metric.get("peInclExtraTTM")),
        "dividendYield": _to_float(metric.get("dividendYieldIndicatedAnnual")),
        "eps": _to_float(metric.get("epsInclExtraItemsTTM")),
        "website": profile.get("weburl"),
    }

def _is_minimum_metadata(d: dict) -> bool:
    # Require core fields; eps can be absent
    return all(d.get(k) is not None for k in ["symbol", "name", "sector", "industry", "marketCap"])


# -------------------------
# Public API
# -------------------------
def get_metadata(symbol: str) -> dict:
    symbol = symbol.upper()
    now = _now()

    # 1) In-memory cache
    cached = _metadata_cache.get(symbol)
    if cached:
        ts, data = cached
        if _is_mem_fresh(ts):
            return data

    # 2) Alpha Vantage (primary)
    alpha = _fetch_alpha_overview(symbol)
    if alpha and _is_minimum_metadata(alpha):
        # Keep only our response fields (and ensure all exist)
        data = {k: alpha.get(k) for k in RESPONSE_FIELDS}
        _metadata_cache[symbol] = (now, data)
        return data

    # 3) Optional: Finnhub fallback
    if ENABLE_FINNHUB_FALLBACK and FINNHUB_API_KEY and finnhub:
        fb = _fetch_finnhub(symbol)
        if fb and _is_minimum_metadata(fb):
            data = {k: fb.get(k) for k in RESPONSE_FIELDS}
            _metadata_cache[symbol] = (now, data)
            return data

    return {"error": "Could not fetch metadata."}


# -------------------------
# Fetchers
# -------------------------
def _fetch_alpha_overview(symbol: str) -> Optional[dict]:
    if not ALPHA_VANTAGE_API_KEY:
        return None
    params = {"function": "OVERVIEW", "symbol": symbol, "apikey": ALPHA_VANTAGE_API_KEY}
    try:
        r = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=12)
        r.raise_for_status()
        payload = r.json()
        if "Symbol" not in payload:
            # Alpha returns {"Note": "..."} or {"Error Message": "..."} on issues
            return None
        return _normalize_alpha_overview(payload)
    except Exception:
        return None

def _fetch_finnhub(symbol: str) -> Optional[dict]:
    try:
        client = finnhub.Client(api_key=FINNHUB_API_KEY)
        profile = client.company_profile2(symbol=symbol) or {}
        metrics = client.company_basic_financials(symbol, "all") or {}
        return _normalize_finnhub(profile, metrics, symbol)
    except Exception:
        return None