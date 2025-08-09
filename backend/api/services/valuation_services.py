from .news_crawler import extract_article_text
from .analysis_helper import analyze_sentiment, get_eps_estimate_growth, get_revenue_growth
from urllib.parse import urlparse
from math import pow
from datetime import datetime

TRUSTED_DOMAINS = ["reuters.com", "bloomberg.com", "cnbc.com", "wsj.com", "marketwatch.com"]

# -----------------------------
# Valuation Scorer
# -----------------------------

def normalize_financials(metadata: dict) -> float:
    score = 0.0
    pe_ratio = metadata.get("peRatio")
    dividend_yield = metadata.get("dividendYield")
    market_cap = metadata.get("marketCap")

    if pe_ratio and pe_ratio > 0:
        if pe_ratio < 15:
            score += 1.0
        elif pe_ratio < 25:
            score += 0.5
        else:
            score -= 0.5

    if dividend_yield is not None:
        if dividend_yield > 2:
            score += 1.0
        elif dividend_yield > 1:
            score += 0.5
        elif dividend_yield < 0.5:
            score -= 0.5

    if market_cap:
        if market_cap > 200e9:
            score += 0.5
        elif market_cap < 10e9:
            score -= 0.5

    return round(score, 2)

def normalize_growth_score(eps_growth, revenue_growth) -> float:
    score = 0.0
    if eps_growth is not None:
        if eps_growth > 10:
            score += 1.0
        elif eps_growth > 5:
            score += 0.5
        elif eps_growth < 0:
            score -= 0.5

    if revenue_growth is not None:
        if revenue_growth > 10:
            score += 1.0
        elif revenue_growth > 5:
            score += 0.5
        elif revenue_growth < 0:
            score -= 0.5

    return round(score, 2)

def compute_valuation_score(news_urls: list, metadata: dict) -> dict:
    sentiments, confidence_factors, debug_info = [], [], []

    for url in news_urls:
        article_text = extract_article_text(url)
        if not article_text:
            from newspaper import Article
            try:
                article = Article(url)
                article.download()
                article.parse()
                article_text = article.title
            except:
                article_text = ""

        if not article_text or len(article_text.strip()) < 20:
            continue

        sentiment = analyze_sentiment(article_text)
        weight = 1.0
        domain = urlparse(url).netloc.replace("www.", "")
        if domain in TRUSTED_DOMAINS:
            weight += 0.5

        sentiments.append(sentiment * weight)
        confidence_factors.append(weight)

        debug_info.append({
            "url": url,
            "sentiment": round(sentiment, 2),
            "weight": weight,
            "effective": round(sentiment * weight, 2),
            "domain": domain,
            "trusted": domain in TRUSTED_DOMAINS
        })

    avg_sentiment = round(sum(sentiments) / len(sentiments), 2) if sentiments else 0.0
    financial_score = normalize_financials(metadata)
    eps_growth = get_eps_estimate_growth(metadata.get("symbol"))
    revenue_growth = get_revenue_growth(metadata.get("symbol"))
    growth_score = normalize_growth_score(eps_growth, revenue_growth)
    total_score = round(avg_sentiment + financial_score + growth_score, 2)
    avg_confidence = round(sum(confidence_factors) / len(confidence_factors), 2) if confidence_factors else 0.0

    if total_score >= 1.5:
        verdict = "Buy"
    elif total_score <= -0.5:
        verdict = "Sell"
    else:
        verdict = "Hold"

    contradiction = None
    if avg_sentiment > 0.5 and (financial_score + growth_score) < 0:
        contradiction = "Positive news sentiment but weak financials/growth"
    elif avg_sentiment < -0.5 and (financial_score + growth_score) > 0:
        contradiction = "Negative news sentiment but strong financials/growth"

    valuation_label = None
    if contradiction is None:
        if verdict == "Buy" and (financial_score + growth_score) > 1 and avg_sentiment < 0:
            valuation_label = "Undervalued"
        elif verdict == "Sell" and (financial_score + growth_score) < -0.5 and avg_sentiment > 0:
            valuation_label = "Overvalued"

    return {
        "sentiment_score": avg_sentiment,
        "financial_score": financial_score,
        "growth_score": growth_score,
        "total_score": total_score,
        "verdict": verdict,
        "eps_growth": eps_growth,
        "revenue_growth": revenue_growth,
        "confidence": avg_confidence,
        "contradiction": contradiction,
        "valuation_label": valuation_label,
        "debug": debug_info
    }

# -----------------------------
# DCF Valuation
# -----------------------------

def calculate_dcf(free_cash_flow: float, growth_rate: float, discount_rate: float, years: int = 5,
                  terminal_growth_rate: float = 0.02) -> dict:
    discounted_cash_flows = []
    for year in range(1, years + 1):
        projected_fcf = free_cash_flow * pow((1 + growth_rate), year)
        discounted_fcf = projected_fcf / pow((1 + discount_rate), year)
        discounted_cash_flows.append(discounted_fcf)

    terminal_value = (free_cash_flow * pow(1 + growth_rate, years) * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
    discounted_terminal_value = terminal_value / pow(1 + discount_rate, years)
    intrinsic_value = sum(discounted_cash_flows) + discounted_terminal_value

    return {
        "fair_value": round(intrinsic_value, 2),
        "details": {
            "yearly_cash_flows": [round(v, 2) for v in discounted_cash_flows],
            "terminal_value": round(discounted_terminal_value, 2)
        },
        "explanation": f"This estimate is based on a {years}-year cash flow forecast with a {growth_rate*100:.1f}% growth rate, "
                       f"{discount_rate*100:.1f}% discount rate, and {terminal_growth_rate*100:.1f}% terminal growth."
    }

def get_dcf_valuation(symbol: str, current_price: float, market_cap: float,
                      default_fcf_ratio: float = 0.05, growth_rate: float = 0.12, discount_rate: float = 0.10) -> dict:
    free_cash_flow = market_cap * default_fcf_ratio
    dcf_result = calculate_dcf(free_cash_flow, growth_rate, discount_rate)
    dcf_result["is_undervalued"] = dcf_result["fair_value"] > current_price
    dcf_result["current_price"] = round(current_price, 2)
    dcf_result["symbol"] = symbol
    return dcf_result

# -----------------------------
# Graham Valuation
# -----------------------------

def calculate_graham_valuation(eps: float, growth_rate: float = 0.12) -> dict:
    intrinsic_value = eps * (8.5 + 2 * (growth_rate * 100))  # Graham formula
    explanation = f"Graham valuation based on EPS={eps} and growth={growth_rate*100:.1f}%"
    return {
        "fair_value": round(intrinsic_value, 2),
        "eps": eps,
        "growth_rate": growth_rate,
        "explanation": explanation
    }