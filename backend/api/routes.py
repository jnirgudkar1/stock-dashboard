"""
routes.py — unified API routes using merged services, plus paper-trade & file storage
"""
from __future__ import annotations

import time
from fastapi import APIRouter, HTTPException, Query

# Existing services
from .services.prices import get_prices
from .services.metadata_services import get_metadata
from .services.news import search_news, fetch_and_cache_article_text
from .services.valuation import score_valuation, predict_direction
from .services.features import get_features

# New: file-based storage + papertrade suggester
from .filestore import preload, load_trades, append_trade, update_trade_eval
from .services.papertrade import suggest_trade

router = APIRouter()

# ---------------- Startup ----------------
@router.on_event("startup")
def _startup():
    preload()

# ---------------- Core stock endpoints (existing) ----------------
@router.get("/stocks/{symbol}/prices")
def api_prices(symbol: str, interval: str = Query("1day"), limit: int = Query(100, ge=1, le=5000)):
    try:
        return get_prices(symbol.upper(), interval=interval, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Prices error: {e}")

@router.get("/stocks/{symbol}/metadata")
def api_metadata(symbol: str):
    try:
        data = get_metadata(symbol.upper())
        if not data:
            raise HTTPException(status_code=404, detail="No metadata")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Metadata error: {e}")

@router.get("/stocks/{symbol}/news")
def api_stock_news(symbol: str, max_items: int = Query(25, ge=1, le=100)):
    try:
        return search_news(symbol.upper(), max_items=max_items)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News error: {e}")

@router.get("/news/search")
def api_search_news(q: str = Query(""), max_items: int = Query(25, ge=1, le=100)):
    try:
        return search_news(q, max_items=max_items)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News search error: {e}")

@router.get("/news/article")
def api_article(url: str = Query(..., description="Article URL")):
    try:
        # returns { url, text, words, cached }
        return fetch_and_cache_article_text(url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Article fetch error: {e}")

@router.get("/stocks/{symbol}/features")
def api_features(symbol: str, interval: str = Query("1day"), limit: int = Query(240, ge=10, le=5000), max_news: int = Query(50, ge=0, le=200)):
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

# ---------------- Paper-trade + portfolio (new) ----------------
@router.get("/papertrade/{symbol}")
def api_papertrade(
    symbol: str,
    budget: float = Query(1000.0, ge=50, le=100000),
    horizon_days: int = Query(7, ge=1, le=90),
    temp: float | None = Query(None, ge=0.2, le=5.0),
    auto_store: bool = Query(True),
):
    try:
        out = suggest_trade(symbol=symbol.upper(), budget=budget, horizon_days=horizon_days, temp=temp)
        if auto_store and out.get("action") == "BUY":
            now = int(time.time())
            trade = {
                "id": f"{out['symbol']}-{now}",
                "symbol": out["symbol"],
                "side": "BUY",
                "shares": int(out["shares"]),
                "entry_price": float(out["entry_price"]),
                "notional": float(out["notional"]),
                "opened_at": now,
                "horizon_days": int(out["horizon_days"]),
                "status": "OPEN",
                "rationale": out.get("rationale", {}),
            }
            append_trade(trade)
            out["stored"] = True
            out["trade_id"] = trade["id"]
        return out
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Papertrade error: {e}")

@router.get("/portfolio/trades")
def api_trades_list():
    try:
        return {"items": load_trades()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"List trades error: {e}")

@router.post("/portfolio/evaluate")
def api_trades_evaluate():
    try:
        items = load_trades()
        done = 0
        now_ms = int(time.time() * 1000)
        for t in items:
            if t.get("status") != "OPEN":
                continue
            opened_ms = int(t.get("opened_at") or 0) * 1000
            horizon_days = int(t.get("horizon_days") or 7)
            due_ms = opened_ms + horizon_days * 86400_000
            if now_ms < due_ms:
                continue

            px = get_prices(t["symbol"], interval="1day", limit=1) or {}
            arr = px.get("prices") or []
            if not arr:
                continue
            last = float(arr[-1]["close"])
            entry = float(t["entry_price"])
            ret = (last - entry) / (entry or 1.0)
            update_trade_eval(t["id"], last=last, ret=ret, correct=(ret >= 0))
            done += 1
        return {"evaluated": done}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Evaluate error: {e}")