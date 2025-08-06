from fastapi import APIRouter
from .services import price_services, news_services, summary_services, metadata_services

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