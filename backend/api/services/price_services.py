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
            ts = data.get("Time Series (Daily)")
            if not ts:
                return None
            prices = {
                date: {
                    "4. close": day["4. close"],
                    "5. volume": day["5. volume"]
                } for date, day in ts.items()
            }
            latest = sorted(prices.keys())[-1]
            latest_price = float(prices[latest]["4. close"])
            return {
                "symbol": symbol,
                "price": latest_price,
                "date": latest,
                "source": "Alpha Vantage",
                "prices": prices
            }
        except Exception as e:
            print("Alpha Vantage error:", e)
            return None

async def fetch_twelve_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=100&apikey={TWELVE_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            data = res.json()
            if "values" not in data:
                return None
            prices = {
                item["datetime"][:10]: {
                    "4. close": item["close"],
                    "5. volume": item.get("volume", "0")
                } for item in data["values"]
            }
            latest = sorted(prices.keys())[-1]
            latest_price = float(prices[latest]["4. close"])
            return {
                "symbol": symbol,
                "price": latest_price,
                "date": latest,
                "source": "Twelve Data",
                "prices": prices
            }
        except Exception as e:
            print("Twelve Data error:", e)
            return None

async def fetch_finnhub(symbol):
    candle_url = f"https://finnhub.io/api/v1/stock/candle"
    now = int(time.time())
    one_month_ago = now - 60 * 60 * 24 * 60
    params = {
        "symbol": symbol,
        "resolution": "D",
        "from": one_month_ago,
        "to": now,
        "token": FINNHUB_KEY
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(candle_url, params=params)
            data = res.json()
            if data.get("s") != "ok":
                return None

            timestamps = data["t"]
            closes = data["c"]
            volumes = data["v"]

            prices = {}
            for i in range(len(timestamps)):
                date = time.strftime('%Y-%m-%d', time.localtime(timestamps[i]))
                prices[date] = {
                    "4. close": str(closes[i]),
                    "5. volume": str(volumes[i])
                }

            latest = sorted(prices.keys())[-1]
            latest_price = float(prices[latest]["4. close"])
            return {
                "symbol": symbol,
                "price": latest_price,
                "date": latest,
                "source": "Finnhub",
                "prices": prices
            }
        except Exception as e:
            print("Finnhub error:", e)
            return None