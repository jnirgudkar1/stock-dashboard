from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

# Service imports
from .services import price_services, news_services, summary_services, metadata_services
from .services.valuation_services import compute_valuation_score, get_dcf_valuation, calculate_graham_valuation
from .services.valuation_predictor import predict_price_direction  # once merged in Step 5

router = APIRouter()

# ========== Routes ==========

@router.get("/api/stocks/{symbol}")
async def get_stock_price(symbol: str):
    return await price_services.get_stock_price(symbol)

@router.get("/api/stocks/{symbol}/metadata")
async def fetch_metadata(symbol: str):
    return metadata_services.get_metadata(symbol)

@router.get("/api/news/{symbol}")
async def get_news(symbol: str):
    return await news_services.get_news(symbol)

@router.get("/api/summaries/{symbol}")
async def get_summary(symbol: str):
    return await summary_services.get_summary(symbol)

class ValuationRequest(BaseModel):
    news_urls: List[str]

@router.post("/api/stocks/{symbol}/valuation")
async def get_stock_valuation(symbol: str, payload: ValuationRequest):
    metadata = metadata_services.get_metadata(symbol.upper())
    if not metadata or "error" in metadata:
        raise HTTPException(status_code=400, detail="Failed to fetch stock metadata.")
    result = compute_valuation_score(payload.news_urls, metadata)
    return JSONResponse(content=result)

@router.get("/api/stocks/{symbol}/valuation/dcf")
async def get_dcf(symbol: str, price: float, market_cap: float):
    return get_dcf_valuation(symbol, price, market_cap)

@router.get("/api/stocks/{symbol}/valuation/graham")
async def get_graham(symbol: str, eps: float, growth_rate: float = 0.12):
    return calculate_graham_valuation(eps, growth_rate)

@router.get("/predict/{symbol}")
def get_prediction(symbol: str):
    try:
        return predict_price_direction(symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))