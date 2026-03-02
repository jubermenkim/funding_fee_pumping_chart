from fastapi import APIRouter, HTTPException
from services.funding_service import get_top5_funding_rates
from services.price_service import get_top5_price_surge_funding

router = APIRouter()


@router.get("/charts/{symbol}")
async def get_chart_data(symbol: str):
    """
    Return two datasets for the given symbol:
    - top5Funding: 5 records with the highest 8h-normalized funding rate
    - top5PriceSurge: funding rates on the 5 days with the highest 24h price increase
    """
    symbol = symbol.upper()
    try:
        top5_funding, top5_surge = await _fetch_both(symbol)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Data fetch error: {e}")

    return {
        "symbol": symbol,
        "top5Funding": top5_funding,
        "top5PriceSurge": top5_surge,
    }


async def _fetch_both(symbol: str):
    import asyncio
    return await asyncio.gather(
        get_top5_funding_rates(symbol),
        get_top5_price_surge_funding(symbol),
    )
