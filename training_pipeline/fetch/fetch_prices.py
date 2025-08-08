from datetime import date

import yfinance as yf
import pandas as pd
from pathlib import Path

def fetch_price_history(symbol, start="2015-01-01", end=None):
    if end is None:
        end = date.today().isoformat()

    df = yf.download(symbol, start=start, end=end)
    df.reset_index(inplace=True)  # ✅ Do this FIRST

    df["symbol"] = symbol         # ✅ Safe to add now

    Path("training_pipeline/data/historical_prices").mkdir(parents=True, exist_ok=True)
    df.to_csv(f"training_pipeline/data/historical_prices/{symbol}.csv", index=False)
    print(f"Saved {symbol} price data from {start} to {end}")

# Example: run for a few stocks
for symbol in ["AAPL", "GOOGL", "NVDA", "RKLB", "RCAT", "BKSY", "AMD", "TSLA", "PLTR", "AMZN"]:
    fetch_price_history(symbol)