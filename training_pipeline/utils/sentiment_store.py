import json
from pathlib import Path

def save_sentiment(symbol, date, score):
    out_path = Path(f"data/sentiment_{symbol}.json")
    if out_path.exists():
        data = json.loads(out_path.read_text())
    else:
        data = {}

    data[date] = score
    out_path.write_text(json.dumps(data, indent=2))

# Example: AAPL, 2025-08-01 -> sentiment score 0.7
save_sentiment("AAPL", "2025-08-01", 0.7)