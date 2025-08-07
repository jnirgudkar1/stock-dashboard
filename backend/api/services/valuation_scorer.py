# backend/api/services/valuation_scorer.py
from .news_crawler import extract_article_text
from .sentiment_analyzer import analyze_sentiment

def normalize_financials(metadata: dict) -> float:
    """
    Converts P/E ratio, dividend yield, and market cap into a valuation score.
    Higher score = more attractive valuation.
    """
    score = 0.0

    pe_ratio = metadata.get("peRatio")
    dividend_yield = metadata.get("dividendYield")
    market_cap = metadata.get("marketCap")

    # P/E ratio scoring
    if pe_ratio and pe_ratio > 0:
        if pe_ratio < 15:
            score += 1.0  # undervalued
        elif pe_ratio < 25:
            score += 0.5  # fairly valued
        else:
            score -= 0.5  # overvalued

    # Dividend Yield scoring
    if dividend_yield is not None:
        if dividend_yield > 2:
            score += 1.0
        elif dividend_yield > 1:
            score += 0.5
        elif dividend_yield < 0.5:
            score -= 0.5

    # Market Cap scoring
    if market_cap:
        if market_cap > 200e9:
            score += 0.5  # strong company
        elif market_cap < 10e9:
            score -= 0.5  # small cap risk

    return round(score, 2)


def compute_valuation_score(news_urls: list, metadata: dict) -> dict:
    """
    Main function to compute final valuation score.
    """
    sentiments = []

    for url in news_urls:
        article_text = extract_article_text(url)
        if article_text:
            sentiment = analyze_sentiment(article_text)
            sentiments.append(sentiment)

    avg_sentiment = round(sum(sentiments) / len(sentiments), 2) if sentiments else 0.0

    from .valuation_scorer import normalize_financials  # ensure this import is included
    financial_score = normalize_financials(metadata)

    total_score = round(avg_sentiment + financial_score, 2)

    if total_score >= 1.5:
        verdict = "Buy"
    elif total_score <= -0.5:
        verdict = "Sell"
    else:
        verdict = "Hold"

    return {
        "sentiment_score": avg_sentiment,
        "financial_score": financial_score,
        "total_score": total_score,
        "verdict": verdict
    }