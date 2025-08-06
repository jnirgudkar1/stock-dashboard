import os
import requests

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def get_metadata(symbol: str) -> dict:
    """Fetches stock metadata from Alpha Vantage only."""
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)

        if "Symbol" not in data:
            raise ValueError("Alpha Vantage metadata error")

        # Normalize output format
        return {
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

    except Exception as e:
        print(f"Alpha Vantage metadata error: {e}")
        return {"error": "Could not fetch metadata."}