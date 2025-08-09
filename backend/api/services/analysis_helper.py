import os
import time
import requests
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# === Load API keys ===
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# === Caching ===
cache = {
    "eps": {},
    "revenue": {}
}
EPS_TTL = 4 * 60 * 60       # 4 hours
REVENUE_TTL = 24 * 60 * 60  # 24 hours

# === Setup NLTK Sentiment ===
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()

# --------------------------
# 🔍 Sentiment Analyzer
# --------------------------

def analyze_sentiment(text: str) -> float:
    """
    Returns a compound sentiment score between -1 (very negative) and +1 (very positive).
    """
    if not text:
        return 0.0
    sentiment = sia.polarity_scores(text)
    return round(sentiment["compound"], 4)

# --------------------------
# 📈 EPS Growth Estimation
# --------------------------

def get_eps_estimate_growth(symbol):
    symbol = symbol.upper()
    now = time.time()

    if symbol in cache["eps"]:
        ts, data = cache["eps"][symbol]
        if now - ts < EPS_TTL:
            return data

    url = f"https://finnhub.io/api/v1/stock/earnings?symbol={symbol}&token={FINNHUB_KEY}"
    try:
        res = requests.get(url)
        earnings = res.json()
        if not earnings or len(earnings) < 2:
            return None

        latest = earnings[0]
        previous = earnings[1]

        if "estimate" in latest and "estimate" in previous:
            latest_eps = float(latest["estimate"])
            previous_eps = float(previous["estimate"])
            if previous_eps == 0:
                return None

            growth = ((latest_eps - previous_eps) / abs(previous_eps)) * 100
            cache["eps"][symbol] = (now, growth)
            return growth
    except Exception as e:
        print(f"EPS growth error: {e}")
    return None

# --------------------------
# 💰 Revenue Growth Estimation
# --------------------------

def get_revenue_growth(symbol):
    symbol = symbol.upper()
    now = time.time()

    if symbol in cache["revenue"]:
        ts, data = cache["revenue"][symbol]
        if now - ts < REVENUE_TTL:
            return data

    url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={ALPHA_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        reports = data.get("annualReports", [])
        if len(reports) >= 2:
            rev_latest = float(reports[0]["totalRevenue"])
            rev_prev = float(reports[1]["totalRevenue"])
            if rev_prev == 0:
                return None

            growth = ((rev_latest - rev_prev) / abs(rev_prev)) * 100
            cache["revenue"][symbol] = (now, growth)
            return growth
    except Exception as e:
        print(f"Revenue growth error: {e}")
    return None