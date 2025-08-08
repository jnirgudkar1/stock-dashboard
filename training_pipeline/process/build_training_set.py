# training_pipeline/process/build_training_set.py

import pandas as pd
from pathlib import Path

FUNDAMENTALS_PATH = Path("training_pipeline/data/fundamentals.csv")
PRICES_DIR = Path("training_pipeline/data/historical_prices")
OUTPUT_PATH = Path("training_pipeline/data/training_data.csv")

def load_fundamentals():
    df = pd.read_csv(FUNDAMENTALS_PATH)
    return {row.symbol: row for _, row in df.iterrows()}

def process_symbol(symbol, fundamentals):
    price_file = PRICES_DIR / f"{symbol}.csv"
    if not price_file.exists():
        return []

    df = pd.read_csv(price_file)
    df = df.sort_values("Date").reset_index(drop=True)

    result_rows = []

    for i in range(len(df) - 7):  # leave 7 days for forward label
        today_row = df.iloc[i]
        future_row = df.iloc[i + 7]

        close_today = today_row["Close"]
        close_future = future_row["Close"]

        label = 1 if close_future > close_today else 0

        fundamentals_row = fundamentals.get(symbol)
        if fundamentals_row is None:
            continue  # skip if no fundamentals for this symbol

        result_rows.append({
            "date": today_row["Date"],
            "symbol": symbol,
            "close_price": close_today,
            "pe_ratio": fundamentals_row.pe_ratio,
            "eps": fundamentals_row.eps,
            "revenue_growth": fundamentals_row.revenue_growth,
            "label_next_7d": label,
        })

    return result_rows

def main():
    fundamentals = load_fundamentals()
    all_rows = []

    for symbol in fundamentals.keys():
        print(f"Processing {symbol}...")
        rows = process_symbol(symbol, fundamentals)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved training dataset to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()