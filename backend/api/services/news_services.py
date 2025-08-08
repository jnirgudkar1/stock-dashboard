# backend/api/services/news_services.py
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
GNEWS_KEY = os.getenv("GNEWS_KEY")
NEWS_SERVICES = os.getenv("NEWS_API_KEY")

async def get_news(symbol: str):
    if not GNEWS_KEY:
        return {"error": "Missing GNEWS_KEY in .env"}

    url = (
        f"https://gnews.io/api/v4/search"
        f"?q={symbol}&lang=en&country=us&max=10&token=fd8502cdf5b5370c46d4e0b936e0a65c"
    )

    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        print("== INCOMING REQUEST HEADERS ==")
        for k, v in res.request.headers.items():
            print(f"{k}: {v}")

    print("GNews status code:", res.status_code)
    print("GNews response:", res.text[:1000])  # Truncate long output

    data = res.json()

    if "errors" in data or "error" in data:
        return {"error": "Failed to fetch news"}

    return data.get("articles", [])