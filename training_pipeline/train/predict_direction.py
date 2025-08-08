# training_pipeline/train/predict_direction.py

import argparse
import pandas as pd
import joblib
from pathlib import Path
import numpy as np

MODEL_PATH = Path("training_pipeline/models/price_direction_model.pkl")
FUNDAMENTALS_PATH = Path("training_pipeline/data/fundamentals.csv")
PRICES_DIR = Path("training_pipeline/data/historical_prices")

def load_latest_features(symbol):
    # Load fundamentals
    fundamentals_df = pd.read_csv(FUNDAMENTALS_PATH)
    f_row = fundamentals_df[fundamentals_df["symbol"] == symbol]
    if f_row.empty:
        raise ValueError(f"No fundamentals found for {symbol}")
    f_row = f_row.iloc[0]

    # Load latest price
    price_path = PRICES_DIR / f"{symbol}.csv"
    if not price_path.exists():
        raise ValueError(f"No price data found for {symbol}")

    price_df = pd.read_csv(price_path)
    price_df = price_df.sort_values("Date")
    latest_close = price_df.iloc[-1]["Close"]

    return {
        "close_price": latest_close,
        "pe_ratio": f_row["pe_ratio"],
        "eps": f_row["eps"],
        "revenue_growth": f_row["revenue_growth"]
    }

def predict(symbol):
    features = load_latest_features(symbol)
    model = joblib.load(MODEL_PATH)

    df = pd.DataFrame([features])
    numeric_features = ["close_price", "pe_ratio", "eps", "revenue_growth"]
    X = df[numeric_features].astype(np.float32)
    prediction = model.predict(X)[0]
    proba = model.predict_proba(X)[0]

    confidence = round(max(proba) * 100, 2)
    verdict = "Buy" if prediction == 1 else "Hold/Sell"

    print(f"\nPrediction for {symbol}: {verdict}")
    print(f"Confidence: {confidence}%")
    print(f"Model input: {features}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, required=True, help="Stock symbol (e.g. AAPL)")
    args = parser.parse_args()

    predict(args.symbol.upper())