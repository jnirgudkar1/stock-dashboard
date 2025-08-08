# backend/api/services/valuation_predictor.py

import pandas as pd
import joblib
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_PATH = BASE_DIR / "training_pipeline/models/price_direction_model.pkl"
FUNDAMENTALS_PATH = BASE_DIR / "training_pipeline/data/fundamentals.csv"
PRICES_DIR = BASE_DIR / "training_pipeline/data/historical_prices"

def load_latest_features(symbol: str):
    fundamentals_df = pd.read_csv(FUNDAMENTALS_PATH)
    f_row = fundamentals_df[fundamentals_df["symbol"] == symbol]
    if f_row.empty:
        raise ValueError(f"No fundamentals for {symbol}")
    f_row = f_row.iloc[0]

    price_file = PRICES_DIR / f"{symbol}.csv"
    price_df = pd.read_csv(price_file).sort_values("Date")
    latest_close = price_df.iloc[-1]["Close"]

    return {
        "close_price": float(latest_close),
        "pe_ratio": float(f_row["pe_ratio"]),
        "eps": float(f_row["eps"]),
        "revenue_growth": float(f_row["revenue_growth"])
    }

def predict_price_direction(symbol: str):
    model = joblib.load(MODEL_PATH)
    features = load_latest_features(symbol)

    df = pd.DataFrame([features])
    X = df[["close_price", "pe_ratio", "eps", "revenue_growth"]].astype(np.float32)

    prediction = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    confidence = round(float(max(proba)) * 100, 2)
    verdict = "Buy" if prediction == 1 else "Hold/Sell"

    return {
        "symbol": symbol,
        "verdict": verdict,
        "confidence": confidence,
        "inputs": features
    }