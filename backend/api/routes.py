"""
routes.py — unified API routes using merged services

Assumes FastAPI. Keeps your existing URL shape like:
- GET  /api/stocks/{symbol}/prices
- GET  /api/stocks/{symbol}/metadata
- GET  /api/stocks/{symbol}/news
- GET  /api/stocks/{symbol}/valuation
- GET  /api/stocks/{symbol}/predict
- GET  /api/news/search?q=...
- GET  /api/news/article?url=...

If your main app mounts `router` from here in `main.py` like:
    app.include_router(router)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

# NEW merged services
from .services.prices import get_prices, PriceServiceError
from .services.news import (
    search_news,
    fetch_and_cache_article_text,
    summarize,
)
from .services.valuation import score_valuation, predict_direction

# Unchanged service (you chose to keep the filename)
from .services.metadata_services import get_metadata

router = APIRouter(prefix="/api")


# ---------------------------
# Stocks: Prices (normalized Alpha-style)
# ---------------------------
@router.get("/stocks/{symbol}/prices")
def api_prices(
    symbol: str,
    interval: str = Query("1day", examples=["1min", "5min", "15min", "30min", "60min", "1day"]),
    limit: int = Query(100, ge=1, le=2000),
):
    try:
        return get_prices(symbol, interval=interval, limit=limit)
    except PriceServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---------------------------
# Stocks: Metadata (Alpha primary, Finnhub fallback per your service)
# ---------------------------
@router.get("/stocks/{symbol}/metadata")
def api_metadata(symbol: str):
    try:
        return get_metadata(symbol.upper())
    except Exception as e:  # keep broad to avoid leaking stack traces
        raise HTTPException(status_code=502, detail=f"Metadata error: {e}")


# ---------------------------
# Stocks: News & Articles
# ---------------------------
@router.get("/stocks/{symbol}/news")
def api_stock_news(symbol: str, max_items: int = Query(20, ge=1, le=100)):
    try:
        return {"symbol": symbol.upper(), "items": search_news(symbol=symbol.upper(), max_items=max_items)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News error: {e}")


@router.get("/news/search")
def api_search_news(q: str = Query(..., alias="query"), max_items: int = Query(20, ge=1, le=100)):
    try:
        return {"query": q, "items": search_news(query=q, max_items=max_items)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News search error: {e}")


@router.get("/news/article")
def api_fetch_article(url: str = Query(...)):
    try:
        art = fetch_and_cache_article_text(url)
        # small helper: inline a short summary for UI tooltip convenience
        art["summary"] = summarize(art.get("text", ""), max_sentences=3)
        return art
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Article fetch error: {e}")


# ---------------------------
# Stocks: Valuation & Prediction
# ---------------------------
@router.get("/stocks/{symbol}/valuation")
def api_valuation(symbol: str):
    try:
        return score_valuation(symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Valuation error: {e}")


@router.get("/stocks/{symbol}/predict")
def api_predict(symbol: str):
    try:
        return predict_direction(symbol=symbol.upper())
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not found. Train and save price_direction_model.pkl.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Prediction error: {e}")
