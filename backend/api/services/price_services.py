# backend/api/services/price_services.py
import os
import httpx
import time
from dotenv import load_dotenv

load_dotenv()

ALPHA_KEY = os.getenv("ALPHAVANTAGE_KEY")
TWELVE_KEY = os.getenv("TWELVE_DATA_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

# In-memory cache
cache = {}
metadata_cache = {}
CACHE_TTL = 60  # seconds

def is_valid_number(value):
    try:
        return value not in (None, "None", "") and float(value)
    except:
        return False

async def get_stock_price(symbol: str):
    symbol = symbol.upper()
    cached = cache.get(symbol)
    if cached and time.time() - cached["timestamp"] < CACHE_TTL:
        return cached["data"]

    for fetcher in [fetch_alpha_vantage, fetch_twelve_data, fetch_finnhub]:
        data = await fetcher(symbol)
        if data:
            cache[symbol] = {"data": data, "timestamp": time.time()}
            return data

    return {"error": "Failed to fetch stock price from all sources"}

async def fetch_alpha_vantage(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            data = res.json()
            if "Note" in data or "Error Message" in data:
                return None
            ts = data.get("Time Series (Daily)")
            if not ts:
                return None
            latest = sorted(ts.keys())[-1]
            price = float(ts[latest]["4. close"])
            return {"symbol": symbol, "price": price, "date": latest, "source": "Alpha Vantage"}
        except:
            return None

async def fetch_twelve_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1week&outputsize=1&apikey={TWELVE_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            data = res.json()
            if "code" in data or "message" in data:
                return None
            if "values" in data:
                v = data["values"][0]
                return {"symbol": symbol, "price": float(v["close"]), "date": v["datetime"], "source": "Twelve Data"}
        except:
            return None

async def fetch_finnhub(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            data = res.json()
            if "c" in data and data["c"] > 0:
                return {"symbol": symbol, "price": data["c"], "date": time.strftime('%Y-%m-%d'), "source": "Finnhub"}
        except:
            return None

async def get_metadata(symbol: str):
    symbol = symbol.upper()
    now = time.time()
    if symbol in metadata_cache:
        ts, data = metadata_cache[symbol]
        if now - ts < CACHE_TTL:
            return data

    # Alpha Vantage
    if ALPHA_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_KEY}"
            async with httpx.AsyncClient() as client:
                res = await client.get(url)
                data = res.json()
                if "Note" in data or "Information" in data or not data.get("MarketCapitalization"):
                    raise Exception("Alpha Vantage limit hit or data unavailable")
                result = {
                    "marketCap": data.get("MarketCapitalization"),
                    "peRatio": float(data.get("PERatio")) if is_valid_number(data.get("PERatio")) else None,
                    "dividendYield": float(data.get("DividendYield")) * 100 if is_valid_number(data.get("DividendYield")) else None,
                    "sector": data.get("Sector"),
                    "description": data.get("Description"),
                    "website": data.get("OfficialSite")
                }
                metadata_cache[symbol] = (now, result)
                return result
        except Exception as e:
            print("Alpha Vantage metadata error:", e)

    # Twelve Data
    if TWELVE_KEY:
        try:
            url = f"https://api.twelvedata.com/profile?symbol={symbol}&apikey={TWELVE_KEY}"
            async with httpx.AsyncClient() as client:
                res = await client.get(url)
                data = res.json()
                if "code" in data or not data.get("market_cap"):
                    raise Exception("Twelve Data metadata error")
                result = {
                    "marketCap": data.get("market_cap"),
                    "peRatio": float(data.get("pe_ratio")) if is_valid_number(data.get("pe_ratio")) else None,
                    "dividendYield": float(data.get("dividend_rate")) if is_valid_number(data.get("dividend_rate")) else None,
                    "sector": data.get("sector"),
                    "description": data.get("description"),
                    "website": data.get("website")
                }
                metadata_cache[symbol] = (now, result)
                return result
        except Exception as e:
            print("Twelve Data metadata error:", e)

    # Finnhub
    if FINNHUB_KEY:
        try:
            url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_KEY}"
            async with httpx.AsyncClient() as client:
                res = await client.get(url)
                data = res.json()
                if not data.get("marketCapitalization"):
                    raise Exception("Finnhub metadata missing")
                result = {
                    "marketCap": str(data.get("marketCapitalization")),
                    "peRatio": float(data.get("peBasicExclExtraTTM")) if is_valid_number(data.get("peBasicExclExtraTTM")) else None,
                    "dividendYield": float(data.get("dividendYield")) * 100 if is_valid_number(data.get("dividendYield")) else None,
                    "sector": data.get("finnhubIndustry"),
                    "description": None,
                    "website": data.get("weburl")
                }
                metadata_cache[symbol] = (now, result)
                return result
        except Exception as e:
            print("Finnhub metadata error:", e)

    return {"error": "Failed to retrieve metadata from all sources."}
