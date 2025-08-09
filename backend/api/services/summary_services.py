# backend/api/services/summary_services.py
import random

async def get_summary(symbol: str):
    dummy_summaries = [
        f"{symbol} is currently showing strong bullish momentum.",
        f"{symbol} has seen mixed sentiment with moderate volume.",
        f"Investors are cautious about {symbol} amid valuation concerns.",
        f"{symbol} is trading sideways with neutral technical signals.",
    ]
    return {"summary": random.choice(dummy_summaries)}