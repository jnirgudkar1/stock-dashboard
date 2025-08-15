"""
routes.py — unified API routes using merged services
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .services.prices import get_prices
from .services.metadata_services import get_metadata
from .services.news import search_news, fetch_and_cache_article_text
from .services.valuation import score_valuation, predict_direction
from .services.features import get_features

router = APIRouter()

@router.get("/stocks/{symbol}/prices")
def api_prices(
    symbol: str,
    interval: str = Query("1day", description="1min|5min|15min|30min|60min|1day"),
    limit: int = Query(200, ge=1, le=5000),
):
    try:
        return get_prices(symbol.upper(), interval=interval, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Price error: {e}")

@router.get("/stocks/{symbol}/metadata")
def api_metadata(symbol: str):
    try:
        return get_metadata(symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Metadata error: {e}")

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
def api_article(url: str = Query(...)):
    try:
        return fetch_and_cache_article_text(url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Article fetch error: {e}")

@router.get("/stocks/{symbol}/features")
def api_features(
    symbol: str,
    interval: str = Query("1day", description="1min|5min|15min|30min|60min|1day"),
    limit: int = Query(240, ge=50, le=5000),
    max_news: int = Query(50, ge=0, le=200),
):
    try:
        return get_features(symbol.upper(), interval=interval, limit=limit, max_news=max_news)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Features error: {e}")

@router.get("/stocks/{symbol}/valuation")
def api_valuation(symbol: str):
    try:
        return score_valuation(symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Valuation error: {e}")

@router.get("/stocks/{symbol}/predict")
def api_predict(
    symbol: str,
    temp: float | None = Query(None, ge=0.2, le=5.0, description="Calibration temperature (1.0 = no change)"),
):
    try:
        return predict_direction(symbol=symbol.upper(), temp=temp)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not found. Train and save price_direction_model.pkl.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Prediction error: {e}")