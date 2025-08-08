# training_pipeline/fetch/fetch_fundamentals.py

import finnhub
import os
import pandas as pd
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("FINNHUB_KEY")
finnhub_client = finnhub.Client(api_key=api_key)

def fetch_fundamentals(symbol):
    try:
        data = finnhub_client.company_basic_financials(symbol, 'all')
        metrics = data.get("metric")

        if not metrics or not isinstance(metrics, dict):
            print(f"No fundamentals for {symbol}")
            return None

        return {
            "symbol": symbol,
            "pe_ratio": metrics.get("peInclExtraTTM") or 0.0,
            "eps": metrics.get("epsInclExtraItemsTTM") or 0.0,
            "revenue_growth": metrics.get("revenueGrowthQoQ") or 0.0,
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

if __name__ == "__main__":
    symbols = ["AAPL", "GOOGL", "NVDA", "RKLB", "RCAT", "BKSY", "AMD", "TSLA", "PLTR", "AMZN"]
    results = []

    for symbol in symbols:
        data = fetch_fundamentals(symbol)
        if data:
            results.append(data)

        # 💡 Add delay between calls to be respectful of API limits
        time.sleep(1.2)  # 50 calls/min = ~1.2 seconds per call

    df = pd.DataFrame(results)
    out_path = Path("training_pipeline/data/fundamentals.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved fundamentals to {out_path}")