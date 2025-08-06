# backend/api/services/metadata_services.py

import os
import httpx
import time
from dotenv import load_dotenv

load_dotenv()

ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")
TWELVE_KEY = os.getenv("TWELVE_DATA_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

# In-memory cache: {symbol: (timestamp, data)}
metadata_cache = {}
CACHE_TTL = 60  # seconds

async def get_metadata(symbol: str):
    now = time.time()
    if symbol in metadata_cache:
        ts, data = metadata_cache[symbol]
        if now - ts < CACHE_TTL:
            return data

    # Try Alpha Vantage first
    if ALPHA_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_KEY}"
            async with httpx.AsyncClient() as client:
                res = await client.get(url)
                data = res.json()
                if 'MarketCapitalization' in data:
                    result = {
                        'marketCap': data.get('MarketCapitalization'),
                        'peRatio': data.get('PERatio'),
                        'dividendYield': data.get('DividendYield'),
                        'sector': data.get('Sector')
                    }
                    metadata_cache[symbol] = (now, result)
                    return result
        except Exception as e:
            print("Alpha Vantage metadata error:", e)

    # Try Twelve Data
    if TWELVE_KEY:
        try:
            url = f"https://api.twelvedata.com/profile?symbol={symbol}&apikey={TWELVE_KEY}"
            async with httpx.AsyncClient() as client:
                res = await client.get(url)
                data = res.json()
                if 'market_cap' in data:
                    result = {
                        'marketCap': data.get('market_cap'),
                        'peRatio': data.get('pe_ratio'),
                        'dividendYield': data.get('dividend_rate'),
                        'sector': data.get('sector')
                    }
                    metadata_cache[symbol] = (now, result)
                    return result
        except Exception as e:
            print("Twelve Data metadata error:", e)

    # Try Finnhub
    if FINNHUB_KEY:
        try:
            url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_KEY}"
            async with httpx.AsyncClient() as client:
                res = await client.get(url)
                data = res.json()
                if 'marketCapitalization' in data:
                    result = {
                        'marketCap': str(data.get('marketCapitalization')),
                        'peRatio': data.get('peBasicExclExtraTTM'),
                        'dividendYield': data.get('dividendYield'),
                        'sector': data.get('finnhubIndustry')
                    }
                    metadata_cache[symbol] = (now, result)
                    return result
        except Exception as e:
            print("Finnhub metadata error:", e)

    return {"error": "Failed to retrieve metadata from all sources."}
