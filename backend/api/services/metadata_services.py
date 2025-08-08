import os
import time
import requests

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# New cache dict
metadata_cache = {}
CACHE_TTL = 7200  # 2 hours

def get_metadata(symbol: str) -> dict:
    symbol = symbol.upper()
    now = time.time()

    # Check cache
    if symbol in metadata_cache:
        ts, data = metadata_cache[symbol]
        if now - ts < CACHE_TTL:
            return data

    # Live fetch
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "Symbol" not in data:
            raise ValueError("Alpha Vantage metadata error")

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

        # ✅ Cache result
        metadata_cache[symbol] = (now, result)
        return result

    except Exception as e:
        print(f"Alpha Vantage metadata error: {e}")
        return {"error": "Could not fetch metadata."}