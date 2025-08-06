import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_KEY")

# Constants
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "RKLB", "BKSY"]
DAYS_BACK = 30

HEADERS = {"X-Finnhub-Token": FINNHUB_API_KEY}
BASE_URL = "https://finnhub.io/api/v1"


def fetch_historical_prices(symbol):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_BACK)
    end_unix = int(end_date.timestamp())
    start_unix = int(start_date.timestamp())

    url = f"{BASE_URL}/stock/candle"
    params = {
        "symbol": symbol,
        "resolution": "D",
        "from": start_unix,
        "to": end_unix,
        "token": FINNHUB_API_KEY
    }

    res = requests.get(url, params=params).json()
    if res.get("s") != "ok":
        print(f"❌ Failed price data for {symbol}: {res}")
        return pd.DataFrame()

    df = pd.DataFrame({
        "date": [datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d') for ts in res["t"]],
        "price": res["c"]
    })
    return df


def fetch_company_profile(symbol):
    url = f"{BASE_URL}/stock/profile2?symbol={symbol}"
    res = requests.get(url, headers=HEADERS).json()
    return {
        "market_cap": res.get("marketCapitalization", 0) * 1e6  # Convert from millions
    }


def fetch_eps(symbol):
    url = f"{BASE_URL}/stock/metric?symbol={symbol}&metric=all"
    res = requests.get(url, headers=HEADERS).json()
    try:
        return float(res["metric"]["epsInclExtraItemsTTM"])
    except:
        return 0.0


def build_dataset():
    all_rows = []
    for symbol in SYMBOLS:
        print(f"⏳ Processing {symbol}...")

        df = fetch_historical_prices(symbol)
        if df.empty:
            continue

        profile = fetch_company_profile(symbol)
        eps = fetch_eps(symbol)
        market_cap = profile.get("market_cap", 0)

        df = df.sort_values("date").reset_index(drop=True)
        df["price_next"] = df["price"].shift(-1)
        df["will_go_up"] = (df["price_next"] > df["price"]).astype(int)

        df["symbol"] = symbol
        df["market_cap"] = market_cap
        df["eps"] = eps
        df["sentiment"] = 0.7  # TODO: Replace with real score from news feed later

        all_rows.append(df[:-1])  # remove last row (no next-day label)

    full_df = pd.concat(all_rows, ignore_index=True)
    final_df = full_df[["price", "market_cap", "eps", "sentiment", "will_go_up"]]

    out_path = os.path.join(os.path.dirname(__file__), "train.csv")
    final_df.to_csv(out_path, index=False)
    print(f"✅ Training dataset saved to: {out_path}")


if __name__ == "__main__":
    build_dataset()