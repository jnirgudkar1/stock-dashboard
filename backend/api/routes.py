from fastapi import APIRouter
from .services import price_services, news_services, summary_services, metadata_services
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

from .services.metadata_services import get_metadata
from .services.valuation_scorer import compute_valuation_score

router = APIRouter()

@router.get("/api/stocks/{symbol}")
async def get_stock_price(symbol: str):
    return await price_services.get_stock_price(symbol)

@router.get("/api/stocks/{symbol}/metadata")
async def get_metadata(symbol: str):
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
    metadata = await get_metadata(symbol.upper())  # ✅ await here
    if not metadata or "error" in metadata:
        raise HTTPException(status_code=400, detail="Failed to fetch stock metadata.")

    result = compute_valuation_score(payload.news_urls, metadata)
    return JSONResponse(content=result)