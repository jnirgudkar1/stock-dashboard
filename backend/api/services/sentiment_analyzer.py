# backend/api/services/sentiment_analyzer.py

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Ensure the lexicon is downloaded only once
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()

def analyze_sentiment(text: str) -> float:
    """
    Returns a compound sentiment score between -1 (very negative) and +1 (very positive).
    """
    if not text:
        return 0.0

    sentiment = sia.polarity_scores(text)
    return round(sentiment["compound"], 4)