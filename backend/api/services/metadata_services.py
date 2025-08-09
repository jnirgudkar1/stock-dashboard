# backend/api/services/metadata_services.py

import os
import time
import requests
import finnhub

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

FINNHUB_API_KEY = os.getenv("FINNHUB_KEY")
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

metadata_cache = {}
CACHE_TTL = 7200  # 2 hours

REQUIRED_FIELDS = [
    "symbol", "name", "description", "sector", "industry",
    "marketCap", "peRatio", "dividendYield", "eps", "website"
]

def is_valid_metadata(data: dict) -> bool:
    return all(field in data and data[field] is not None for field in REQUIRED_FIELDS)

def normalize_metadata(data: dict) -> dict:
    return {
        "symbol": data.get("symbol"),
        "name": data.get("name"),
        "description": data.get("description"),
        "sector": data.get("sector"),
        "industry": data.get("industry"),
        "marketCap": float(data.get("marketCap", 0)),
        "peRatio": float(data.get("peRatio", 0)),
        "dividendYield": float(data.get("dividendYield", 0)),
        "eps": float(data.get("eps", 0)),
        "website": data.get("website"),
    }

def get_metadata(symbol: str) -> dict:
    symbol = symbol.upper()
    now = time.time()

    # Check cache
    if symbol in metadata_cache:
        ts, data = metadata_cache[symbol]
        if now - ts < CACHE_TTL:
            return data

    # Attempt Alpha Vantage
    alpha_params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=alpha_params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "Symbol" in data:
            result = {
                "symbol": data.get("Symbol"),
                "name": data.get("Name"),
                "description": data.get("Description"),
                "sector": data.get("Sector"),
                "industry": data.get("Industry"),
                "marketCap": float(data.get("MarketCapitalization", 0)),
                "peRatio": float(data.get("PERatio", 0)),
                "dividendYield": float(data.get("DividendYield", 0)),
                "eps": float(data.get("EPS", 0)),
                "website": data.get("Website"),
            }

            if is_valid_metadata(result):
                metadata_cache[symbol] = (now, result)
                return result
    except Exception as e:
        print(f"[Alpha Vantage error] {e}")

    # Try fallback: Finnhub
    try:
        profile = finnhub_client.company_profile2(symbol=symbol)
        metrics = finnhub_client.company_basic_financials(symbol, 'all').get("metric", {})

        fallback_result = {
            "symbol": symbol,
            "name": profile.get("name"),
            "description": profile.get("finnhubIndustry"),
            "sector": profile.get("finnhubIndustry"),
            "industry": profile.get("finnhubIndustry"),
            "marketCap": profile.get("marketCapitalization") * 1e6 if profile.get("marketCapitalization") else 0,
            "peRatio": metrics.get("peInclExtraTTM") or 0,
            "dividendYield": metrics.get("dividendYieldIndicatedAnnual") or 0,
            "eps": metrics.get("epsInclExtraItemsTTM") or 0,
            "website": profile.get("weburl"),
        }

        if is_valid_metadata(fallback_result):
            result = normalize_metadata(fallback_result)
            metadata_cache[symbol] = (now, result)
            return result
    except Exception as e:
        print(f"[Finnhub fallback error] {e}")

    return {"error": "Could not fetch metadata."}