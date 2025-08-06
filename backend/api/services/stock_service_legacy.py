import os
import httpx
from dotenv import load_dotenv

load_dotenv()
ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")

async def get_stock_data(symbol: str):
    if not ALPHA_KEY:
        return {"error": "Missing ALPHA_VANTAGE_KEY in .env"}

    url = (
        f"https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY"
        f"&symbol={symbol}"
        f"&apikey={ALPHA_KEY}"
    )

    async with httpx.AsyncClient() as client:
        res = await client.get(url)

    data = res.json()

    # Catch API limit errors
    if "Note" in data:
        return {"error": "Rate limit hit. Try again later or upgrade your API plan."}
    return data